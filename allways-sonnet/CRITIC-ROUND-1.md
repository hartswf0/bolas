# Critic round 1 · ALLWAYS first batch

An independent critic agent reviewed eight films (055, 057, 058, 059, 061, 062, 063, 064) on 2026-10-31.
It did not make the films. It read 4 fps frame sheets with timecodes, scene-cut measurements and
audio levels/spectrograms. It **could not listen**, and it wrote each verdict before reading the
builder's notes. These are an AI critic's readings; human screening has not happened.

## Repairs made after this round

| film | verdict | repair applied |
|---|---|---|
| 059 Ball | pass | jet shot now ends at 35.2 s, before the source's own page-turn effect; source card no longer clipped |
| 055 Words | pass (qualified) | whiteboard shot removed; the statue now cuts straight back to the opening map (44.8 s) |
| 058 Laughs | inconclusive, ethics flags | grey runout and the closing boys shot (which isolated one boy amid group laughter) removed; the film ends on black (37.2 s). The car-to-stage cut across sources and the face-covering man remain open for human review |
| 061 Matter | inconclusive, protected condition breached | the grain-growth animation is now captioned "animated diagram, not filmed metal" |
| 064 Parabolas | pass | not yet: labels still small (critic: double them, hold each model 3 s) |
| 062 Colors | pass (qualified) | not yet: the middle needs one blue chapter, the red chapter more time |
| 057 Moments | inconclusive | not yet: the opening skate shots show no change; cut them |
| 063 Breath | **fail** | not yet: needs a faceless human exhale the cache does not contain; v2 waits for live archive search |

The critic's full text follows. Timecodes refer to the cuts before these repairs.

---

# ALLWAYS batch 1: independent critic review

How I reviewed: I did not make these films. For each main cut I read 4 fps contact sheets with burned-in timecodes. I measured cuts with ffmpeg scene detection (threshold 0.3). Sound was checked with per-0.5 s RMS, volumedetect and spectrograms. **I could not listen. Every statement about sound comes from levels and spectrograms only.** I also checked the comparison cuts where they mattered: 059-control, 058-context and 058-alt, 061-alt-sourcesound, 055-alt, 057-alt. I wrote each verdict before opening that film's NOTES.md. The only exception is the EDL source IDs, which I read as a structural check of whether adjacent shots share a source. I did not read the EDL labels before forming my visual readings. Frames and spectrograms are in this folder.

Verdict scale: pass / inconclusive / fail. I had no reference film to compare against, so no film gets "reference stronger".

---

## 055 Words: Polysemic Relay. **PASS (qualified)**

- **Observations**
  - I worked out the word "draw" by about 22 s without any text.
    - 0–3.5 pencil on a map (inscribe)
    - 3.5–6.75 film pulled off a reel (pull out)
    - 6.75–12.9 cards drawn at a café table
    - 13.0–22.1 a draw on a cigarette (the inhale is visible 14.5–17.5)
    - 22.2–25.5 particle between N and S magnet blocks (attract)
    - 25.6–31.5 a crowd, then 31.6–39.0 a statue hauled on a cable (draw a crowd / draw up)
    - 39.0–43.4 a whiteboard diagram being drawn
    - 43.5–46 the map pencil returns
  - Transitions follow the sense, not the shape. The magnet cut at 22.2 is the real pivot from hand-pulling to force-pulling.
  - Sound, measured:
    - Audio exists only at 0–1 s, 3.5–6.7 s (about −56 dB, barely audible) and 13–21.5 s (about −33 dB).
    - 22.2 s to the end (27 s) is **digital silence**. Sound stops supporting inference exactly where the film turns.
    - At 18.5–21.5 the smoker's lips move under audio with formant-like structure. There are no captions. It may be music, as the builder says, but this needs an ear check.
- **Largest gap:** The emotional turn and the return do not land. The whiteboard diagram (39–43.4) reads as a classroom and deflates the crowd and statue section. The return to the map at 43.5 reads as "the same shot again", not as a changed meaning.
- **Repair (falsifiable):** Cut the whiteboard (39.0–43.4) and go straight from the statue on its cable (end about 38.5) to the map pencil.
  - Prediction: a viewer asked "what is the pencil doing in the last shot?" answers something like "drawing a line / border / route", not "sketching".
  - If they still say "sketching", the return needs a different final image.
- **Strength to protect:** the cigarette "draw" (13–22), the only shot where sound and the sense meet, and the unexplained, unbridged magnet pivot at 22.2.
- **Ethics:** The crowd and the statue come from the same source (5524afe5, per the EDL), so their adjacency does not invent an encounter. The statue removal (1921) is civic and political. It is fine as used, but it should not be pushed further toward celebration or mockery.
- **Builder claims I disagree with:**
  - NOTES says that after the turn come "forces that pull things and people … and an emergency flight path". The whiteboard does not read as an emergency flight path. It reads as a lecture diagram.
  - NOTES says the return makes the pencil line "read as a planned route". I did not perceive that.
  - NOTES says captions are moot because no speech is audible. That is unverified for 13–21.5.
  - The 055-alt "curtain" pivot (22–30 in the alt) is at least as legible as the magnet, despite NOTES saying no drawn curtain exists. It shows a curtain in motion beside a lamp.

## 057 Moments: Micro-event attention. **INCONCLUSIVE**

- **Observations**
  - **0–8.4 is three near-static inserts of skates on ice.** A full-resolution check found no legible change. The film opens on an inventory of picturesque fragments, which is exactly what the theorem rules out.
  - Real micro-events, each with a beginning, change and aftermath:
    - 8.5–12: a hand drops a tablet into a beaker and the water clouds.
    - 12–17: a toddler pushes a door, turns, and holds an aftermath stare at the camera, 14–17.
    - 35–38.4: a pinch of skin is released and slowly recovers.
    - 41.6–48.5: a girl and then a boy leave through a doorway, and the **empty lamp-lit room is held 46.25–48.5**. This is the one aftermath that feels necessary.
  - Doorknob, 17–28: about 8 s of a motionless hand, then a wipe at 25.25–26.5 reveals a gleaming knob, held for only 1.25 s.
    - The deliberate long hold comes *before* the change. It builds anticipation, but it is not a held aftermath.
  - The return to the beaker (48.5–49.75) does call up the first event, but only for 1.25 s, and it fades out.
  - Sound is almost absent: digital silence except −55 dB hiss under the toddler, about −45 dB under the bread, and about −40 dB under the beaker return.
    - Oddly, the first beaker event (8.5–12) is silent while its return has sound.
- **Largest gap:** The opening 8.4 s teaches the wrong unit. It is a fragment, not an event. Because of that, the 8 s knob hold reads as more stillness instead of attention that has been sharpened.
- **Repair (falsifiable):** Remove the skates (0–8.4) so the film opens on the tablet drop.
  - Prediction: viewers asked "what changed in the first shot?" all answer, and during the knob hold they say they were waiting for something to happen, not that it was "slow".
- **Strength to protect:** the empty-room hold at 46.25–48.5, and the toddler's backward stare at 14–17.
- **Ethics:** None, apart from the general care owed to footage of identifiable children.
- **Builder claims I disagree with:** The table entry "a hand works the strap (≈3.5–4.5 s)" describes a change I could not see even at full resolution. That shot does not deliver an event.

## 058 Laughs: Audible contagion. **INCONCLUSIVE, leaning fail on the core (acoustic) clause**

- **Observations**
  - The separate source situations are clearly established:
    - 0–5.6 a boy at a window smiles and withdraws
    - 6–8.6 a man in a car throws his head back laughing
    - 8.75–11.6 a stage comic with a tankard and chorus
    - 11.75–16.7 children on a ride
    - 16.75–19.2 a street
    - 19.25–25.1 colour portraits
    - 25.2–31.2 a group of laughing girls
    - 32.2–38.75 boys in suits
  - The acoustic chain, measured:
    - Voice-band energy exists only in three blocks with hard edges: 11.75–16.75, 19.25–25.15 and 32.2–39.
    - **The two most intense visible laughs, the car man (−66 dB) and the girls (−55 dB, hiss only), are mute.**
    - The block edges are vertical in the spectrogram. There are no overlap windows, so onset → overlap → recovery never develops. There is no clipping (peak −13.7 dBFS).
  - **Montage-created exchange, not marked:** the car man's laugh at 7–8.6 cuts directly to the stage comic at 8.75. These are different sources (fb5bfa37 and c6291759), and the cut reads as audience and performer. That may be intended, but nothing helps the viewer tell this cross-source exchange apart from the girls' shared in-source laughter.
  - The grey frame at 31.2–32.2 is source runout. It reads as a dropout, not as a designed rest.
- **Largest gap:** There is no audible laughter chain. The film is a visual chain of grins over intermittent beds, so the theorem's acoustic spread is not demonstrated.
- **Repair (falsifiable):** Let the 19.25–25.15 voice block decay over 2 s into the girls' shot (25.15–27.5) at falling gain, and pre-lap the boys' room 1 s before 32.2.
  - Prediction: the spectrogram shows overlap at 25–27.5 and 31–32.2, and a listener says the girls "pick up" the previous laughter while still being able to say it came from a different place.
  - If they cannot tell, that is the theorem's distinction failing and has to be undone.
- **Strength to protect:** the girls' sequence (25.2–31.2) is real shared in-source laughter with physical contagion (leaning, grabbing). It is the best evidence in the batch for "people laughing together".
- **Ethics, needs review:**
  1. The film ends on the boys' scene with a heavy-set boy, head lowered and smiling uneasily (37–38.75), while others laugh around him. The relation exists in the source; the context reel shows school-dance egging-on. Ending on him isolates him as the butt of the joke.
  2. The builder's own flag also stands: the man shielding his face (16.75–19.2) sits next to unrelated laughter.
  3. The stage comic comes from a 1939 Amsterdam Jewish community film (per NOTES). Cutting a stranger's laugh "at" him (7–8.75) puts the comic in the role of the person laughed at, in a historically sensitive source. I would cut it.
- **Builder claims I disagree with:**
  - NOTES says "the runout grey … serves as the 'empty room tone' beat". It reads as a technical dropout.
  - NOTES says the ending shows "boys still smiling in conversation". The last 1.5 s reads as group laughter around one boy.
  - NOTES says "no laugh sound is placed under any other person". That is true for audio, but the picture cut at 8.75 still implies a reaction across sources.

## 059 Ball: Graphic constancy. **PASS (strongest proof in the batch)**

- **Observations**
  - From 0 to 17.5 the circle stays perceptually locked through sun → earth (3.5) → magnifier over a map (5.75) → magnifier over a document (8) → magnifier over an eye (10.25) → clock (12.75) → BORON dial (15.25) → octagonal meter (17.5–20.2).
    - The octagon is the irregular object, left uncorrected, and it adds tension.
    - Against **059-ball-control** the difference is obvious: the control's magnifier sits upper-left (6–7), the shower rose sits on the left edge (24), and the motorcycle wheel is large and lower-left (31–33).
  - Contextual release at 20.25–23.7: a wide lab shot, then a hand turning a control knob among the gauges, then the operator's face. The dials are recast as instruments of control.
    - The score withholds its pulses here: digital silence 20.2–23.7, measured.
  - The exit is clear. The planet drifts out of frame left (36.5–37.75), leaving stars and a passing satellite (39.75). The anchor literally leaves.
  - Sound is a synthetic tap score whose timbre changes by section (low thumps, then about 2.5–4 kHz pings, then lower triads, then broadband clicks), in the spectrogram only.
- **Largest gap:**
  - After the release, the second half (23.75–35.5: shower rose, speaker grille, reel, wheel, engine) goes back to plain matching. Meaning drifts but does not become more unstable, and there is no second release.
  - Craft faults: the jet-engine source's own page-turn effect is visible at 35.25–35.5 as a squeezed frame that reads as a render error, and the end credit line is clipped at both edges (40.25–43, "…ifteen round things … 1929–200…").
- **Repair (falsifiable):** End the engine shot at 35.2, before the source effect, and cut straight to the planet. Re-set the credit to fit the frame.
  - Prediction: no frame between 35.0 and 36.0 shows a non-uniform transform.
  - For meaning, a separate v2 test: widen the engine shot to show the aircraft and the person in red as a second release, and see whether viewers describe a change of scale or purpose there.
- **Strength to protect:** registration that holds through the opening, the uncorrected octagon, and the silent release.
- **Ethics:** none.
- **Builder claims I disagree with:** none of substance.

## 061 Matter: Material affordance chain. **INCONCLUSIVE, with one protected-condition breach**

- **Observations**
  - There are clearly more than three material responses, each visible inside its own shot:
    - 0–3.5 skin pinched and recovering
    - 3.6–6.4 paper creased
    - 6.6–9.4 foil pressed
    - 9.6–12.4 dye plumes in water
    - 12.6–20.3 a pour spreading into a disc, with a long satisfying hold
    - 20.4–23.4 molten metal
    - 23.4–32 nozzle deposits keeping their tails
    - 32–41.4 a lathe chip curling and keeping its curl
  - The metal → red-deposit cut did **not** read to me as the same material, which is good.
  - **45.0–55.0: I read this, without notes, as real drying cracks forming after the "steam" shot at 41.5.** It is in fact an *animated diagram* of grain growth (EDL/NOTES). Nothing on screen marks it as constructed, so a simulated response came across as observed physical behaviour. That is a direct breach of protected condition 3 and tribunal item 3.
  - **The main cut is digitally silent (−91 dB).** "Sound communicates contact and recovery" fails outright.
    - The alt-sourcesound version has long blocks with syllable-rate harmonic striations (12.9–21, 43–64), which look like narration in the spectrogram.
  - Return at 55–58.4: the pinch is seen again after fold, set and curl. Recovery against permanence works as an idea.
    - The 6-up comparison grid at 58.6–61.6 spells it out and weakens it.
- **Largest gap:** Sound is absent, and the grain diagram passes for footage.
- **Repair (falsifiable):** Put a visible marker on 45.0–55.0, for example "diagram" burned in for the first 1.5 s, or a hard frame/inset that shows it is a drawing. Alternatively, drop it and hold the lathe chip.
  - Prediction: a naive viewer, asked whether 45–55 was filmed or drawn, says "drawn". I said "filmed".
  - Separately, a v2 must find any non-speech contact audio, even 2–3 s under the lathe and the pour.
- **Strength to protect:** the 7.8 s pour (12.6–20.3) and the lathe-chip hold (32–41.4). Both durations are earned.
- **Ethics:** none. Note that the skin-pinch shot (1570ec0b) also appears in 057 and the smoker shot appears in 055 and 063. Reusing them across films dilutes each one.
- **Builder claims I disagree with:** NOTES says "furnace → diagram are cuts between visibly different films". The furnace and the diagram are the *same* source, and the cut did not read as a change of kind. It read as cause and effect in one process.

## 062 Colors: Chromatic chapters. **PASS (qualified)**

- **Observations**
  - The chapters and their hinges:
    - Yellow, 0–7.4: firefighters, first hosing and then watching. These are different actions in the same hue.
    - **Mixed-colour hinge at 7.5:** a yellow engine swung out over teal sea. This hinge works.
    - Teal: a cargo net hoisted (10.25) and a ship (15.5).
    - A second hinge at 29.5: a pale crate over the teal sea against a red hull.
    - Red/orange: bag packing (32.25), volunteers unloading a van (35.25), a red harvester (38.25).
  - A thread of lifting and loading runs across the hues (engine, net, crate, bag, van), so each colour organises different stakes, not just different objects.
  - **The ending (41.25–47), a breakfast table, gathers every chapter colour**: teal cloth, red curtain, yellow wall, blue sweater, orange fruit. That gives the colours a shared situation.
  - Middle, 18.75–29.4: a glove under repair, a woman sniffing a foil pack, silhouettes against a blue screen. There is no dominant hue, and it reads as filler.
  - Sound is source sound with three digital-silence holes (26.5–29.4, 32.2–35.2, 38.2–41.2). These fall mid-chapter and read as dropouts rather than structure.
    - The breakfast audio shows speech-like striations, so stray dialogue is possible and needs an ear check.
  - I saw no evidence of selective recolouring. The tones look natural and untouched.
- **Largest gap:** The middle 10.6 s breaks the chapter logic, and the red chapter is three thin 3 s fragments.
- **Repair (falsifiable):** Make 18.75–29.4 a single blue chapter: keep the silhouettes against blue and drop the glove and foil shots. Give the time to the red chapter.
  - Prediction: asked to name the chapters afterwards, viewers list yellow, teal, (blue), red and then "everything at the table". Today I would expect most to stall at the middle.
- **Strength to protect:** the two mixed-colour hinges (7.5 and 29.5) and the breakfast-table ending.
- **Ethics:** Wildfire crew footage is fine as used. Volunteers at a van: no issue.
- **Builder claims I disagree with:** none major. I agree with the builder that the red chapter is thin.

## 063 Breath: Invisible force, visible consequence. **FAIL**

- **Observations**
  - Human breath appears only with faces: a smoker lighting up (0–3.6; no exhaled plume visible at 4 fps) and a singer or speaker in close-up (4.75–14).
  - Everything without a face is wind, steam or mist:
    - a dust storm projected behind the singer (14–19.2)
    - a sand yacht's sail (19.25–26.9)
    - a furnace or flame (27–30)
    - a steam jet (30–39)
    - a steam plume (39.25–43.6)
    - valley mist (44.5–53)
  - Without the title I would describe the film as "air / vapour / weather", not breath. The theorem's core ("notice breath without every shot needing a face") is not achieved.
  - There is no perceptible *comparison* between human and mechanical air, only a sequence of one block after the other.
  - Sound: source voice at 4.75–19.2 only, then **38 s of digital silence (19.3–57)**. That is one long dropout, not quiet intervals in a rhythm.
    - Black holds at 3.75–4.6 and 43.75–44.4 are the only designed rests.
  - The expansion and release shape does exist: the steam jet holds 9 s, then the plume breaks up, then the mist settles.
- **Largest gap:** There is no faceless trace of human breath, so "breath" never becomes legible through its consequences.
- **Repair (falsifiable):** Shorten the talking head (4.65–14.0) to at most 3 s. Immediately before the steam jet at 29.9, insert a faceless human exhale (a smoke plume leaving frame, or visible breath in cold air).
  - Prediction: viewers shown the film without its title name "breath / breathing" rather than "wind / steam".
- **Strength to protect:** the 9 s steam-jet hold (30–39) and the closing mist. As release imagery they are beautiful.
- **Ethics:** none.
- **Builder claims I disagree with:**
  - NOTES says the mechanical comparison works "structurally (separate block…)". A separate block is not a comparison the viewer feels.
  - NOTES calls the 38 s silence "purposeful". As measured, it is one undifferentiated block. Its makeup also does not match the EDL: it marks audio on for the steam (29.9) and the mist (44.4) shots, yet both render silent, presumably because those sources have no track. The ledger should say so.

## 064 Parabolas etc.: Curves with different causes. **PASS (most complete realisation in the batch)**

- **Observations**
  - The unannotated first pass (0–34.4) sets up the family resemblance before any overlay:
    - 0–7.4 a sagging washing line
    - 7.5–11.4 rows of laundry
    - 12.5–14.6 a pool dive
    - 14.75–18.4 a somersault off a platform
    - 18.5–25.5 a swan dive from a tower with the camera panning
    - 25.75–27.6 a hose jet
    - 27.75–31.4 a station arch
    - 31.5–34.4 museum arches
  - The annotated pass (34.5–46) makes the competing causes visible:
    - Model A: the pool dive with pan removed, where the guide fits.
    - **Model B: the tower dive with the camera moving, rms 10.6 px.** The orange screen track is jagged because of camera motion. The mismatch teaches that image trajectory is not body trajectory, and it does not look like a render error.
    - **Model C: the arch, parabola rms 4.0 px against circle rms 0.42 px.** It is a circle, not a parabola, with the excluded jamb points marked ×. This directly honours "do not label every curved object a parabola".
  - The film ends on the unannotated washing line (46–50.5). That is a curve of a third cause, hanging, and it gains interest from the comparison.
  - Sound, measured, sits only at impacts: the splash (12.5–14.6), the hose (25–27.6) and the splash again (34.4–36). That is economical and causally tied.
- **Largest gap:**
  - The overlay labels are about 10 px on a 640×480 frame. They are readable full-size but not on a phone, and they carry most of the argument.
  - The hose jet (25.75–27.6) reads as a *straight* line at this scale, the weakest member.
  - The station arch and the museum arch are redundant.
  - The final washing line's cause, a catenary rather than gravity on a projectile, stays invisible to anyone who does not already know it.
- **Repair (falsifiable):** Double the label size and hold each annotated model at least 3 s.
  - Prediction: viewing on a phone, a viewer can repeat "circle fits the arch better than parabola" after one viewing. Today I predict they cannot.
  - Also cut the station arch (27.75–31.4).
- **Strength to protect:**
  - The order: clean resemblance first, models second, unannotated return last.
  - Model B's honest misfit.
  - The 4.0 against 0.42 px arch comparison.
- **Ethics:** none. The museum shot's orange/blue look should be confirmed as source tint (it is not a protected condition here).
- **Builder claims I disagree with:** NOTES says there is "no clean hanging chain … so the catenary/parabola question … is not tested". The film nevertheless opens and closes on a hanging line, so it *raises* the question visually. That is a strength the builder undersells, but it is fair that it remains untested.

---

## Ranking

1. **Strongest:** 064-parabolas, then 059-ball. Both visibly prove their theorem (registration against the control, model against misfit) with clean endings. 055-words and 062-colors pass with clear, fixable gaps.
2. **Middle:** 061-matter and 057-moments. Both have good visual events, but 061 is silent and lets its diagram pass as footage, and 057 opens on non-events.
3. **Most need a v2:** 063-breath fails its core clause. 058-laughs has no audible chain and has ethics flags, including an end shot that isolates one boy and a cross-source laugh cut onto a 1939 Jewish community performer.
