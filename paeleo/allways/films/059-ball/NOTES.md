# 059 · BALL

**Operator:** SCION 059 · Ball — Graphic Constancy Across Sources
**Runtime:** 40.2 s + 3 s source card · 640×480 · 24 fps
**Files:** `059-ball.mp4` (registered cut) · `059-ball-control.mp4` (unregistered control, same sources and order, each frame fitted to the screen) · `edl.json` built by `mk.py` · ledgers · `registration-check.json` · `contact.jpg`, `contact-control.jpg`
**Status:** proof in progress. Picture and timing were inspected by frame sheets, not watched at speed; the score was synthesised, not listened to. **Independent critic review: pending.**

## 1 · Theorem, adapted

One rim stays still at the centre of the screen while the thing it belongs to keeps changing: a sun, a planet, a lens, a clock, a dial, a shower rose, a speaker, a reel, a wheel, a jet engine. Continuity of form, instability of use. The registration is the film; the control cut shows what it adds.

## 2 · Forage log

The archive's text search cannot find a shape. The queries that returned these shots ("a mirror ball spinning", "first person view of hands on a steering wheel") describe scenes, and almost none of the "ball" hits contain a ball. So the forage was a **shape scan**: `tools/allways-forage/circles.py` ran a Hough circle detector over every local still (5,272) and one frame every 3 s of every local clip (405), scoring each circle by how much of its rim lies on real image edges. 3,443 still circles and 1,459 clip-frame circles came back. 108 had more than 70% rim support. I read the top 140 stills and 80 clip frames by eye (`ball_top.jpg`, `ball_clips.jpg` in the session scratchpad).

What came back, by use:

- **Sky and models:** a sun behind cloud (2007), a painted Earth (1984), a painted moon and Saturn (1965).
- **Looking:** magnifying glasses, three times, from two films 20 years apart: over a moon map, over a signature, over an eye (1947, 1967).
- **Measuring and time:** wall clock (1966), slide-rule dials (1950), gauge panels (1950, 1957, 1961), an octagonal clock (1944).
- **Machines and media:** a projector's reels (1958), a film reel (1948), a speaker grille (1929 cartoon), a jet intake (2007), a motorcycle wheel (1967).
- **The home:** a shower rose (1956), rolls on a plate, coins.

What surprised me:

- The **magnifier** recurs. Archive films keep showing someone looking through a circle, which is this film's own operation.
- The **circle that looks back**: the 1967 eye behind its lens.

**What the local cache does not have: a ball in play.** No bouncing, thrown or kicked ball survives in the 405 cached clips or in a still where the detector could hold it. The prompt's "object used in play" is met only obliquely, by a boy handling a film reel. The live archive certainly has balls; see the forage queue below.

## 3 · The cut

The target is the screen centre with a rim radius of 134.4 px (0.28 of the frame height). Every registered shot is translated and uniformly scaled, nothing else. Sound is a newly composed tap score (`score.wav`, from `mk.py`): one tap per 0.75 s beat, with a timbre for each material (sky low, glass high, metal ringing, plastic clicked, paper brushed, rubber bent). **No source audio is used**, because the cached tracks are narration and library music.

| # | t | shot | source | rim error (centre / radius px) |
|---|---|---|---|---|
| 0 | 0.0 | sun through cloud | *Sun Peeks Out From Behind Clouds*, 2007 | 4.5 / −1.1 |
| 1 | 3.5 | painted Earth | *Climate Factor*, 1984 | 4.9 / −2.3 |
| 2 | 5.75 | lens over a moon map | *Assignment: Shoot the Moon*, 1967 | 2.3 / 1.4 |
| 3 | 8.0 | lens over a signature | *The Twenty-Six Old Characters*, 1947 | 3.2 / 2.5 |
| 4 | 10.25 | lens over an eye | *Assignment: Shoot the Moon*, 1967 | 3.2 / −0.4 |
| 5 | 12.75 | wall clock, second hand moving | *Alaskan Earthquake*, 1966 | 22 / 3 (clip is 720×480; anchor slightly off) |
| 6 | 15.25 | slide-rule dial, BORON | *The Big Train (Part I)*, 1950 | 3.0 / −0.2 |
| 7 | 17.5 | **octagonal clock: the rim fails** | *Plastics*, 1944 | 14.6 / −29 (hand-set anchor; deliberately approximate) |
| 8 | 20.25 | **release:** whole frame, a hand turns a control beside the gauges | *Man and Space*, 1961 | unregistered |
| 9 | 23.7 | shower rose | *[Frigidaire Imperial Line]*, 1956 | 2.7 / −1.4 |
| 10 | 26.45 | speaker grille and a pointer | *Finding His Voice*, 1929 | 2.3 / 2.1 |
| 11 | 29.2 | film reel in a boy's hands | *Facts About Film*, 1948 | drifts ±25 px as he turns it (ellipse in perspective, hand-marked) |
| 12 | 31.4 | motorcycle wheel, running | *Cycle Logic, Cycle Safety*, 1967 | ≈8 px by eye (detector re-reads the hub) |
| 13 | 33.6 | jet intake | *Finale*, 2007 | 5.5 / 4.9 |
| 14 | 35.6 | **exit:** whole frame, a painted moon drifts out and leaves the stars | *Highlights 1965 (Part III)*, 1965 | unregistered; fade out |

Rim errors are re-measured on the rendered film (`regcheck.py`). The reel and wheel figures come from drawn overlays (`registration-check.json` shows that the detector locks onto hubs there).

**The omitted beat.** The beat is withheld at the release (shot 8): the gauge panel arrives in silence, and the hand that turns the control is the first thing in the film that *uses* a circle rather than shows one. Taps resume at the shower rose, slower, at 2.75 s and more per shot.

## 4 · Departures from the hard proof

- **Material.** Found archive stills and clips, not newly authorised photographs. Twelve images became thirteen registered plus two whole-frame shots, from 13 different films, 1929–2007.
- **Uses.** Wheel ✓, clock face ✓, play object only obliquely (a reel); the prompt's bowl becomes a shower rose and a speaker grille.
- **Images that move.** Several anchors are moving images (sun, clock, reel, wheel, jet), not stills. Registration is static per shot, so moving rims drift. The reel shows this most and is kept as an honest seam.
- **Resolution.** Sources are mostly 320×240 and are upscaled up to about 2.4×, which softens some rims.
- **Ending.** The circle leaves in "an original moving shot", but the shot is a 1965 *painted* space animation, not a photographed object.

## 5 · Self-review against §5 (not a critic verdict)

- **The anchor holds across the opening six transitions.** Measured: ≤5 px centre and ≤2.5 px radius error for shots 0–4 and 6; the clock is 22 px off.
- **Material differences survive.** Colour/black-and-white, painted/photographed and 1929/2007 all stay visible, because nothing is recoloured.
- **The irregular object is not corrected.** The octagon is left 29 px small in radius. The reel's perspective ellipse is left as it is.
- **The release changes the meaning.** Plausibly, but unverified. It is the only shot where a hand acts on a circle; the critic must judge whether that reads.
- **The ending is a clear exit.** The moon leaves an empty starfield, then the image fades.
- **Open risk:** at 2.25–2.5 s per shot the opening may read as a slideshow of circles (prompt §6, failure 1). The control cut exists to test exactly this.

## Forage queue (for when the archive is reachable)

Live searches to run against movingimagearchive.com's shot index for BALL v2: `a ball bouncing on a floor`, `children playing with a ball in a schoolyard`, `a baseball thrown toward the camera`, `a basketball dropping through a hoop`, `a bowling ball rolling down the lane`, `a mixing bowl seen from above`, `a dinner plate set on a table, overhead`, `a steering wheel turned by hands`, `a potter's wheel turning`, `a ball rolling out of frame`.
