"""99 ways, page 77 "The cupboard" (genre; medium: charcoal-card).
Shot as horror: low-key charcoal light, one lamp, a shadow that goes ahead of him, a face at the black glass, a
Dutch-tilted clock, an emptied window still speaking, the cupboard looming closer; then a shock cut to the key hanging
in the black of the cupboard (CREEEAK, burst of charcoal strokes); his underlit face; and the horror is the blank: a
huge empty thought balloon over a small man, key on its hook, SERVICE door shut.
Articulated grey-card puppets (charcoal99 kit, b1m2 cut model) pinned on the teuf-teuf Cueva rock wall (CC BY-SA 3.0);
the key is the ANRC 1922 cutout cut as a card. Lettering in the shared pen hand; captions bone-on-black.
Run: python3 -I p77_the_cupboard.py"""
import json
import math
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import charcoal99 as C  # noqa: E402
import b1m2 as B  # noqa: E402
from b1m2 import agent, stranger, desk, window, clock, cupboard, service_door, Shape, R_  # noqa: E402
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
import p31_sounds_only as P31  # noqa: E402  (floor_band, key_card)

N, PID, TITLE = 77, "the-cupboard", "The cupboard"
W, H = 2200, 2850
BLACK = np.array([20, 19, 17], np.float32)
BONE = np.array([232, 224, 200], np.float32)

BOXES = {
    "P1": (110, 110, 1310, 640), "P2": (1350, 110, 2090, 640),
    "P3": (110, 670, 1080, 1230), "P4": (1120, 670, 2090, 1230),
    "P5": (110, 1260, 743, 1800), "P6": (783, 1260, 2090, 1800),
    "P7": (110, 1830, 1400, 2730), "P8": (1440, 1830, 2090, 2270), "P9": (1440, 2300, 2090, 2730),
}


def light(lum, cx, cy, r, floor=0.16, power=1.0):
    """Darkness: everything falls off from one lamp pool (applied after the cards are pinned)."""
    h, w = lum.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d2 = ((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r)
    L = floor + (1 - floor) * np.exp(-d2) ** power
    lum *= L
    return lum


def tilt(lum, deg, fill=0.1):
    h, w = lum.shape
    M = cv2.getRotationMatrix2D((w / 2, h / 2), deg, 1.18)
    return cv2.warpAffine(lum, M, (w, h), borderMode=cv2.BORDER_REFLECT)


def scale_shapes(shapes, s, ox=0, oy=0):
    return [Shape(sh.pts * s + (ox, oy), sh.role, hole=sh.hole, smooth=sh.smooth, z=sh.z) for sh in shapes]


def written(lum, lines, cx, cy, cap, seed, deg=0.0, dark=0.12):
    m = pen99.letter(lines, cap, seed, weight=0.14)
    pm = np.zeros(lum.shape, np.uint8)
    C.place(pm, m, cx, cy, deg)
    a = C.rub_mask(pm, seed, smear=(2, 1), keep=0.95)
    lum[:] = lum * (1 - a) + dark * a


def caption(rgb, text, x, y, seed, cap=34, width=None):
    width = width or rgb.shape[1] - 2 * x - 40
    lines = B.wrap(text, cap, width)
    B.slip(rgb, x, y, lines, cap, seed, paper=BLACK, pad=(20, 12), ink=BONE, shadow=0.5)


def to_rgb(lum):
    return C.tone(lum)


# ------------------------------------------------------------------ panels (each returns lum; post() adds text in RGB)
def P1(w, h, st=None):        # the memo under the lamp
    lum = C.wall(w, h, 7701, level=0.80)
    top = int(h * 0.52)
    C.pin_up(lum, [R_(-20, top, w + 20, h + 20, "desk")], 7702, halo=False)
    C.pin_up(lum, [Shape(B.bar_pts((w * 0.70, h * 0.86), (w * 0.93, h * 0.74), 14), "pencil", smooth=False)], 7703, halo=False)
    m = np.zeros((h, w), np.uint8)
    mx, my, mw, mh = w * 0.34, h * 0.30, w * 0.34, h * 0.52
    pts = np.array([(mx, my), (mx + mw, my + 8), (mx + mw - 4, my + mh), (mx + 4, my + mh - 6)])
    cv2.fillPoly(m, [np.int32(pts * 4)], 255, cv2.LINE_AA, shift=2)
    C.drop(lum, m, (6, 9), 5, 0.5)
    C.card_piece(lum, m, 0.95, 7704, edge=0.06, rub=0.02)
    written(lum, ["MEMO", "4:15 - open", "SERVICE door.", "Key in cupboard."], mx + mw / 2, my + mh / 2, 46, 7705, deg=1.5)
    light(lum, mx + mw * 0.5, my + mh * 0.4, w * 0.36, floor=0.10)
    return lum


def P1post(rgb):
    caption(rgb, "It was the simplest errand in the world.", 24, 22, 7706, width=1000)


def P2(w, h, st=None):        # he rises; his shadow goes ahead of him up the wall toward the cupboard
    lum = C.wall(w, h, 7711, level=0.82)
    fy = h - 70
    P31.floor_band(lum, fy, 7712)
    cup, _ = cupboard(w * 0.70, fy - 330, 170, 330)
    C.pin_up(lum, cup, 7713)
    sh = agent(0, 0, face=1, scale=1.0, legs=(22, -18), sh=40, el=-30, pencil_deg=200)
    big = scale_shapes(sh, 0.62, w * 0.50, fy - 40)
    m = B.raster([s for s in big if not s.hole], w, h)
    m = cv2.GaussianBlur(m, (0, 0), 6).astype(np.float32) / 255
    M = cv2.getRotationMatrix2D((w * 0.30, fy), -14, 1.0)
    m = cv2.warpAffine(m, M, (w, h))
    lum *= (1 - 0.72 * m)
    C.pin_up(lum, agent(w * 0.26, fy + 4, face=1, scale=0.36, legs=(16, -10), sh=10, el=-10, lean=6, pencil_deg=200), 7714)
    light(lum, w * 0.10, fy + 20, w * 0.60, floor=0.14, power=0.7)
    return lum


def P2post(rgb):
    caption(rgb, "He rose. His shadow went on ahead of him.", 24, 22, 7716, width=600)


def window_lum(w, h, seed, face=True, scale=1.2):
    lum = C.wall(w, h, seed, level=0.78)
    x0, y0, ww = w * 0.22, h * 0.14, w * 0.56
    sill = h * 0.74
    pane = np.zeros((h, w), np.float32)
    pane[int(y0 + 60):int(sill), int(x0):int(x0 + ww)] = 1
    lum[:] = lum * (1 - pane) + 0.07 * pane                     # black glass
    if face:
        st_ = stranger(x0 + ww * 0.52, sill + 6, face=-1, scale=scale)
        C.pin_up(lum, st_, seed + 2, halo_reach=10, halo_strength=0.1,
                 tones=dict(coat=0.10, collar=0.16, skin_s=0.86, hat=0.06, bow=0.30, glove=0.1))
    ws, _ = window(x0, y0, ww, h - y0 + 40, sill=sill, header=60)
    C.pin_up(lum, ws[:5], seed + 3, halo_reach=10, halo_strength=0.15)
    return lum, (x0, y0, ww, sill)


def P3(w, h, st=None):        # a face at the black glass, lit from below
    lum, (x0, y0, ww, sill) = window_lum(w, h, 7721)
    light(lum, x0 + ww * 0.50, sill + 40, w * 0.42, floor=0.12)
    return lum


def P3post(rgb, w, h):
    caption(rgb, "Then, at the glass, a face.", 24, 22, 7726, width=480)
    B.balloon(rgb, ["Pardon me —", "have you the", "right time?"], 42, (w * 0.80, h * 0.30), (w * 0.56, h * 0.48), 7727)


def P4(w, h, st=None):        # the clock, Dutch-tilted: 4:10
    lum = C.wall(w, h, 7731, level=0.84)
    r = h * 0.30
    C.pin_up(lum, clock(w * 0.40, h * 0.36, r, hh=4, mm=10, swing=14), 7732, halo_reach=20)
    C.sfx(lum, "TICK", w * 0.16, h * 0.84, 70, 7733, deg=8, weight=0.2, fatten=1, halo=6, dark=0.06)
    light(lum, w * 0.40, h * 0.40, w * 0.45, floor=0.14)
    return tilt(lum, 11)


def P4post(rgb, w, h):
    B.balloon(rgb, ["Ten past four,", "by the clock."], 42, (w * 0.76, h * 0.25), (w * 0.95, h * 1.06), 7736)


def P5(w, h, st=None):        # the window empty; the thanks comes out of the dark
    lum, (x0, y0, ww, sill) = window_lum(w, h, 7741, face=False)
    light(lum, x0 + ww * 0.5, sill + 60, w * 0.5, floor=0.12)
    return lum


def P5post(rgb, w, h):
    B.balloon(rgb, ["Much", "obliged!"], 40, (w * 0.50, h * 0.44), (w * 0.50, h * 0.66), 7746)
    caption(rgb, "And she was gone.", 20, h - 92, 7747, width=400)


def cupboard_scene(w, h, seed, k=1.0, opened=0.0, hand=False, man=True):
    """The cupboard seen low, looming; k = how close (1 = far, 2 = filling the frame)."""
    lum = C.wall(w, h, seed, level=0.80)
    fy = h - 50
    P31.floor_band(lum, fy, seed + 1)
    cw, ch = 210 * k, 400 * k
    cx0 = w * 0.62 - cw / 2
    cup, _ = cupboard(cx0, fy - ch, cw, ch, open_deg=opened)
    C.pin_up(lum, cup, seed + 2)
    if man:
        C.pin_up(lum, agent(cx0 - 70 * k ** 0.5, fy + 4, face=1, scale=0.40 * k ** 0.5, legs=(16, -12),
                            sh=70 if hand else 10, el=10 if hand else -10, pencil_deg=200), seed + 3)
    light(lum, cx0 + cw * 0.5, fy - ch * 0.3, w * 0.30 * k ** 0.5, floor=0.10, power=0.9)
    return lum


def P6(w, h, st=None):
    return cupboard_scene(w, h, 7751, k=1.15, hand=True)


def P6post(rgb, w, h):
    caption(rgb, "Closer. The cupboard. Closer.", 24, 22, 7756, width=600)


def key_shock(w, h, seed, creak=True):
    """Shock cut: the key in the black of the cupboard, the leaf edge, a burst of strokes."""
    lum = np.full((h, w), 0.07, np.float32)
    lum *= 1 + 0.4 * C.grain(h, w, seed, 3.0)
    g = C.wall(w, h, seed + 1, level=0.5)
    lum[:] = np.maximum(lum, g * 0.0 + 0.0) * 1.0 + 0.0
    rng = np.random.default_rng(seed)
    kx, ky = w * 0.52, h * 0.52
    for i in range(46):                                         # burst of charcoal strokes around the key
        a = rng.uniform(0, 2 * math.pi)
        r0, r1 = rng.uniform(0.28, 0.36) * h, rng.uniform(0.55, 0.9) * h
        p = [(kx + r0 * math.cos(a), ky + r0 * math.sin(a)), (kx + r1 * math.cos(a), ky + r1 * math.sin(a))]
        m = np.zeros((h, w), np.uint8)
        penlib.brush_line(m, p, rng.uniform(3, 7), seed + i, 1.2)
        aa = C.rub_mask(m, seed + i) * 0.7
        lum[:] = lum * (1 - aa) + 0.62 * aa
    C.pin_up(lum, [R_(-20, -20, w * 0.13, h + 20, "door")], seed + 2, halo=False)     # leaf edge, near
    ks = h / 640 * 0.62
    km = P31.key_card(lum, kx, ky, ks, seed + 3)
    ys, xs = np.nonzero(km)
    tx, ty = kx + 26, ky + (ys.max() - ky) * 0.15                  # key_card's blank tag: write SERVICE on it
    written(lum, ["SERVICE"], tx + 32, ty + 24, 15, seed + 5, deg=6, dark=0.1)
    light(lum, kx, ky, h * 0.60, floor=0.35)
    if creak:
        C.sfx(lum, "CREEEAK", w * 0.70, h * 0.88, 92, seed + 4, deg=-6, weight=0.21, fatten=2, halo=10, dark=0.05)
    return tilt(lum, -6), km


def P7(w, h, st=None):
    lum, _ = key_shock(w, h, 7761)
    return lum


def P7post(rgb, w, h):
    # the tag: SERVICE written on it (key_card cuts it blank); position of the tag after the tilt is approximate
    pass


def face_lum(w, h, seed):
    lum = C.wall(w, h, seed, level=0.55)
    s = h / 440 * 1.55
    fig = agent(w * 0.50, h * 0.52 + 800 * s, face=-1, scale=s, sh=50, el=120, wr=8, pencil_deg=40, tilt=8)
    C.pin_up(lum, fig, seed + 1, halo_reach=30, tones=dict(skin=0.70, ear=0.62, hair=0.06))
    light(lum, w * 0.50, h * 1.10, h * 0.70, floor=0.10)
    return lum


def P8(w, h, st=None):
    return face_lum(w, h, 7771)


def P8post(rgb, w, h):
    B.balloon(rgb, ["Well, here I am...", "and what for?"], 36, (w * 0.50, h * 0.16), (w * 0.44, h * 0.74), 7776)


def blank_lum(w, h, seed, grow=1.0):
    lum = C.wall(w, h, seed, level=0.78)
    u = min(w / 650, h / 430) if h > 600 else 1.0            # portrait beat frames: the same scene, larger
    fy = h - 40 * u
    P31.floor_band(lum, fy, seed + 1)
    cx0 = w * 0.30
    cup, _ = cupboard(cx0, fy - 170 * u, 100 * u, 170 * u, open_deg=112)
    C.pin_up(lum, cup, seed + 2, halo_reach=10)
    P31.key_card(lum, cx0 - 18 * u, fy - 120 * u, 0.10 * u, seed + 3)
    C.pin_up(lum, service_door(w * 0.78, fy - 200 * u, 90 * u, 200 * u), seed + 4, halo_reach=10)
    C.pin_up(lum, agent(cx0 + 150 * u, fy + 2, face=-1, scale=0.19 * u, legs=(3, -3), sh=50, el=120, wr=8, pencil_deg=40, tilt=6),
             seed + 5, halo_reach=10)
    light(lum, cx0 + 120 * u, fy - 60 * u, w * 0.40, floor=0.12)
    # the blank: a huge empty thought balloon, three bubbles rising from his head
    if grow > 0:
        hx, hy = cx0 + 155 * u, fy - 175 * u
        for k, (dx, dy, r) in enumerate(((10, -16, 7), (30, -40, 12), (60, -70, 18))):
            m = np.zeros((h, w), np.uint8)
            cv2.circle(m, (int(hx + dx * u), int(hy + dy * u)), int(r * u * min(1, grow * 3)), 255, -1, cv2.LINE_AA)
            C.drop(lum, m, (3, 4), 2, 0.3)
            C.card_piece(lum, m, 0.97, seed + 10 + k, edge=0.04, rub=0.01)
        if grow > 0.34:
            g = (grow - 0.34) / 0.66
            m = np.zeros((h, w), np.uint8)
            cv2.ellipse(m, (int(w * 0.56), int(h * 0.30)), (int(w * 0.40 * g), int(min(h * 0.24, w * 0.28) * g)), -4, 0, 360, 255, -1, cv2.LINE_AA)
            C.drop(lum, m, (6, 8), 4, 0.4)
            C.card_piece(lum, m, 0.985, seed + 20, edge=0.03, rub=0.01)
            e = cv2.morphologyEx(m, cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8))
            a = C.rub_mask(e, seed + 21) * 0.8
            lum[:] = lum * (1 - a) + 0.1 * a
    return lum


def P9(w, h, st=None):
    return blank_lum(w, h, 7781)


def P9post(rgb, w, h):
    caption(rgb, "Where the errand was: nothing.", 16, h - 74, 7786, cap=28, width=w - 60)


PANELS = {"P1": (P1, lambda rgb, w, h: P1post(rgb)), "P2": (P2, lambda rgb, w, h: P2post(rgb)),
          "P3": (P3, P3post), "P4": (P4, P4post), "P5": (P5, P5post), "P6": (P6, P6post),
          "P7": (P7, P7post), "P8": (P8, P8post), "P9": (P9, P9post)}


def build():
    page = pen99.sheet99()
    for k, (x0, y0, x1, y1) in BOXES.items():
        w, h = x1 - x0, y1 - y0
        f, post = PANELS[k]
        rgb = to_rgb(f(w, h))
        post(rgb, w, h)
        page[y0:y1, x0:x1] = rgb
    B.frame_border(page, list(BOXES.values()), w=12, seed=7799)
    return page


# ------------------------------------------------------------------ beats: the creep, the shock cut, the blank
BW, BH = 960, 1242


def framed(rgb):
    fr = pen99.sheet99(BW, BH) if False else rgb
    B.frame_border(fr, [(14, 14, BW - 14, BH - 14)], w=10, seed=7830)
    return fr


def beats():
    out = []
    for k, hand in ((1.0, False), (1.5, False), (2.1, True)):
        rgb = to_rgb(cupboard_scene(BW, BH, 7800, k=k, hand=hand))
        out.append(framed(rgb))
    lum, _ = key_shock(BW, BH, 7810)
    out.append(framed(to_rgb(lum)))
    rgb = to_rgb(face_lum(BW, BH, 7820))
    B.balloon(rgb, ["Well, here I am...", "and what for?"], 54, (BW * 0.5, BH * 0.14), (BW * 0.44, BH * 0.74), 7821)
    out.append(framed(rgb))
    for g in (0.25, 0.6, 1.0):
        out.append(framed(to_rgb(blank_lum(BW, BH, 7840, grow=g))))
    return out


def record(size, nb):
    canon = json.load(open(B.ROOT / "films/swarm/99-ways/canon.json"))
    Cn = [c for c in canon["constraints"] if c["id"] == PID][0]
    src = ["teuf-teuf:cueva-de-las-manos", "99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934",
           "99-ways:handmade"]
    B.credit_pages(src, N)
    rec = {
        "n": N, "id": PID, "title": TITLE, "rule": Cn["rule"], "medium": Cn["medium"], "family": Cn["family"],
        "canon_revision": canon["revision"], "declares": Cn["declares"],
        "file": f"assets/pages/99-ways/{N}-{PID}.jpg", "master": f"films/sources/99-ways/masters/{N}-{PID}.png",
        "beats_dir": f"films/sources/99-ways/beats/{N}",
        "build": "films/swarm/99-ways/build/p77_the_cupboard.py (charcoal-card kit: charcoal99.py; key card and floor: p31_sounds_only.py; cut model: b1m2)",
        "sources": src,
        "made": [
            "nine panels of articulated grey-card puppets and set pieces (charcoal99.pin_up: separate cut cards, charcoal rubbed in darker at the cut edges, drop shadows, brass split pins) from the b1m2 cut model, pinned on the teuf-teuf Cueva plain-rock wall (CC BY-SA 3.0, relief only) and printed through the teuf-teuf sepia ramp",
            "horror lighting made per panel as one lamp pool with a deep falloff over the pinned cards (low key, vignettes, underlighting on the face at the glass and on his face), Dutch tilts on the clock and the shock panel",
            "the creep: the memo under the lamp; his shadow (his own puppet blurred, enlarged and swung up the wall) going ahead of him to the cupboard; a pale face at the black glass; the emptied window still saying 'Much obliged!'; the cupboard looming as he reaches",
            "the shock cut: the ANRC 1922 key cut as a pale card filling the big panel in the cupboard's black, the near leaf edge, a burst of rubbed charcoal strokes, CREEEAK in fattened charcoal pen lettering; SERVICE written on its tag",
            "the blank: his underlit face with the forgetting line, then a small man at the open cupboard (key on its hook, SERVICE door shut) under a huge EMPTY cut-card thought balloon",
            "captions as black cards lettered bone in the shared pen hand ('It was the simplest errand in the world.' ... 'Where the errand was: nothing.'); the four canon lines in the shared cut-paper balloons; folio '77 / The cupboard' (pen99.folio)"],
        "events": {"E0": "P1 the memo under the lamp; P2 he rises, his shadow goes ahead", "E1": "P3 a face at the black glass: 'Pardon me \u2014 have you the right time?'",
                   "E2": "P4 the clock, tilted, 4:10: 'Ten past four, by the clock.'", "E3": "P5 the window empty: 'Much obliged!'",
                   "E4": "P6 he reaches the cupboard; P7 shock cut: the key on its hook, tagged SERVICE",
                   "E5": "P8 his face, pencil at chin: 'Well, here I am... and what for?'; P9 the empty thought balloon, key on its hook, SERVICE door shut"},
        "lines": {k: v["text"] for k, v in canon["incident"]["lines"].items()},
        "genre_cues": ["low-key single-lamp light and vignettes", "shadow going ahead of the figure", "face at a black window",
                       "Dutch angles", "slow push-in on a looming door", "shock cut with sound effect (CREEEAK) and burst lines",
                       "underlit face close-up", "dread captions on black cards", "the empty thought balloon as the monster"],
        "beat": "the push-in and the shock: the cupboard grows in three frames as he creeps up and reaches, a hard cut to the key in the dark (CREEEAK), his underlit face says the line, then the empty thought balloon swells over him in three frames",
        "beat_frames": ["b01: cupboard far, he creeps", "b02: closer", "b03: the cupboard fills the frame, his hand reaches",
                        "b04: SHOCK CUT: the key in the black, CREEEAK", "b05: his face, 'Well, here I am... and what for?'",
                        "b06: small man at the open cupboard, thought bubbles rising", "b07: the blank balloon swelling", "b08: the blank balloon full"],
        "self_check": {"size_px": [2200, 2850], "jpeg_bytes": size, "jpeg_quality": 90,
                       "in_target_0.4_1.2MB": 400000 <= size <= 1200000, "panels": len(BOXES), "beat_frames": nb,
                       "outcome": "key on its hook (P7, P9), SERVICE door shut (P9)",
                       "check": Cn["check"], "pending": "independent blind reading not run by the maker"},
    }
    B.write_record(rec)


if __name__ == "__main__":
    page = build()
    img, size = B.save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    nb = B.save_beats(N, beats())
    record(size, nb)
