"""SCION #2 Reiniger articulated shadow theatre, beat S2d (the swallow), 3.0 s = 72 frames at 24 fps, on twos.
Jointed card puppets posed by FK (pinned joints, angle limits), backlit warm paper (perspective mark: his
account), multiplane far plane = the lounge window blinds of the same V0 print, thresholded and softened.
The box silhouette uses box-spec proportions (w, body 0.30w, lid hinged at back) with the ring standing
at 0.50w in the slit. Exposure sheet + assertions are written by expose()."""
import numpy as np, cv2, math, json
from PIL import Image, ImageDraw
import box as B
SRC = "/home/user/bolas/paeleo/scion/oulipo/films/sources/monsieur-ripois/"
W, H, S = 720, 540, 3
INK = np.array([28, 23, 19], np.float32)                    # #1c1713
LIMITS = {"m_front_upper": (100, 160), "m_front_fore": (-40, 190), "m_back_upper": (66, 80), "m_back_fore": (196, 210),
          "w_upper": (30, 95), "w_fore": (-20, 50), "m_torso": (-12, 2)}
BW = 34.0                                                    # box width in screen px

def _paper(seed=1954):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - 380) / 470) ** 2 + ((yy - 250) / 360) ** 2)
    lum = np.clip(1.0 - 0.55 * r ** 1.8, 0.35, 1.0)
    base = np.array([226, 214, 196], np.float32)
    fib = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 0.9) * 3.5
    fib += cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 7) * 5
    p = base[None, None] * lum[..., None] + fib[..., None]
    # far plane: the window blinds of the V0 lounge, behind the paper (out of focus, faint)
    v0 = np.array(Image.open(SRC + "8d04830.jpg").convert("L"))
    win = cv2.resize(v0[120:470, 840:1010], (150, 300))
    far = cv2.GaussianBlur((win < 120).astype(np.float32), (0, 0), 2.4) * 0.22
    e = np.minimum.reduce([np.linspace(0, 1, 150)[None, :].repeat(300, 0), np.linspace(1, 0, 150)[None, :].repeat(300, 0),
                           np.linspace(0, 1, 300)[:, None].repeat(150, 1), np.linspace(1, 0, 300)[:, None].repeat(150, 1)]) * 5
    far *= np.clip(e, 0, 1)
    p[60:360, 520:670] *= (1 - far[..., None])
    return np.clip(p, 0, 255)
PAPER = _paper()

def limb(p0, ang, L, w0, w1):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang)); nx, ny = -s, c
    x0, y0 = p0; x1, y1 = x0 + c * L, y0 + s * L
    return [(x0 + nx * w0, y0 + ny * w0), (x1 + nx * w1, y1 + ny * w1), (x1 - nx * w1, y1 - ny * w1), (x0 - nx * w0, y0 - ny * w0)], (x1, y1)

def rot(pts, piv, ang):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(piv[0] + (x - piv[0]) * c - (y - piv[1]) * s, piv[1] + (x - piv[0]) * s + (y - piv[1]) * c) for x, y in pts]

def ss(pts): return [(x * S, y * S) for x, y in pts]

def lerp(a, b, x): return a + (b - a) * x
def sm(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)

def pose(f):
    """exposure sheet: f = local frame (0..71). Drawn on twos: f2 = even frame."""
    f2 = f - f % 2
    t = f2 / 24.0
    P = {}
    # torso turn: ~10° away from her as he draws the box in, then back as he hands it over
    P["m_torso"] = lerp(0, -10, sm((t - 0.20) / 0.25)) * (1 - sm((t - 0.62) / 0.50))
    # near (front) arm: offering (118/186) -> drawn in to the chest (120/-23) -> extended to her (152/182)
    if t < 0.62:
        k = sm((t - 0.25) / 0.20)
        P["m_front_upper"], P["m_front_fore"] = lerp(118, 120, k), lerp(186, 337, k) - (360 if k > 0 else 0) * 0 
        P["m_front_fore"] = lerp(186, 337, k) if lerp(186, 337, k) <= 190 else lerp(186, 337, k) - 360
        P["draw_in"] = k
    else:
        k = sm((t - 0.62) / 0.36)
        P["m_front_upper"], P["m_front_fore"] = lerp(120, 152, k), lerp(-23, -178, k) + 360 * (k > 0.86) * 0
        P["m_front_fore"] = lerp(337, 182, k) if lerp(337, 182, k) <= 190 else lerp(337, 182, k) - 360
        P["draw_in"] = 1 - k
    # far arm behind his back: the hidden hand rests at the chest; only the elbow moves, +6° in the swallow (16.9-17.25 s)
    P["m_back_upper"] = 70 + 6 * sm((t - 0.42) / 0.30) * (1 - sm((t - 1.0) / 0.5))
    P["m_back_fore"] = 203
    # lid: open (−95°) -> closed while it goes in (frames ~7-15)
    P["lid"] = -95 * (1 - sm((t - 0.30) / 0.32))
    # her arm: waiting palm, reaches as he hands it over, then takes the box down to her lap
    if t < 1.2:
        P["w_upper"], P["w_fore"] = 62, -12
    elif t < 1.75:
        k = sm((t - 1.2) / 0.55); P["w_upper"], P["w_fore"] = lerp(62, 40, k), lerp(-12, -4, k)
    else:
        k = sm((t - 1.95) / 0.65); P["w_upper"], P["w_fore"] = lerp(40, 85, k), lerp(-4, 25, k)
    P["holder"] = "him" if t < 1.75 else "her"
    P["earring"] = 3.0 * math.sin(2 * math.pi * (t / 0.9)) * math.exp(-t * 1.2) + (4 * math.sin(2 * math.pi * (t - 1.75) / 0.8) * math.exp(-(t - 1.75) * 2) if t > 1.75 else 0)
    for k_, (lo, hi) in LIMITS.items():
        if k_ in P: P[k_] = float(min(hi, max(lo, P[k_])))
    return P

def draw(P):
    """returns (alpha mask float HxW, dict of part masks for assertions)"""
    sil = Image.new("L", (W * S, H * S), 0); d = ImageDraw.Draw(sil)
    parts = {}
    def part(name):
        im = Image.new("L", (W * S, H * S), 0); parts[name] = im; return ImageDraw.Draw(im)
    # stage: floor rail with punched scallops, lamp, door frame (edge), wing chair
    d.rectangle([0, 470 * S, W * S, H * S], fill=255)
    for k in range(30): d.ellipse(ss([(10 + k * 25 - 4, 466), (10 + k * 25 + 4, 474)]), fill=0)
    d.polygon(ss([(448, 250), (452, 250), (452, 470), (448, 470)]), fill=255)
    d.polygon(ss([(420, 205), (480, 205), (492, 252), (408, 252)]), fill=255)
    d.rectangle(ss([(412, 222), (488, 226)]), fill=0)
    d.polygon(ss([(432, 462), (468, 462), (458, 470), (442, 470)]), fill=255)
    d.polygon(ss([(690, 95), (712, 95), (712, 470), (690, 470)]), fill=255)
    d.polygon(ss([(640, 80), (720, 80), (720, 96), (640, 96)]), fill=255)
    cx, cy = 150, 360
    k = 0.8
    def T(pts, ox, oy, ang=0, piv=None):
        q = [(ox + x * k, oy + y * k) for x, y in pts]
        return rot(q, piv, ang) if piv else q
    d.polygon(ss(T([(-74, -190), (-54, -204), (-34, -196), (-26, -50), (-70, -40), (-84, -120)], cx, cy)), fill=255)
    d.polygon(ss(T([(-80, -44), (84, -52), (92, -30), (86, 6), (-84, 10)], cx, cy)), fill=255)
    for lx in (-76, 76): d.polygon(ss(T([(-5, 0), (5, 0), (7, 138), (-3, 138)], cx + lx * k, cy + 8)), fill=255)
    for j in range(6): d.ellipse(ss([(cx - 47 + j * 1.6 - 3, cy - 144 + j * 19 - 3), (cx - 47 + j * 1.6 + 3, cy - 144 + j * 19 + 3)]), fill=0)
    # aunt
    d.polygon(ss(T([(-16, 0), (30, 0), (24, -30), (18, -58), (30, -92), (26, -112), (6, -124), (-14, -120), (-20, -92), (-12, -60), (-18, -28)], cx + 8, cy - 56)), fill=255)
    d.polygon(ss(T([(-30, 6), (40, -6), (96, -2), (108, 14), (104, 40), (100, 232), (124, 240), (126, 248), (82, 250), (76, 60), (40, 46), (-26, 44)], cx + 3, cy - 56)), fill=255)
    nk = (cx + 18, cy - 152)
    d.polygon(ss(T([(-7, 0), (7, 0), (9, -30), (-5, -30)], *nk)), fill=255)
    d.polygon(ss(T([(-16, -28), (-4, -30), (8, -36), (14, -46), (20, -50), (16, -54), (19, -60), (16, -68), (12, -78), (0, -86), (-14, -84), (-22, -72), (-22, -50)], *nk)), fill=255)
    for (dx, dy, r) in ((-18, -84, 17), (-6, -96, 11)):
        d.ellipse(ss([(nk[0] + dx * k - r * k, nk[1] + dy * k - r * k), (nk[0] + dx * k + r * k, nk[1] + dy * k + r * k)]), fill=255)
    # earring: pendulum (secondary dynamics) from the ear lobe
    ear = (nk[0] - 2 * k, nk[1] - 40 * k); a = math.radians(90 + P["earring"]); L = 12 * k
    drop = (ear[0] + math.cos(a) * L, ear[1] + math.sin(a) * L)
    d.line(ss([ear, drop]), fill=255, width=2 * S)
    d.ellipse(ss([(drop[0] - 4, drop[1] - 4), (drop[0] + 4, drop[1] + 4)]), fill=255)
    d.ellipse(ss([(drop[0] - 1.5, drop[1] - 1.5), (drop[0] + 1.5, drop[1] + 1.5)]), fill=0)
    shw = (cx + 24, cy - 141)
    ua, el = limb(shw, P["w_upper"], 43 * k / 0.8 * 0.8, 7, 6); fa, wr = limb(el, P["w_fore"], 48, 6, 4)
    d.polygon(ss(ua), fill=255); d.polygon(ss(fa), fill=255)
    palm = rot([(wr[0], wr[1] - 4), (wr[0] + 18, wr[1] - 7), (wr[0] + 21, wr[1] - 3), (wr[0] + 11, wr[1] + 3), (wr[0], wr[1] + 4)], wr, P["w_fore"])
    d.polygon(ss(palm), fill=255)
    # the visitor: hip pivot, torso turn
    hx, hy = 372, 345
    hip = (hx, hy + 10)
    for Lg in ([(-26, 0), (4, 0), (0, 95), (-6, 150), (-44, 160), (-46, 154), (-24, 148), (-26, 95)], [(0, 0), (26, 0), (28, 95), (26, 150), (12, 160), (-8, 158), (4, 150), (2, 95)]):
        d.polygon(ss(T(Lg, hx, hy)), fill=255)
    tor = P["m_torso"]
    jacket = rot(T([(-36, 26), (32, 26), (34, -10), (30, -92), (24, -142), (8, -156), (-18, -156), (-30, -142), (-40, -100), (-38, -40)], hx, hy), hip, tor)
    d.polygon(ss(jacket), fill=255)
    dt = part("torso"); dt.polygon(ss(jacket), fill=255)
    d.polygon(ss(rot(T([(-40, -112), (-30, -108), (-36, -100)], hx, hy), hip, tor)), fill=0)
    nm = rot([(hx - 5, hy - 123)], hip, tor)[0]
    head = rot(T([(-8, 0), (8, 0), (8, -22), (-6, -22)] + [], *nm), nm, tor)
    d.polygon(ss(head), fill=255)
    hm = [(-2, -16), (12, -18), (16, -32), (18, -52), (14, -64), (2, -76), (-10, -80), (-20, -72), (-22, -62), (-21, -56), (-30, -46), (-23, -42), (-24, -36), (-28, -30), (-23, -27), (-24, -20), (-16, -12)]
    d.polygon(ss(rot(T(hm, *nm), nm, tor)), fill=255)
    d.polygon(ss(rot(T([(-22, -66), (-14, -84), (6, -86), (18, -66), (10, -74)], *nm), nm, tor)), fill=255)
    # far arm (behind the back): the hidden hand
    sb = rot([(hx + 16, hy - 109)], hip, tor)[0]
    ua, elb = limb(sb, P["m_back_upper"] + tor, 46, 8, 7); fa, wrb = limb(elb, P["m_back_fore"] + tor, 40, 7, 5)
    d.polygon(ss(ua), fill=255); d.polygon(ss(fa), fill=255)
    d.ellipse(ss([(elb[0] - 7, elb[1] - 7), (elb[0] + 7, elb[1] + 7)]), fill=255)
    dh = part("far_hand"); hand_b = [(wrb[0] - 6, wrb[1] - 5), (wrb[0] + 2, wrb[1] - 6), (wrb[0] + 3, wrb[1] + 5), (wrb[0] - 6, wrb[1] + 5)]
    dh.polygon(ss(hand_b), fill=255); d.polygon(ss(hand_b), fill=255)
    # near arm (FK: shoulder -> elbow -> wrist), holding the box
    sf = rot([(hx - 14, hy - 110)], hip, tor)[0]
    ua, el = limb(sf, P["m_front_upper"] + tor, 51, 9, 7); fa, wrf = limb(el, P["m_front_fore"] + tor, 48, 7, 6)
    d.polygon(ss(ua), fill=255); d.polygon(ss(fa), fill=255)
    hand_f = rot([(wrf[0], wrf[1] - 6), (wrf[0] - 13, wrf[1] - 6), (wrf[0] - 16, wrf[1]), (wrf[0] - 8, wrf[1] + 6), (wrf[0], wrf[1] + 6)], wrf, P["m_front_fore"] - 180 + tor)
    d.polygon(ss(hand_f), fill=255)
    # the box (box-spec proportions): body w x 0.30w, lid 0.08w hinged at the back top edge
    if P["holder"] == "him":
        off = lerp(-BW - 4, -BW / 2, P.get("draw_in", 0))
        bx0, by0 = wrf[0] + off, wrf[1] - 0.30 * BW * 0.5
    else:
        # hand-off: the box keeps the offset it had to her wrist at the hand-off frame, then rides her hand
        if "_off" not in HANDOFF:
            Ph = pose(HANDOFF_F); Ph["holder"] = "him"; _, _, ih = draw(Ph); HANDOFF["_off"] = (ih["box_x0"] - ih["wr_her"][0], ih["box_y0"] - ih["wr_her"][1])
        bx0, by0 = wr[0] + HANDOFF["_off"][0], wr[1] + HANDOFF["_off"][1]
    db = part("box")
    body = [(bx0, by0), (bx0 + BW, by0), (bx0 + BW, by0 + 0.30 * BW), (bx0, by0 + 0.30 * BW)]
    for dd in (d, db): dd.polygon(ss(body), fill=255)
    hinge = (bx0 + BW, by0)
    lid = rot([(bx0, by0 - 0.08 * BW), (bx0 + BW, by0 - 0.08 * BW), (bx0 + BW, by0), (bx0, by0)], hinge, P["lid"])
    for dd in (d, db): dd.polygon(ss(lid), fill=255)
    ring_c = None
    if P["lid"] < -40:
        # lid's mirror lining punched out (it glows), and the ring standing in the slit at 0.50w
        inner = rot([(bx0 + 3, by0 - 0.08 * BW + 1.0), (bx0 + BW - 3, by0 - 0.08 * BW + 1.0), (bx0 + BW - 3, by0 - 0.6), (bx0 + 3, by0 - 0.6)], hinge, P["lid"])
        lidbig = rot([(bx0, by0 - 0.62 * BW), (bx0 + BW, by0 - 0.62 * BW), (bx0 + BW, by0), (bx0, by0)], hinge, 0)
        ring_c = (bx0 + B.SLOT["cx"] * BW, by0 - 4.5)
        r_o, r_i = 5.5, 3.2
        for dd in (d, db):
            dd.ellipse(ss([(ring_c[0] - r_o, ring_c[1] - r_o), (ring_c[0] + r_o, ring_c[1] + r_o)]), fill=255)
        d.ellipse(ss([(ring_c[0] - r_i, ring_c[1] - r_i), (ring_c[0] + r_i, ring_c[1] + r_i)]), fill=0)
        d.ellipse(ss([(ring_c[0] - 1.6, ring_c[1] - r_o - 3.0), (ring_c[0] + 1.6, ring_c[1] - r_o + 0.2)]), fill=255)   # the stone
    # rivets: pin-holes of light at the joints (pinned, not detached)
    for p_ in (sf, el, shw, sb):
        d.ellipse(ss([(p_[0] - 1.1, p_[1] - 1.1), (p_[0] + 1.1, p_[1] + 1.1)]), fill=0)
    a = np.array(sil.resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
    pm = {n: np.array(im.resize((W, H), Image.BILINEAR)) > 127 for n, im in parts.items()}
    info = {"ring_c": ring_c, "box_x0": bx0, "box_y0": by0, "box_w": BW, "elbow": elb, "wr_front": wrf, "wr_her": wr}
    return a, pm, info

HANDOFF = {}
HANDOFF_F = 42          # 1.75 s, on twos

def frame(f):
    P = pose(f)
    a, pm, info = draw(P)
    halo = cv2.GaussianBlur(a, (0, 0), 1.8)
    img = PAPER * (1 - a[..., None]) + INK * a[..., None]
    img *= (1 - 0.14 * np.clip(halo - a, 0, 1))[..., None]
    return np.clip(img, 0, 255).astype(np.uint8), P, pm, info

def expose(n=72):
    sheet = []
    for f in range(n):
        P = pose(f); a, pm, info = draw(P)
        box_vis = int((pm["box"] & ~pm["torso"]).sum())
        far_out = int((pm["far_hand"] & ~pm["torso"]).sum())
        sheet.append({"frame": f, **{k: (round(v, 2) if isinstance(v, float) else v) for k, v in P.items()},
                      "box_px_outside_torso": box_vis, "far_hand_px_outside_torso": far_out,
                      "ring_visible": info["ring_c"] is not None})
    return sheet
