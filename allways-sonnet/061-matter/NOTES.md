# 061-matter — Matter: Material Affordance Chain (found-footage draft)

Files: `edl.json` → `061-matter.mp4` (64.6 s, 4.7 MB, silent) + `061-matter.ledger.json`;
comparison cut `edl-alt.json` → `061-matter-alt-sourcesound.mp4` (same picture, source tracks on at −6/−14 dB) + ledger;
`contact.jpg`; `mk.py` regenerates both EDLs. Revision: r1 (2026-10-31). Builder scratch name: forms.

**How it was checked.** I inspected contact sheets and frame strips (0.25–1.5 s spacing) of every candidate, and a 1 fps strip of the render. I did not watch the film at speed, and I could not listen: sound decisions rest on RMS/modulation statistics only. **Independent critic review: PENDING.**

## 1 · Theorem, adapted to archive footage
One material behaviour leads to another through a transformation the viewer can see happen in the shot: pressure that springs back, a fold that stays, a liquid that spreads, metal and chocolate that pour and set, steel that curls when it is cut. The archive has no tabletop sample filmed under controlled loads, so each link is a separate documented action from a different film. The chain is built from **matching behaviours** (press / keep, pour / set, cut / curl), and the cuts between materials are offered as analogies, not as one specimen changing. The question the film leaves is which deformations return and which persist, and that question comes back when the opening pinch is shown again among the residues.

## 2 · Forage log
- **Method.** I made 8-frame contact sheets of all 405 clips and 5-frame sheets of all 474 loops (scripts in `scratchpad/forms/allsheets.py`) and read them all by eye. Query and regex searches (`press|fold|wet|pour|molten|knead|dough|cut|clay|melt…`) were nearly useless: the `queries` field describes what the archive search *wanted* (sand in hourglasses, glass towers), not what the shots contain. Every pick below came from looking at the frames.
- **Found (strong):** a skin-pinch demonstration (*Hydration*, 2004): a ridge lifts and sinks back. Lacquer poured onto a turning recording blank that spreads to a disc (*Command Performance*, 1942). Chocolate deposited from nozzles, each drop keeping a tail (*Great American Chocolate Factory*). A lathe chip curling off steel (*Industries of the U.S.: Steel*). A ladle pour of molten metal (*Master Hands*). Hands creasing a paper packet (*Gardening*, 1940). A hand pressing crumpled foil (*Moonwalk One*). Dye falling into water (untitled "food colouring clip").
- **Found but not used:** a pottery wheel (*POTTERY*, c.1926: the clay barely changes in the 8 s held), salmon filleting (2 s), a fizzing tablet dropped in water (*Welding Operator*, 1942; 3 s, cause unclear), a high-speed fuse/wire flare (*Fastax-tion*), a haircut (*Barbers*), a grinding wheel on plastic (*Plastics*, 1944), a sauerkraut-factory pour, glass windows already broken.
- **Surprising:** *Heat Treatment of Aluminum* (1990) contains an animated diagram of grains growing after heating. It is the only "memory in matter" image in the archive, and it is a drawing, not a micrograph.
- **What the archive does not have:** controlled before/after comparisons of one sample. Wetting that changes how paper behaves. Kneading (no dough found in any clip or loop). Close contact sound of any kind: the clips with sound carry narration or music that was added after filming.

## 3 · The cut (timecodes from the ledger; all `fit: cover`, no retime)
| t | shot | source (year) | why |
|---|---|---|---|
| 0:00–0:03.6 | skin pinched into a ridge, released, ridge sinks | *Hydration* (2004) clip 0–3.6 | pressure + recovery, the reference action |
| 0:03.6–0:06.6 | hands fold a paper packet | *Gardening* (1940) loop | fold that stays |
| 0:06.6–0:09.6 | hand presses crumpled metallised foil | *Moonwalk One* (c.1970) loop | pressure that does not spring back |
| 0:09.6–0:12.6 | dye falls and spreads in water | "food colouring clip" (undated) loop | wetting / spreading (the medium changes, not the solid) |
| 0:12.6–0:20.4 | lacquer poured on a turning blank spreads to a disc | *Command Performance* (1942) clip 0–7.8 | pour → coat, the cause in view |
| 0:20.4–0:23.4 | ladle pours molten metal | *Master Hands* (undated in index) loop | molten |
| 0:23.4–0:32.0 | chocolate deposited, drops keep their tails | *Great American Chocolate Factory* clip 5.2–13.8 | molten → set. **Analogy cut** from metal |
| 0:32.0–0:41.5 | lathe chip curls off steel and keeps the curl | *Industries of the U.S.: Steel* clip 6.0–15.5 | cut → persistent curl |
| 0:41.5–0:45.0 | heat-treatment furnace door | *Heat Treatment of Aluminum* (1990) 0.4–3.9 | context/cause for the next image |
| 0:45.0–0:55.0 | **animated diagram** of grain growth | same film 8.0–18.0 | "memory" of heat, explicitly a constructed image in its source |
| 0:55.0–0:58.6 | the same pinch again | *Hydration* 0–3.6 | return |
| 0:58.6–1:01.6 | 3×2 grid: pinch / fold / foil / lacquer / chocolate / chip, each live in its own source interval | as above | constructed side-by-side comparison of responses |
| 1:01.6–1:04.6 | source card | | |

## 4 · Departures from the hard proof, and why
- The prompt asks for original tabletop experiments with one paper sheet, weight, cloth and wetting. **None of this exists in the archive.** I substituted documented industrial and instructional actions from many films. Each claimed transformation is visible inside its own shot. The links between shots are analogies, and the source titles in the ledger keep the materials distinct.
- "Return to the dry sheet with the load moved": I could not restage anything, so the return replays the identical pinch. Its meaning changes only by position in the film. This is weaker than the prompt's design.
- The "weathered painted surface" analogy became the grain-growth diagram, which is a **simulated/diagrammatic** image. Its source film presents it as a diagram (line drawing). I placed the furnace shot before it so that heat is shown as the cause. It is not shown as a micrograph or as the furnace's actual load.
- **Sound.** The prompt asks for real contact sounds. The archive tracks are post-dubbed narration or music; I found no contact sound. The main cut is therefore **silent**, and the comparison cut puts the source tracks back in so a reviewer can judge whether they help. I did not hear either version.
- Running time is 64.6 s, longer than the 50 s target.

## 5 · Self-review against §5 (perceptual items are my reading of stills, not a viewing)
- *At least three material responses distinguishable:* likely yes (spring-back, crease, spread, pour/set, curl).
- *Each residue follows an action visible in its own scene:* yes for pinch, fold, foil, lacquer, chocolate, chip. For the grain diagram the cause is shown in the preceding shot of the same film, not inside the diagram.
- *Analogical cut does not masquerade as a physical transition:* metal → chocolate and furnace → diagram are cuts between visibly different films. A critic should test whether the metal→chocolate match reads as "the same stuff".
- *Sound communicates contact:* **fails.** The film is silent; this is the largest gap.
- *Last comparison changes the opening:* the grid puts the pinch (which returns) beside things that do not. Untested with viewers.
- *Structural checks:* every layer maps to source id, clip interval and film time in the ledger. Observed vs constructed status is written into each event `label` (OBSERVED / ANALOGY / CONSTRUCTED). No colour, speed or geometry transforms apart from uniform scale (grid cells).
- **Largest unresolved limitation:** there is no contact sound, and there is no single sample filmed before and after one action. The chain is a montage of documented responses, not one material's history.
- Critic verdict: **PENDING**.

## Critic round 1 and repair

See [../CRITIC-ROUND-1.md](../CRITIC-ROUND-1.md) for the verdict and the repair applied to this film. Shot tables above describe the cut before that repair; the current `edl.json` and ledger are authoritative.
