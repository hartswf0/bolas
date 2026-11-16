# La Cité Raymond Queneau: swarm plan (round 3, build)

Revision: `plan-r3`. Direction: **2 · La maquette** (proposals/kf-2.png), as the user chose. This is a handmade cut-paper model of cream blocks with curved zinc roofs, a verge and a road, animated in multiplane. The windows light one by one as a kinetic score, and two soundtracks (A domestic, B surveillance) change what the same picture means.

The round-2 recommendation suggested a photographic opening (the Corbeil track, 0–8 s) with a match-dissolve into the paper model. **This plan declines that opening.** A photograph followed by a paper model reads as "illustration of a real place", and the dissolve would be a large picture event that the soundtracks have to share. That would blur which heard cue switched the reading. The picture stays wholly handmade, built from paper scans that are themselves foraged. Archive footage is used only as an untraced gait-timing reference, and as sound.

---

## 1 · Creative thesis

Show one paper cité twice, frame for frame, and let only what is heard decide whether a lit window is **someone coming home** or **someone being logged**. The picture is a countable instrument: 22 windows light in a fixed permutation, one every 0.9 s. Sound decides what each light means.
- **Edition A** lands each light on a domestic sound that is late by a varying amount: a latch, a kettle, a "bonsoir". The score becomes a neighbourhood.
- **Edition B** lands each light, exactly on the frame, on a relay click or typewriter key over a held hum. The same score becomes a ledger.

**Defining beat (20.5 s, frame 492):** window 16 (top floor, bay 16, above the entrance) lights. A paper silhouette rises behind its tissue curtain at 20.9–21.6 s and turns its head toward the road at 22.4–23.0 s.
- **A:** a latch, then a kettle beginning to sing, and « C'est toi ? Le thé est prêt. » The silhouette is someone waiting for the walker who went in at 15 s.
- **B:** a relay click on frame 492, a typewriter carriage, and « 18 h 04 · fenêtre 16 : quelqu'un regarde la rue. » The silhouette is the watcher.

When the beat succeeds, a viewer can point to **window 16 and the head turn**, and name the heard event that made it a welcome (latch/kettle/greeting) or a watch (click/carriage/report).

**Comparison baseline:** the **silent control**, the same master with declared digital silence. The proof needs the silent control to be ambiguous: an empty cité at dusk, neither warm nor menacing. A second, historical baseline is the previous version of this film (`films/la-cite-raymond-queneau.py`, a drawn station with an envelope and a key). Its two mixes were frame-identical, but nothing in the picture let the viewer point to *where* the meaning switched. This build must beat it on locatability.

---

## 2 · Lineage Genome (compact)

| field | value |
|---|---|
| source | *La Cité Raymond Queneau*, Olivier Azam & Laurent Firode, 1998, a documentary on video. It is described (film-documentaire.fr) as one identical visual edit presented twice with different commentary and music. The content and tone of its two commentaries are **unknown to us** (not verified). We do not claim to copy them. |
| source medium | SD video documentary: a real housing estate filmed at eye level, with voice-over and music. |
| target medium | 30.000 s handmade cut-paper multiplane animation (960×464, 24 fps, 720 frames). There are two playable editions with sidecar captions (no TTS), a silent control and a voice crossover diagnostic. A 72 s screening reel puts the captions in a band outside the picture. |
| preserved relation | One frozen picture edit, two soundtracks, two coherent readings. Only the audio and the caption track differ. |
| optics change | Photographed estate → paper model under flat overcast light that drifts to dusk. The multiplane camera tracks laterally (0–16 s and 26–30 s) and holds still for the key shot. |
| formalism change | The picture carries an explicit permutation score (window i lights at step (37·i mod 96)). Frame hashes and decoded framemd5 lock the picture. Cue maps tie each heard event to a frame number. |
| concept change | Community vs surveillance, made *locatable*: the switch happens at a named window and frame. The original's own pair of readings is not claimed. |
| sound change | Spoken commentary → timed captions, plus short openly licensed real speech (Lingua Libre word recordings) if found. Foraged room/domestic/mechanical recordings are used, with synthesis only where nothing suitable is licensed. Both editions are held to one loudness target. |

**Formation epochs (weight 0–100, reason):**
- **95 · Chris Marker, *Lettre de Sibérie* (1957).** It repeats the same Yakutsk sequence under three commentaries. This is the canonical precedent for the operation. (It is documented; Azam/Firode's awareness of it is *uncertain*.)
- **85 · Queneau, *Exercices de style* (1947) / Oulipo.** One fixed incident, many retellings under a rule. The estate's namesake supplies the constraint logic.
- **70 · Kuleshov effect (1920s).** Meaning comes from juxtaposition, not the image. Here the juxtaposition is sonic. (The original experiment's exact form is historically *uncertain*.)
- **60 · French *grands ensembles* and 1990s banlieue documentary.** This is the subject and the reference image's world: cream blocks, zinc roofs, verge, avenue.
- **55 · Norstein multiplane (1970s).** Depth, haze and dusk exposure carry feeling (the technique SCION, below).
- **45 · Whitney computational motion (1960s).** The window lights are a numerical score you can see.
- **50 · CCTV and administrative surveillance culture (1990s–).** This is edition B's register: logs, timestamps, relay clicks.
- **40 · Media forensics / reproducible builds (2010s–).** Frame hashes as proof that "the picture did not change".

---

## 3 · Theory: Olog of the system

**Types**
- `◻PictureMaster`: one video-only H.264 file `out/master.mp4`, 960×464, yuv420p, 24 fps CFR, exactly 720 frames, encoded once. It carries `master.sha1.json` (sha1 of each rgb24 frame before encoding) and `master.framemd5` (decoded). Its revision id is the sha1 of the concatenated frame hashes.
- `◻PictureEvent`: `{id, kind ∈ {window_on, window_off, walker_step, door_open, door_close, silhouette_rise, head_turn, lamp_on, cut}, frame, window?}` from `picture/edl.json`. The events are fixed now (§6), before any artifact exists.
- `◻SoundVersion(A|B|C|X)`: stems `voice` (captions VTT plus any real-speech audio), `music`, `fx`, `amb`. Each stem is a 44.1 kHz stereo wav of exactly 1,323,000 samples (30.000 s) on the master clock. The version also carries an integrated loudness and a true peak.
- `◻CueClaim`: `{sound_event, t_sound, picture_event_id, frame, offset_ms = t_sound − frame/24, reading ∈ {domestic, surveillance}, claim: "this sound makes this moment read as …"}`.
- `◻Edition`: `attach(PictureMaster, SoundVersion)` → mp4 made with `-c:v copy`, plus a soft mov_text subtitle track and a sidecar `.vtt`.

**Arrows**
- `PictureEvent --occurs_in--> PictureMaster`
- `CueClaim --anchors--> PictureEvent`
- `CueClaim --belongs_to--> SoundVersion`
- `SoundVersion --attached_by(attach)--> Edition`
- `Edition --decodes_to--> framemd5`, which must equal `PictureMaster.framemd5`
- `Edition --heard_as--> Reading` (judged by the viewer)

**Central operation: `attach(M, S) → E`**
- *Typed preconditions*
  - `S.samples == 1,323,000` (±0) and the stems are summed on the same clock.
  - Every `CueClaim.picture_event_id` exists in `edl.json` for the **same** `M.revision`.
  - `|S.integrated − (−23.0 LUFS)| ≤ 0.5 LU`, and `S.true_peak ≤ −1.0 dBTP`.
  - S contains no picture data. Captions travel as a subtitle track or sidecar and are never burned into M.
  - M is not re-encoded: the video stream is copied.
- *Observable consequences*
  - `framemd5(E) == framemd5(M)` for all 720 frames, at the same frame count, dimensions and timebase.
  - The ebur128 report shows A and B within 0.5 LU of each other.
  - Played back, E's audible events fall at their CueClaim frames: B within ±1 frame, A at its declared irregular offsets.
  - A viewer of E names a reading and points to a CueClaim (ideally the window-16 cue) as its cause.
- *Counterexamples (must fail the fixture)*
  1. B rendered by redrawing the master with a caption or a red "REC" dot burned into frames 384–623. framemd5 then differs on 240 frames: **FAIL**.
  2. B muxed with the video delayed one frame (`-itsoffset 0.0417`) or with frame 0 dropped. The count or order shifts and the md5 sequence no longer aligns: **FAIL**.
  3. B made 6 LU louder than A, so that "menace" is only loudness. The loudness check fails: **FAIL**.
  4. The silent control already reads as surveillance to the viewer, so the picture is biased. The proof fails semantically: repair the picture (§8) and open a new master revision.
- *Where views are equivalent and where they diverge*
  - Replaying A twice, A vs B, A vs the silent control, and A vs X are all **picture-equivalent**: framemd5 is equal, and so are order and cadence.
  - They **diverge** only in the audio and caption tracks, and only at the CueClaims. The cue maps are compared side by side (`out/cuemap-compare.json`) before any edition is rendered. These are the "100×" checks: run the comparison for every candidate revision, not once.
  - The screening reel is a *presentation* derivative, not the fixture. Its passes are verified as sha1-identical before encoding (720/720 picture-region frames), and after decoding as PSNR ≥ 45 dB on the picture region. This is declared as "lossy representation, structurally verified".

TTL = 2 (the default). It decrements on child inquiry, not on the work budget.

---

## 4 · Invariants

1. **Picture lock.** 720 frames, 960×464, 24 fps CFR, fixed order. One `master.mp4` is encoded once (libx264, crf 16, preset slow, yuv420p, `-tune animation`). All editions use `-c:v copy`. A picture change creates a new master revision and reopens alignment for **both** sound teams.
2. **Same essence.** Editions A, B, C (optional), X and the silent control all decode to identical framemd5.
3. **Silent control preserved.** `out/control-silent.mp4` is the master plus a silent AAC track (digital zero).
4. **One loudness target.** −23.0 LUFS integrated ±0.5 LU, true peak ≤ −1 dBTP, measured with `ffmpeg -af ebur128=peak=true` on the final editions. Gains are recorded in `out/mix.json`, so the mixer's choices stay reviewable.
5. **Shared clock.** The audio stems are exactly 1,323,000 samples. The CueClaims name frames from `edl.json`.
6. **No type in the picture master.** Captions live in the VTT/mov_text track or in the reel's caption band below row 463.
7. **Provenance.** Every foraged byte has a ledger row (allowed licence read from Commons extmetadata, LoC rights, or the archive page). Downloads are decoded with ffmpeg/PIL only.
8. **Determinism.** `maquette.py frame(k)` is a pure function of k. Re-running it gives identical sha1s (checked on 10 random frames).
9. **Branches.** Non-commuting alternatives (for example the edition C variants, or a picture repair) are kept as named branches under `out/branches/<name>/`, each with its base revision recorded.

---

## 5 · Animation technique SCIONs

1. **#5 Yuri Norstein, Atmospheric Multiplane Cinema.** Its primitives are glass-plane layers, z distances, diffusion/fog fields, an exposure/focus schedule, cutout silhouettes and depth audio. It is used here as follows.
   - Eight paper planes at declared z: P0 sky sheet (z ∞, ratio 0.00), P1 haze of far blocks (0.15), P2 far block volume with roof (0.35), P3 near block with curved roof end and the window grid (0.55), P4 saplings and hedge (0.75), P5 pavement, road and dashes (0.90), P6 grass verge (1.00), P7 foreground fence post and lamp post (1.25).
   - A haze field between P1–P3 that is *not* uniform: it is denser low, near the hedge line, and thins with height.
   - An exposure schedule from overcast day to dusk (§6).
   - A cutout silhouette at window 16.
   - Depth audio, done by the sound teams: far traffic panned and low-passed, near events dry.
   - Its acceptance test applies: near layers move more than far ones, occlusion stays coherent across the pan, and the fog is not an overlay.
2. **#6 John Whitney, Harmonic Motion Orchestra.** Its primitives are an oscillator bank, phase relationships and an event envelope. It is used here as follows.
   - The window score is a measured numerical structure: window i lights at step s(i) = 37·i mod 96, every 0.9 s from 6.1 s. Each glow uses a 3-frame attack envelope.
   - Each lit window "breathes" through a slow oscillator (0.5 % luminance, its own phase φ_i = 2π·i/96 and period 3.1 s), so the field becomes denser and more complex rather than mechanically still.
   - Sapling sway uses two incommensurate oscillators (0.37 Hz and 0.23 Hz, amplitude 1.5° at the base, rising with height).
   - The progression runs from sparse to dense: 0 lit, then 11 at the key cut, then 22 by 25 s. It releases when window 16 goes dark at 29.0 s.
   - Its invariant applies: the phase and step relations are measurable from the frames.
3. **#47 Sound-to-Action, Viseme and Gesture Swarm.** Its primitives are audio events, expressive holds, gesture accents and sonic perspective. It is used here as follows.
   - Each sound team writes a cue map of CueClaims anchored to picture-event frames.
   - The silhouette's gesture (rise, a 0.8 s hold, head turn, hold) is the "body action". Each edition hears it differently, and silence is allowed to animate it: in A, the 1.5 s crossover at the key cut; in B, the hold after the head turn.
   - Its acceptance test applies: the impact cue and the reaction are properly spaced, and nothing flaps mechanically in silence.

Supporting methods (not separate SCIONs) are #32 forward kinematics for the articulated walker and the silhouette's neck, #45 occlusion compositing (the lamp post and fence in front, the door flap over the walker) and #41 secondary dynamics (the bag swing and the curtain settle).

---

## 6 · Hard proof: timed sequence (picture master, 30.000 s = 720 frames)

The window numbering is i = floor·24 + bay, over the near block's 4 floors × 24 bays (floor 0 is the top floor under the zinc roof; bay 0 is the leftmost). The near block also has a ground floor (rez-de-chaussée) with the entrance door under bay 16. Window i lights at t = 6.1 + 0.9·s(i) for s(i) = 37·i mod 96 ≤ 21. Its glow rises over 3 frames from the frame below. **These frames are locked now; the sound teams work from this table in parallel with the picture.**

| step | window (floor, bay) | frame | t (s) |
|---|---|---|---|
| 0 | 0 (0,0) | 146 | 6.1 |
| 1 | 13 (0,13) | 168 | 7.0 |
| 2 | 26 (1,2) | 190 | 7.9 |
| 3 | 39 (1,15) | 211 | 8.8 |
| 4 | 52 (2,4) | 233 | 9.7 |
| 5 | 65 (2,17) | 254 | 10.6 |
| 6 | 78 (3,6) | 276 | 11.5 |
| 7 | 91 (3,19) | 298 | 12.4 |
| 8 | 8 (0,8) | 319 | 13.3 |
| 9 | 21 (0,21) | 341 | 14.2 |
| 10 | 34 (1,10) | 362 | 15.1 |
| 11 | 47 (1,23) | **384 = key cut** | 16.0 |
| 12 | 60 (2,12) | 406 | 16.9 |
| 13 | 73 (3,1) | 427 | 17.8 |
| 14 | 86 (3,14) | 449 | 18.7 |
| 15 | 3 (0,3) | 470 | 19.6 |
| **16** | **16 (0,16)** | **492** | **20.5** |
| 17 | 29 (1,5) | 514 | 21.4 |
| 18 | 42 (1,18) | 535 | 22.3 |
| 19 | 55 (2,7) | 557 | 23.2 |
| 20 | 68 (2,20) | 578 | 24.1 |
| 21 | 81 (3,9) | 600 | 25.0 |

### Shots

All picture elements are **HANDMADE** unless marked otherwise. The model is built from cut "sheets": each one is a foraged real paper scan (below), cut by a hand-jittered polygon path, given a soft drop shadow (offset ≤ 3 px, blur ≥ 6 px, as overcast light implies) and a 1 px lighter cut edge.

**S1 · Établissement: 0.000–8.000 s (f 0–191).**
- *On screen:* a wide view at eye level across the grass verge (P6, lower left wedge) and a road running from lower-left to mid-right (P5). Two cream blocks recede toward the left (P2 far, P3 near). The curved zinc roof ends on the right, with pale dormers. Bare saplings and a hedge line sit along the pavement (P4), and a fence post stands at the right foreground (P7). The sky (P0) is flat white overcast.
- *Camera and light:* the camera tracks laterally (a 64 px move at P6 over 8 s, ease-in; the other planes follow their ratios). Exposure is 1.00.
- *Score:* the first lights come on at f146 (window 0) and f168 (window 13).
- *Heard:* A and B each establish their world (§6b).

**S2 · Approche: 8.000–16.000 s (f 192–383).**
- *Camera:* the track continues at half speed, with a multiplane push-in. Each plane scales by 1 + 0.18·ratio between 8 and 16 s, so near planes grow more.
- *Walker (frame-by-frame animation):* a **paper walker** (articulated cutout: head, torso, upper and lower arm, thigh, shin and foot on each side, and a shopping bag, all joined at pivots like brass fasteners) enters from the left on the pavement at f200. It walks with an FK gait (stride period 1.10 s, both feet in contact for 6 frames per step, torso bob 2 px, bag swing as secondary motion with a 4-frame lag) toward the entrance under bay 16.
  - *Optional FORAGED timing reference:* the step period can be measured (not traced onto screen) from an archive pedestrian in movingimagearchive.com clip `ee12b007` "Arteries of New York City" (1941, housing-project courtyard). Credit it as "gait timing reference, not shown".
- *Door:* the door flap opens f334–346, the walker passes in f346–362 (occluded by the door jamb, #45) and the door closes f365–374.
- *Score:* windows light at steps 2–10.
- *Light:* exposure drifts from 1.00 to 0.93, and the sky sheet takes a slightly cooler cast.

**KEY CUT: 16.000 s (f 384).** Window 47 lights on the cut frame itself. The voice-only/music-only crossover sits here (§6b).

**S3 · La partition (key shot): 16.000–26.000 s (f 384–623).**
- *Framing:* the camera is locked, on a closer framing of the near block. All 24 bays and 4 floors fill the width, with the roof and dormers above and a strip of hedge and pavement below. The model is the same, so the same windows stay lit, at the new scale.
- *Score:* windows light at steps 11–21, one every 0.9 s. The lit windows breathe (Whitney oscillator) and the saplings sway.
- *Light:* exposure drifts from 0.93 to 0.78 and the sky sheet cools toward (205,205,215). The lit amber windows become relatively stronger: the dusk is real light on paper, not a colour filter.
- **Defining beat:**
  - f492: window 16 lights.
  - f502–518: a black-card **silhouette** (head, neck, shoulders, articulated at the neck) rises from below the sill behind the tissue. The tissue softens the edge (back-lit shadow puppet, #2 Reiniger method).
  - f518–538: hold.
  - f538–552: the head turns 25° toward the road (FK neck, 2° overshoot settling over 6 frames).
  - f552–566: the curtain edge slides 8 px and settles.
  - The silhouette holds to the end of S3.

**S4 · Sortie: 26.000–30.000 s (f 624–719).**
- *Camera:* it returns to the wide framing of S1 through a hard cut at f624, then tracks right (the opposite direction to S1). The paper **lamp post** (P7, swan neck) crosses the foreground at ratio 1.25, occluding the blocks.
- *Light:* the lamp's head lights at f660, with a warm pool on the pavement (P5) computed from its pose. Exposure drifts from 0.78 to 0.70.
- *Window 16:* goes dark at f696. The silhouette is gone.
- *End:* the last frame is f719. There is no fade to black, so A and B end on the same frame.

**Picture materials**
- **FORAGED:** 3–6 scans of real paper and card from Commons (search "paper texture", "blank page", "cardboard texture", "tissue paper", "Japanese paper"; CC0/PD/CC BY/CC BY-SA only, read from extmetadata; ≤ 15 MB total). They provide the facade sheet, the roof card, the tissue windows and the road card, so the fibre is real rather than procedural noise. They are tinted only to the sampled palette (§7) by per-channel levels, which is grading to unify real material.
- **HANDMADE:** every cut shape, the articulated walker, the silhouette, the door flap and the lamp post.

### 6b · Heard (both editions, the same picture)

The voice is captions: a French line plus a small English gloss, timed in VTT, shown in the reel's caption band. Short **FORAGED real speech** is allowed: Lingua Libre French word recordings on Commons (CC BY-SA). Examples are "bonsoir" and "c'est toi" for A, and numbers ("seize", "dix-huit") through a radio band-pass for B. Each stem is 30.000 s.

| time | Edition A: a welcoming community | Edition B: uneasy surveillance |
|---|---|---|
| 0–8 | Amb: outdoor estate, light wind, distant children, a far bus (foraged). Caption 1.0–5.5: « Rue Raymond-Queneau, fin d'après-midi. » / *Raymond Queneau Street, late afternoon.* Each light (f146, f168) answers with an irregular domestic sound (+120…+400 ms): a far window latch, a dish. | Amb: the same wind under a 50 Hz electrical hum and a low held drone. Caption 1.0–5.5: « Secteur 4, bâtiment C. 17 h 52. » / *Sector 4, block C. 5:52 pm.* Each light answers with a relay click **on its frame** (±1 frame). |
| 8–16 | The walker's footsteps (foraged or synthesized, in sync with the gait contacts), the bag rustling, a "bonsoir" (Lingua Libre) at about 12 s, the door latch and creak at f334, the door shutting at f370. Caption 8.5–13.5: « Madame Ferrand rentre des courses. » / *Madame Ferrand is back from the shops.* | The same footsteps, drier and closer. A typewriter key on each step contact, starting as a few. The door sound replaced by an electric strike buzz at f334. Caption 8.5–13.5: « 18 h 01 · entrée porte C, une personne, un sac. » / *6:01 pm · door C, one person, one bag.* |
| **16.0–17.5 (crossover)** | **Music only:** a short music-box or accordion phrase (FORAGED public-domain recording if found, otherwise synthesized). All other stems silent. No caption. | **Voice only:** caption « Fenêtre suivante. » / *Next window.* Radio-filtered "quarante-sept" (Lingua Libre) on f384. Silence otherwise, with no hum and no drone. |
| 17.5–20.3 | Room tone; lights answered by a radio coming on, a tap and laughter (irregular). Caption: « Six heures : on rentre, une fenêtre après l'autre. » / *Six o'clock: people come home, one window after another.* | The hum returns and every light gets a click. Caption: « Six heures : chaque fenêtre allumée est notée. » / *Six o'clock: every lit window is logged.* |
| **20.5–25.5 (beat)** | f492: a latch (+150 ms), then a kettle beginning to sing (rising over the silhouette's rise). At the head turn (f538): a soft "c'est toi ?" or a warm hum of a tune. Caption 20.6–25.5: « — C'est toi ? Le thé est prêt. » / *Is that you? The tea is ready.* | f492: a relay click exactly on frame, a typewriter carriage return at f518, and silence at the head turn (f538–566, an expressive hold) broken by a single camera shutter at f566. Caption 20.6–25.5: « 18 h 04 · fenêtre 16 : quelqu'un regarde la rue. » / *6:04 pm · window 16: someone is watching the street.* |
| 26–30 | A distant radio song (a PD recording if found), a bus passing left to right with the track, and a "bonne nuit" as window 16 goes dark at f696. Caption 26.5–29.8: « Ici, tout le monde se connaît. » / *Here, everyone knows everyone.* | The drone thins, a teleprinter or relay chatter, and a final click at f696. Caption 26.5–29.8: « Ici, tout le monde est connu. » / *Here, everyone is known.* |

A's offsets are irregular: across at least 8 window cues, the standard deviation of offsets is ≥ 80 ms and no two consecutive cues use the same sound. B's offsets are within ±42 ms (1 frame) of their frames, and B repeats one click sample, which is part of its meaning.

**FORAGED sound, looked for first.**
- The movingimagearchive.com cache (`forage.py`, clips with sound). Leads to listen to: `ee12b007`/`7b8a9d52` (housing-project courtyard ambience), `b6100d97` "Singing Wires" 1951 (typewriter at night), `b352abf2`/`575666be` "The Town and the Telephone" 1950 and `92d84a1d` "Telephone and Telegraph" 1946 (switchboard relays), `d2156bef`/`b3ef2f32` (kitchen), `1f03935f` (a radio in a living room). Only stretches without narration or music are usable as stems. The units check this by listening and with spectral checks.
- Commons audio (CC0/PD/BY/BY-SA): door latch, kettle, footsteps, typewriter, relay, shutter, mains hum, city ambience, music box, and public-domain 78-rpm French songs or accordion.
- Lingua Libre speech.

**HANDMADE (synthesized with kit.Mix) only** where nothing licensed fits, declared in the ledger.

### 6c · Crossover diagnostic and third soundtrack
- **X (voice crossover):** A's music, fx and amb stems for 0–30 s, with B's **voice** stem (captions and radio speech) substituted from 16.0 s. It tests whether the words alone flip the reading.
- **C (selective silence and room tone, §8, optional if time allows):** only the amb stems, plus silence for 16.0–26.0 except a single room-tone swell at f492. All variants attach to the same master.

---

## 7 · AESTHETIC TARGET (from `assets/references/citefilm.webp`, 748×406)

I sampled the reference with PIL, using 7×7 medians unless noted. Tones are cool and low in saturation, read off SD video in overcast light.

**Medium.** The reference is a frame of 1990s SD documentary video: soft, with slight chroma smear and no visible grain, under overcast daylight. Our medium is a *real cut-paper model* in multiplane. We reach the look through real paper fibre (foraged scans), very soft overcast shadows and an eye-level documentary camera. We do **not** use a video-noise or VHS filter.

**Tonal range.** The reference's luma has p2 = 46, p50 = 131 and p98 = 242. Contrast is low, the sky is blown to near-white and the darkest values are the hedge and the balcony shadows. Mean saturation (max−min) is 19.6. The kf-2 keyframe was too high-key in the mid-tones (p50 = 197) and its sky too dark (210).

**Palette (sampled).**
- Sky: (245,235,241) at the top to (234,225,239) low, a faint lavender-white rather than grey.
- Facade cream: median of the lit cream pixels is (175,178,163) — a cool, slightly green cream, *not* yellow — with highlights near (205,205,190). The left white block is (132,141,141) in shade.
- Zinc roof: blue-green slate, median (77,91,93), with a sheen of (119,133,147). It is not black; kf-2's (59,63,69) is too dark.
- Dormers: (190,207,212). Window glass and recesses: (74,85,86).
- Balcony and loggia bands: dark olive (73,73,55).
- Bare trees: (114,124,105). Hedge: (48,63,41).
- Road: blue-grey (97,115,113), with faint dashes (99,110,111).
- Grass verge: (78,102,56). Fence: (60,69,61).
- Lit windows, our addition for dusk: amber (240,190,110). These are the only warm saturated note.

**Light.** Flat, shadowless overcast from above. There is no cast shadow direction, only ambient occlusion under balconies and roof eaves. The model's drop shadows must therefore be small (≤ 3 px offset) and very soft. Dusk arrives by lowering the exposure on the paper and raising the lamps, not by tinting.

**Texture.** Smooth, no noise, with surfaces read through edges and small features (balconies, dormers, window grids). The fibre of the paper scans shows only at near planes. The far planes are softened by the haze field.

**Framing and scale.** Eye level, about 1.5 m, from across the road. The blocks fill the upper 60 % and recede on a diagonal to the **left** toward a vanishing point beyond the frame. The road crosses as a band rising gently from left to right, the verge is a wedge at the lower left and there is a fence post at the right edge. The horizon line sits about 0.60 H down. The curved roofs are quarter-cylinders with 6–8 dormers per volume. The *key shot* (S3) is closer but keeps the eye level.

**Typography.** None in the picture, as in the reference. Captions appear only in the reel's band (Instrument Serif 22–24 px in near-black (36,32,29) on paper (243,239,228), English gloss in sans 14 px muted) and in the VTT.

**Pacing.** Documentary slowness: long holds, slow lateral tracks and no fast cuts. There are 4 shots in 30 s. Rhythm comes from the window score (0.9 s), not from editing.

**Planned departure:** the light drifts toward dusk from 16 s, as the chosen direction requires. **S1 (0–8 s) must match the reference's daylight.**

---

## 8 · Units (run in parallel against plan-r3)

The picture and sound teams fork from the same locked event table (§6). Coupled tasks are merged: model maker with picture editor, and each sound team with its own caption writer and stem pre-mix. The mixer, the validator and the reel assembly belong to the editor. The fresh viewer is the workflow's independent reviewer.

1. **picture: model maker and picture editor** (both). Outputs `picture/edl.json`, `picture/maquette.py`, `out/master.mp4`, `out/master.sha1.json` and `out/master.framemd5`. Media goes in `sources/la-cite-raymond-queneau/picture/`.
2. **sound-A: domestic team** (both). Outputs `sound-A/cues-A.json`, plus the stems, `A.vtt` and a ledger. Media goes in `sources/.../sound-A/`.
3. **sound-B: surveillance team** (both). Outputs `sound-B/cues-B.json`, plus the stems, `B.vtt` and a ledger. Media goes in `sources/.../sound-B/`.

The details are in the structured units returned to the workflow.

---

## 9 · Acceptance bar (falsifiable; the critic watches the reel and reads `out/identity-report.json`, `out/mix.json`, `cues-*.json`, credits)

1. **Picture identity (measured).** `out/edition-A.mp4`, `edition-B.mp4`, `edition-X.mp4` and `control-silent.mp4` each decode (`ffmpeg -f framemd5`) to the same 720 hashes as `master.mp4`, at 960×464 and 24 fps. The reel's two passes have 720/720 equal sha1 before encoding. A single altered or shifted frame fails.
2. **Loudness (measured).** Integrated loudness of A and B is −23.0 ±0.5 LUFS and their difference is ≤ 0.5 LU. True peak is ≤ −1 dBTP. The silent control is digital zero. The values are in `mix.json` along with every gain.
3. **Locatable defining beat (measured + perceptually judged).** Window 16 lights at f492, the silhouette rises at f502–518 and the head turns at f538–552, visible in both passes. In `cues-B.json` every window cue lies within ±42 ms of its frame. In `cues-A.json` the window-cue offsets have a standard deviation ≥ 80 ms. Watching, a critic can name the heard event at window 16 that makes A a welcome and B a watch.
4. **Crossover at the key cut (measured).** For 16.0–17.5 s, A's voice, fx and amb stems are silent (≤ −60 dBFS) and only music plays. B's music, fx and amb stems are silent and only voice (caption plus radio speech) plays. Edition X exists and the reviewer records which reading it produces.
5. **Genuine frame-by-frame animation (perceptually judged + structurally verified).**
   - The paper walker's knee and hip angles change every frame across at least 5 strides (8.3–15.0 s), with foot-contact holds and a lagging bag.
   - The silhouette's neck turn shows an overshoot and settle.
   - During S1, the frame-to-frame displacement of P6 is ≥ 4× that of P1 (multiplane, measured from `edl.json` plane offsets).
   - The haze is denser low than high.
6. **Aesthetic, numeric side-by-side with the reference.** On frame t = 4.0 s next to `citefilm.webp`:
   - The sky's median channels are within 12 of (240,230,240).
   - The facade cream's median has R−B ≤ 20 and lies within 25 of (175,178,163).
   - The zinc roof's median has B ≥ R and luma between 75 and 130, so it is slate and not black.
   - Picture luma p50 is between 115 and 170, and mean saturation (max−min) is ≤ 30.
7. **Aesthetic, perceptual side-by-side.** The critic places frames at 4.0 s and 21.0 s next to the reference at the same height and confirms each of these:
   - The same kind of place: cream blocks receding to the left, curved slate roofs with dormers, a verge and a road on a diagonal, eye level, flat overcast light with no hard shadows.
   - The material reads as real cut paper (fibre, cut edges), not vector flats or a filter.
   - The picture has no type.
8. **Readings and provenance (perceptually judged + structural).** A fresh viewer sees the silent control first, then A and B in counterbalanced order, without labels. They call A welcoming and B watched (or uneasy), and point to a named cue (preferably window 16) as the cause. They do not read the silent control as clearly either; if they do, it counts as a picture bias failure. Every foraged item is in `films/credits/la-cite-raymond-queneau.json` with a licence in {PD, CC0, CC BY, CC BY-SA} and a source URL.

## 10 · Repair rules (§8 of the prompt)
- If A and B read the same, swap only the voice stem over a common bed (edition X is that test).
- If the difference depends on volume, level-match (already enforced) and test harmony or perspective separately (dry vs far).
- If the silent control is biased, repair the picture: change the silhouette's gesture timing, not its look. This opens a new master revision and both teams re-align.
- After two failed repairs, state two explanations and run the smallest deciding comparison. Record each against its revision and keep the strongest accepted checkpoint.
