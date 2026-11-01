# 065-five — Five: Parallel Lives, Unequal Details (archive proof)

Files: `edl.json` → `065-five.mp4` (67.6 s, 4.1 MB) + ledger.
`edl-alt.json` → `065-five-alt.mp4` (longer individual passages, no crosscut, 68.4 s, 4.2 MB) + ledger.
`contact.jpg` takes one frame every 2 s. `mk.py` regenerates both EDLs. Both mp4s were re-encoded after rendering at x264 CRF 28 (the renderer uses CRF 23) to stay under ~6 MB. Timing and audio are unchanged.
Revision: first assembly, 2026-10-31. Builder: `pairs` (scratch agent). **Independent critic review: PENDING. No critic session took place.**

How I checked: still frames only. I used a contact sheet of all 405 clips, 1 fps strips of about 15 practice candidates, 2–6 fps tiles around every in/out, scene-change detection and volumedetect. I did **not** watch at speed or listen. **No transcripts, no subtitles, and no participant self-descriptions exist for any of these people.**

## 1 · Theorem as adapted

Five people from five unrelated films (a 1970 TV kitchen, an undated victory-garden film, a 1953 posture film, an undated amateur home movie and a 1959 film about barbers) go through the same editorial structure. Each gets an uninterrupted opening action. Then three of them are crosscut at the moment of setting something down. Two return after their practice, each held for a different length. The shared operation (hands placing, lifting, arranging) creates a relation. The differences of decade, colour, sound space and purpose keep the five from becoming interchangeable. **The exception is the barber's chair.** It is the only practice done *to* someone. Its person, the boy, has to hold still while another person's hands work on him, so it cannot join the "setting down" crosscut. It gets the longest opening and does not return.

No religious, ethnic or other identity is inferred. The structure says nothing about what any practice *means* to the person. I do not know, and the sources do not say.

## 2 · Forage log

- Searches: `pray|church|ritual|wash|kitchen|cook|tea|breakfast|sew|knit`, `hand`, `chair|sit|seat`. Then the full 405-clip contact sheet, read for anyone performing a small, complete, everyday act in one shot.
- **Found and used:** kitchen *Toute La Bande, Episode 9: Bricolage* (1970) d2156bef, a 22.8 s single take, colour; garden *Victory Gardens* (undated) 4f70731f; clothesline *Health: Your Posture* (1953) 0f8a091e 24–31 s; lawn chairs *Amateur Film Children Playing Near Hudson* (undated, silent) 46cd8d58; barber *Barbers* (1959) c015a7f0.
- **Considered, not used:** *Command Performance* (1942), record pressing (industrial, not personal); *Two Pay Days* (1927), counting money at a desk (used in 056); *Learning to Set Type* (1959, used in 056); *Facts About Film* (1948), a boy rewinding a reel; *Nature's Cameo* (1930), a crouching man digging; *Inside/Outside* (1983), a couple eating, 6 s; *Thanksgiving Cooking Class* (2020), handheld and blurred; *Story of a City* (1946), washing on a line with no person.
- **Surprises.** The kitchen shot is one continuous camera pull-back from a frying pan to the woman. There is no cut, so her whole sequence (stir, scoop, lift, exit) is one uninterrupted record. The lawn-chair home movie is the only footage made by no one *for* an audience: it is an amateur record, not a demonstration.
- **What the archive does not have:** any participant's own statement about their practice, any self-described religious or devotional practice, washing of hands or body, prayer, any footage that runs on after a practice for the clothesline, barber or lawn-chair people, and any clean sync sound of the actions (frying, pegging, clippers). The speech-band tracks are probably narration.

## 3 · The cut (main, `edl.json`)

| t | source (year) · id · clip in–out · film time | action | role |
|---|---|---|---|
| 0.0–11.0 | *Toute La Bande ep. 9* (1970) · d2156bef · 0.0–11.0 · 759.0 s | Camera pulls back from a pan to a woman stirring potatoes at a stove | Opening 1, uninterrupted, source sound (speech-band, language unverified, untranscribed) |
| 11.0–17.0 | *Victory Gardens* (undated) · 4f70731f · 0.0–6.0 · 355.9 s | Hands take from a bowl and press into a furrow | Opening 2, uninterrupted, source track (index: music) |
| 17.0–21.2 | *Health: Your Posture* (1953) · 0f8a091e · 24.4–28.6 · 371.7 s | A woman lifts a sheet to a clothesline | Opening 3, uninterrupted, source track (narration probable) |
| 21.2–26.8 | *Amateur Film Children Playing Near Hudson* (undated) · 46cd8d58 · 1.1–6.7 · 338.7 s | Two people in wicker garden chairs, backs to camera, one with a paper | Opening 4, the whole surviving shot, silent |
| 26.8–37.3 | *Barbers* (1959) · c015a7f0 · 0.0–10.5 · 471.6 s | A barber combs and lifts a boy's hair (shot 1, 0–7.4 s), then the source's own cut to a close view of clippers at the boy's head | Opening 5 / **exception**. Ends before the source dissolves to a different salon (~10.6 s) |
| 37.3–43.8 | kitchen · 11.0–17.5 | She scoops potatoes onto the plate | Crosscut: setting down |
| 43.8–47.8 | garden · 6.0–10.0 | The last of the bowl goes into the ground | Crosscut |
| 47.8–50.4 | clothesline · 28.6–31.2 | The sheet goes over the line; ends at the source's dissolve | Crosscut |
| 50.4–55.6 | kitchen · 17.5–22.7 | She lifts the plate and walks out; the stove stays in frame | Return (5.2 s) |
| 55.6–62.6 | garden · 10.8–17.8 | After the source's dissolve, a man stands in the planted plot | Return (7.0 s) |
| 62.6–63.6 | black | | |
| 63.6–67.6 | card: "Five records, five sources, 1953–1970 and undated / Sources: movingimagearchive.com · see ledger" | | |

Every segment of a source continues from where that source's previous segment stopped (no repeats, no reordering within a source). Each person's sound is heard only under their own picture.

**Alternative (`edl-alt.json`)**: each source's whole usable passage once, uninterrupted, in the same order. Kitchen 0–22.7, garden 0–17.8, clothesline 24.4–31.2, lawn chairs 1.1–6.7, barber 0–10.5. This is the "longer individual passages" comparison the prompt asks for.

## 4 · Departures from the prompt's hard proof

- **No consenting participants, no self-descriptions, no statements in their own language, no subtitles.** These are staged or instructional films (plus one home movie). The people did not choose the practice and were not asked what it means. The "participant ledger" is therefore only descriptive (see §3). The prompt's subtitle and translation requirements cannot be met, and I did not invent text to fill the gap.
- 67.6 s instead of 100–120 s. That is all the footage available locally that keeps each person's action uninterrupted without repeating it.
- Only two of the five can "return after the practice". The other sources contain no footage after the action.
- The exception is structural (a practice done to someone, which does not join the crosscut). It is not a resistant *belief*. That would need testimony the archive does not hold.
- Speech-band tracks (kitchen, clothesline, barber) are probably narration or dialogue that I could not transcribe. The kitchen track's language (probably French, given the title) is **unverified**. The *Victory Gardens* track is indexed as music. I kept it as source sound and did not add a score.

## 5 · Self-review against §5 (builder's reading of frames; NOT a critic verdict)

- *Viewer can distinguish the five afterwards*: likely. They differ in colour (two colour sources, three black and white), setting (kitchen, soil, line, lawn, barbershop) and sound (one silent).
- *A parallel action leads to a meaningful difference*: the "setting down" crosscut ends with one person leaving her kitchen and one standing in a finished plot. The barber's boy is never released into the pattern.
- *The exception is integral*: intended (the longest opening; it is excluded from the crosscut by what it is). Untested.
- *Speech, subtitles and source context agree*: **not met.** There are no subtitles, and the speech is unverified.
- *The final passage changes the understanding of a practice*: weak. The returns show what remains (an empty stove, a planted plot) but add little new.
- Structural audit: each of the five has at least one uninterrupted passage (kitchen 11.0 s, garden 6.0 s, clothesline 4.2 s, lawn chairs 5.6 s, barber 7.4 s + 3.1 s) and a source credit in the ledger. **Largest gap**: no testimony, so the theorem's core ("individual testimony not interchangeable") is represented only by visual and sonic difference, not by anything the people say.
