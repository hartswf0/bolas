"""Page 58 He talks himself through it (voice and language; medium: photo-cutout).

The agent narrates every step aloud in his own balloons, from the memo to the forgetting. Page 01's eight
photo panels (99-ways-template rest layers: Rothstein 1937 agent and office, Rothstein clock, ANRC 1922 key;
HANDMADE memo, cards, hook, tag) with the template balloons left out; in every panel at least one balloon is
tailed to the agent's own mouth (or, where his head has left the frame in P2, to his rising figure).
Two recompositions so that the agent is in every panel: P2 lays P1's own cut-out agent (torso and head,
with their shadows) risen and moved toward the frame's right edge; P6 lays P4's cut-out agent at the window
side (the P6 view is P4's, 40 px on). The four canon lines verbatim; the stranger keeps her two.
Run: python3 -I p58_talks_himself.py [--page-only]
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "kit"))
import pen99  # noqa: E402
from pen99 import penlib, ROOT  # noqa: E402
import build_page01 as b01  # noqa: E402

N, PID, TITLE = 58, "talks-himself-through", "He talks himself through it"
SRC = ROOT / "films/sources/99-ways"
OUT_JPG = ROOT / "assets/pages/99-ways" / f"{N}-{PID}.jpg"
OUT_PNG = SRC / "masters" / f"{N}-{PID}.png"
BEATS = SRC / "beats" / f"{N}"
REST = b01.REST


def layers(key):
    d = REST / key
    return [(r["name"], np.asarray(Image.open(d / r["file"])).astype(np.float32))
            for r in json.load(open(d / "layers.json"))["layers"]]


def over(c, im, dx=0, dy=0):
    h, w = c.shape[:2]
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    im = cv2.warpAffine(im, M, (w, h), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0)) if (dx or dy or im.shape[:2] != (h, w)) else im
    a = im[..., 3:4] / 255
    c[:] = c * (1 - a) + im[..., :3] * a


CLERK = ("clerk.torso.shadow", "clerk.torso", "clerk.head.shadow", "clerk.head")
P2_SHIFT = (250, -100)
P6_SHIFT = (40, 0)


def panel(key, pose=None):
    """recompose a rest panel without balloons/border; P2 and P6 get the agent laid in"""
    L = layers(key)
    c = L[0][1][..., :3].copy()
    for name, im in L[1:]:
        if name.startswith("b_") or name == "border":
            continue
        if key == "P2" and name.startswith("clerk."):
            continue          # P2's own sleeve stub is replaced by the risen P1 agent
        over(c, im)
    head = None
    if key in ("P2", "P6"):
        srcL = dict(layers("P1" if key == "P2" else "P4"))
        dx, dy = (P2_SHIFT if key == "P2" else P6_SHIFT) if pose is None else pose
        for n in CLERK:
            over(c, srcL[n], dx, dy)
        a = srcL["clerk.head"][..., 3]
        ys, xs = np.nonzero(a > 128)
        head = (xs.min() + dx, ys.min() + dy, xs.max() + dx, ys.max() + dy)
    else:
        a = dict(L)["clerk.head"][..., 3]
        ys, xs = np.nonzero(a > 128)
        head = (xs.min(), ys.min(), xs.max(), ys.max())
    return c, head


def mouth(head, fx=0.5, fy=0.80):
    x0, y0, x1, y1 = head
    return (x0 + (x1 - x0) * fx, y0 + (y1 - y0) * fy)


def bal(c, lines, cap, centre, tip, seed):
    return b01.balloon_on(c, lines, cap, tip, centre, seed)


# per panel: (lines, cap, centre (panel px), tail target) — 'M' = the agent's mouth, else an explicit point
# The template panel px are at the 2550 x 3300 working scale (page scaled 0.8627 at the end).
SPEECH = {
    "P1": [(["Four-fifteen, the SERVICE door.", "Key's in the cupboard. Right!"], 36, (370, 110), "M")],
    "P2": [(["Up we get.", "Cupboard, key, door.", "Easy as pie."], 42, (250, 150), "M")],
    "P3": [(["Past the SERVICE door,", "over to the cupboard..."], 40, (330, 150), "M")],
    "P4": [(["Pardon me —", "have you the", "right time?"], 46, (230, 160), (-30, 500)),
           (["Eh? The time?", "Just a moment..."], 36, (250, 850), "M")],
    "P5": [(["Let me look at", "the clock..."], 36, (240, 120), "M"),
           (["Ten past four,", "by the clock."], 52, (300, 600), "M")],
    "P6": [(["Much", "obliged!"], 56, (170, 170), (-30, 330)),
           (["There she goes.", "Now, the cupboard."], 36, (300, 850), "M")],
    "P7": [(["Here's the cupboard.", "Open her up...", "there we are."], 42, (330, 150), "M")],
    "P8": [(["Now I came over", "for... for..."], 36, (260, 120), "M"),
           (["Well, here I am...", "and what for?"], 52, (380, 400), "M")],
}
MOUTH_F = {"P1": (0.55, 0.82), "P2": (0.45, 0.80), "P3": (0.5, 0.82), "P4": (0.42, 0.82), "P5": (0.45, 0.80),
           "P6": (0.42, 0.82), "P7": (0.40, 0.82), "P8": (0.5, 0.82)}
CANON_LINES = {"question": ["Pardon me —", "have you the", "right time?"], "answer": ["Ten past four,", "by the clock."],
               "thanks": ["Much", "obliged!"], "forgetting": ["Well, here I am...", "and what for?"]}


def build(reveal=8, last_bal=None, p2pose=None):
    pg = penlib.sheet(b01.W0, b01.H0)
    rec = {}
    for i, (k, box) in enumerate(b01.PANELS.items()):
        if i >= reveal:
            continue
        x0, y0, x1, y1 = box
        c, head = panel(k, p2pose if k == "P2" else None)
        bl = SPEECH[k] if (i < reveal - 1 or last_bal is None) else SPEECH[k][:last_bal]
        rec[k] = []
        for j, (lines, cap, ctr, tgt) in enumerate(bl):
            tip = mouth(head, *MOUTH_F[k]) if tgt == "M" else tgt
            cc, rr = bal(c, lines, cap, ctr, tip, 5800 + i * 13 + j)
            rec[k].append(dict(lines=lines, speaker="AGENT" if tgt == "M" else "STRANGER", centre=cc,
                               tail_tip=[float(tip[0]), float(tip[1])]))
        pg[y0:y1, x0:x1] = c
    bm = penlib.border_mask((b01.H0, b01.W0), list(b01.PANELS.values())[:reveal], 9, 900)
    penlib.ink_onto(pg, bm)
    img = Image.fromarray(np.clip(np.round(pg), 0, 255).astype(np.uint8)).resize((pen99.PAGE_W, pen99.PAGE_H), Image.LANCZOS)
    a = cv2.GaussianBlur(np.asarray(img).astype(np.float32), (0, 0), 0.5)
    pen99.folio(a, N, TITLE)
    return np.clip(np.round(a), 0, 255).astype(np.uint8), rec


def main():
    for p in (OUT_JPG.parent, OUT_PNG.parent, BEATS):
        p.mkdir(parents=True, exist_ok=True)
    page, rec = build()
    Image.fromarray(page).save(OUT_PNG, compress_level=6)
    Image.fromarray(page).save(OUT_JPG, quality=90)
    print("jpeg", OUT_JPG.stat().st_size)
    json.dump(rec, open(SRC / "p58_rec.json", "w"), indent=1, default=float)
    if "--page-only" in sys.argv:
        return
    for f in BEATS.glob("b*.png"):
        f.unlink()
    # he talks, panel by panel: P1 laid; P2 he rises (two poses) and talks; ...; P8 first the faltering, then the line
    states = [dict(reveal=1), dict(reveal=2, last_bal=0, p2pose=(150, 0)), dict(reveal=2, last_bal=0),
              dict(reveal=2), dict(reveal=5), dict(reveal=7), dict(reveal=8, last_bal=1), dict(reveal=8)]
    for j, s in enumerate(states, 1):
        im = page if s == dict(reveal=8) else build(**s)[0]
        Image.fromarray(im).resize((960, 1242), Image.LANCZOS).save(BEATS / f"b{j:02d}.png")
    print("beats", len(states))


if __name__ == "__main__":
    main()
