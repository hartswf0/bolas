"""Récits d'Ellis Island · traces and testimony (SCION, plan-r1).

A real montage of foraged and handmade material, assembled by the rule of the
Hard proof (two 25-second movements):

  Prologue    0.0-3.0   handmade title card (silence, then field air)
  Movement I  3.0-28.0  what the site shows: Commons photographs of the disused
                        halt at Bourré (T1, T2), the 1904 PO network map (T6).
                        Source cards only. No voices, no quotation marks.
  Card       28.0-30.0  handmade card, declared silence
  Movement II 30.0-55.0 two fictional, labelled witnesses (handmade testimony
                        records + captions) over the SAME T1 crop and tag. The
                        same foraged bell (S1) and keys (S2) are placed in
                        opposite orders under A and under B. Handmade ledger.
  Coda       55.0-60.0  handmade credits/ledger card, silence

Inputs (read, never edited here): films/swarm/recits-dellis-island/
traces.json, sounds.json, testimony.json, claims.json, captions.srt, and media in
films/sources/recits-dellis-island/{location-archive,sound,testimony}/.
Foraged images are pasted as decoded pixels with no filter, grain or vignette.
Foraged sounds are decoded with ffmpeg and placed with mix.add. Nothing is
synthesised.

Run from the project root:
  python3 films/recits-dellis-island.py                 public cut -> assets/films/
  python3 films/recits-dellis-island.py --stills 5 20   stills -> films/stills/<slug>/
  python3 films/recits-dellis-island.py --baseline      private single-voice baseline
  python3 films/recits-dellis-island.py --order-BA      private branch, B before A
  python3 films/recits-dellis-island.py --check         run the preconditions only
  python3 films/recits-dellis-island.py --check --simulate-missing-consent A
                                                         dry run of the consent gate
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from kit import (Film, Ink, OUT, PROJECT, W, H, FPS, RATE, PAPER, PAGE, INK, MUTED, RULE,
                 ACCENT, WASH, ease, ramp, clamp, lerp, font)

SLUG = "recits-dellis-island"
SWARM = PROJECT / "films" / "swarm" / SLUG
SRC = PROJECT / "films" / "sources" / SLUG
LA = SRC / "location-archive"

# ------------------------------------------------------------ arguments ---
ARGS = sys.argv[1:]
VARIANT = "main"
if "--baseline" in ARGS:
    VARIANT = "baseline"
elif "--order-BA" in ARGS:
    VARIANT = "order-BA"
CHECK_ONLY = "--check" in ARGS
SIMULATE_MISSING = None
if "--simulate-missing-consent" in ARGS:
    SIMULATE_MISSING = ARGS[ARGS.index("--simulate-missing-consent") + 1]
# leave only what kit.Film.render understands (--stills t ...)
sys.argv = [sys.argv[0]] + [a for a in ARGS if a == "--stills" or re.fullmatch(r"[0-9.]+", a)]


def load(name):
    with open(SWARM / name, encoding="utf-8") as f:
        return json.load(f)


TRACES = {r["id"]: r for r in load("traces.json")["traces"]}
SOUNDS = {r["id"]: r for r in load("sounds.json")["items"]}
TESTIMONY = load("testimony.json")
CLAIMS = load("claims.json")
SEGS = {s["seg"]: s for s in TESTIMONY["segments"]}
LINES = {l["id"]: dict(l, seg=s["seg"]) for s in TESTIMONY["segments"] for l in s["lines"]}
if SIMULATE_MISSING:
    SEGS[SIMULATE_MISSING]["consent"]["state"] = "missing"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def proj(p):
    p = Path(p)
    return p if p.is_absolute() else PROJECT / p


# ======================================================= preconditions ===
# 3.2 (1) every Trace and Sound used has a licence in the allowed set.
ALLOWED = re.compile(r"^(Public domain|PD[- ].*|CC0|CC BY( [0-9.]+)?|CC BY-SA( [0-9.]+)?)$")
FORBIDDEN = re.compile(r"NC|ND|fair use|unknown", re.I)
TRACES_USED = ["T1", "T2", "T6", "T7"]
SOUNDS_USED = ["S1", "S2", "S3", "S4"]
for rid in TRACES_USED + SOUNDS_USED:
    rec = TRACES.get(rid) or SOUNDS.get(rid)
    lic = rec["license"]
    assert ALLOWED.match(lic) and not FORBIDDEN.search(lic), f"{rid}: licence {lic!r} not allowed -> quarantine"
    assert rec.get("author") and rec.get("source_url"), f"{rid}: author/source missing"
    if lic.startswith("CC BY"):
        assert rec.get("license_url"), f"{rid}: CC BY(-SA) needs a licence URL"

# I5 evidence records are immutable: every byte we paste or mix matches its record.
MEDIA = {
    "T1_raw": (TRACES["T1"]["local_path"], TRACES["T1"]["sha256"]),
    "T1_platform": (TRACES["T1"]["prepared_media"]["platform_crop_22.5s_32.5s_43.5s"]["path"],
                    TRACES["T1"]["prepared_media"]["platform_crop_22.5s_32.5s_43.5s"]["sha256"]),
    "T2_raw": (TRACES["T2"]["local_path"], TRACES["T2"]["sha256"]),
    "T6_raw": (TRACES["T6"]["local_path"], TRACES["T6"]["sha256"]),
    "T6_sheet": (TRACES["T6"]["prepared_media"]["full_sheet_pillarbox"]["path"],
                 TRACES["T6"]["prepared_media"]["full_sheet_pillarbox"]["sha256"]),
}
for sid in SOUNDS_USED:
    MEDIA[sid] = (SOUNDS[sid]["local_path"], SOUNDS[sid]["sha256"])
for lid in ("A1", "B1"):
    MEDIA["sheet_" + lid] = (LINES[lid]["sheet_png"], LINES[lid]["sheet_sha256"])
for key, (p, digest) in MEDIA.items():
    assert sha256(proj(p)) == digest, f"{key}: bytes differ from the evidence record -> quarantine"
_t7 = TRACES["T7"]["prepared_media"]["excerpt_frames"]
T7_FRAMES = [proj(_t7["dir"]) / (_t7["pattern"] % k) for k in range(_t7["count"])]
assert sha256(T7_FRAMES[0]) == _t7["first_sha256"] and sha256(T7_FRAMES[-1]) == _t7["last_sha256"], "T7 excerpt changed"

# 3.2 (3) consent gates the public export.
CONSENT_OK = {"authored-fiction", "granted"}
for s in SEGS.values():
    assert s["consent"]["state"] in CONSENT_OK | {"missing"}, f"seg {s['seg']}: unknown consent state"
    assert s["consent"].get("use_scope"), f"seg {s['seg']}: no use scope"
PUBLIC_OK = all(SEGS[k]["consent"]["state"] in CONSENT_OK for k in ("A", "B"))

# ============================================================ captions ===

def parse_srt(path):
    cues = []
    for block in path.read_text(encoding="utf-8").strip().split("\n\n"):
        rows = block.strip().split("\n")
        a, b = rows[1].split(" --> ")
        tc = lambda s: (lambda h, m, rest: int(h) * 3600 + int(m) * 60 + float(rest.replace(",", ".")))(*s.split(":"))
        cues.append((tc(a), tc(b), rows[2], rows[3]))
    return cues


SRT = parse_srt(SWARM / "captions.srt")

# ======================================================== evidence tags ===
TAG = {
    "T1_wide": ("T1 · goods shed and empty loading platform, disused halt · photo D. Jolivet · CC BY 2.0 · Commons",
                "photographed 23 Jan 2021, 13:58 (EXIF, measured) · place stated by uploader, title and GPS"),
    "T2": ("T2 · a closed door · photo D. Jolivet · 23 Jan 2021, 13:59 (EXIF, measured) · CC BY 2.0 · Commons",
           "shows the door shut that day, nothing more"),
    "T6": ("T6 · Carte du réseau des chemins de fer de la Cie d'Orléans · printed Mars 1904 (read on the sheet)",
           "names Bourré on the Tours-Vierzon line · does not show the halt · BnF via Commons · public domain"),
    "T1_platform": ("T1 · empty platform edge · photo D. Jolivet · 23 Jan 2021, 13:58 (EXIF, measured) · CC BY 2.0",
                    "shows this platform on that day · no bench, no bell, no key visible"),
    "T7": ("T7 · Vincennes, 1896 · another station, another century · illustrates, does not prove",
           "film by G. Méliès · public domain · Commons · silent (declared: no projector sound added)"),
    "sheetA": ("H · testimony record A · typeset for this film (handmade) · authored fiction",
               "heard: silence (declared · no room recording used)"),
    "sheetB": ("H · testimony record B · typeset for this film (handmade) · authored fiction",
               "heard: silence (declared · no room recording used)"),
}
HEARD = {
    "S3": "heard · S3 field air, Folkingham (Lincolnshire, UK), 18 Sep 2020 · recorded elsewhere · R. E. A. Harvey · CC BY-SA 4.0",
    "S4": "heard · S4 distant train, line 170, Czech Republic, 1 Sep 2013 · recorded elsewhere · Juandev · CC BY-SA 3.0",
    "beat": "heard · S1 station bell, Fridingen (DE) 2019 · S2 keys against wood · both recorded elsewhere, same files under A and B",
}

# =============================================================== timeline ===
PROLOGUE, M1_START, M1_END, M2_START, M2_END, END = 3.0, 3.0, 28.0, 30.0, 55.0, 60.0


def movement_one():
    return [
        dict(a=3.0, b=4.5, kind="card1", trace=None, testimony=None),
        dict(a=4.5, b=11.0, kind="T1_wide", trace="T1", testimony=None, tag=TAG["T1_wide"], heard="S3"),
        dict(a=11.0, b=16.0, kind="T2", trace="T2", testimony=None, tag=TAG["T2"], heard="S3"),
        dict(a=16.0, b=22.5, kind="T6", trace="T6", testimony=None, tag=TAG["T6"], heard="S3"),
        dict(a=22.5, b=28.0, kind="T1_platform", trace="T1", testimony=None, tag=TAG["T1_platform"], heard="S3"),
    ]


def block_A(t0):
    """Account A: sheet (A1), Beat A over T1 (A2, A3), T7 insert (A4). 11.0 s."""
    shots = [
        dict(a=t0, b=t0 + 2.5, kind="sheet", seg="A", trace=None, tag=TAG["sheetA"], caps=[("A1", t0, t0 + 2.5)]),
        dict(a=t0 + 2.5, b=t0 + 8.5, kind="T1_platform", seg="A", trace="T1", tag=TAG["T1_platform"], heard="beat",
             caps=[("A2", t0 + 2.5, t0 + 6.0), ("A3", t0 + 6.0, t0 + 8.5)]),
        dict(a=t0 + 8.5, b=t0 + 11.0, kind="T7", seg="A", trace="T7", tag=TAG["T7"], caps=[("A4", t0 + 8.5, t0 + 11.0)]),
    ]
    events = [("S1", t0 + 3.6, 0.0), ("S2", t0 + 5.4, 0.0)]   # bell, then key
    return shots, events, t0 + 11.0


def block_B(t0):
    """Account B: sheet (B1), Beat B over the same T1 crop (B2, B3, B4). 8.5 s."""
    shots = [
        dict(a=t0, b=t0 + 2.5, kind="sheet", seg="B", trace=None, tag=TAG["sheetB"], caps=[("B1", t0, t0 + 2.5)]),
        dict(a=t0 + 2.5, b=t0 + 8.5, kind="T1_platform", seg="B", trace="T1", tag=TAG["T1_platform"], heard="beat",
             caps=[("B2", t0 + 2.5, t0 + 5.0), ("B3", t0 + 5.0, t0 + 7.2), ("B4", t0 + 7.2, t0 + 8.5)]),
    ]
    events = [("S2", t0 + 3.6, 0.0), ("S1", t0 + 6.6, 0.0)]   # key, then bell
    return shots, events, t0 + 8.5


def movement_two(order):
    t, shots, events = M2_START, [], []
    for blk in (block_A, block_B) if order == "AB" else (block_B, block_A):
        s, e, t = blk(t)
        shots += s
        events += e
    assert abs(t - 49.5) < 1e-9
    shots.append(dict(a=49.5, b=55.0, kind="ledger", trace=None, testimony=None, caps=[]))
    # ledger replays: A's order panned left, then B's order panned right (same in both orders)
    events += [("S1", 49.9, -0.7), ("S2", 50.6, -0.7), ("S2", 51.6, 0.7), ("S1", 52.4, 0.7)]
    for sh in shots:
        sh.setdefault("caps", [])
        sh["testimony"] = [c[0] for c in sh["caps"]] or None
    return shots, events


ORDER = "BA" if VARIANT == "order-BA" else "AB"
M1 = movement_one()
M2, EVENTS = movement_two(ORDER)
CAPS = [(lid, a, b) for sh in M2 for (lid, a, b) in sh["caps"]]
PROJECTED_CLAIMS = ["C1", "C2", "C3", "C4"]       # what the ledger card puts on screen

# 3.2 (6) the two movements each last 25.0 s.
assert abs((M1_END - M1_START) - 25.0) < 1e-9 and abs((M2_END - M2_START) - 25.0) < 1e-9
assert abs(sum(s["b"] - s["a"] for s in M1) - 25.0) < 1e-9, "Movement I shots do not sum to 25.0 s"
assert abs(sum(s["b"] - s["a"] for s in M2) - 25.0) < 1e-9, "Movement II shots do not sum to 25.0 s"
for seq in (M1, M2):
    for p, q in zip(seq, seq[1:]):
        assert abs(p["b"] - q["a"]) < 1e-9, "gap or overlap in the shot list"

# 3.2 (2) Movement I uses no Testimony; its captions are source cards, never quotations.
QUOTES = re.compile(r"[\"«»“”„]")
for sh in M1:
    assert not sh.get("testimony") and not sh.get("caps"), "testimony in Movement I"
    for line in sh.get("tag", ()):
        assert not QUOTES.search(line), f"quotation marks in a Movement I source card: {line}"

# 3.2 (4) every Testimony-over-Trace shot shows speaker+interval AND trace id+depiction scope.
for sh in M2:
    if sh.get("testimony") and sh.get("trace"):
        tag = " ".join(sh["tag"])
        assert tag.startswith(sh["trace"] + " · "), f"{sh['kind']}: trace id not on screen"
        assert re.search(r"shows|illustrates|does not", tag), f"{sh['kind']}: depiction scope missing"
        for lid in sh["testimony"]:
            seg = SEGS[LINES[lid]["seg"]]
            lab = LINES[lid]["caption_label"]
            assert lab.startswith(f"{seg['seg']} · {seg['speaker']['name'].upper()}"), f"{lid}: speaker label"
            assert "fictional witness · staged" in lab and f"seg {seg['seg']} " in lab, f"{lid}: interval/staged label"

# I1/I2/7 every caption: speaker, interval, staged label, transcript revision, consent; I8: halt never named.
for lid, a, b in CAPS:
    line, seg = LINES[lid], SEGS[LINES[lid]["seg"]]
    assert line["caption_label"].endswith(f"{line['interval']['in_tc']}–{line['interval']['out_tc']}")
    assert line["transcript_status"]["revision"] == seg["transcript_status"]["revision"], f"{lid}: stale caption revision"
    assert seg["consent"]["state"] != "missing" or not PUBLIC_OK
    assert "Bourr" not in line["en"] and "Bourr" not in line["fr"], f"{lid}: the real halt is named in an account"
    assert lid.startswith(seg["seg"]), f"{lid}: one speaker's words under the other's label"
# the public cut follows captions.srt exactly (label + text + film time)
if ORDER == "AB":
    assert len(SRT) == len(CAPS)
    for (lid, a, b), (sa, sb, slab, stext) in zip(CAPS, SRT):
        assert abs(a - sa) < 1e-6 and abs(b - sb) < 1e-6, f"{lid}: caption time differs from captions.srt"
        assert slab == LINES[lid]["caption_label"] and stext == LINES[lid]["en"], f"{lid}: caption text differs"

# 3.2 (5) no 'image proves memory' claim is projected without a Match record.
MATCHES = CLAIMS.get("matches", [])
for c in CLAIMS["claims"]:
    proves = re.search(r"image proves|proves .*memory", c["text"], re.I)
    if c["id"] in PROJECTED_CLAIMS:
        assert not proves or MATCHES, f"{c['id']}: image-proves-memory claim projected without a Match"
    if proves:
        assert c.get("project") is False and not MATCHES, f"{c['id']}: must stay blocked"

# 3.2 (6) disputed evidence is kept: C3's cited intervals are all in the cut.
c3 = next(c for c in CLAIMS["claims"] if c["id"] == "C3")
cut_lines = {lid for lid, _, _ in CAPS}
for ev in c3["evidence"]:
    if ev["type"] == "Testimony":
        assert ev["ref"].split(":")[1] in cut_lines, f"C3 evidence {ev['ref']} dropped from the cut"
    else:
        assert ev["ref"] in TRACES_USED

# S1/S2 order under each account (3.3: measurable on the waveform).
def _order(seg):
    blk = [sh for sh in M2 if sh.get("seg") == seg and sh["kind"] == "T1_platform"][0]
    ev = sorted((t, s) for s, t, p in EVENTS if blk["a"] <= t < blk["b"])
    return [s for _, s in ev]


assert _order("A") == ["S1", "S2"] and _order("B") == ["S2", "S1"]

# the public export goes to assets/films only when consent allows it; else private only.
if VARIANT == "main" and PUBLIC_OK:
    OUT_DIR = OUT
else:
    OUT_DIR = SWARM if VARIANT != "main" else SWARM / "private"
assert PUBLIC_OK or OUT_DIR != OUT, "consent missing: public export refused"

if CHECK_ONLY:
    print("preconditions OK" if PUBLIC_OK else "preconditions OK except consent: PUBLIC EXPORT BLOCKED")
    print("variant", VARIANT, "order", ORDER, "->", OUT_DIR)
    sys.exit(0)

# ================================================================ media ===

def rgb(p):
    im = Image.open(proj(p))
    im.load()
    return im.convert("RGB")


IMG_T1 = rgb(MEDIA["T1_raw"][0])
IMG_T1P = rgb(MEDIA["T1_platform"][0])
IMG_T2 = rgb(MEDIA["T2_raw"][0])
IMG_T6_SHEET = rgb(MEDIA["T6_sheet"][0])
SHEETS = {k: rgb(MEDIA["sheet_" + k][0]) for k in ("A1", "B1")}
_t6 = rgb(MEDIA["T6_raw"][0])
T6_PAD = 1510   # black margin so a 16:9 window can frame the whole (square) sheet
IMG_T6 = Image.new("RGB", (_t6.width + 2 * T6_PAD, _t6.height), (0, 0, 0))
IMG_T6.paste(_t6, (T6_PAD, 0))
del _t6
_T7_CACHE = {}


def t7_frame(k):
    k = max(0, min(len(T7_FRAMES) - 1, k))
    if k not in _T7_CACHE:
        _T7_CACHE[k] = rgb(T7_FRAMES[k])
    return _T7_CACHE[k]


def window(img, box):
    """Sub-pixel crop of a foraged image to 960x540: a reframe, no filter."""
    return img.resize((W, H), Image.BICUBIC, box=tuple(box), reducing_gap=3.0)


def lerp_box(p, q, x):
    return [lerp(a, b, x) for a, b in zip(p, q)]


def decode(path):
    """ffmpeg -> mono float signal at 44.1 kHz (the WAVs are duplicated-mono stereo)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(proj(path)), "-f", "s16le", "-ac", "1",
                          "-ar", str(RATE), "-"], check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float64) / 32768.0


# ========================================================== drawing kit ===
COL = {k: tuple(SEGS[k]["colour_rgb"]) for k in ("A", "B")}


def fit(ink, s, kind, size, maxw):
    while size > 9 and ink.text_size(s, kind, size)[0] > maxw:
        size -= 1
    return size


def top_tag(ink, lines, alpha=1.0):
    if alpha <= 0:
        return
    h = 12 + 19 * len(lines)
    ink.d.rectangle([0, 0, W, h], fill=PAGE + (int(232 * alpha),))
    ink.d.line([(0, h), (W, h)], fill=RULE + (int(255 * alpha),), width=1)
    for k, s in enumerate(lines):
        sz = fit(ink, s, "mono", 13, W - 32)
        ink.label((16, 8 + 19 * k), s, sz, INK if k == 0 else MUTED, alpha=int(255 * alpha))


def bottom_heard(ink, s, alpha=1.0):
    if alpha <= 0:
        return
    sz = fit(ink, s, "mono", 12, W - 32)
    ink.d.rectangle([0, H - 26, W, H], fill=PAGE + (int(220 * alpha),))
    ink.label((16, H - 20), s, sz, MUTED, alpha=int(255 * alpha))


def testimony_caption(ink, lid, alpha=1.0, labels=True):
    line = LINES[lid]
    col = COL[line["seg"]]
    text = line["en"]
    tsz = fit(ink, text, "serif", 25, W - 40)
    if labels:
        ink.d.rectangle([0, H - 82, W, H], fill=PAGE + (int(238 * alpha),))
        ink.d.rectangle([0, H - 82, 6, H], fill=col + (int(255 * alpha),))
        lab = line["caption_label"]
        ink.label((20, H - 74), lab, fit(ink, lab, "mono", 13, W - 150), col, alpha=int(255 * alpha))
        rev = f"EN tr. of FR · rev {line['transcript_status']['revision']}"
        ink.label((W - 16, H - 74), rev, 11, MUTED, alpha=int(255 * alpha), anchor="ra")
        ink.text((20, H - 47), text, "serif", tsz, INK, alpha=int(255 * alpha))
    else:   # baseline: words only, no speaker, no interval
        ink.caption(text, alpha, size=tsz)


def plain(ink, color=PAPER):
    ink.paper(color, grain=False)   # no faux grain anywhere


# ================================================================ cards ===

def draw_prologue(t, ink):
    plain(ink)
    a = ease(t, 0.0, 0.4) * (1 - ease(t, 2.75, 3.0))
    ink.text((W / 2, 196), "Récits d'Ellis Island", "serif", 56, INK, anchor="mm", alpha=int(255 * a))
    ink.text((W / 2, 246), "traces and testimony", "serif", 30, MUTED, anchor="mm", alpha=int(255 * a))
    l1 = "The witnesses and the last train are invented."
    l2 = "The photographs show a real disused halt, Bourré (Loir-et-Cher), standing in."
    ink.text((W / 2, 318), l1, "mono", 15, INK, anchor="mm", alpha=int(255 * a))
    ink.text((W / 2, 342), l2, "mono", 15, INK, anchor="mm", alpha=int(255 * a))
    ink.text((W / 2, 404), "after Bober and Perec, 1980 · nothing from that film is used", "mono", 12, MUTED,
             anchor="mm", alpha=int(255 * a))


def draw_card1(t, ink, sh):
    plain(ink)
    a = ease(t, sh["a"], sh["a"] + 0.25) * (1 - ease(t, sh["b"] - 0.2, sh["b"]))
    ink.text((W / 2, 250), "I · What the site shows", "serif", 50, INK, anchor="mm", alpha=int(255 * a))
    ink.text((W / 2, 302), "no voices · source cards only · every image carries its evidence ID", "mono", 15, MUTED,
             anchor="mm", alpha=int(255 * a))


def draw_card2(t, ink):
    plain(ink)
    a = ease(t, 28.05, 28.35) * (1 - ease(t, 29.8, 30.0))
    ink.text((W / 2, 236), "II · The last train, twice", "serif", 50, INK, anchor="mm", alpha=int(255 * a))
    ink.text((W / 2, 290), "two fictional witnesses · staged testimony", "mono", 16, INK, anchor="mm", alpha=int(255 * a))
    ink.text((W / 2, 318), "voices are captions · silence declared", "mono", 14, MUTED, anchor="mm", alpha=int(255 * a))


def chip(ink, x, y, s, col, lit):
    w = ink.text_size(s, "mono", 18)[0] + 28
    ink.d.rounded_rectangle([x, y, x + w, y + 36], 6, fill=(col + (255,)) if lit else PAGE + (255,),
                            outline=col + (255,), width=2)
    ink.label((x + w / 2, y + 18), s, 18, PAGE if lit else col, anchor="mm")
    return x + w


def draw_ledger(t, ink, sh):
    plain(ink)
    a0 = sh["a"]
    ink.label((40, 26), "LEDGER · claim graph (claims.json, plan-r1) · handmade", 13, MUTED)
    ink.text((40, 48), "Two accounts, one detail", "serif", 34, INK)
    lit = lambda at: at - 0.05 <= t < at + 0.55
    for side, x0, seg, order, times, ref, cid in (
            ("A", 40, SEGS["A"], ("bell", "key"), (49.9, 50.6), "seg A 00:18.0–00:22.5", "C1"),
            ("B", 500, SEGS["B"], ("key", "bell"), (51.6, 52.4), "seg B 01:04.5–01:10.5", "C2")):
        col = COL[side]
        ink.d.rectangle([x0, 108, x0 + 420, 250], fill=WASH + (255,))
        ink.d.rectangle([x0, 108, x0 + 6, 250], fill=col + (255,))
        ink.label((x0 + 20, 120), f"{side} · {seg['speaker']['name'].upper()} — fictional witness · staged", 13, col)
        ink.label((x0 + 20, 140), f"{ref} · {cid}: recalls {order[0]}, then {order[1]}", 12, MUTED)
        x = chip(ink, x0 + 20, 172, order[0], col, lit(times[0]))
        ink.d.line([(x + 8, 190), (x + 32, 190)], fill=INK + (255,), width=2)
        ink.d.polygon([(x + 33, 190), (x + 25, 185), (x + 25, 195)], fill=INK + (255,))
        chip(ink, x + 40, 172, order[1], col, lit(times[1]))
        ink.label((x0 + 20, 226), f"heard: S1/S2 replayed in {side}'s order, panned {'left' if side == 'A' else 'right'}",
                  11, MUTED)
    ink.d.line([(40, 276), (W - 40, 276)], fill=RULE + (255,), width=1)
    ink.label((40, 290), "AGREED BY BOTH (A1 A2 A3 · B1 B2 B4)", 12, MUTED)
    ink.text((40, 310), "a sealed envelope · the brass key left on the bench · the service door shut",
             "serif", 25, INK)
    ink.label((40, 350), "C4 · a door shut on 23 Jan 2021 (T2) supports that photographed day only, not the night in the accounts",
              11, MUTED)
    ua = ease(t, a0 + 0.3, a0 + 0.9)
    ink.d.rectangle([40, 376, W - 40, 512], outline=ACCENT + (int(255 * ua),), width=3)
    ink.text((60, 392), "UNRESOLVED · C3 · did the bell ring before or after the key?", "serif", 27, ACCENT,
             alpha=int(255 * ua))
    ink.label((60, 436), "A says bell, then key; B says key, then bell. Both segments stay in the ledger and in the cut.", 13, INK,
              alpha=int(255 * ua))
    ink.label((60, 458), "T1 shows a platform on 23 Jan 2021 and supports neither order (leaves open).", 13, INK,
              alpha=int(255 * ua))
    ink.label((60, 478), "No image-to-memory match on file.", 13, INK, alpha=int(255 * ua))
    fade = ease(t, sh["b"] - 0.4, sh["b"])
    if fade > 0:
        ink.d.rectangle([0, 0, W, H], fill=PAPER + (int(255 * fade),))


CREDIT_ROWS = [
    ("T1 T2", "Bourré (Loir-et-Cher) (50866798791), (50866795131) · Daniel Jolivet · CC BY 2.0 · Wikimedia Commons"),
    ("T6", "Carte du réseau des chemins de fer de la Cie d'Orléans, Mars 1904 · Cie P.-O. · BnF/Gallica · public domain · Commons"),
    ("T7", "Arrivée d'un train gare de Vincennes (1896) · Georges Méliès · public domain · Commons (excerpt, silent)"),
    ("S1", "Glockenschlagwerk Bahnhof Fridingen · Olga Ernst · CC BY-SA 4.0 · Commons"),
    ("S2", "Keys hitting tree 2 · Gravity Sound · CC BY 4.0 · Commons (keys against wood, not a key on a bench)"),
    ("S3", "Folkingham 2020-09-18 1149 · Robert EA Harvey · CC BY-SA 4.0 · Commons"),
    ("S4", "Zeleznicni trat 170, projizdejici vlak ... (Czech title; the font lacks its accents) · Juandev · CC BY-SA 3.0 · audio only"),
    ("A B", "testimony A/B: authored fiction (SCION U3), consent recorded, public use · FR original, EN captions rev 1"),
    ("H", "handmade: title cards, testimony record sheets, ledger, this card · fonts Instrument Sans/Serif, IBM Plex Mono (OFL)"),
]


def draw_coda(t, ink):
    plain(ink)
    a = ease(t, 55.0, 55.35) * (1 - ease(t, 59.6, 60.0))
    ink.text((40, 40), "Sources and permissions", "serif", 32, INK, alpha=int(255 * a))
    ink.label((40, 84), "every evidence ID on screen · licences read from Commons extmetadata, 15 Nov 2026", 12, MUTED,
              alpha=int(255 * a))
    y = 118
    for k, (eid, s) in enumerate(CREDIT_ROWS):
        ink.label((40, y), eid, 13, ACCENT, alpha=int(255 * a))
        ink.label((110, y), s, fit(ink, s, "mono", 13, W - 150), INK, alpha=int(255 * a))
        y += 34
    note = ("branch order-BA (B before A) rendered privately and recorded in assembly.md"
            if ORDER == "AB" else "THIS IS BRANCH order-BA (B before A) · private · the published cut plays A first")
    ink.label((40, y + 8), note, 12, MUTED, alpha=int(255 * a))
    ink.label((40, y + 30), "silence", 12, MUTED, alpha=int(255 * a))


# ================================================================ shots ===
T1_WIDE = ([0, 144, 1805, 1159], [115, 144, 1920, 1159])        # 6 % lateral reframe (traces.json)
T2_PUSH = ([0, 202, 1920, 1282], [0, 288, 1690, 1238])           # slight push-in (traces.json)
_K = TRACES["T6"]["prepared_media"]["key_regions_raw_px"]


def _centre_box(cx, cy, w):
    h = w * 9 / 16
    return [cx - w / 2 + T6_PAD, cy - h / 2, cx + w / 2 + T6_PAD, cy + h / 2]


T6_FULL = [0, 0, IMG_T6.width, IMG_T6.height]
_d = _K["printed_date_Mars_1904"]
_b = _K["label_Bourre_approx"]
T6_DATE = _centre_box((_d[0] + _d[2]) / 2, (_d[1] + _d[3]) / 2, 720)
T6_BOURRE = _centre_box((_b[0] + _b[2]) / 2 - 40, (_b[1] + _b[3]) / 2, 720)


def t6_box(t):
    if t < 17.2:
        return T6_FULL
    if t < 19.0:
        x = ease(t, 17.2, 19.0)
        # zoom on a log scale so the push feels constant
        w0, w1 = T6_FULL[2] - T6_FULL[0], T6_DATE[2] - T6_DATE[0]
        w = w0 * (w1 / w0) ** x
        cx = lerp((T6_FULL[0] + T6_FULL[2]) / 2, (T6_DATE[0] + T6_DATE[2]) / 2, ease(x, 0, 1) ** 0.6)
        cy = lerp((T6_FULL[1] + T6_FULL[3]) / 2, (T6_DATE[1] + T6_DATE[3]) / 2, ease(x, 0, 1) ** 0.6)
        return [cx - w / 2, cy - w * 9 / 32, cx + w / 2, cy + w * 9 / 32]
    if t < 19.9:
        return T6_DATE
    if t < 21.1:
        x = ease(t, 19.9, 21.1)
        box = lerp_box(T6_DATE, T6_BOURRE, x)
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        w = (box[2] - box[0]) * (1 + 2.2 * np.sin(np.pi * x))   # travel out and back in across the sheet
        return [cx - w / 2, cy - w * 9 / 32, cx + w / 2, cy + w * 9 / 32]
    return T6_BOURRE


def raw_to_screen(box, rect):
    sx = W / (box[2] - box[0])
    sy = H / (box[3] - box[1])
    return [(rect[0] + T6_PAD - box[0]) * sx, (rect[1] - box[1]) * sy,
            (rect[2] + T6_PAD - box[0]) * sx, (rect[3] - box[1]) * sy]


def draw_t6(t, ink, sh):
    if t < 17.2:
        ink.paste(IMG_T6_SHEET)          # U1's full-sheet pillarbox (identical framing to T6_FULL)
    else:
        box = t6_box(t)
        box = [max(0, box[0]), max(0, box[1]), min(IMG_T6.width, box[2]), min(IMG_T6.height, box[3])]
        ink.paste(window(IMG_T6, box))
        for rect, at0, at1, label in ((_d, 18.9, 19.95, "printed date"), (_b, 21.0, 22.5, "place name")):
            al = ease(t, at0, at0 + 0.25) * (1 - ease(t, at1 - 0.1, at1))
            if al > 0:
                r = raw_to_screen(box, rect)
                ink.d.rectangle([r[0] - 10, r[1] - 8, r[2] + 10, r[3] + 8], outline=ACCENT + (int(230 * al),), width=3)
                ink.label((r[0] - 10, r[3] + 14), label + " (marker added)", 12, ACCENT, alpha=int(255 * al))


def draw_shot(t, ink, sh, labels=True):
    k = sh["kind"]
    if k == "T1_wide":
        ink.paste(window(IMG_T1, lerp_box(*T1_WIDE, ramp(t, sh["a"], sh["b"]))))
    elif k == "T2":
        ink.paste(window(IMG_T2, lerp_box(*T2_PUSH, ease(t, sh["a"], sh["b"]))))
    elif k == "T6":
        draw_t6(t, ink, sh)
    elif k == "T1_platform":
        ink.paste(IMG_T1P)              # the one exact crop, unchanged, every time
    elif k == "T7":
        ink.paste(t7_frame(int(round((t - sh["a"]) * FPS))))
    elif k == "sheet":
        plain(ink, WASH)
        sheet = SHEETS[sh["caps"][0][0]]
        s = sheet.resize((768, 432), Image.LANCZOS)
        ink.paste(s, ((W - 768) / 2, 48))
    if labels and sh.get("tag"):
        if k == "sheet":
            top_tag(ink, [sh["tag"][0] + " · " + sh["tag"][1]])
        elif sh.get("caps") and sh.get("heard"):
            top_tag(ink, list(sh["tag"]) + [HEARD[sh["heard"]]])
        else:
            top_tag(ink, sh["tag"])
    if labels and sh.get("heard"):
        if not sh.get("caps"):
            s = HEARD["S4"] if (k == "T2" and 12.4 <= t < 16.0) else HEARD[sh["heard"]]
            bottom_heard(ink, s)
    for lid, a, b in sh.get("caps", []):
        if a <= t < b:
            al = ease(t, a, a + 0.12) * (1 - ease(t, b - 0.08, b)) if labels else 1.0
            testimony_caption(ink, lid, max(al, 0.0001) if labels else 1.0, labels)


def frame(t, ink):
    plain(ink)
    if t < PROLOGUE:
        return draw_prologue(t, ink)
    if 28.0 <= t < 30.0:
        return draw_card2(t, ink)
    if t >= 55.0:
        return draw_coda(t, ink)
    for sh in M1 + M2:
        if sh["a"] <= t < sh["b"]:
            if sh["kind"] == "card1":
                return draw_card1(t, ink, sh)
            if sh["kind"] == "ledger":
                return draw_ledger(t, ink, sh)
            draw_shot(t, ink, sh)
            if sh["kind"] == "T1_platform" and sh["b"] == 28.0:     # fade to the card
                f = ease(t, 27.4, 28.0)
                if f > 0:
                    ink.d.rectangle([0, 0, W, H], fill=PAPER + (int(255 * f),))
            return


# ================================================================ sound ===
SIG = {}


def sig(sid):
    if sid not in SIG:
        SIG[sid] = decode(SOUNDS[sid]["local_path"])
    return SIG[sid]


def faded(x, fin, fout):
    x = x.copy()
    n_in, n_out = int(fin * RATE), int(fout * RATE)
    if n_in:
        x[:n_in] *= np.linspace(0, 1, n_in)
    if n_out:
        x[-n_out:] *= np.linspace(1, 0, n_out)
    return x


def excerpt(sid, start, dur):
    s = sig(sid)
    return s[int(start * RATE): int((start + dur) * RATE)]


ONSET = {k: SOUNDS[k]["onset_s"] for k in ("S1", "S2")}
G = {"S3": 0.5, "S3_low": 0.13, "S4": 0.05, "S1": 0.75, "S2": 0.95}


def sound(mix):
    # S3 bed under Movement I: in at 2.2 s, thins during T6, out by 28.6 s
    bed = excerpt("S3", 0.0, 28.6 - 2.2)
    tt = 2.2 + np.arange(len(bed)) / RATE
    env = np.ones_like(tt)
    env *= np.clip((tt - 2.2) / 0.8, 0, 1)
    thin = np.interp(tt, [15.6, 16.6, 22.0, 22.8], [1.0, 0.55, 0.55, 0.85])
    env *= thin
    env *= np.clip((28.6 - tt) / 0.6, 0, 1)
    mix.add(bed * env, 2.2, G["S3"])
    # S4 distant train under T2: file 10-15 s (rumble peak ~12.5 s) lands at 11-16 s, peak ~13.5 s
    mix.add(faded(excerpt("S4", 10.0, 5.0), 0.9, 1.0), 11.0, G["S4"])
    # S3 low under both beats: the SAME stretch of the file under A and under B
    for sh in M2:
        if sh["kind"] == "T1_platform":
            mix.add(faded(excerpt("S3", 4.0, sh["b"] - sh["a"]), 0.3, 0.25), sh["a"], G["S3_low"])
    # S1 bell and S2 keys: transient on the shot-list time (file onset subtracted)
    for sid, at, pan in EVENTS:
        mix.add(sig(sid), at - ONSET[sid], G[sid], pan)
    # statement sheets, T7, cards and coda: declared silence


# ============================================================= baseline ===
BASE_SECONDS = 14.0
BASE_CAPS = [("A1", 0.4, 2.5), ("A2", 2.5, 6.0), ("A3", 6.0, 8.5), ("A4", 8.5, 11.0)]
BASE_PUSH = ([0, 0, 960, 540], [90, 50, 870, 489])


def base_frame(t, ink):
    plain(ink)
    if 8.5 <= t < 11.0:
        ink.paste(t7_frame(int(round((t - 8.5) * FPS))))
    else:
        ink.paste(window(IMG_T1P, lerp_box(*BASE_PUSH, ease(t, 0.0, BASE_SECONDS))))
    for lid, a, b in BASE_CAPS:
        if a <= t < b:
            testimony_caption(ink, lid, 1.0, labels=False)
    f = ease(t, BASE_SECONDS - 0.6, BASE_SECONDS)
    if f > 0:
        ink.d.rectangle([0, 0, W, H], fill=(0, 0, 0, int(255 * f)))


def base_sound(mix):
    mix.add(faded(excerpt("S3", 4.0, BASE_SECONDS), 0.5, 0.8), 0.0, 0.3)
    mix.add(sig("S1"), 3.6 - ONSET["S1"], G["S1"])
    mix.add(sig("S2"), 5.4 - ONSET["S2"], G["S2"])


# ================================================================ render ===
if VARIANT == "baseline":
    film = Film("baseline", seconds=BASE_SECONDS, boil=0, wobble=0)
    film.picture(base_frame)
    film.sound(base_sound)
    film.poster_at = 4.0
else:
    film = Film(SLUG if VARIANT == "main" else "order-BA", seconds=END, boil=0, wobble=0)
    film.picture(frame)
    film.sound(sound)
    film.poster_at = 33.0

if __name__ == "__main__":
    if VARIANT != "main" and "--stills" in sys.argv:
        sys.exit("stills are for the public cut only")
    film.render(out_dir=OUT_DIR)
