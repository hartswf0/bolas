# 056-symmetry — Symmetry: Imperfect Pairing (archive proof)

Files: `edl.json` → `056-symmetry.mp4` (53.9 s, 2.6 MB) + `056-symmetry.ledger.json`.
Sequential-cut alternative: `edl-alt.json` → `056-symmetry-alt.mp4` (96.3 s, 4.8 MB) + ledger. Same in/out points as the split screen, played one after another full frame. After rendering, the alt was re-encoded at x264 CRF 27 (the renderer uses CRF 23) to keep it under the ~6 MB budget. Picture and timing are unchanged.
`contact.jpg` / `contact-alt.jpg` take one frame every 2 s / 3 s. `mk.py` regenerates both EDLs.
Revision: first assembly, 2026-10-31. Builder: `pairs` (scratch agent). **Independent critic review: PENDING. No critic session took place.**

How I checked: I looked at still frames only. That means contact sheets of all 405 sound clips (5 frames each), 1 fps strips of about 30 candidates, 1.5–6 fps tiles around in/out points, ffmpeg scene-change detection, and RMS/volumedetect readings. I did **not** watch any clip or the finished film at normal speed, and I cannot listen. Statements about sound are level readings, not hearing.

## 1 · Theorem as adapted to archive footage

Two panels side by side, each from a different film and a different decade, first agree on a shared gesture: a man bent over paperwork at a desk, two hands placing small parts, a man in a dark suit with his back to us before a closed door. Then each pair separates in a way that changes the relation: one record ends while the other continues; one assembly stays done while the other is taken apart again; one man knocks while the other waits silently beside a witness. The likeness is supposed to send attention to the particular room, decade and purpose of each film. It does not claim the people are equivalent.

The panels are 320×240 at native scale (k = 1.0, `fit: contain` into half-width boxes). There is no crop, mirroring, retiming or warp, and the ledger records each identity transform. Each panel ends where its own footage ends or at its own source cut. A panel that runs out goes black. It is never frozen or looped.

## 2 · Forage log

- **Method.** I made contact sheets of all 405 clips (`scratchpad/pairs/all_00..11.jpg`). Then `forage.py` regex runs for `chair|sit|seat`, `knot|tie|rope|string`, `hand`, `classroom|school`, `playground`, `dance|party|teen|date`, `pray|church|ritual|wash|kitchen|cook|tea|...`. The queries are mostly misleading. For example, "chair|sit" returns crop-dusters and museum halls, so every choice was made from frames.
- **Sitting down.** Nothing in the archive shows a person *preparing to sit and sitting* in a clear, readable action. The closest material is a woman flopping onto a sofa for about 1 s (*Let Yourself Go*, 1940, 46874a7c), men already seated in armchairs (*Financial Investigation*, 2004, cd9add6a; *Alcohol and the Human Body*, 1949, db4a7675, which I rejected because of the film's diagnostic framing), and two people seated in wicker garden chairs (amateur film, 46cd8d58). I substituted **two men already seated at desks over paperwork**: *Two Pay Days* (1927) and *Bookkeeping and Accounting* (1945).
- **Knot tying.** None. No rope, string or lace is being tied anywhere in the clip set. The substitute is **two hands placing small parts**: setting type into a composing stick (*Learning to Set Type*, 1959) and fitting rocket-payload model parts (*Wallops Island launch facility*, 1965). The Wallops hands withdraw, leave the parts standing, then come back and lift the top piece off. That is as close as the archive gets to "one finishes, the other must start again".
- **Waiting beside an empty chair / pulling a chair away.** None. The substitute is **two men facing a closed door**. *The Door to Heaven* (1941) has a man pounding on a white door painted "Door to Heaven" against a starred backdrop. *Wreckless* (1935) has a man standing hat in hand at a panelled office door while a seated secretary watches him.
- **Surprise.** The door pair. Both men are seen from behind in dark suits, framed at almost the same size, and both are in front of a closed door. Yet one is an allegorical set and the other a mundane office with a gatekeeper. It was found through the `door` cluster, not through any "waiting" query.
- **What the archive does not have for this concept:** ordinary chairs used in action, knots, an empty chair held in frame, and any pair in which *both* sides have non-verbal sync sound. Most sound tracks are narration or room hiss (see §4).

## 3 · The cut (main, `edl.json`), left panel | right panel

| t | left (source, year · id · clip in–out · film time) | right | why / what changes |
|---|---|---|---|
| 0.0–6.8 | *Two Pay Days (Part I)* 1927 · 3b9d2889 · 0.0–6.8 · 187.3 s. Man in a waistcoat counts at a desk. Silent source. | *Bookkeeping and Accounting* 1945 · c688de99 · 0.0–6.8 · 515.1 s. Young man writes in a ledger, phone at his ear. Source sound +4 dB (speech-band track; content not transcribed). | **Correspondence**: the same posture, head down over paper, and similar desk framing. |
| 6.8–11.4 | same · 6.8–11.4. The man keeps counting, then the source's own cut at 8.5 s to a desk-calendar insert, "Pay Day". | **black** (footage ends at 6.8 s; silence) | **First mismatch held 4.6 s**: one record stops; the other continues to name what the paperwork was for. |
| 11.4–24.4 | *Learning to Set Type* 1959 · aaf17c56 · 1.0–14.0 · 542.6 s. Right hand sets pieces of type into a composing stick held in the left. Source sound +6 dB. | *Wallops Island launch facility* 1965 · e617813e · 2.0–15.0 · 570.1 s. Fingers fit small parts onto a payload model. Muted. | **Correspondence**: pinching fingers placing small metal parts. Each side has its own sound in turn. |
| 24.4–29.9 | same · 14.0–19.5. Source dissolve to a close view: the filled stick held still. Sound on. | same · 15.0–20.5. Hands withdraw; the parts stand alone. Sound on. | Both tracks together. Both tasks look finished. |
| 29.9–34.4 | same · 19.5–24.0. Still. **Muted.** | same · 20.5–25.0. Hands return and lift the top part off. Sound on. | **Divergence**: one finished thing stays finished; the other is taken apart again. One side goes silent. |
| 34.4–47.0 | *The Door to Heaven* 1941 · 9199c819 · 0.6–13.2 · 359.9 s. Man walks to a white door labelled "Door to Heaven" and knocks repeatedly. +6 dB. | *Wreckless* 1935 · ef7bfc89 · 5.6–18.2 · 328.6 s. Man walks to a panelled door beside a seated secretary and stands waiting, hat in hand. +8 dB (low room tone, falling). | **Correspondence**: back view, dark suit, closed door, same scale. **Difference**: insistence versus waiting; alone versus watched. |
| 47.0–48.7 | **black** (the left source fades out at about 13.3 s) | same · 18.2–19.9. He turns from the door and walks toward the camera. | **Final hold**: the knocking side has ended; the waiting man leaves. The ending expectation differs from the opening match. |
| 48.7–49.9 | black | black | |
| 49.9–53.9 | card: "Sources: movingimagearchive.com · see ledger" | | |

Every film time is in the ledger as source start + clip in.

**Sequential alternative (`edl-alt.json`, 96.3 s):** *Two Pay Days* 0–11.4 → *Bookkeeping* 0–6.8 → *Set Type* 1.0–24.0 → *Wallops* 2.0–25.0 → *Door to Heaven* 0.6–13.2 → *Wreckless* 5.6–19.9, each full frame (k = 2.0), each with its own sound. It answers the prompt's question of which relations need simultaneity. My expectation, **not yet tested by a viewer**: the hands pair (finish vs. restart) and the door pair (knock vs. wait) lose most of their force in sequence, because their divergence lives in the *same seconds*. The desk pair may read about as well sequentially, because its difference is an ending (the "Pay Day" insert) and not a simultaneous action.

## 4 · Departures from the prompt's hard proof

- None of the three prescribed actions (sitting down, tying a knot, empty chair / chair pulled away) exists in the clip set. All three pairs are substitutions, documented above. The theorem (agreement first, then a consequential difference, kept visible) is kept. The specific choreography is not.
- **Sound.** The renderer mixes every layer to one stereo bus and has no per-panel pan, so "left and right sound stems" are done as *turn-taking*: one side audible, then both, then one silent. They are not spatially separated. Most tracks are narration or room hiss, and I did not transcribe the speech (no ASR tool). The 1945 and 1959/1965 tracks carry speech-band energy that is probably narrator voice and not the people on screen. A listener should check this.
- **Onset alignment** is approximate, from frames at 2–6 fps. It is not frame-exact.
- The ~50 s target was met (53.9 s with card).
- All six sources are staged instructional or fiction films. None is an observational record of the people shown.

## 5 · Self-review against §5 (builder's own reading of frames; NOT a critic verdict)

- *First correspondence understood at display size*: likely. Both desk panels are medium shots of a man bent over paper at 320×240. Perceptual, unverified.
- *Preserved mismatch adds information*: the black right panel while the left reaches "Pay Day" is deliberate and held for 4.6 s. Whether it reads as meaningful or as a missing clip is the main risk.
- *Each participant keeps an identifiable context*: yes in frames. 1927 waistcoat and ornate desk vs. 1945 office and telephone; a stage set with painted stars vs. a panelled office with a secretary.
- *Final hold has a different expectation from the opening*: the ending is a man walking away from a door that did not open, against a black panel. This differs from the opening's parallel diligence.
- *Critic can say why a pair belongs together without equating people*: untested.
- Structural checks: every panel has a different source film (6 distinct). Every transform is an identity scale (k = 1.0 split, k = 2.0 sequential), with no crop of protected subject regions, because `contain` at native size shows the full frame. **Largest gap**: no pair was found for the prompt's actual opening event (two people preparing to sit), and the stereo panning the prompt implies is not available.
