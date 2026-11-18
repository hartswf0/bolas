# Branches from checkpoint r1: 99-ways-template

Both branches were forked from `checkpoints/r1` to attack the open P8 gaze failure: in P8 the clerk should look up and away from the key, but readers saw him looking down at his fist or wrist.

## Branch A: the head piece (`branch-a/`)

- **Hypothesis (Explanation A):** the only head piece, cut from Rothstein's LoC 2017776093, has its eyelids lowered and its face pitched down. No 2D roll on the collar hinge can make that face look up. The fix is a different head (eyes open and up, or a profile or back-of-head piece), with the staging left as it is.
- **What it did:** it searched the LoC sitting (8 items, no second frame of the agent), FSA/OWI contact sheets (Wolcott, Bubley and others) and the local MIA stills index. Commons was rate-limited. No usable head was found, so the picture was left at r1 and S8 was not re-keyed. It confirmed the diagnosis by looking at the plate and the render. It shipped the rights fixes in `credits.json` and `notes.txt`. Its render is identical to r1 and all editor asserts pass.
- **Verdict:** **won.** It beat checkpoint r1 in independent review and was promoted to r2.

## Branch B: the staging (`branch-b/`)

- **Hypothesis (Explanation B):** the staging sets the gaze, not the head. Move the clerk to (500, 1290), bring his shoulder under the key, drop the fist below the frame so only the pencil rises to the chin, and move the balloon right of his head so its tail never crosses the face. Change P8/S8 only.
- **What it did:** it recomposed P8 in a branch copy of `page/`. The page diff was confined to P8 and the editor checks passed. It made a parallel set of rights fixes. It also noted that the r1 roll of -11 deg tips this un-mirrored face further down, not up.
- **Verdict:** **not promoted.** The orchestrator's record for this round carries only the outcome: A beat r1 in independent review and is the branch to promote. No written verdict or critic text for B was found on disk (`critic-branch-b/` holds frame sheets only), so its review reasons are not restated here.

## Why A won

- **Safe gain:** A is a strict improvement on r1 with zero picture risk. Its film is byte-identical to r1, so everything the critic protected (the 3/3/2 grid, P6, the memo, the door swing and creak, the motionless key, D1/D2, the tone and the ledger card) holds by construction. Its rights record is materially better: a LoC licence quote with URLs, PD-author for the Commons sounds, an honest PD-by-date note for MIA, and a CC BY "modified" record with an attribution line in both credits and notes.
- **Settled question:** A answered its question with evidence, not a guess. The diagnosis is confirmed and the archive route is closed (no second frame of the sitter, no matching plate). B is a recomposition of a protected page; even if it is right, it is a separate move that must clear its own review.

## Still open (for the operator)

- **P8 gaze:** still unrepaired. The remaining routes are a staging change (B's direction, or turning him fully away) or a new handmade photograph of a real sitter.
- **Commons:** not searched for a head piece (rate-limited).
- **Amendments A-1 to A-4:** pending. The Madden line is still quoted in frozen plan.json and other planning files.
