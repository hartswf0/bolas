# SCION-MOEBIUS-OTOMO · Mœbius and Otomo: ligne claire with light trails. PAE-09, MESA CHIP

**Film:** `film.mp4` (960×540, 24 fps, H.264 + AAC, 24 s). **Rebuild:** `python3 build/render.py` (numpy, Pillow, scipy, ffmpeg).

## Thesis
Clean lines and flat colour make a strange world legible. Then the body is let go of its outline.

- **The line.** One black contour of constant weight: 2 px at film size, drawn at 2× and reduced.
- **The colour.** Fills are flat. The only darkness is cast shadow: every figure throws a flat sheared shadow away from the light.
- **The place.** A vast pale glass floor in bands, the dune overhead with round openings, flat columns of light (one moves with the score) and small figures.
- **Light trails.** Speed is drawn as light that stays behind: the sword's tip, the knight's leap out of the window, and every paint shot from muzzle to target.
- **The bloom.** Where paint takes the knight, each freed piece blooms first: its outline grows coral lobes for 0.22 s, then it splits off and falls. At the last shot the whole knight blooms at once.

## Made of
- **Uncle Mesa:** a Black man in his sixties with a long white beard and gold-lensed round glasses, in a cream wide-brimmed hat, a white guayabera-style shirt with a gold badge, khaki trousers and dark boots.
- **The knight:** panels of silver, steel, gold and red, with a red plume and a red glass sword.
- **The sound:**
  - a synth pad;
  - drums that come in with the gun and drive toward each break;
  - a zap for each shot, a rising shimmer for each bloom and a crash as the pieces let go;
  - a big drum and crash for the last bloom.

## Repairs after critic round 1

- **The mirror floor.** Every figure is reflected about its foot line: flat, lined, lower in value.
- **A coda light.** It crosses the pile, and the pieces brighten under it.
- **The pieces.** Each keeps a core of the knight's own glass under the paint, and the sword falls at its own scale.
- **The knight.** It strides, with the sword raised off him.
- **The fall and the rise.** Acted: the knees give first.
- **Uncle Mesa.** An eye, a nose, a round gold-rimmed lens, a long tapering beard, guayabera pleats and pockets, and a yellow badge.
- **The last bloom.** A push-in (19.54–20.1 s, not measured).
- **The hits.** Sharper, with glass chimes.

**After round 2:**
- **The push-in** stays inside the drawing, with no black bars.
- **The pieces** brighten under the coda light, scaled so they keep their hue.
- **The tracers** are wider and persist longer.
- **The knight has two legs.**
- **The scene** moves in from the left edge.
- **The badge** sits clear of the beard, and the pleats are darker.
- **The last shot's pieces** lie under the earlier ones.

## Measured (from this film's own label mask and pixels, `invariants.json`)

- **I1, events at time:** hold. turns_head 3.0→3.04, steps_out 4.5→4.62, draws 6.0→6.04, raises_gun 6.5→6.58, hit_1 9.5→9.50, knocked_down 12.2→12.42, gets_up 14.0→13.88, hit_2 15.0→15.00, hit_3 16.0→16.00, hit_4 17.0→17.00, hit_5 18.0→18.00, shatter 19.5→19.50, sits 22.0→22.04.
- **I2, out of the glass:** holds. Inside the window in 100% of frames before 4.5 s, outside it in 100% after 5.5 s.
- **I3, the pieces stay, in their colour:** holds. Hue held by shot: #2fd0d8 71%, #f2a83a 69%, #e85aa8 69%, #f2d04a 74%, #2a9a5a 63%, #d8342c 72%.
- **I4, the distance follows the score:** holds. 100% of 335 frames within ±15 %, r = 0.999.
- **Frames measured:** 562 of 576. The other 14 are inserts and re-tellings, listed in `trace.json` (`edl`); they are not the master geography.

## Judged, not measured
Whether every frame reads as a drawing, whether the trails show direction and speed, and whether the breaking is beautiful and frightening at once.

## Known limits
The figures are small and simple, close to stick-and-panel construction: Mœbius's hands, folds and faces are not attempted. The knight's panels are a regular grid, not a designed armour.
