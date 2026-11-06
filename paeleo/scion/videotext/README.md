# VIDEOTEXT

**The game** is the film itself: `index.html` opens `../contaminant.html?play=1`, the cinema cut's own renderer with you steering. A title screen teaches three verbs:
- **Swim:** tap, swipe, click, hold, or use the arrow keys or WASD. A stroke on the music's pulse goes faster.
- **Catch:** swim into a glowing frame and it plays inside the jellyfish. Tap the jellyfish to watch it full screen. The next frame must share something with the last.
- **Splice:** carry the frame to the sun to add it to your reel.

The sun's beam is the censor: a frame with a touch in it (a red dot) burns if you carry it through the light, and burned frames sink, so you dive for them. After 90 seconds your reel plays, cut on its matches. The music is a garden: your reel is its melody.

See [THEORY_OF_PLAY.md](THEORY_OF_PLAY.md), and the SCION instructions it follows: [interface](SCION_INTERFACE_THINKING_MACHINE.md), [ludic engine](SCION_LUDIC_ENGINE.md), [identity after Scher](SCION_IDENTITY_AFTER_SCHER.md), [title after Bass](SCION_TITLE_AFTER_BASS.md), [garden after Eno](SCION_GARDEN_AFTER_ENO.md).

**The editor (`editor.html`).** The same rules as an interface: write a cut as a sentence of shared features, a swarm finds every cut that obeys it, invariants check each one, and you sign the one the projector plays.

It is the first proof of [SCION — AGENT-FIRST ARCHITECT](SCION_AGENT_FIRST_ARCHITECT.md), applied to video editing, on the archive of the contaminant jellyfish film (`../contaminant.html`).

## How the editor plays

- **Write.** Tap features (glow, hand, door, person, animal, ground, body, up). Each word is one cut: the feature the shots on either side of it share.
- **Swarm.** Every cut through the fourteen archive shots that obeys the sentence is found at once and ranked by the contract.
- **Sign and play.** The projector plays the chosen cut. Inside each shot the camera travels from the feature it shares with the shot before to the feature it shares with the shot after, so each cut lands on the same point of the screen. With the censor on, a shot in which something is touched burns from the touch.
- **Commissions.** 1 Rhyme · 2 Censor's commission (five cuts, nothing burns) · 3 Paradiso (keep four touches) · 4 Whole archive (all fourteen shots in one cut) · 5 Blind spot (a planted mislabel passes every check; spot the touch on screen and pull the Breaker).

## The analysis it embodies

**BIOLOGICAL_ARTIFACTS_EXPOSED**
- *The timeline and playhead* are a ritual. The state change is an ordered list of source intervals joined at a shared feature; the scrubbed timeline exists because one person can see one moment at a time.
- *Render, then watch* is the hidden human bottleneck: a cut can only be judged at 1x, by one viewer.
- *The 100x failure point:* when agents produce a hundred candidate cuts, the bottleneck moves from cutting to viewing. Nobody can watch them all, so legacy review becomes either rubber stamp or refusal.

**AGENT_FIRST_ARCHITECTURE**
- *Atomic unit of state:* a clip with its joints (located visible features) and its evidence (is something touched, and where). Relations between clips are shared joints.
- *Concurrency and collision:* the source is immutable; candidates are independent paths through the joint graph, enumerated in parallel. There is nothing to lock.
- *Intent verification:* intent is a sentence plus a contract. Invariants checked on every candidate: each neighbouring pair shares the written feature; under the censor, no recorded touch.
- *Human residual role:* write the intent, sign one cut, and answer for what the censor burns.

**NEW_FAILURE_REGIME**
- *Correlated blind spot:* the same joint record generates the cut and checks it, so a mislabelled clip passes both. Commission 5 plants one. This happened for real in the film: an independent critic watching the picture caught a hand the record had not burned.
- *Accountability trap:* the signer answers for burned images they did not inspect. The projector shows "record" and "burned on screen" side by side so the gap is visible.
- *Hard-invariant circuit breaker:* the Breaker halts playback, quarantines the cut and corrects the label; it is tripped on purpose in commission 5.

**THE_OPPORTUNITY_WEDGE** (claims, not measurements)
- *Obsolete cow-path category:* the per-seat timeline editor, which sells faster scrubbing of one cut at a time.
- *The Scion equivalent:* a joint-and-evidence graph over footage, an intent contract, and parallel enumeration with invariant checks; the editor becomes a sentence and a signature.
- *Incumbent's dilemma:* seat licences and timeline file formats are the revenue and the lock-in; an editor with no timeline undercuts both.

## Status

**The game (second version)** was measured by a scripted bot in headless Chromium:
- **1280×720:** finished all 14 frames in about 49 s.
- **844×390 touch:** finished all 14 frames in about 50 s; burns, rescues and tap-to-watch were all exercised.
- No page errors and no horizontal overflow.

No person has played this version yet.

**The editor:** commissions 1, 4 and 5 were completed by script, with no page errors. No independent critic has operated it.
