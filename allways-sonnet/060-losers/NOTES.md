# 060-losers — Losers: Social Position Through Montage (smallest honest archive version)

Files: `edl.json` → `060-losers.mp4` (tight opening, 36.7 s, 3.1 MB) + ledger.
`edl-alt.json` → `060-losers-wide.mp4` (wide-opening comparison, 39.7 s, 3.1 MB) + ledger.
`contact.jpg` / `contact-wide.jpg` take one frame per second. `mk.py` regenerates both EDLs.
Revision: first assembly, 2026-10-31. Builder: `pairs` (scratch agent). **Independent critic review: PENDING. No critic session took place.**

How I checked: still frames only. I used a contact sheet of all 405 clips, 1 fps strips of the dance, classroom and playground candidates, a 2 fps tile of every clip used, scene-change detection, a spectrogram and volumedetect. I did **not** watch at speed or listen.

**This is deliberately smaller than the prompt (60–75 s, a worktable, a chair, a bag).** The prompt calls for staged adult performers unless a documentary sequence already contains all the relations. No such sequence exists in the local archive (see §2). I used the only passage I found where the social positions are *produced inside one source film's own continuity*. It is a staged 1953 social-guidance film, and the end card says so.

## 1 · Theorem as adapted

A tight view of a huddle of boys reads as private banter around one boy who ends up alone in frame. The source's very next shot, the wide room, shows *why* the huddle exists. Girls stand in a line along the far wall, the boys are on the other side, and the floor between them has to be crossed. Each person's position (who waits, who crosses, who is pushed forward, who is left) is set by the room's arrangement and the others' conduct, not by a trait of the boy. The comparison cut opens on the room geography first, so the viewer can compare how the two openings distribute responsibility across the *same observed actions*. Nobody is labelled. No motive is assigned.

## 2 · Forage log

- Searches: `classroom|school|pupil|teacher`, `playground|children play`, `dance|party|teen|date`, `chair|sit|seat`. I then went through the full 405-clip contact sheet looking for any shot where one person's position is visibly produced by others.
- Candidates considered:
  - *Beginning to Date* (1953): 3b640aa6 (huddle → room → asking a girl to dance), 22ba9c11 (packed floor → a girl seated at the margin with a boy), and stills/loops 22a114dd, 27697678, b02745f5, 2c2401f2. **Used.**
  - *Fatty's Magic Pants* (1914), 87f91a18: a heavy man dances alone in a ring of formally dressed onlookers. **Rejected.** It is slapstick built on his body, so using it would risk ridicule, and its track is a modern music bed (−21 dB).
  - *Duck and Cover* (1951), acd4a4cf: a classroom, but a drill with no interpersonal positioning. *Sleep for Health* (1950), a0520ffb: boys in a gym, 7 s, no relation visible. *[Ivan Besse amateur]* (1938), cfdc3fa9: a football scrimmage, too distant. *Going Steady?* (1951), e3bb83b5: a shot/reverse-shot conversation, a relation between two people only. *Health: Your Posture* (1953), 0f8a091e 38–54 s: a teen party, crowded, with no readable exclusion.
- **Surprise.** The 1953 producers themselves opened this passage *wide*. The shot before the huddle (22a114dd, 490.7–499.9 s in the source) is the room geography: girls in a curve along the wall, boys in the foreground, empty floor between. So the source's own order is the prompt's "comparison edit that begins wide". The tight opening is my edit, made by dropping that shot.
- **What the archive does not have:** any worktable or chair-into-a-gap scene; any visible *obstruction* by one participant (the prompt's bag); any sequence where an initially isolated person then *initiates* the next shared task; any non-narrated sync sound of a social scene (chair scrapes, paper handling, the silence after a request).

## 3 · The cut

**Tight opening (`edl.json`)**

| t | source · id · clip in–out · film time | what is visible | why |
|---|---|---|---|
| 0.0–6.95 | *Beginning to Date* 1953 · 3b640aa6 · 0.0–6.95 · 499.9–506.8 s | Tight on boys in suits. One talks at a stockier boy; a hand on a shoulder; the left boy turns away. The stocky boy is left in frame, smiling. | Withholds the room, so the huddle reads as about *him*. |
| 6.95–17.1 | same clip · 7.0–17.15 · 506.9–517.0 s (source cut at 6.97 s; the scene detector also flags frame flicker at 8.7–9.2 s inside this shot) | Wide: girls lined along the far wall; a boy crosses the floor and asks a girl in a white dress; they begin to dance while others pair off around them. | The reveal: the positions belong to the room's arrangement. Whether the crossing boy is the stocky boy **cannot be confirmed from frames**, and I do not claim it. |
| 17.1–18.1 | black | | A seam marking that what follows is **not the same moment**. |
| 18.1–32.7 | *Beginning to Date* 1953 · 22ba9c11 · 0.0–14.6 · 594.8–609.4 s (about 95 s later in the film; source cut at 1.9 s) | Packed dance floor; then a dim close shot of a girl seated at the margin by a table, a boy beside her who looks up and away; a third figure; darkness. | Coda, *montage relation within the same film*: a later moment where someone sits outside the dancing. An unresolved look, no outcome. |
| 32.7–36.7 | card: "Beginning to Date (1953) · a staged social-guidance film / Sources: movingimagearchive.com · see ledger" | | Staging label (protected condition) and sources. |

**Wide-opening comparison (`edl-alt.json`)**: identical, except that it opens on **22a114dd as a still** for 3.0 s (0.0–3.0). That is the source's own preceding wide shot, and only a thumbnail of it exists locally. Everything after shifts by 3.0 s: tight 3.0–9.95, wide 9.95–20.1, black, coda 21.1–35.7, card. The still is a held frame. It is marked as such in the EDL label and in the ledger (`media: still`).

**Context and reaction map (staging status: every shot is STAGED by the 1953 producers; performers are uncredited in the index)**

| participant (described, not named) | action | response visible in the same shot | scene evidence |
|---|---|---|---|
| stocky boy | stands in the huddle, smiles | others talk at him and touch his shoulder, then turn away | 3b640aa6 0–7 s, one shot |
| girls along the wall | stand, wait, some talk to each other | one is approached; she accepts | 3b640aa6 7–17 s, one shot |
| boy crossing | walks across the open floor, asks | the girl in white steps forward to dance | same shot |
| girl at the margin (coda) | seated by a table in the dark | a boy beside her looks up; no exchange is visible | 22ba9c11 5–14 s; a **different scene**, linked only by montage |

No reaction is moved between scenes. The only cross-scene link is the coda, and it is marked by the black seam.

## 4 · Departures from the prompt's hard proof

- No newly staged worktable scene. This is found staged footage from 1953, and the relations are the producers' staging (a dance-etiquette lesson), not an observed exclusion.
- No obstructor, no "third person moves their own chair", and no isolated person who re-enters by passing the work on. **The archive cannot honestly supply the prompt's agency beat.** I did not fake it by cross-cutting a different film. The person "initially read as isolated" (the stocky boy) is not shown regaining agency. The crossing boy and the girl in white do act, but I cannot confirm identities across shots.
- 36.7 s / 39.7 s instead of 60–75 s, because only about 32 s of motion footage from this film exists locally.
- **Sound.** The source track (about −43 dB, raised +8 dB globally and +10 dB per layer) shows speech-like harmonic bursts in the spectrogram. It may be the film's narrator rather than the dancers. It is **not transcribed or verified**. Chair scrapes and paper handling: none.

## 5 · Self-review against §5 (builder's reading of frames; NOT a critic verdict)

- *Exclusion located in visible actions, not narration*: partly. The room geography (a line of waiting girls, an open floor) is visible. "Exclusion" is too strong a word for what is mostly etiquette staging. The visible fact is *who waits and who must cross*.
- *Reveal changes the reading of an earlier moment*: plausible in the tight cut. The huddle becomes part of a room-wide arrangement. Perceptual, untested.
- *The initially isolated person keeps agency beyond being rescued*: **not achieved.** He is not seen again with certainty.
- *Ending avoids bully/victim/hero identities*: yes. Nobody is rescued and the coda ends in an unresolved look.
- Structural: every response is in the same shot as its action (verified by frames and scene detection), except the coda, which is marked by a seam. The staging label is in the end card of both exports and in each EDL label.
- **Largest gap**: no source carries the prompt's obstruction-and-agency structure. The proof shows only the first half of the theorem (a position revealed by widening), using a 1953 film whose own purpose was to teach these roles.
