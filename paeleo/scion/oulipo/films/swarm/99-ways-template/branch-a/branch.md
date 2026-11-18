# Branch A: 99-ways-template (from checkpoint r1)

**Hypothesis (Explanation A):** the P8 gaze cannot be expressed with the only head piece.

The only head piece is `page-cartoonist/pieces/clerk.head.png`, cut from Rothstein, LoC 2017776093. In it the eyelids are lowered and the face is pitched down at the desk. A 2D roll on the collar hinge (2 → -11 degrees) cannot turn that face into one looking up. The repair the hypothesis implies is to replace the P8 head with a head whose eyes are open and turned up or away, or else with a profile or back-of-head piece. S8 would then be re-keyed in steps of 15 degrees or more. The staging stays as it is.

## What I checked (looked at, not guessed)

- **The head piece itself.** The eyes are fully closed or downcast behind the spectacles, and the chin is tucked. The P8 crop of the page shows the same thing: at -11 degrees he still reads as looking at his fist and pencil, and the key is at the far left. **The diagnosis is confirmed.**
- **The same sitting (LoC search "rothstein randolph vermont").** It returns 8 items:
  - 2017776093: the agent; the only frame of him.
  - 2017776087 / 8b16704: station interior with a *different* man in a straw hat at the Express & Telegraph window.
  - 2017776101 and 2017776100: the station exterior and the business block.
  - 2017722583-86 (8a08780/82/83, 3c30469): locomotives and the station exterior.

  **No second frame of the Randolph agent exists at the LoC.** The same-sitter route is closed.
- **A matching FSA/OWI plate for a profile or back-of-head piece.** I looked at the contact sheets:
  - Wolcott 8c11760, 8c11830 and 8c11778, and Bubley 8d33077, 8d33109, 8d33125, 8d33082 and 8d33085: every agent wears a hat or faces the camera.
  - 8d24973: a capped passenger agent, front on.
  - 8a26752-54: a young man reading a directory, eyes down.
  - 8d16561 and 8d15102: workers seen too small or looking down.

  None gives a bareheaded man in white shirtsleeves, seen from behind or in profile, with his head tipped up, at a scale that would pass as the same clerk. Any frontal up-looking face from another sitter would read as a different man and break the photo-comic's continuity. That is a worse failure than the one being fixed.
- **Commons.** It returned "too many requests" on every call, including after a back-off, so it could not be searched in this round.
- **The Moving Image Archive stills index (local).** I ran a regex for clerk/looking up/thinking. It turned up only crowds and dogs looking up, plus "Two Pay Days (1927), a clerk at his ledger", who also looks down. Nothing usable.

## What changed in this branch

1. **`99-ways-template.py`**: copied from `films/99-ways-template.py`. Only its output paths changed:
   - `film.render(out_dir=BRANCH)` → `branch-a/99-ways-template.mp4` (+ .webp poster).
   - The page the film performs is copied to `branch-a/99-ways-template.png`.
   - `editor_checks.json` → `branch-a/`.

   Picture and sound logic are untouched. Because no replacement head was found, the page art is still r1's, so the protected items are unchanged by construction: the 3/3/2 grammar, P6, the memo, the door swing and creak, the motionless key, D1/D2, the tonality and the ledger card. The S8 head poses were **not** re-keyed. Larger rolls of the same downcast face are exactly what the hypothesis says cannot work, so doing only that half of the repair would be cosmetic.
2. **`credits.json`** (branch copy). Rights fixes:
   - **Blank sheet:**
     - The licence string is de-duplicated and quotes LoC's statement ("not aware of any copyright … rights assessment is your responsibility").
     - `license_url` = https://www.loc.gov/legal/.
     - `file_url` = the 0001 JP2 on tile.loc.gov.
     - The LoC credit line is added.
   - **The six Commons PD sounds:**
     - The licence now says "released by the author (PD-author, PDsounds.org)", as the live extmetadata categories show.
     - `license_url` = Template:PD-author.
   - **Panama by Air (1914):**
     - `author` no longer pretends "via movingimagearchive.com" is an author. It says the producer is not recorded and names the access route.
     - The licence says plainly that it is PD by date only, that no archive licence statement was read (proxy 403), where the title and year come from, and that MIA is not a BRIEF-2 archive.
     - `license_url` points to the US copyright-duration FAQ.
   - **Train sounds from Iowa (CC BY 3.0):**
     - `used_as` now opens with "modified (excerpt 40-50 s, low-passed at 1.4 kHz …)".
     - A ready attribution line is added.
3. **`notes.txt`** (branch copy, 103 words, inside 60-110):
   - "the GrabCut cutouts" becomes "pieces cut by hand from the photographs", so the handmade claim covers the cutting, not the pixels.
   - The CC BY recording is now attributed (Glaneur de sons, modified).

## Not done / for the operator

- **The P8 gaze gap remains open.** This branch shows that Explanation A's repair has no source in the reachable archives:
  - The LoC holds no second frame of this sitter.
  - No suitable back-of-head or profile plate turned up in FSA/OWI or the MIA cache.
  - Commons was rate-limited.

  If the gaze must be fixed under the current bar, the remaining moves are a staging change or a new photograph. A staging change would be one of these:
  - put the key inside his eyeline, so that a downcast look reads as looking *at* the key without seeing it;
  - turn him fully away, torso included.

  Both are outside this branch's mandate ("leave the staging unchanged"). The new-photograph route would be a handmade photograph of a real sitter, which is allowed as HANDMADE.
- **Render.** The root volume sat at 0-12 MB free for most of the session (it is shared with other jobs). One render attempt broke its pipe and was discarded. Once space returned, it was re-run with `TMPDIR=/dev/shm`:
  - Outputs: `branch-a/99-ways-template.mp4` (72.5 s, 3.6 MB), `.webp` poster, `99-ways-template.png` (a copy of the r1 page; art unchanged), `editor_checks.json` (all asserts pass).
  - Frames sampled at 29.8, 36, 41, 44.5 and 70.5 s (`work/contact.jpg`).
  - Result: identical to r1. P5, P7 and P8 all show the same downcast eyelids, and in P8 he still reads as looking at his fist, with the key at the far left. This is the visual confirmation of Explanation A.
- **Amendments A-1 to A-4** are untouched (operator decisions). The B1/defining_beat text in plan.json still quotes Madden's line, and it is frozen.
