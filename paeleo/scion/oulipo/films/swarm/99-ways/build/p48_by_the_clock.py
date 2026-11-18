"""99 ways, page 48 "By the clock" (time and order; medium: photo-cutout).
Page 01's eight photo panels (99-ways-template rest layers: Rothstein 1937 agent and office, ANRC 1922 key; HANDMADE
memo, cards, hook, tag) with the office clock (the Rothstein clock case, its own hands re-set on the arbor) pinned
into EVERY panel, on the wall where that view shows wall, and a HANDMADE red seconds hand added (build/rig45.py).
The panels are exactly ten seconds apart: 4:09:20, 4:09:30 ... 4:10:30; each clock carries a small pinned time slip.
At the answer (P5) the clock reads 4:10:00, ten past four.
Writes assets/pages/99-ways/48-by-the-clock.jpg, films/sources/99-ways/masters/48-by-the-clock.png,
films/sources/99-ways/beats/48/b01..b08.png, films/swarm/99-ways/pages/48.json.  Run: python3 -I p48_by_the_clock.py"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "kit"))
import rig45 as rg  # noqa: E402
import pen99  # noqa: E402
from pen99 import penlib, ROOT  # noqa: E402
import build_page01 as b01  # noqa: E402

bp = rg.bp
CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
C = CANON["constraints"][47]
assert C["id"] == "by-the-clock", C["id"]
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
SRC = ROOT / "films/sources/99-ways"
OUT_JPG = ROOT / "assets/pages/99-ways/48-by-the-clock.jpg"
OUT_PNG = SRC / "masters/48-by-the-clock.png"
BEATS = SRC / "beats/48"
OLD = json.load(open(b01.TPL / "page" / "speech.json"))

T0 = 4 * 3600 + 9 * 60 + 20
STEP = 10
# panel -> clock position (panel px, template 2550 scale), clock scale; event
CLOCKS = {"P1": ((600, 175), 0.50, "E0"), "P2": ((520, 175), 0.50, "E0"), "P3": ((150, 250), 0.52, "E0"),
          "P4": ((112, 640), 0.42, "E1"), "P5": ((845, 200), 0.70, "E2"), "P6": ((122, 640), 0.42, "E3"),
          "P7": ((560, 130), 0.48, "E4"), "P8": ((1090, 455), 0.55, "E5")}


def hms(t):
    return t // 3600, (t // 60) % 60, t % 60


def panel_rest_no_clock(key):
    d = b01.REST / key
    c = None
    used = []
    for r in json.load(open(d / "layers.json"))["layers"]:
        if r["name"].startswith("b_") or r["name"] == "border" or r["name"].startswith("clock."):
            continue
        im = np.asarray(Image.open(d / r["file"])).astype(np.float32)
        if c is None:
            c = im[..., :3].copy()
        else:
            a = im[..., 3:4] / 255
            c = c * (1 - a) + im[..., :3] * a
        used.append(r["name"])
    return c, used


def time_slip(c, at, kk, t, seed):
    """a small cut-paper slip pinned under the clock, the time pencilled in the shared pen hand"""
    h_, m_, s_ = hms(t)
    txt = f"{h_}:{m_:02d}:{s_:02d}"
    cap = 40
    lm = pen99.letter([txt], cap, seed, weight=0.16)
    lh, lw = lm.shape
    cx, cy = at[0], at[1] + 300 * kk + 34
    h, w = c.shape[:2]
    cx = float(np.clip(cx, lw / 2 + 8, w - lw / 2 - 8))
    cy = float(np.clip(cy, 40, h - 40))
    x0, y0 = int(cx - lw / 2), int(cy - lh / 2)
    slip = np.zeros((h, w), np.uint8)
    cv2.fillPoly(slip, [np.int32([(x0 + 14, y0 + 10), (x0 + lw - 12, y0 + 6), (x0 + lw - 10, y0 + lh - 8), (x0 + 12, y0 + lh - 4)])], 255, cv2.LINE_AA)
    penlib.shadow_onto(c, slip, off=4, blur=3, opacity=0.4)
    a = (slip.astype(np.float32) / 255)[..., None]
    c[:] = c * (1 - a) + np.array([250, 248, 240], np.float32) * a
    ink = np.zeros((h + 2 * lh, w + 2 * lw), np.uint8)
    ink[y0 + lh:y0 + 2 * lh, x0 + lw:x0 + 2 * lw] = lm
    ink = ink[lh:lh + h, lw:lw + w].copy()
    penlib.ink_onto(c, ink, np.array([150, 34, 20], np.float32))
    return txt, [cx, cy]


def panel(i, key):
    c, used = panel_rest_no_clock(key)
    P = bp.Panel(key, c)
    at, kk, ev = CLOCKS[key]
    t = T0 + i * STEP
    hh, mm, ss = hms(t)
    centre = rg.clock_on(P, at, kk, hh, mm, ss=ss)
    c = P.c
    txt, slip_at = time_slip(c, at, kk, t, 4800 + i)
    bals = []
    for (pk, oid, lines, cap, spk, e) in b01.BAL:
        if pk != key:
            continue
        o = OLD[key][0]
        ctr, rad = b01.balloon_on(c, lines, cap, o["tail_tip_panel_px"], o["centre_panel_px"], 7300 + i * 11)
        bals.append(dict(event=e, speaker=spk, line=" ".join(lines), centre_panel_px=ctr))
    return c, dict(panel=key, event=ev, time=txt, seconds_hand_deg=ss * 6, minute=mm, clock_centre_panel_px=list(map(float, centre)),
                   clock_scale=kk, layers=used, balloons=bals)


def build(reveal=8):
    pg = penlib.sheet(b01.W0, b01.H0)
    rec = []
    for i, (k, box) in enumerate(b01.PANELS.items()):
        if i >= reveal:
            continue
        x0, y0, x1, y1 = box
        c, r = panel(i, k)
        pg[y0:y1, x0:x1] = c
        rec.append(r)
    bm = penlib.border_mask((b01.H0, b01.W0), list(b01.PANELS.values())[:reveal], 9, 900)
    penlib.ink_onto(pg, bm)
    img = Image.fromarray(np.clip(np.round(pg), 0, 255).astype(np.uint8)).resize((pen99.PAGE_W, pen99.PAGE_H), Image.LANCZOS)
    a = np.asarray(img).astype(np.float32).copy()
    a = cv2.GaussianBlur(a, (0, 0), 0.5)          # a print's softness: keeps the JPEG inside the 1.2 MB target
    pen99.folio(a, 48, C["title"])
    return np.clip(np.round(a), 0, 255).astype(np.uint8), rec


def main():
    for p in (OUT_JPG.parent, OUT_PNG.parent, BEATS):
        p.mkdir(parents=True, exist_ok=True)
    page, rec = build(8)
    Image.fromarray(page).save(OUT_PNG, compress_level=6)
    Image.fromarray(page).save(OUT_JPG, quality=90, dpi=(300, 300))
    size = OUT_JPG.stat().st_size
    if "--page-only" in sys.argv:
        print(size)
        return
    for f in BEATS.glob("b*.png"):
        f.unlink()
    bd = []
    for j in range(1, 9):
        im = page if j == 8 else build(j)[0]
        Image.fromarray(im).resize((960, 1242), Image.LANCZOS).save(BEATS / f"b{j:02d}.png")
        bd.append(f"b{j:02d}: panels P1-P{j}; the newest clock reads {rec[j - 1]['time']}")
    times = [T0 + i * STEP for i in range(8)]
    record = {
        "n": 48, "id": C["id"], "title": C["title"], "rule": C["rule"], "medium": C["medium"], "family": C["family"],
        "canon_revision": CANON["revision"], "declares": C["declares"],
        "file": str(OUT_JPG.relative_to(ROOT)), "master": str(OUT_PNG.relative_to(ROOT)), "beats_dir": str(BEATS.relative_to(ROOT)),
        "build": "films/swarm/99-ways/build/p48_by_the_clock.py (rig: build/rig45.py; panels: kit/build_page01.py)",
        "sources": ["99-ways-template:rothstein-randolph-agent-1937", "99-ways-template:rothstein-tavern-clock-1937",
                    "99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
        "made": [
            "page 01's eight panels recomposed from films/swarm/99-ways-template/page/rest/P1..P8 (P5's own clock layers left out and re-laid), c1 balloons as on page 01",
            "the Rothstein clock case (FORAGED, 99-ways-template cutout, white scissor margin) pinned into every panel on a stretch of office wall, its own hour and minute hands re-set on the arbor to each panel's time",
            "a HANDMADE seconds hand (inked needle with counterweight, red) on every clock, at 20, 30, 40, 50, 0, 10, 20, 30 s",
            "a HANDMADE cut-paper time slip under each clock, the time pencilled in red in the shared pen hand (4:09:20 ... 4:10:30)",
            "hand-ruled borders; folio '48 / By the clock' (pen99.folio)"],
        "events": {r["panel"]: f"{r['event']} at {r['time']}" + (f" | {r['balloons'][0]['speaker']}: {r['balloons'][0]['line']}" if r["balloons"] else "") for r in rec},
        "lines": LN,
        "panels": rec,
        "beat": "the clock performed: the panels are laid one by one, each ten seconds after the last, the red seconds hand stepping a sixth of the dial per panel, from 4:09:20 to 4:10:30",
        "beat_frames": bd,
        "self_check": {
            "size_px": [page.shape[1], page.shape[0]], "jpeg_bytes": size, "jpeg_quality": 90,
            "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
            "panels_with_clock": sum(1 for r in rec if r["time"]), "panels": len(rec),
            "times": [r["time"] for r in rec],
            "steps_s": [b - a for a, b in zip(times, times[1:])],
            "equal_steps": len({b - a for a, b in zip(times, times[1:])}) == 1,
            "answer_panel_time": [r["time"] for r in rec if r["event"] == "E2"],
            "check": "A reader reads a time in every panel, rising by equal steps (structurally verified from the build; legibility of slips and dials judged by the maker from the full-size page; blind reading pending)",
            "evidence": "structurally verified (times set by code) and perceptually judged (full-size page) by the maker"},
    }
    json.dump(record, open(ROOT / "films/swarm/99-ways/pages/48.json", "w"), indent=1, ensure_ascii=False, default=float)
    print(json.dumps(record["self_check"], indent=1, default=float))


if __name__ == "__main__":
    main()
