"""Page 42 Lamp shadows (medium and material; medium: shadow-puppet).

Only shadows tell it: every panel frames a stretch of the office wall (plaster above a boarded wainscot, the
LoC 1934 sheet as plaster fibre) and the people are never in frame. The b1m2 cut-paper puppets (HANDMADE) are
held between a lamp and the wall, so what the page shows is the soft, stretched shadow they throw (puppet
masks projected through a homography toward the wall, penumbra by blur, the wall's own lamp light multiplied
down). The things in the office are there in plain light: the desk edge with the memo slip, the clock, the
cupboard, the ANRC 1922 brass key (99-ways-template cutout) and the SERVICE door. Two lamps: the agent's desk
lamp, and the pendant lamp over the ticket window, which throws the window grille and the stranger's shadow in
onto the same wall. Lines in the shared pen hand, their tails pointing to the shadows' heads.
Run: python3 -I p42_lamp_shadows.py [beats]
"""
import math
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa
from p05_noir import brass_key, paper_card, hook

N, PID, TITLE = 42, "lamp-shadows", "Lamp shadows"
SHEET = pen99.sheet99()
FIBRE = SHEET.mean(axis=2) - SHEET.mean()
BCAP = 44

BOXES = {
    "P1": (110, 110, 1250, 900), "P2": (1290, 110, 2090, 900),
    "P3": (110, 940, 760, 1720), "P4": (800, 940, 1420, 1720), "P5": (1460, 940, 2090, 1720),
    "P6": (110, 1760, 900, 2730), "P7": (940, 1760, 2090, 2730),
}

PLASTER = np.array([232, 220, 196], np.float32)
BOARD = np.array([168, 128, 88], np.float32)
WOOD = np.array([104, 70, 44], np.float32)
WOOD_D = np.array([70, 46, 30], np.float32)
INSIDE = np.array([52, 38, 28], np.float32)
SHADOW_TINT = np.array([40, 30, 26], np.float32)


def wall(w, h, ox, oy, lamp, wains, lit=1.0, spread=1.0):
    """Office wall lit by a lamp at `lamp` (panel coords, may be off-panel): plaster and wainscot."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    img = np.empty((h, w, 3), np.float32)
    img[:] = PLASTER
    # boarded wainscot with a rail
    img[wains:] = BOARD
    seam = ((xx[wains:] % 74) < 4)
    img[wains:][seam] = BOARD * 0.72
    img[wains - 16:wains + 4] = WOOD
    img[wains - 18:wains - 14] = WOOD * 1.25
    f = FIBRE[oy:oy + h, ox:ox + w]
    img += f[..., None] * 1.0
    d = np.sqrt((xx - lamp[0]) ** 2 + ((yy - lamp[1]) * 1.15) ** 2) / (spread * max(w, h))
    light = np.clip(1.12 - 0.78 * d, 0.30, 1.0) ** 1.25
    light = 0.12 + (light - 0.12) * lit
    warm = np.array([1.0, 0.95, 0.84], np.float32)
    return img * light[..., None] * warm


def lit_patch(img, quad, gain=0.55, blur=5):
    m = np.zeros(img.shape[:2], np.uint8)
    cv2.fillPoly(m, [np.int32(np.array(quad) * 4)], 255, cv2.LINE_AA, shift=2)
    m = cv2.GaussianBlur(m, (0, 0), blur).astype(np.float32) / 255
    img *= (1 + gain * m)[..., None]
    return m


def project(shapes, quad, box=None):
    """Map the shapes' bounding box (or `box`) onto quad (tl, tr, br, bl) by a homography: the cast."""
    allp = np.concatenate([s.curve() for s in shapes])
    if box is None:
        x0, y0 = allp.min(0)
        x1, y1 = allp.max(0)
    else:
        x0, y0, x1, y1 = box
    src = np.float32([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    Hm = cv2.getPerspectiveTransform(src, np.float32(quad))
    out = []
    for s in shapes:
        c = s.curve()
        q = cv2.perspectiveTransform(c.reshape(-1, 1, 2).astype(np.float32), Hm).reshape(-1, 2)
        out.append(Shape(q, s.role, hole=s.hole, smooth=False, z=s.z))
    return out


def cast(img, shapes, quad, box=None, depth=0.70, soft=3.5, holes=True):
    """Lay the projected shadow on the wall: a multiply, deepest where the lamp is brightest."""
    sh = project(shapes, quad, box)
    m = raster(sh, img.shape[1], img.shape[0], holes=holes)
    m = cv2.GaussianBlur(m, (0, 0), soft).astype(np.float32) / 255
    a = (m * depth)[..., None]
    img[:] = img * (1 - a) + SHADOW_TINT * a * (img / 255.0 + 0.25)
    return m


def solid(img, shapes, color, roles=None, holes=True, blur=0.6):
    m = raster(shapes, img.shape[1], img.shape[0], roles=roles, holes=holes)
    if blur:
        m = cv2.GaussianBlur(m, (0, 0), blur)
    comp(img, m, color)
    return m


def furn(img, shapes, color):
    """A wooden fixture: solid board, its cut moulding lines drawn darker (not cut through to the wall)."""
    solid(img, shapes, color, holes=False)
    sl = [Shape(x.pts, "slit", smooth=x.smooth, z=0) for x in shapes if x.hole and x.role == "slit"]
    if sl:
        solid(img, sl, color * 0.55)


def object_shadow(img, shapes, dx, dy, depth=0.45, soft=6):
    """The small shadow a wall fixture throws beside itself."""
    m = raster(shapes, img.shape[1], img.shape[0], holes=False)
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    m = cv2.warpAffine(m, M, (img.shape[1], img.shape[0]))
    m = cv2.GaussianBlur(m, (0, 0), soft).astype(np.float32) / 255
    img *= (1 - depth * m)[..., None]


def wall_clock(img, cx, cy, r, hh, mm, swing, lamp):
    sh = clock(cx, cy, r, hh=hh, mm=mm, swing=swing)
    dx, dy = (cx - lamp[0]) * 0.035, (cy - lamp[1]) * 0.035
    object_shadow(img, sh, dx, dy)
    body = [s for s in sh if s.role in ("clock", "dial", "pendwin")]
    solid(img, body, WOOD)
    face = np.zeros(img.shape[:2], np.uint8)
    cv2.circle(face, (int(cx * 4), int(cy * 4)), int(r * 0.80 * 4), 255, -1, cv2.LINE_AA, shift=2)
    comp(img, face, np.array([240, 232, 210], np.float32) * float(np.clip(img[int(cy), int(cx)].mean() / PLASTER.mean() + 0.25, 0.6, 1.05)))
    solid(img, [s for s in sh if s.role == "hand" or (s.role == "clock" and not s.hole and s.z == 2 and len(s.pts) == 4)],
          np.array([22, 18, 16], np.float32))


def window_light(img, quad, header_frac=0.17, sill_frac=0.62, lit=1.0):
    """The ticket-window pendant lamp throws the window onto our wall: a bright skewed patch, the header board
    and glazing bars as dark bands, TICKET OFFICE through the etched header glass, mirror-reversed."""
    tl, tr, br, bl = [np.array(p, float) for p in quad]
    lit_patch(img, quad, gain=0.62 * lit, blur=6)
    lerp = lambda a, b, t: a + (b - a) * t

    def band(t0, t1, s0=0.0, s1=1.0):
        a0, a1 = lerp(tl, bl, t0), lerp(tr, br, t0)
        b0, b1 = lerp(tl, bl, t1), lerp(tr, br, t1)
        return [lerp(a0, a1, s0), lerp(a0, a1, s1), lerp(b0, b1, s1), lerp(b0, b1, s0)]
    bars = [band(0, header_frac), band(sill_frac, sill_frac + 0.06), band(sill_frac + 0.06, 1.0, 0.0, 1.0),
            band(header_frac, sill_frac, 0.485, 0.515), band(0.38, 0.40)]
    m = np.zeros(img.shape[:2], np.uint8)
    for q in bars[:2] + bars[3:]:
        cv2.fillPoly(m, [np.int32(np.array(q) * 4)], 255, cv2.LINE_AA, shift=2)
    m = cv2.GaussianBlur(m, (0, 0), 3).astype(np.float32) / 255
    img *= (1 - 0.62 * m)[..., None]
    # reversed letters of the etched header glass, light through them
    hq = band(0.02, header_frac - 0.02, 0.05, 0.95)
    lm = letter(["TICKET OFFICE"], 40, 4201, weight=0.17)[:, ::-1]
    hgt, wid = lm.shape
    Hm = cv2.getPerspectiveTransform(np.float32([(0, 0), (wid, 0), (wid, hgt), (0, hgt)]), np.float32(hq))
    L = cv2.warpPerspective(lm, Hm, (img.shape[1], img.shape[0]))
    L = cv2.GaussianBlur(L, (0, 0), 1.4).astype(np.float32) / 255
    img *= (1 + 0.85 * L * lit)[..., None]
    return band


def P1(st):
    x0, y0, x1, y1 = BOXES["P1"]
    w, h = x1 - x0, y1 - y0
    lamp = (260, h + 40)
    img = wall(w, h, x0, y0, lamp, wains=h - 210, lit=st.get("lit", 1.0))
    if st.get("lit", 1.0) < 0.5:
        return img
    wall_clock(img, w - 210, 200, 74, 4, 9, -4, lamp)
    # the agent at his desk, between lamp and wall: his shadow, bent over the memo, pencil up
    a = agent(0, 0, face=1, scale=1.0, seated=True, lean=8, tilt=16, sh=40, el=70, wr=-10, pencil_deg=60, far_arm=(30, 60))
    cast(img, a, [(330, 60), (900, 40), (930, h - 40), (360, h - 20)], depth=0.72, soft=4.5)
    # the desk edge and lamp in the near foreground (objects, lit), with the memo slip on the desk
    desk_top = h - 96
    sl = [R_(-10, desk_top, w + 10, h + 10, "desk")]
    solid(img, sl, WOOD_D)
    img[desk_top:desk_top + 6] = img[desk_top:desk_top + 6] * 0.6 + np.array([196, 150, 96]) * 0.4
    shade = [Shape([(lamp[0] - 150, h - 150), (lamp[0] - 80, h - 300), (lamp[0] + 80, h - 300), (lamp[0] + 150, h - 150)],
                   "lamp", smooth=False)]
    solid(img, shade + [R_(lamp[0] - 10, h - 150, lamp[0] + 10, desk_top, "lamp")], np.array([30, 44, 34], np.float32))
    rim = np.zeros(img.shape[:2], np.uint8)
    cv2.line(rim, (int((lamp[0] - 148) * 4), int((h - 150) * 4)), (int((lamp[0] + 148) * 4), int((h - 150) * 4)), 255, 24,
             cv2.LINE_AA, shift=2)
    comp(img, rim, np.array([250, 232, 170], np.float32))
    slip(img, 470, desk_top - 64, ["MEMO", "4:15 - open SERVICE door.", "Key in cupboard."], 30, 4211, tilt=-4,
         paper=np.array([242, 236, 216], np.float32), shadow=0.5)
    return img


def P2(st):
    x0, y0, x1, y1 = BOXES["P2"]
    w, h = x1 - x0, y1 - y0
    lamp = (-260, h + 60)
    img = wall(w, h, x0, y0, lamp, wains=h - 230, lit=st.get("lit", 1.0), spread=1.25)
    if st.get("lit", 1.0) < 0.5:
        return img
    c, _ = cupboard(w - 290, 230, 220, 380)
    object_shadow(img, c, 18, -6)
    furn(img, c, WOOD)
    sd = service_door(w - 30, 150, 220, 600)
    furn(img, sd, WOOD_D)
    # he has risen and walks off from the lamp: the shadow is huge and leans away along the wall
    f = st.get("walk", 1.0)
    a = agent(0, 0, face=1, scale=1.0, legs=(24, -22), sh=-24, el=26, lean=4, pencil_deg=200, far_arm=(24, 22))
    xs = 20 + 260 * f
    cast(img, a, [(xs + 70, 10), (xs + 430, 40), (xs + 380, h - 10), (xs + 30, h - 6)], depth=0.70, soft=5.0)
    return img


def window_panel(key, st, lamp, quad, stranger_pose, agent_quad, agent_pose, line=None):
    x0, y0, x1, y1 = BOXES[key]
    w, h = x1 - x0, y1 - y0
    img = wall(w, h, x0, y0, lamp, wains=h - 190, lit=st.get("lit", 1.0), spread=1.2)
    if st.get("lit", 1.0) < 0.5:
        return img, w, h
    band = window_light(img, quad)
    if stranger_pose is not None:
        s = stranger(0, 0, **stranger_pose)
        tl, tr, br, bl = [np.array(p, float) for p in quad]
        # her shadow sits in the glazing, head and hat above the sill band
        q = band(0.16, 0.64, 0.12, 0.88)
        cast(img, s, q, box=(-110, -275, 110, 30), depth=0.78, soft=3.0, holes=True)
    if agent_pose is not None:
        cast(img, agent(0, 0, **agent_pose), agent_quad, depth=0.70, soft=4.5)
    return img, w, h


def P3(st):   # E1
    img, w, h = window_panel("P3", st, (520, 820), [(40, 120), (330, 150), (320, 640), (30, 650)],
                             dict(face=1, glove=True), [(380, 70), (720, 60), (720, 790), (390, 790)],
                             dict(face=-1, scale=1.0, legs=(6, -6), sh=8, el=20, tilt=-2, pencil_deg=190))
    if st.get("lit", 1.0) >= 0.5:
        balloon(img, ["Pardon me —", "have you the", "right time?"], BCAP, (300, 480),
                (190, 300), 4231, tail_w=0.22)
    return img


def P4(st):   # E2
    x0, y0, x1, y1 = BOXES["P4"]
    w, h = x1 - x0, y1 - y0
    lamp = (-120, h + 40)
    img = wall(w, h, x0, y0, lamp, wains=h - 190, lit=st.get("lit", 1.0), spread=1.2)
    if st.get("lit", 1.0) < 0.5:
        return img
    wall_clock(img, w - 190, 190, 110, 4, 10, 6, lamp)
    a = agent(0, 0, face=1, scale=1.0, sh=6, el=16, tilt=-26, pencil_deg=190, lean=-3)
    cast(img, a, [(40, 130), (380, 150), (330, h + 40), (20, h + 30)], depth=0.70, soft=4.5)
    balloon(img, ["Ten past four,", "by the clock."], BCAP, (360, 560), (210, 250), 4241, tail_w=0.24)
    return img


def P5(st):   # E3
    img, w, h = window_panel("P5", st, (480, 820), [(50, 120), (340, 150), (330, 640), (40, 650)],
                             dict(face=-1, tilt=-6), [(370, 80), (690, 70), (690, 790), (380, 790)],
                             dict(face=-1, scale=1.0, legs=(10, -8), sh=4, el=10, tilt=2, pencil_deg=190))
    if st.get("lit", 1.0) >= 0.5:
        balloon(img, ["Much", "obliged!"], BCAP, (300, 460), (210, 330), 4251, tail_w=0.26)
    return img


def cupboard_lit(img, cx0, cy0, cw, chh, open_deg, key_scale, seed):
    c, ins = cupboard(cx0, cy0, cw, chh, open_deg=open_deg)
    object_shadow(img, [s for s in c if s.role != "door"], 22, -8, depth=0.4)
    solid(img, [s for s in c if s.role not in ("door", "shelf")], WOOD)
    if ins is not None:
        ix0, iy0, ix1, iy1 = ins
        r = np.zeros(img.shape[:2], np.uint8)
        cv2.rectangle(r, (int(ix0), int(iy0)), (int(ix1), int(iy1)), 255, -1)
        comp(img, r, INSIDE)
        solid(img, [s for s in c if s.role == "shelf"], WOOD * 0.8)
        kx, ky = (ix0 + ix1) / 2, iy0 + (iy1 - iy0) * 0.47
        hook(img, kx, ky - 723 * key_scale / 2 - 10)
        brass_key(img, kx, ky, key_scale, deg=0)
        paper_card(img, kx + 66 * key_scale / 0.5, ky + 150 * key_scale / 0.5, ["SERVICE"], 24, seed, tilt=8)
        solid(img, [s for s in c if s.role == "door"], WOOD * 1.08)
    return c, ins


def P6(st):   # E4
    x0, y0, x1, y1 = BOXES["P6"]
    w, h = x1 - x0, y1 - y0
    lamp = (-300, h + 80)
    img = wall(w, h, x0, y0, lamp, wains=h - 220, lit=st.get("lit", 1.0), spread=1.3)
    if st.get("lit", 1.0) < 0.5:
        return img
    od = st.get("open", 112)
    cupboard_lit(img, 390, 200, 360, 560, od, 0.50, 4261)
    # his reaching arm: its shadow falls across the cupboard and the wall, hand at the door's edge
    a = agent(0, 0, face=1, scale=1.0, sh=70 + 14 * (od / 112), el=-6, wr=0, pencil_deg=200, tilt=2, lean=6)
    cast(img, a, [(-40, 170), (470, 250), (420, h + 110), (-100, h + 110)], depth=0.66, soft=5.0)
    return img


def P7(st):   # E5
    x0, y0, x1, y1 = BOXES["P7"]
    w, h = x1 - x0, y1 - y0
    lamp = (-200, h + 60)
    img = wall(w, h, x0, y0, lamp, wains=h - 220, lit=st.get("lit", 1.0), spread=1.25)
    if st.get("lit", 1.0) < 0.5:
        return img
    cupboard_lit(img, 120, 330, 300, 470, 112, 0.40, 4271)
    sd = service_door(w - 250, 170, 220, h - 170)
    object_shadow(img, sd, 20, 0, depth=0.35)
    furn(img, sd, WOOD_D)
    paper_card(img, w - 250 + 110, 220, ["SERVICE"], 30, 4272, tilt=0)
    pd = st.get("pencil", 1.0)
    a = agent(0, 0, face=-1, scale=1.0, sh=40 * pd, el=128 * pd, wr=-14 * pd, pencil_deg=90 + 110 * (1 - pd), tilt=-4, lean=-2)
    cast(img, a, [(500, 170), (860, 150), (860, h + 40), (510, h + 50)], depth=0.72, soft=4.5)
    if st.get("line", True):
        balloon(img, ["Well, here I am...", "and what for?"], BCAP, (290, 150), (600, 270), 4273, tail_w=0.20)
    return img


PANELS = [("P1", P1), ("P2", P2), ("P3", P3), ("P4", P4), ("P5", P5), ("P6", P6), ("P7", P7)]


def build(state=None):
    state = state or {}
    page = SHEET.copy()
    for k, fn in PANELS:
        x0, y0, x1, y1 = BOXES[k]
        page[y0:y1, x0:x1] = fn(state.get(k, {}))
    frame_border(page, list(BOXES.values()), w=12, seed=4290)
    return page


if __name__ == "__main__":
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        dark = {"lit": 0.2}
        seq = []
        for k in range(1, 8):   # the lamps come on panel by panel; in P2 the shadow walks, in P6 the door swings
            st = {key: (dark if i >= k else {}) for i, (key, _) in enumerate(PANELS)}
            if k == 2:
                st["P2"] = {"walk": 0.0}
            if k == 6:
                st["P6"] = {"open": 40}
            if k == 7:
                st["P7"] = {"pencil": 0.0, "line": False}
            seq.append(st)
        seq.append({})
        frames = []
        for st in seq:
            p = np.clip(np.round(build(st)), 0, 255).astype(np.uint8)
            pen99.folio(p, N, TITLE)
            frames.append(np.asarray(Image.fromarray(p).resize((960, 1242), Image.LANCZOS)))
        save_beats(N, frames)
