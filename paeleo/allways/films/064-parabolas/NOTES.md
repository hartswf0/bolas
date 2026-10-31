# 064-parabolas — Parabolas (etc.): Curves With Different Causes (found-footage draft)

Credit for the reference: *Parabolas (etc.)*, Will Hoffman and Derek Paul Boyle (2009, per the prompt's research record). The reference was not viewed.

Files:
- `edl.json` → rendered by `render.py` as **`064-parabolas-noguides.mp4`** (53.7 s, 4.1 MB): the film with **all guides removed**, plus `064-parabolas-noguides.ledger.json`.
- `guides/guides.py` burns model overlays onto *copies* of the frames of that render → **`064-parabolas.mp4`** (53.7 s, 3.8 MB, the annotated film; same audio and timing). `064-parabolas.ledger.json` is a copy of the no-guides ledger (identical source intervals).
- `guides/fits.json`: fit method, samples, coefficients, residuals and uncertainty for every displayed guide.
- `contact.jpg` (annotated version), `mk.py` (regenerates the EDL). Tracking/marking helpers are in `scratchpad/forms/` (`track.py`, `grid.py`, `zgrid.py`).
- Revision r1 (2026-10-31). Builder: forms.

**How it was checked.** I inspected contact sheets, 0.125–0.5 s frame strips, gridded zoom frames used for marking, and stills from the annotated render, and confirmed by eye that each guide sits on the source boundary it claims. I did not watch the film at speed or listen to it. Most of these sources are silent. **Independent critic review: PENDING.**

## 1 · Theorem, adapted
Curves recur across very different causes: a loaded line hanging from posts, a body in flight, a jet of water, a built arch. The film lets these resemble each other first. Afterwards it replays three of them with coloured **fitted models** whose quality differs:
- **A.** A pan-compensated diver's path: a quadratic-in-time model fits (rms 6.6 px against ±8 px marking error).
- **B.** A high dive filmed by a camera that tilts to follow: the same model fitted to the *screen* path draws a small hook that the diver leaves behind (rms 10.6 px). The screen path records the camera operator as much as the flight.
- **C.** A round-headed doorway: a parabola misses the rim by 4.0 px rms and 15–27 px on the held-out jambs, while a circle fits to 0.4 px. The arch is not a parabola.

The film ends on the unannotated clothesline.

## 2 · Forage log
- **Method.** I read all 405 clip and 474 loop contact sheets by eye. Query regex (`bridge|cable|chain|arch|fountain|throw|jump|…`) mostly returned irrelevant "architecture" hits.
- **Hanging lines:** clotheslines in *Health: Your Posture* (1953) and *Story of a City: New York* (1946). Both are oblique and loaded by laundry, and the sag is weak or hidden. Tower Bridge (1928 loop) shows only short, nearly straight side-span chains, and the bascules are moving. Golden Gate (*American Road*): the roadway view shows no main cable. Spider-silk strands (*Spider Engineers*, 1956) are taut and straight. **The archive has no clean free-hanging chain or cable profile.** I made no hanging-curve guide, because none could be honestly sampled.
- **Trajectories:** a run-and-dive at a pool (*Industry on Parade: Sylacauga Saga*); camera pans about 28 px during the flight. A tumbling platform dive (*Selected scenes…*, 1951); the camera follows him across a blank sky, so no compensation is possible. A high dive from a lattice tower (*Century of Progress*, 1933); the camera tilts and the 6+ s duration suggests slowed footage. A fire-hose jet (*Structure Protection*, 2003). There were no thrown balls or fountains with a static camera. Bouncing-ball loops (*Big Bounce*) are animation.
- **Arches:** a forward tracking shot into an arched Berlin station hall (*Berlin: Symphony of a Great City*, 1927). Per-frame automatic edge fits worked for only about 0.8 s before the arch leaves the frame, so that guide was abandoned. A **static** gallery shot with a round-headed doorway (*Miss Clark Introduces Panorama*, 1960) became guide C.
- **Surprising:** the most "parabolic-looking" thing in the archive, the doorway, is the one the parabola fits worst. The camera, more than gravity, shapes most archive trajectories.

## 3 · The cut (no retime, no mirroring; uniform scale only)
| t | shot | source (year), interval | evidence type |
|---|---|---|---|
| 0:00–0:07.6 | woman pegs a sheet on a clothesline | *Health: Your Posture* (1953) 24.0–31.6 | static outline, context |
| 0:07.6–0:12.6 | laundry strung between buildings | *Story of a City: New York* (1946) 0.5–5.5 | static outline, loaded |
| 0:12.6–0:14.8 | diver runs off the board, enters water | *Industry on Parade* (undated) 2.4–4.6, source sound on | moving trajectory |
| 0:14.8–0:18.4 | diver tumbles from platform, camera follows | *Selected scenes…* (1951) 0.3–3.9 | trajectory seen by following camera |
| 0:18.4–0:25.6 | high dive from lattice tower against clouds | *Century of Progress* (1933) 9.2–16.4 | trajectory, tilting camera, time base unknown |
| 0:25.6–0:27.7 | fire-hose jet over burnt slope | *Structure Protection* (2003) 12.3–14.4, source sound on | moving fluid / static shape |
| 0:27.7–0:31.45 | train enters an arched station hall | *Berlin* (1927) 0–3.75 | built arch, moving camera |
| 0:31.45–0:34.45 | round-headed doorway in a sculpture gallery | *Miss Clark Introduces Panorama* (1960) 0–3.0 | built arch, static camera |
| 0:34.45–0:36.45 | **replay + guide A** (blue) | *Industry on Parade* 2.6–4.6 | model overlay on tracked trajectory |
| 0:36.45–0:42.85 | **replay + guide B** (orange), departs | *Century of Progress* 9.4–15.8 | model overlay on screen track |
| 0:42.85–0:45.85 | **replay + guide C** (cyan parabola, magenta circle), doorway enlarged (k=6 source px → 3× the full view) | *Miss Clark…* 0–3.0 | model overlays on static outline |
| 0:45.85–0:50.65 | clothesline again, no guides | *Health: Your Posture* 27.0–31.8 | return |
| 0:50.65–0:53.65 | source card | | |

## 4 · Departures, and the guides
- The prompt's three original observations (hanging chain, tossed object, hand-bent strip with supports) were replaced by archival equivalents. The **bent strip has no equivalent**; the built arch stands in for a "shape held by a structure", and its supports (the jambs) are visible and held out of the fit. "Chain gently released" became the woman pegging and letting go of the sheet.
- **Guides are model overlays only.** They are drawn as thin lines and markers on copies of rendered frames (`guides.py`); the clean film is `064-parabolas-noguides.mp4`. Each annotated frame carries a small tag ("fitted model A/B", "fitted C") with the rms value. No narration claims a law.
- **A:** hip positions were marked by eye on 3× zoomed gridded frames at 3.1–3.6 s (6 samples, ±8 px). Camera translation came from phase correlation on the tree band (cumulative −25 px x, −13 px y). The model is x linear and y quadratic in t, fitted in background-registered coordinates and redrawn each frame with the current camera offset. Caveats: an extended diving body is not a point, and pan estimation drift is unmeasured.
- **B:** an automatic dark-blob tracker (local contrast vs a 12 px Gaussian background, compact components, nearest to the previous position, seeded at the diver) gave 139 samples. The same model was fitted in **raw screen coordinates**. I tried cloud-based camera compensation and rejected it as unreliable (vignette, low-contrast clouds). The departure is intended to teach that screen paths in following shots are not trajectories.
- **C:** 11 rim samples on the crown and 4 held-out jamb samples were marked by eye on a 6× gridded frame (the arch is only about 44 px wide in the source). The circle is an algebraic (Kåsa) fit; the parabola is y(x). The rim is a moulded or painted band seen slightly obliquely.
- The water jet got no guide (it is short, hand-held and nearly straight in frame).
- No physical constant is derived. 1930s footage may be slowed, and the 1933 dive's duration is not physically interpretable without a known time base.

## 5 · Self-review against §5
- *Family resemblance noticed before overlays:* the first 34 s carry no annotation and present line, flight, jet and arch in sequence. Untested with viewers.
- *At least one difference in cause visible:* load on a line, gravity on a body, pressure in a hose, masonry. Each is shown in context.
- *Guide mismatch teaches rather than looks like an error:* B departs with its own label. C shows two coloured models on the same marked samples with their rms values. Whether B reads as instructive or as a glitch is the critic's call.
- *Final unannotated image gains interest:* the return is the clothesline, the one curve family that was **not** fitted. This may read as an evasion. Note for the critic.
- *No physical law claimed from a 2-D outline:* yes. No text claims a law; `fits.json` says so explicitly.
- *Structural:* `fits.json` stores method, samples, coefficients and residuals for A, B and C. Guide coordinates map through the ledger transform (scale 2.0, offset 0 for A and B; register k=6 with the recorded offset for C). I checked the alignment visually on stills from the annotated render.
- **Largest unresolved limitation:** there is no clean hanging chain or cable in the archive, so the catenary/parabola question that defines the reference is not tested. Guide A rests on hand-marked points with ±8 px uncertainty.
- Critic verdict: **PENDING**.
