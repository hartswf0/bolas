# PAE-09 · MESA CHIP, handmade

One scene from the MESA CHIP game (make-photo/mesa), the knight in the sunken glass cathedral, made four times, each time from the bottom up by a different SCION swarm. This works the way PAE-02 (*The threshold, handmade*) does: hold the description and the score still and let each swarm build everything else. That means what the figures are made of, how they move, what the place is and what it sounds like.

## What is held still

**The ekphrasis** (`EKPHRASIS.txt`):

> Under the dune the floor is glass, and the light comes down in columns. Uncle Mesa comes down the steps. In a window of the canyon wall a knight of stained glass turns its head. It steps out of the window, whole, and draws a red glass sword. Uncle Mesa raises the six-shooter of paint. The knight comes on. He fires: the paint takes the knight's shoulder, and pieces fall and lie on the floor in his colour. The sword comes down and he goes down. He gets up. He fires again, and again, and again; the knight comes apart, piece by piece, and keeps walking. At the last shot it goes to pieces on the mirror floor, every shard still holding its colour. Uncle Mesa lowers the gun and sits on the lowest step. The light moves on across the pieces.

**The score** (`score/glass-knight-score.json`, made by `tools/score.py`):

- It is the game's own knight machine (`make-photo/mesa/mesa.js`, swarmStep) run once with fixed timings.
- It runs 24 s at 24 fps, 576 frames.
- Every frame gives Uncle Mesa's place and state, the knight's place, state and wholeness, the distance between them, and where the light is.

| t (s) | who | event |
|---|---|---|
| 3.0 | knight | turns its head |
| 4.5 | knight | steps out of the window |
| 6.0 | knight | draws the red glass sword |
| 6.5 | Uncle Mesa | raises the six-shooter of paint |
| 9.5 | Uncle Mesa | hit 1: the shoulder (12 % of the knight) |
| 12.2 | Uncle Mesa | knocked down by the sword |
| 14.0 | Uncle Mesa | gets up |
| 15.0, 16.0, 17.0, 18.0 | Uncle Mesa | hits 2–5 (13, 14, 15, 16 %) |
| 19.5 | Uncle Mesa | the last shot: the knight shatters |
| 22.0 | Uncle Mesa | sits on the lowest step |

Each shot has its paint: cyan, amber, pink, yellow, green, red.

**Who is in it:**

- **Uncle Mesa** is a Black man in his sixties with a long white beard and round glasses with gold lenses. He wears a cream wide-brimmed hat, a white guayabera-style shirt with the yellow MESA CHIP badge, khaki trousers and dark boots, and carries a six-shooter of paint.
- **The knight** is made of stained glass: silver, gold and red pieces, a red plume and a red glass sword.

## The invariants

These are measured from each film's own pixels. Every frame, the swarm hands over a label mask of what it drew (Uncle Mesa, the knight, the window's glass, the sword, the gun, the visor, and each freed piece by the shot that freed it) together with the picture. `tools/common.py` (`Meter`) then measures:

- **I1.** Every event happens at its time, ±0.25 s, and is found in the picture. How each event is found:
  - the head turn: the visor moves toward him;
  - the step out: the knight's centre leaves the window;
  - the draw: the sword appears;
  - the gun: it rises toward his shoulder;
  - the fall: his height drops below 62 %;
  - getting up: back above 85 %;
  - each hit: its first freed piece appears;
  - the shatter: the knight is gone;
  - sitting: his height drops below 80 %.
- **I2.** The knight comes out of the glass. Its centre is inside the window in every frame before 4.5 s, outside it after 5.5 s, and never anywhere else before 4.5 s.
- **I3.** Every freed piece stays on the floor to the end, in the paint colour of the shot that freed it. Each frame shows at least one piece per shot after it, and more than 60 % of each shot's pixels have that paint's hue and saturation, with brightness normalised, so the light moving over them does not count against them.
- **I4.** The distance between them on screen follows the score's distance. Both are normalised to their own range, and they must agree within ±15 % in more than 90 % of the frames from 5.5 s until the shatter.

The colour is read at exactly the label's own pixels. An earlier version resized the picture to the label's size and read one pixel off, which counted the edges of small pieces as floor. That was fixed in round 2, and every film was re-measured.

The numbers only show that the description survived. Whether a film is good is for an independent critic to say.

## The swarms

The four new SCION prompts are in `swarms.json`, and each swarm's folder has a `prompt.md`. Each prompt has the operator's eight sections and inherits the fifteen-point SCION doctrine word for word from `paeleo/scion/swarms.json`.

| | swarm | it builds the scene from |
|---|---|---|
| M1 | Afewerk Tekle | one leaded window, cut once; only the light moves |
| M2 | Lucasfilm Computer Division, 1985 | a hand-keyed skeleton under convex glass shards, a separate specular pass, motion blur, a rack focus |
| M3 | Djibril Diop Mambéty | torn paper cut from the game's own footage, stiff card puppets, a griot's cutting |
| M4 | Mœbius and Otomo | ligne claire, flat colour, cast shadow, light trails, a bloom before each break |

## Rules

- **Build from the bottom up.** Only the score, the ekphrasis and `tools/common.py` are shared, and `common.py` holds the measurement, sound primitives and the mux, but no drawing. Everything else (assets, figures, motion, place, sound design) lives in the swarm's own `build/`.
- **Rights.** Every picture source is made by this project: the swarms' own drawing code, or, for M3, the game's own stills and clips. Sound is synthesised. No outside footage or likeness is used.
- **Critics.** Each round is a fresh agent. It sees the film, this brief and the swarm's prompt, never the builder's notes or code, and returns PASS, REFERENCE STRONGER or INCONCLUSIVE with exact frames and a falsifiable repair.
