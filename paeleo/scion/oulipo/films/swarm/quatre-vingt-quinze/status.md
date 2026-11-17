# quatre-vingt-quinze: status (r1)

## Current preview
- `assets/films/quatre-vingt-quinze.mp4`: 64.0 s, 1280x720, 24 fps, 3.88 MB.
- Poster: `.webp`, taken at 44.5 s.
- Page: `assets/pages/quatre-vingt-quinze.png`, 3360x2400. It is pixel-identical to r0.
- Reader cuts: `readers/*-only.mp4`, 35 s each.

## Decisive frame, 44.5 s
Checked side by side with the reference and kf-1 (`review-r1/side_44.5_kf1_ref.png`). This is the down route entering E from B: the down arrow is in the B/E gutter and the marks have long vertical arms.

**What E now does (measured from the exposure sheet):**
- 0–0.25 s: rest drawing, held while the camera travels.
- 0.25 s: anticipation dip.
- Four-drawing lift to the overshoot and glint at 0.58 s. It settles by 0.75 s.
- 0.50–1.67 s: the replacement head is the new `v_sky` drawing, with her face turned up toward the top edge of the panel (about 50° above horizontal).
- After that, back to `v_up` on the key, which is the page pose.
- A breath runs through the dwell.

Her head being up at 44.5 s is a fact of the drawing. In r0 status.md claimed it, but it was false then. This is identical on both routes: at 15.6 s across she looks up past the raised key.

**Bell tail under the balloon (film soundtrack, 1.6–1.85 kHz band):**

| Window (s) | Level (dBFS) |
|---|---|
| 44.50–44.75 | −32 |
| 45.00–45.25 | −36 |
| 45.50–45.75 | −41 |

E's clink is ducked to −48 dBFS full-band. Across E (15–18 s) is at −90 dBFS in the band, so it has no bell.

## Fixture
`adjacency-results.json` reports ALL_OK = true, re-run on r1.

## Open
- **B3 has not been re-run.** Fresh readers are needed, one per single-route cut (`readers/README.md`).
- Figures are about 55–65% of the panel height.
- The H stencil reads as abstract slabs.
- The amendment on sheet start still needs sign-off.

## Revisions
- r0: first build.
- r1: repair round 1 (`checkpoints/r1/`).
