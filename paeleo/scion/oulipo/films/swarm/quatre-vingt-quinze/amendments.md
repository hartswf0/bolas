
## Editor, r0 (2026-11-17)
- **Plan section 7, per-cell clock.** The plan has the "0.5–2.6 s exposure sheet plays" (and cue at local 0.5 s). The proposal is to change it to "sheet and cue start at the occurrence start (frame 0); the 0.5 s camera travel overlaps the first six drawings."
  - Reason: with a 0.5 s start, E is still at rest at 44.5 s. The defining beat (plan section 1, B5) needs her mid-lift with the head turning up at 44.5 s. U2 and U3 both built to frame 0.
  - The bar's text is unaffected. The film is built this way.

## Editor, r1 (2026-11-17)
- **Still awaiting operator sign-off:** the r0 sheet-start proposal above. The r0 and r1 films are both built to it. In r1 the E sheet holds its rest drawing for the first 0.25 s, so the lift now starts after the camera has nearly settled. The bar's text is unchanged.
- **Note, not a bar change:** the visitor's replacement library grows from 10 to 11 drawings. The new one is the commissioned skyward head `v_sky`. SCION 38's "at most ten drawings" applies to its own proof scene. The r1 critic's repair needs a distinct up-turned head, and every one of the 10 existing drawings is in use. U2's assert in puppets.py now allows 11.
- **Protocol gap in B3, not a bar change:** B3 needs a down-first reader. The 64 s film always plays across first, so r1 adds two reader cuts in `readers/`, each 35 s and each holding a single route:
  - across-only: title, then across, then end;
  - down-only: title, then down, then end.
  
  Both cuts are time-mapped master frames from the same composite. The operator or the reader units must give each cut to a fresh reader.
