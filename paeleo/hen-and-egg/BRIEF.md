# PAE-04 · The hen and the egg: the brief

PAE-03 gave the oldest animation test (the 1930s flour sack: no face, no limbs, mood through weight and silhouette) a
decision to make. Its chronicle is the strongest cartoon narrative the lab has: a small body that **cannot stop the blade,
so it does the only thing its body can do**. PAE-04 keeps that chronicle and its score beat for beat and recasts it with
two characters taken from a diner breakfast menu: a hen standing on an egg, and a singing short-order cook in a cowboy hat
with a spatula and a fork.

The menu art is the **style reference only**. Nothing is traced or copied from it; the photographs are not stored in the
repository (the rights are unknown, and unknown is not permission). The hen and the cook here are new drawings made in
that manner.

## The style (the menu, described)

- **Two inks and a paper.** Deep teal-green (`#1f4b47`), tomato red (`#e2603e`), on warm cream stock (`#f2ebdf`), plus one
  warm grey (`#c9bcab`) for shadow halos. Nothing else. No gradients.
- **Screen-print, mid-century.** Flat shapes, a loose registration (the cream line work sits a pixel or two off the
  teal), and a **sprayed, speckled halo** behind the hero object (the red ring around the egg, the grey ring behind the
  spatula and fork). Shapes have hand-cut wobble.
- **The hen.** A round teal body with a scalloped tail fanned up, a cream spiral scroll for the wing, red tick marks on
  the breast, a scalloped red comb, a small red beak open in a cluck with three speed ticks, a **closed, lashed, happy
  eye**, one thin red leg with three toes. She stands on a big cream egg with teal speckles, on a little crosshatched
  nest of teal straw.
- **The cook.** A tomato-red ten-gallon hat with a teal band, a red bandana knotted at the throat, a teal shirt with
  cream piping and buttons, a cream face with closed eyes, a teal moustache and a wide singing mouth; music notes rise
  from him. He holds a slotted spatula and a fork crossed behind him, haloed in grey.

## The treatment (the North Star)

A hen sits small at the far end of a diner counter while the cook, singing, works a tall heap of straw with an egg
balanced on top, swiping slices off it with his spatula. The hen recognises the egg; she cannot stop the spatula, so she
does the only thing a hen can do: she holds the heap up, catches the egg when the heap falls, gathers the scattered straw
back into a nest where the heap stood, and stands on the egg. The cook comes back with his fork, finds a hen on the egg,
and goes back to his song.

It ends on the menu picture: the hen on the egg on its nest, clucking. The film is how that picture came to be.

**Energy arc.**
- Act 1 (0–9 s), staccato: the spatula comes down in hard, fast swipes; each swipe is a flinch; the hen is fluffed low and small.
- Act 2 (9–21 s), sustained: the hen crosses the counter slowly, head low, and leans her whole body against the leaning heap; she braces under the next swipe.
- Act 3 (21–32 s), surprising and inevitable: the heap falls, the egg is flung up, the hen leaps and catches it on her back, gathers the straw into a nest, sets the egg in it and stands on top. The fork comes, hovers, and withdraws.

## The chronicle (the ekphrasis to operate)

> A counter. Right of centre, a tall heap of packed straw, an egg balanced on its top. At the far left, a hen, fluffed low and small.
> The cook's spatula comes down and swipes a slice from the heap. Straw sprays. The hen flinches back. Therefore she watches; the spatula comes down again, on the other side, and she flinches again, less.
> The heap begins to lean. Straw sifts off its cut face. The hen's comb lifts; she stands tall. She recognises the egg. Therefore she comes, slowly, head low, across the counter, and stops against the heap's leaning side and leans her whole body into it, spreading her wing to hold it.
> The spatula comes down a third time. The hen braces and holds. Therefore it swipes a fourth time, on the far side, and the heap comes apart. The egg is flung up. The hen leaps, stretched long, and the egg lands on her back. She comes down hard in a squash, the egg still on her, in a spray of straw.
> She stays still. Then she gathers: she sweeps the scattered straw with her wing into a nest where the heap stood, sets the egg in it, and steps up onto the egg.
> The fork comes. It hovers over the hen. It withdraws. She clucks; he sings.

## The score (unchanged from PAE-03, 32 s at 24 fps)

Counter coordinates in metres, x = −2.0 to +2.0; the hen starts at x = −1.3; the heap stands at x = +0.8 (base radius
0.26, height 0.95 to the egg).

| t (s) | event (world) | the hen's choice |
|---|---|---|
| 1.00 | swipe 1 (left face of the heap) | **flinches** back (squash, hops left to x ≈ −1.5) |
| 4.00 | swipe 2 (right face) | **flinches** again, smaller |
| 6.50 | the heap starts leaning toward her, straw sifts off | **notices**: stands tall, comb up, eye open |
| 9.00 | | **comes**, head low, x −1.5 → +0.40 by 14.0 |
| 14.50 | | **props** the heap: breast and wing pressed into its leaning side |
| 18.00 | swipe 3 | **braces** (squashes, holds, does not retreat) |
| 21.00 | swipe 4; the heap collapses; the egg is flung up | |
| 21.40 | | **leaps** (stretched long) |
| 22.40 | the egg lands on her back | **catches** |
| 23.00 | | **lands** in a squash, egg still on her |
| 24.50 | | **gathers** the straw into a nest at x ≈ 0.8 |
| 30.00 | the fork hovers over her | **stays**, on the egg, still |
| 31.20 | the fork withdraws | (she clucks, he sings) |

## Invariants

1. The ten choices happen at their times, ±0.25 s, and read as choices on screen.
2. **Volume.** Through every squash and stretch the hen's body keeps its area (±6%). Straw is conserved: every strand
   that leaves the heap is in the air, on the counter or in the nest.
3. **Swipes push her away; circumstances bring her in.** The flinches go left; the approach starts only after the heap visibly leans.
4. She ends standing on the egg in the nest at the heap's place (x ≈ +0.8), and the fork leaves without touching her.
5. **No labels doing the acting.** No state names on screen during the scene. (Unlike the sack, the hen has a face; the
   face is part of the grammar here, so it must act with the body, never instead of it.)
6. **The menu grammar holds in every frame.** Two inks, cream, one grey; flat shapes; whole drawings swapped, not tweened.
