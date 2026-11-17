# How the film swarms follow the SCION protocol

There are four layers. Each one owns a part of the protocol.

## 1 · Operator (the user and the lead session)

- **Keyframes** (`scion-keyframes.js`): three directions per work, at least two of them animation-led, shown as a board beside the reference.
- **The user picks a direction.**
- **Test shot** (`scion-film-swarm.js`, `stage: "shot"`): the defining beat only. This is the prompt's "hard proof before scaling". For page works it also makes the hinge panels.
- **The user says go, redo or hold.** A go passes `shotNotes` into the full build.
- **Status view:** the screening reel, plus each work's page on the site.
- **Bar amendments:** only the operator may change a frozen bar. Makers propose changes in `amendments.md`.

## 2 · Work SCION (`prompts/<slug>.md`, sections 1–10)

| Section | Where it is carried out |
|---|---|
| 2 Thesis, beat, baseline | The director, in `plan.md` |
| 3 Lineage Genome, Olog, preconditions, counterexample | The director, in `plan.md` |
| 4 Invariants and concurrency | Immutable source IDs in the unit ledgers. Branches work in `branch-a/` and `branch-b/`; checkpoints `r0`–`r2` keep the revisions. |
| 5 Swarm assignments | The director merges the roles into 2–4 maker units. Readers, validators and the critic are run separately, never by makers. |
| 6 Hard proof | The shot list. For page works (`args.page`), the page `assets/pages/<slug>.png` **and** a film that performs its reading. |
| 7 Fixture and critique | Two blind readers answer the section 7 questions from the work alone. The critic compares their answers with the intended reading. |
| 8 Repair and inquiry | Round 1 is a single repair. Round 2 states two explanations, tries both on separate branches, judges them side by side, and promotes the better one. |
| 9 Deliverables | Listed by the director in `plan.json`. The editor makes all of them. |
| 10 Common seed | The station incident is used unless the chosen direction tells another story. `plan.md` says which. |

## 3 · Technique SCIONs (`../../../swarms.json`)

- The director picks 2–3 of them. Units and editors read them in full and apply their native primitives, numeric invariant, perceptual achievement and tests.
- The tribunal uses their verdict: **pass / reference stronger / inconclusive**. Numeric checks support the critic's perceptual judgement but never replace it.

## 4 · Workflow (`scion-film-swarm.js`)

1. **Director.** Writes `plan.md` and `plan.json`. The bar in `plan.json` is frozen: 4–6 blocking conditions and up to 4 advisory ones.
2. **Units, then editor.** The editor renders and saves checkpoint `r0`.
3. **Review.**
   - Two blind readers look at the work in the intended condition: contact sheets, plus full-rate strips of the defining beat.
   - An independent critic then judges against the frozen bar, the reference and the chosen keyframe.
   - An attribution reviewer runs alongside. Only licence and attribution problems block; process slips are logged and fixed.
4. **Repair round 1.** The editor fixes the failures and saves checkpoint `r1`. Review runs again.
5. **Repair round 2.** Two hypotheses are tried on separate branches, each with its own readers and critic. The winner is promoted to checkpoint `r2` only if it beats `r1`.
6. **Promote.** The strongest reviewed checkpoint is restored, not simply the last one. `review-history.json` is written, and the work's files are committed and pushed.

## Evidence labels

- measured
- structurally verified
- perceptually judged (watched)
- perceptually judged (from frames)
- unknown

Judgements made from frames are never reported as watched. Final real-time viewing with sound is the operator's.
