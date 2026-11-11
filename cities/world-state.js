// Shared, renderer-independent state for the archive world. Room adapters own
// geometry; this module owns only validated, serializable visitor preferences.
export const WORLD_SCHEMA_VERSION = 1;
export const STYLE_IDS = Object.freeze([
  'original', 'woodblock', 'ink', 'doodle', 'watercolor',
  'graffiti', 'thread', 'cyanotype', 'glass'
]);
export const PAINT_IDS = Object.freeze([
  'auto', 'none', 'phosphor', 'set', 'silhouette', 'cave', 'embers',
  'circle', 'sun', 'card', 'bay', 'paper', 'worms', 'stencil', 'poster',
  'spray', 'ink', 'wash', 'watercolour', 'sumi', 'impasto', 'woodblock',
  'cyanotype', 'riso', 'xray'
]);
export const ARCHITECTURE_IDS = Object.freeze([
  'auto', 'grid', 'shell', 'reef', 'amph', 'kelp', 'helix', 'wheel', 'comb', 'table'
]);

const MAX_VISITED = 128, MAX_COLLECTION = 64, MAX_IMPORT_BYTES = 262144;
const own = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
const record = value => value !== null && typeof value === 'object' && !Array.isArray(value)
  && (Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null);
const clamp = (value, lo, hi) => Math.max(lo, Math.min(hi, value));
const clone = value => JSON.parse(JSON.stringify(value));
const freeze = object => { Object.values(object).forEach(value => {
  if (value && typeof value === 'object') freeze(value);
}); return Object.freeze(object); };

export const DEFAULT_CONFIG = freeze({
  version: WORLD_SCHEMA_VERSION,
  room: '', song: '', mode: 'explore', navigation: 'walk',
  authored: {paint: 'auto', architecture: 'auto'},
  style: {preset: 'original', strength: 1, outline: 0, lineWidth: 1, grain: 0.35, wobble: 0.15},
  environment: {stars: true, density: 0.65, constellations: true, fog: 1},
  controls: {speed: 6, sensitivity: 0.8, invertY: false},
  comfort: {reducedMotion: false}, audio: {volume: 0.8},
  pose: null, visited: [], collection: []
});

const SECTIONS = {
  authored: {paint: PAINT_IDS, architecture: ARCHITECTURE_IDS},
  style: {preset: STYLE_IDS, strength: [0, 1], outline: [0, 1], lineWidth: [0.5, 4], grain: [0, 1], wobble: [0, 1]},
  environment: {stars: 'boolean', density: [0, 1], constellations: 'boolean', fog: [0.3, 2]},
  controls: {speed: [1, 16], sensitivity: [0.2, 2], invertY: 'boolean'},
  comfort: {reducedMotion: 'boolean'}, audio: {volume: [0, 1]}
};

function invalid(strict, path) {
  if (strict) throw new TypeError(`Invalid world configuration: ${path}`);
}

function textValue(value, fallback, max, strict, path, nonempty = false) {
  if (typeof value !== 'string' || (nonempty && !value.trim())) {
    invalid(strict, path); return fallback;
  }
  return value.trim().slice(0, max);
}

function field(value, fallback, rule, strict, path) {
  if (rule === 'boolean') {
    if (typeof value === 'boolean') return value;
  } else if (typeof rule[0] === 'number') {
    if (typeof value === 'number' && Number.isFinite(value)) return clamp(value, rule[0], rule[1]);
  } else if (rule.includes(value)) return value;
  invalid(strict, path);
  return fallback;
}

function sourceURL(value, strict, path) {
  if (typeof value === 'string' && value.length <= 2048) {
    try {
      const url = new URL(value);
      if ((url.protocol === 'https:' || url.protocol === 'http:') && !url.username && !url.password) return url.href;
    } catch { /* An imported source must be an absolute web URL. */ }
  }
  invalid(strict, path); return undefined;
}

function collection(value, strict) {
  if (!Array.isArray(value)) { invalid(strict, 'collection must be an array'); return []; }
  const items = new Map();
  for (let index = 0; index < value.length; index++) {
    const item = value[index], path = `collection[${index}]`;
    if (!record(item)) { invalid(strict, path); continue; }
    const id = textValue(own(item, 'id') ? item.id : undefined, '', 160, strict, `${path}.id`, true);
    if (!id) continue;
    const result = {id};
    for (const [key, max] of [['title', 300], ['sourceProject', 160], ['filmId', 160], ['shotId', 160]]) {
      if (own(item, key)) result[key] = textValue(item[key], '', max, strict, `${path}.${key}`);
    }
    if (own(item, 'sourceURL')) {
      const url = sourceURL(item.sourceURL, strict, `${path}.sourceURL`);
      if (url) result.sourceURL = url;
    }
    if (own(item, 'frameIndex')) {
      result.frameIndex = Math.floor(field(item.frameIndex, 0, [0, 1000000000], strict, `${path}.frameIndex`));
    }
    items.delete(id); items.set(id, result);
  }
  return [...items.values()].slice(-MAX_COLLECTION);
}

function pose(value, strict) {
  if (value === null) return null;
  if (!record(value) || !Array.isArray(value.position) || value.position.length !== 3
    || !value.position.every(n => typeof n === 'number' && Number.isFinite(n))
    || typeof value.yaw !== 'number' || !Number.isFinite(value.yaw)
    || typeof value.pitch !== 'number' || !Number.isFinite(value.pitch)) {
    invalid(strict, 'pose must contain a finite position, yaw and pitch'); return null;
  }
  return {
    position: value.position.map(n => clamp(n, -100000, 100000)),
    yaw: Math.atan2(Math.sin(value.yaw), Math.cos(value.yaw)),
    pitch: clamp(value.pitch, -Math.PI / 2 + 0.01, Math.PI / 2 - 0.01)
  };
}

function normalize(input, strict = false) {
  if (!record(input)) { invalid(strict, 'expected an object'); input = {}; }
  if (own(input, 'version') && input.version !== WORLD_SCHEMA_VERSION) {
    throw new TypeError(`Unsupported world configuration version: ${String(input.version)}`);
  }
  const result = clone(DEFAULT_CONFIG);
  for (const key of ['room', 'song']) {
    if (own(input, key)) result[key] = textValue(input[key], result[key], 160, strict, key);
  }
  for (const [key, rule] of [['mode', ['explore', 'film']], ['navigation', ['walk', 'fly']]]) {
    if (own(input, key)) result[key] = field(input[key], result[key], rule, strict, key);
  }
  for (const [section, fields] of Object.entries(SECTIONS)) {
    if (!own(input, section)) continue;
    if (!record(input[section])) { invalid(strict, section); continue; }
    for (const [key, rule] of Object.entries(fields)) {
      if (own(input[section], key)) result[section][key] = field(input[section][key], result[section][key], rule, strict, `${section}.${key}`);
    }
  }
  if (own(input, 'pose')) result.pose = pose(input.pose, strict);
  if (own(input, 'visited')) {
    if (!Array.isArray(input.visited)) invalid(strict, 'visited must be an array');
    else {
      const visits = input.visited.map((id, index) => textValue(id, '', 160, strict, `visited[${index}]`, true)).filter(Boolean);
      result.visited = [...new Set(visits)].slice(-MAX_VISITED);
    }
  }
  if (own(input, 'collection')) result.collection = collection(input.collection, strict);
  return result;
}

// Direct settings calls are forgiving: invalid values fall back, finite numeric
// values clamp. JSON imports use the stricter validator below before committing.
export function normalizeConfig(input = {}) { return normalize(input); }

function mergeKnown(base, partial) {
  if (!record(partial)) return clone(base);
  const next = clone(base);
  for (const key of Object.keys(DEFAULT_CONFIG)) {
    if (!own(partial, key)) continue;
    if (own(SECTIONS, key) && record(partial[key])) {
      for (const fieldName of Object.keys(SECTIONS[key])) {
        if (own(partial[key], fieldName)) next[key][fieldName] = partial[key][fieldName];
      }
    } else next[key] = partial[key];
  }
  return next;
}

function roomSet(roomIds) {
  const ids = new Set(roomIds || []);
  if (!ids.size || [...ids].some(id => typeof id !== 'string' || !id || id.length > 160)) {
    throw new TypeError('createWorldStore requires valid roomIds');
  }
  return ids;
}

export function createWorldStore({storage, key = 'celluloid.world.v1', roomIds, initialRoom, initialSong = ''} = {}) {
  const allowed = roomSet(roomIds);
  const home = allowed.has(initialRoom) ? initialRoom : allowed.values().next().value;
  const baseline = normalizeConfig({room: home, song: initialSong, visited: [home]});
  let state = baseline;
  const subscribers = new Set();
  const filterRooms = (candidate, strict) => {
    if (!allowed.has(candidate.room)) {
      invalid(strict, `unknown room: ${candidate.room}`); candidate.room = home; candidate.pose = null;
    }
    candidate.visited = candidate.visited.filter(id => allowed.has(id));
    if (!candidate.visited.includes(candidate.room)) candidate.visited.push(candidate.room);
    candidate.visited = candidate.visited.slice(-MAX_VISITED);
    return candidate;
  };
  try {
    const saved = storage?.getItem(key);
    if (saved && saved.length <= MAX_IMPORT_BYTES) {
      const parsed = JSON.parse(saved);
      if (record(parsed) && parsed.version === WORLD_SCHEMA_VERSION) state = filterRooms(normalize(parsed, true), false);
    }
  } catch { /* Disabled storage or a stale/corrupt save must not block entry. */ }

  const get = () => clone(state);
  const commit = next => {
    if (JSON.stringify(next) === JSON.stringify(state)) return get();
    state = next;
    try { storage?.setItem(key, JSON.stringify(state)); } catch { /* Storage is optional. */ }
    for (const listener of subscribers) listener(get());
    return get();
  };
  return {
    get,
    patch(partial) {
      if (!record(partial)) return get();
      const incoming = mergeKnown(state, partial);
      // Invalid room selections leave the current room and its pose in place.
      if (own(partial, 'room') && !allowed.has(partial.room)) incoming.room = state.room;
      if (incoming.room !== state.room && !own(partial, 'pose')) incoming.pose = null;
      return commit(filterRooms(normalize(incoming), false));
    },
    subscribe(listener) {
      if (typeof listener !== 'function') throw new TypeError('A world subscriber must be a function');
      subscribers.add(listener); return () => subscribers.delete(listener);
    },
    reset() { return commit(clone(baseline)); },
    exportJSON() { return JSON.stringify(state, null, 2); },
    importJSON(text) {
      if (typeof text !== 'string' || text.length > MAX_IMPORT_BYTES) throw new TypeError('World configuration file is too large or is not text');
      let parsed;
      try { parsed = JSON.parse(text); } catch { throw new TypeError('World configuration is not valid JSON'); }
      if (!record(parsed) || parsed.version !== WORLD_SCHEMA_VERSION) throw new TypeError('World configuration must use version 1');
      const candidate = filterRooms(normalize(parsed, true), true);
      return commit(candidate);
    }
  };
}

const asURL = url => new URL(url instanceof URL ? url.href : url);

// The host resolves legacy look/city/song routing. Authored paint and city
// architecture are shared preferences, preserving their existing URL names.
export function parseWorldURL(url, {roomIds} = {}) {
  const params = asURL(url).searchParams, result = {}, allowed = roomIds ? new Set(roomIds) : null;
  const room = params.get('room');
  if (room && room.length <= 160 && (!allowed || allowed.has(room))) result.room = room;
  const mode = params.get('mode');
  if (['explore', 'film'].includes(mode)) result.mode = mode;
  const navigation = params.get('movement');
  if (['walk', 'fly'].includes(navigation)) result.navigation = navigation;
  if (params.get('walk') === '1') {
    if (!params.has('mode')) result.mode = 'explore';
    if (!params.has('movement')) result.navigation = 'fly';
  }
  const preset = params.get('style');
  if (STYLE_IDS.includes(preset)) result.style = {preset};
  const rawPaint = params.get('lens'), paints = PAINT_IDS.slice(1);
  const paint = /^\d+$/.test(rawPaint || '') ? paints[Number(rawPaint) % paints.length] : rawPaint;
  const architecture = params.get('arch'), authored = {};
  if (PAINT_IDS.includes(paint)) authored.paint = paint;
  if (ARCHITECTURE_IDS.includes(architecture)) authored.architecture = architecture;
  if (Object.keys(authored).length) result.authored = authored;
  return result;
}

export function updateWorldURL(url, state) {
  const next = asURL(url);
  if (typeof state?.room === 'string' && state.room && state.room.length <= 160) next.searchParams.set('room', state.room);
  if (['explore', 'film'].includes(state?.mode)) next.searchParams.set('mode', state.mode);
  if (['walk', 'fly'].includes(state?.navigation)) next.searchParams.set('movement', state.navigation);
  if (STYLE_IDS.includes(state?.style?.preset)) next.searchParams.set('style', state.style.preset);
  for (const [fieldName, parameter, ids] of [['paint', 'lens', PAINT_IDS], ['architecture', 'arch', ARCHITECTURE_IDS]]) {
    const value = state?.authored?.[fieldName];
    if (!ids.includes(value)) continue;
    if (value === 'auto') next.searchParams.delete(parameter);
    else next.searchParams.set(parameter, value);
  }
  return next;
}
