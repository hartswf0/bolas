# SCION-MAMBETY · Djibril Diop Mambéty: griot collage cinema. PAE-09, MESA CHIP

**Film:** `film.mp4` (960×540, 24 fps, H.264 + AAC, 24 s). **Rebuild:** `python3 build/render.py` (numpy, Pillow, scipy, ffmpeg).

## Thesis
The scene is told the way a griot would tell it: the clock is kept and the angle is broken.

- **Torn from the game's own pictures.** Everything is paper cut from the MESA CHIP stills and its two recorded clips (`build/footage.py`).
  - The backdrop is strips torn from five frames.
  - The figures are stiff cards. For each card the footage hunter cut the material from the frame whose colour and grain came closest, and logged it in `assets.json`.
- **Holds and jump cuts.** The master holds and jumps on a plucked rhythm of 2, 1, 1, 3, 1, 2, 1, 1, 2, 3 frames, and cuts on the frame at each event.
- **The walk** is two cards swapped on each hold.
- **Told more than once.** The first hit and the fall are each told three times: the master, then the same moment again in a closer crop, then again mirrored and closer, while the clock goes on underneath. The shatter is told twice.
- **Returning images** interrupt at decisions:
  - the zebu horns from the game's horned motorcycle, three times;
  - the sea, twice;
  - the kanaga, the game's own shatter and a mural, once each.
- **The ending.** It ends on the sea, in silence.
- **The grade.** Hot and worn: saturated and warm, with flicker, grain, scratches, dust and gate weave.

## Made of
- **Uncle Mesa:** a Black man in his sixties with a long white beard and gold-lensed round glasses, in a cream wide-brimmed hat, a white guayabera-style shirt, khaki trousers and dark boots, cut as seven cards.
- **The knight:** a card of 52 torn pieces of the game's silver, gold and red glass.
- **The sound:**
  - a Karplus-Strong plucked string keeps the teller's time over a street hum;
  - each shot arrives a little before its picture;
  - the fall is heard three times, as it is told;
  - a low horn sounds under the horns;
  - the street stops for the last silence.

## Repairs after critic round 1

- **The coda.** A close shot of the pile with a light crossing it, in the silence. The sea no longer ends the film.
- **The mirror.** A reflection in the floor of the action.
- **The horns take the paint.** Each return of the horns carries every colour fired so far, so the third return comes back painted in all six.
- **The step.** Drawn, with a lit edge.
- **The head turn.** The visor swings a third of the helmet.
- **The knight.** It strides, with the sword raised off him.
- **Uncle Mesa.** Two gold lenses, a yellow badge card, and khaki cut from a cleaner patch of footage.

## Measured (from this film's own label mask and pixels, `invariants.json`)

- **I1, events at time:** hold. turns_head 3.0→3.04, steps_out 4.5→4.58, draws 6.0→6.04, raises_gun 6.5→6.54, hit_1 9.5→9.50, knocked_down 12.2→12.29, gets_up 14.0→13.96, hit_2 15.0→15.00, hit_3 16.0→16.00, hit_4 17.0→17.00, hit_5 18.0→18.00, shatter 19.5→19.50, sits 22.0→22.00.
- **I2, out of the glass:** holds. Inside the window in 100% of frames before 4.5 s, outside it in 100% after 5.5 s.
- **I3, the pieces stay, in their colour:** holds. Hue held by shot: #2fd0d8 100%, #f2a83a 100%, #e85aa8 97%, #f2d04a 99%, #2a9a5a 100%, #d8342c 100%.
- **I4, the distance follows the score:** holds. 100% of 305 frames within ±15 %, r = 0.997.
- **Frames measured:** 495 of 576. The other 81 are inserts and re-tellings, listed in `trace.json` (`edl`); they are not the master geography.

## Judged, not measured
Whether the story survives the cuts, whether the inserts are motivated, and whether sound and picture disagree on purpose.

## Known limits
The figures are cut from the footage's colour, not from footage of people. The game's frames show Uncle Mesa mostly from behind, so the hunter took his materials (shirt, hat, skin, khaki) and the swarm drew the cards. The invariants are measured only on master frames. The re-tellings and inserts are left out of the measurement and listed with their times in `trace.json`.
