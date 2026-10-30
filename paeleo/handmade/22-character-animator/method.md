# SCION 22 · Adobe Character Animator, live performance capture: the threshold in felt

## The swarm, and the honest state of "live"

Character Animator's language is a layered puppet (named Photoshop-style groups) with behaviours attached to it. A webcam
and a microphone drive those behaviours, and a take editor records the result as takes. **Here there is no camera, no
webcam landmarks, no microphone performer, and no Adobe software.** So I built the parts of that language that do not need
them, and I say on the end card what is missing:

- a small **puppet runtime** (`build/rig.py`) with the behaviours: **Lip Sync** (visemes from audio), **Triggers** (held swap
  and pose beats), **Head & Body Turner** (swap sets for views), **Eye Gaze** (snap gaze to named targets, 2-frame saccades),
  **Auto Blink**, **Breathe**, **Dangle** (verlet chains: both dog ears, the tail, the person's ponytail, with floor
  collision), **Walk** (feet planted from distance travelled) and **Limb IK** (front leg shoulder-elbow-wrist, hind leg
  hip-stifle-hock-paw);
- **takes** (`takes.json`): timed control tracks layered like Character Animator takes, where a later take overrides only the
  parameters it records. Take 1, *capture*, is the PAELEO machine's continuous dog performance (the score's `act` tracks,
  verbatim). It stands in for what a live capture would give. Takes 2 to 5 (triggers, head & body turner, eye gaze, person)
  are the take editor's gated beats on top. The editor's corrections to the capture are listed in `takes.json`. This is the
  prompt's live/processed pair: continuous response vs. gated beats.
- the **person's mouth** is driven by the actual voice track. `build/voice.py` synthesizes the voice (cascade formant
  synthesis with a Rosenberg glottal pulse; no TTS engine and no recording). `build/visemes.py` then reads **only the audio**
  (RMS, voicing by autocorrelation, high-band ratio, and band-energy openness/frontness/centroid standing in for F1/F2) and
  picks one of 12 Character Animator visemes per frame, with a 2-frame minimum hold (`puppet/visemes.json`).

Roles were merged: I was the puppet rigger, input/calibration engineer, scene director and take editor. **No independent
critic has run yet.** I have not approved this work. That verdict belongs to the critic.

## What the dog is made of and how it moves

The dog is a **layered felt puppet**. Each layer is a felt cut-out: a fibre texture synthesized here, a fuzzy cut edge, a soft
drop shadow onto the layers beneath, and a running stitch on the larger pieces (`build/felt.py`). The set is a felt board
in the same material. Named groups (full list in `puppet/puppets.json`): `Dog/Body/<view>/Torso|Saddle|Bib|Haunch|Shoulder`,
`Dog/Legs/FN|FF|HN|HF/+Paw`, `Dog/Neck/Collar/Tag`, `Dog/Head/<view>/Skull|Cap|Muzzle|Nose|Mouth|Eye/White|Iris|Pupil|Glint|Blink|Brow|Ear near|Ear far`, `Dog/Tail/Tip`.
**Swap sets:** body Side / Quarter (rear three-quarter) / Back, mirrored; head Profile / QFront / QBack / Back. The turner
**cuts** between drawings and never tweens them, so a turn never squashes or ghosts. Both body turns pass through the Back
view, so the dog shows its back while it turns. The head leads the body in both turns. At 7.46 the head comes round through
QFront (face to the camera) and settles over the shoulder toward the door while the body is still lying. The dog rises at
7.6–8.05 and the body follows at 8.02–8.56. The **look-in** (26.42–28.40, held 26.8–28.0) is a swap to the QBack head: the
back of the skull and both ears face the viewer, and the muzzle points into the lit room. The neck reaches forward, with
the muzzle measured at x = −0.16 m, well inside the wall's inner face at 0.34 m. A lit inner hall doorway gives the room
depth, and the person draws her hand back to her lap as she says *come in*, so the look cannot be read as a look at her.

## Protected (measured from my render; `trace.json` summary)

- Choices, measured on the render's silhouette and head pieces vs. the score: retreat 1.208 (+0.21), stops 2.458 (+0.13),
  refuse (head starts away) 3.50 (+0.08), turns back to look (head moves) 7.417 (−0.04), approach 14.708 (0.00), lie down
  23.875 (+0.08), looks in 26.292 (−0.11). The checker's I1–I4 report **ALL OK**: r = 0.999 on `x_world_measured`
  (the camera pushes in from 14.6 s, so the dog's world x is measured by inverting the camera on its silhouette centroid),
  refusal back turned on 91.8% of refuse frames, min x 0.59, ends at 0.59.
- Head below the back line on 100% of approach frames. This is a rig-geometry measure (head pieces' top vs. the back line),
  not a pixel measure.
- Lying across the sill: 37% of the final silhouette lies inside the wall line and 45% outside. The tail is outside.
- Soft voice is 10.4 dB below the calls and 20.1 dB above the room tone (`build/cache/levels.json`, copied in assets.json).

## What failed and what I changed (detail in ledger.jsonl)

- LPC found harmonics, not formants, and the first sin² glottal source was muffled. I switched to a Rosenberg pulse and a
  band-energy classifier.
- The ponytail read as a cap brim, and the head on the approach was not clearly low. I retuned the dangle and moved the
  low-head pivot down.
- At 7.46 the head still faced away, and the tucked tail dangled through the boards. I moved the turner keys earlier and
  added floor collision.
- The look-in pointed at the offered hand. I moved the person back, added the hall depth, extended the neck and withdrew
  the hand.
- The film came out 1024 wide because the card was a bare fibre tile. I fixed the card and forced 1280×720.

## Still weak / not done

- Lip sync was verified only as a viseme sequence and on frames. I cannot listen here. The synthesized voice is intelligible
  only as far as a formant synth can be. There is one false M on the *l* of "all".
- The person's mouth is small in the wide shot (about 15 px), so lip sync reads best after the push-in.
- The Eye Gaze pupils are small in the wide shot. The dangle reads clearly on the tail and ears in the turns and the walk,
  less clearly when the dog is still.
- The hind leg in the crouch is a stylised felt fold, not anatomy. The Quarter body view appears for only a few frames per turn.
- I did not record a live take, use a webcam or landmarks, or render the "two versions" proof (live vs. postcorrected) as a
  film. The comparison exists only as tracks (Take 1 vs. Takes 2–4) in `takes.json`. There is no operator page.
- Kit and archive materials are unused. Everything is drawn or synthesized here.
