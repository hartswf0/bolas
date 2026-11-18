# Branch B: P8 staging repair (hypothesis B: the staging sets the gaze, not the head)

Start: checkpoint r1. Scope: only P8 and S8 are recomposed. The head piece, its collar hinge, H8 = -11 deg, the S8 key timing (head roll +2 to -11, the 4-pose arm rise, scratch, hold), the balloon text and every other panel stay as they were.

## Diagnosis (from looking, not from the build comments)

- The face in the Rothstein plate is cast down and near-frontal. A roll on the collar does not lift the eyes. It only slants the downward gaze. In r1 the P8 roll of -11 deg (top of the head to our left) slants it down and to the right.
- In r1, the fist and the pencil sat straight under that slant, at the panel centre. That is the P4/P7 arm silhouette, so readers took the hand as what he was looking at ("his wrist").
- The key sat at the far-left door edge. The balloon and empty door space lay between the key and him, so it read as "on the door, away from him".
- Side finding for the head branch, not acted on here: the r1 comment "head tipped up" is not what the picture shows. A negative roll on this un-mirrored face tips it further down. A positive roll, or a mirrored clerk with -11, would lift the chin. (The swap was tested in /dev/shm and is not used here.)

## What changed (branch-b/page/build_page.py, P8 only)

| | r1 | branch-b |
|---|---|---|
| clerk root (panel px) | P8_ROOT (640, 1150), kc 0.74 | **(500, 1290)**, kc 0.74 (left 140, down 140) |
| near shoulder to key | about 330 px, with the balloon between | shoulder edge directly under the key tag; key about 150 px from the head (less than one head-width, about 280 px); nothing between them |
| pencil hand | fist and pencil centred under the eyes | the fist falls below the panel's lower edge. The pencil comes UP into frame to the chin (tip to chin 16 px). Nothing sits in his down-right eye line. |
| what he faces (down-right) | his own fist | open space: the SERVICE leaf and the lamp socket. The ticket racks are above him. |
| balloon | top-left, at (390, 160), cap 62, tail across the face to the mouth | **right of his head** (890, 440), cap 52 so the 3 lines fit inside the border. The tail stops at his right cheek beside the mouth and **never crosses the face**. |
| key, hook, tag, door, SERVICE card | unchanged | unchanged (same hook, same pixels: the key never moves) |

S8 needed no key edits: the same timeline now plays over the new placement. The head rolls one way (+2 to -11) and the hand rises in 4 poses from below the frame, so the pencil enters the frame upward to the chin. Then the scratch and the hold. FK drift and rest identity are unchanged (editor checks pass: branch-b/editor_checks.json).

Everything protected by the critic is untouched and byte-identical outside P8 (page diff bbox = P8 only: x 1247-2395, y 2174-3146). That covers the 3/3/2 grid and hand-ruled borders, the lettering, P6 'Thanks!' exiting, the memo card, the S7 door swing with creak, the motionless SERVICE key, D1/D2 (read from assets/, not rebuilt), the high-key tone and the ledger card.

## Plumbing

- branch-b/page = copy of page/. penlib ROOT now resolves one level deeper. PAGE_OUT is branch-b/99-ways-template.png. Rest layers, speech and checks are written inside branch-b/page.
- branch-b/anim = copy of anim/ (strips/ dropped). It imports the branch page builder.
- branch-b/99-ways-template.py: anim, timing, sound and fk_test come from branch-b. Page B is the branch page. D1, D2, variants and coverage are read from the shared swarm (read-only). The film renders to branch-b/99-ways-template.mp4 (+ .webp).
- The disk volume was full during this round, with only a few MB free and taken by other processes. The render therefore used TMPDIR=/dev/shm/bb for kit's wav scratch.

## Rights fixes (branch-b/credits.json, notes.txt)

- **Blank sheet:** the repeated clause is removed. The licence is rewritten from the LoC Restriction and Notice Statement, read live on 2026-11-17. license_url is the item record. file_url is the tile.loc.gov IIIF image. The credit line is recorded.
- **MIA "Panama by Air (Reel 4)" (1914):** the licence now says it is public domain in the US by date only, with no archive licence statement read and the status not independently verified. license_url is US Copyright Office Circular 15A. license_note records the 403, the cached-metadata provenance, why author names the archive, and that MIA is outside BRIEF-2's list (it is the shared rules' primary source).
- **Six Commons PD sounds:** license_url is the file page's #Licensing section. A note says Commons gives no licence URL for 'Public domain'.
- **CC BY 3.0 train:** used_as now says "MODIFIED (excerpt 40-50 s, low-passed at 1.4 kHz ...)". Added `changes` and a ready-to-print `attribution` line.
- **notes.txt (106 words):** names the CC BY recordist and the changes. "the GrabCut cutouts" is now "cutouts cut by hand (GrabCut) from those photographs".

Not fixed here, because they are outside this branch's files and are for the operator:
- The literal Madden line is still quoted in plan.json (frozen bar), plan.md, proposals.md, amendments.md and checkpoints/r0/assembly.md. A-4 is pending.
- A-1 should also cover bubley.visitor.hi.json. B6 still names Wolcott (A-2).
- The film carries no on-screen credits, so CC BY attribution depends on the credits file being shown with the page.
