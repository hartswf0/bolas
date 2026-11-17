"""le-maki-mococo -- a paper mouth reads one fixed poem; sound, then text, then image (SCION editor rev E1).

Direction 2 'Paper Mouth' (spine) + Direction 3 'Gong to Animal' (image cue), plan.md rev P1, shot list S0-S9.

HANDMADE : the articulated cut-paper mouth, pose library + decoder, kinetic type, red pencil (mouth_rig.py, U2);
           the bronze-card gong, cord and knot (gong_rig.py, U3); captions, cue strip, end card; paper/cord
           sound effects and room tone (kit synthesis, declared).
FORAGED  : the reading voice (Lingua Libre word recordings on Wikimedia Commons: Grendelkhan CC0, Vealhurl
           CC BY-SA 4.0; assembled by U1, cue_timeline.json); the binturong (Brehm's Life of Animals p. 265,
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
RESP = {r["resp_id"]: dict(r) for r in TL["responses"]}
if not IMAGE_FIRST:
    RESP["R1"]["t_said"] = round(FT["S1"]["end"] + 0.4, 2)
    RESP["R2"]["t_said"] = round(FT["S3"]["end"] + 0.4, 2)
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
        assert e["kind"] in ("tick", "creak", "tear", "land", "flop"), e
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
        ks = [k for k in keys if k["seg_id"] == s["seg_id"]]
        for i, k in enumerate(ks):
            a = max(t0 - 0.06, k["t"] + shift - 0.02) if i == 0 else k["t"] + shift
            b = ks[i + 1]["t"] + shift if i + 1 < len(ks) else t1
            if b <= a:
                continue
            op = TL["visemes"]["openness"].get(k["shape"], 0)
            base = M.POSES[k["shape"]]["jaw"]
            jaw = base * (k["jaw"] / op) if op > 0 else base              # U1 loudness factor on the pose's own jaw
            ev.append(dict(t0=a, t1=b, pose=k["shape"], kind="speech", jaw=float(min(M.JAW_MAX, jaw)), seg=s["seg_id"]))
    return ev, onsets


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


def darken(t):
    """S4: 'hangs', 'swings', 'never rings' darken one by one (no glyph moves); ease back in the S5 hold."""
    if IMAGE_FIRST:
        return None
    r2 = RESP["R2"]["t_said"]
    out = {}
    for k, words in enumerate((("hangs",), ("swings",), ("never", "rings"))):
        a = kit.smooth(kit.ramp(t, r2 + 0.6 + 0.8 * k, r2 + 0.9 + 0.8 * k)) * (1 - kit.smooth(kit.ramp(t, 33.0, 35.0)))
        for w in words:
            out[w] = a
    return out if any(v > 0 for v in out.values()) else None


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
    al = min(1.0, (t - a0) / 0.25) * min(1.0, (a1 - t) / 0.35)
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
    lines = ["Voice: Lingua Libre volunteer word recordings on Wikimedia Commons — Grendelkhan (CC0),",
             "Vealhurl ('binturong', CC BY-SA 4.0); words re-ordered into a poem they never read.",
             "Image: the binturong, Brehm's Life of Animals (1895) p. 265, engraved by F. Specht, public domain.",
             "Handmade: paper mouth, bronze-card gong, cord, type, red pencil; room tone and paper sounds synthesised."]
    for i, ln in enumerate(lines):
        d.text((480, 330 + i * 21), ln, font=F_END_S, fill=m, anchor="mm")


# ----------------------------------------------------------------------------------------- picture
HANG_CUES = {"Q_image": CUES["Q_image"]}
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


def sound(mix):
    mix.bell = no_ring
    mix.ring = no_ring
    end = 17.5 if IMAGE_FIRST else 60.0
    if IMAGE_FIRST:
        mix.room(0, end, gain=0.018)
    else:
        mix.room(0, 31.2, gain=0.018)
        mix.room(30.8, 7.4, gain=0.006)            # S5 declared silence: room tone only, about -40 dB
        mix.room(37.8, end - 37.8, gain=0.018)
    vp = load_wav(VOICE_DIR / "voice_poem.wav")
    if IMAGE_FIRST:
        mix.add(vp, FT["S1"]["at"] + OFFSET, 0.95, -0.15)
    else:
        mix.add(vp, FT["S1"]["at"], 0.95, -0.15)                                  # S1 Q_sound
        mix.add(vp, FT["S3"]["at"], 0.95, -0.15)                                  # S3 identical bytes
        mix.add(load_wav(VOICE_DIR / "voice_binturong.wav"), FT["S6"]["at"], 0.85, -0.15)
        mix.add(load_wav(VOICE_DIR / "voice_L1.wav"), FT["S8"]["at"], 0.95, -0.15)
    ev = G.events(HANG_CUES) if not IMAGE_FIRST else [e for e in G.events(HANG_CUES) if e["kind"] in ("flop", "creak") and e["t"] < 10]
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
        SFX.append(e)


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


if __name__ == "__main__":
    if TEST_SHOT:
        render_test_shot()
    else:
        if IMAGE_FIRST:          # the baseline is a ledger branch: keep it next to the editor's media, not in assets/
            sys.argv = [a for a in sys.argv if a != "--image-first"]
            film.render(out_dir=FILMS / "sources" / SLUG / "editor")
        else:
            film.render()
