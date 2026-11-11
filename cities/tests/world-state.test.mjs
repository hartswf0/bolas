import test from 'node:test';
import assert from 'node:assert/strict';
import {DEFAULT_CONFIG, WORLD_SCHEMA_VERSION, STYLE_IDS, PAINT_IDS, ARCHITECTURE_IDS, normalizeConfig, createWorldStore, parseWorldURL, updateWorldURL} from '../world-state.js';

const rooms = ['library', 'wet', 'store', 'city-b1', 'observatory'];
const memoryStorage = () => { const data = new Map(); return {getItem: key => data.get(key), setItem: (key, value) => data.set(key, value)}; };
const makeStore = extra => createWorldStore({roomIds: rooms, initialRoom: 'library', initialSong: 's27-two-rooms', ...extra});

test('defaults are immutable and direct normalization accepts only the schema', () => {
  assert.equal(WORLD_SCHEMA_VERSION, 1);
  assert.equal(STYLE_IDS.length, 9);
  assert.ok(Object.isFrozen(DEFAULT_CONFIG.style));
  assert.ok(Object.isFrozen(DEFAULT_CONFIG.authored));
  assert.ok(Object.isFrozen(PAINT_IDS));
  assert.ok(Object.isFrozen(ARCHITECTURE_IDS));
  assert.deepEqual(DEFAULT_CONFIG.authored, {paint: 'auto', architecture: 'auto'});
  assert.equal(DEFAULT_CONFIG.navigation, 'walk');
  assert.equal(DEFAULT_CONFIG.style.preset, 'original');
  assert.equal(DEFAULT_CONFIG.style.outline, 0);
  const config = normalizeConfig({style: {preset: 'woodblock', lineWidth: 999, grain: -4, arbitrary: true}, controls: {speed: Infinity, sensitivity: NaN}, audio: {volume: 4}, injected: 'no'});
  assert.equal(config.style.preset, 'woodblock');
  assert.equal(config.style.lineWidth, 4);
  assert.equal(config.style.grain, 0);
  assert.equal(config.controls.speed, DEFAULT_CONFIG.controls.speed);
  assert.equal(config.controls.sensitivity, DEFAULT_CONFIG.controls.sensitivity);
  assert.equal(config.audio.volume, 1);
  assert.ok(!('injected' in config));
  assert.ok(!('arbitrary' in config.style));
});

test('patch merges known sections, tracks visits, resets a travelling pose and preserves song', () => {
  const store = makeStore();
  store.patch({style: {preset: 'ink'}, pose: {position: [1, 2, 3], yaw: 0, pitch: 0}});
  const changed = store.patch({room: 'wet', style: {grain: 0.7}});
  assert.equal(changed.style.preset, 'ink');
  assert.equal(changed.style.grain, 0.7);
  assert.equal(changed.style.lineWidth, DEFAULT_CONFIG.style.lineWidth);
  assert.equal(changed.song, 's27-two-rooms');
  assert.equal(changed.pose, null);
  assert.deepEqual(changed.visited, ['library', 'wet']);
  assert.equal(store.patch({room: 'missing'}).room, 'wet');
});

test('snapshots and subscriber snapshots cannot mutate the store', () => {
  const store = makeStore(), calls = [];
  const stop = store.subscribe(state => { calls.push(state.room); state.style.preset = 'glass'; });
  const snapshot = store.get(); snapshot.controls.speed = 999;
  store.patch({room: 'wet'});
  assert.equal(store.get().style.preset, 'original');
  assert.equal(store.get().controls.speed, DEFAULT_CONFIG.controls.speed);
  stop(); store.patch({room: 'store'});
  assert.deepEqual(calls, ['wet']);
});

test('persistence, reset and unavailable storage work without leaking previous configurations', () => {
  const storage = memoryStorage(), first = makeStore({storage});
  first.patch({room: 'wet', style: {preset: 'thread'}, controls: {invertY: true}});
  const second = makeStore({storage});
  assert.equal(second.get().room, 'wet');
  assert.equal(second.get().controls.invertY, true);
  second.reset();
  assert.equal(second.get().room, 'library');
  assert.equal(second.get().style.preset, 'original');
  assert.equal(makeStore({storage}).get().room, 'library');
  const unavailable = makeStore({storage: {getItem() { throw Error('disabled'); }, setItem() { throw Error('quota'); }}});
  assert.doesNotThrow(() => unavailable.patch({room: 'wet'}));
  assert.equal(unavailable.get().room, 'wet');
});

test('malformed, future, unsafe and wrongly typed imports are transactionally rejected', () => {
  const store = makeStore(), storage = memoryStorage();
  store.patch({room: 'wet', style: {preset: 'cyanotype'}});
  const before = store.exportJSON(), calls = [];
  store.subscribe(next => calls.push(next));
  const invalid = [
    '{oops', '[]', '{}', '{"version":2}', '{"version":"1"}',
    '{"version":1,"room":"missing"}',
    '{"version":1,"style":[]}',
    '{"version":1,"style":{"preset":"unsafe"}}',
    '{"version":1,"environment":{"stars":"false"}}',
    '{"version":1,"controls":{"speed":"7"}}',
    '{"version":1,"controls":{"speed":1e999}}',
    '{"version":1,"pose":{"position":[1,2],"yaw":0,"pitch":0}}',
    '{"version":1,"collection":[{"id":"x","sourceURL":"javascript:alert(1)"}]}',
    '{"version":1,"collection":[{"id":"x","sourceURL":"data:text/html,test"}]}',
    '{"version":1,"collection":[{"id":"x","sourceURL":"https://name:secret@example.org/"}]}',
    '{"version":1,"collection":[{"title":"missing id"}]}'
  ];
  for (const json of invalid) {
    assert.throws(() => store.importJSON(json), TypeError, json);
    assert.equal(store.exportJSON(), before, json);
  }
  assert.equal(calls.length, 0);
  storage.setItem('celluloid.world.v1', '{"version":9,"room":"wet"}');
  assert.equal(makeStore({storage}).get().room, 'library');
});

test('validated import clamps numbers, bounds collections and filters visited room IDs', () => {
  const store = makeStore();
  const entries = Array.from({length: 90}, (_, index) => ({id: `f${index}`, title: 'A film', sourceURL: 'https://example.org/film', sourceProject: 'bolas', frameIndex: 3.9, ignored: 'drop'}));
  const next = store.importJSON(JSON.stringify({version: 1, room: 'city-b1', song: 'another-song',
    style: {strength: 9, outline: -1, lineWidth: 0}, environment: {fog: 0, density: 5},
    controls: {speed: 99, sensitivity: -8}, audio: {volume: -1},
    pose: {position: [999999, 0, -999999], yaw: 7, pitch: 8},
    visited: ['missing', 'wet', 'wet'], collection: entries, ignored: true}));
  assert.equal(next.style.strength, 1); assert.equal(next.style.outline, 0); assert.equal(next.style.lineWidth, 0.5);
  assert.equal(next.environment.fog, 0.3); assert.equal(next.environment.density, 1);
  assert.equal(next.controls.speed, 16); assert.equal(next.controls.sensitivity, 0.2); assert.equal(next.audio.volume, 0);
  assert.deepEqual(next.pose.position, [100000, 0, -100000]);
  assert.ok(Math.abs(next.pose.yaw) <= Math.PI); assert.ok(next.pose.pitch < Math.PI / 2);
  assert.deepEqual(next.visited, ['wet', 'city-b1']);
  assert.equal(next.collection.length, 64); assert.equal(next.collection[0].id, 'f26');
  assert.equal(next.collection[0].frameIndex, 3);
  assert.ok(!('ignored' in next.collection[0])); assert.ok(!('ignored' in next));
  const restored = makeStore(); restored.importJSON(store.exportJSON());
  assert.deepEqual(restored.get(), next);
});

test('collection IDs deduplicate and tolerant patches discard unsafe source URLs', () => {
  const store = makeStore();
  store.patch({collection: [{id: 'x', title: 'old'}, {id: 'x', title: 'new', sourceURL: 'javascript:alert(1)'}, {id: 'y', sourceURL: 'https://example.org/y'}]});
  assert.deepEqual(store.get().collection, [{id: 'x', title: 'new'}, {id: 'y', sourceURL: 'https://example.org/y'}]);
});

test('prototype keys never enter state', () => {
  const store = makeStore();
  store.importJSON('{"version":1,"room":"library","__proto__":{"polluted":true},"style":{"__proto__":{"polluted":true},"preset":"ink"}}');
  assert.equal({}.polluted, undefined);
  assert.equal(store.get().style.preset, 'ink');
  assert.ok(!Object.hasOwn(store.get(), '__proto__'));
});

test('authored settings merge independently, persist and round-trip without altering overlay style', () => {
  const storage = memoryStorage(), store = makeStore({storage});
  store.patch({authored: {paint: 'riso'}, style: {preset: 'thread'}});
  const next = store.patch({authored: {architecture: 'helix', ignored: 'drop'}});
  assert.deepEqual(next.authored, {paint: 'riso', architecture: 'helix'});
  assert.equal(next.style.preset, 'thread');
  assert.deepEqual(makeStore({storage}).get(), next);
  const restored = makeStore();
  assert.deepEqual(restored.importJSON(store.exportJSON()), next);
  assert.deepEqual(restored.importJSON('{"version":1,"room":"library"}').authored, {paint: 'auto', architecture: 'auto'});
  assert.deepEqual(normalizeConfig({authored: {paint: 'unknown', architecture: false}}).authored, {paint: 'auto', architecture: 'auto'});
});

test('invalid authored imports reject the entire transaction before persistence or notification', () => {
  const storage = memoryStorage(), store = makeStore({storage}), calls = [];
  store.patch({authored: {paint: 'xray', architecture: 'reef'}});
  const before = store.exportJSON(), saved = storage.getItem('celluloid.world.v1');
  store.subscribe(value => calls.push(value));
  for (const authored of [null, [], 'woodblock', {paint: 'invalid'}, {paint: 1}, {architecture: 'unknown'}, {architecture: false}]) {
    assert.throws(() => store.importJSON(JSON.stringify({version: 1, room: 'wet', authored})), /authored/);
    assert.equal(store.exportJSON(), before);
    assert.equal(storage.getItem('celluloid.world.v1'), saved);
  }
  assert.equal(calls.length, 0);
});

test('world URLs round-trip explicit preferences without overwriting existing routes or transport', () => {
  const original = new URL('https://hartswf0.github.io/bolas/cities/?city=b1&look=paper&lens=watercolour&arch=reef&song=s27-two-rooms&extra=yes#film');
  const state = makeStore().patch({room: 'city-b1', mode: 'film', navigation: 'walk', style: {preset: 'woodblock'}, authored: {paint: 'cyanotype', architecture: 'helix'}, pose: {position: [1, 2, 3], yaw: 0, pitch: 0}});
  const url = updateWorldURL(original, state);
  for (const key of ['city', 'look', 'song', 'extra']) assert.equal(url.searchParams.get(key), original.searchParams.get(key));
  assert.equal(url.searchParams.get('lens'), 'cyanotype'); assert.equal(url.searchParams.get('arch'), 'helix');
  assert.equal(url.hash, '#film'); assert.ok(!original.searchParams.has('room')); assert.ok(!url.searchParams.has('pose'));
  assert.deepEqual(parseWorldURL(url, {roomIds: rooms}), {room: 'city-b1', mode: 'film', navigation: 'walk', style: {preset: 'woodblock'}, authored: {paint: 'cyanotype', architecture: 'helix'}});
  assert.deepEqual(parseWorldURL('https://example.org/?room=not-a-room&mode=bad&movement=bad&style=bad', {roomIds: rooms}), {});
  assert.deepEqual(parseWorldURL('https://example.org/?city=b1&look=paper&lens=ink&song=abc', {roomIds: rooms}), {authored: {paint: 'ink'}});
});

test('legacy links retain authored IDs while modern movement fields take precedence', () => {
  const parse = query => parseWorldURL(`https://example.org/?${query}`, {roomIds: rooms});
  assert.deepEqual(parse('walk=1&lens=woodblock&arch=reef'), {mode: 'explore', navigation: 'fly', authored: {paint: 'woodblock', architecture: 'reef'}});
  assert.deepEqual(parse('walk=1&mode=film&movement=walk'), {mode: 'film', navigation: 'walk'});
  assert.deepEqual(parse('walk=1&mode=film'), {mode: 'film', navigation: 'fly'});
  assert.deepEqual(parse('walk=1&movement=walk'), {mode: 'explore', navigation: 'walk'});
  assert.deepEqual(parse('walk=1&mode=bad&movement=bad&lens=bad&arch=bad'), {});
  assert.deepEqual(parse('walk=0&lens=none&arch=auto'), {authored: {paint: 'none', architecture: 'auto'}});
  assert.deepEqual(parse('lens=0'), {authored: {paint: 'none'}});
  assert.deepEqual(parse('lens=21'), {authored: {paint: 'cyanotype'}});
  const original = new URL('https://example.org/?lens=xray&arch=reef&walk=1&other=value#source');
  const url = updateWorldURL(original, makeStore().get());
  assert.ok(!url.searchParams.has('lens')); assert.ok(!url.searchParams.has('arch'));
  assert.equal(url.searchParams.get('walk'), '1'); assert.equal(url.searchParams.get('other'), 'value'); assert.equal(url.hash, '#source');
  assert.equal(parseWorldURL(url, {roomIds: rooms}).navigation, 'walk');
  const partial = updateWorldURL(original, {authored: {paint: 'none'}});
  assert.equal(partial.searchParams.get('lens'), 'none'); assert.equal(partial.searchParams.get('arch'), 'reef');
});
