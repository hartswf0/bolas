# PAE-02 · SCION 47 · Sound-to-Action: method

## Thesis

The voice is the cause. Every choice the dog makes is scheduled on the exposure sheet from a sound event: the vowel that
carries a call, the end of a call, the first vowel of a soft line, the dog's own sniffing after a silence, its footsteps
stopping at the sill. Calls are loud and hard and push it away. Soft words are 16 dB quieter and draw its head round. The
long silence (11.5 to 14.2 s) is where it thinks: it looks at the low hand, looks up at the light, sniffs, and only then
comes. The film would go bland if the dog moved all the time, if the mouth flapped in silence, or if the sound were laid
on after the picture. Here the sound is made first and the picture is timed from it.

## The swarm (merged roles; one builder ran all of them; no agents were simulated)

| Role | Artifact it made | File |
|---|---|---|
| Sound dramaturg | typed audio timeline: where each line and world sound sits, and which answer it causes | `build/plan.py` → `build/audio_timeline.json` |
| Alignment engineer | the lines synthesized with CMU Flite; phoneme timing read from the synthesizer's own Segment relation | `build/voice.py` → `build/voice_lines.json`, `proof/alignment.png` |
| Mouth-shape designer | ten profile visemes for the person; the dog's sprite set (172 drawings exposed) | `build/person.js`, `build/dog.js`, `proof/dog_sprite_set.png` |
| Body-gesture choreographer | the exposure sheet: one dog drawing key, person pose and viseme per frame | `build/xsheet.py` → `build/xsheet.json` |
| Mix editor | synthesized foley and room tone, the mix, measured levels | `build/mix.py` → `build/audio_measure.json`, `proof/mix_levels.png` |
| Independent acting listener | **not run**: the builder may not approve its own work; a separate critic judges the film | none |

## Native formal language, as built

- **Audio events** (`audio_timeline.json`): typed records `{id, kind: voice|room|step|sit|touch|creak|cloth|sniff, src, t0, t1, x, causes}`
  on the scene clock (s, 0 to 32). Voice events carry words, phones and `cue_t`, the onset of the vowel the dog answers.
- **Phoneme timing**: from Flite's Segment relation (ctypes into libflite 2.2, voice cmu_us_slt). A first hand-written Viterbi
  aligner was rejected (`proof/alignment_rejected_viterbi.png`, `build/rejected_viterbi_aligner.py`).
- **Viseme sprite set**: X, MBP, AA, OO, EE, R, FV, L, TS, KG in profile (jaw rotation about a pivot, lip gap, rounding, pressed
  lips). Exposed on ones with a 40 ms lead and a minimum hold of 2 frames. The linguistic shape comes from the phone. Emotional
  emphasis is a separate scale: calls open the jaw fully, soft lines open it to 0.75 of that.
- **Expressive holds**: dog drawings are exposed on twos and held as the identical drawing. There is no boil and no
  interpolation. The refusal hold (5.1 to 7.4 s), the watching holds (8.7 to 12.3 s) and the final hold (28.6 to 32 s)
  are still drawings. Only a breath drawing changes, every 1.2 s.
- **Gesture accents**: the person pats a thigh on the stressed vowel of each early call. The dog cowers lower on the stressed
  "on" of "Come on!", its ears turn to the door creak (and nothing else moves: it hears and does not answer), it gives a low
  wag at "It's okay", and its tail knocks on the boards at "Come in".
- **Sonic perspective**: the microphone is the camera. Sources are panned by screen x. Calls are close to breaking (tanh
  drive), with porch reflections. Soft lines are low-passed and breathy. On screen, the voice is seen in two places at once:
  arcs at the person's mouth and arcs arriving at the dog's ear (heard there now, answered a latency later). The words are
  set in type as they are spoken: calls in heavy condensed capitals, soft words in small warm italic. No state of the dog
  and no choice name is ever printed.
- **Time base**: 24 fps; scene frame i is film frame 72 + i. Coordinates: x metres along the porch (score's), fixed
  orthographic camera, 180 px/m, camera tilt 16°. The dog is drawn 1.2× life size. This is a deliberate stylistic exception,
  so that its acting reads at 1280×720.

## How the dog is built and moved

**What it is made of.** Each drawing in the dog's sprite set is laid out from a 20-point pose guide (spine, neck, skull,
muzzle, ears, four legs of three bones, a three-segment tail) and inked in my own way. It is a union of spheres and tapered
capsules with a two-pass outline: every shape grown by the line width in ink, then filled. Groups are depth-sorted, so
outlines appear only where one part occludes another. A shepherd's dark saddle, cream bib and legs are clipped inside the
union and placed in 3-D, so they turn with the body (the saddle is what shows "the back" in the refusal). A drawing is
named by a discrete key (`yaw, hy, hp, ear, tl, wag, cr, lie, g, br, rs, sn, st`). The guide is never posed at render time.
The renderer only exposes the drawing the sheet names. The guide is a maquette used as a layout aid; what the viewer sees is
the drawn sprite and the selection between drawings.

**How it moves.** By substitution on an exposure sheet:
- **Walking**: 12 gait drawings per 0.55 m stride (a lateral-sequence walk, duty 0.62). The body is placed where the exposed
  drawing's planted feet are: a drawing changes only when the body has travelled one gait step, so planted feet do not slide
  (structurally verified by construction, not measured from pixels). Footfall sounds come from the drawings: a leg going
  from swing to stance is a nail click on the boards. Backing away plays the same walk in reverse.
- **Turns**: drawn through every intermediate view (side → three-quarter → rear → three-quarter away). The head leads the
  body. I looked at every drawing of both turns (contact sheets at 3.33 to 4.42 s and 7.33 to 8.75 s). Each reads as a dog
  seen from that angle, and none collapses edge-on. The turn-in-place drawings step the feet with a short stride.
- **Lying down**: the rear folds, then the front. Paws and lower joints move and the upper joint is solved by IK, so bone
  lengths hold. Lying is a sphinx pose with the forearms on the boards and the hind legs folded. There is no raised
  hindquarter.
- **Looking in**: the head turns 90° into the house (away from the camera): the back of the head and both ears are toward the
  viewer, against the lit doorway. The dog is drawn backlit there (darker, with a warm rim).

## Protected invariants: measured from the render

Measured on an ID pass drawn with the same sprites (flat colours: body, skull, muzzle, open mouth) and read pixel by pixel
(`build/measure.py`). Onsets are the first frame the drawing answers, by a detector fixed per choice. `trace.json`'s state
switches at these measured frames.

| Choice | Score t | Measured onset | dt | Detector |
|---|---|---|---|---|
| watch → retreat | 1.000 | 1.000 | 0.000 | drawing changes after the hold |
| retreat → watch | 2.333 | 2.250 | −0.083 | head rises ≥ 4 px |
| watch → refuse | 3.417 | 3.458 | +0.041 | drawing changes after the hold |
| refuse → watch | 7.458 | 7.458 | 0.000 | head moves ≥ 3 px |
| watch → approach | 14.708 | 14.750 | +0.042 | body moves toward the door ≥ 2 px |
| approach → lie down | 23.792 | 23.833 | +0.041 | body centroid drops ≥ 3 px |
| hears "come in" → looks in | 26.4 | 26.500 | +0.100 | head moves ≥ 3 px after 26.1 s |

Checker (`tools/paeleo/check_handmade.py`): **ALL OK**. I1 all six within ±0.25 s. I2: min x 0.59, end 0.59 (sill 0.56),
never inside. I3: r = 1.000 (x_screen vs score x, 768 frames). I4: 94.8 % of refusal frames show the back turned.

**Sound → action, measured** (cue time from the synthesizer's segments; answer from the render):

| Answer | Cause | Latency |
|---|---|---|
| backs away | vowel of "here" in "Come here!" | 0.170 s |
| turns its back | vowel of "here" in the second "Come here!" (with the reach) | 0.211 s |
| turns back to look | first vowel of "It's all right" | 0.170 s |
| looks in | vowel of "in" in "Come in" | 0.190 s |
| stops backing, lifts its head | the call stops sounding | 0.375 s |
| first step of the approach | its own third sniff, after 3.2 s of silence | 0.570 s |
| lies down | it has arrived at the sill (score x stops) | 0.125 s |

**Voice levels, measured on the stems** (RMS over voiced phones): calls −12.9 to −14.8 dBFS, soft lines −31.2 to −35.1 dBFS.
Soft is **16.4 dB below** the quietest call and **16.5 dB above** the room tone (−51.6 dBFS). Peak −1.0 dBFS.

**Lip-sync assertions, measured**: the open-mouth interior appears in 104 frames, **0 of them in silence** (more than 2
frames from any phone). **Every /m/ (5 of 5) shows a closed mouth** on the frames of the phone.

Frame counts: 768 scene frames; film.mp4 912 frames, 38.000 s, 1280×720, H.264 + AAC, faststart, about 2 MB.

## Looked at (perceptually judged by the builder; not an approval)

I looked at contact sheets of the whole film every 0.5 s and every 1 s, and at full-size frames at 0.83, 3.58, 3.83, 9.0,
19.0, 27.08, 28.0 and 29.17 s. I looked at crops of every drawing in both turns, both lie-downs and the rise, and at the
mouth frames 10 to 29 of the first call. These views produced the repairs in `ledger.jsonl`. I can see the mouth closing on
the m of "Come" and opening on the vowels. I cannot hear the film.

## What failed and what changed (see ledger.jsonl)

- The forced aligner I wrote misplaced vowels. I replaced it with the synthesizer's own phoneme timing.
- Sprite holes (polygon winding), eyes on the back of the head, and the muzzle drawn over the skull when pointing away: fixed.
- An accent head-duck was measured as the "stop and watch" rise. The accent now moves the body only. Answers that began one
  drawing late now move at the onset frame; an answer may land on a one.
- The dog disappeared into the lit doorway. It is now backlit with a rim.
- The lying look-in read as a giraffe neck. The neck is thicker and lower; the outline is smoothed (Catmull-Rom spine, grown
  capsule quads).
- Lie and rise passed through broken-looking legs. They now fold with IK.
- The paw clicks sat at room-tone level. They were raised 9 dB.

## Still weak (honest)

- The dog is small in a fixed wide shot (about 250 px long). The choices read at full size but are small in thumbnails.
- At the 3.6 s still the dog is mid-turn (three-quarter away, head turned). The full rear view arrives at about 3.75 to 3.9 s.
- Flite's voice is synthetic and flat. "Soft" is made by level, filtering and breath, not by an actor. Whether it sounds
  gentle is **unknown** to me.
- The person is simple: a profile figure with no turn drawing (a horizontally compressed front for 2 frames), and the face
  is small, so visemes are visible but tiny.
- The rise at 7.75 to 7.92 s is quick and a little awkward. The tail reads as a long straight stroke when it lies on the floor.
- The visible-sound arcs are a stylization. The dog reacts to the sound with a latency; the arcs are not physical
  propagation.

## Not done

- No independent critic run and no listening critique: the "acting listener" role is open. The verdict is pending.
- No human listened to the audio. No loudness standard (LUFS) was measured, only RMS on stems.
- Foot planting was checked by construction and by looking, not by a pixel measure of the feet.
- No footage, no Quick, Draw! drawings and no found-frame shots are used. The archive dog was looked at as a reference for
  type and markings only.
- No git, no commits. Nothing written outside this folder.

## Rebuild

`sh build/make.sh` (python3 with numpy and scipy, node 22 with Playwright Chromium, ffmpeg, libflite 2.2 with cmu_us_slt).
Intermediates go to `build/cache/` (regenerable).
