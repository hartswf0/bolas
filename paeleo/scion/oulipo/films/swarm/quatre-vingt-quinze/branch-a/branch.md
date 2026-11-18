# branch-a (from checkpoint r1): explanation A, separating the gaze from the key

## The repair
r1's skyward head (v_sky, pitch 70) sat on the same line as the raised key, so her nose pointed up and to the right at the key in both routes. "Looking up" and "looking at the key" were one silhouette, and the bell's place (above E, slightly left of her head: B's bell pivot is at cell x 430, and her eye is at x about 530) was never pointed at.

What changed. All of it is in E's single canonical timeline, the same in both routes, and nothing takes a route argument:
- v_sky redrawn. The head turns back further (pitch 70 to 84, back_k 0.86), the mouth opens a little and the brim flares (a startle). It is still one drawing, so the library stays at 11.
- Startle under the sky look (slots 6 to 20, 0.50 to 1.67 s). The spine straightens back by up to 9 degrees and the neck throws back by up to 12 more. The free shoulder hitches and its hand flinches out at slot 7 (0.58 s, on the glint) and then eases down. Everything returns to zero by slot 21, so the page pose (slot 35) is r1's exactly.
- Measured gaze, from the eye along the head's forward axis (0 = right, 90 = up): r1 about 60 degrees, which is the key's line. Branch-a is 93 to 109 degrees: straight up and slightly up-left, past the key and toward the bell's place. The key stays at about 55 degrees, up and to the right.
- The key arm keeps r1's lift: anticipation, overshoot and glint at 0.58 s, settle by 0.75 s. The ducked clink stays in sync.
- GAZE_UP_E (the decoder feature) is corrected from (600,-380) to (450,-300), B's bell mouth above E.
- FK check: joint error 0.0 px, no angle-limit clamps.

## What is protected (verified)
- Page: branch-a/quatre-vingt-quinze.png is pixel-identical to checkpoints/r1/quatre-vingt-quinze.png (max abs diff 0). Every cell's page pose is unchanged.
- Cell immutability: E is a function of (cell, frame) only. The across and down occurrences show the same drawings.
- Sound: the soundtrack PCM is identical to r1 (sha prefix 2ad1840ad9adf9aa, both files). The bell tail lies under down-E and across-E stays silent.
- Untouched: the I ending (the key slides under the shut door, MERCI.), the Lécroart grid, washes, silhouettes, lettering, red barbed marks, the flipped title, the red thread and cord, and the watcher in D's window.

## Frames looked at
At 15.6, 16.2, 44.6, 45.2, 45.6 and 46.0 s: her nose points straight up in E, apart from the key. At 46.0 s she is back on the key (v_up, the page pose). The down arrow from B sits above E's top border at 44.6 s. The bell itself is still out of frame in the camera at 44.5 s; that is unchanged here (camera fixes are outside explanation A).

## Rights fixes (branch copies only)
- credits.json: the two ShareAlike declarations (bell, steps) now state one soundtrack licence, CC BY-SA 4.0, with its URL, and note that BY-SA 3.0 section 4(b) permits a later version for adaptations.
- notes.txt: "CC BY-SA" is now versioned (soundtrack under CC BY-SA 4.0). It also states that the film has no on-screen credits and that the credits file must be published with it.
- ledger.json (a copy of forage/ledger.json; the upstream file is unchanged): BELL, KEYS and STEPS used_as are synced to the r1 credits text. outputs.checks now quotes the r1 measured bell-tail figures, with the r0 ones marked superseded. adapted_licence is one licence, CC BY-SA 4.0.
- puppets/puppets.py and exposure.json (branch copies): the "absences" text no longer claims that U3's key cut and stencils were undelivered. The KEY local_path names forage/key_cut.png and its source sha. KEYS-CLINK gets its Commons file_url, and its local_path is marked E-test only.
- Not changed, and still for the operator (amendments.md): the r0 sheet-start change and the visitor library at 11 (v_sky redrawn, not added) are still unratified. The B3 single-route reader accounts are still pending. Render the reader cuts with QVQ_CUT=across|down (output to branch-a/readers/), with a down-first reader whose account is recorded before the across route.

## Files
branch-a/quatre-vingt-quinze.py (FILMS = parents[3]; imports branch-a/puppets; writes only to branch-a/), puppets/puppets.py, puppets/exposure.json, puppets/joint-errors.json, quatre-vingt-quinze.mp4 (64 s, sha prefix d36e13aa37cc3e0a), .png, -across.png, -down.png, .webp, cells/, credits.json, notes.txt, ledger.json.
