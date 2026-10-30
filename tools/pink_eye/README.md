# PINK EYE

Conjunctivitis: when the small blood vessels of the eye are irritated and swell, they become visible. In the Ludovico
sequence of *A Clockwork Orange* (1971), an attendant keeps putting drops in Alex's clamped eyes. That is the institution's
care, given so that the watching can go on. In *Pink Eye*, every drop pins another paper vessel onto the eye, until the
irritation has made the whole structure visible.

```bash
python3 tools/pink_eye/pink_eye.py CLIP.mp4 OUT_DIR      # writes OUT_DIR/pink-eye-v1.mp4 (49 s)
```

`CLIP.mp4` is a local copy of the Ludovico sequence (the 4:21 excerpt, 640x360). The segment times in `SEGS` were checked
against half-second strips at each cut.

| Part | Time | What happens |
|---|---|---|
| A · Exposure | 0–16 s | Archive layers surface and sink into one another, and the eye rises out of them. |
| B · Drops | 16–32 s | The dropper and the doctor drift over the eye. Each drop starts a vessel growing. |
| C · Pink eye | 32–44 s | The vessels spread, the paper flushes pink, and the other layers dissolve away. |

**Version 1** answers a direct note on version 0, "horrible to watch": it should be more blended, less abrupt, less cutting up,
with new sound. Nothing cuts. Footage plays in blended slow motion inside feathered, rounded paper scraps with three-second
fades, and is printed into the paper fibre. The vessels grow like ink over about two seconds each. The sound is new and
entirely synthesized: a low breathing room, a drone that thickens as the eye inflames, a slowing pulse, wine-glass partials
that swell, a falling plink for each drop, and one shared dark reverb. No clip audio is used.

## The Past Under Another Light (`under_another_light.py`)

The direct note on Pink Eye was "think more like a filmmaker, less gross to watch". Every Pink Eye version stared at the
clamped eye and repeated the violence it meant to answer. The feminist archive filmmakers this follows (Hammer, Citron,
Dunye with Leonard, Tajiri, Trinh) turn the camera on the apparatus and on the people handling the images, and they treat
a gap as a choice. So this recut never shows the clamped eye or the screaming. The reel is projected onto a pinned paper
sheet in a dark room, over a worktable with prints and typed slips under a desk lamp. The projector light is the
institution's record, the lamp is the hand that handles it, and the spill is where one falls on the other. The camera
moves only when a relation between images changes.

| Part | Operation | What happens |
|---|---|---|
| I · Rearrange (0–26 s) | after Hammer, *History Lessons* | The attendant's reach with the dropper is repeated against a public-domain hand lifting a miner's lantern. Two prints are slid side by side. On the last repetition the two superimpose, and his reach carries the light. |
| II · Reinterpret (26–52 s) | after Citron, *Daughter Rite*; Trinh, *Surname Viet Given Name Nam* | The reel slows almost to stillness on the woman doctor, the only woman in that room. Typed slips on the table do not agree with the picture. |
| III · Invent (52–84 s) | after Dunye and Leonard, *The Watermelon Woman*; Hartman, "Venus in Two Acts" | The print of the eye lies face down: "eye, clamped. not shown." An invented record card is typed, and her account stays blank. The reel runs out to a white gate, the table is cleared, and the light falls on it. |

```bash
python3 tools/pink_eye/under_another_light.py CLIP.mp4 SHOTS_DIR OUT_DIR   # about 15 min; 84 s
```

`SHOTS_DIR` is `shots/` from hartswf0/secondhand-motion (only `lantern-sam` is read). The sound is synthesized: room
tone, the projector's motor and gate, the lamp's faint buzz, a two-note motif that returns with each repetition in I, a
held low tone under her face in II, typing for every slip and card, and the tail of the film slapping the reel at the
run-out. It is a composed scene: archive fragments re-performed, not a recorded event. It stays local, like Pink Eye.

## Rights

The film is under copyright. This tool reads a local copy and writes a local render. Neither the footage nor the render
is committed to this repository or published on the site. Whether to show the result, and on what grounds (criticism and
commentary), is the author's decision.

## Archive voices: not yet in the film

The idea needs voices from the archive about feminism, laid into part C where the clip's sound falls away. They are not
in version 0. This session could not download from archive.org, the Moving Image Archive or the Library of Congress,
because the environment's network policy blocks those hosts. No archive speech index in hartswf0's repos is searchable by
topic either: `cineosis-lab`'s `found-audio` has no transcripts. Nothing has been faked in their place.

Candidates found by web search. Rights are **not confirmed** for any of them. Check each item's rights statement
before use.

- Pacifica Radio Archives, [*Women's liberation day: New York, San Francisco and Berkeley rallies of August 26, 1970*](https://pacificaradioarchives.org/recording/bb2603), the Women's Strike for Equality. The listing offers it for purchase.
- Pacifica Radio Archives, [*Liberation: a woman's viewpoint*](https://pacificaradioarchives.org/print/4221) (1970 series). The folio is on archive.org, but the audio's rights are unknown.
- Pacifica Radio Archives, [Women's Strike for Equality recordings](https://pacificaradioarchives.org/subject-tags/womens-strike-equality), and Margaret Mead's 22 September 1970 testimony to the New York City Commission on Human Rights on the status of women.
- CSU Dominguez Hills archives, [a Betty Friedan talk on the women's movement and the 1970 strike](https://csudharchives.libraryhost.com/repositories/7/archival_objects/100760). It is restricted where not in the public domain.
- University of Maryland, [*Women's Liberation*, 23 February 1972, Cleveland](https://recoveringdemocracyarchives.umd.edu/rda-audio/?ID=117) (Recovering Democracy Archives).
- Shirley Chisholm, ["For the Equal Rights Amendment"](https://voicesofdemocracy.umd.edu/chisholm-for-the-equal-rights-amendment-sources/) (10 August 1970). The text is in the Congressional Record. No public-domain audio was confirmed.
- A 1908 recording of Christabel Pankhurst is reported as public domain. Emmeline Pankhurst's own voice was not found.

Two ways to get them in:

1. Allow archive.org (and movingimagearchive.com) under Network access in the environment settings. Then search the
   Prelinger and Internet Archive collections for public-domain recordings, transcribe them and cut the passages in.
2. Supply the recordings you have rights to, and they will be placed in part C.
