# SCION plan · Récits d'Ellis Island · "Traces and testimony"

Director's plan, rebuilt from scratch at revision `plan-r1` (2026-11-15).
Inputs read: prompts/recits-dellis-island.md (all sections), films/BRIEF-2.md, films/kit.py,
catalogue/cinema.json (id 4), assets/references/ellis.webp, the earlier script/notes/credits.

The earlier version drew a station and two cartoon faces with kit primitives. That is a
style costume and is withdrawn. Its four Commons photographs and the Méliès film are kept
as candidates only. Their licences were re-read from Commons extmetadata on 2026-11-15
(see below), and U1 must verify them again.

The reference still (ellis.webp) is a present-day colour photograph: the Statue of Liberty
and the Manhattan skyline across grey water, taken from the site Bober and Perec visit. So
the source's "site" layer is photography of a real, present place. This film forages real
photographs of a real disused halt. It does not imitate the look of the still.

---

## 1 · Creative thesis

A place can show only what is still there: a platform, a closed door, a date in a file's
metadata. Once someone speaks, an event becomes knowable that the place cannot show. When
two people remember that event differently, the place cannot settle who is right.

The film makes the viewer feel this in two 25-second movements:
- **Movement I** shows only traces: a real disused halt photographed on a known day, with
  no voices.
- **Movement II** carries two attributed, clearly fictional accounts of the last train
  over the same images. The accounts disagree on one detail that you can hear: whether the
  bell rang before or after the brass key was put down.

The film ends with the disagreement still open.

## 2 · Defining beat and comparison baseline

**Defining beat (Movement II, about 33–48 s of the film).** The same platform photograph
(trace T1) appears twice, with the same crop and the same source card:
- First under witness A: the bell, then the key.
- Then under witness B: the key, then the bell.

The same foraged bell recording (S1) and key sound (S2) are placed in opposite orders under
the two captions. The image does not change and its source card keeps saying the same
thing: "shows the platform on 23 Jan 2021; does not show 1979, the bell or the key". Only
the testimony and the sound order change.

When the beat works, a viewer can point to three things:
1. The identical frame and source card under both voices.
2. The bell heard at two different moments relative to the key.
3. The ledger card that names the detail as UNRESOLVED.

**Comparison baseline (the conventional cut the beat must beat).** A single-voice cut:
- Only account A, captioned with no speaker label or interval.
- Laid over T1, with the bell synced to the image and no source card.
- B dropped and no ledger.

In the baseline the photograph reads as proof of A's memory. The montage editor renders
this baseline as a separate private clip (`baseline.mp4`, not published) so the reviewer
can compare the two cuts. If a test viewer of the real cut still says "the photo shows the
bell rang first", the beat has failed and section 8's repair runs.

## 3 · Lineage Genome (compact)

| field | value |
|---|---|
| source | *Récits d'Ellis Island*, Robert Bober (director) and Georges Perec (text, voice), 1980; two-part television documentary (BnF record cb392144425; QAGOMA screening notes) |
| source media | Film for television. Part 1: present-day visit to the empty site, historical photographs, Perec's narration. Part 2: interviews with people who passed through. Exact broadcaster and part titles: **uncertain**, not verified here. |
| target media | 60-second digital film, 960×540, 24 fps, stereo. Captions carry the voices. Saved assembly at films/recits-dellis-island.py. Source and permission ledger, claim graph and timecoded captions alongside. |
| preserved relation | The site is shown first and silent; witnesses come after. Testimony adds what the place cannot show. The gap between the two parts is the subject. |
| optics change | No filmed travelling shots. Instead: still photographs from Commons (one photographer, one day, 23 Jan 2021), cropped and slowly reframed. One public-domain moving image from 1896 is used and labelled as *not this station*. |
| formalism change | Every image and sound carries an on-screen evidence ID. Every quotation carries speaker, interval and a "staged" label. The cut is projected from a claim graph (supports / disputes / leaves open). |
| concept change | The witnesses are fictional and labelled as fictional, not real emigrants. Their disagreement is the subject, not the authority of memory. The station is a stand-in, not Ellis Island. |
| sound change | No narrator voice (no TTS; Perec's voice is not used). Foraged field ambience, a real recorded bell and a real key sound. Silence under the voice captions is a deliberate choice. |

Formation epochs (weight 0–100, and why):
- **1892–1924 immigration photography at Ellis Island** (e.g. Augustus Sherman, Lewis
  Hine). Weight 40. The source's Part 1 rests on historical photographs as traces. Which
  photographers appear in the film is **uncertain**.
- **1960s cinéma direct and interview cinema.** Weight 55. Part 2's interview form. Direct
  lineage is a reasonable inference, not a documented claim (**uncertain**).
- **Perec's 1970s inventories of the infra-ordinary** (*Espèces d'espaces* 1974;
  *Tentative d'épuisement d'un lieu parisien* 1975). Weight 85. They give Movement I its
  rule: list only what the place shows.
- **The 1980 film itself.** Weight 100. Two parts, site then voices.
- **2020s open archives and provenance graphs** (Commons extmetadata; SCION §54). Weight
  70. Source IDs and transformations are carried through to the render.

Uncertain historical claims are kept as claims with the relation `leaves_open`:
- The Commons uploader's description says the halt was built in 1869 (architect Rougemont).
- It says the halt is now disused, on the Vierzon–Tours section of the PO line.
- It says the PO was nationalised in 1937 and that an express derailed near the station in
  1904.

None of these is used on screen as fact. At most it is shown as "according to the
uploader".

### 3.1 Olog (types and arrows)

```
Trace     --has--> AssetID         (immutable: commons title + sha256 of local bytes)
Trace     --has--> Coverage        (place: verified|stated|unknown; time: EXIF|stated|unknown)
Trace     --has--> Source          (archive, url, author)
Trace     --has--> Permission      (licence ∈ {PD, CC0, CC BY, CC BY-SA}, licence_url)
Trace     --shows--> Depiction     (what is visibly in frame — the only thing it can support unaided)
Testimony --has--> Speaker         (fictional name + "fictional witness")
Testimony --has--> Consent         (state ∈ {authored-fiction, granted, missing}; use scope)
Testimony --has--> Interval        (segment id + verbatim in/out timecode)
Testimony --has--> Language        (fr written original; en caption translation)
Testimony --has--> TranscriptStatus(verbatim | corrected@rev | translated)
Claim     --cites--> Evidence      (Trace | Testimony interval), with Relation ∈ {supports, disputes, leaves_open}
Match     --links--> (Trace, Testimony)   (separately verified identity/date match; none exist in this film)
Shot      --uses--> Trace? , Testimony? , Sound*
[assemble]: (Claims, Traces, Testimonies, Sounds, Order) --> Sequence = Movement I (Trace-only) ; Movement II (Testimony over Trace)
```

### 3.2 Central operation `[assemble]`: typed preconditions

1. Every Trace and Sound used has a permission in the allowed set, read from Commons
   extmetadata (or LoC rights "No known restrictions"). The licence is recorded with
   author and URL. Otherwise the asset is quarantined and never rendered.
2. Movement I uses no Testimony. Its captions are source cards only, never quotation marks.
3. Every Testimony interval used has `consent ≠ missing`. A missing consent state blocks
   the public export (`assets/films/…mp4`) and allows only the private assembly. The script
   `assert`s this.
4. Every shot that puts a Testimony over a Trace shows both on screen:
   - the speaker and interval, and
   - the trace ID and its depiction scope.
5. No Claim of the form "image proves memory" may be projected unless a `Match` record
   exists. In this film the `Match` set is empty, so no such claim appears.
6. Disputed evidence is kept. Every Claim with `disputes` keeps both cited intervals in the
   ledger and in the cut.
7. A transcript correction bumps the segment revision. Every caption derived from it must
   carry the new revision, or the render fails.

### 3.3 Observable consequences

- Movement I has no quoted speech: you hear only ambience and see only source cards.
- Every caption in Movement II begins with the speaker's letter and name. It carries
  "fictional witness · staged" and an interval label.
- T1 appears under A and under B with an identical crop and an identical source card. A
  frame diff of the two shots, minus the caption band, is about zero.
- S1 (bell) comes before S2 (key) under A and after S2 under B. This can be measured on the
  waveform.
- The 1896 Vincennes insert carries "another station, 1896, not the last train".
- The closing ledger lists the agreed facts, both orders and "UNRESOLVED".

### 3.4 Counterexample (what `[assemble]` must refuse)

Cut account A's line "the bell rang first, then she put the key on the bench" over T1 with:
- no speaker label,
- the bell synced to a slow push-in on the platform,
- B's account omitted.

This breaks preconditions 4 and 6. The viewer reads T1 as proof of A, and the dispute
disappears.

A second counterexample: a caption that puts B's words under A's name label, mixing two
speakers in one shot. This breaks the quotation invariant, and the reviewer must catch it.

### 3.5 Replay and alternate views: equivalent vs divergent

- **Equivalent.** Swap the order of the A and B blocks. The claim graph is unchanged:
  A disputes B and B disputes A, symmetric. The ledger card is the same.
- **Divergent.** The swap changes perception. The first account heard colours the
  photograph. This is the section 8 "second ordering". The editor keeps it as a named
  branch (`order-BA`) and records it; it is not merged silently.
- **Equivalent.** Replaying the whole film gives the same frames and audio. The script is
  deterministic and seeded.

This is not interactive work, so no invitation, actions or exit are needed.

TTL is 2 (the default). No child inquiry is opened at plan time.

## 4 · Invariants (hard; a breach quarantines the candidate)

- **I1.** A quotation keeps its speaker, interval timecode, context (which question or
  statement it came from) and permitted use, on screen and in testimony.json.
- **I2.** Staged or fictional testimony carries a visible label in every frame where it is
  read.
- **I3.** A photograph supports claims only about what it shows. Place and date beyond that
  need a separate verification record (EXIF date = "measured"; uploader description =
  "stated, unverified").
- **I4.** Disputed evidence stays in the ledger and in the cut.
- **I5.** Evidence records are immutable: an asset ID is title + sha256. Editors only
  propose associations. The reviewer verifies claim scope.
- **I6.** A transcript correction invalidates its dependent captions. A consent change
  invalidates the public export, while the private assembly stays.
- **I7.** Licences are only PD, CC0, CC BY or CC BY-SA, read from extmetadata. Nothing from
  the 1980 film itself is used: no stills, no Perec text, no voice.
- **I8.** The accounts never name the real halt (Bourré). The film states on screen that the
  witnesses and the last train are invented and that the photographs show a real disused
  halt standing in for the place in the accounts. No invented history is attached to a real
  place.

## 5 · Fixed evidence IDs (shared by all units so they can work in parallel)

Traces (U1 owns them; the IDs are fixed now):

| ID | candidate | licence (read 2026-11-15) | depiction it can support |
|---|---|---|---|
| T1 | `File:Bourré (Loir-et-Cher) (50866798791).jpg`, Daniel Jolivet | CC BY 2.0; EXIF 23 Jan 2021 13:58 | goods shed, empty loading platform, grass where track was, catenary on the line behind |
| T2 | `File:Bourré (Loir-et-Cher) (50866795131).jpg`, Daniel Jolivet | CC BY 2.0; 23 Jan 2021 13:59 | goods-shed front, closed wooden double door, platform edge |
| T3 | `File:Bourré (Loir-et-Cher) (50866891867).jpg`, Daniel Jolivet | CC BY 2.0; 23 Jan 2021 13:59 | station house with painted name "BOURRÉ" |
| T4 | `File:Bourré (Loir-et-Cher) (50866888732).jpg`, Daniel Jolivet | CC BY 2.0 (re-read) | shed side, station house behind |
| T5 | `File:Gare de Bourré.jpg` | CC0; EXIF 2025-09-05 15:04 | to check: content must be the same site |
| T6 | **to forage**: a public-domain dated historical trace of this line or halt (early-1900s postcard "Bourré – la gare" with a readable date, or a PO timetable or map page) on Commons or LoC | must be PD | if none is found: an absence record |
| T7 | `File:Arrivée d'un train gare de Vincennes … (1896).webm`, Méliès | Commons says "Public domain"; re-verify the tag | a train arriving at *another* station in 1896 |

Sounds (U2): S1 bell (one single real bell recording, used twice), S2 key or keys set down
on wood or stone, S3 outdoor field ambience (wind or birds, open countryside), S4 distant
train pass-by (optional), S5 interior room tone (optional; otherwise silence is declared).

Testimony (U3): segment A (witness "Marthe V."), segment B (witness "Paul R."). Both are
fictional and authored for this film, with consent state `authored-fiction` and use scope
"this film, public".

## 6 · Timed shot list: Hard proof (two 25-s movements), total 60.0 s

Picture is 960×540. "Tag" means a small source card: kit `ink.label`/mono text on a band,
with the evidence ID. All film-time values are absolute.

### Prologue 0.0–3.0 (3.0 s), handmade title card
- **On screen.** Typeset card: "Récits d'Ellis Island · traces and testimony". Second line:
  "The witnesses and the last train are invented. The photographs show a real disused halt,
  Bourré (Loir-et-Cher), standing in." (HANDMADE: a typeset card.)
- **Heard.** Silence until 2.2 s, then S3 fades in.

### Movement I · What the site shows: 3.0–28.0 (25.0 s)
No voices and no quotation marks. Each shot has a tag: ID · author · licence · what it
shows · date status.

| film time | dur | on screen | heard | element |
|---|---|---|---|---|
| 3.0–4.5 | 1.5 | Card "I · What the site shows · no voices" | S3 | HANDMADE card |
| 4.5–11.0 | 6.5 | T1 full frame, slow 6% lateral reframe across the empty loading platform. Tag: "T1 · goods platform, disused halt · photo D. Jolivet, 23 Jan 2021 (EXIF) · CC BY 2.0" | S3 field ambience, continuous | FORAGED: Commons photo |
| 11.0–16.0 | 5.0 | T2: closed goods-shed door, static, slight push-in. Tag: "T2 · a closed door · 23 Jan 2021 · shows the door shut that day, nothing more" | S3; at about 13.5 s, S4 distant train pass-by at low level, tagged "S4 · recorded elsewhere" | FORAGED: photo + sound |
| 16.0–22.5 | 6.5 | **Dated trace.** If T6 is found: the PD postcard or timetable page full frame, slow reveal of the printed date or postmark, tag with its date and verification status. If not: T3, with the painted nameboard isolated by crop, and an EXIF date card overlaid ("photographed 23 Jan 2021, 13:59 · built 1869 according to the uploader, unverified"), followed by T5 (CC0, 5 Sep 2025) for 2 s if it shows the same building ("same façade, four years later"). | S3 thins out | FORAGED (T6, or T3+T5) + HANDMADE date card |
| 22.5–28.0 | 5.5 | T1 again, the empty platform edge cropped tight (this is the crop reused in Movement II). Tag: "T1 · empty platform · no bench, no bell, no key visible". Fades to the card. | S3 only, then a 0.6 s fade to silence | FORAGED |

### Interstitial 28.0–30.0 (2.0 s), handmade card
- **On screen.** "II · The last train, twice · two fictional witnesses · staged testimony".
- **Heard.** Declared silence (the card says "voices are captions").

### Movement II · Two accounts of the last train: 30.0–55.0 (25.0 s)
Every caption: `A · MARTHE V. — fictional witness · staged · seg A 00:mm–00:mm`, with the
line in A's colour. The same pattern holds for B.

| film time | dur | on screen | heard | element |
|---|---|---|---|---|
| 30.0–32.5 | 2.5 | A's handmade statement sheet: a typeset testimony record (FR original, speaker, consent "authored fiction", interval). The line being read is highlighted. Caption EN: "The last train was the 18:40. A woman got off with an envelope." | S5 room tone or declared silence | HANDMADE: statement sheet |
| 32.5–38.5 | 6.0 | **Beat A.** T1 platform crop (identical to 22.5 s), with the unchanged T1 tag at the top. Caption A: "The bell rang first. Then she put the brass key on the bench." | S3 low; **S1 bell at 33.6 s**; **S2 key at 35.4 s** | FORAGED photo + sounds |
| 38.5–41.0 | 2.5 | T7 Méliès 1896 train arrival, about 2.5 s excerpt. Tag: "T7 · Vincennes, 1896 · another station, another century · illustrates, does not prove". Caption A (seg A 00:26–00:28): "An old train, the last one that stopped." | T7 is silent: declared, no fake projector sound | FORAGED: PD film |
| 41.0–43.5 | 2.5 | B's handmade statement sheet. Caption EN: "She was already waiting when the train came in. She had a letter." | S5 or silence | HANDMADE |
| 43.5–49.5 | 6.0 | **Beat B.** The *same* T1 crop and the *same* tag. Caption B: "She set the key down first. The bell only rang as the train pulled out." | S3 low; **S2 key at 44.6 s**; **S1 bell at 47.6 s** (same sample as at 33.6) | FORAGED |
| 49.5–55.0 | 5.5 | Handmade ledger card (claim graph). Left: A timeline, bell → key. Right: B timeline, key → bell. Centre row "agreed by both: envelope · key left on the bench · service door shut". Bottom: "UNRESOLVED · bell before or after the key? · T1 shows a platform on 23 Jan 2021 and supports neither order · no image-to-memory match on file". | S1 and S2 replayed in A's order panned left (49.9/50.6 s), then in B's order panned right (51.6/52.4 s); fade out | HANDMADE: claim-graph card + FORAGED sounds |

### Coda 55.0–60.0 (5.0 s), handmade credits and ledger card
- **On screen.** Every evidence ID with title, author, licence and archive, plus
  "testimony A/B: authored fiction, consent recorded, public use". It also notes the
  `order-BA` branch if one exists.
- **Heard.** Silence.

The duration is 60 s, within ≤ 75 s, and the file must stay ≤ ~6 MB. The two movements
are exactly 25.0 s each, which the script must `assert`.

Section 8 repairs to keep ready:
1. **If T1 reads as proof.** Prepend a source card to Beat A, or change what is next to it
   (put the T7 insert before Beat A), while the caption words stay fixed.
2. **Second ordering `order-BA`.** B's block plays before A's. Render it to a private file
   and record it as a branch.

## 7 · Units (excluding the montage editor/assembler and the independent reviewer)

Every unit works from revision `plan-r1` and the fixed IDs in section 5. Every unit:
- reads BRIEF-2.md and the licence rules;
- downloads only from commons / upload.wikimedia.org / www.loc.gov / tile.loc.gov, with
  User-Agent `oulipo-film-research/1.0`;
- decodes media only with ffmpeg or PIL (`python3 -I`), and never executes anything from
  downloads;
- does not commit, and touches no other film;
- keeps under 50 MB of downloads.

### U1 · location-archive (FORAGE)
The merged location unit and archive researcher. Both forage the same archives under the
same licence check, so they are coupled.

**Task.**
- Re-verify T1–T5 and T7 from extmetadata: licence, author, DateTimeOriginal, description.
- Check that T5 is the same site.
- Search Commons and LoC for T6: a PD dated trace of the Bourré halt or the Vierzon–Tours
  PO line. Try postcards "Bourré gare", "Montrichard gare", PO timetables, Loir-et-Cher
  railway maps before 1930.
- Record each search and each absence.
- Prepare 960×540 crops for every shot in section 6, including the exact T1 platform crop
  used three times (22.5 s, 32.5 s, 43.5 s), as PNG files.
- Prepare a 2.5 s, 960×540 excerpt of T7, decoded with ffmpeg.
- For each trace write: what it shows, what it does not show, the date status
  (measured / stated / unknown) and the place status.

**Output.**
- `films/swarm/recits-dellis-island/traces.json`: a list of trace records with id, title,
  author, license, license_url, source_url, file_url, local_path, sha256, coverage,
  depiction, not_shown, used_in_shots, and an `absences` list.
- Media in `films/sources/recits-dellis-island/location-archive/`.

### U2 · sound (FORAGE)
**Task.** Find, verify and prepare from Commons audio:
- S1: one bell recording, a single strike or a short ring, ideally a station, hand or
  platform bell.
- S2: keys set down on wood or stone.
- S3: rural outdoor wind or birds ambience, at least 25 s, or loopable.
- S4: distant train pass-by (optional).
- S5: interior room tone (optional).

Licences must be PD, CC0, CC BY or CC BY-SA from extmetadata. Decode to 44.1 kHz stereo
WAV, trim, and normalise the peak to -3 dBFS. For each file record duration, onset time and
RMS. If a sound cannot be found, record the absence and propose a declared silence; do not
synthesise silently.

**Output.**
- `films/swarm/recits-dellis-island/sounds.json`: id, title, author, license, license_url,
  source_url, file_url, local_path, sha256, duration, onset_s, use, and what was recorded
  where, if stated.
- WAVs in `films/sources/recits-dellis-island/sound/`.

### U3 · testimony (HANDMADE)
**Task.**
- Write the two fictional accounts in full: French original plus English caption
  translation, about 4 lines each. They follow the section 10 seed (visitor, sealed
  envelope, bell, brass key left on the bench, service door stays closed). They agree on
  envelope, key-on-bench and door-shut, and disagree only on bell order.
- Assign segment intervals (seg A 00:14–00:28, seg B 01:02–01:13), speaker, consent
  `authored-fiction` with use scope, language and transcript status.
- Never name the real halt.
- Build the claim graph:
  - C1 "A recalls bell before key", supported by segA interval;
  - C2 "B recalls key before bell", supported by segB;
  - C3 "bell order on the night", disputed by A vs B and left open by T1;
  - C4 "a door was shut on 23 Jan 2021", supported by T2;
  - C5 "built 1869", leaves_open, from the uploader description of T3;
  - C6 "the image proves A's memory", **blocked: no Match**.
- Write the timecoded captions on the film timeline of section 6.
- Typeset the two statement sheets as real testimony record forms with PIL and the kit
  fonts (assets/fonts). Each form has a header, fields, a FR text block, interval markers
  and a "FICTIONAL · STAGED" stamp. Make one PNG per highlighted line.

**Output.**
- `films/swarm/recits-dellis-island/testimony.json`: segments with lines, intervals and
  consent.
- `claims.json`: the claim graph.
- `captions.srt`: film-timeline captions, each carrying its speaker and seg label.
- Sheets in `films/sources/recits-dellis-island/testimony/`.

### Run separately by the workflow (not assigned here)
- **Montage editor/assembler.**
  - Writes films/recits-dellis-island.py with kit.py from traces.json, sounds.json,
    testimony.json and captions.srt.
  - Puts the precondition asserts of section 3.2 into the script.
  - Renders the film, `baseline.mp4` (private) and optionally `order-BA`.
  - Updates the credits JSON and notes.
- **Independent reviewer.** Checks attribution, claim scope and the perceivable
  distinctions against the acceptance bar.

## 8 · Acceptance bar (falsifiable; checked by watching the render and reading the ledgers)

1. **Lengths.** Movement I and Movement II each last 25.0 s (±0.1 s, measured from the
   script's segment table and the render). The film is ≤ 75 s and ≤ 6 MB.
2. **Movement I is traces only.** It shows no quotation and no speaker name; only source
   cards. At least one shot is a foraged photograph of an empty platform. At least one shot
   carries a dated trace whose date status ("EXIF measured" or a printed date) is on screen
   and matches traces.json.
3. **Every quotation is labelled.** Every caption in Movement II shows the speaker letter and
   name, the word "fictional" or "staged", and a seg interval. Each one matches testimony.json
   exactly: no caption puts one speaker's words under the other's label.
4. **The defining beat holds.**
   - The T1 crop under A and the T1 crop under B are the same image with the same tag
     (frame diff outside the caption band about 0).
   - The same bell asset S1 is heard before the key sound S2 under A, and after S2 under B
     (onsets visible on the waveform and matching section 6 within ±0.3 s).
5. **The disagreement is intelligible and unresolved.** The closing ledger card names the
   agreed facts and both orders, and marks the bell-before-or-after-key detail UNRESOLVED.
   claims.json has C3 with relation `disputes`/`leaves_open` and keeps both segments.
6. **Images do not overclaim.** No on-screen text or ledger claim says that T1, T7 or any
   photograph proves a witness's memory (claims.json C6 is blocked; there is no Match). T7
   is labelled as another station and another year. The real halt is never named inside an
   account.
7. **Licences are clean.** Every foraged image and sound appears in
   films/credits/recits-dellis-island.json with author, licence and URL, and the licences
   are PD, CC0, CC BY or CC BY-SA. Each one matches its Commons extmetadata on re-query.
   There are no drawn figures, filters or faux grain imitating a photograph, and nothing
   from the 1980 film.
8. **Consent gates the export.** testimony.json records a consent state for both segments.
   Setting either one to `missing` makes the script refuse the public export (an assert, or
   a write to a private path only). This is structurally verified by reading the script, or
   by a dry run.
