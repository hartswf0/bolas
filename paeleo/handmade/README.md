# PAE-02 · The threshold, handmade

One description, many operations. Each SCION swarm builds the same threshold scene from the bottom up, with its own assets and
its own way of making a body move, under one score of the dog's choices that every version must keep.

## Why the lenses were not enough

PAE-01 showed all 54 swarms as lenses on one paper dog: the stage drew its cut-out once and each lens read the record of
that drawing and laid its language on top (a mesh, a matte, a halftone, a state graph). Eight critic rounds made every lens
legible. But a lens is a filter, not a studio. The dog underneath was always the same paper puppet, built and moved the same
way; only its surface changed. That shows what each swarm would *look at*. It does not show what each swarm would *make*.

The SCION prompts ask for more. Each names a **native formal language** to build with (engraved figures and substitution
graphs, articulated silhouettes, an image torrent, a constraint graph, a drawing library, re-performed footage), a smallest
capable **swarm** of makers, and a **hard proof** to produce before anything is scaled. Taken seriously, two swarms given the
same scene should not share a single asset or a single way of moving.

## The PAELEO form of the test

PEO separates three things, and PAE-02 holds two of them still:

- **P, the prompt**: the same typed circumstances for every version (call, call and reach, sit down beside the door, open the
  door, offer a hand low, say it softly, come in).
- **E, the ekphrasis**: the same description (`BRIEF.md`), and the same **score**: the dog's decision trace from the PAELEO
  machine, 32 s at 24 fps, six choices at fixed times (`score/threshold-score.json`, built by
  `tools/paeleo/build_score.js`).
- **O, the operation**: entirely the swarm's. What the dog is made of, how the world is built, how anything moves, what it
  sounds like.

If description is operative, the choices survive every operation, and that is measurable: `tools/paeleo/check_handmade.py`
checks each version's own trace against the score (I1 the six choices within ±0.25 s, I2 never inside the house and ending on
the sill, I3 screen motion following the score's distance, I4 the refusal showing the back). Whether the choices *read* as
choices is judged by an independent critic who sees the film, the brief and the swarm's bar, never the builder's notes.
Everything that differs between versions is the operation. The invariants are the description.

## Materials, and where they come from

The swarms build from things whose rights are recorded, mostly found:

- **The archive dog**: 50 frames of a home-movie dog approaching a person by a house, a bowl at its feet, from *Amateur Film
  New Jersey C* (Home Movies collection, Internet Archive, public domain), with SAM masks and rig keys. It came to Bolas
  through Secondhand Motion, which had already observed it (stage 1 of its pipeline) for its own dog shot.
- **The archive door**: 32 frames of a person opening a door, from *Straight Talk* (NTIS, public domain), with SAM masks.
- **98 more public-domain archive shots** (3,841 frames, SAM masks), from the same Secondhand Motion observation pass.
- **Quick, Draw!** drawings by real people (dog, door, house, hand, face, moon, tree, fence, stairs; CC BY 4.0).
- Whatever a swarm draws, cuts, solves or synthesizes itself.

The CINEOSIS lab's 15,149 archive shots are the next library to draw on. They stream from the Moving Image Archive, which
this environment cannot reach yet, and only rights-recorded footage may be used.

## The first cohort

Six swarms, one from each family and two from the algorithms, chosen to be as far apart as possible in what they build with:

| Swarm | Builds the dog from | Moves it by |
|---|---|---|
| 01 Terry Gilliam | the real archive dog, cut out and engraved | card pivots, hard substitution, held frames |
| 02 Lotte Reiniger | a hand-cut silhouette, studied from the archive dog's outline | articulated joints on a lit screen |
| 04 Frank Mouris | thousands of tiny real archive frames | a torrent that forms the body and boils |
| 08 Ivan Sutherland | points and lines under constraints | an iterative solver and a light pen |
| 38 Dynamic pose selection | real people's dog doodles | choosing whole drawings, never bending them |
| 53 Atlanta Moving Image | the archive dog's own footage | re-timing, reversing and re-ordering its frames |

Each is one agent working alone in its folder with its SCION prompt verbatim and this brief. Each delivers a 38 s film, its
own trace, an asset ledger, its method, its build scripts, stills and a ledger of attempts. Then each film goes to an
independent critic, and repairs go back to the swarm, as in PAE-00.

## What happened

All six built a 38 s film from the bottom up, and every film keeps the four invariants when its own trace is checked. Each
then went to a fresh critic per round (the film, the brief and its SCION prompt; never the builder's notes), and repairs went
back to the same swarm. The record per swarm is in its `reviews/`, and the page is `paeleo/handmade/` on the site.

- **The choices survived every operation.** A torn card turned over, a silhouette swapped for its end-on piece, a solver
  refusing a light-pen drag, a doodle chosen from four thousand, a home-movie dog's own walk played backward, a torrent of
  tiles replaced at once: each is a different way of making the same six decisions readable at the same six moments.
- **The critics found the operations where they were weakest, and it was always in the operation, not the description.**
  The found-footage dog had never been filmed lying down, so its one composed pose was where it failed first. The doodle
  library had no single person's dog walking, so its walk skated. The constraint dog's turns were a flat mirror flip until
  they were solved as a rotation. The image torrent filled a drawn outline instead of being the body.
- **What each kept is its own.** Gilliam's refusal is the card's blank back; Reiniger's, a cut rear view; Sutherland's, a
  console line saying the dog is not selectable; Atlanta's, a dog's real turn away from a real person in 1930s New Jersey.

The status of each film (pass, narrow pass, repair in progress) is kept live on the page, read from the `reviews/` folders.

## What comes after

- **The other 48.** Each swarm's lens in PAE-01 is its sketch for PAE-02; the lens's `show` sentence is the first line of its
  brief. The cohort's results decide what the brief needs before it scales.
- **After the threshold.** The same method can hold the next description constant: what the dog does the next evening, when
  the door is already open. A swarm that kept the threshold's invariants is asked to carry its dog one scene further, with
  the same materials. That tests whether a swarm's world is a world, or only a look.
- **The language.** The score is the first piece of PAELEO the language: a description precise enough to operate, loose
  enough to be built fifty ways. Its next form is a file a person writes rather than a machine run: the choices, the
  circumstances that earn them and the invariants they must keep.
