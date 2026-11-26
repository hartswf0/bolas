# SCION-TEKLE · Afewerk Tekle: leaded-light monumental glass. PAE-09, MESA CHIP

**Film:** `film.mp4` (960×540, 24 fps, H.264 + AAC, 24 s). **Rebuild:** `python3 build/render.py` (numpy, Pillow, scipy, ffmpeg).

## Thesis
One window, cut once, and **no piece of glass moves for 24 seconds.** The figures, the blow and the fallen pieces are all light passing through fixed glass.

- **The cutting.** A Voronoi cutting of about 4,970 pieces. It is finer where the story will pass (the glazier cuts knowing the score) and coarser in the dune and the wall.
- **The lead.** It draws the architecture (dune line, wall, lancet, sill, steps, floor joints) and sweeps calligraphically over the nave.
- **Each frame.** Every piece takes the light that most of it receives: the figure's colour, crisp by majority, or the backlight through its own pot colour. Its body texture and the lead never change.
- **The knight's pieces.** The knight is first a figure in the window's own blue glass. Where paint takes it, its pieces go dark, and pieces of the floor glass light up in the paint's colour.
- **The light.** The columns of light and the day curve are a light timeline over the same glass.

## Made of
- the cutting (`build/render.py`, `cutting()`);
- the figures as light (`build/figures.py`):
  - **Uncle Mesa:** a Black man in his sixties with a long white beard and gold-lensed round glasses, in a cream wide-brimmed hat, a white guayabera-style shirt with the MESA CHIP badge, khaki trousers and dark boots;
  - **the knight:** plates of silver, gold and red with a red glass sword;
- the sound: a breathing choir chord, bells at the events, glass chimes for each shot's pieces and a low bell for the fall.

## Repairs after critic round 1

- **Lead around the held poses.** The window is re-cut with lead around the poses where the figures hold: the knight in the window, Uncle Mesa aiming, lying and seated. When a figure is there, the lead draws it. When it has gone, the outline stays in the glass as the window's memory. This keeps the theorem, since the glass still never moves.
- **The face.** A large eye in the icon manner and a round gold lens of their own.
- **The visor.** Larger, and it swings further when the knight turns its head.
- **The first hit.** It is aimed at the shoulder.
- **The fall, the rise and the sit.** Acted: the knees give before he falls, and each move takes 6 frames or more.
- **The mirror floor.** Reflections are stronger.
- **A coda light.** It crosses the floor and lights the pieces as it passes.

**After round 2:**
- **The light draws the contour.** A ring of unlit glass is left around every lit figure, so dark glass draws the contour of every pose and not only the held ones.
- **The mirror.** The reflection in the floor is foreshortened, as seen from above.
- **The window remembers.** In the coda, the knight's outline glows in the empty window.
- **Two lenses** for Uncle Mesa.
- **The later shots** lie under the earlier ones on the floor.

**After round 3:**
- **Every held pose gets its own cut:** the knight on the pier, and Uncle Mesa holding his ground at 15–20 s.
- **The sword** is held high, off him, after he rises.
- **The empty window flashes** in each shot's colour.

## Measured (from this film's own label mask and pixels, `invariants.json`)

- **I1, events at time:** hold. turns_head 3.0→3.04, steps_out 4.5→4.62, draws 6.0→6.08, raises_gun 6.5→6.58, hit_1 9.5→9.50, knocked_down 12.2→12.42, gets_up 14.0→13.88, hit_2 15.0→15.00, hit_3 16.0→16.00, hit_4 17.0→17.00, hit_5 18.0→18.00, shatter 19.5→19.50, sits 22.0→22.04.
- **I2, out of the glass:** holds. Inside the window in 100% of frames before 4.5 s, outside it in 100% after 5.5 s.
- **I3, the pieces stay, in their colour:** holds. Hue held by shot: #2fd0d8 100%, #f2a83a 100%, #e85aa8 100%, #f2d04a 100%, #2a9a5a 100%, #d8342c 100%.
- **I4, the distance follows the score:** holds. 100% of 335 frames within ±15 %, r = 1.000.

## Judged, not measured
Whether the motion reads as glass and not as an LED sign, whether the figures keep their dignity at this piece size, and whether colour is the event.

## Known limits
At this piece size Uncle Mesa's face and glasses are only a few pieces of glass. His beard and hat read, but his face does not. The icon manner (large eyes, frontal faces) is not achieved: grisaille painting would be fired onto fixed glass and could not move.
