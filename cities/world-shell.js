import {createWorldNavigation} from './world-navigation.js';
import {createWorldStylePass, STYLE_PRESETS} from './world-style.js';
import {createWorldStore, parseWorldURL, updateWorldURL, WORLD_SCHEMA_VERSION, PAINT_IDS, ARCHITECTURE_IDS} from './world-state.js';
import {createStarfield, createRoomPortals} from './world-sky.js';

const element = (tag, attributes = {}, text) => {
  const node = document.createElement(tag);
  for (const [name, value] of Object.entries(attributes)) node.setAttribute(name, value);
  if (text != null) node.textContent = text;
  return node;
};
const get = (object, path) => path.split('.').reduce((o, key) => o?.[key], object);
const patchAt = (path, value) => path.split('.').reverse().reduce((v, key) => ({[key]: v}), value);

/** One owner for navigation, settings and transitions. Scene/media stay in the host. */
export function createSharedWorld({THREE, Pass, FullScreenQuad, renderer, composer, scene, camera, canvas, rooms, host}) {
  const events = new EventTarget(), roomIds = rooms.map(room => room.id), byId = new Map(rooms.map(room => [room.id, room]));
  let storage, hasSaved = false; try { storage = window.localStorage; hasSaved = !!storage.getItem('celluloid-world.v1'); } catch {}
  const store = createWorldStore({storage, key: 'celluloid-world.v1', roomIds, initialRoom: 'constellation'});
  const url = new URL(location.href), explicit = parseWorldURL(url, {roomIds});
  if (!explicit.room) {
    const old = url.searchParams.get('city') ? 'city-' + url.searchParams.get('city') : url.searchParams.get('look');
    if (roomIds.includes(old)) explicit.room = old;
  }
  // A published paint link should show that paint even after a different saved overlay.
  if (!url.searchParams.has('style') && (url.searchParams.has('lens') || byId.get(explicit.room)?.street)) {
    explicit.style = {preset: 'original'};
  }
  if (url.searchParams.has('song')) explicit.song = url.searchParams.get('song');
  if (!hasSaved && matchMedia('(prefers-reduced-motion: reduce)').matches) {
    explicit.comfort = {reducedMotion: true};
  }
  const initial = store.patch(explicit);
  const stylePass = createWorldStylePass({THREE, Pass, FullScreenQuad}); composer.addPass(stylePass);
  const stars = createStarfield(THREE, scene, innerWidth < 640);
  const destinations = ['library', 'store', 'depot', 'wet', 'datacenter', 'orbit',
    rooms.find(room => room.setting === 'orbit')?.id, rooms.find(room => room.city)?.id]
    .filter((id, i, list) => id && byId.has(id) && list.indexOf(id) === i)
    .map(id => ({id, title: byId.get(id).title}));
  const portals = createRoomPortals(THREE, scene, destinations);
  let profile = null, currentRoom = null, transitionSerial = 0, transitioning = false, restoring = false, disposed = false;
  let statusTimer, saveTimer, lastPoseSave = 0, latestRecord = null, lastState = store.get(), activeDialog = null;
  const cleanup = [], borrowed = [];
  const listen = (target, type, handler, options) => { target.addEventListener(type, handler, options); cleanup.push(() => target.removeEventListener(type, handler, options)); };
  const emit = (type, detail) => events.dispatchEvent(new CustomEvent(type, {detail}));
  const announce = (message, error = false) => {
    clearTimeout(statusTimer); status.replaceChildren(element('span', {}, message));
    if (error) emit('world:error', {operation: 'world', message});
    statusTimer = setTimeout(() => status.replaceChildren(), error ? 11000 : 4500);
  };
  const navigation = createWorldNavigation({THREE, camera, canvas, onChange: change => {
    if (change.type === 'pose' && performance.now() - lastPoseSave > 2000 && !restoring) {
      lastPoseSave = performance.now(); store.patch({pose: change.pose});
    }
  }});

  document.body.classList.add('world-shell');
  const header = element('div', {id: 'world-header'}), heading = element('div');
  heading.append(element('div', {class: 'eyebrow'}, 'CELLULOID CITIES / SHARED WORLD'));
  const roomTitle = element('h1', {}, 'Entering the archive'); heading.append(roomTitle);
  const modeLabel = element('div', {id: 'world-mode-label'}); header.append(heading, modeLabel);
  const dock = element('nav', {id: 'world-dock', 'aria-label': 'World controls'});
  const makeButton = (label, action, title = label) => {
    const button = element('button', {type: 'button', title}, label); listen(button, 'click', action); dock.append(button); return button;
  };
  const modeButton = makeButton('Explore', () => { store.patch({mode: store.get().mode === 'explore' ? 'film' : 'explore'}); canvas.focus({preventScroll: true}); }, 'Switch between exploring and the film director');
  makeButton('Map', () => openPanel(mapPanel));
  const inspectButton = makeButton('Inspect', () => inspectCenter(), 'Inspect the object in the center of the view (F)');
  makeButton('Settings', () => openPanel(settingsPanel));
  const playButton = makeButton('Play', () => { host.togglePlay(); canvas.focus({preventScroll: true}); });
  makeButton('Cabinet', () => { drawCabinet(); openPanel(cabinetPanel); });
  const hint = element('div', {id: 'world-hint'}), status = element('div', {id: 'world-status', role: 'status', 'aria-live': 'polite'});
  const crosshair = element('div', {id: 'world-crosshair', 'aria-hidden': 'true'});
  const joystick = element('div', {id: 'world-stick', role: 'group', 'aria-label': 'Touch movement joystick'});
  const vertical = element('div', {id: 'world-vertical'});
  const ascend = element('button', {type: 'button', 'aria-label': 'Fly upward'}, '↑');
  const descend = element('button', {type: 'button', 'aria-label': 'Fly downward'}, '↓'); vertical.append(ascend, descend);
  document.body.append(header, dock, hint, status, crosshair, joystick, vertical);
  navigation.attachControls({joystick, ascend, descend});

  function panel(id, title) {
    const dialog = element('dialog', {id, class: 'world-panel', 'aria-labelledby': id + '-title'});
    const top = element('header'), titleNode = element('h2', {id: id + '-title'}, title);
    const close = element('button', {type: 'button', 'aria-label': 'Close ' + title}, 'Done');
    listen(close, 'click', () => dialog.close()); top.append(titleNode, close);
    const content = element('div', {class: 'content'}); dialog.append(top, content); document.body.append(dialog);
    listen(dialog, 'close', () => {
      if (activeDialog === dialog) activeDialog = null;
      navigation.setEnabled(!activeDialog && !transitioning && !document.getElementById('start'));
      if (!activeDialog) canvas.focus({preventScroll: true});
    });
    return {dialog, content};
  }
  function openPanel(p) {
    flushPose();
    if (activeDialog) activeDialog.close();
    activeDialog = p.dialog; navigation.setEnabled(false); p.dialog.showModal();
  }
  const settingsPanel = panel('world-settings', 'Tune the world');
  const mapPanel = panel('world-map', 'Constellation map');
  const cabinetPanel = panel('world-cabinet', 'Your cabinet');
  settingsPanel.content.append(element('p', {}, 'Keep your place while changing the marks, atmosphere and movement. Settings follow you between rooms.'));
  const fields = [];
  function section(title) { settingsPanel.content.append(element('h3', {}, title)); }
  function range(title, path, min, max, step) {
    const row = element('div', {class: 'field'}), id = 'setting-' + path.replaceAll('.', '-');
    const input = element('input', {id, type: 'range', min, max, step}), output = element('output', {for: id});
    row.append(element('label', {for: id}, title), input, output); settingsPanel.content.append(row);
    listen(input, 'input', () => store.patch(patchAt(path, Number(input.value)))); fields.push({input, output, path});
  }
  function check(title, path) {
    const row = element('div', {class: 'field'}), id = 'setting-' + path.replaceAll('.', '-');
    const input = element('input', {id, type: 'checkbox'}); row.append(element('label', {for: id}, title), input);
    settingsPanel.content.append(row); listen(input, 'change', () => store.patch(patchAt(path, input.checked))); fields.push({input, path});
  }
  function select(title, path, options, change) {
    const row = element('div', {class: 'field'}), id = 'setting-' + path.replaceAll('.', '-'), input = element('select', {id});
    for (const option of options) input.append(element('option', {value: option.id}, option.label));
    row.append(element('label', {for: id}, title), input); settingsPanel.content.append(row);
    listen(input, 'change', () => {
      try { Promise.resolve(change ? change(input.value) : store.patch(patchAt(path, input.value))).catch(error => announce(error.message, true)); }
      catch (error) { announce(error.message, true); }
    }); fields.push({input, path}); return input;
  }
  section('PLACE & SCORE');
  select('Place', 'room', rooms.map(room => ({id: room.id, label: room.title})), id => api.configure({room: id}));
  if (host.songs?.length) select('Song', 'song', host.songs, id => api.configure({song: id}));
  const paintInput = select('Authored paint', 'authored.paint', host.paints || PAINT_IDS.map(id => ({id, label: id === 'auto' ? 'Room / song original' : id})),
    paint => store.patch({authored: {paint}, style: {preset: 'original'}}));
  const architectureInput = select('City form', 'authored.architecture', host.architectures || ARCHITECTURE_IDS.map(id => ({id, label: id === 'auto' ? 'City original' : id})));
  section('MARKS');
  select('Art treatment', 'style.preset', STYLE_PRESETS);
  range('Treatment strength', 'style.strength', 0, 1, .01);
  range('Outline amount', 'style.outline', 0, 1, .01);
  range('Line width', 'style.lineWidth', .5, 4, .05);
  range('Paper / material grain', 'style.grain', 0, 1, .01);
  range('Line wobble', 'style.wobble', 0, 1, .01);
  settingsPanel.content.append(element('p', {class: 'note'}, 'Room original keeps the authored paint. Choose another treatment to change its palette and marks. Outline amount and line width also work with the original.'));
  section('SKY & MOVEMENT');
  check('Stars', 'environment.stars'); range('Star density', 'environment.density', 0, 1, .01);
  check('Constellation doors', 'environment.constellations'); range('Fog', 'environment.fog', .3, 2, .05);
  select('Travel', 'navigation', [{id: 'walk', label: 'Walk'}, {id: 'fly', label: 'Fly / swim'}]);
  range('Speed', 'controls.speed', 1, 16, .25); range('Look sensitivity', 'controls.sensitivity', .2, 2, .05);
  check('Invert vertical look', 'controls.invertY'); check('Steady camera & marks', 'comfort.reducedMotion');
  range('Volume', 'audio.volume', 0, 1, .01);
  const actions = element('div', {class: 'actions'});
  for (const [title, fn] of [
    ['Return to entrance', () => { if (profile) { navigation.enterRoom(profile); store.patch({pose: navigation.getPose()}); announce('Returned to this room’s entrance.'); } }],
    ['Export settings', () => downloadConfig()],
    ['Copy room link', () => copyLink()],
    ['Reset settings', () => { const room = store.get().room; store.reset(); store.patch({room}); announce('Visual and movement settings reset.'); }]
  ]) { const button = element('button', {type: 'button'}, title); listen(button, 'click', fn); actions.append(button); }
  settingsPanel.content.append(actions);
  const fileLabel = element('label', {for: 'world-import'}, 'Import saved settings');
  const file = element('input', {id: 'world-import', type: 'file', accept: 'application/json,.json'});
  listen(file, 'change', async () => {
    try { if (file.files[0]) { await importConfig(await file.files[0].text()); announce('Settings imported.'); } }
    catch (error) { announce(error.message, true); } finally { file.value = ''; }
  }); settingsPanel.content.append(fileLabel, file);
  const tools = element('details', {id: 'world-tools'}); tools.append(element('summary', {}, 'Film, recording & experiment tools'));
  for (const id of ['bar', 'card']) { const node = document.getElementById(id); if (node) { borrowed.push({node, parent: node.parentNode, next: node.nextSibling}); tools.append(node); } }
  settingsPanel.content.append(tools);

  mapPanel.content.append(element('p', {}, 'Every room shares your camera controls, song, cabinet and visual settings. Enter a star in the observatory or choose a room here.'));
  const search = element('input', {type: 'search', class: 'search', placeholder: 'Find a room, city, or material…', 'aria-label': 'Find a room'});
  const mapGrid = element('div', {class: 'room-grid'}); mapPanel.content.append(search, mapGrid);
  const roomButtons = [];
  for (const room of rooms) {
    const button = element('button', {type: 'button', 'data-room': room.id});
    button.append(element('span', {}, room.title), element('small', {}, room.city ? 'FILM CITY' : room.id === 'constellation' ? 'OBSERVATORY / DOORS' : room.inspect ? 'ARCHIVE / INSPECT' : 'EXPERIMENT'));
    listen(button, 'click', () => { mapPanel.dialog.close(); enterRoom(room.id); }); mapGrid.append(button); roomButtons.push({button, room});
  }
  listen(search, 'input', () => roomButtons.forEach(({button, room}) => { button.hidden = !(`${room.title} ${room.id}`.toLowerCase().includes(search.value.toLowerCase())); }));
  const links = element('details'); links.append(element('summary', {}, 'Other working experiments'));
  links.append(element('p', {class: 'note'}, 'These open their own scenes. Their bodies and instruments are preserved; they are not mounted as rooms in this runtime yet.'));
  for (const [title, href] of [['The Real Jelly', '/contaminant-jelly/bonus/realjelly.html'], ['The Drifts', '/contaminant-jelly/current/drift/'], ['Worlds index', '../worlds/']]) {
    const a = element('a', {href}, title); a.style.cssText = 'display:inline-block;padding:10px 16px 10px 0'; links.append(a);
  } mapPanel.content.append(links);

  function persistURL(state) {
    const next = updateWorldURL(new URL(location.href), state), room = byId.get(state.room);
    if (room?.city) { next.searchParams.set('city', room.city); next.searchParams.delete('look'); }
    else { next.searchParams.set('look', state.room); next.searchParams.delete('city'); }
    if (host.getSong()) next.searchParams.set('song', host.getSong());
    history.replaceState(null, '', next);
  }
  function apply(state) {
    const changedStyle = JSON.stringify(lastState.style) !== JSON.stringify(state.style);
    const changedAuthored = JSON.stringify(lastState.authored) !== JSON.stringify(state.authored);
    if (state.mode === 'explore' && lastState.mode === 'film' && currentRoom && !transitioning) refreshRoom();
    if (profile?.id === state.room && profile.walkable === false && state.navigation === 'walk') {
      store.patch({navigation: 'fly'}); return;
    }
    navigation.configure({...state.controls, reducedMotion: state.comfort.reducedMotion});
    navigation.setMode(state.mode === 'film' ? 'guided' : state.navigation);
    navigation.setEnabled(!activeDialog && !transitioning && !document.getElementById('start'));
    stylePass.configure({...state.style, reducedMotion: state.comfort.reducedMotion});
    stars.configure(state.environment); portals.configure(state.environment.constellations, state.mode === 'explore');
    host.setVolume(state.audio.volume);
    document.body.dataset.worldMode = state.mode;
    modeButton.textContent = state.mode === 'explore' ? 'Explore' : 'Film';
    modeButton.setAttribute('aria-pressed', String(state.mode === 'explore'));
    modeLabel.textContent = state.mode === 'explore' ? state.navigation === 'walk' ? 'WALK / FREE LOOK' : 'FLY / FREE LOOK' : 'FILM / DIRECTOR';
    vertical.dataset.fly = String(state.navigation === 'fly'); inspectButton.disabled = state.mode === 'film';
    hint.textContent = state.mode === 'film' ? 'The film director is moving the camera. Choose Film to return to Explore.' :
      matchMedia('(pointer: coarse)').matches ? 'Left thumb: move · right thumb: look · tap an object or Inspect' :
      'WASD / arrows: move · drag: look · F: inspect' + (state.navigation === 'fly' ? ' · Q / E: descend / rise' : '');
    fields.forEach(({input, output, path}) => {
      const value = get(state, path); if (input.type === 'checkbox') input.checked = value; else input.value = value;
      if (output) output.value = Number(value).toFixed(path === 'style.lineWidth' ? 2 : 2);
    });
    paintInput.disabled = !!byId.get(state.room)?.street;
    architectureInput.disabled = !byId.get(state.room)?.city;
    roomButtons.forEach(({button, room}) => button.setAttribute('aria-current', String(room.id === state.room)));
    clearTimeout(saveTimer); saveTimer = setTimeout(() => persistURL(store.get()), 180);
    lastState = state;
    if (changedAuthored && currentRoom && !transitioning) {
      const layoutChanged = host.configureAuthored?.(state.authored);
      if (layoutChanged) refreshRoom(true);
      host.clearHistory();
      if (profile?.walkable === false && state.navigation === 'walk') store.patch({navigation: 'fly'});
    }
    if (changedStyle) emit('world:style-changed', {style: state.style});
  }
  const unsubscribe = store.subscribe(apply); apply(store.get());
  async function onRoomChanged(id) {
    if (!byId.has(id) || disposed) return false;
    if (currentRoom === id) {
      ++transitionSerial; transitioning = false;
      host.setVolume(lastState.audio.volume);
      roomTitle.textContent = byId.get(id).title;
      navigation.setEnabled(!activeDialog && !transitioning && !document.getElementById('start')); return true;
    }
    const token = ++transitionSerial, previousRoom = currentRoom;
    roomTitle.textContent = 'Entering ' + byId.get(id).title;
    transitioning = true; navigation.setEnabled(false);
    try {
      await host.ready(id);
      if (token !== transitionSerial || disposed) return false;
      const saved = store.get(), savedPose = saved.room === id ? saved.pose : null;
      profile = host.profile(id); profile.id = id;
      restoring = true; navigation.enterRoom(profile);
      if (savedPose) navigation.setPose(savedPose);
      currentRoom = id; portals.enter(id, profile);
      transitioning = false;
      store.patch({room: id, pose: navigation.getPose(), song: host.getSong() || saved.song,
        navigation: profile.walkable === false ? 'fly' : saved.navigation});
      restoring = false; host.clearHistory();
      roomTitle.textContent = byId.get(id).title;
      emit('world:room-entered', {room: id, previousRoom, state: store.get()});
      return true;
    } catch (error) {
      if (token !== transitionSerial || disposed) return false;
      transitioning = false; restoring = false; announce('This room could not load. ' + error.message, true);
      if (previousRoom && previousRoom !== id) host.enterRoom(previousRoom);
      navigation.setEnabled(!activeDialog && !document.getElementById('start'));
      roomTitle.textContent = byId.get(previousRoom)?.title || 'Choose a room in the map';
      return false;
    }
  }
  async function enterRoom(id) {
    if (!byId.has(id)) throw new Error('Unknown room: ' + id);
    try { return await host.enterRoom(id); }
    catch (error) { announce(error.message, true); return false; }
  }
  function refreshRoom(resetPose = false) {
    if (!currentRoom || transitioning || disposed) return;
    const previous = navigation.getPose(); profile = host.profile(currentRoom); profile.id = currentRoom;
    restoring = true; navigation.enterRoom(profile); if (!resetPose) navigation.setPose(previous);
    restoring = false; portals.enter(currentRoom, profile);
  }
  function inspectCenter() {
    if (store.get().mode !== 'explore' || activeDialog) return;
    const destination = portals.hit(camera, 0, 0, host.getOccluders?.());
    if (destination) return enterRoom(destination.id);
    const rect = canvas.getBoundingClientRect();
    canvas.dispatchEvent(new MouseEvent('click', {bubbles: true, clientX: rect.left + rect.width / 2, clientY: rect.top + rect.height / 2}));
    canvas.focus({preventScroll: true});
  }
  listen(canvas, 'click', event => {
    if (store.get().mode !== 'explore' || activeDialog) return;
    const rect = canvas.getBoundingClientRect();
    const destination = portals.hit(camera, (event.clientX - rect.left) / rect.width * 2 - 1, 1 - (event.clientY - rect.top) / rect.height * 2, host.getOccluders?.());
    if (destination) { event.preventDefault(); event.stopImmediatePropagation(); enterRoom(destination.id); }
  }, true);
  function collect(record) {
    if (!record || typeof record.id !== 'string' || !record.id.trim() || typeof record.title !== 'string') throw new TypeError('A cabinet item needs an id and title.');
    const state = store.get(); store.patch({collection: [...state.collection.filter(item => item.id !== record.id), record]});
    announce('Kept in your cabinet: ' + record.title); return store.get().collection;
  }
  function selected(record) {
    latestRecord = record; emit('world:media-selected', {record});
    const address = document.getElementById('addr');
    if (address) {
      address.querySelector('#world-inspect-pin')?.remove();
      const pin = element('button', {id: 'world-inspect-pin', type: 'button'}, 'Keep in cabinet');
      pin.onclick = () => collect(latestRecord); address.append(pin);
    }
  }
  function drawCabinet() {
    cabinetPanel.content.replaceChildren(element('p', {}, 'Selected film objects keep their source address as you move between rooms.'));
    const collection = store.get().collection;
    if (!collection.length) cabinetPanel.content.append(element('p', {}, 'Inspect a city floor or a tape, then choose Keep in cabinet.'));
    for (const record of collection) {
      const entry = element('div', {class: 'entry'}); entry.append(element('strong', {}, record.title), element('small', {}, record.sourceProject || 'Archive'));
      if (record.sourceURL) entry.append(element('a', {href: record.sourceURL, target: '_blank', rel: 'noopener noreferrer'}, 'Open source ↗'));
      const remove = element('button', {type: 'button'}, 'Remove'); remove.style.cssText = 'float:right';
      listen(remove, 'click', () => { store.patch({collection: store.get().collection.filter(item => item.id !== record.id)}); drawCabinet(); });
      entry.append(remove); cabinetPanel.content.append(entry);
    }
  }
  function flushPose() { if (currentRoom && !transitioning) store.patch({pose: navigation.getPose()}); }
  function exportConfig() { flushPose(); return store.exportJSON(); }
  function downloadConfig() {
    const blobURL = URL.createObjectURL(new Blob([exportConfig()], {type: 'application/json'}));
    const a = element('a', {href: blobURL, download: 'celluloid-world-settings.json'}); a.click();
    setTimeout(() => URL.revokeObjectURL(blobURL), 1000);
  }
  async function importConfig(text) {
    const validator = createWorldStore({roomIds, initialRoom: currentRoom || initial.room});
    const next = validator.importJSON(text);
    if (next.song && host.hasSong && !host.hasSong(next.song)) throw new Error('This settings file names a song that is not in the archive.');
    flushPose(); const previous = store.exportJSON(), prior = store.get();
    try {
      if (!(await enterRoom(next.room))) throw new Error('The destination room could not load.');
      if (next.song && next.song !== host.getSong() && host.selectSong) await host.selectSong(next.song);
      store.importJSON(text); store.patch({song: host.getSong()}); restoring = true;
      if (next.pose) navigation.setPose(next.pose);
      restoring = false; flushPose(); return store.get();
    } catch (error) {
      restoring = false; store.importJSON(previous);
      if (currentRoom !== prior.room) await enterRoom(prior.room);
      if (prior.pose) navigation.setPose(prior.pose);
      throw error;
    }
  }
  async function copyLink() {
    persistURL(store.get());
    try { await navigator.clipboard.writeText(location.href); announce('Room link copied. Export settings to include every fine adjustment.'); }
    catch { announce('Copy the address in your browser. Export settings carries the full configuration.'); }
  }
  listen(window, 'pagehide', () => { if (currentRoom) store.patch({pose: navigation.getPose()}); });
  listen(window, 'keydown', event => {
    if (event.key === 'Escape') document.getElementById('addr').style.display = 'none';
  });
  function dispose() {
    if (disposed) return; disposed = true; ++transitionSerial;
    cleanup.forEach(fn => fn()); unsubscribe(); clearTimeout(statusTimer); clearTimeout(saveTimer);
    navigation.dispose(); stars.dispose(); portals.dispose(); composer.removePass(stylePass); stylePass.dispose();
    for (const {node, parent, next} of borrowed) parent.insertBefore(node, next?.parentNode === parent ? next : null);
    for (const node of [header, dock, hint, status, crosshair, joystick, vertical, settingsPanel.dialog, mapPanel.dialog, cabinetPanel.dialog]) node.remove();
    document.body.classList.remove('world-shell'); delete document.body.dataset.worldMode;
  }
  const api = {version: WORLD_SCHEMA_VERSION, rooms: rooms.map(({id, title, inspect}) => ({id, title,
    capabilities: {explore: true, inspect: !!inspect, collect: !!inspect, media: true, style: true}})), events,
    enterRoom, getState: () => store.get(), configure: async patch => {
      if (!patch || typeof patch !== 'object') throw new TypeError('Configuration must be an object.');
      if (patch.song && host.hasSong && !host.hasSong(patch.song)) throw new Error('Unknown archive song.');
      if (patch.room && patch.room !== currentRoom && !(await enterRoom(patch.room))) throw new Error('Room could not load.');
      if (patch.song && patch.song !== host.getSong() && host.selectSong) await host.selectSong(patch.song);
      const next = store.patch({...patch, song: host.getSong()}); if (patch.pose) navigation.setPose(next.pose); return next;
    }, inspectCenter, collect, exportConfig, importConfig, openSettings: () => openPanel(settingsPanel), dispose};
  return {api, initialRoom: initial.room, initialSong: initial.song, onRoomChanged, selected, announce, refreshRoom,
    get isFilm() { return lastState.mode === 'film'; },
    get reducedMotion() { return lastState.comfort.reducedMotion; },
    get activeRoom() { return currentRoom; },
    started() { navigation.setEnabled(!activeDialog && !transitioning); apply(store.get()); },
    onTrackChanged() { store.patch({song: host.getSong()}); host.setVolume(store.get().audio.volume); },
    update(dt, time) {
      if (disposed) return;
      const state = lastState;
      navigation.update(dt);
      if (state.mode === 'explore') { camera.fov = 58; camera.updateProjectionMatrix(); }
      else if (state.comfort.reducedMotion && profile) {
        camera.position.fromArray(profile.spawn); camera.lookAt(...profile.target); camera.fov = 52; camera.updateProjectionMatrix();
      }
      stylePass.configure({...state.style, time, reducedMotion: state.comfort.reducedMotion});
      // Original means the authored experiment. Other treatments start from the unfiltered scene.
      host.setTreatmentOverride(state.style.preset !== 'original');
      scene.fog.density = .028 * state.environment.fog;
      stars.update(camera); portals.update(time, state.comfort.reducedMotion);
      host.flushRoom(currentRoom); host.setVolume(state.audio.volume);
      playButton.textContent = host.isPlaying() ? 'Pause' : 'Play';
    }
  };
}
