# Celluloid Cities: shared world contract, version 1

This is the integration contract for the existing Celluloid Cities renderer and
its exploration shell. The host keeps the existing film archive, jelly cast,
music and room geometry. Shared modules add movement, configuration, visual
styles and a navigable constellation layer.

## Integration boundary

The connected rooms are the scenes already built inside `cities/index.html`:
the library, video store, film depot, wet collection, data center, Orbit, experiment
spaces and Bolas/Cineosis cities, together with the constellation room. Their
stable IDs come from the host room registry. Existing city IDs have the form
`city-b1` or `city-1`; titles are display text, never lookup keys.

The Drifts, Real Jelly, Jelly Studio and other separate pages retain their own
renderers, clocks and interactions. Links to those pages are destinations, not
mounted rooms in this renderer. The present integration does not claim that
all legacy experiments share one runtime. Mounting a legacy experiment later
requires a lifecycle adapter and preservation of its media provenance and
existing gestures.

`cities/index.html` and `contaminant-jelly/bonus/jellyorchestra.html` began this
pass as copies with different branding and asset roots. Changes to this host
do not automatically update the other repository. The shared modules are a
route toward one implementation; a future core extraction should parameterize
branding and asset roots rather than maintain two modified copies indefinitely.

## Public host API

The host exposes an object with the following surface. Callers should depend
on this interface rather than the existing `window.__jo` debugging object.

```js
const world = window.archiveWorld;
world.version === 1;
world.rooms;                 // [{id, title, capabilities}, ...]
world.events;                // EventTarget
await world.enterRoom(id);
world.getState();             // defensive serializable snapshot
await world.configure(patch);
world.inspectCenter();       // use the current camera's center ray
world.openSettings();        // pause movement while configuring the world
world.collect(record);
world.exportConfig();         // versioned JSON string
await world.importConfig(text); // validate before applying
world.dispose();
```

Capabilities describe what a room actually supports. Expected names are
`explore`, `inspect`, `collect`, `media` and `style`; consumers must check a
capability before offering a corresponding action. A visual doorway and a
room-menu selection use the same `enterRoom(id)` operation.

`enterRoom` accepts a registered ID and resolves after its room transition is
applied. An unknown ID must not replace the current room. Entering a room
updates its selected state and visit history, releases held input, chooses a
valid spawn or saved pose, and changes room ambience. It does not restart the
current song. Pending room work must not let an older transition win after a
newer request.

`configure` changes preferences through the validated state store. Renderer
objects, event handlers, HTML and arbitrary executable expressions are not
configuration. `importConfig` must finish validation before making a visible
room, style or media change. `dispose` releases resources owned by the shared
shell and its modules; it must not silently dispose assets owned by an unrelated
legacy page. Full teardown of legacy inline render loops requires their own
adapter and is outside this initial integration.

## Events

Use `world.events.addEventListener(name, callback)`. Events are `CustomEvent`
instances with plain data in `detail`. Host-specific extra data may be added;
the named fields below remain the shared vocabulary.

| Event | Detail | Meaning |
| --- | --- | --- |
| `world:room-entered` | `{room, previousRoom, state}` | The selected room transition has completed. |
| `world:style-changed` | `{style}` | A validated style configuration has been applied. |
| `world:media-selected` | `{record}` | Inspection or selection resolved an archive item. |
| `world:error` | `{operation, message}` | A requested operation failed; the prior valid state should remain usable. |

An inspection is not automatically a collection action. Collection records
are copied into the user's bounded collection only by an explicit collect
operation. The UI renders source titles as text and uses validated source URLs
for links.

## Ownership inside a room transition

The host owns one renderer, camera, animation loop, input router, configuration
store and current audio transport. Existing `WORLD[id].build(group)` functions
and cached `WG[id]` groups remain the geometry source for this pass.

The transition sequence is:

1. Validate the destination ID and release captured movement input.
2. Suspend the prior room's interactive updates and select/build the destination.
3. Restore a valid pose or use its spawn; reset accumulated screen history when
   crossing a room boundary unless a transition deliberately retains it.
4. Apply global style, movement, environment and comfort preferences.
5. Update route/visit state, resume the destination and emit `world:room-entered`.

Room-local code must not create a second renderer, animation loop or AudioContext.
New adapters should expose `enter(context, savedState)`, `step(dt, context)`,
`inspect(ray)`, `serialize()`, `suspend()`, `resume()` and `dispose()` while using
host-owned services. These are adapter requirements for future extraction,
not claims that every old inline builder already implements those methods.

The host retains at most three city groups. Eviction marks a city disposed,
stops queued atlas loads from adding more work, and releases its owned geometry,
materials and textures. Shared film/video textures are preserved. Atlas uploads
are flushed by the active room instead of a per-city interval. Lighter existing
experiment groups remain cached. New asynchronous loaders must retain a
cancellation/generation token and cleanup function.

## Camera and interaction rules

`mode: "explore"` gives movement control to the visitor. `mode: "film"` gives
the camera back to the existing shot director. Exactly one owner applies
camera position, orientation, FOV, roll and shake during a frame.

`navigation: "walk"` is the default. `"fly"` is an explicit alternative;
entering an orbital or non-planar scene without a walking surface selects flight.
Configure mode is a UI state: opening a panel releases movement and prevents
typing, slider drags or touches on controls from steering the world. It does
not introduce a third serialized camera mode.

Dragging to look or steer must not trigger the canvas's existing click-to-rent
or inspect action on pointer release. Pointer cancellation, lost focus and
room transitions release held controls. Reduced motion disables optional
camera shake/roll and excessive animated mark jitter while keeping navigation
available.

## Configuration schema

`world-state.js` exports `WORLD_SCHEMA_VERSION`, `DEFAULT_CONFIG`, `STYLE_IDS`,
`PAINT_IDS`, `ARCHITECTURE_IDS`,
`normalizeConfig`, `createWorldStore`, `parseWorldURL` and `updateWorldURL`.
The store exposes `get`, `patch`, `subscribe`, `reset`, `exportJSON` and
`importJSON`. `subscribe` fires on changes and returns an unsubscribe function.

```js
{
  version: 1,
  room: "library",
  song: "s27-two-rooms",
  mode: "explore",
  navigation: "walk",
  authored: {paint: "auto", architecture: "auto"},
  style: {
    preset: "original", strength: 1, outline: 0,
    lineWidth: 1, grain: 0.35, wobble: 0.15
  },
  environment: {stars: true, density: 0.65, constellations: true, fog: 1},
  controls: {speed: 6, sensitivity: 0.8, invertY: false},
  comfort: {reducedMotion: false},
  audio: {volume: 0.8},
  pose: null,
  visited: ["library"],
  collection: []
}
```

| Value | Accepted range or IDs |
| --- | --- |
| Style preset | `original`, `woodblock`, `ink`, `doodle`, `watercolor`, `graffiti`, `thread`, `cyanotype`, `glass` |
| Authored paint | `auto`, `none`, `phosphor`, `set`, `silhouette`, `cave`, `embers`, `circle`, `sun`, `card`, `bay`, `paper`, `worms`, `stencil`, `poster`, `spray`, `ink`, `wash`, `watercolour`, `sumi`, `impasto`, `woodblock`, `cyanotype`, `riso`, `xray` |
| Authored architecture | `auto`, `grid`, `shell`, `reef`, `amph`, `kelp`, `helix`, `wheel`, `comb`, `table` |
| Strength, outline, grain, wobble | 0–1 |
| Line width | 0.5–4 |
| Star density | 0–1 |
| Fog multiplier | 0.3–2 |
| Speed | 1–16 |
| Sensitivity | 0.2–2 |
| Audio volume | 0–1 |
| Position coordinates | finite numbers clamped to ±100000 |
| Pose yaw | finite radians, wrapped to ±π |
| Pose pitch | finite radians, clamped just inside ±π/2 |

`authored` preserves the host's existing paint/lens and city-building choices.
`paint: "auto"` leaves the room's authored paint selection in charge;
`architecture: "auto"` retains the original city form. An explicit paint of
`"none"` disables the authored lens. These selections are independent of the
shared `style` overlay: for example, authored `"xray"` is the existing Glass
paint, while `style.preset: "glass"` selects the shared treatment. The original
renderer remains visible when the overlay is `"original"` with zero outline.
Version1 saves made before `authored` was added remain valid and receive both
`"auto"` defaults. Unknown enum values in an import reject the whole import.

A pose is either `null` or `{position: [x, y, z], yaw, pitch}`. Changing rooms
clears the previous pose unless a destination pose is explicitly provided.
Room IDs are checked against the registry; unknown visit IDs are removed.
Visits are deduplicated and bounded to 128 entries. Collection IDs are
deduplicated with the latest record retained, and the collection is bounded
to 64 entries. A song is an identifier of at most 160 characters; actual
playback time remains owned by the audio transport.

Direct partial updates merge known nested fields. Finite numbers clamp to
their allowed bounds; invalid direct field values fall back to defaults.
Unknown fields are ignored. JSON imports require a plain version1 object,
valid field types, valid enum values and a registered current room. Malformed
JSON, unsupported versions, non-finite values and unsafe source URLs are
rejected before any state is committed. Files over 262144 characters are
rejected. Imported valid finite numbers still clamp to supported ranges.

Persistence is optional and synchronous. Pass the browser's storage object to
`createWorldStore`; blocked storage, quota errors or corrupt saved data must
not block entry. The store's default key is `celluloid.world.v1`; this host uses
`celluloid-world.v1`. Reset restores the
host-supplied initial room/song and default preferences.

## Film provenance

A collected record uses this small portable shape:

```js
{
  id: "bolas:film:shot:frame",
  title: "A title from the archive",
  sourceURL: "https://example.org/original-film",
  sourceProject: "bolas",
  filmId: "original-film-id",
  shotId: "original-shot-id",
  frameIndex: 24
}
```

The state format requires `id`; the public collect action requires an `id` and
display `title`. IDs and project names are bounded to 160 characters,
titles to 300 and source URLs to 2048. Frame indices are nonnegative integers.
Source URLs must be absolute HTTP(S) URLs without embedded credentials. The
host resolves trusted archive-relative paths against their correct project
root before constructing a collection record.

The city builder already retains source information in `cy.FL`, `C.towers`,
`C.beats` and the original source links. Preserve these identities when making
a record. A new material or constellation representation must not replace a
film's provenance with a generated display title. Do not merge The Drifts'
`cj-reel` schema into this collection by guessing: its clips also carry frame,
duration, chapter and source-pattern information that needs a deliberate adapter.

## Routes

`parseWorldURL` reads explicit `room`, `mode`, `movement` and `style` parameters.
Valid legacy `lens` and `arch` IDs become `authored.paint` and
`authored.architecture`. Legacy `walk=1` supplies `mode: "explore"` and
`navigation: "fly"` only when the corresponding modern `mode` or `movement`
parameter is absent. A present modern parameter takes precedence even when
invalid; invalid values are ignored rather than activating legacy movement.
It does not guess a room from legacy `look` or `city`; the host resolves those
using its registry. `updateWorldURL` returns a new `URL` instance and preserves
unrelated query parameters and the hash, including `song`, `look` and `city`.
It writes authored selections to `lens`/`arch`, removing the corresponding
parameter for `"auto"`; a partial update without an authored field preserves
that parameter. The host updates legacy `look`/`city` values when entering a room.
The complete JSON export includes authored choices as well as overlay style.

`window.archiveWorld` owns serialized preferences and camera mode. Retained
`window.__jo` debugging hooks must delegate movement and configuration to that
owner rather than install another controller or independent settings store.

Full settings, collection items and camera positions are exported as JSON,
not encoded into an oversized share URL. An old link must continue to reach
its original room and media even after the visitor changes a new preference.

## Verification

Run the dependency-free state, navigation and style checks with Node22+:

```sh
node --test cities/tests/world-state.test.mjs cities/tests/world-navigation.test.mjs cities/tests/world-style.test.mjs
```

Run the complete suite, including the shell's asynchronous transition and
configuration tests, with:

```sh
npm --prefix cities/tests install --ignore-scripts
npm --prefix cities/tests test
```

The shell tests execute the real modules against THREEr160 and a LinkeDOM
document. Canvas drawing, dialogs, composer and archive host are explicit test
doubles. Passing these checks does not certify rendered appearance, audio
playback or physical mobile touch behavior. Those require a browser/device
review of the actual world.

They cover finite bounds, transactional rejection, persistence failures,
defensive snapshots, room filtering, collection limits, source URL safety,
prototype-key exclusion and preservation of legacy route parameters. These
checks do not establish shader appearance, frame rate, audio continuity or
real-device touch behavior; those require the host's browser validation.
