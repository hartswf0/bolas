// Integration checks for the real shell/state/navigation/style/sky modules.
// This is a DOM/host contract harness, not browser or GPU validation. LinkeDOM
// supplies the document; canvas 2D drawing, dialogs, composer and archive host
// are explicit doubles. THREE's actual scene, camera, geometry and ray math run.
// Install: npm --prefix cities/tests install --ignore-scripts
// Optional external dependencies: WORLD_SHELL_TEST_DEPS=/path/to/package-root
// Optional production THREE module: WORLD_SHELL_TEST_THREE=/path/to/three.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createSharedWorld} from '../world-shell.js';
import {PAINT_IDS, ARCHITECTURE_IDS} from '../world-state.js';

let parseHTML, THREE, dependencyError;
try {
  const require = createRequire(process.env.WORLD_SHELL_TEST_DEPS
    ? resolve(process.env.WORLD_SHELL_TEST_DEPS, 'package.json') : import.meta.url);
  ({parseHTML} = require('linkedom'));
  THREE = process.env.WORLD_SHELL_TEST_THREE
    ? await import(pathToFileURL(resolve(process.env.WORLD_SHELL_TEST_THREE)).href)
    : require('three');
} catch (error) { dependencyError = error; }

if (dependencyError) {
  test('world shell integration dependencies', {
    skip: 'Run npm --prefix cities/tests install --ignore-scripts, then rerun the tests.'
  }, () => {});
} else {
  const rooms = [
    {id: 'constellation', title: 'Constellation Observatory'},
    {id: 'library', title: 'Library', inspect: true},
    {id: 'store', title: 'Video Store', inspect: true},
    {id: 'wet', title: 'Wet Collection', inspect: true},
    {id: 'city-b1', title: 'Orbital Film City', inspect: true, city: 'b1', setting: 'orbit'}
  ];
  const deferred = () => { let resolve, reject; const promise = new Promise((a, b) => { resolve = a; reject = b; }); return {promise, resolve, reject}; };
  const memoryStorage = () => { const values = new Map(); return {
    getItem: key => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, String(value)), values
  }; };

  function harness(t, options = {}) {
    const {document, window} = parseHTML('<!doctype html><html><body><canvas id="gl"></canvas><div id="bar"><button>Legacy play</button></div><div id="card">Legacy card</div><div id="addr"></div></body></html>');
    const oldGlobals = new Map(), install = (name, value) => {
      oldGlobals.set(name, Object.getOwnPropertyDescriptor(globalThis, name));
      Object.defineProperty(globalThis, name, {value, writable: true, configurable: true});
    };
    // LinkeDOM has a read-only select.value and no native dialog/canvas runtime.
    Object.defineProperty(window.HTMLSelectElement.prototype, 'value', {
      configurable: true,
      get() { return this._testValue ?? this.querySelector('option[selected]')?.value ?? ''; },
      set(value) { this._testValue = String(value); }
    });
    window.HTMLCanvasElement.prototype.getContext = () => ({fillRect() {}, strokeRect() {}, fillText() {}});
    window.HTMLElement.prototype.getBoundingClientRect = function () {
      const width = this.id === 'world-stick' ? 112 : 960, height = this.id === 'world-stick' ? 112 : 600;
      return {left: 0, top: 0, width, height, right: width, bottom: height};
    };
    window.HTMLElement.prototype.focus = function () {};
    window.HTMLElement.prototype.setPointerCapture = function () {};
    window.HTMLElement.prototype.releasePointerCapture = function () {};
    window.HTMLElement.prototype.hasPointerCapture = () => false;
    window.HTMLElement.prototype.showModal = function () { this.open = true; };
    window.HTMLElement.prototype.close = function () {
      if (!this.open) return;
      this.open = false;
      // Native close notifications are queued; the guard must survive opening
      // another dialog before this older notification reaches its handler.
      queueMicrotask(() => this.dispatchEvent(new window.Event('close')));
    };
    class MouseEvent extends window.Event {
      constructor(type, options = {}) {
        super(type, options);
        Object.assign(this, {clientX: options.clientX ?? 0, clientY: options.clientY ?? 0, detail: options.detail ?? 0});
      }
    }
    const timers = new Map(); let nextTimer = 1, now = 3000;
    const setTimer = (fn, delay = 0) => { const id = nextTimer++; timers.set(id, {fn, at: now + delay}); return id; };
    const clearTimer = id => timers.delete(id);
    const advance = amount => {
      const end = now + amount;
      while (true) {
        const next = [...timers].filter(([, timer]) => timer.at <= end).sort((a, b) => a[1].at - b[1].at)[0];
        if (!next) break;
        timers.delete(next[0]); now = next[1].at; next[1].fn();
      }
      now = end;
    };
    const storage = options.storage || memoryStorage(), location = {href: options.url || 'https://example.org/bolas/cities/?song=the-current&arch=reef&lens=watercolour#selected'};
    const routes = [], history = {replaceState(_state, _title, next) {
      location.href = new URL(next, location.href).href; routes.push(location.href);
    }};
    const globals = {window, document, innerWidth: 960, innerHeight: 600,
      Event: window.Event, EventTarget: window.EventTarget, CustomEvent: window.CustomEvent, MouseEvent,
      location, history, navigator: {clipboard: {writeText: async () => {}}},
      matchMedia: query => ({matches: !!options.reducedMotion && query.includes('reduced-motion')}),
      setTimeout: setTimer, clearTimeout: clearTimer, performance: {now: () => now}};
    for (const [name, value] of Object.entries(globals)) install(name, value);
    Object.defineProperty(window, 'localStorage', {value: storage, configurable: true});
    Object.defineProperty(document, 'hidden', {value: false, configurable: true});
    const scene = new THREE.Scene(); scene.fog = new THREE.FogExp2(0x102030, 0.028);
    const camera = new THREE.PerspectiveCamera(58, 960 / 600, 0.1, 400), canvas = document.getElementById('gl');
    const borrowed = [document.getElementById('bar'), document.getElementById('card')];
    const composer = {passes: [], addPass(pass) { this.passes.push(pass); pass.setSize(960, 600); }, removePass(pass) { this.passes = this.passes.filter(item => item !== pass); }};
    class Pass { constructor() { this.enabled = true; this.renderToScreen = false; } }
    class FullScreenQuad { constructor(material) { this.material = material; } render() {} dispose() { this.disposed = true; } }
    let shell, activeHostRoom = null, volume = 1, song = 'the-current', playing = false;
    let authored = {paint: 'auto', architecture: 'auto'};
    const readiness = new Map(), calls = [];
    const host = {
      songs: [{id: 'the-current', label: 'Current archive song'}, {id: 'other-song', label: 'Another archive song'}],
      paints: PAINT_IDS.map(id => ({id, label: id === 'auto' ? 'Original room paint' : `Author ${id}`})),
      architectures: ARCHITECTURE_IDS.map(id => ({id, label: id === 'auto' ? 'Original city form' : `Form ${id}`})),
      configureAuthored(config) {
        const layoutChanged = authored.architecture !== config.architecture;
        authored = {...config}; calls.push(['authored', {...config}]); return layoutChanged;
      },
      getSong: () => song, setVolume: value => { volume = value; },
      hasSong: id => ['the-current', 'other-song'].includes(id),
      selectSong: async id => {
        if (!['the-current', 'other-song'].includes(id)) throw new Error('Unknown archive song');
        song = id; calls.push(['song', id]); shell.onTrackChanged();
      },
      togglePlay() { playing = !playing; }, isPlaying: () => playing,
      setTreatmentOverride: value => calls.push(['treatment', value]),
      flushRoom: id => calls.push(['flush', id]), clearHistory: () => calls.push(['clearHistory']),
      getOccluders: () => [],
      profile: id => ({id, spawn: [0, -5.1, 14], target: [0, -5.1, 0], floorY: -6.8, eyeHeight: 1.7,
        bounds: {min: [-30, -6.8, -40], max: [30, 30, 30]}, obstacles: [], walkable: id !== 'city-b1'}),
      ready: id => readiness.get(id)?.promise ?? Promise.resolve(),
      enterRoom: async id => { activeHostRoom = id; calls.push(['enter', id]); return shell.onRoomChanged(id); }
    };
    t.after(() => {
      try { shell?.api.dispose(); } finally {
        for (const [name, descriptor] of oldGlobals) {
          if (descriptor) Object.defineProperty(globalThis, name, descriptor); else delete globalThis[name];
        }
      }
    });
    shell = createSharedWorld({THREE, Pass, FullScreenQuad, renderer: {}, composer, scene, camera, canvas, rooms, host});
    const click = node => node.dispatchEvent(new MouseEvent('click', {bubbles: true, detail: 1}));
    const dockButton = title => [...document.querySelectorAll('#world-dock button')].find(node => node.textContent === title);
    const key = code => {
      const event = new window.Event('keydown', {bubbles: true, cancelable: true});
      Object.assign(event, {code, key: code, repeat: false}); window.dispatchEvent(event);
    };
    return {shell, api: shell.api, document, window, camera, scene, canvas, composer, host, storage, location, routes, calls,
      advance, readiness, click, dockButton, key, borrowed,
      get hostRoom() { return activeHostRoom; }, get volume() { return volume; }, setSong(value) { song = value; },
      get hostAuthored() { return {...authored}; },
      async enter(id = shell.initialRoom) { return shell.api.enterRoom(id); }
    };
  }

  test('shell boots with actual THREE, blocked storage and reduced-motion preferences', async t => {
    const h = harness(t, {reducedMotion: true, storage: {getItem() { throw Error('disabled'); }, setItem() { throw Error('disabled'); }}});
    assert.equal(THREE.REVISION, '160');
    assert.equal(h.shell.initialRoom, 'constellation');
    assert.equal(await h.enter(), true);
    assert.equal(h.api.getState().comfort.reducedMotion, true);
    assert.equal(h.api.getState().room, h.hostRoom);
    assert.equal(h.composer.passes.length, 1);
    assert.equal(h.composer.passes[0].enabled, false);
    assert.doesNotThrow(() => h.shell.update(1 / 60, 1));
  });

  test('legacy entry routing and new preferences agree with the active host room', async t => {
    const h = harness(t, {url: 'https://example.org/bolas/cities/?city=b1&song=the-current&lens=watercolour&arch=reef&style=thread#selected'});
    assert.equal(h.shell.initialRoom, 'city-b1');
    await h.enter(); h.advance(200);
    const query = new URL(h.location.href);
    assert.equal(h.api.getState().room, h.hostRoom);
    assert.equal(query.searchParams.get('room'), 'city-b1');
    assert.equal(query.searchParams.get('city'), 'b1');
    assert.equal(query.searchParams.get('song'), 'the-current');
    assert.equal(query.searchParams.get('lens'), 'watercolour');
    assert.equal(query.searchParams.get('arch'), 'reef');
    assert.equal(query.hash, '#selected');
    assert.equal(h.api.getState().navigation, 'fly');
  });

  test('legacy walk and authored lens links initialize the shared controls and survive URL persistence', async t => {
    const h = harness(t, {url: 'https://example.org/bolas/cities/?look=library&walk=1&lens=woodblock&arch=reef&song=the-current#source'});
    assert.equal(h.shell.initialRoom, 'library');
    assert.equal(h.api.getState().mode, 'explore');
    assert.equal(h.api.getState().navigation, 'fly');
    assert.deepEqual(h.api.getState().authored, {paint: 'woodblock', architecture: 'reef'});
    assert.equal(h.document.getElementById('setting-authored-paint').value, 'woodblock');
    assert.equal(h.document.getElementById('setting-authored-architecture').value, 'reef');
    await h.enter(); h.advance(200);
    assert.equal(h.canvas.dataset.navigation, 'fly');
    const query = new URL(h.location.href);
    assert.equal(query.searchParams.get('mode'), 'explore');
    assert.equal(query.searchParams.get('movement'), 'fly');
    assert.equal(query.searchParams.get('lens'), 'woodblock');
    assert.equal(query.searchParams.get('arch'), 'reef');
    assert.equal(query.hash, '#source');
  });

  test('an explicit authored paint link wins over a previously saved adjustable treatment', async t => {
    const storage = memoryStorage();
    storage.setItem('celluloid-world.v1', JSON.stringify({version: 1, room: 'library', style: {preset: 'thread'}}));
    const h = harness(t, {storage, url: 'https://example.org/bolas/cities/?look=library&lens=riso'});
    await h.enter();
    assert.equal(h.api.getState().authored.paint, 'riso');
    assert.equal(h.api.getState().style.preset, 'original');
    h.shell.update(1 / 60, 1);
    assert.equal(h.calls.filter(([kind]) => kind === 'treatment').at(-1)[1], false);
  });

  test('choosing authored paint applies the host hook and returns the adjustable treatment to Original', async t => {
    const h = harness(t); await h.enter('city-b1');
    await h.api.configure({authored: {architecture: 'helix'}, style: {preset: 'thread'}});
    h.shell.update(1 / 60, 1);
    assert.equal(h.calls.filter(([kind]) => kind === 'treatment').at(-1)[1], true);
    const paint = h.document.getElementById('setting-authored-paint');
    assert.equal(paint.querySelector('option[value="riso"]').textContent, 'Author riso');
    assert.equal(h.document.getElementById('setting-authored-architecture').disabled, false);
    paint.value = 'riso'; paint.dispatchEvent(new h.window.Event('change', {bubbles: true}));
    h.shell.update(1 / 60, 2);
    assert.deepEqual(h.api.getState().authored, {paint: 'riso', architecture: 'helix'});
    assert.deepEqual(h.hostAuthored, {paint: 'riso', architecture: 'helix'});
    assert.equal(h.api.getState().style.preset, 'original');
    assert.equal(h.document.getElementById('setting-style-preset').value, 'original');
    assert.equal(h.calls.filter(([kind]) => kind === 'treatment').at(-1)[1], false);
    assert.equal(h.composer.passes[0].enabled, false);
    await h.enter('library');
    assert.equal(h.document.getElementById('setting-authored-architecture').disabled, true);
  });

  test('authored choices persist between rooms and a JSON import restores both host paint and architecture', async t => {
    const h = harness(t); await h.enter('library');
    await h.api.configure({authored: {paint: 'cyanotype', architecture: 'shell'}, style: {preset: 'ink'}});
    const expected = {paint: 'cyanotype', architecture: 'shell'};
    assert.deepEqual(h.calls.filter(([kind]) => kind === 'authored').at(-1)[1], expected);
    await h.enter('city-b1');
    assert.deepEqual(h.api.getState().authored, expected); assert.deepEqual(h.hostAuthored, expected);
    const exported = h.api.exportConfig();
    assert.deepEqual(JSON.parse(exported).authored, expected);
    await h.api.configure({room: 'wet', authored: {paint: 'xray', architecture: 'reef'}, style: {preset: 'glass'}});
    assert.deepEqual(h.hostAuthored, {paint: 'xray', architecture: 'reef'});
    await h.api.importConfig(exported); h.advance(200);
    assert.equal(h.hostRoom, 'city-b1');
    assert.deepEqual(h.api.getState().authored, expected); assert.deepEqual(h.hostAuthored, expected);
    assert.equal(h.api.getState().style.preset, 'ink');
    const query = new URL(h.location.href);
    assert.equal(query.searchParams.get('lens'), 'cyanotype'); assert.equal(query.searchParams.get('arch'), 'shell');
  });

  test('configuration transitions a real room and UI range changes reach shader uniforms', async t => {
    const h = harness(t); await h.enter();
    const events = [];
    h.api.events.addEventListener('world:style-changed', event => events.push(event.detail.style));
    await h.api.configure({room: 'wet', style: {preset: 'woodblock'}, audio: {volume: 0.3}});
    assert.equal(h.hostRoom, 'wet'); assert.equal(h.api.getState().room, 'wet'); assert.equal(h.volume, 0.3);
    const input = h.document.getElementById('setting-style-outline'); input.value = '0.42';
    input.dispatchEvent(new h.window.Event('input', {bubbles: true}));
    assert.equal(h.api.getState().style.outline, 0.42);
    assert.equal(h.composer.passes[0].material.uniforms.uOutline.value, 0.42);
    assert.equal(h.composer.passes[0].enabled, true);
    assert.equal(events.at(-1).outline, 0.42);
  });

  test('an old dialog close notification cannot reenable movement under the new dialog', async t => {
    const h = harness(t); await h.enter();
    h.click(h.dockButton('Settings')); h.click(h.dockButton('Map'));
    await Promise.resolve();
    assert.equal(h.document.getElementById('world-map').open, true);
    assert.equal(h.document.getElementById('world-stick').dataset.navEnabled, 'false');
    h.document.getElementById('world-map').close(); await Promise.resolve();
    assert.equal(h.document.getElementById('world-stick').dataset.navEnabled, 'true');
  });

  test('public openSettings pauses navigation, releases held keys and restores control when Done closes it', async t => {
    const h = harness(t); await h.enter('library');
    h.key('KeyW'); h.shell.update(1 / 60, 1);
    assert.ok(h.camera.position.z < 14, 'the harness must deliver movement before opening settings');
    h.api.openSettings();
    const dialog = h.document.getElementById('world-settings'), stopped = h.camera.position.toArray();
    assert.equal(dialog.open, true);
    assert.equal(h.document.getElementById('world-stick').dataset.navEnabled, 'false');
    h.key('KeyW'); h.shell.update(1 / 60, 2);
    assert.deepEqual(h.camera.position.toArray(), stopped);
    h.click(dialog.querySelector('header button')); await Promise.resolve();
    assert.equal(dialog.open, false);
    assert.equal(h.document.getElementById('world-stick').dataset.navEnabled, 'true');
    h.shell.update(1 / 60, 3);
    assert.deepEqual(h.camera.position.toArray(), stopped, 'closing must not resume a stale held key');
    h.key('KeyW'); h.shell.update(1 / 60, 4);
    assert.ok(h.camera.position.z < stopped[2]);
    assert.equal(h.api.getState().mode, 'explore'); assert.equal(h.host.getSong(), 'the-current');
  });

  test('failed readiness returns to the previous room without changing visual settings', async t => {
    const h = harness(t); await h.enter('library');
    const failure = deferred(); h.readiness.set('wet', failure);
    const pending = h.enter('wet'); failure.reject(Error('archive unavailable'));
    assert.equal(await pending, false); await Promise.resolve();
    assert.equal(h.hostRoom, 'library'); assert.equal(h.api.getState().room, 'library');
    assert.equal(h.document.getElementById('world-stick').dataset.navEnabled, 'true');
    assert.match(h.document.getElementById('world-status').textContent, /could not load/);
  });

  test('a stale successful room load cannot replace a newer destination', async t => {
    const h = harness(t); await h.enter('library');
    const old = deferred(), next = deferred(); h.readiness.set('wet', old); h.readiness.set('store', next);
    const a = h.enter('wet'), b = h.enter('store'); next.resolve();
    assert.equal(await b, true); old.resolve(); assert.equal(await a, false);
    assert.equal(h.hostRoom, 'store'); assert.equal(h.api.getState().room, 'store');
    assert.equal(h.document.getElementById('world-stick').dataset.navEnabled, 'true');
  });

  test('a stale rejected room load cannot roll back a newer destination', async t => {
    const h = harness(t); await h.enter('library');
    const old = deferred(); h.readiness.set('wet', old);
    const a = h.enter('wet'); assert.equal(await h.enter('store'), true);
    old.reject(Error('late failure')); assert.equal(await a, false);
    assert.equal(h.hostRoom, 'store'); assert.equal(h.api.getState().room, 'store');
  });

  test('returning to the current room cancels an outstanding destination load', async t => {
    const h = harness(t); await h.enter('library');
    const pendingRoom = deferred(); h.readiness.set('wet', pendingRoom);
    const previousRequest = h.enter('wet');
    assert.equal(await h.enter('library'), true);
    assert.equal(h.document.getElementById('world-stick').dataset.navEnabled, 'true');
    pendingRoom.resolve(); assert.equal(await previousRequest, false);
    assert.equal(h.hostRoom, 'library'); assert.equal(h.api.getState().room, 'library');
  });

  test('invalid and unloaded imports preserve the current configuration and room', async t => {
    const h = harness(t); await h.enter('library');
    await h.api.configure({style: {preset: 'cyanotype'}});
    const before = h.api.exportConfig(), callCount = h.calls.length;
    await assert.rejects(h.api.importConfig('{"version":9}'), /version/);
    assert.equal(h.api.exportConfig(), before); assert.equal(h.calls.length, callCount);
    const failure = deferred(); h.readiness.set('wet', failure);
    const incoming = JSON.parse(before); incoming.room = 'wet'; incoming.style.preset = 'glass';
    const importing = h.api.importConfig(JSON.stringify(incoming)); failure.reject(Error('no room'));
    await assert.rejects(importing, /could not load/); await Promise.resolve();
    assert.equal(h.api.exportConfig(), before); assert.equal(h.hostRoom, 'library');
  });

  test('a valid config import restores room, marks and a constrained camera pose', async t => {
    const h = harness(t); await h.enter('library');
    const incoming = JSON.parse(h.api.exportConfig());
    incoming.room = 'wet'; incoming.style.preset = 'watercolor'; incoming.controls.speed = 9;
    incoming.pose = {position: [4, -5.1, 3], yaw: 0.4, pitch: 0.2};
    await h.api.importConfig(JSON.stringify(incoming)); h.shell.update(1 / 60, 2); h.advance(200);
    assert.equal(h.hostRoom, 'wet'); assert.equal(h.api.getState().room, 'wet');
    assert.equal(h.api.getState().style.preset, 'watercolor');
    assert.deepEqual(h.camera.position.toArray(), [4, -5.1, 3]);
    assert.equal(new URL(h.location.href).searchParams.get('room'), 'wet');
  });

  test('explicit song selection restores transport identity while room changes preserve it', async t => {
    const h = harness(t); await h.enter('library');
    await h.api.configure({song: 'other-song'});
    assert.equal(h.host.getSong(), 'other-song'); assert.equal(h.api.getState().song, 'other-song');
    await h.enter('wet');
    assert.equal(h.host.getSong(), 'other-song'); assert.equal(h.api.getState().song, 'other-song');
    const incoming = JSON.parse(h.api.exportConfig()); incoming.song = 'the-current'; incoming.room = 'store';
    await h.api.importConfig(JSON.stringify(incoming)); h.advance(200);
    assert.equal(h.hostRoom, 'store'); assert.equal(h.host.getSong(), 'the-current');
    assert.equal(h.api.getState().song, 'the-current');
    assert.equal(new URL(h.location.href).searchParams.get('song'), 'the-current');
  });

  test('unknown song imports reject before changing rooms or visual state', async t => {
    const h = harness(t); await h.enter('library');
    const before = h.api.exportConfig(), incoming = JSON.parse(before);
    incoming.song = 'missing-song'; incoming.room = 'wet'; incoming.style.preset = 'glass';
    await assert.rejects(h.api.importConfig(JSON.stringify(incoming)), /song|track/i);
    assert.equal(h.hostRoom, 'library'); assert.equal(h.api.exportConfig(), before);
    assert.equal(h.host.getSong(), 'the-current');
  });

  test('media selection remains distinct from explicit collection and source links survive export', async t => {
    const h = harness(t); await h.enter('library');
    const item = {id: 'bolas:source:4', title: '<strong>Archive source</strong>', sourceProject: 'bolas', sourceURL: 'https://example.org/source.mp4', filmId: 'source', frameIndex: 4};
    let eventRecord; h.api.events.addEventListener('world:media-selected', event => { eventRecord = event.detail.record; });
    h.shell.selected(item); assert.deepEqual(eventRecord, item); assert.equal(h.api.getState().collection.length, 0);
    h.document.getElementById('world-inspect-pin').onclick();
    assert.equal(h.api.getState().collection.length, 1);
    h.click(h.dockButton('Cabinet'));
    const entry = h.document.querySelector('#world-cabinet .entry');
    assert.equal(entry.querySelector('strong').textContent, item.title);
    assert.equal(entry.querySelectorAll('strong').length, 1);
    assert.equal(entry.querySelector('a').getAttribute('href'), item.sourceURL);
    assert.equal(JSON.parse(h.api.exportConfig()).collection[0].sourceURL, item.sourceURL);
  });

  test('disposal releases shell resources and restores borrowed host controls', async t => {
    const h = harness(t); await h.enter();
    assert.equal(h.borrowed[0].closest('dialog').id, 'world-settings');
    h.api.dispose();
    assert.equal(h.composer.passes.length, 0); assert.equal(h.scene.children.length, 0);
    assert.equal(h.document.getElementById('world-dock'), null);
    assert.equal(h.borrowed[0].parentNode, h.document.body); assert.equal(h.borrowed[1].parentNode, h.document.body);
    assert.equal(h.document.body.classList.contains('world-shell'), false);
    assert.doesNotThrow(() => h.shell.update(1 / 60, 10));
  });
}
