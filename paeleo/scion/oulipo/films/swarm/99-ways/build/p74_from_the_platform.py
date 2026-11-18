"""Page 74 From the platform (point of view; medium: photo-cutout).

The whole incident watched from the platform side of the ticket window. P1 is Arthur Rothstein's own 1937 photograph
of the outside of Randolph station (LoC 2017776101, FORAGED for this page), the stranger (Bubley 1943 cutout, from
99-ways-template) at the window. Every office view is seen through the TICKET OFFICE glass from outside: the glass is
the window cut from Rothstein's interior photograph, laid mirror-reversed because we stand on its other side, so its
lettering reads backwards; the office (99-ways-template rest layers, recomposed without balloons) shows through the
etched pane, and the agent's own words (answer, forgetting) lie behind the glass with it. Only the stranger's words,
spoken on the platform, sit on top of the glass.
Run: python3 -I p74_from_the_platform.py [beats]
"""
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib, ROOT  # noqa: E402
import build_page01 as b01  # noqa: E402
from b1m2 import save_page, save_beats, slip, wrap, balloon, frame_border  # noqa: E402

N, PID, TITLE = 74, "from-the-platform", "From the platform"
W, H = pen99.PAGE_W, pen99.PAGE_H
FOR = ROOT / "films/sources/99-ways/forage/p74"
PIECES = ROOT / "films/sources/99-ways-template/cutout-surgeon/pieces"
VIS = ROOT / "films/sources/99-ways-template/variant-builders/pieces/bubley.visitor.hi.png"
SPEECH = b01.OLD
BOXES = {"P1": (110, 110, 2090, 800),
         "P2": (110, 830, 1085, 1460), "P3": (1115, 830, 2090, 1460),
         "P4": (110, 1490, 1085, 2120), "P5": (1115, 1490, 2090, 2120),
         "P6": (110, 2150, 1085, 2730), "P7": (1115, 2150, 2090, 2730)}
CAP, BCAP = 38, 46
WARM = np.array([1.0, 0.975, 0.93], np.float32)        # one grade for every photograph on the page


def station():
    g = np.asarray(Image.open(FOR / "t_v2400.jpg").convert("L")).astype(np.float32)
    return g          # 2400 x 1917, from the LoC service jpeg (1024 px derivative of 8b36164)


def visitor():
    im = np.asarray(Image.open(VIS)).astype(np.float32)
    return im[..., :3].mean(axis=2), im[..., 3].astype(np.uint8)


def gray3(g):
    return np.dstack([g] * 3) * WARM


def paste_cut(img, g, a, cx, yb, height, margin=10):
    """a photo cutout with its white scissor margin and paper shadow, feet at yb"""
    s = height / g.shape[0]
    gw, gh = int(g.shape[1] * s), int(height)
    gg = cv2.resize(g, (gw, gh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    aa = cv2.resize(a, (gw, gh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
    h, w = img.shape[:2]
    x0, y0 = int(cx - gw / 2), int(yb - gh)
    full = np.zeros((h, w), np.uint8)
    fg = np.zeros((h, w), np.float32)
    xs, ys, xe, ye = max(0, x0), max(0, y0), min(w, x0 + gw), min(h, y0 + gh)
    full[ys:ye, xs:xe] = aa[ys - y0:ye - y0, xs - x0:xe - x0]
    fg[ys:ye, xs:xe] = gg[ys - y0:ye - y0, xs - x0:xe - x0]
    m = (full > 127).astype(np.uint8) * 255
    pm = penlib.scissor(m, margin) if margin else m
    penlib.shadow_onto(img, pm, off=6, blur=5, opacity=0.4)
    pa = pm.astype(np.float32)[..., None] / 255
    img[:] = img * (1 - pa) + np.array([246, 242, 232], np.float32) * pa
    af = full.astype(np.float32)[..., None] / 255
    img[:] = img * (1 - af) + gray3(fg) * af
    return (x0, y0, gw, gh)


def cap_slip(img, text, wmax, seed, x=22, y=20, bottom=False):
    lines = wrap(text, CAP, wmax)
    if bottom:
        y = img.shape[0] - 22 - (int(CAP * 1.42) * (len(lines) - 1) + CAP * 2)
    return slip(img, x, y, lines, CAP, seed)


def size(k):
    x0, y0, x1, y1 = BOXES[k]
    return x1 - x0, y1 - y0


# ------------------------------------------------------------------ the glass, seen from the platform
GLASS = np.asarray(Image.open(PIECES / "rothstein.window.png").convert("L")).astype(np.float32)[:, ::-1].copy()
GX0, GY0, GX1, GY1 = 1440 - 1160, 130, 1440 - 30, 1090        # the etched pane, in the mirrored piece


def glass_panel(k, rest_key, vfrac, inside=None, outside=None, caption=None, seed=0, bottom_cap=False, zoom=1.0, hfrac=0.5):
    w, h = size(k)
    s = w / GLASS.shape[1]
    Gs = cv2.resize(GLASS, (w, int(GLASS.shape[0] * s)), interpolation=cv2.INTER_AREA)
    oy = (Gs.shape[0] - h) // 2
    G = Gs[oy:oy + h]
    gx0, gy0, gx1, gy1 = int(GX0 * s), max(0, int(GY0 * s) - oy), int(GX1 * s), min(h, int(GY1 * s) - oy)
    # the office behind: a rest panel cover-fitted to the pane
    c, used = b01.panel_rest(rest_key)
    pw, ph = gx1 - gx0, gy1 - gy0
    sc = max(pw / c.shape[1], ph / c.shape[0]) * zoom
    cw, ch = int(c.shape[1] * sc) + 1, int(c.shape[0] * sc) + 1
    cs = cv2.resize(c, (cw, ch), interpolation=cv2.INTER_AREA)
    ox = int((cw - pw) * hfrac)
    oyy = int((ch - ph) * vfrac)
    I = cs[oyy:oyy + ph, ox:ox + pw].mean(axis=2)
    I = gray3(I)
    if inside:      # his words are in the office: they lie behind the glass
        lines, cap, ctr, tip_key = inside
        tip = SPEECH[tip_key][0]["tail_tip_panel_px"]
        tx, ty = tip[0] * sc - ox, tip[1] * sc - oyy
        balloon(I, lines, cap, (ctr[0] * pw, ctr[1] * ph), (tx, ty), seed + 1, tail_w=0.22)
    out = gray3(G)
    pane = out[gy0:gy1, gx0:gx1]
    Gp = G[gy0:gy1, gx0:gx1]
    hp = Gp - cv2.GaussianBlur(Gp, (0, 0), 18)
    etch = np.clip((np.abs(hp) - 6) / 22, 0, 1)
    etch = cv2.GaussianBlur(etch, (0, 0), 0.8)[..., None]
    I = cv2.GaussianBlur(I, (0, 0), 0.7)                     # behind the pane: a little softer
    see = I * 0.80 + gray3(Gp) * 0.20                      # through the pane, a little frosted
    pane[:] = see * (1 - 0.78 * etch) + gray3(Gp) * (0.78 * etch)
    # the platform behind us, faintly reflected in the pane (the tracks of the station photograph)
    st = station()
    refl = cv2.resize(st[1450:1800, 120:2280], (pw, ph), interpolation=cv2.INTER_AREA)[:, ::-1]
    pane += ((refl - refl.mean()) * 0.10)[..., None]
    img = out
    if outside:     # her words, on the platform side, on top of the glass
        lines, cap, ctr, tip = outside
        balloon(img, lines, cap, (ctr[0] * w, ctr[1] * h), (tip[0] * w, tip[1] * h), seed + 2, tail_w=0.22)
    if caption:
        cap_slip(img, caption, int(w * 0.62), seed + 3, bottom=bottom_cap)
    return img, used


# ------------------------------------------------------------------ panels
def P1(st):     # E0 the station from the platform; she comes to the window; the agent inside at his desk
    w, h = size("P1")
    g = station()
    k = 2400 / 1024
    x0, y0, x1, y1 = int(35 * k), int(300 * k), int(995 * k), int(640 * k)
    crop = g[y0:y1, x0:x1]
    s = w / crop.shape[1]
    crop = cv2.resize(crop, (w, int(crop.shape[0] * s)), interpolation=cv2.INTER_AREA)
    oy = max(0, (crop.shape[0] - h) // 2)
    img = gray3(cv2.GaussianBlur(crop[oy:oy + h], (0, 0), 0.7))
    v, a = visitor()
    sc = w / (960 * k)        # station px -> panel px
    if st.get("her", True):
        paste_cut(img, v, a, (430 - 35) * k * sc, (612 - 300) * k * sc - oy, 300, margin=6)
    cap_slip(img, "Randolph, 4:09. A traveller comes along the platform to the ticket window. Inside, behind the glass, "
                  "the agent sits at his desk.", 900, 7401)
    return img, ["station"]


def P2(st):     # E0 through the glass: he reads the memo and rises
    return glass_panel("P2", "P1", 0.30, zoom=1.3, hfrac=0.75, caption="Through the glass: the agent reads his memo, and gets up.", seed=7410)


def P3(st):     # E1 her question, from the platform
    q = (["Pardon me —", "have you the", "right time?"], BCAP, (0.76, 0.58), (1.04, 0.95)) if st.get("q", True) else None
    return glass_panel("P3", "P3", 0.40, zoom=1.3, hfrac=0.85, outside=q, caption="He crosses the office. She calls in:", seed=7420)


def P4(st):     # E2 his answer, behind the glass, under his clock
    a = (["Ten past four,", "by the clock."], BCAP + 4, (0.40, 0.20), "P5") if st.get("a", True) else None
    return glass_panel("P4", "P5", 0.30, zoom=1.2, hfrac=0.9, inside=a, seed=7430)


def P5(st):     # E3 she thanks him and turns from the window, toward us
    w, h = size("P5")
    g = station()
    k = 2400 / 1024
    crop = g[int(400 * k):int(640 * k), int(400 * k):int(760 * k)]
    crop = cv2.resize(crop, (w, int(crop.shape[0] * w / crop.shape[1])), interpolation=cv2.INTER_CUBIC)
    crop = cv2.GaussianBlur(crop, (0, 0), 2.0)                # far behind her: out of focus
    oy = max(0, (crop.shape[0] - h) // 2)
    img = gray3(crop[oy:oy + h]) * 0.92
    v, a = visitor()
    box = paste_cut(img, v, a, w * 0.62, h + 820, 1420, margin=12)
    if st.get("t", True):
        balloon(img, ["Much", "obliged!"], BCAP + 6, (w * 0.24, h * 0.36), (box[0] + box[2] * 0.50, box[1] + 112), 7441,
                tail_w=0.24)
    cap_slip(img, "She thanks him and leaves the window.", 560, 7442, bottom=True)
    return img, ["station", "visitor"]


def P6(st):     # E4 through the emptied window: the cupboard opened, the key on its hook
    return glass_panel("P6", "P7", 0.40, caption="Now only the glass: he opens the cupboard. The key hangs inside.",
                       seed=7450)


def P7(st):     # E5 through the glass: pencil to his chin, the line read through it
    f = (["Well, here I am...", "and what for?"], BCAP + 6, (0.50, 0.17), "P8") if st.get("f", True) else None
    return glass_panel("P7", "P8", 0.30, zoom=1.3, hfrac=0.35, inside=f, caption="The key stays on its hook. The SERVICE door stays shut.",
                       seed=7460, bottom_cap=True)


PANELS = [("P1", P1), ("P2", P2), ("P3", P3), ("P4", P4), ("P5", P5), ("P6", P6), ("P7", P7)]


def build(upto=7, state=None):
    state = state or {}
    page = pen99.sheet99()
    shown = []
    for i, (k, fn) in enumerate(PANELS):
        if i >= upto:
            continue
        x0, y0, x1, y1 = BOXES[k]
        page[y0:y1, x0:x1] = fn(state.get(k, {}))[0]
        shown.append(BOXES[k])
    frame_border(page, shown, w=12, seed=7490)
    return page


if __name__ == "__main__":
    page = build()
    img, size_b = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size_b)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = []
        for u, st in ((1, {}), (2, {}), (3, {}), (4, {}), (5, {}), (6, {}), (7, {"P7": {"f": False}}), (7, {})):
            p = np.clip(np.round(build(u, st)), 0, 255).astype(np.uint8)
            pen99.folio(p, N, TITLE)
            frames.append(cv2.resize(p, (960, 1242), interpolation=cv2.INTER_AREA))
        save_beats(N, frames)
