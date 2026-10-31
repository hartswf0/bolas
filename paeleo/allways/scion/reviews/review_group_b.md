# Independent specification review — group B

## Scope and verdict

Reviewed all **20 entries, IDs 75–94**, in `group_b.json`, including the completed 90–94 batch, plus the shared doctrine and prompt compilation in `assemble.py`. This was a **prompt-specification review**. No reference film was audiovisually inspected in this review; no new film, installation, participant workflow, render, or artistic acceptance test was executed. Nothing below is a film acceptance verdict.

**No release-blocking specification defect found.** The operators are materially distinct, their proposed proofs are bounded, and named working objects generally support the prescribed actions. Two local changes would improve internal consistency; one shared clarification would make the limits of automated evidence checks safer and more precise.

## Material fixes

### 1. ID 82 — explicitly accept an honestly unchanged performance

The proof correctly allows no improvement and an unmet goal. Its theorem nevertheless starts with making an improvement consequential; acceptance requires a “visible difference between attempts,” and a repair branch assumes a claimed improvement exists. A faithful recording in which the same problem persists can therefore satisfy the proof’s documentary conditions while failing its prescribed acceptance test. That creates pressure to select or imply progress.

**Suggested fix:** make the achievement the relationship between participant-defined goal, practice, constraints, and actual outcome. Require that the edit’s claim about change **or persistence** be visible in comparable complete attempts. Make the “improvement cannot be seen” repair conditional on an improvement actually being claimed. Retain the real outcome and the possibility of failure.

### 2. ID 80 — distinguish participatory production from an interactive delivered artifact

`execution_mode` is `participatory_system`, but the defining proof and deliverables are a linear collaborative film assembled from already authorized contributions. The protocol, restriction states, and date records are useful production primitives; the proof does not operate a contribution, correction, or withdrawal path. This is ambiguous beside the shared doctrine’s complete interaction-path requirement.

**Suggested fix:** use `linear_film` for the delivered mode and preserve participation in the process description. If an actual participation platform is intended instead, add one small, locally simulated submission → review → inclusion → withdrawal path whose state changes the assembly, with no live outreach or collection implied. Do not require a viewer interaction merely because a film was made collaboratively.

## Shared clarification

### 3. Source-ledger checks establish consistency, not the truth of their inputs

IDs 75–83 and 88 frequently ask an automated check to validate an authorization, date, object-continuity, translation, or outcome assertion against a record. Such a check can correctly detect missing references, contradictory states, out-of-range intervals, and a cut that violates recorded restrictions. It cannot independently establish that the original permission, identity claim, translation, or observation is true. The compiler already separates structural and perceptual evidence and conditions checks on supported representations; an explicit sentence would close the remaining ambiguity.

**Suggested fix in shared doctrine:** “Automated source checks verify record completeness and internal consistency; source truth, permission validity, translation meaning, and observational claims require appropriate source inspection or human review. Report which of these was actually performed.” This is a clarification, not a finding that the current entries already claim to have proven such facts.

## Strengths to preserve

- The central operations are different in consequential ways: milestone comparison; local ritual logic; open counterpoint; a changed material return; three technological time regimes; a common recording-date protocol; testimony integrity; practice and exposure; a civic day; object-transfer drama; repeated routine; pressure within a tableau; obligation across tableaux; nonhuman attention relay; geometric blocking; real clock synchronization; perceptual momentum; gesture evidence; alternative edits from one source pool; and character constraints in animation.
- The small scenes have concrete action, consequence, and sound. IDs 84–89 are original staged or honestly declared observation/staging experiments, rather than empty requests to imitate a director’s appearance.
- IDs 90, 93, and 94 have particularly inspectable working representations: explicit clock states and resume behavior; paired EDLs with shared source-time alignment; and pose/contact/hold states under controlled gag variants.
- Automated checks address timings, source references, ordering, supported state, and geometry. None purports to calculate artistic quality or infer a participant’s feelings. Perceptual criteria remain questions for actual viewing.
- All reference records are `text_only`; the entries repeatedly distinguish documented descriptions from audiovisual inspection. Missing dates, region blocks, edition differences, and uncertain lineage information remain visible.
- The compiler permits a labeled interpretation when a reference cannot be played, requires an actual inspected comparison before “reference stronger,” and leaves acceptance pending when an independent critic is unavailable. It does not imply that authoring the prompt completes the film.

## Source spot-checks

Independently reopened the following primary/project or authorized-release descriptions as text. These supported the relevant metadata and broad method claims. This is a spot-check, **not** a fresh external audit of every citation in all twenty entries.

- [Samsara official project](https://www.barakasamsara.com/samsara/about): nonverbal framing, standard-rate and motion-control capture, cyclical premise, and the 2011 work/2012 release context. The proposed print-workshop cycle is clearly an original experiment.
- [Criterion — The Qatsi Trilogy](https://www.criterion.com/boxsets/934-the-qatsi-trilogy): distinct approaches across the three films and the catalogue’s 1983/1988/2002 years. The prompt preserves the unresolved 1982/1983 event distinction instead of making an unsupported blanket correction.
- [Hope Production — HUMAN](https://www.hopeprod.com/en/human-le-film): 2015, Yann Arthus-Bertrand, Armand Amar, testimony/image structure, and links to multiple forms of the work. Treating HUMAN as testimony-led rather than purely nonverbal is supported.
- [Vivo film — Le Quattro Volte](https://vivofilm.it/en/production/le-quattro-volte/): 2010, Michelangelo Frammartino, and successive human/animal/plant/material subjects. The prompt correctly attributes the soul-cycle account as a poetic premise, not a scientific claim.

## Review boundary

No author JSON was changed by this review. Suggested fixes concern specification wording and mode classification. Any future proof still needs actual sources, a playable result, and independent viewing or operation before artistic acceptance can be reported.
