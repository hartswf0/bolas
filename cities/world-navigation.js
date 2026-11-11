/**
 * One camera controller for the archive rooms. The director owns the camera in
 * guided mode; this controller owns it in walk/fly mode. It never moves a scene.
 *
 * Room positions use world units. floorY is the walking surface, eyeHeight is
 * added to it, and obstacle boxes are conservative XZ blockers for walking.
 * Flying deliberately ignores those blockers, but respects the room bounds.
 */
const MODES = new Set(['guided', 'walk', 'fly']);
const KEYS = new Set(['KeyW', 'KeyA', 'KeyS', 'KeyD', 'ArrowUp', 'ArrowDown',
  'ArrowLeft', 'ArrowRight', 'KeyQ', 'KeyE', 'Space', 'ControlLeft',
  'ControlRight', 'ShiftLeft', 'ShiftRight', 'KeyF']);
const HALF_PI = Math.PI / 2 - 0.025;
const finite = (n, fallback) => Number.isFinite(n) ? n : fallback;
const clamp = (n, min, max) => Math.max(min, Math.min(max, n));
const vec = (a, fallback) => Array.isArray(a) && a.length === 3 && a.every(Number.isFinite) ? a.slice() : fallback.slice();
const wrap = n => ((n + Math.PI) % (Math.PI * 2) + Math.PI * 2) % (Math.PI * 2) - Math.PI;
const blocksKeyboard = target => !!target?.closest?.('input, select, textarea, button, a, dialog, [role="dialog"], [contenteditable]:not([contenteditable="false"])');

function roomProfile(input = {}) {
  const a = vec(input.bounds?.min, [-120, -20, -160]);
  const b = vec(input.bounds?.max, [120, 80, 120]);
  const bounds = {min: a.map((n, i) => Math.min(n, b[i])), max: a.map((n, i) => Math.max(n, b[i]))};
  const floorY = finite(input.floorY, -6.8), eyeHeight = clamp(finite(input.eyeHeight, 1.7), 0.5, 4);
  return {
    id: String(input.id || ''), bounds, floorY, eyeHeight,
    spawn: vec(input.spawn, [0, floorY + eyeHeight, 14]),
    target: vec(input.target, [0, floorY + eyeHeight, 0]),
    obstacles: (Array.isArray(input.obstacles) ? input.obstacles : []).filter(o =>
      Array.isArray(o?.min) && Array.isArray(o?.max) && o.min.length === 3 && o.max.length === 3 &&
      o.min.every(Number.isFinite) && o.max.every(Number.isFinite)).map(o => ({
      min: o.min.map((n, i) => Math.min(n, o.max[i])),
      max: o.min.map((n, i) => Math.max(n, o.max[i]))
    }))
  };
}

export function createWorldNavigation({THREE, camera, canvas, onChange = () => {}}) {
  if (!THREE?.Euler || !camera?.position || !camera?.quaternion || !canvas?.addEventListener) {
    throw new TypeError('World navigation requires THREE, a camera and its canvas.');
  }
  const win = canvas.ownerDocument?.defaultView || window;
  const doc = canvas.ownerDocument || document;
  const euler = new THREE.Euler(0, 0, 0, 'YXZ');
  const listeners = [], controlListeners = [], keys = new Set(), pointers = new Map(), vertical = new Set(), verticalPointers = new Map();
  const originalTouchAction = canvas.style.touchAction;
  const originalTabindex = canvas.getAttribute('tabindex');
  const settings = {speed: 4.5, sensitivity: 1, invertY: false, reducedMotion: false};
  let profile = roomProfile(), position = profile.spawn.slice(), yaw = 0, pitch = 0;
  let mode = 'guided', enabled = true, disposed = false;
  let joystick = null, lookPad = null, ascend = null, descend = null, interact = null;
  let movePointer = null, lookPointer = null, stickX = 0, stickY = 0;
  let suppressClickUntil = 0, dirty = false, lastNotice = 0;
  const now = () => win.performance?.now?.() ?? Date.now();
  const active = () => !disposed && enabled && mode !== 'guided' && !doc.hidden;
  const listen = (target, name, fn, options, list = listeners) => {
    if (!target?.addEventListener) return;
    target.addEventListener(name, fn, options);
    list.push(() => target.removeEventListener(name, fn, options));
  };
  const pose = () => ({position: position.slice(), yaw, pitch, mode});
  const notify = type => onChange({type, roomId: profile.id, mode, pose: pose()});

  function paintStick() {
    if (!joystick) return;
    joystick.style.setProperty('--stick-x', `${(stickX * 28).toFixed(2)}px`);
    joystick.style.setProperty('--stick-y', `${(stickY * 28).toFixed(2)}px`);
    joystick.dataset.active = movePointer === null ? 'false' : 'true';
  }
  function syncControls() {
    const on = active();
    canvas.style.touchAction = on ? 'none' : originalTouchAction;
    canvas.dataset.navigation = mode;
    for (const el of [joystick, lookPad, ascend, descend, interact]) {
      if (!el) continue;
      const usable = on && (el !== ascend && el !== descend || mode === 'fly');
      el.dataset.navEnabled = String(usable);
      el.setAttribute('aria-disabled', String(!usable));
    }
  }
  function clearInput() {
    keys.clear(); vertical.clear();
    const held = [...pointers.values(), ...verticalPointers.values()];
    verticalPointers.clear();
    pointers.clear(); movePointer = lookPointer = null; stickX = stickY = 0;
    held.forEach(p => { try { if (p.target.hasPointerCapture?.(p.id)) p.target.releasePointerCapture(p.id); } catch {} });
    paintStick();
  }

  function constrain() {
    position = position.map((n, i) => clamp(finite(n, profile.spawn[i]), profile.bounds.min[i], profile.bounds.max[i]));
    if (mode === 'walk') {
      position[1] = clamp(profile.floorY + profile.eyeHeight, profile.bounds.min[1], profile.bounds.max[1]);
      // Imported poses and a change from flight may start inside a shelf. Move to
      // its nearest face before the next input so the visitor cannot be trapped.
      for (let pass = 0; pass < 2; pass++) for (const box of profile.obstacles) {
        const loX = box.min[0] - 0.35, hiX = box.max[0] + 0.35;
        const loZ = box.min[2] - 0.35, hiZ = box.max[2] + 0.35;
        if (position[0] > loX && position[0] < hiX && position[2] > loZ && position[2] < hiZ) {
          const faces = [[Math.abs(position[0] - loX), 0, loX], [Math.abs(hiX - position[0]), 0, hiX],
            [Math.abs(position[2] - loZ), 2, loZ], [Math.abs(hiZ - position[2]), 2, hiZ]];
          faces.sort((a, b) => a[0] - b[0]);
          position[faces[0][1]] = faces[0][2];
        }
      }
      position[0] = clamp(position[0], profile.bounds.min[0], profile.bounds.max[0]);
      position[2] = clamp(position[2], profile.bounds.min[2], profile.bounds.max[2]);
    }
    yaw = wrap(finite(yaw, 0)); pitch = clamp(finite(pitch, 0), -HALF_PI, HALF_PI);
  }
  function applyCamera() {
    if (!active()) return;
    camera.position.set(...position);
    euler.set(pitch, yaw, 0, 'YXZ');
    camera.quaternion.setFromEuler(euler);
    camera.updateMatrixWorld?.();
  }
  function moveAxis(axis, delta) {
    const other = axis === 0 ? 2 : 0, start = position[axis];
    let next = clamp(start + delta, profile.bounds.min[axis], profile.bounds.max[axis]);
    if (mode === 'walk' && (axis === 0 || axis === 2)) for (const box of profile.obstacles) {
      if (position[other] <= box.min[other] - 0.35 || position[other] >= box.max[other] + 0.35) continue;
      const lo = box.min[axis] - 0.35, hi = box.max[axis] + 0.35;
      if (delta > 0 && start <= lo && next > lo) next = Math.min(next, lo);
      else if (delta < 0 && start >= hi && next < hi) next = Math.max(next, hi);
    }
    position[axis] = next;
  }

  function startPointer(event, kind, target) {
    if (!active() || (event.pointerType === 'mouse' && event.button !== 0)) return;
    if (kind === 'look' && lookPointer !== null || kind === 'move' && movePointer !== null) return;
    if (kind === 'look') lookPointer = event.pointerId; else movePointer = event.pointerId;
    const rect = target.getBoundingClientRect();
    const p = {id: event.pointerId, kind, target, startX: event.clientX, startY: event.clientY,
      x: event.clientX, y: event.clientY, dragged: false,
      radius: kind === 'move' && target === joystick ? Math.max(24, Math.min(60, Math.min(rect.width, rect.height) * 0.4)) : 48};
    pointers.set(p.id, p);
    try { target.setPointerCapture(p.id); } catch {}
    if (target === canvas) canvas.focus?.({preventScroll: true});
    event.preventDefault(); event.stopPropagation(); paintStick();
  }
  function movePointerEvent(event) {
    const p = pointers.get(event.pointerId);
    if (!p || !active()) return;
    const dx = event.clientX - p.x, dy = event.clientY - p.y;
    p.x = event.clientX; p.y = event.clientY;
    if (Math.hypot(p.x - p.startX, p.y - p.startY) > 6) p.dragged = true;
    if (p.kind === 'look' && p.dragged) {
      yaw = wrap(yaw - dx * 0.0025 * settings.sensitivity);
      pitch = clamp(pitch - dy * 0.0025 * settings.sensitivity * (settings.invertY ? -1 : 1), -HALF_PI, HALF_PI);
      dirty = true; applyCamera();
    } else if (p.kind === 'move') {
      const x = (p.x - p.startX) / p.radius, y = (p.y - p.startY) / p.radius, d = Math.max(1, Math.hypot(x, y));
      stickX = x / d; stickY = y / d; paintStick();
    }
    event.preventDefault();
  }
  function endPointer(event, cancelled = false) {
    const p = pointers.get(event.pointerId);
    if (!p) return;
    if (p.dragged || p.kind === 'move') suppressClickUntil = now() + 450;
    if (cancelled) { clearInput(); return; }
    pointers.delete(p.id);
    if (lookPointer === p.id) lookPointer = null;
    if (movePointer === p.id) { movePointer = null; stickX = stickY = 0; paintStick(); }
    try { if (p.target.hasPointerCapture?.(p.id)) p.target.releasePointerCapture(p.id); } catch {}
    if (dirty) { notify('pose'); dirty = false; lastNotice = now(); }
  }
  function bindPointerTarget(target, chooseKind, list) {
    listen(target, 'pointerdown', e => startPointer(e, chooseKind(e), target), {passive: false}, list);
    listen(target, 'pointermove', movePointerEvent, {passive: false}, list);
    listen(target, 'pointerup', e => endPointer(e), undefined, list);
    listen(target, 'pointercancel', e => endPointer(e, true), undefined, list);
    listen(target, 'lostpointercapture', e => { if (pointers.has(e.pointerId)) endPointer(e, true); }, undefined, list);
  }
  function interactAtCentre() {
    if (!active()) return;
    const rect = canvas.getBoundingClientRect();
    // Reuse the room's existing click/raycast path and source provenance UI.
    canvas.dispatchEvent(new win.MouseEvent('click', {bubbles: true, detail: 0,
      clientX: rect.left + rect.width / 2, clientY: rect.top + rect.height / 2}));
  }

  if (originalTabindex === null) canvas.setAttribute('tabindex', '0');
  bindPointerTarget(canvas, e => !joystick && e.pointerType !== 'mouse' &&
    e.clientX - canvas.getBoundingClientRect().left < canvas.getBoundingClientRect().width * 0.4 ? 'move' : 'look', listeners);
  listen(canvas, 'click', e => {
    if (e.detail !== 0 && now() < suppressClickUntil) { e.preventDefault(); e.stopImmediatePropagation(); }
  }, true);
  listen(win, 'keydown', e => {
    if (!active() || !KEYS.has(e.code) || blocksKeyboard(e.target) || e.metaKey ||
      (e.ctrlKey && !['ControlLeft', 'ControlRight'].includes(e.code)) || e.altKey || e.isComposing) return;
    if (e.code === 'KeyF') { if (!e.repeat) interactAtCentre(); }
    else keys.add(e.code);
    e.preventDefault();
  });
  listen(win, 'keyup', e => keys.delete(e.code));
  listen(win, 'blur', clearInput);
  listen(doc, 'focusin', e => { if (blocksKeyboard(e.target)) { keys.clear(); stickX = stickY = 0; paintStick(); } });
  listen(doc, 'visibilitychange', () => { clearInput(); syncControls(); });

  const api = {
    get mode() { return mode; },
    get enabled() { return enabled; },
    get isDragging() { return [...pointers.values()].some(p => p.dragged); },
    getPose: pose,
    setPose(value) {
      if (!value || !Array.isArray(value.position) || value.position.length !== 3 ||
        !value.position.every(Number.isFinite) || !Number.isFinite(value.yaw) || !Number.isFinite(value.pitch)) return false;
      position = value.position.slice(); yaw = value.yaw; pitch = value.pitch;
      constrain(); applyCamera(); notify('pose'); return true;
    },
    setMode(value) {
      if (!MODES.has(value)) return false;
      if (value === mode) return true;
      clearInput(); mode = value; constrain(); syncControls(); applyCamera(); notify('mode'); return true;
    },
    enterRoom(input) {
      clearInput(); profile = roomProfile(input); position = profile.spawn.slice();
      const d = profile.target.map((n, i) => n - position[i]);
      yaw = Math.atan2(-d[0], -d[2]); pitch = Math.atan2(d[1], Math.hypot(d[0], d[2]));
      constrain(); applyCamera(); notify('room');
    },
    setEnabled(value) {
      enabled = !!value; if (!enabled) clearInput(); syncControls();
    },
    configure(value = {}) {
      settings.speed = clamp(finite(value.speed, settings.speed), 0.2, 25);
      settings.sensitivity = clamp(finite(value.sensitivity, settings.sensitivity), 0.15, 4);
      if (typeof value.invertY === 'boolean') settings.invertY = value.invertY;
      if (typeof value.reducedMotion === 'boolean') settings.reducedMotion = value.reducedMotion;
    },
    attachControls(controls = {}) {
      clearInput(); controlListeners.splice(0).forEach(remove => remove());
      ({joystick = null, lookPad = null, ascend = null, descend = null, interact = null} = controls);
      if (joystick) {
        const old = joystick.style.touchAction; joystick.style.touchAction = 'none';
        controlListeners.push(() => { joystick.style.touchAction = old; });
        bindPointerTarget(joystick, () => 'move', controlListeners);
      }
      if (lookPad) {
        const old = lookPad.style.touchAction; lookPad.style.touchAction = 'none';
        controlListeners.push(() => { lookPad.style.touchAction = old; });
        bindPointerTarget(lookPad, () => 'look', controlListeners);
      }
      for (const [el, name] of [[ascend, 'up'], [descend, 'down']]) {
        if (!el) continue;
        const old = el.style.touchAction; el.style.touchAction = 'none';
        controlListeners.push(() => { el.style.touchAction = old; });
        const stop = e => {
          vertical.delete(`${name}:${e.pointerId}`); verticalPointers.delete(e.pointerId);
          try { if (el.hasPointerCapture?.(e.pointerId)) el.releasePointerCapture(e.pointerId); } catch {}
        };
        listen(el, 'pointerdown', e => {
          if (!active() || mode !== 'fly' || (e.pointerType === 'mouse' && e.button !== 0)) return;
          vertical.add(`${name}:${e.pointerId}`); verticalPointers.set(e.pointerId, {id: e.pointerId, target: el});
          try { el.setPointerCapture(e.pointerId); } catch {}
          e.preventDefault(); e.stopPropagation();
        }, {passive: false}, controlListeners);
        listen(el, 'pointerup', stop, undefined, controlListeners);
        listen(el, 'pointercancel', () => clearInput(), undefined, controlListeners);
        listen(el, 'lostpointercapture', stop, undefined, controlListeners);
        listen(el, 'keydown', e => {
          if (active() && mode === 'fly' && ['Space', 'Enter'].includes(e.code)) {
            vertical.add(`${name}:key`); e.preventDefault();
          }
        }, undefined, controlListeners);
        listen(el, 'keyup', () => vertical.delete(`${name}:key`), undefined, controlListeners);
        listen(el, 'blur', () => vertical.delete(`${name}:key`), undefined, controlListeners);
      }
      if (interact) listen(interact, 'click', interactAtCentre, undefined, controlListeners);
      paintStick(); syncControls();
    },
    update(dt) {
      if (!active()) return;
      const step = clamp(finite(dt, 0), 0, 0.05);
      const key = (...names) => names.some(n => keys.has(n)) ? 1 : 0;
      const x = key('KeyD', 'ArrowRight') - key('KeyA', 'ArrowLeft') + stickX;
      const f = key('KeyW', 'ArrowUp') - key('KeyS', 'ArrowDown') - stickY;
      const up = mode === 'fly' ? key('KeyE', 'Space') - key('KeyQ', 'ControlLeft', 'ControlRight') +
        ([...vertical].some(n => n.startsWith('up:')) ? 1 : 0) - ([...vertical].some(n => n.startsWith('down:')) ? 1 : 0) : 0;
      const cp = mode === 'fly' ? Math.cos(pitch) : 1, sp = mode === 'fly' ? Math.sin(pitch) : 0;
      let dx = Math.cos(yaw) * x - Math.sin(yaw) * f * cp;
      let dy = sp * f + up, dz = -Math.sin(yaw) * x - Math.cos(yaw) * f * cp;
      const length = Math.hypot(dx, dy, dz), norm = Math.max(1, length);
      const speed = settings.speed * step * (key('ShiftLeft', 'ShiftRight') && !settings.reducedMotion ? 1.8 : 1) / norm;
      if (length > 0.001) {
        moveAxis(0, dx * speed); moveAxis(2, dz * speed);
        if (mode === 'fly') moveAxis(1, dy * speed);
        dirty = true;
      }
      constrain(); applyCamera();
      if (dirty && now() - lastNotice > 200) { notify('pose'); dirty = false; lastNotice = now(); }
    },
    dispose() {
      if (disposed) return;
      clearInput(); controlListeners.splice(0).forEach(remove => remove());
      listeners.splice(0).forEach(remove => remove()); disposed = true;
      canvas.style.touchAction = originalTouchAction;
      delete canvas.dataset.navigation;
      if (originalTabindex === null) canvas.removeAttribute('tabindex'); else canvas.setAttribute('tabindex', originalTabindex);
    }
  };
  syncControls();
  return api;
}
