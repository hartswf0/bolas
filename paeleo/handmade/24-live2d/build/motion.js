/* SCION-24 · motion: the score drives the parameters; the expression director's tracks time attention (eyes lead, head follows,
   body last); solver passes (gait to planted feet, tail/ear/tag pendulums, breath) run frame by frame at 24 fps. */
(function (G) {
  'use strict';
  const R = G.Rig, { lerp, clamp, smooth } = R;
  const FPS = 24, DT = 1 / FPS;

  // ---- keyframe tracks: [t, value] pairs, smooth (in-out) between keys unless 'lin'
  function track(keys) {
    return t => {
      if (t <= keys[0][0]) return keys[0][1];
      for (let i = 0; i < keys.length - 1; i++) {
        const [t0, v0] = keys[i], [t1, v1, e] = keys[i + 1];
        if (t <= t1) { let u = (t - t0) / (t1 - t0); if (e !== 'lin') u = u * u * (3 - 2 * u); if (e === 'out') u = 1 - Math.pow(1 - (t - t0) / (t1 - t0), 2.2); return lerp(v0, v1, u); }
      }
      return keys[keys.length - 1][1];
    };
  }
  const pulse = (t, t0, a, h, d) => (t < t0 ? 0 : t < t0 + a ? (t - t0) / a : t < t0 + a + h ? 1 : t < t0 + a + h + d ? 1 - (t - t0 - a - h) / d : 0);

  /* ---------- the acting sheet (expression director) ---------- */
  const A = {
    // body yaw: the refusal turn and the return both pass through the view toward the viewer (chest to camera)
    bodyYaw: track([[0, 0], [3.47, 0], [3.93, 190], [8.06, 190], [8.78, 0], [32, 0]]),
    // head yaw leads the body; over-the-shoulder look at 7.46; looking in through the door at 26.4
    headYaw: track([[0, 10], [1.0, 10], [1.6, 4], [2.4, 6], [3.43, 6], [3.86, 196], [4.6, 204], [7.47, 204], [7.92, 16], [8.3, 8], [8.8, 4],
      [9.4, 6], [9.9, -6], [10.4, -9], [10.9, 8], [11.9, 10], [12.5, 6], [13.0, -8], [13.6, -5], [14.3, 6], [14.75, 2], [23.6, 2], [24.6, 10], [26.42, 12], [26.62, 8], [27.2, -54], [28.05, -52], [28.45, -10], [28.9, 10], [32, 10]]),
    headPitch: track([[0, 0], [1.0, 0], [1.4, -10], [2.4, -4], [3.4, 0], [3.9, -8], [5.0, -14], [7.46, -12], [7.9, 4], [8.4, 2], [9.1, -2], [9.35, -9], [9.8, 3], [10.8, 0], [12.1, -2], [12.35, -10], [12.8, 0], [13.2, 4], [14.0, 0], [14.4, -8],
      [14.8, -20], [23.6, -18], [24.4, 2], [25.6, -4], [26.5, -2], [27.2, -1], [28.0, 0], [28.5, -6], [29.0, -12], [32, -12]]),
    headRoll: track([[0, 0], [7.9, 0], [8.2, 6], [8.8, 0], [10.4, 0], [10.7, 8], [11.4, 0], [26.4, 0], [26.6, -5], [27.3, 0], [32, 0]]),
    // gaze: separate from the head; eyes move first
    eyeX: track([[0, 0.2], [0.98, 0.2], [1.06, -0.2], [2.4, 0.1], [3.42, 0.1], [3.46, -1.0], [3.86, -0.2], [4.6, 0.1], [6.2, 0.1], [6.3, -0.95], [6.9, -0.9], [7.05, 0.1], [7.44, 0.1], [7.5, -1.05], [7.9, 0.2],
      [9.3, 0.2], [9.75, 0.7], [10.5, 0.6], [10.8, 0.05], [12.2, 0.1], [12.9, 0.7], [13.7, 0.3], [14.7, 0.3], [23.8, 0.3], [26.44, 0.2], [26.52, 0.8], [27.3, 0.55], [28.1, 0.4], [28.4, 0.1], [32, 0.1]]),
    eyeY: track([[0, 0], [1.0, 0], [1.3, -0.3], [2.4, 0], [3.42, 0], [3.5, -0.3], [7.5, -0.2], [7.9, 0.1], [9.0, 0.0], [9.25, -0.55], [9.7, 0.15], [10.8, 0.1], [12.1, -0.5], [12.8, 0.1], [14.2, -0.3], [14.7, 0.1], [15.0, 0.55], [23.6, 0.5], [24.4, 0.1], [26.5, 0.1], [26.6, 0.45], [28.0, 0.4], [28.4, 0], [32, 0]]),
    brow: track([[0, 0.25], [1.0, 0.25], [1.1, 1.0], [2.4, 0.8], [3.42, 0.7], [3.5, 1.0], [5.2, 0.8], [7.4, 0.7], [8.4, 0.3], [12, 0.15], [14.7, 0.15], [15.2, 0.4], [23.6, 0.35], [24.6, 0.0], [26.4, 0], [26.6, 0.35], [28.2, 0.3], [28.7, 0], [32, 0]]),
    mouth: track([[0, 0], [24.8, 0], [25.2, 0.18], [26.3, 0.18], [26.5, 0], [29.1, 0], [29.3, 0.12], [29.9, 0.05], [30.4, 0], [32, 0]]),
  };
  // blinks (s, duration); slow ones while refusing and when settled
  const BLINKS = [[0.55, 0.14], [2.75, 0.14], [5.4, 0.32], [6.7, 0.3], [9.6, 0.15], [11.2, 0.15], [12.75, 0.14], [14.05, 0.18], [16.4, 0.15], [19.7, 0.15], [22.3, 0.15], [25.0, 0.16], [29.3, 0.4], [30.9, 0.6]];
  const blinkAt = t => { let b = 0; for (const [t0, d] of BLINKS) b = Math.max(b, Math.sin(Math.PI * clamp((t - t0) / d)) * (t >= t0 && t <= t0 + d ? 1 : 0)); return b; };
  // ear asymmetries on top of the score's ear: one ear turns to the voice first
  const earLag = t => [pulse(t, 7.4, 0.05, 0.05, 0.2) * 0.3 + pulse(t, 10.42, 0.05, 0.2, 0.3) * 0.25, pulse(t, 6.22, 0.05, 0.25, 0.3) * 0.35 + pulse(t, 26.44, 0.04, 0.3, 0.4) * 0.15];

  // the person's speech script (shared with the sound): syllable onsets, durations and openness
  const SPEECH = [
    { kind: 'call', text: 'Come here.', syl: [[1.04, 0.26, 0.75, 'k@m'], [1.36, 0.44, 0.6, 'hi@']] },
    { kind: 'call', text: 'Come here! Come on.', syl: [[3.44, 0.24, 0.85, 'k@m'], [3.72, 0.4, 0.7, 'hi@'], [4.2, 0.18, 0.7, 'k@m'], [4.4, 0.24, 0.8, 'on']] },
    { kind: 'soft', text: "It's all right.", syl: [[7.48, 0.16, 0.35, 'its'], [7.7, 0.3, 0.6, 'ol'], [8.06, 0.48, 0.5, 'rait']] },
    { kind: 'soft', text: "All right. Good dog.", syl: [[10.46, 0.3, 0.55, 'ol'], [10.8, 0.42, 0.45, 'rait'], [11.3, 0.18, 0.4, 'gud'], [11.52, 0.3, 0.5, 'dog']] },
    { kind: 'soft', text: 'Come in.', syl: [[26.46, 0.24, 0.6, 'k@m'], [26.76, 0.46, 0.45, 'in']] },
  ];
  function mouthAt(t) { let m = 0, v = 0.5; for (const ln of SPEECH) for (const [t0, d, o] of ln.syl) { const u = (t - t0) / d; if (u > -0.1 && u < 1.1) { const e = Math.sin(Math.PI * clamp(u)) * o * (ln.kind === 'call' ? 1 : 0.6); if (e > m) { m = e; v = o; } } } return [m, v]; }

  function neckFromScore(h) { const K = [[0, -0.3], [0.15, -0.24], [0.35, -0.1], [0.45, -0.26], [0.55, 0.05], [0.7, 0.5], [0.9, 0.9], [1.2, 1.15]]; for (let i = 0; i < K.length - 1; i++) if (h <= K[i + 1][0]) return lerp(K[i][1], K[i + 1][1], (h - K[i][0]) / (K[i + 1][0] - K[i][0])); return 1.15; }

  // camera (staging): a closer two-shot for the calls and the refusal, the room revealed as she sits and the door opens,
  // a portrait of the dog while it considers, wide for the approach, in to the sill for the end
  const CAM = {
    zoom: track([[0, 1.2], [4.9, 1.2], [6.4, 1.0], [8.9, 1.0], [10.3, 2.9], [13.5, 2.9], [14.6, 1.0], [24.1, 1.0], [26.2, 1.75], [32, 1.75]]),
    cx: track([[0, 2.0], [4.9, 2.0], [6.4, 1.504], [8.9, 1.504], [10.3, 3.74], [13.5, 3.74], [14.6, 1.504], [24.1, 1.504], [26.2, 0.02], [32, 0.02]]),
    cy: track([[0, 0.97], [4.9, 0.97], [6.4, 0.851], [8.9, 0.851], [10.3, 0.6], [13.5, 0.6], [14.6, 0.851], [24.1, 0.851], [26.2, 0.8], [32, 0.8]]),
  };
  function create(score) {
    const F = score.frames;
    const N = F.length;
    // body-level pose (no solver state) at frame i (fractional allowed by nearest) — used for gait prediction
    function bodyAt(t) {
      const i = clamp(Math.round(t * FPS), 0, N - 1), f = F[i], a = f.dog.act;
      return { x: f.dog.x, z: 0, bodyYaw: A.bodyYaw(t), lie: a.lie, crouch: a.crouch, breath: 0 };
    }
    const feet = R.homeFeet(Object.assign(bodyAt(0), {})).map(f => ({ x: f.x, z: f.z, y: 0, planted: true, sw: null }));
    // stagger the starting stance a little (a walk is not four feet in a row)
    [0.03, -0.04, -0.02, 0.04].forEach((dx, k) => feet[k].x += dx);
    const tail = Array.from({ length: 7 }, () => ({ p: -40, w: 0, vp: 0, vw: 0 }));
    const ears = [{ a: 0, v: 0 }, { a: 0, v: 0 }];
    const tag = { a: 0, v: 0 };
    let prevHead = null, prevHeadV = [0, 0], prevRoot = null, prevRootV = 0, breathPh = 0, wagPh = 0;
    const events = [];
    const pState = { stepPh: 0 };

    function step(i) {
      const t = i * DT, f = F[i], d = f.dog, a = d.act;
      const B = bodyAt(t);
      const pose = Object.assign({}, B);
      pose.headYaw = A.headYaw(t);
      pose.headPitch = A.headPitch(t);
      pose.headRoll = A.headRoll(t);
      let hsc = a.head;
      let rsc = a.rest;
      if (t >= 25.9 && t < 26.85) { const a0 = F[Math.round(25.9 * FPS)].dog.act, u = t < 26.42 ? 0 : smooth(26.42, 26.85, t); hsc = lerp(a0.head, a.head, u); rsc = lerp(a0.rest, a.rest, u); }
      pose.neck = neckFromScore(hsc);
      pose.rest = rsc; pose.headPitch -= 6 * rsc;
      pose.eyeX = A.eyeX(t); pose.eyeY = A.eyeY(t);
      const wide = pulse(t, 1.0, 0.05, 0.5, 0.6) * 0.18 + pulse(t, 3.42, 0.04, 0.4, 0.5) * 0.2 + pulse(t, 26.44, 0.06, 0.6, 0.6) * 0.12;
      const sleepy = a.lie * (d.state === 'refuse' ? 0.22 : 0) + smooth(28.8, 31, t) * 0.3;
      pose.eyeOpen = clamp(1 + wide - sleepy - blinkAt(t), 0, 1.3);
      pose.brow = A.brow(t);
      pose.mouth = A.mouth(t);
      const el = earLag(t);
      pose.ear = [clamp(a.ear - el[0] * 0 + el[0] * (a.ear < 0.5 ? 1 : -0.6)), clamp(a.ear + el[1] * (a.ear < 0.5 ? 1 : -0.6))];

      // ---- breath (faster when afraid; a long exhale once it has settled)
      const rate = lerp(0.3, 0.75, clamp(a.crouch * 1.2 + (d.state === 'refuse' ? 0.4 : 0)));
      breathPh += 2 * Math.PI * rate * DT;
      const sigh = pulse(t, 29.15, 0.5, 0.2, 1.3);
      pose.breath = 0.5 + 0.5 * Math.sin(breathPh) + 1.6 * sigh;
      if (i > 0 && Math.abs(t - 29.15) < DT / 2) events.push({ t, kind: 'sigh' });

      // ---- gait solver: feet stay planted; a foot steps only when its home has moved away, in the air, coordinated
      const homes = R.homeFeet(pose); const frNow = R.dogFrame(pose);
      const moving = Math.abs(F[Math.min(N - 1, i + 1)].dog.x - d.x) * FPS;
      const swinging = feet.filter(q => !q.planted).length;
      const thr = pose.lie > 0.3 ? 0.03 : (moving > 0.05 ? 0.11 : 0.045);
      const order = feet.map((q, k) => [k, Math.hypot(q.x - homes[k].x, q.z - homes[k].z)]).sort((p, q) => q[1] - p[1]);
      let nSw = swinging;
      for (const [k, err] of order) {
        const q = feet[k];
        if (!q.planted) continue;
        if (err < thr) continue;
        const sameSide = k ^ 2, sameEnd = k ^ 1;
        const J = k < 2 ? R.BODY.shoulder : R.BODY.hip, jw = frNow.loc(J[0], J[1], J[2] * (k % 2 ? -1 : 1));
        const reach = Math.hypot(jw[0] - q.x, jw[1], jw[2] - q.z) / (k < 2 ? R.BODY.front[0] + R.BODY.front[1] + 0.045 : R.BODY.hind[0] + R.BODY.hind[1] + 0.12);
        const blocked = (!feet[sameSide].planted || !feet[sameEnd].planted || nSw >= 2) && err < thr * 2.2 && reach < 0.9;
        if (blocked) continue;
        const dur = clamp(0.3 - 0.1 * moving, 0.15, 0.3) * (pose.lie > 0.3 ? 1.3 : 1);
        const fut = R.homeFeet(Object.assign({}, bodyAt(t + dur)), k);
        const fut2 = R.homeFeet(Object.assign({}, bodyAt(t + dur + 0.2)), k);
        const lead = moving > 0.05 ? 0.6 : 0;
        const to = { x: fut.x + (fut2.x - fut.x) * lead, z: fut.z + (fut2.z - fut.z) * lead };
        q.planted = false; q.sw = { t0: t, dur, from: { x: q.x, z: q.z }, to, h: lerp(0.055, 0.03, clamp(a.crouch + pose.lie)) };
        nSw++;
      }
      for (let k = 0; k < 4; k++) {
        const q = feet[k];
        if (q.planted) { q.y = 0; continue; }
        const u = clamp((t - q.sw.t0) / q.sw.dur), e = u * u * (3 - 2 * u);
        q.x = lerp(q.sw.from.x, q.sw.to.x, e); q.z = lerp(q.sw.from.z, q.sw.to.z, e); q.y = q.sw.h * Math.sin(Math.PI * u);
        if (u >= 1) { q.planted = true; q.y = 0; events.push({ t, kind: 'paw', foot: k, x: q.x, soft: pose.lie > 0.3 || a.crouch > 0.6 }); }
      }
      pose.feet = feet.map(q => ({ x: q.x, z: q.z, y: q.y, planted: q.planted }));

      // ---- tail pendulum chain: targets from the score's tail and wag, follow-through down the chain
      const lift = a.tail;
      const base = lift < 0.5 ? lerp(28, -42, lift / 0.5) : lerp(-42, -98, (lift - 0.5) / 0.85);
      const curl = lift < 0.9 ? 1 : -1;
      const yawV = i > 0 ? R.wrap180(A.bodyYaw(t) - A.bodyYaw(t - DT)) * FPS : 0;
      const wagF = lerp(1.3, 2.4, clamp(a.wag));
      wagPh += 2 * Math.PI * wagF * DT;
      for (let k = 0; k < tail.length; k++) {
        const s = tail[k];
        const tp = base + (curl > 0 ? (k < 4 ? -6 * k : -18 + 9 * (k - 3)) : -9 * k);
        const tw = a.wag * 26 * Math.sin(wagPh - k * 0.55) - yawV * 0.05 * (k + 1) * 0.3;
        const kk = 140 - 12 * k, c = 16 - 1.2 * k;
        const parent = k > 0 ? tail[k - 1] : null;
        const accp = kk * (tp - s.p) - c * s.vp + (parent ? 20 * (parent.p - s.p - (tp - base) * 0) * 0 : 0);
        const accw = kk * (tw - s.w) - c * s.vw + (parent ? 30 * (parent.w - s.w) : 0);
        s.vp += accp * DT; s.vw += accw * DT; s.p += s.vp * DT; s.w += s.vw * DT;
      }
      pose.tail = tail.map(s => ({ p: s.p, w: s.w }));

      // ---- ear and tag pendulums: driven by head angular acceleration and body acceleration
      const hv = prevHead ? [R.wrap180(pose.headYaw - prevHead[0]) * FPS, (pose.headPitch - prevHead[1]) * FPS] : [0, 0];
      const ha = [(hv[0] - prevHeadV[0]) * FPS, (hv[1] - prevHeadV[1]) * FPS];
      prevHead = [pose.headYaw, pose.headPitch]; prevHeadV = hv;
      for (let k = 0; k < 2; k++) { const e = ears[k]; const drive = -(ha[1] * 0.00022 + ha[0] * 0.00008 * (k ? -1 : 1)); e.v += (-90 * e.a - 9 * e.v + drive * 60) * DT; e.a += e.v * DT; e.a = clamp(e.a, -0.35, 0.35); }
      pose.earSwing = [ears[0].a, ears[1].a];
      const rv = prevRoot === null ? 0 : (d.x - prevRoot) * FPS, ra = (rv - prevRootV) * FPS; prevRoot = d.x; prevRootV = rv;
      const bob = feet.reduce((s, q) => s + (q.planted ? 0 : 1), 0) * 0.4;
      tag.v += (-60 * tag.a - 4 * tag.v + ra * 3 + yawV * 0.02 + (Math.random() - 0.5) * bob * 0) * DT; tag.a += tag.v * DT;
      pose.tag = tag.a;
      if (Math.abs(tag.v) > 2.2 && (!events.length || events[events.length - 1].kind !== 'tag' || t - events[events.length - 1].t > 0.18)) events.push({ t, kind: 'tag', amp: Math.min(1, Math.abs(tag.v) / 6) });

      // ---- person
      const p = f.person;
      const [mo, vw] = mouthAt(t);
      const reach = p.reach, low = p.low;
      const standing = p.sit < 0.02 && p.x > -0.3;
      const leanCall = pulse(t, 0.98, 0.15, 1.1, 0.4) * 6;
      const person = { x: p.x, z: lerp(-0.05, 0.3, smooth(5.4, 6.2, t)), sit: p.sit, lean: leanCall + reach * 20 + low * 26, reach, low, mouth: mo, vowel: vw, blink: 0, breath: 0.5 + 0.5 * Math.sin(t * 1.7), brow: 0, hair: 0 };
      // walking back to the bench
      const walking = t > 5.38 && t < 6.25 ? 1 : 0;
      if (walking) pState.stepPh += DT * 2 * Math.PI * 1.8;
      person.walking = walking; person.stepPh = pState.stepPh; person.step = walking ? Math.sin(pState.stepPh) : 0;
      // head: toward the dog (down when the dog is low and close), turned a little to the viewer once seated
      const dogHead = [d.x - 0.3, 0.55 * (1 - 0.45 * a.lie)];
      person.headYaw = lerp(0.15, 0.45, smooth(5.8, 6.8, t));
      person.headPitch = clamp(-Math.atan2(1.5 - dogHead[1], dogHead[0] - p.x) * 1.4 + 0.1, -1, 0.6) * (1 - 0.3 * p.sit) - 0.35 * p.sit;
      person.blink = [1.9, 4.9, 8.9, 12.7, 17.2, 21.5, 24.6, 28.6, 31.2].reduce((b, t0) => Math.max(b, (t >= t0 && t <= t0 + 0.14) ? Math.sin(Math.PI * (t - t0) / 0.14) : 0), 0);
      // arms: reach toward the dog, pull the door, offer a hand low
      const shY = lerp(1.38, 0.98, p.sit);
      let target = null;
      if (reach > 0.01) target = [lerp(p.x + 0.12, p.x + 0.62, reach), lerp(shY - 0.5, shY - 0.28, reach)];
      const pull = pulse(t, 5.95, 0.3, 0.25, 0.35);
      const door = t < 6.2 ? 38 : lerp(38, 100, smooth(6.2, 6.95, t));
      if (pull > 0.01) { const a2 = door * Math.PI / 180; const hx = -0.22 - 0.88 * 0.9 * Math.sin(a2); target = [lerp(p.x + 0.15, hx, pull), lerp(0.6, 1.0, pull)]; }
      if (low > 0.01) { const lowT = [p.x + 0.8, 0.2]; target = target ? [lerp(target[0], lowT[0], low), lerp(target[1], lowT[1], low)] : [lerp(p.x + 0.2, lowT[0], low), lerp(0.55, lowT[1], low)]; }
      person.armTarget = target;
      if (i > 0 && Math.abs(t - 5.45) < DT / 2) events.push({ t, kind: 'steps' });
      if (i > 0 && Math.abs(t - 6.05) < DT / 2) events.push({ t, kind: 'sit' });
      if (i > 0 && Math.abs(t - 6.2) < DT / 2) events.push({ t, kind: 'door' });

      // ---- scene state: door, light, camera
      const open = clamp((door - 38) / 62);
      const S = { doorAng: door, open, lightAmt: 1, lightBlock: standing ? 0.5 : lerp(0.5, 1, smooth(5.3, 5.9, t)) };
      const cam = { S: 188, zoom: CAM.zoom(t), cx: CAM.cx(t), cy: CAM.cy(t), W: 1280, H: 720 };
      // light on the dog: door spill at its head, dimmer at dusk outside
      const warm = Scene.spill(Math.max(d.x - 0.2, Scene.WALL.outer + 0.05), 0, open, S.lightBlock) * 0.9;
      const L = { dusk: 0.36, warm: clamp(warm) };
      if (pose.lie > 0.5 && i > 0 && F[i - 1].dog.act.lie <= 0.5) events.push({ t, kind: 'lie' });
      return { t, i, pose, person, S, cam, L, state: d.state, score: f };
    }
    return { step, events, SPEECH, A, BLINKS, CAM };
  }
  G.Motion = { create, SPEECH, track, FPS };
})(typeof window !== 'undefined' ? window : globalThis);
