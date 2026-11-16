# La belle Hortense: fresh-reader protocol (structure S1)

The reader must be someone (or an agent) that has NOT read plan.md, structure.json, the board, the captions after 39.0 s, or this film's notes. Give them only these instructions and the film.

## Viewing condition
- Play `assets/films/la-belle-hortense.mp4` (or the editor's current preview) from 0.0 s with sound, full frame, at normal speed. No scrubbing forward.
- **Stop at 39.0 s**, the end of module IV (caption "Qui a la clé ? / Who has the key?"). Do not watch past 39.0 s before answering.
- Re-watching 0.0 to 39.0 s is allowed once. Note if you used it.

## Questions (answer in writing, before you see anything after 39.0 s)
1. **Leading explanation:** where is the brass key now, and how did it get there? One sentence.
2. **Motif that changed it:** which of the six things (coat, bell, key, bench, receipt, door) changed or fixed your explanation? Give the moment (roughly the time, or describe the shot).
3. **Rejected explanations:** list any other explanation you considered, and what you saw that ruled it out.
4. **Confidence:** 0 to 100.
5. **Pointing back:** name the earliest shot that, looking back, already contained the answer.

Then watch 39.0 to 66.0 s and answer:

6. Did the ending match your answer? Did it feel fair (everything needed was shown before 39 s) or arbitrary?
7. Did you notice that the six things come back in a rotating order? (Yes / no / only at the end card.) Answer this question separately from fairness.

## Scoring (done afterwards by the critic, against structure.json)
- **Solved:** Q1 names the conductor or the coat as carrying the key away (claim S). Leaving "the conductor" unnamed is acceptable if the coat is named.
- **Fair-play pass:** the answers to Q2 and Q5 point at frames that hold supports K1 (I.4, 7.5 to 9.0 s, key laid on the red coat), K2 (II.2, 13.5 to 15.0 s, coat lifted with a glint), K10 (IV.2 replay), or K0 (I.1, coat on the bench). The target answer to Q5 is "the red coat on the bench in the first scene, with the key laid on it" (frames 3.75 s and 8.25 s).
- **The motif that should change the explanation is the coat (manteau).** A reader who names the receipt is moving away from ALT-1, which is still a structural pass. A reader who names the bell or the door is rejecting ALT-3 or ALT-2.
- **Fail:** the reader cannot form any explanation at 39.0 s, or their leading explanation is ALT-1, ALT-2 or ALT-3 after the refuting clue was on screen. Record which refuting clue they missed (K4/K8, K9/K11, K5/K7). Following prompt §8, the repair is to move the earliest missing support within its legal slot, then re-run verify.py.
- Score motif recurrence (Q7) and mystery fairness (Q1 to Q6) separately.

## Record
Append each reader to `films/swarm/la-belle-hortense/reader-log.md`:
reader id, film revision (file hash), structure revision, rewatch used (y/n), answers to Q1 to Q7 verbatim, score (solved / fair-play / fail plus the missed clue), and the date. Label the result *perceptually judged*.

## Status
No fresh reader has been run by this unit. Its answers are **pending** (unknown) until a separate agent who has not seen this structure watches a saved assembly.
