# CINEOSIS HAND BUTTER: making-of, production record

A making-of film for the handmade CINEOSIS film, about 4 minutes long. The film's own cast performs it in a screening room:
- Bola and Shim;
- the Critic, a new third figure. He stands for the fresh blind reviewer and wears a blindfold, because he sees the pictures but not what was meant.

The film has eight scenes:

| # | Scene | Content |
|---|---|---|
| 1 | the film | |
| 2 | the archive | |
| 3 | by hand | |
| 4 | the shadows | |
| 5 | the critic | |
| 6 | the nose | 4.0 and 30.0 |
| 7 | the list | |
| 8 | next | |

## Observed and generated

**Observed (on the screen):**
- archival plates, raw: the atlas sheet, 10.4 and 7.2;
- frames of finished handmade passages: 10.4, 14.0, 14.1, 4.0, 30.0, 7.2, 21.1, 44.1, plus a montage of 18;
- frames of the automatic atlas film, in scene 3;
- the actual key code of 14.0 (crash/m_x14_0.js), in scene 3;
- the sign card for 14, from the handmade film.

The passages carry their own generated figures, as recorded in cineosis-handmade-validation.md.

**Generated:**
- The room: wall, curtains, floor, the screen mask, projection falloff and light spill.
- The three figures. Every body pose is keyed by hand in crash/m_hb1.js through m_hb8.js.
- The Critic's blindfold, drawn by the rig.
- Shadows. The projector is the key light, so shadows run along the floor and up onto the picture. The shared integration standard applies: contact patch, cast shadow, tone, grain, softening.

**Voices:**
- Synthesized locally with Piper, from open voice models:
  - Bola: en_US lessac;
  - Shim: en_US ryan;
  - the Critic: en_GB alan.
- No recorded human voices are used.

**Mouths:**
- Opened by the loudness of each synthesized line, sampled every 2 frames (hb/voice.py → crash/m_hb0.js). This is generated, not keyed by hand.
- Expressions are keyed by hand per line.

**Sound:**
- the screen's own track, low;
- synthesized footsteps and room tone.

## The Critic's lines

The lines he reads as quotes come from reviews that took place. All other dialogue is written for this film.

| Passage | Quote | Source |
|---|---|---|
| 14.0 | "Two outsiders join a strike with blank signs, and drop out." | round 4 blind read |
| 4.0 | "She stands frontally on the nose bridge throughout, with zero body movement." | round 3 blind read |
| 30.0 | "Confusing … it reads as a second figure inside the mirror." | round 4 blind read |
| 21.1 | "She appears to stand in mid-air." | round 4 reveal |

Other claims in the dialogue checked against cineosis-handmade-validation.md:
- 85 passages, 21.8 minutes.
- Shim appears in 14.0 and 14.1 only.
- 78 passages in the formula atlas.
- 10.4 time-remapped to her steps.
- 7.2 crumbs drawn.
- 4.0 shadow side fixed in round 3.
- 30.0 double listed as a weak spot.
- Review rounds 2, 3 and 4.
- The newest fixes have not been reviewed.

## Review

There has been no blind review of this film.
