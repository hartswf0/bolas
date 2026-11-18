"""Record + credits for page 31 (Sounds only)."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b1m2 as B

N, PID = 31, "sounds-only"
jp = B.PAGES_OUT / f"{N:02d}-{PID}.jpg"
size = jp.stat().st_size
CUEVA = {
    "id": "teuf-teuf:cueva-de-las-manos",
    "title": "File:Cueva de las manos - detalle.jpg",
    "author": "Suzko",
    "license": "CC BY-SA 3.0",
    "license_url": "https://creativecommons.org/licenses/by-sa/3.0",
    "source_url": "https://commons.wikimedia.org/wiki/File:Cueva_de_las_manos_-_detalle.jpg",
    "file_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/Cueva_de_las_manos_-_detalle.jpg/960px-Cueva_de_las_manos_-_detalle.jpg",
    "carried_from": "films/credits/teuf-teuf.json (licence_checked 2026-11-16, Commons extmetadata)",
    "note": "local copy films/sources/teuf-teuf/hands_cueva.jpg (960x720), decoded with PIL only",
    "used_as_99_ways": "the charcoal-card wall: only the plain rock of the photograph's upper-left (x 0-470, y 0-215, no painted figures), its L-channel relief high-passed at low gain, mirror-tiled to each panel and printed through the teuf-teuf ramp. Adaptation shared under CC BY-SA.",
}
src = ["teuf-teuf:cueva-de-las-manos", "99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
B.credit_pages(src, N, [CUEVA])
B.write_record({
    "n": N, "id": PID, "title": "Sounds only", "family": "voice and language", "medium": "charcoal-card",
    "canon_revision": "c1",
    "rule": "No words at all: the story is told in sound lettering (scrape, tick, tap, creak); the lines become wordless balloons with their rhythm.",
    "declares": "the four lines muted (shape and rhythm only)",
    "file": f"assets/pages/99-ways/{N:02d}-{PID}.jpg", "master": f"films/sources/99-ways/masters/{N:02d}-{PID}.png",
    "beats_dir": f"films/sources/99-ways/beats/{N:02d}",
    "build": "films/swarm/99-ways/build/p31_sounds_only.py (kit: films/swarm/99-ways/build/charcoal99.py)",
    "sources": src,
    "made": [
        "charcoal-card kit (charcoal99.py): articulated grey-card puppets cut from the b1m2 control-point agent and stranger and the b1m2 scenery (desk, chair, ticket window without glazing bars, wall clock at 4:08 and 4:10, cupboard opening on its left jamb, SERVICE door); each piece a separate card with charcoal rubbed in, darker at its cut edges, its own drop shadow; brass split pins at shoulder and elbow; a blown charcoal spray halo on the wall round each figure",
        "the wall: the teuf-teuf Cueva rock relief (plain rock only) flattened to a pale wash and printed through the teuf-teuf greenish-sepia ramp; rubbed charcoal floor band and ground line",
        "the brass key: a light card cut on the ANRC 1922 key silhouette (99-ways-template cutout) on a drawn hook, its tag a blank card",
        "no words: the memo is a pale card with '4:15', a drawn key and an arrow to a drawn cupboard; the SERVICE card carries a drawn key instead of its word; the tag is blank; no TICKET OFFICE lettering",
        "sound lettering in the shared pen hand, fattened and rubbed as charcoal with a pale chalk knock-out: SCRRAPE! (chair), tick, TAP TAP TAP (his steps), tok tok (her glove on the counter), TICK / tock (clock), tok tok tok receding (her heels), CREEEAK (cupboard), tink (key), tick . . . (the silence)",
        "the four lines as wordless cut-card balloons (penlib.balloon_piece outline, no letters): one charcoal dash per syllable at its pitch, stressed syllables longer and heavier, pauses as gaps, and only the end mark in the pen hand: question 8 dashes rising to '?', answer 6 dashes falling to '.', thanks 3 dashes to '!', forgetting 7 dashes with '...' trailing off (last dashes fading) to '?'",
        "hand-ruled panel borders (penlib.border_mask), folio '31 / Sounds only' (pen99.folio)"],
    "events": {"E0": "panel 1: SCRRAPE! as he rises from the desk; memo card 4:15 + key -> cupboard; clock 4:08 'tick'; panel 2: TAP TAP TAP across the office toward the closed cupboard",
               "E1": "panel 3: at the ticket window, her 'tok tok' on the counter; balloon from her: rising rhythm to '?'",
               "E2": "panel 4: he looks up at the clock (4:10), TICK / tock; balloon from him: falling rhythm to '.'",
               "E3": "panel 5: she turns away; balloon from her: three dashes to '!'; her heels 'tok tok tok' receding",
               "E4": "panel 6: CREEEAK, the cupboard door opens on its left jamb; the key on its hook, 'tink'",
               "E5": "panel 7: pencil to chin; trailing rhythm '...' to '?'; key unmoved; SERVICE door shut; only 'tick . . .'"},
    "lines": {"question": "muted: Par-don me | have you the right time ? (8 syllables, rising)",
              "answer": "muted: Ten past four, | by the clock . (6 syllables, falling)",
              "thanks": "muted: Much o-bliged ! (3 syllables, 3 dashes, the middle one light)",
              "forgetting": "muted: Well, | here I am ... | and what for ? (7 syllables, trailing)"},
    "beat": "the office fills with sound panel by panel: scrape, steps, the question's rhythm, tick and the answer, thanks and heels, the creak; last, the forgetting balloon is laid and its rhythm trails off",
    "beat_frames": ["b01: panel 1 only: SCRRAPE!, memo, tick (E0)", "b02: + panel 2: TAP TAP TAP (E0)",
                    "b03: + panel 3: tok tok, the rising '?' balloon (E1)", "b04: + panel 4: TICK/tock, the answer's falling balloon (E2)",
                    "b05: + panel 5: '!' balloon, heels receding (E3)", "b06: + panel 6: CREEEAK, key on hook (E4)",
                    "b07: + panel 7 silent: pencil to chin, no balloon yet (E5)", "b08: + the trailing '...?' balloon and 'tick . . .' (= the page)"],
    "self_check": {"size_px": [2200, 2850], "jpeg_bytes": size, "jpeg_quality": 90,
                   "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
                   "words_on_page": "none except sound lettering (SCRRAPE, tick, TAP, tok, TICK, tock, CREEEAK, tink) and the folio title; numerals only on the memo (4:15)",
                   "dialogue_words": 0,
                   "check": "No word of dialogue appears; question (rising ? from her), answer (falling . from him under the 4:10 clock), thanks (! from her as she turns) and forgetting (trailing ...? at the open cupboard) are found by shape and end mark (maker's judgement from the full-size page; blind reading pending)"},
})
print(size)
