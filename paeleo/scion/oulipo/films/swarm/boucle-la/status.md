# boucle-là : status (editor, r0, 2026-11-17)

**Preview:** `assets/films/boucle-la.mp4` (66.0 s, 4.96 MB, 960×540/24, AAC) · poster `assets/films/boucle-la.webp` (30.0 s: H held, note face-out on spot black) · page `assets/pages/boucle-la.png` (3200×1800, U3) · annotated `assets/pages/boucle-la-annotated.png`. Timecodes: `assembly.md`.

**Revision hashes (sha256, first 16):**
films/boucle-la.py 7765717d003dbc7d · boucle-la.mp4 ae5c844e750b6bea · boucle-la.webp d73ed5b93a0a4063 · pages/boucle-la.png 37e666ab5deb6986 (= page-animator/page.png, = page.json) · boucle-la-annotated.png 04550d0f479c5904 · page.json 86bbf06a0775bed4 · script.json 789273b95abd2345 · cutouts.json 440addb6827d5708 · route.json d2d62b25a7526325 · plan.json f3c2921ac7904821 · page-ghost.png a4203cf98275ebe4 · annotation-layer.png b9071d0a6abe3c6f · bell.wav 76cab96bbaaff31b · rustle.wav e1e79836bc8a3530 · credits ~b26c2088 (before this status).

**Review against the frozen bar**
- B1 page: U3's page, unchanged; seven occurrences A B C / H spot black / C B A, furniture in margin and gutters. Structural PASS (operator to confirm legibility at 1920 fit; balloons read in film at every hold).
- B2 fixture: PASS (59 PASS; the only unexpected row is U3's advisory annotated-page touch at x 554–555, y 1473–1475). Film paired frames 138/138 sha256-equal per pair; voice clip identity trivially satisfied (no voice in mix).
- B3 blind reader: NOT RUN by the editor (turning-point.md must come from the blind readers).
- B4: pieces from U1, frames from U3 (≥ 20 drawings per ID, note flip 6 drawings); film pastes only those frames; each occurrence lands on and holds the page drawing (fixture PASS).
- B5 aesthetic: white ground, chroma 0, spot-black H, solid crayon blacks (A/B/C ≈ 23 % < L60). Perceptual judgement pending.
- B6 film: 66.0 s, normal speed, sound; route walked A→B→C→H→C→B→A; row 3 ghost at 0–3 s and 37–39 s; one bell at 28.000 s (fixture); clean page 58.5–61.6 before the annotation trace. PASS (measured parts).
- V1 PASS (U3: 23 %, chroma p99 0). V3 PASS (U1/U3 self-checks 0.0 px). V4: mp4 4.96 MB ≤ 6; credits list print, bell, rustle and the two (unheard) voice sources; notes declare foraged/handmade.

**Remaining failure / weaknesses**
1. No voice: the shot list asked for voice clips; the user's test-shot note ("drop the English voice, keep only bell and paper") wins, so the voice-stress part of V2 is untestable. `--voices` restores them.
2. The route-trace tags are 15 px on the page and ~5 px in the film's full-page view: the route line reads, the speech-act tags do not at 960 px (readable only on the annotated PNG).
3. H wide framing (scale 0.56) puts the figures at ~280 px tall; the push to the note (31–35 s) carries the beat; the balloon is cut at the left edge during that push.
4. B's vacated sleeve patch and Odette's dark robe edge (U1) are visible in close holds.
5. Disk was full during the edit (other works filling the volume); the render was made in /dev/shm and copied. Checkpoint r0 holds real copies.
6. B3 and B5 still need the blind reader and side-by-side viewer.
