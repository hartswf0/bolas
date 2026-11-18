"""le-maki-mococo -- a paper mouth reads one fixed poem; sound, then text, then image (SCION editor rev E3).

E3 = repair round 1: mouth and gong re-made as visibly cut paper / printed card (mouth_rig.py, u3/make_gong.py);
ledger synced with the cut (editor_ledger.py + u1/fixture_check.py); 'popcorn' closes on its medial p; cavity
trimmed behind the F/V lip; closer framing; the engraving's label says it was cut out and re-hung, from 0:38.0.

Direction 2 'Paper Mouth' (spine) + Direction 3 'Gong to Animal' (image cue), plan.md rev P1, shot list S0-S9.

HANDMADE : the articulated cut-paper mouth, pose library + decoder, kinetic type, red pencil (mouth_rig.py, U2);
           the bronze-card gong, cord and knot (gong_rig.py, U3); captions, cue strip, end card; paper/cord
           sound effects and room tone (kit synthesis, declared).
FORAGED  : the reading voice (Lingua Libre word recordings on Wikimedia Commons: Grendelkhan CC0, Vealhurl
           CC BY-SA 4.0 'binturong' and 'popcorn'; all 16 words incl. line 3, assembled and measured by U1,
           cue_timeline.json); the binturong (Brehm's Life of Animals p. 265,
           engraved by F. Specht, 1895, public domain; GrabCut cutout by U3).

Run from the oulipo project root:
  python3 films/le-maki-mococo.py                 render assets/films/le-maki-mococo.mp4 (65 s)
  python3 films/le-maki-mococo.py --stills 6 24 46  stills into films/stills/le-maki-mococo/
  python3 films/le-maki-mococo.py --test-shot     films/sources/le-maki-mococo/editor/test_shot.mp4
  python3 films/le-maki-mococo.py --image-first   the baseline condition (branches.image_first), ~17 s
"""
import hashlib
import json
import math
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FILMS = Path(__file__).resolve().parent
SWARM = FILMS / "swarm" / "le-maki-mococo"
sys.path.insert(0, str(FILMS))
sys.path.insert(0, str(SWARM))
import kit  # noqa: E402
from kit import Film, Mix  # noqa: E402
import mouth_rig as M  # noqa: E402
import gong_rig as G  # noqa: E402

SLUG = "le-maki-mococo"
IMAGE_FIRST = "--image-first" in sys.argv
TEST_SHOT = "--test-shot" in sys.argv
TL = json.loads((SWARM / "cue_timeline.json").read_text())
FT = TL["audio"]["film_time"]
VOICE_DIR = Path(TL["audio"]["files"]["voice_poem.wav"]["path"]).parent

# ----------------------------------------------------------------------------------------- cues
CUES = {c["cue_id"]: float(c["t_avail"]) for c in TL["cues"]}            # Q_sound 2.0, Q_text 15.5, Q_image 38.0
if IMAGE_FIRST:
    br = TL["branches"]["image_first"]
    CUES = {c["cue_id"]: (None if c["t_avail"] is None else float(c["t_avail"])) for c in br["cues"]}
CUE_ORDER = ("Q_sound", "Q_text", "Q_image")
CUE_NAME = {"Q_sound": "sound", "Q_text": "text", "Q_image": "image"}


def released(q, t):
    return CUES.get(q) is not None and t >= CUES[q] - 1e-9


# ----------------------------------------------------------------------------------------- responses
# Staging decision (U1 staging_warning, option b): the measured voice runs past the plan's 0:10 / 0:24, so each
# guess is said 0.4 s after the voice that it answers has ended.  R3/R4 keep the plan times.  P1 is re-checked.
# E3: these staged times are now written into the ledger itself (editor_ledger.py), so ledger = cut.
RESP = {r["resp_id"]: dict(r) for r in TL["responses"]}
if not IMAGE_FIRST:
    assert RESP["R1"]["t_said"] >= FT["S1"]["end"] + 0.4 - 1e-6 and RESP["R2"]["t_said"] >= FT["S3"]["end"] + 0.4 - 1e-6
    SHOW = {"R1": (RESP["R1"]["t_said"], 15.25), "R2": (RESP["R2"]["t_said"], 31.6),
            "R3": (44.0, 51.8), "R4": (48.5, 51.8)}
    RESP_ON = ["R1", "R2", "R3", "R4"]
else:
    for r in TL["branches"]["image_first"]["responses"]:
        RESP[r["resp_id"]] = dict(r)
    SHOW = {"B1": (RESP["B1"]["t_said"], 17.5), "B2": (RESP["B2"]["t_said"], 17.5)}
    RESP_ON = ["B1", "B2"]


def mss(t):
    return f"{int(t) // 60}:{int(t) % 60:02d}"


def resp_label(r):
    cites = []
    for q in CUE_ORDER:
        if q in r["cites"]:
            cites.append(CUE_NAME[q] + (f" ({mss(CUES[q])})" if q == "Q_image" and not IMAGE_FIRST else ""))
    return f"{r['speaker'].upper().replace('(FICTIONAL)', '(fictional)')} · {mss(r['t_said'])} · cites: {', '.join(cites)}"


# ----------------------------------------------------------------------------------------- invariants
def invariant_1_cue_order():
    if IMAGE_FIRST:
        assert CUES["Q_image"] < CUES["Q_sound"] and CUES["Q_text"] is None
        return
    assert CUES["Q_sound"] == 2.0 and CUES["Q_text"] == 15.5 and CUES["Q_image"] == 38.0
    assert CUES["Q_sound"] < CUES["Q_text"] < CUES["Q_image"]
    # sound: first voiced sample is at Q_sound; text: no glyph lands before Q_text; image: engraving only from Q_image
    assert abs(FT["S1"]["at"] - CUES["Q_sound"]) < 1e-9
    assert min(s["t0"] for s in FT["S3"]["syllables"]) >= CUES["Q_text"]
    assert G.t_image(CUES) == CUES["Q_image"]
    for t in (0.0, CUES["Q_text"] - 1 / 24):
        assert np.asarray(M.type_layer(t, ONSETS))[..., 3].max() == 0, "poem glyph visible before Q_text"


def glyph_alpha(t):
    return np.asarray(M.type_layer(t, ONSETS, cursor=False))[..., 3]


GLYPH_HASH = hashlib.sha1(json.dumps([g["box"] for g in M.GLYPHS]).encode()).hexdigest()


def invariant_2_glyph_boxes():
    """Poem fixed: the glyph table is a pure function of the frozen string, and every glyph keeps its box."""
    assert [L["text"] for L in TL["poem"]["lines"]] == M.POEM
    assert hashlib.sha1(json.dumps([g["box"] for g in M.glyph_table()]).encode()).hexdigest() == GLYPH_HASH
    if IMAGE_FIRST:
        return
    x0, y0, x1, y1 = [int(round(v)) for v in M.HANGS_BOX]
    box = (slice(y0 - 26, y1 + 8), slice(x0 - 4, x1 + 4))
    a24, a46, a58 = glyph_alpha(24.0)[box], glyph_alpha(46.0)[box], glyph_alpha(58.0)[box]
    assert a24.max() > 200 and np.array_equal(a24, a46) and np.array_equal(a46, a58), "'hangs' glyph box changed"
    full = glyph_alpha(30.0)
    for t in (38.0, 46.0, 59.9):
        assert np.array_equal(full, glyph_alpha(t)), f"poem glyphs moved or changed at {t}"


def admit_reading(r, t_said=None):
    """P1: every cited cue is released at or before t_said."""
    t = r["t_said"] if t_said is None else t_said
    return all(CUES.get(q) is not None and CUES[q] <= t for q in r["cites"])


def invariant_3_citations():
    for rid in RESP_ON:
        r = RESP[rid]
        assert admit_reading(r), f"{rid} cites a cue released after it is said"
        assert SHOW[rid][0] >= r["t_said"] - 1e-9
        assert "(fictional)" in r["speaker"]
        if not IMAGE_FIRST:   # E3: ledger time == on-screen label == first frame showing the caption (within 1 frame)
            assert r["on_screen_label"] == resp_label(r), (rid, r["on_screen_label"], resp_label(r))
            assert abs(r["first_frame_shown"] - SHOW[rid][0]) <= 1 / 24 + 1e-9
            assert abs(SHOW[rid][0] * 24 - round(SHOW[rid][0] * 24)) < 1e-6, "caption must start on a frame"
    for x in ([] if IMAGE_FIRST else TL.get("quarantined_counterexamples", [])):
        assert not admit_reading(x), "counterexample should fail P1"
    if not IMAGE_FIRST:
        assert "by its tail" in RESP["R3"]["quoted_span"] and "Q_image" in RESP["R3"]["cites"]
        assert "Q_image" not in RESP["R1"]["cites"] + RESP["R2"]["cites"]
        assert SHOW["R4"][1] - SHOW["R4"][0] >= 2.5
        assert G.T_ASM >= RESP["R1"]["t_said"]           # Reader A's picture is built only after the guess is said


RING_WORDS = ("ring", "bell", "chime", "gong")


def invariant_7_no_ring(events):
    for e in events:
        assert e["kind"] in ("tick", "creak", "tear", "land", "flop", "scratch"), e
        assert not any(w in e["kind"] for w in RING_WORDS)
    frac = [e for e in events if CUES.get("Q_image") is not None and CUES["Q_image"] <= e["t"] < CUES["Q_image"] + 6]
    assert frac and all(e["kind"] in ("tear", "land", "flop", "creak") for e in frac)


# ----------------------------------------------------------------------------------------- timing
OFFSET = 0.0                       # image-first variant: voice starts 1.0 s later (branch voice.at 3.0)
if IMAGE_FIRST:
    OFFSET = TL["branches"]["image_first"]["voice"]["at"] - FT["S1"]["at"]
    G.T_ASM = 1e9                  # no gong is ever imagined in the baseline
    G.T_SWING = 1e9
else:
    G.T_ASM = round(RESP["R1"]["t_said"] + 0.45, 3)          # S2: the guess, then its picture
    G.T_SWING = RESP["R2"]["t_said"]                         # S4: "It hangs and swings" sets the gong swinging


def section_speech(sec, shift=0.0):
    """U1's measured syllables + viseme keys -> rig speech events (phones) and type onsets."""
    syl = FT[sec]["syllables"]
    keys = sorted(TL["visemes"]["film_time"][sec], key=lambda k: k["t"])
    ev, onsets = [], {}
    for s in syl:
        t0, t1 = s["t0"] + shift, s["t1"] + shift
        onsets[s["seg_id"]] = (t0, t1)
        ks = [dict(k) for k in keys if k["seg_id"] == s["seg_id"]]
        sev = []
        for i, k in enumerate(ks):
            a = max(t0 - 0.06, k["t"] + shift - 0.02) if i == 0 else k["t"] + shift
            b = ks[i + 1]["t"] + shift if i + 1 < len(ks) else t1
            if b <= a:
                continue
            op = TL["visemes"]["openness"].get(k["shape"], 0)
            base = M.POSES[k["shape"]]["jaw"]
            jaw = base * (k["jaw"] / op) if op > 0 else base              # U1 loudness factor on the pose's own jaw
            sev.append(dict(t0=a, t1=b, pose=k["shape"], kind="speech", jaw=float(min(M.JAW_MAX, jaw)), seg=s["seg_id"]))
        # E3: a consonant-vowel-consonant syllable with a very short vowel ('pop' in 'popcorn': 0.06 s of O between
        # two closures) loses its vowel on twos; trim each flanking consonant to one pair of frames (>= 0.09 s) and
        # give the vowel the middle, so the lips close, open, and close again.
        if len(sev) == 3 and sev[1]["t1"] - sev[1]["t0"] < 0.13:
            c0, v, c1 = sev
            c0["t1"] = min(c0["t1"], c0["t0"] + 0.09)
            c1["t0"] = max(v["t1"], c1["t1"] - 0.10)
            v["t0"], v["t1"] = c0["t1"], c1["t0"]
        ev += sev
    # E3 (critic: the medial p of 'popcorn' never closed): every bilabial closure is held >= 0.09 s, i.e. at least
    # one full pair of frames on twos, borrowing the time from the following key (it starts later).
    ev.sort(key=lambda e: e["t0"])
    for i, e in enumerate(ev):
        if e["pose"] == "MBP" and e["t1"] - e["t0"] < MBP_MIN:
            e["t1"] = e["t0"] + MBP_MIN
            for f in ev[i + 1:]:
                if f["t0"] < e["t1"]:
                    f["t0"] = min(e["t1"], f["t1"] - 0.09)       # the vowel keeps a pair of frames too
    return ev, onsets


MBP_MIN = 0.09                     # one pair of frames on twos (>= 2 frames at 24 fps)


def gestures():
    if IMAGE_FIRST:
        return []
    r1, r2 = RESP["R1"]["t_said"], RESP["R2"]["t_said"]
    return [
        dict(t0=r1 - 0.2, t1=r1 + 0.7, pose="hm", kind="gesture"),                          # S2 Reader A: pursed hm
        dict(t0=r1 + 0.7, t1=r1 + 2.4, pose="LNT", kind="gesture", jaw=1.6),                # ... opens slightly
        dict(t0=r2 - 0.2, t1=31.0, pose="rest", kind="gesture", jaw=2.8, ease=0.8, jaw_from=0.8),   # S4 thinking
        dict(t0=38.3, t1=44.0, pose="surprise", kind="gesture", ease=1.1, jaw_from=0.8),    # S6 slow surprise
        dict(t0=44.0, t1=45.2, pose="O", kind="gesture"),                                    # S7 'Oh -'
        dict(t0=45.2, t1=45.8, pose="hm", kind="gesture"),                                   # ... closes
    ]


EVENTS, ONSETS = [], {}
if IMAGE_FIRST:
    e, _ = section_speech("S1", OFFSET)
    EVENTS += e
    BREATHS = [(0.9, 1.4, 1.0)]
else:
    for sec in ("S1", "S3", "S6", "S8"):
        e, o = section_speech(sec)
        EVENTS += e
        if sec == "S3":
            ONSETS = o
    BREATHS = list(M.BREATHS)                    # S0 one breath, S5 one slow breath (declared)
EVENTS += gestures()
SECONDS = 17.5 if IMAGE_FIRST else 65.0
TRACK = M.make_track(EVENTS, BREATHS, seconds=SECONDS)


def lip_set(t):
    if IMAGE_FIRST:
        return "A"
    return "B" if RESP["R2"]["t_said"] - 0.2 <= t < 31.0 else "A"


POEM_WORDS = sorted({v["word"] for v in M.SYL.values()})
KEY_WORDS = (("hangs",), ("swings",), ("never", "rings"))


def darken(t):
    """S4: 'hangs', 'swings', 'never rings' come forward one by one (no glyph moves, no glyph changes).
    The poem ink is already near-black, so the rest of the poem greys (rig darken < 0 lightens: INK x (1 - 0.55 v))
    and each key word returns to full ink in turn; everything eases back to full ink in the S5 hold."""
    if IMAGE_FIRST:
        return None
    r2 = RESP["R2"]["t_said"]
    hold = kit.smooth(kit.ramp(t, r2 + 0.2, r2 + 0.6)) * (1 - kit.smooth(kit.ramp(t, 33.0, 35.0)))
    if hold <= 0:
        return None
    grey = -3.2 * hold                                     # INK (42,36,34) -> about (116,99,94)
    out = {w: grey for w in POEM_WORDS}
    for k, words in enumerate(KEY_WORDS):
        a = kit.smooth(kit.ramp(t, r2 + 0.7 + 0.8 * k, r2 + 1.0 + 0.8 * k))
        for w in words:
            out[w] = grey * (1 - a)
    return out


# ----------------------------------------------------------------------------------------- type + labels
INTER = "/usr/share/fonts/opentype/inter/"
F_STRIP = ImageFont.truetype(INTER + "Inter-Regular.otf", 13)
F_STRIP_M = ImageFont.truetype(INTER + "Inter-Medium.otf", 13)
F_LABEL = ImageFont.truetype(INTER + "Inter-Medium.otf", 13)
F_CAP = ImageFont.truetype(INTER + "Inter-Regular.otf", 19)
F_END = ImageFont.truetype(M.CAL, 30)
F_END_S = ImageFont.truetype(INTER + "Inter-Regular.otf", 13)
MUTED = (107, 98, 91)
INKC = (42, 36, 34)
ROSE = (196, 112, 120)


def wrap(s, f, width):
    words, lines, cur = s.split(" "), [], ""
    for w in words:
        nxt = (cur + " " + w).strip()
        if f.getlength(nxt) > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = nxt
    return lines + [cur]


def cue_strip(d, t):
    """Top right, y 22, ending left of the cord (x 850): timestamp + ● released / ○ not yet, on every frame."""
    x = 832
    for q in reversed(CUE_ORDER):
        on = released(q, t)
        name = CUE_NAME[q]
        w = F_STRIP.getlength(name)
        col = INKC if on else MUTED
        d.text((x - w, 22), name, font=F_STRIP_M if on else F_STRIP, fill=col, anchor="lm")
        cx = x - w - 9
        if on:
            age = t - CUES[q]
            fresh = max(0.0, 1 - age / 0.6) if age < 0.6 else 0.0
            if fresh:
                rr = 4 + 5 * (1 - fresh)
                d.ellipse([cx - rr, 22 - rr, cx + rr, 22 + rr], outline=ROSE + (int(200 * fresh),), width=1)
            d.ellipse([cx - 4, 18, cx + 4, 26], fill=col)
        else:
            d.ellipse([cx - 4, 18, cx + 4, 26], outline=MUTED, width=1)
        x = cx - 18
    ts = f"{mss(t)}.{int((t % 1) * 10)}"
    d.text((x - 6, 22), ts, font=F_STRIP_M, fill=MUTED, anchor="rm")


def caption(d, rid, t, y):
    a0, a1 = SHOW[rid]
    if not (a0 <= t < a1):
        return
    al = min(1.0, (t - a0 + 1 / 24) / 0.25) * min(1.0, (a1 - t) / 0.35)     # visible from its first frame
    if rid == "R3" and not IMAGE_FIRST:     # the reconsideration steps back (still legible) when the alternate speaks
        al *= 1 - 0.4 * kit.smooth(kit.ramp(t, SHOW["R4"][0], SHOW["R4"][0] + 0.4))
    r = RESP[rid]
    d.text((455, y), resp_label(r), font=F_LABEL, fill=MUTED + (int(255 * al),), anchor="la")
    for i, ln in enumerate(wrap("“" + r["quoted_span"] + "”", F_CAP, 485)):
        d.text((455, y + 19 + i * 23), ln, font=F_CAP, fill=INKC + (int(255 * al),), anchor="la")


def end_card(d, t):
    al = min(1.0, (t - 60.0) / 0.5)
    c = INKC + (int(255 * al),)
    m = MUTED + (int(255 * al),)
    d.text((480, 200), "Same poem.", font=F_END, fill=c, anchor="mm")
    d.text((480, 246), "Sound 0:02 · text 0:15 · image 0:38.  Readers A and B are fictional.",
           font=ImageFont.truetype(INTER + "Inter-Regular.otf", 17), fill=c, anchor="mm")
    lines = ["Voice: 14 Lingua Libre single-word recordings on Wikimedia Commons by Grendelkhan (CC0) and Vealhurl",
             "('binturong', 'popcorn', CC BY-SA 4.0), trimmed, loudness-matched, re-ordered into a poem the speakers",
             "never read; 'hangs', 'swings' = 'hang', 'swing' + the /z/ of 'is'. The soundtrack is CC BY-SA 4.0.",
             "Sources: commons.wikimedia.org/wiki/File:LL-Q1860_(eng)-Vealhurl-binturong.wav and ..._Vealhurl-popcorn.wav;",
             "all 14 file links, authors and licences: films/credits/le-maki-mococo.json.",
             "Image: the binturong from Brehm's Life of Animals (1895) p. 265, engraved by F. Specht, public domain",
             "(scan: Biodiversity Heritage Library, CC BY 2.0 tag on Commons); cut out and hung by its tail by us",
             "(in the original it stands, tail curled round a branch).",
             "Handmade: paper mouth, printed card gong, cord, type, red pencil; room tone and paper sounds synthesised."]
    for i, ln in enumerate(lines):
        d.text((480, 290 + i * 19), ln, font=F_END_S, fill=m, anchor="mm")


# ----------------------------------------------------------------------------------------- picture
HANG_CUES = {"Q_image": CUES["Q_image"]}
G.ENGRAVING_LABEL = False      # E3: the editor draws the fuller disclosure label (engraving_label) from Q_image
F_ENGR_M = ImageFont.truetype(INTER + "Inter-Medium.otf", 12)
F_ENGR = ImageFont.truetype(INTER + "Inter-Regular.otf", 12)
ENGRAVING_LABEL = [("cut out from Brehm, 1895 (engraved by F. Specht)", F_ENGR_M),
                   ("hung here by us, by its tail, from our cord;", F_ENGR),
                   ("in the original it stands, tail round a branch", F_ENGR)]


def engraving_label(d, t):
    if not released("Q_image", t):
        return
    al = min(1.0, (t - CUES["Q_image"] + 1 / 24) / (2 / 24))
    for i, (txt, f) in enumerate(ENGRAVING_LABEL):
        d.text((836, 44 + i * 15), txt, font=f, fill=MUTED + (int(255 * al),), anchor="ra")
WHITE = (255, 255, 255)


def picture(t, ink):
    ink.paper(WHITE, grain=False)               # pure white field (reference σ=0); paper tooth lives in the pieces
    img = ink.img.convert("RGBA")
    if t < 60.0 or IMAGE_FIRST:
        img.alpha_composite(M.mouth_layer(t, TRACK, lip_set(t)))
        if not IMAGE_FIRST:
            img.alpha_composite(M.type_layer(t, ONSETS, darken=darken(t)))
            if t >= 52.0:
                img.alpha_composite(M.underline_layer(t))
        img.alpha_composite(G.hang_layer(t, HANG_CUES))
    d = ImageDraw.Draw(img, "RGBA")
    if t < 60.0 or IMAGE_FIRST:
        if IMAGE_FIRST:
            caption(d, "B1", t, 388)
            caption(d, "B2", t, 460)
            d.text((455, 530), "baseline condition: image first (branches.image_first)", font=F_LABEL, fill=MUTED, anchor="ls")
        else:
            caption(d, "R1", t, 395)
            caption(d, "R2", t, 395)
            caption(d, "R3", t, 388)
            caption(d, "R4", t, 460)
    else:
        end_card(d, t)
    if t < 60.0 or IMAGE_FIRST:
        engraving_label(d, t)
    cue_strip(d, t)
    ink.img = img.convert("RGB")
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


# ----------------------------------------------------------------------------------------- sound
def load_wav(p):
    with wave.open(str(p)) as w:
        assert w.getframerate() == 44100 and w.getsampwidth() == 2
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768.0
        if w.getnchannels() == 2:
            x = x.reshape(-1, 2).mean(1)
    return x


def no_ring(*a, **k):
    raise AssertionError("invariant 7: the gong never rings")


SFX = []
PENCIL_STROKES = ((52.0, 52.9), (53.1, 53.8))        # mouth_rig.underline_layer's two strokes under 'hangs'


def sfx_events():
    """Every synthesised (non-speech) effect in the mix, in film time: gong_rig's paper/cord events + the pencil.
    E4: this list IS the ledger's declared_silences_and_synth.sfx_events (asserted, invariant 8)."""
    if not IMAGE_FIRST:
        ev = [dict(e) for e in G.events(HANG_CUES)]
        for a, b in PENCIL_STROKES:
            ev.append(dict(t=a, kind="scratch", gain=0.035, pan=0.2, seconds=round(b - a, 3),
                           synth="kit band-passed noise 2-7 kHz shaped by stroke speed",
                           note="red pencil underlines 'hangs' (S8)"))
    else:   # no gong is ever built in the baseline (G.events would wait forever on wedges that were never placed)
        k0 = G.T_KICK + (CUES["Q_image"] - G.T_IMAGE_DEFAULT)
        ev = [dict(t=k0, kind="flop", gain=0.18, pan=0.55), dict(t=k0 + G.T_B / 4, kind="creak", gain=0.07, pan=0.55)]
    return sorted(ev, key=lambda e: e["t"])


def invariant_8_ledger_sfx(mixed):
    """E4 (reviewer): the ledger's SFX list equals the set of SFX kinds and times actually mixed (within 1 frame)."""
    led = TL["declared_silences_and_synth"].get("sfx_events")
    assert led is not None, "ledger has no sfx_events: run films/le-maki-mococo.py --dump-ledger, then editor_ledger.py"
    a = sorted((e["kind"], e["t"]) for e in mixed)
    b = sorted((e["kind"], e["t"]) for e in led)
    assert len(a) == len(b) and all(x[0] == y[0] and abs(x[1] - y[1]) <= 1 / 24 for x, y in zip(a, b)), "ledger SFX != mix"


def sound(mix):
    mix.bell = no_ring
    mix.ring = no_ring
    end = 17.5 if IMAGE_FIRST else 60.0
    if IMAGE_FIRST:
        mix.room(0, end, gain=0.018)
    else:
        mix.room(0, 31.2, gain=0.018)
        mix.room(30.8, 7.4, gain=0.006)            # S5 declared silence: room tone only (measured in assembly.md)
        mix.room(37.8, end - 37.8, gain=0.018)
    vp = load_wav(VOICE_DIR / "voice_poem.wav")
    if IMAGE_FIRST:
        mix.add(vp, FT["S1"]["at"] + OFFSET, 0.95, -0.15)
    else:
        mix.add(vp, FT["S1"]["at"], 0.95, -0.15)                                  # S1 Q_sound
        mix.add(vp, FT["S3"]["at"], 0.95, -0.15)                                  # S3 identical bytes
        mix.add(load_wav(VOICE_DIR / "voice_binturong.wav"), FT["S6"]["at"], 0.85, -0.15)
        mix.add(load_wav(VOICE_DIR / "voice_L1.wav"), FT["S8"]["at"], 0.95, -0.15)
    ev = sfx_events()
    if not IMAGE_FIRST:
        invariant_7_no_ring(ev)
    for e in ev:
        t, g, p = e["t"], e["gain"], e["pan"]
        if t >= end:
            continue
        if e["kind"] == "tick":
            mix.click(t, g, p, bright=3200)
        elif e["kind"] == "land":
            mix.click(t, g, p, bright=1500, seconds=0.04)
        elif e["kind"] == "tear":
            n = mix.noise(0.06) * np.exp(-np.linspace(0, 5, int(0.06 * mix.rate)))
            mix.add(mix.band(n, 1500, 6000), t, g, p)
            mix.click(t, g * 0.6, p, bright=2500)
        elif e["kind"] == "creak":
            sec = 0.35
            tt = mix.t(sec)
            n = mix.band(mix.noise(sec), 300, 900) * (0.55 + 0.45 * np.sign(np.sin(2 * np.pi * 31 * tt)))
            mix.add(n * np.hanning(len(n)), t, g, p)
        elif e["kind"] == "flop":
            mix.thud(t, freq=90, gain=g, pan=p, seconds=0.2)
        elif e["kind"] == "scratch":
            sec = e["seconds"]
            tt = mix.t(sec)
            speed = np.sin(np.pi * np.clip(tt / sec, 0, 1)) ** 0.7 * (0.75 + 0.25 * np.sin(2 * np.pi * 9 * tt))
            mix.add(mix.band(mix.noise(sec), 2000, 7000) * speed, t, g, p)
        SFX.append(e)
    if not IMAGE_FIRST:
        invariant_8_ledger_sfx(SFX)


# ----------------------------------------------------------------------------------------- render
film = Film(SLUG + ("-image-first" if IMAGE_FIRST else ""), seconds=SECONDS, boil=0, wobble=0.0, seed=7)
film.poster_at = 2.6 if IMAGE_FIRST else 46.0
film.picture(picture)
film.sound(sound)

invariant_1_cue_order()
invariant_2_glyph_boxes()
invariant_3_citations()


def render_test_shot():
    """0:15.5-0:18.0 (L1 spoken while its words type) cut directly to 0:38.0-0:40.0 (first fracture frames)."""
    out = FILMS / "sources" / SLUG / "editor"
    out.mkdir(parents=True, exist_ok=True)
    spans = [(15.5, 18.0), (38.0, 40.0)]
    mix = Mix(SECONDS, seed=7)
    sound(mix)
    pcm = mix.master()
    parts = [pcm[int(a * 44100):int(b * 44100)] for a, b in spans]
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "a.wav"
        with wave.open(str(wav), "wb") as wf:
            wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(44100)
            wf.writeframes(np.concatenate(parts).tobytes())
        mp4 = out / "test_shot.mp4"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "960x540", "-r", "24",
               "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-pix_fmt", "yuv420p",
               "-tune", "animation", "-c:a", "aac", "-b:a", "96k", "-shortest", "-movflags", "+faststart", str(mp4)]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for a, b in spans:
            for k in range(int(round(a * 24)), int(round(b * 24))):
                im = film.frame(k)
                proc.stdin.write(im.tobytes())
                if k in (int(a * 24) + 30, int(b * 24) - 1):
                    im.save(out / f"test_{k / 24:05.2f}.png")
        proc.stdin.close()
        assert proc.wait() == 0
    print("wrote", mp4)


def dump_ledger():
    """E4: write the cut's own sound-effect list, decoder paths and gestures for editor_ledger.py to merge into
    cue_timeline.json / mouth_rig.json (ledger = cut)."""
    ft = FT
    def path(t0, t1):
        return TRACK.ledger(t0, t1)
    full = [TRACK.path[k] for k in range(TRACK.n)]
    flick = M.flicker_count(full)
    out = dict(sfx_events=sfx_events(), gestures=gestures(), breaths=[dict(t_center=a, seconds=b, deg=c) for a, b, c in BREATHS],
               S1_path_12fps=path(ft["S1"]["at"], ft["S1"]["end"]), S3_path_12fps=path(ft["S3"]["at"], ft["S3"]["end"]),
               S6_path_12fps=path(38.0, 44.0), S8_path_12fps=path(ft["S8"]["at"], ft["S8"]["end"]),
               flicker_runs_lt_2_frames=flick, voice_spans={k: [ft[k]["at"], ft[k]["end"]] for k in ("S1", "S3", "S6", "S8")})
    p = SWARM / "editor_e4_dump.json"
    p.write_text(json.dumps(out, indent=1))
    print("wrote", p, "flicker", flick)


if __name__ == "__main__":
    if "--dump-ledger" in sys.argv:
        dump_ledger()
    elif TEST_SHOT:
        render_test_shot()
    else:
        if IMAGE_FIRST:          # the baseline is a ledger branch: keep it next to the editor's media, not in assets/
            sys.argv = [a for a in sys.argv if a != "--image-first"]
            film.render(out_dir=FILMS / "sources" / SLUG / "editor")
        else:
            film.render()
