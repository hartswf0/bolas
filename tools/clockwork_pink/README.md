# A CLOCKWORK PINK · proof 0

The hard-proof scene for the SCION-GILLIAM reconstruction: one gesture, made as cut paper in code, with
picture and sound, before anything is scaled.

**The gesture.** A lid speculum holds an eye open under hard projector light. A bare hand lands on the lower
clamp, swivels it off, and the eye blinks for the first time. A forced gaze, released by touch.

**Reference, not source.** The Ludovico sequence in *A Clockwork Orange* (1971) was consulted as reference
only, from a 360p clip (speculum hold and eye close-up, roughly 90 to 130 s into it). No film frames, sound or
traced shapes are used here. The film is under copyright and is not redistributed. The hummed melody is the
first phrase of Beethoven's *Ode to Joy* (public domain), synthesized.

## Run

```bash
python3 tools/clockwork_pink/proof0.py OUT_DIR      # writes OUT_DIR/clockwork-pink-proof0.mp4 (11.5 s, 960x540, 24 fps)
python3 tools/clockwork_pink/check_proof0.py        # numeric invariants
```

This needs Python 3 with numpy and Pillow, and ffmpeg.

## Craft to code

| Tabletop action | Operator in `proof0.py` |
|---|---|
| pin | a piece held at fixed coordinates (the hold, frames 144 to 179) |
| slide | `clamp_*_y`, `hand_x`/`hand_y` stepped along a path |
| swivel | `swivel`: the hand and the clamp it holds rotate about the wrist |
| substitute | the pupil sizes and blink lids are swapped drawings, not tweens |
| expose | `pose()` samples on twos: 12 drawings a second on a 24 fps timeline |

Each piece has a fixed ragged cut edge (`ragged`, seeded per piece) and a lifted, blurred shadow. Cutouts are
rigid. They do not re-cut or boil between frames.

## Invariants (`check_proof0.py`)

1. Every pose holds for exactly two frames.
2. Nothing moves during the hold, and the lower clamp sits at the lid edge.
3. A fingertip rests on the lower clamp bar, and no fingertip lands on the eye.
4. Both clamps are clear of the lids by the end of the swivel.
5. The blink fully closes on at least one drawing.
6. The tear runs at least a quarter of the face card's height and lands before the bulb pops.

These checks do not judge whether the passage works. That is the critic's job, and the critic watches the
frames blind first.

## Critic record

- **Revision 0: reference stronger.** The hand was illegible (its charcoal smudges read as a face), it landed on
  the lid rather than the clamp, the flicker was a uniform wash, and the tear was invisible. Repair condition:
  in a still from the hold, a viewer names "a hand" and separate fingers; the fingertips overlap the clamp bar,
  not the lid; the clamp's motion starts where the fingers touch; a visible tear travels a quarter of the face
  card's height.
- **Revision 1:** open flat hand with separated fingers and nails, charcoal as thin streaks on the pads. Rest
  pose keyed backwards from the contact point. Speculum arms and screw knobs that rotate with the clamp. Hard-edged
  strobe spot instead of a wash. Larger tear at the outer corner, clear of the hand. The title no longer states
  the theme. The critic's review of this revision is pending.

Audio has not been judged by any critic. The review agents can see frames but cannot hear sound.
