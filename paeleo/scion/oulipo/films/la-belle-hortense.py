"""La belle Hortense: a sextine exercise, in hommage to the novel by Jacques Roubaud (1985); a fiction re-staging
archive photographs (nothing is taken from the novel or its cover).  SCION swarm assembly, revision E3 (repair round 2).

Six 9 s modules of six 1.5 s slots.  Module I deals the six motifs ABCDEF (manteau, cloche, cle, banc, recu,
porte); each next module re-deals them by the sestina permutation sigma = [6,1,5,2,4,3].  The red coat lies on the
bench as set dressing in I.1, the visitor lays the key on it in I.4, and sigma brings the coat back to slot 3 of
module V (42.0-43.5 s), running, pan-streaked red on green, with the key dropping out of its fold.

Picture: decoded frames of prepared clips (animator unit U3 and the editor beats), all built from foraged
photographs (FSA/OWI conductor and visitor, Highsmith bench, Bourre plates by Daniel Jolivet, Commons bell
and key) cut out, articulated, stencil-dyed and pan-exposed by sub-frame integration; handmade print objects and
type from U4 laid over them.  Sound: U4's cue sheet of foraged recordings (Fridingen bell, steps, handle, hinge,
lock, keys, paper) plus kit-synthesised clicks, wind and whooshes, placed with mix.add.

    python3 films/la-belle-hortense.py                    # render assets/films/la-belle-hortense.mp4
    python3 films/la-belle-hortense.py --stills 3.75 8.25 # stills to films/stills/la-belle-hortense/
    python3 films/la-belle-hortense.py --baseline         # story-order diagnostic -> films/swarm/.../baseline-cut.mp4
"""
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit import Film, FPS, W, H, PROJECT  # noqa: E402

SLUG = "la-belle-hortense"
SW = PROJECT / "films/swarm" / SLUG
SRC = PROJECT / "films/sources" / SLUG
ANIM = SRC / "animator-scene-authors-reiniger-rig-multiplane-stencil-dye-pan-exposure-scions-2-and-44-/clips"
EDIT = SRC / "editor/clips"
PRINT = SRC / "print-sound/print"
EPRINT = SRC / "editor/print"                    # editor E2 cards (fiction label, hommage line, licence)

STRUCT = json.loads((SW / "structure.json").read_text())
PRINTJ = json.loads((SW / "print.json").read_text())
CUES = json.loads((SW / "sound_cues.json").read_text())

LETTERS = "ABCDEF"
MOTIF = {"A": "manteau", "B": "cloche", "C": "clé", "D": "banc", "E": "reçu", "F": "porte"}
ROMAN = ["I", "II", "III", "IV", "V", "VI"]
SIGMA = STRUCT["sigma"]
ORDERS = [m["order"] for m in STRUCT["modules"]]


# ----------------------------------------------------------- permutation fixture (asserted at render time)
def sigma_step(order):
    return "".join(order[s - 1] for s in SIGMA)


assert SIGMA == [6, 1, 5, 2, 4, 3]
assert sigma_step("ABCDEF") == "FAEBDC", "fixture ABCDEF -> FAEBDC"
o = "ABCDEF"
for _ in range(6):
    o = sigma_step(o)
assert o == "ABCDEF", "sigma^6 = id"
assert ORDERS[0] == "ABCDEF"
for i in range(5):
    assert ORDERS[i + 1] == sigma_step(ORDERS[i]), f"module {ROMAN[i + 1]} = sigma(module {ROMAN[i]})"
assert sigma_step(ORDERS[5]) == ORDERS[0], "VI returns to I"
for od in ORDERS:
    assert sorted(od) == list(LETTERS), f"duplicate motif in {od}"


def slot_start(i, k):          # i, k from 0
    return 3.0 + 9.0 * i + 1.5 * k


# ------------------------------------------------------------------ the sequence (clip per slot)
# (clip directory, clip name, first clip frame).  Clips are 36 frames = one 1.5 s slot unless noted.
A, E = ANIM, EDIT
SLOT_CLIPS = {
    "I.1": (E, "I1_manteau_E3", 0), "I.2": (E, "I2_cloche_E3", 0), "I.3": (E, "I3_cle_E2", 0),
    "I.4": (E, "I4_banc_E3", 0), "I.5": (E, "I5_recu_E3", 0), "I.6": (E, "I6_porte_E3", 0),
    "II.1": (E, "II1_porte", 0), "II.2": (E, "II2_manteau_E3", 0), "II.3": (E, "II3_recu", 0),
    "II.4": (A, "bell_strike", 0), "II.5": (A, "bench_empty", 0), "II.6": (E, "II6_cle_E3", 0),
    "III.1": (E, "III1_cle_E2", 0), "III.2": (E, "III2_porte", 0), "III.3": (A, "bench_empty", 0),
    "III.4": (E, "III4_manteau_E3", 0), "III.5": (A, "bell_strike", 0), "III.6": (E, "III6_recu", 0),
    "IV.1": (E, "IV1_recu", 0), "IV.2": (E, "I4_banc_E3", 0), "IV.3": (A, "bell_strike", 0),
    "IV.4": (E, "IV4_porte", 0), "IV.5": (E, "IV5_manteau_E2", 0), "IV.6": (A, "bench_empty", 0),
    "V.1": (E, "V1_banc_E2", 0), "V.2": (E, "V2_recu_E2", 0),
    "V.3": (A, "V3_manteau_clean", 12),          # the accepted test shot: clip covers 41.5-44.0, slot = frames 12..47
    "V.4": (E, "V4_cle_E2", 0), "V.5": (A, "V5_porte", 0), "V.6": (A, "bell_strike", 0),
    "VI.1": (A, "VI1_cloche", 0), "VI.2": (E, "I4_banc_E3", 0), "VI.3": (E, "VI3_porte", 0),
    "VI.4": (E, "VI4_recu", 0), "VI.5": (E, "VI5_cle", 0), "VI.6": (E, "I1_manteau_E3", 0),
}
# the motif each clip shows (checked against the order below)
CLIP_MOTIF = {
    "I1_manteau": "manteau", "I2_cloche": "cloche", "I3_cle": "clé", "I4_banc": "banc", "I5_recu": "reçu",
    "I6_porte": "porte", "II1_porte": "porte", "II2_manteau": "manteau", "II3_recu": "reçu", "bell_strike": "cloche",
    "bench_empty": "banc", "II6_cle": "clé", "III1_cle": "clé", "III2_porte": "porte", "III4_manteau": "manteau",
    "III6_recu": "reçu", "IV1_recu": "reçu", "IV4_porte": "porte", "IV5_manteau": "manteau", "V1_banc": "banc",
    "V2_recu": "reçu", "V3_manteau_clean": "manteau", "V4_cle": "clé", "V5_porte": "porte", "VI1_cloche": "cloche",
    "VI3_porte": "porte", "VI4_recu": "reçu", "VI5_cle": "clé",
}
CLIP_MOTIF.update({n + "_E2": m for n, m in list(CLIP_MOTIF.items())})
CLIP_MOTIF.update({n + "_E3": m for n, m in list(CLIP_MOTIF.items()) if not n.endswith("_E2")})
CLIP_MOTIF.update({"I4_banc_E2": "banc", "I1_manteau_E2": "manteau", "I4_banc_E3": "banc", "I1_manteau_E3": "manteau"})
REPLAY = {"IV.2": "clé", "VI.2": "banc"}       # the I.4 pixels, framed and tagged I·4: an equivalent view

SLOT_TYPE = [o for o in PRINTJ["objects"] if o["id"] == "SLOT-TYPE"][0]["states"]
SEGMENTS = []                                    # (t0, t1, slot id, motif)
for i, od in enumerate(ORDERS):
    for k, letter in enumerate(od):
        sid = f"{ROMAN[i]}.{k + 1}"
        t0 = slot_start(i, k)
        ap = STRUCT["modules"][i]["appearances"][k]
        assert ap["id"] == sid and ap["motif"] == letter and abs(ap["start"] - t0) < 1e-9, sid
        clip = SLOT_CLIPS[sid][1]
        shown = REPLAY.get(sid, CLIP_MOTIF[clip])
        assert shown == MOTIF[letter], f"{sid}: clip {clip} shows {shown}, order says {MOTIF[letter]}"
        st = SLOT_TYPE[sid]
        assert st["active_word"] == MOTIF[letter].upper(), f"{sid} slot word {st['active_word']}"
        assert abs(st["t"][0] - t0) < 1e-9
        SEGMENTS.append((t0, t0 + 1.5, sid, MOTIF[letter]))


def segment_at(t):
    for seg in SEGMENTS:
        if seg[0] <= t < seg[1]:
            return seg
    return None


# the highlighted slot word equals order_i[k] at every slot midpoint (and the 3.75 + ... sample times)
for i, od in enumerate(ORDERS):
    for k, letter in enumerate(od):
        for tm in (slot_start(i, k) + 0.75, slot_start(i, k) + 0.75 + 1e-3):
            seg = segment_at(tm)
            assert SLOT_TYPE[seg[2]]["active_word"] == MOTIF[letter].upper(), (tm, seg)

# ------------------------------------------------------------------ decoding (ffmpeg only; untrusted data)
_clips = {}


def clip_frames(d, name):
    key = (str(d), name)
    if key not in _clips:
        if len(_clips) >= 3:
            _clips.pop(next(iter(_clips)))
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(Path(d) / f"{name}.mp4"),
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        a = np.frombuffer(raw, np.uint8)
        _clips[key] = a.reshape(-1, H, W, 3)
    return _clips[key]


_png = {}


def png(name):
    if name not in _png:
        _png[name] = Image.open(PRINT / name).convert("RGBA")
    return _png[name]


# enamel '6' plate on the left leaf of the door in V.5 (same plate coords as the editor beats: (470, 505), 30 px)
V5_SCALE, V5_OX, V5_OY = 1.15, int(500 * 1.15 - W / 2), int(545 * 1.15 - H / 2)
_en = png("enamel_plate_6.png")
_ew = 30.0 * V5_SCALE
ENAMEL_V5 = _en.resize((int(round(_ew)), int(round(_ew * _en.size[1] / _en.size[0]))), Image.LANCZOS)
ENAMEL_V5_XY = (int(round(470 * V5_SCALE - V5_OX - ENAMEL_V5.size[0] / 2)),
                int(round(505 * V5_SCALE - V5_OY - ENAMEL_V5.size[1] / 2)))

CREAM = (225, 229, 178)
_st = {}


def slot_type(sid):
    """U4's slot type, with a cream typed strip laid under the red caption line (as under the slot line), so the
    red stays legible over the dark shed wall as well as over the green streak."""
    if sid not in _st:
        ov = png(Path(SLOT_TYPE[sid]["file"]).name)
        a = np.asarray(ov)
        red = (a[..., 3] > 128) & (a[..., 0] > 120) & (a[..., 1] < 70) & (a[..., 2] < 80)
        red[int(H * 0.9):] = False                       # the slot line's active word has its own strip
        band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if red.any():
            ys, xs = np.nonzero(red)
            b = np.zeros((H, W, 4), np.uint8)
            b[max(ys.min() - 5, 0):ys.max() + 6, max(xs.min() - 7, 0):xs.max() + 8] = (*CREAM, 235)
            dark = (a[..., 3] > 128) & (a[..., :3].max(-1) < 40)
            dark[:max(ys.min() - 70, 0)] = False
            dark[ys.min() - 4:] = False
            if dark.any():                                # the module numeral above it
                yn, xn = np.nonzero(dark)
                b[yn.min() - 5:yn.max() + 6, max(xn.min() - 7, 0):xn.max() + 8] = (*CREAM, 235)
            band = Image.fromarray(b, "RGBA")
        band.alpha_composite(ov)
        _st[sid] = band
    return _st[sid]
INKC = (1, 2, 1)


def replay_frame_mat(img):
    out = img.convert("RGBA")
    a = np.zeros((H, W, 4), np.uint8)
    a[:12], a[-12:], a[:, :12], a[:, -12:] = (*CREAM, 255), (*CREAM, 255), (*CREAM, 255), (*CREAM, 255)
    a[12:14, 12:-12] = a[-14:-12, 12:-12] = (*INKC, 255)
    a[12:-12, 12:14] = a[12:-12, -14:-12] = (*INKC, 255)
    out.alpha_composite(Image.fromarray(a, "RGBA"))
    return out.convert("RGB")


def replay_frame(img):
    """typed frame round the replayed I.4 pixels: a cream mat 12 px wide, black rule, tag I·4 top left."""
    out = img.copy()
    mat = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = np.zeros((H, W, 4), np.uint8)
    a[:12], a[-12:], a[:, :12], a[:, -12:] = (*CREAM, 255), (*CREAM, 255), (*CREAM, 255), (*CREAM, 255)
    a[12:14, 12:-12] = a[-14:-12, 12:-12] = (*INKC, 255)
    a[12:-12, 12:14] = a[12:-12, -14:-12] = (*INKC, 255)
    mat = Image.fromarray(a, "RGBA")
    out = out.convert("RGBA")
    out.alpha_composite(mat)
    out.alpha_composite(png("replay_tag_I4.png"), (26, 24))
    return out.convert("RGB")


ENDCARD = [(57.0, "endcard_rows_0.png"), (57.5, "endcard_rows_1.png"), (58.0, "endcard_rows_2.png"),
           (58.5, "endcard_rows_3.png"), (59.0, "endcard_rows_4.png"), (59.5, "endcard_rows_5.png"),
           (60.0, "endcard_rows_6.png"), (60.5, "endcard_sigma.png"), (61.0, "endcard_credits.png")]


_eprint = {}


def eprint(name):
    if name not in _eprint:
        _eprint[name] = Image.open(EPRINT / name).convert("RGBA")
    return _eprint[name]


V4_REPLAY_FRAMES = 17                            # V.4 local frames 0..16: half-speed replay of the key leaving the hem


def ralenti_frame(img):
    """the V.4 replay is labelled like the I.4 replays: cream mat, black rule, typed tag 'V·3 ralenti'."""
    from PIL import ImageDraw, ImageFont
    out = replay_frame_mat(img)
    d = ImageDraw.Draw(out)
    f = ImageFont.truetype("/home/user/bolas/paeleo/scion/oulipo/films/sources/la-belle-hortense/editor/type/HortenseSlab-Bold.ttf", 20)
    x0, y0, x1, y1 = d.textbbox((30, 26), "V·3 ralenti ×0,64", font=f)
    d.rectangle((x0 - 6, y0 - 4, x1 + 6, y1 + 4), fill=CREAM, outline=INKC, width=2)
    d.text((30, 26), "V·3 ralenti ×0,64", font=f, fill=(165, 9, 23))
    return out


def frame_image(k):
    """the film's frame k as a PIL RGB image."""
    t = k / FPS
    if t < 3.0:
        img = Image.fromarray(clip_frames(EDIT, "TITLE_E3")[min(k, 71)]).convert("RGBA")
        img.alpha_composite(eprint("title_type_E2.png"))
        return img.convert("RGB")
    if t >= 57.0:
        name = [n for t0, n in ENDCARD if t >= t0 - 1e-9][-1]
        img = png(name).copy()
        if t >= 60.5 - 1e-9:
            img.alpha_composite(eprint("endcard_text_E2.png"))
        return img.convert("RGB")
    seg = segment_at(t)
    sid = seg[2]
    d, name, first = SLOT_CLIPS[sid]
    local = k - int(round(seg[0] * FPS))
    fr = clip_frames(d, name)
    img = Image.fromarray(fr[min(first + local, len(fr) - 1)])
    if sid == "V.5":
        img = img.convert("RGBA")
        img.alpha_composite(ENAMEL_V5, ENAMEL_V5_XY)
        img = img.convert("RGB")
    if sid in REPLAY:
        img = replay_frame(img)
    if sid == "V.4" and local < V4_REPLAY_FRAMES:
        img = ralenti_frame(img)
    img = img.convert("RGBA")
    img.alpha_composite(slot_type(sid))
    return img.convert("RGB")


# ------------------------------------------------------------------ sound: U4's cue sheet via mix.add
def read_wav(path):
    with wave.open(str(path), "rb") as wf:
        assert wf.getframerate() == 44100 and wf.getsampwidth() == 2
        x = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768.0
        if wf.getnchannels() == 2:
            x = x.reshape(-1, 2).mean(1)
    return x


CLICK_BOOST = 10 ** (10 / 20)                   # +10 dB on every typewriter click (critic: inaudible under room tone)
V4_RETIME = {"key_tink_strong.wav": 44.15, "key_tink_soft.wav": 44.33}   # landing as seen in the V.4 half-speed replay


def cue_plan(cues=None):
    out = []
    for c in (cues if cues is not None else CUES["cues"]):
        f = c["file"].split("/")[-1]
        t, g = c["t"], c["gain"]
        if f == "click.wav" or f.startswith("type_"):
            g *= CLICK_BOOST
        if c.get("slot") == "V.4" and f in V4_RETIME:
            t = V4_RETIME[f]
        out.append(dict(c, t=t, gain=g))
    return out


def lay_sound(mix, cues=None, offset=0.0):
    for c in cue_plan(cues):
        mix.add(read_wav(PROJECT / c["file"]), c["t"] - offset, gain=c["gain"], pan=c.get("pan", 0.0))


# ------------------------------------------------------------------ film
film = Film(SLUG, seconds=66.0)
film.poster_at = 43.3


def picture(t, ink):
    ink._grain = False              # the cover's texture is motion streak, not grain: no added grain anywhere
    k = int(round(t * FPS))
    ink.img.paste(frame_image(k))


film.picture(picture)
film.sound(lay_sound)


# ------------------------------------------------------------------ baseline diagnostic (story order, no sigma)
BASE = [  # (label, clip dir, clip, first frame, caption)
    ("card", None, None, 0, None),
    ("I.1", EDIT, "BASE_I1", 0, "Une gare vide."),
    ("I.4", EDIT, "BASE_I4", 0, "Elle laisse la clé sur le banc."),
    ("II.2", EDIT, "II2_manteau_E3", 0, "Il prend son manteau."),
    ("II.5", ANIM, "bench_empty", 0, "La clé a disparu."),
    ("V.1", ANIM, "V1_banc", 0, None),
    ("V.3", ANIM, "V3_manteau_clean", 12, "Le manteau revient."),
    ("V.4", EDIT, "V4_cle_E2", 0, "La clé était dans le pli."),
    ("end", None, None, 0, None),
]


def baseline_film():
    from kit import Ink  # noqa: F401
    from PIL import ImageDraw, ImageFont
    cb = ImageFont.truetype("/home/user/bolas/paeleo/scion/oulipo/films/sources/la-belle-hortense/editor/type/HortenseSlab-Bold.ttf", 26)
    cs = ImageFont.truetype("/home/user/bolas/paeleo/scion/oulipo/films/sources/la-belle-hortense/editor/type/HortenseSlab-Bold.ttf", 18)
    durs = [2.0] + [1.5] * 7 + [3.0]
    starts = np.cumsum([0] + durs[:-1])
    total = float(sum(durs))
    bf = Film(SLUG + "-baseline", seconds=total)

    def pic(t, ink):
        ink._grain = False
        j = int(np.searchsorted(starts, t, side="right") - 1)
        label, d, name, first, cap = BASE[j]
        if d is None:
            img = Image.new("RGB", (W, H), (232, 228, 196))
            dr = ImageDraw.Draw(img)
            if label == "card":
                dr.text((60, 190), "CONTRE-ÉPREUVE · ordre du récit", font=cb, fill=INKC)
                dr.text((60, 236), "baseline: story order, no permutation; no coat in I", font=cs, fill=(165, 9, 23))
                dr.text((60, 266), "the key is laid on the bare bench; the coat is first seen in II", font=cs, fill=INKC)
            else:
                dr.text((60, 190), "verify.py: baseline.json REJECTED (14 checks)", font=cb, fill=(165, 9, 23))
                dr.text((60, 236), "the only supports of S are the reveal itself (42.0, 43.5 s);", font=cs, fill=INKC)
                dr.text((60, 266), "nothing before 39 s points back to the coat.", font=cs, fill=INKC)
            ink.img.paste(img)
            return
        k = int(round((t - starts[j]) * FPS))
        fr = clip_frames(d, name)
        img = Image.fromarray(fr[min(first + k, len(fr) - 1)])
        dr = ImageDraw.Draw(img)
        dr.text((40, 446), f"baseline {label}", font=cs, fill=INKC)
        if cap:
            tw = dr.textlength(cap, font=cb)
            dr.rectangle((34, 474, 46 + tw, 510), fill=INKC)
            dr.text((40, 478), cap, font=cb, fill=CREAM)
        ink.img.paste(img)

    def snd(mix):
        # the same recordings, re-timed to the baseline: clicks at cut starts, the V.3 steps and key tinks
        cues = [c for c in CUES["cues"] if c.get("slot") in ("V.3", "V.4")]
        off = 42.0 - starts[6]
        lay_sound(mix, cues, off)
        click = [c for c in CUES["cues"] if c["file"].endswith("click.wav")][0]
        for s in starts[1:]:
            mix.add(read_wav(PROJECT / click["file"]), float(s), gain=click["gain"])

    bf.picture(pic)
    bf.sound(snd)
    bf.poster_at = starts[6] + 1.3
    return bf


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--baseline":
        sys.argv = sys.argv[:1]
        baseline_film().render(out_dir=SW)
    else:
        film.render()
