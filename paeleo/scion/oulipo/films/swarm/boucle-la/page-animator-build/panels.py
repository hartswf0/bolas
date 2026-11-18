"""boucle-la U3 (page compositor / animator): panel rasters at page scale.

One function draws a panel ID's drawing from a pose: render(ID, pose, balloon=bool, black=bool).
Pieces and FK come from U1's rig (panel-artist/rig.py, cutouts.json; not edited here).
Balloons and note card come from U2's letter.py functions (same text, seed, cap, letterforms;
only the tail tip is recomputed from the rig's mouth anchor in the canonical pose).
"""
import math
import os
import random
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SWARM = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(SWARM, "../../.."))
sys.path.insert(0, os.path.join(SWARM, "panel-artist"))
sys.path.insert(0, os.path.join(SWARM, "dialogue-writer-build"))
import rig as U1  # noqa: E402
import letter as U2  # noqa: E402

INK, PAGE = 13, 251
PW, PH = 3200, 1800
MEDIA = os.path.join(ROOT, "films/sources/boucle-la/page-animator")

# ---------------------------------------------------------------- page geometry (plan section 5)
RECT = {  # panel interiors' border centre-lines, page px
    "r1c1": (560, 40, 1410, 620), "r1c2": (1440, 40, 2290, 620), "r1c3": (2320, 40, 3170, 620),
    "r2": (560, 650, 3170, 1150),
    "r3c1": (560, 1180, 1410, 1760), "r3c2": (1440, 1180, 2290, 1760), "r3c3": (2320, 1180, 3170, 1760),
}
SLOTS = ["r1c1", "r1c2", "r1c3", "r2", "r3c1", "r3c2", "r3c3"]
SEQ = ["A", "B", "C", "H", "C", "B", "A"]
PAD = dict(l=6, t=6, r=6, b=6)  # raster = panel rect + pad (border); no balloon breaks the top border at this layout
SIZE = {"A": (850, 580), "B": (850, 580), "C": (850, 580), "H": (2610, 500)}
BORDER_PX = 6.0


def raster_size(pid):
    w, h = SIZE[pid]
    return w + PAD["l"] + PAD["r"], h + PAD["t"] + PAD["b"]


def crop_rect(slot):
    x0, y0, x1, y1 = RECT[slot]
    return x0 - PAD["l"], y0 - PAD["t"], x1 + PAD["r"], y1 + PAD["b"]


# ---------------------------------------------------------------- framing (s, ox, oy) panel-relative
# s = page px per thumb px.  Heads (thumb y ~304..432) land in the middle third; figures fill > 60 % of height.
S = 1.20
FRAME = {
    "A": (S, 425 - 525 * S, 188 - 304 * S),
    "B": (S, 425 - 525 * S, 188 - 304 * S),
    "C": (S, 425 - 525 * S, 188 - 304 * S),
    "H": (S, 1450 - 525 * S, 112 - 304 * S),
}

RIG = U1.Rig()
NOTE_THUMB = RIG.cj["rig"]["note"]["size_thumb"]  # [92, 60]
NOTE_OFF = RIG.cj["rig"]["note"]["offset_from_anchor_thumb"]


def note_cards(s):
    w, h = int(round(NOTE_THUMB[0] * s)), int(round(NOTE_THUMB[1] * s))
    out = {}
    for face in (True, False):
        im = np.asarray(U2.note_card(face, w, h).convert("RGBA")).astype(np.float32)
        out[face] = (im[..., 0], im[..., 3] / 255.0)
    return out


CARDS = note_cards(S)


def draw_note(canvas, Ms, P, origin):
    """Handmade card in Odette's hand.  turn: 0 back to reader, 180 face out; substitution at edge-on (90)."""
    th = P.get("note_turn", 0.0)
    face = th > 90.0
    gray, alpha = CARDS[face]
    h, w = gray.shape
    c = abs(math.cos(math.radians(th)))
    half = max(0.035, c) * w / 2
    persp = 0.16 * math.sin(math.radians(th))  # the swinging near edge grows: foreshortened card
    hx, hy = U1.ap(Ms["odette_fore"], RIG.j["odette"]["hand"])
    hx, hy = hx + origin[0], hy + origin[1]
    tilt = math.radians(P.get("note_tilt", 0.0))
    cx, cy = hx + NOTE_OFF[0] * w, hy + NOTE_OFF[1] * h
    sgn = 1 if th <= 90 else -1  # which edge is near flips at edge-on
    corners = [(-half, -h / 2 * (1 - sgn * persp)), (half, -h / 2 * (1 + sgn * persp)),
               (half, h / 2 * (1 + sgn * persp)), (-half, h / 2 * (1 - sgn * persp))]
    dst = [(cx + x * math.cos(tilt) - y * math.sin(tilt), cy + x * math.sin(tilt) + y * math.cos(tilt)) for x, y in corners]
    Hh, Ww = canvas.shape
    if c < 0.08:  # edge-on: the sheet is one pen stroke of paper edge (the substitution drawing)
        d = Image.new("L", (Ww * 3, Hh * 3), 0)
        top = ((dst[0][0] + dst[1][0]) / 2, (dst[0][1] + dst[1][1]) / 2)
        bot = ((dst[2][0] + dst[3][0]) / 2, (dst[2][1] + dst[3][1]) / 2)
        ImageDraw.Draw(d).line([(top[0] * 3, top[1] * 3), (bot[0] * 3, bot[1] * 3)], fill=255, width=int(3.2 * 3))
        aw = np.asarray(d.resize((Ww, Hh), Image.LANCZOS), np.float32) / 255
        gw = np.full_like(canvas, INK)
    else:
        src = np.float32([(0, 0), (w, 0), (w, h), (0, h)])
        Mp = cv2.getPerspectiveTransform(src, np.float32(dst))
        gw = cv2.warpPerspective(gray, Mp, (Ww, Hh), flags=cv2.INTER_CUBIC, borderValue=PAGE)
        aw = cv2.warpPerspective(alpha, Mp, (Ww, Hh), flags=cv2.INTER_LINEAR, borderValue=0)
    sh = cv2.GaussianBlur(np.roll(np.roll(aw, 3, 0), 3, 1), (0, 0), 1.5) * 0.22
    canvas[:] = canvas * (1 - sh) + INK * sh
    canvas[:] = canvas * (1 - aw) + np.clip(gw, INK, PAGE) * aw
    return (cx, cy), (hx, hy)


def figures(pid, pose, black=False, jitter=(0.0, 0.0)):
    """Panel interior (h, w) gray from the rig; draw order with the note slipped under Odette's fingers."""
    w, h = SIZE[pid]
    s, ox, oy = FRAME[pid]
    frame = (s, ox + jitter[0], oy + jitter[1])
    ground = INK if black else PAGE
    cv_ = np.full((h, w), float(ground), np.float32)
    cov = np.zeros((h, w), np.float32)
    Ms, J = RIG.fk(pose, frame)
    if pid != "H":  # the print's own dark bed-curtain crayon behind the heads (A B C)
        RIG.warp(cv_, cov, "backdrop", U1.T(frame[0] / RIG.K, frame[1], frame[2]), (w, h), shadow=False)
    note_xy = None
    for f, pn in U1.ORDER:
        RIG.warp(cv_, cov, f"{f}_{pn}", Ms[f"{f}_{pn}"], (w, h), shadow=not black)
    # the note goes on last: held from behind by its right edge, so its lettered face is never covered
    note_xy = draw_note(cv_, Ms, pose["odette"], (0, 0))
    return np.clip(cv_, 0, 255), J, note_xy, Ms


# ---------------------------------------------------------------- pen furniture (handmade)
def wobbly_border(size, r, width, seed, ss=3):
    m = Image.new("L", (size[0] * ss, size[1] * ss), 0)
    d = ImageDraw.Draw(m)
    rs = random.Random(seed)
    x0, y0, x1, y1 = [v * ss for v in r]
    pts = []
    for (ax, ay, bx, by) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        L = math.hypot(bx - ax, by - ay)
        for t in np.linspace(0, 1, max(4, int(L / (90 * ss))), endpoint=False):
            pts.append((ax + (bx - ax) * t + rs.uniform(-1.1, 1.1) * ss, ay + (by - ay) * t + rs.uniform(-1.1, 1.1) * ss))
    d.line(pts + [pts[0]], fill=255, width=int(width * ss), joint="curve")
    return np.asarray(m.resize(size, Image.LANCZOS), np.float32) / 255


BSEED = {"A": 101, "B": 102, "C": 103, "H": 104}  # one border drawing per panel ID (pairs share it)


def border_mask(pid):
    W, H = raster_size(pid)
    w, h = SIZE[pid]
    return wobbly_border((W, H), (PAD["l"], PAD["t"], PAD["l"] + w, PAD["t"] + h), BORDER_PX + (1.0 if pid == "H" else 0), BSEED[pid])


_BORDER = {k: border_mask(k) for k in SIZE}


# ---------------------------------------------------------------- balloons (U2's hand, tails from the rig)
TAIL_SPEAKER = {"A": "odette", "B": "gustave", "C": "odette", "H": "gustave"}
TAIL_BACKOFF = 34  # tail tip stops short of the mouth (page px)
BAL_LAYOUT = {  # U2's layout (centre, cap, maxw); centre adjusted to the tighter framing where needed
    "A": dict(U2.LAYOUT["A"]), "B": dict(U2.LAYOUT["B"]), "C": dict(U2.LAYOUT["C"]),
    "H": dict(U2.LAYOUT["H"], c=(800, 150)),
}
_BALLOON = {}


def balloon(pid, canon_pose):
    if pid in _BALLOON:
        return _BALLOON[pid]
    _, J, _, _ = figures(pid, canon_pose, black=(pid == "H"))
    mx, my = J[TAIL_SPEAKER[pid]]["mouth"]
    lay = BAL_LAYOUT[pid]
    cx, cy = lay["c"]
    if pid == "H":  # balloon on his left: the tail stops at the back of his head (U2's H convention)
        tx, ty = mx - 132 * FRAME["H"][0], my - 14
    else:
        d = math.hypot(mx - cx, my - cy)
        tx, ty = mx - (mx - cx) / d * TAIL_BACKOFF, my - (my - cy) / d * TAIL_BACKOFF
    spk, text = U2.LINES[pid]
    seed = U2.seed_of(pid, text)
    im, (bx, by), lines, c = U2.balloon(pid, text, cx, cy, lay["cap"], lay["maxw"], (tx, ty), seed, SIZE[pid][0])
    a = np.asarray(im.convert("RGBA")).astype(np.float32)
    rec = dict(text=text, speaker=spk, seed=seed, cap=lay["cap"], maxw=lay["maxw"], centre_in_panel=[round(c[0], 1), round(c[1], 1)],
               tail_tip_in_panel=[round(tx, 1), round(ty, 1)], mouth_in_panel=[round(mx, 1), round(my, 1)],
               offset_in_panel=[bx, by], size=list(im.size), wrapped_lines=lines)
    os.makedirs(os.path.join(MEDIA, "lettering"), exist_ok=True)
    p = os.path.join(MEDIA, "lettering", f"balloon-{pid}.png")
    im.save(p)
    rec["file"] = os.path.relpath(p, ROOT)
    _BALLOON[pid] = (a[..., 0], a[..., 3] / 255.0, (bx, by), rec)
    return _BALLOON[pid]


def render(pid, pose, show_balloon, black=False, canon=None, jitter=(0.0, 0.0)):
    """Full panel raster (gray uint8, RGB-equal), panel rect + PAD; outside the border = page white."""
    W, H = raster_size(pid)
    w, h = SIZE[pid]
    out = np.full((H, W), float(PAGE), np.float32)
    art, J, note_xy, Ms = figures(pid, pose, black, jitter)
    out[PAD["t"]:PAD["t"] + h, PAD["l"]:PAD["l"] + w] = art
    b = _BORDER[pid]
    out = out * (1 - b) + INK * b
    if show_balloon:
        g, a, (bx, by), _ = balloon(pid, canon)
        x, y = bx + PAD["l"], by + PAD["t"]
        hh, ww = a.shape
        sub = out[y:y + hh, x:x + ww]
        sub[:] = sub * (1 - a) + g * a
    return np.clip(out + 0.5, 0, 255).astype(np.uint8), J, note_xy, Ms
