# Quatre-vingt-quinze: three proposed directions

**Reference.** `assets/references/extract-003.webp` is Lécroart's crossed page.
- It is a grid of four columns and five rows of ink-ruled panels on white paper.
- The panels are white or salmon-orange, with soft pools of light. The figures are big-nosed, and some are solid black shadows.
- The balloons and captions are hand-lettered in capitals.
- There are red barbed crossing marks in the row gutters, at the panel edges and between the columns.
- The title is lettered with alternate glyphs turned over.

**The stage, shared by all three directions.** The page grammar is kept and animated:
- A 3×3 grid of ink-ruled panels, white or salmon, with the red crossing marks in the row gutters.
- The title is lettered with every second glyph turned upside down.
- There is an id tab in each cell.
- The left margin rail shows the route being read: **II, en bas**, as a vertical list. The right margin shows route **I, en travers**, as a greyed 3×3 list because it has already been read.
- **The axis cue** is the crossing marks themselves. In the across reading their horizontal arms grow long and barbed; in the down reading the vertical arms do. The cue reads in grayscale and at thumbnail size.
- On each route, cells not yet read carry a paper wash. A red cut-paper arrow sits in the gutter of the transition being read.

**Hard proof, the same in all three.**
- **Cells:** A is the empty station ("PERSONNE ?"), B the bell ("DING ! DING !"), C the envelope opened ("UNE CLÉ ?"), D the shadow behind the service door, E the visitor lifting the key ("C'EST POUR MOI ?"), F the key left on the bench ("TANT PIS."), G "IL TIRE LA CORDE.", H the empty bench ("PLUS PERSONNE."), and I the service door, shut, with the key in its lock and "MERCI." spoken from behind it.
- **Across** (A B C D E F G H I) is the lost-key story. E follows D, so the line means "is this key meant for me?" She leaves the key, it vanishes, and the door keeps it.
- **Down** (A D G B E H C F I) is who set up the encounter. E follows B, so the same line means "is the bell ringing for me?" The man behind the door watched her arrive and pulled the rope.
- **Shared final cell:** I is the end of both routes.
- `kf.py` asserts the fixture:
  - Both routes are legal and each covers every cell once.
  - I is the shared last cell.
  - E's predecessor is D across and B down.
  - The text table is immutable, one entry per cell.

**Defining beat and clock.**
- **Timing:** title 0–3 s; across reading 3–30 s at 3 s per cell; the turn of the crossing marks 30–32 s; down reading 32–59 s; end card 59–62 s.
- **The beat:** all three keyframes stop at **44.5 s**, where the down route enters E from B. This is the second reading of the centre cell, where the latent meaning (she was summoned) shows.
- **Baseline:** the same nine cells read only across.
- **What the viewer should be able to point to:** "the same lady with the key, but this time the bell just rang for her."

**Builder.** `proposals/kf.py` is deterministic. Run it as `python3 -I kf.py /home/user/bolas/paeleo/scion/oulipo`. It also writes `board.jpg`: the reference beside the three keyframes, 1899 px wide.

---

## 1 · Ombres en croix: articulated shadow puppets on the grid (kf-1.png)

- **Material: all handmade.** The page, the lettering and the ruled borders are all made for this film. The figures are black cut-paper silhouette puppets in Lécroart's big-nose profile: a visitor in a cloche hat and a man in a peaked cap. The props are cut paper too: the bell on its bracket, a cream envelope, the key, the bench and the service door. In D, the man is seen only through the lit window, masked to the glass. There is no foraged image in it. Fonts: FreeSans Bold (GPL, with the font exception) and DejaVu Serif Bold (free licence).
- **Technique SCIONs:**
  - **2** Reiniger articulated shadow theater
  - **32** forward kinematics
  - **38** dynamic pose selection
  - **48** state machines, for the route
  - **8** constraint sketchpad, as the grid validator
- **How it moves, frame by frame, at 12 drawings/s on 2s:**
  - Every figure is an FK rig (hip, two-bone legs, two-bone arms, head tilt), drawn fresh each frame from its joint angles.
  - In E, the forward arm rises from rest to the lift over 12 poses (the keyframe is pose 7), the head turns up toward the bell, and the key catches a glint.
  - In B, the bell swings on its pivot in an 8-drawing cycle, with the clapper at about 1.9× the swing angle.
  - In D, the shadow slides across the glass. In G, the man's arm hauls down and the rope follows the wrist.
  - Only the cell being read animates. The others hold their last pose, the way a page holds still.
  - At 30–32 s every crossing mark turns its long arms from horizontal to vertical, drawn mark by mark.
- **Risk:**
  - The figures are geometric. Without hand-drawn line inside the shapes they can read as clip-art rather than Lécroart's pen.
  - The fix is to give the rig hand-drawn replacement heads and hands: a small drawing library, SCION 38.
  - Lettering is a typeface, not a hand.

## 2 · Collage de gare: photo cutouts in two inks (kf-2.png)

- **Material: foraged, then cut and printed in two inks** (black plus salmon on paper, the page's own palette). The sources are FSA/OWI photographs of Chicago Union Station (Jack Delano, 1943), from the Library of Congress. They are **public domain** (US government work; LoC: "no known restrictions"). The local copies come from `sources/la-machine-a-tuer-le-temps/`, and their licences were read by that film.

  | cell | photograph | LoC id |
  |---|---|---|
  | A, F, H | empty waiting room with benches | 2017843779 |
  | B, E (stage) | window wall with ceiling lamp | 2017843789 |
  | C | counter with papers | 2017843913 |
  | D | dispatcher behind his window | 2017844012 |
  | E | woman in fur, cut out on a hand-placed scissor line | 2017843935 |
  | G | conductor looking up | 2017844115 |
  | I | barred window | 2017844010 |

  - **The key** is `File:Skeletonkey.png` by Blenheimears (Wikimedia Commons, **CC0**), cut by density with its bow hole kept open.
  - **Handmade pieces:** the bell, the envelope and the bell rope.
- **Technique SCIONs:**
  - **1** Gilliam cutout metamorphosis
  - **3** Ernst collage grammar
  - **29** GrabCut cutout extraction, plus hand scissor lines
  - **34** ARAP and **35** MLS, for limb bends
  - **43** collage graph rewriting: the key changes owner cell by cell
  - **44** multiplane, for a slight parallax in E
  - **50** LoC historical print stage
- **How it moves:**
  - The cutouts are rigid paper pieces moved by per-frame affine keys, in Gilliam's style, at 12 fps.
  - In E, the woman's sleeve is a strip of her own fur coat, hinged at the shoulder. It rotates 0° → 34° over 12 frames (22° in the keyframe), and the key rides on the wrist.
  - The bell piece swings over the photograph. The conductor's rope piece is pulled down 3 frames per haul.
  - The key cutout physically moves between cells: from the envelope (C), to her hand (E), to the bench (F), to the lock (I). That cutout is the graph edge the two routes share.
- **Risk:**
  - The woman is photographed from behind, so she has no face or nose to letter to. The fur cutout reads as a texture at panel size.
  - The two-ink print flattens the FSA tones, and some panels (C, I) are busy for a comic cell.
  - I need a better visitor cutout: a woman in profile, also from FSA. The LoC API returned 503 last session and Commons returned 429 today, so no new search was possible.

## 3 · Neuf écrans: nine archive shots in the panels (kf-3.png), the archive-led direction

- **Material: foraged.** These are Moving Image Archive cache clips, with frames decoded with ffmpeg:

  | cell | shot | clip |
  |---|---|---|
  | A | *Berlin: Symphony of a Great City*, empty platform | b6e217eb |
  | B | *Communications and Our Town* (1947), belfry | 381d177e |
  | C | *Door to Heaven* (1941), a man at the door | 9199c819 |
  | D | *Door to Heaven*, the couple at the door | 6a336c56 |
  | E | *Key to Our Horizons* (1952), a hand at the lock | 7102b861 |
  | F | *Dating: Do's and Don'ts* (1949), a door ajar | a267fee7 |
  | G | *Wreckless* (1935), a man at the panelled door | ef7bfc89 |
  | H | *Amateur Film Children Playing Near Hudson*, empty chairs | 46cd8d58 |
  | I | *The Electric House* (1922), a closed door | bb5ffe06 |

- **Licences:**
  - *Wreckless* is **public domain**: Prelinger, re-read for la-machine-a-tuer-le-temps.
  - *Berlin* (1927) and *The Electric House* (1922) are very probably PD-US by date. Confirm on Commons.
  - **The rest are unverified.** The cache carries no licence field. Prelinger titles are usually PD, but each must be checked before any build.
- **Technique SCIONs:**
  - **53** civic footage performer
  - **26** archive stage rendering
  - **27** declarative film compiler
  - **8** constraint sketchpad
- **How it moves:**
  - Each panel plays its own clip only while it is being read, and holds its first frame otherwise.
  - The animation is in the page: the crossing marks turn, the gutter arrow steps cell to cell, and the paper wash lifts off each cell as it is read.
- **Risk:**
  - **Licences are unverified for six or seven of the nine clips.**
  - This is the least animated direction. Live footage in nine windows reads as a video wall rather than a comic page.
  - The shots don't share a cast. The visitor never appears and C never shows a key, so the across story has to be carried by the lettering alone, and E's double meaning is weakest here.

---

## Recommendation

**I recommend direction 1, *Ombres en croix*, with the key cutout and the paper pieces of direction 2 folded in.** That means a real CC0 key and a real FSA bench plate, used as stencilled backgrounds in two or three cells.

- **Why direction 1:**
  - It is the only one where the same visitor and the same shadow-man are visibly the same person in every cell. The proof depends on that: E has to be identical while its meaning changes.
  - Lécroart's own page already uses solid black shadow figures on salmon, so the silhouette rig is his grammar, not a costume.
  - The FK rig gives genuine frame-by-frame motion in exactly the cells being read.
  - Every pixel can be credited.
- **What it needs before a build:**
  - Hand-drawn replacement heads and hands for the rig (SCION 38) to bring in a pen line.
  - A drawn lettering hand to replace the typeface.
- **Direction 2 is the stronger collage,** but it needs a better visitor cutout.
- **Direction 3 should be kept only as the comparison baseline.**

**New SCION prompts to add to `swarms.json`:**
- An "Oubapo letterer": balloon text that must hold two readings. The bank has no lettering or typography SCION.
- A "comic-page stage": gutter marks as animated axis cues.
