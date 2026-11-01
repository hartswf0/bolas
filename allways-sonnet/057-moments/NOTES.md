# 057-moments — Moments: Microevent Attention

Files: `edl.json` → `057-moments.mp4` (52.8 s, 3.3 MB) + `057-moments.ledger.json`;
alternate duration cut `edl-alt.json` → `057-moments-alt.mp4` (37.4 s, 2.4 MB, all events made roughly equal, no long hold) + ledger; `contact.jpg`.
Revision: first assembly, 2026-10-31. Builder: words-moments (scratch agent). **Independent critic review: PENDING.**

How I checked: contact sheets of all 405 clips and 474 loops, then 8–10 frame sheets of about 30 candidates at specific in/out ranges, plus audio level envelopes and spectrogram images. I did **not** watch at normal speed and could not listen. Event descriptions come from still frames sampled every 0.3–1.5 s. Claims about sound come from level and spectrogram readings, not from hearing it.

## 1 · Theorem as adapted to archive footage

Short ordinary events from unrelated films, each kept whole (before, change, after), should feel complete enough to matter. One unusually long hold should change how the viewer watches the next events: a hand waiting next to a fixture before it places a knob. After that hold, the aftermaths (a table without hands, skin settling, an emptied pavement, an emptied room, water gone still) should register as events in their own right. The film ends on an earlier location after its event is over.

## 2 · Forage log

**Method.** I built my own contact sheets of every sound clip and every loop (`scratchpad/words-moments/sheets/`). Then I searched loop metadata for `pour|cup|glass`, `latch|lock|key|door`, `cloth|laundry|sheet|curtain|blanket`, `empty (room|chair|hall)|leaves`, `hand|fingers|sleeve|glove`, and checked the hits by frames (`sheets/moments_loops.jpg`). Loops turned out to be 3 s silent fragments, usually cut mid-event, so the film uses only clips.

**What came back.**
- Hand-scale events with a visible before and after: `7102b861` *Key to Our Horizons* (1952), a hand holds a round knob beside a fixture for about 8 s before fitting it. `222b8362` *The Welding Operator* (1942), fingers drop something into a beaker of water. `0e86363a` *Best Food In Town*, hands break a roll, then the same table without hands. `1570ec0b` *Hydration* (2004), a pinch of skin is released and settles. `f1c85218` *Winter in Den Haag* (1922), wooden skates strapped on, a hand works the strap.
- Waiting: `cd47717f` Ivan Besse amateur film (1938), a toddler pats a closed door, turns and waits.
- Leaving and emptiness: `6a336c56` *The Door to Heaven* (1941), a girl waves from a doorway and leaves, a man crosses, the lamp-lit room holds. `14c8b94b` *Third Avenue El*, a man seen from above walks under a roof and the pavement stays empty.
- Also seen, not used: Valley Town (1940) `df82dd90`, a man wiping an empty plate with bread (strong, but it brings the film's unemployment drama with it); Two Pay Days (1927) calendar page; Speech: Platform Posture (1949) feet shifting weight; Court to Court (2001) a corridor where a figure walks away; laundry in wind `30fe8bbc` (moves, never settles); JFK EXHIBIT 3 reconstruction corridor (empty, but excluded because of its context).

**Surprising.** The fixture shot in *Key to Our Horizons* is almost entirely waiting: the hand sits beside the fixture for most of the take, and the actual placing takes about 2 s at the end. It is the "hand deciding" event the prompt imagines, and it exists by accident in a 1952 industrial film.

**What the archive does not have.** A sleeve catching on a handle, water reaching the brim of a cup, a latch heard clicking, someone choosing where to put a *key*, and a cloth settling after being shaken. **Above all, location sound.** Almost every clip with sound carries narration, dialogue or score. The handful of silent amateur reels have only transfer hiss.

## 3 · The cut (main, `edl.json`) — event log

| t (film) | source (year) · clip · clip in–out | onset → change → aftermath | substitution for |
|---|---|---|---|
| 0.0–8.6 | *Winter in Den Haag / IJs in Den Haag* (1922) · f1c85218 · 1.0–9.6 | strapped wooden skate on ice → a hand works the strap (≈3.5–4.5 s in film) → the foot set down, strap holding | sleeve catching on a handle (small resistance, close) |
| 8.6–12.1 | *The Welding Operator* (1942) · 222b8362 · 0.0–3.5 | fingers hover over a beaker (short anticipation) → something dropped in → water clouds and churns | water reaching the edge of a cup |
| 12.1–17.1 | Ivan Besse amateur film, Britton SD (1938) · cd47717f · 0.2–5.2 | toddler faces a closed door → reaches up and pats it → turns and waits; nothing opens | waiting for a latch to click |
| 17.1–28.0 | *Key to Our Horizons* (1952) · 7102b861 · 0.3–11.2 | **LONG HOLD, 10.9 s.** A hand holds a round knob beside a fixture → fits it into place → withdraws; the knob stays (≈1 s) | a hand deciding where to place a key |
| 28.0–32.0 | *Best Food In Town* · 0e86363a · 0.4–4.4 | hands break a roll at a set table | — |
| 32.0–35.0 | same · 6.4–9.4 | the same table with no hands: rolls, glass (the source's own next shot) | aftermath |
| 35.0–38.4 | *Hydration* (2004) · 1570ec0b · 0.2–3.6 | skin pinched → held → released, settles back slowly | a cloth settling after being shaken |
| 38.4–41.6 | *Third Avenue El* · 14c8b94b · 0.0–3.2 | a man crosses a pavement from above → passes under a roof → the pavement remains | lead-in to absence |
| 41.6–48.5 | *The Door to Heaven* (1941) · 6a336c56 · 7.8–14.7 | a girl waves from a doorway and leaves → a man crosses → the lamp-lit room holds about 2.4 s after both have gone | the empty space after a person leaves |
| 48.5–49.8 | *The Welding Operator* (1942) · 222b8362 · 1.9–3.2 | **RETURN**: the beaker again, its event over, water settling. Fades out | return to an earlier location |
| 49.8–52.8 | card | "Sources: movingimagearchive.com · see ledger" | |

Attention anchors: strap/hand, fingertips over the water, the toddler's raised hand, the knob, the roll, the skin fold, the walker's head, the doorway, the water surface.
Pacing curve: 8.6 → 3.5 → 5.0 → **10.9** → 4.0 + 3.0 → 3.4 → 3.2 → 6.9 → 1.3. Short events lead up to the long hold. After it, the aftermath and absence shots slow back down to the room hold, and the return is deliberately brief.

**Sound map (measured levels, not listened to):**
- E1, Den Haag 1922: no audio track. Silence.
- E2, beaker: narration, muted.
- E3, toddler 1938: source hiss kept (≈ −56 dB), the honest silence of an amateur reel.
- E4, knob: narration, muted.
- E5a, roll: the source's pre-narration bed kept at −2 dB (≈ −45 to −54 dB). In the spectrogram it reads as low room tone or quiet music; not verified by ear.
- E5b, plate: narration starts here, muted.
- E6, skin; E7, El; E8, room: narration, music and dialogue all muted.
- E9, return: the source's hum between narration phrases kept (≈ −44 dB).
- No newly composed sound and no score. In practice most of the film plays in silence.

**Alternate duration cut (`edl-alt.json`):** the same ten events trimmed to 3–4 s each. The knob shot becomes just the placing (7.6–11.6). The room keeps only the empty hold (9.6–13.6). This is the control for whether the long hold changes attention.

## 4 · Departures from the prompt's hard proof

- **All six named events are substitutions** (see the table). The archive has no sleeve, cup brim, audible latch, key or settling cloth. I chose stand-ins that keep the structure of each event (resistance; anticipation then a payoff; waiting at a closed opening; a hesitant placement; settling; absence), and each one is logged.
- The "settling cloth" became skin in a hydration demo (2004). It is a hand demonstration in a health film, not a diagnosis of anyone, and it is included for the slow return to rest.
- **Location sound: not achieved.** The prompt asks for location sound that crosses one boundary. No clip I found has sync location sound free of narration, and I could not transcribe narration to caption it. So narration is muted and the film is largely silent. This is the biggest gap against the prompt.
- About 53 s, not 60. The usable footage after each event's aftermath runs out (the Door to Heaven room hold is 2.4 s before the source cuts away), and I did not loop or slow anything.
- The final empty room does not "continue after the expected cut" for long, because the source cuts at 14.9 s. The long hold is carried by the knob shot instead.
- Sources span 1922–2004, colour and black-and-white. Nothing implies the events happen in one place or one time.

## 5 · Self-review against §5 (builder's own view, not acceptance)

- *Critic can describe the change in each microevent:* plausible for the beaker, toddler, knob, roll/plate and room, from frames. The skate strap action is brief and may not read. The El walker is small in frame.
- *A held aftermath feels necessary:* the knob holding after the hand leaves (≈1 s), and the empty room (≈2.4 s). Both are short, so this is a risk.
- *Pacing varies for identifiable reasons:* yes by construction (the curve above). The alt cut is the comparison.
- *Return activates memory:* a brief return to the beaker (1.3 s). It may be too short to be recognised.
- *Specific without music:* the film has no music beyond the possible faint bed in E5a, so this is satisfied trivially.
- Structural: the ledger maps each event to its source range. The renderer concatenates with no gaps. The beaker return (1.9–3.2) overlaps the beaker opening (0.0–3.5) by design. Muted narration means no source audio decay is cut except the E5a bed, which fades over 0.5 s.

**Critic verdict: PENDING.** I inspected frames and contact sheets; I did not watch at speed.
**Largest unresolved limitation:** no location sound. The archive's audio is narration or score, so the prompt's acoustic-space structure (ambient entrances, decays, one boundary-crossing sound) cannot be built, and the film relies on picture alone.
