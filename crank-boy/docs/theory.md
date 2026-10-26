# The Crank Boy — Theory of Play

Written in SCION LUDIC theory mode before any code. Source artifact: *À l'École* (At School), from the *En l'an 2000* series, attributed to Villemard, about 1910.

## 1. Initial interpretation

**What the image shows (documented, visible).** Six seated students wear metal headsets. Each headset hangs from a wire that runs up to one shared line along the ceiling. At the right, an old teacher in glasses drops books into a hopper on top of a cabinet machine. A boy in an orange jacket turns a hand crank on the side of the machine. He is the only student without a headset. Books sit on a shelf behind the teacher. Maps hang on the walls. The caption reads "En l'an 2000."

**What is read in (interpretation).** That the machine turns books into a signal. That the signal carries the book's content. That the students are learning, not just listening. The image does not settle any of these.

**The detail that matters for play.** The machine runs on a student's arm. The transmission depends on the labor of one student, who stands outside the system he powers and is the only one who can see which books go in.

- **Ordinary action:** a student does a classroom chore (turning a crank) while the rest of the class receives a lesson.
- **Friction:** the crank-turner cannot hear the lesson, cannot see inside the hopper without stopping, and is visible to everyone if he stops.
- **Ludic opportunity:** the rate, steadiness, and continuation of the lesson are in one student's hands, and that student has the only view of the sources.

**Play thesis.** You turn the crank that powers the lesson. You are the only person in the room who is not wired in and the only one who can see which books are fed to the machine. Keeping it running, looking at what goes in, changing what goes in, or stopping are all available to you, and each has a visible cost in the room.

## 2. Ludic skeleton

**Entities:** the crank boy (player); the machine (hopper, rollers, crank, bin); the bus (one ceiling line feeding six headsets, so every student receives the same signal); six students; the teacher (feeds books in a fixed order, asks one question at the bell, grades against his own copy); the shelf; the bin; the bell.

**Morphisms:** `[crank]` `[stop]` `[inspect]` `[swap]` `[unplug]` `[refuse]`.

**States and what produces them**

- *steady hum:* crank in a narrow speed band; heads stay down
- *drift:* crank too slow; heads droop, signal thins
- *garble:* crank too fast; students twitch, signal arrives scrambled
- *silence:* player stops; all six students look up at the player. The central state change of the game.
- *suspicion:* rises while the machine is silent, faster when the teacher faces it
- *contradiction found:* a page disagrees with the wall map or with another book

**Constraints**

| Rule | Permits | Prohibits | Tension | If removed |
|---|---|---|---|---|
| Machine runs only while cranked | control over pace | idle reading | every look costs signal | player becomes a spectator |
| Door opens only when stopped | reading sources | reading for free | knowledge vs. continuity | no tension |
| Sent words cannot be un-taught | — | retracting a transmission | swaps are final | no stakes to swapping |
| One bus, one signal | — | teaching one student differently | unplugging gives silence, not a different lesson | becomes a personalized-feed game |
| Teacher grades against his own copy | — | citing other sources | correct by authority vs. by evidence | no authority to question |

**Invariants.** Voluntary entry and safe exit (letting go never ends the game). A bounded lesson (the bell). The game does not certify an interpretation. Grades are pretend consequences. The postcard is never altered; everything invented is labeled in a ledger.

## 3. Illusion ledger

| Convention | Class | Reinforcement |
|---|---|---|
| Crank = power | safe | hum and dials follow crank speed |
| Headset = receiving the lesson | safe | posture tracks signal quality |
| Signal carries book content | uncertain | words of the page travel along the wires |
| Books are consumed | uncertain | not used; books sink into the hopper and the struck words show what has gone |
| The six students matter | requires devotion | each looks up, droops, and answers in their own words |
| Teacher's authority | requires devotion | he grades without explaining |

## 4. Operational description

The teacher feeds a book. You crank; words go down the wires. You stop; six heads lift and the teacher starts to turn. You open the hopper door and read: the page says the river on the wall map runs the other way. Before he turns back you can resume, swap the book, unplug a student, or read the page aloud. At the bell he asks one question, each student answers from what reached them, and he marks the answers against his copy.

Core loop: watch the hopper, decide whether to look, pay for looking in silence, act on what you saw, see it in the answers.

## 5. Failure description

- **Rule-breaking:** swapping in view. The teacher puts his book back and stands guard. A penalty that changes tactics.
- **Emergent play to protect:** cranking in rhythm; unplugging everyone and reading aloud (the oral classroom retrieved from inside the machine classroom); cranking an empty machine.
- **Spoil-sport:** a design that quietly rewards one reading of the contradiction; altering the archival image.

## 6. Change test

- **Remove the room:** stopping is no longer seen; inspection becomes free. The room is load-bearing.
- **Remove the bell:** the crank becomes a job. Keep the bell.
- **Remove victory:** the moment six heads lift still holds.
- **Remove instruction:** the door rule and the one-bus rule are discoverable by trying them.
- **Reverse authority:** the player feeds books and the teacher cranks. (Planned as v2.)
- **Permit refusal:** letting go must be allowed and must produce a consequence, not a fail screen.

## 10. Residual theory

- Whether steady drag-cranking on a phone is pleasant or tedious after two minutes.
- Whether six students with one reaction each are enough to make their grades matter.
- Whether the contradiction can be found without being highlighted.
- Whether the strongest version is the one where the player stops for good.
