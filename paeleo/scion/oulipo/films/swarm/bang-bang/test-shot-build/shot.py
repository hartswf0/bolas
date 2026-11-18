# BB-08 test shot ("the stall"), film frames f480-f624 (20.0-26.0 s), rendered through films/kit.py.
#   cd films && python3 -I swarm/bang-bang/test-shot-build/shot.py [--stills k ...]
# Planche 2, panel 2 of a cream storyboard sheet.  Cut-paper puppets from PD engravings (pieces made by cut.py),
# pinned and animated frame by frame on 2s from an exposure sheet; the legs are a damped pendulum on the hip pin;
# the bird's slip is written on in a handmade pen hand and corrected at f528.
import sys, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
FILMS = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, FILMS)
sys.path.insert(0, os.path.join(HERE, "..", "proposals"))
from pathlib import Path
import numpy as np, cv2
from PIL import Image
import kit
import pen

SRC = os.path.join(FILMS, "sources", "bang-bang", "test-shot")
PCS = os.path.join(SRC, "pieces")
OUTDIR = Path(os.path.join(FILMS, "swarm", "bang-bang"))
F0, F1 = 480, 624                      # film frames covered by the shot
PAPER = np.array((242, 228, 212), np.float32)
PANEL = np.array((228, 216, 202), np.float32)
MARGIN = np.array((234, 220, 203), np.float32)
GHOST = np.array((206, 195, 185), np.float32)
PENINK = (50, 41, 34)
GRAPH = (112, 106, 102)
SHADOW = np.array((150, 130, 110), np.float32)
BRASS = (176, 138, 62)

# ------------------------------------------------------------------ page geometry (page px)
PW, PH = 1400, 1800
PX, PWID, PHT, GAP = 80, 700, 483, 44
PANELS = [(PX, 60 + i * (PHT + GAP)) for i in range(3)]
P2 = PANELS[1]
CY0, CY1 = 470, 1210                   # the band of the page the camera ever sees
GROUND = 440                           # ground line, panel-2 local v
POST = (70, 362)                       # fence-post top, panel-2 local


def paper(w, h, seed, tone):
    r = np.random.default_rng(seed)
    lo = cv2.resize(r.normal(0, 1, (h // 50 + 2, w // 50 + 2)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    mid = cv2.resize(r.normal(0, 1, (h // 7 + 2, w // 7 + 2)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    fib = cv2.GaussianBlur(r.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 0.7)
    k = 1 + 0.010 * lo + 0.006 * mid + 0.010 * fib
    return np.asarray(tone, np.float32)[None, None, :] * k[..., None]


def comp(dst, rgb, a):
    a = a[..., None]
    dst *= (1 - a); dst += rgb * a


# ------------------------------------------------------------------ the static sheet
def build_sheet():
    pg = paper(PW, PH, 11, PAPER)
    xx = np.arange(PW, dtype=np.float32)
    mg = np.clip((60 - xx) / 40, 0, 1)[None, :, None]          # the left margin is a touch duskier, as in the reference
    pg = pg * (1 - mg) + (pg / PAPER * MARGIN) * mg
    # facing page show-through: the previous planche's commentary, mirrored, faint
    gk = pen.Ink(PW, PH, 301); rg = np.random.default_rng(302)
    lines = ["Il s'est fait une aile en papier.", "Le papier plie quand il veut.", "Le mien, quand je veux.  ... pof.",
             "Ensuite, un moulin à élastique.", "Il le lâche, et le moulin monte", "tout seul. Lui reste en bas.",
             "C'est sage : il faut bien", "quelqu'un pour regarder.  clac."]
    for i, s in enumerate(lines):
        pen.hand(gk, s, 120 + (i % 2) * 30, 170 + i * 150 + (i // 3) * 90, size=1.0, width=1.8, rng=rg)
    for i in range(3):
        y0 = 70 + i * 540
        if i == 1: continue
        gk.line([(860, y0), (1330, y0 + 4)], width=1.6); gk.line([(1330, y0 + 4), (1326, y0 + 470)], width=1.6)
        gk.line([(1326, y0 + 470), (858, y0 + 466)], width=1.6); gk.line([(858, y0 + 466), (860, y0)], width=1.6)
    gc = cv2.GaussianBlur(gk.coverage()[:, ::-1], (0, 0), 2.4) * 0.30
    comp(pg, GHOST, gc)
    # panel interiors (duskier card) and the pen frames + punched dots
    k = pen.Ink(PW, PH, 303)
    for (x0, y0) in PANELS:
        inner = np.zeros((PH, PW), np.float32); inner[y0 + 2:y0 + PHT - 2, x0 + 2:x0 + PWID - 2] = 1
        comp(pg, pg / PAPER * PANEL, inner)
        k.line([(x0, y0), (x0 + PWID, y0 + 1)], width=2.0, jit=0.9); k.line([(x0 + PWID, y0 + 1), (x0 + PWID + 1, y0 + PHT)], width=2.0, jit=0.9)
        k.line([(x0 + PWID + 1, y0 + PHT), (x0 - 1, y0 + PHT - 1)], width=2.0, jit=0.9); k.line([(x0 - 1, y0 + PHT - 1), (x0, y0)], width=2.0, jit=0.9)
        k.dot(x0 + 24, y0 + 22, 6.5)
    # panel 1 (BB-07, above): its ground and hill, still drawn; panel 3 is still blank
    a1 = PANELS[0]
    k.curve([(a1[0] + 8, a1[1] + GROUND), (a1[0] + 300, a1[1] + GROUND + 2), (a1[0] + 520, a1[1] + GROUND - 30), (a1[0] + 692, a1[1] + GROUND - 80)], width=1.7)
    # panel 2 set: ground line with sparse grass ticks, the hill he ran down (right), a fence post (left)
    ox, oy = P2
    k.curve([(ox + 6, oy + GROUND), (ox + 220, oy + GROUND + 2), (ox + 470, oy + GROUND - 2), (ox + 600, oy + GROUND - 22), (ox + 694, oy + GROUND - 52)], width=1.8)
    rr = np.random.default_rng(304)
    for u in rr.uniform(20, 680, 26):
        gy = GROUND - max(0, (u - 470) * 0.23) if u > 470 else GROUND
        k.line([(ox + u, oy + gy + 1), (ox + u + rr.uniform(-4, 4), oy + gy - rr.uniform(5, 11))], width=1.0, jit=0.4)
    for dx in (-5, 5):
        k.line([(ox + POST[0] + dx, oy + POST[1] + 2), (ox + POST[0] + dx * 1.2, oy + GROUND + 1)], width=1.7, jit=0.6)
    k.line([(ox + POST[0] - 8, oy + POST[1] + 1), (ox + POST[0] + 8, oy + POST[1])], width=1.7, jit=0.4)
    k.line([(ox + POST[0] - 8, oy + POST[1] + 40), (ox + POST[0] - 60, oy + POST[1] + 44)], width=1.3, jit=0.6)   # a rail end
    pg = pen.put_ink(pg, k.coverage(), ink=PENINK, seed=305)
    # graphite: board header above panel 2, vertical margin note beside it
    g = pen.Ink(PW, PH, 306)
    pen.hand(g, "BB-08   21,0 - 24,0 s   le décrochage", P2[0] + 46, P2[1] - 12, size=0.52, width=0.9, rng=np.random.default_rng(307))
    pen.hand(g, "BB-07   18,0 - 21,0 s   l'élan", PANELS[0][0] + 46, PANELS[0][1] - 12, size=0.52, width=0.9, rng=np.random.default_rng(308))
    pen.hand(g, "BB-09   24,0 - 27,5 s   la chute", PANELS[2][0] + 46, PANELS[2][1] - 12, size=0.52, width=0.9, rng=np.random.default_rng(309))
    vg = pen.Ink(420, 60, 310)
    pen.hand(vg, "BB-08  f504 - 576", 10, 40, size=0.55, width=0.9, rng=np.random.default_rng(311))
    vc = np.rot90(vg.coverage(), 1)                     # reads bottom-to-top, along the margin
    gc = g.coverage(); y0 = P2[1] + 60; gc[y0:y0 + vc.shape[0], 30:30 + vc.shape[1]] = np.maximum(gc[y0:y0 + vc.shape[0], 30:30 + vc.shape[1]], vc)
    pg = pen.put_ink(pg, gc * 0.75, ink=GRAPH, seed=312, bleed=0.4)
    return pg


# ------------------------------------------------------------------ pieces and rig
rig = json.load(open(os.path.join(PCS, "rig.json")))
GS, BS = 0.46, 0.145


def load(name, s, mirror=False):
    im = cv2.imread(os.path.join(PCS, name + ".png"), cv2.IMREAD_UNCHANGED)[..., [2, 1, 0, 3]].astype(np.float32)
    w = int(round(im.shape[1] * s)); h = int(round(im.shape[0] * s))
    a = cv2.resize(im[..., 3] / 255, (w, h), interpolation=cv2.INTER_AREA)
    rgb = cv2.resize(im[..., :3] * (im[..., 3:] / 255), (w, h), interpolation=cv2.INTER_AREA)   # premultiplied
    pv = np.array(rig["pieces"][name]["pivot"], np.float32) * s
    pp = np.array(rig["pieces"][name].get("parent_pivot", rig["pieces"][name]["pivot"]), np.float32) * s
    if mirror:
        a, rgb = a[:, ::-1].copy(), rgb[:, ::-1].copy(); pv[0] = w - 1 - pv[0]
    return {"a": a, "rgb": rgb, "pv": pv, "pp": pp, "w": w}


glider, legs = load("glider", GS), load("legs", GS)
cbody, chead, cwing = load("crow_body", BS, True), load("crow_head", BS, True), load("crow_wing", BS, True)
for c in (chead, cwing):
    c["pp"][0] = cbody["w"] - 1 - c["pp"][0]


def M(piece, P, ang):
    a = math.radians(ang); c, s = math.cos(a), math.sin(a)
    R = np.array([[c, -s], [s, c]], np.float32)
    t = np.asarray(P, np.float32) - R @ piece["pv"]
    return np.hstack([R, t[:, None]])


def apply(Mx, p):
    return Mx[:, :2] @ np.asarray(p, np.float32) + Mx[:, 2]


# ------------------------------------------------------------------ exposure sheet (panel-2 local coords, film frame f)
def smooth(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def glider_pose(f):
    """hip (u,v) and pitch theta (deg, nose-up +).  x stops at f530; theta 5->35 over f504-f540 (ease-in:
    15 deg at f528); hang f540-f554 exactly still; tail-first slide from f556."""
    v0, T = 7.0, 26.0
    if f <= 504:
        u = 330 + v0 * T * (2 / 3) + v0 * (504 - f)
    elif f <= 530:
        s = (f - 504) / T; u = 330 + v0 * T * (2 / 3) - v0 * T * (s - s ** 3 / 3)
    else:
        u = 330.0
    vv = 250 - 28 * smooth((f - 500) / 40)
    th = 5 + 30 * min(1.0, max(0.0, (f - 504) / 36)) ** 2.71
    if f > 556:
        d = f - 556
        u += 0.175 * d * d; vv += 0.06 * d * d; th = 35 - 9 * smooth(d / 50)
    return u, vv, th


def legs_sim(f_end=640, hold_forever=False):
    """Hip pin pendulum (SCION #41): phi'' = [-(g-a_y) sin phi + a_x cos phi]/L - c (phi' - theta'),
    semi-implicit Euler at 240 Hz; page px, 60 px/m.  Returns phi (deg, world, forward +) per film frame."""
    g, L, c = 9.81 * 60, 13.0, 4.2
    dt = 1 / 240.0; sub = 10
    pose = (lambda f: glider_pose(min(f, 554.0))) if hold_forever else glider_pose
    def pos(f):
        u, v, th = pose(f); return np.array([u, v]), math.radians(th)
    phi, w = 0.0, 0.0; out = {}
    f = 470.0; h = 1 / sub
    while f <= f_end + 1e-6:
        if abs(f - round(f)) < 1e-6:
            out[int(round(f))] = math.degrees(phi)
        p0, t0 = pos(f - h); p1, t1 = pos(f); p2, t2 = pos(f + h)
        acc = (p2 - 2 * p1 + p0) / (dt * dt); thd = (t2 - t0) / (2 * dt)
        al = (-(g - acc[1]) * math.sin(phi) + acc[0] * math.cos(phi)) / L - c * (w - thd)
        w += al * dt; phi += w * dt; f += h
    return out


PHI = legs_sim()
PHI_HOLD = legs_sim(700, hold_forever=True)


def bird_pose(f):
    """neck point (u,v), body angle, head angle, wing angle; None before it enters."""
    if f < 538:
        return None
    flap = [-85, -45, 5, -45][(int(f) // 2) % 4]
    if f <= 562:                                  # level flight past him, right to left, at his height
        s = (f - 538) / 24; u = 760 - 600 * s; v = 205 + 6 * math.sin(s * 6); return u, v, 0, 55, flap
    if f <= 568:                                  # the flare: nose up, wings spread forward, braking
        s = (f - 562) / 6; u = 160 - 55 * (1 - (1 - s) ** 2); v = 205 + 18 * s
        return u, v, 38 * smooth(s * 1.5), 55 - 15 * s, -95
    feet = np.array([600 - rig["pieces"]["crow_body"]["offset_src"][0], 585 - rig["pieces"]["crow_body"]["offset_src"][1]], np.float32) * BS
    feet[0] = cbody["w"] - 1 - feet[0]
    def at_post(ang, lift=0.0):
        Mx = M(cbody, (0, 0), ang); fp = apply(Mx, feet)
        return POST[0] - fp[0], POST[1] - lift - fp[1]
    if f <= 578:                                  # sink onto the post, wings still up, body levelling
        s = smooth((f - 568) / 10); ang = 38 * (1 - s)
        u1, v1 = at_post(ang, 0); u0, v0 = 105, 223
        return u0 + (u1 - u0) * s, v0 + (v1 - v0) * s, ang, 40 + 10 * s, -95 + 30 * s
    if f <= 590:                                  # wings fold, a small settle hop
        s = (f - 578) / 12; hop = 7 * math.sin(math.pi * min(1, s * 1.6)) if s < 0.62 else 0
        u1, v1 = at_post(-4 * math.sin(math.pi * s), hop)
        return u1, v1, -4 * math.sin(math.pi * s), 50, -65 + 65 * smooth(s * 2)
    u1, v1 = at_post(0); return u1, v1, 0, 50 + (8 if (int(f) // 12) % 2 else 0), 0


# ------------------------------------------------------------------ slips: torn cream paper, the bird's hand, revealed by time
def torn_slip(w, h, seed):
    r = np.random.default_rng(seed); m = np.zeros((h, w), np.float32)
    xs = np.arange(w)
    top = 6 + 5 * np.interp(xs, np.linspace(0, w, 24), r.normal(0, 0.6, 24)) + r.normal(0, 0.7, w)
    bot = h - 6 - 5 * np.interp(xs, np.linspace(0, w, 24), r.normal(0, 0.6, 24)) - r.normal(0, 0.7, w)
    for x in xs:
        m[int(max(0, top[x])):int(min(h, bot[x])), x] = 1
    m[:, :2] = 0; m[:, -2:] = 0
    rgb = paper(w, h, seed + 1, PAPER)
    rim = (cv2.dilate((1 - m).astype(np.uint8), np.ones((4, 4), np.uint8)) > 0) & (m > 0)
    rgb[rim] = np.minimum(255, rgb[rim] + 9)
    return rgb, cv2.GaussianBlur(m, (0, 0), 0.6)


def word_layers(w, h, items, seed):
    """items: (text, x, y, size, width, t0, t1).  Returns list of (coverage-of-word, bbox, t0, t1), one per word,
    each word written on left-to-right between its own start and end frame (rate by letters)."""
    out = []
    for j, (text, x, y, size, width, t0, t1) in enumerate(items):
        words = text.split(" "); total = sum(len(wd) + 1 for wd in words)
        letters = sum(len(wd) for wd in words); prev = np.zeros((h, w), np.float32); used = 0; done = 0
        for wd in words:
            used += len(wd) + 1
            lay = pen.Ink(w, h, seed + j)
            pen.hand(lay, text, x, y, size=size, width=width, rng=np.random.default_rng(seed * 10 + j), upto=(used - 0.5) / total)
            cov = lay.coverage(); wc = np.clip(cov - prev, 0, 1); prev = np.maximum(prev, cov)
            ys, xs = np.nonzero(wc > 0.05)
            a = t0 + (t1 - t0) * done / letters; done += len(wd); b = t0 + (t1 - t0) * done / letters
            if len(xs):
                out.append((wc, (xs.min(), xs.max() + 1), a, b))
    return out


def reveal(layers, f, w, h):
    cov = np.zeros((h, w), np.float32); xs = np.arange(w, dtype=np.float32)
    for wc, (x0, x1), a, b in layers:
        if f < a:
            continue
        if f >= b:
            cov = np.maximum(cov, wc); continue
        xe = x0 + (x1 - x0) * (f - a) / max(1e-6, b - a)
        cov = np.maximum(cov, wc * np.clip((xe - xs) / 3, 0, 1)[None, :])
    return cov


S5W, S5H = 236, 160
S5 = torn_slip(S5W, S5H, 401)
S5L = word_layers(S5W, S5H, [("Il lève le nez", 16, 52, 0.74, 1.35, 482, 509),
                             ("pour monter", 16, 128, 0.74, 1.35, 510, 527)], 41)
MONTER = S5L[-1]                                       # bbox of 'monter' on the slip
mx0, mx1 = MONTER[1]
S5FIX = word_layers(S5W, S5H, [("s'arrêter", mx0 - 6, 92, 0.64, 1.25, 531, 549)], 47)
strike = pen.Ink(S5W, S5H, 402); strike.line([(mx0 - 4, 121), (mx1 + 4, 116)], width=2.1, jit=0.5, press=0.3)
STRIKE = strike.coverage()
S5B = torn_slip(230, 150, 403)
S5BL = word_layers(230, 150, [("Moi aussi,", 16, 44, 0.72, 1.35, 553, 563),
                              ("quand je veux", 16, 88, 0.72, 1.35, 564, 586),
                              ("me poser.", 16, 130, 0.72, 1.35, 587, 602)], 43)
GLW, GLH = 260, 40
GLOSS = word_layers(GLW, GLH, [("he lifts his nose to stop", 6, 28, 0.42, 0.85, 556, 578)], 49)


def slip_rgba(base, layers, f, extra=None, strike_at=None):
    rgb, a = base; h, w = a.shape
    cov = reveal(layers, f, w, h)
    if extra is not None:
        cov = np.maximum(cov, reveal(extra, f, w, h))
    if strike_at is not None and f >= strike_at:
        xs = np.arange(w, dtype=np.float32); xe = mx0 - 4 + (mx1 - mx0 + 8) * min(1.0, (f - strike_at + 1) / 3)
        cov = np.maximum(cov, STRIKE * np.clip((xe - xs) / 3, 0, 1)[None, :])
    return pen.put_ink(rgb.copy(), cov, ink=PENINK, seed=int(f) // 4), a


# ------------------------------------------------------------------ board-artist annotations (ink A/B, graphite 35 deg arc)
def annotations():
    u, v, th = glider_pose(540)
    P = (P2[0] + u, P2[1] + v - CY0)
    Mg = M(glider, P, th)
    nose = apply(Mg, glider["pv"] + np.array([-170, -6], np.float32))
    wing = apply(Mg, glider["pv"] + np.array([150, 18], np.float32))
    W_, H_ = PW, CY1 - CY0
    ka = pen.Ink(W_, H_, 501); pen.hand(ka, "A", wing[0] + 12, wing[1] + 46, size=0.8, width=1.5, rng=np.random.default_rng(502))
    kb = pen.Ink(W_, H_, 503); pen.hand(kb, "B", nose[0] - 34, nose[1] - 6, size=0.8, width=1.5, rng=np.random.default_rng(504))
    gh = pen.Ink(W_, H_, 505)
    gh.line([(P[0] - 175, P[1]), (P[0] - 8, P[1])], width=0.9, jit=0.3, dash=7)         # the horizon through the pin
    R = 120
    gh.ellipse(P[0], P[1], R, R, a0=180, a1=180 + 35, width=0.9, jit=0.3)
    gt = pen.Ink(W_, H_, 506)
    pen.hand(gt, "35°", P[0] - R - 50, P[1] - 22, size=0.5, width=0.85, rng=np.random.default_rng(507))
    return ka.coverage(), kb.coverage(), gh.coverage(), gt.coverage(), P


ANN_A, ANN_B, ANN_ARC, ANN_35, HANG_P = annotations()
SHEET = build_sheet()
PANEL_MASK = np.zeros((CY1 - CY0, PW), np.float32)
PANEL_MASK[P2[1] + 3 - CY0:P2[1] + PHT - 3 - CY0, P2[0] + 3:P2[0] + PWID - 3] = 1
PANEL_MASK = cv2.GaussianBlur(PANEL_MASK, (0, 0), 0.7)


def put_piece(canvas, sh_acc, piece, Mx, height):
    Hc, Wc = canvas.shape[:2]
    a = cv2.warpAffine(piece["a"], Mx, (Wc, Hc), flags=cv2.INTER_LINEAR) * PANEL_MASK
    rgb = cv2.warpAffine(piece["rgb"], Mx, (Wc, Hc), flags=cv2.INTER_LINEAR) * PANEL_MASK[..., None]
    canvas *= (1 - a[..., None]); canvas += rgb
    dx, dy = 0.07 * height + 3, 0.10 * height + 4                 # shadow offset encodes height above the card
    Ms = Mx.copy(); Ms[0, 2] += dx; Ms[1, 2] += dy
    sa = cv2.warpAffine(piece["a"], Ms, (Wc, Hc), flags=cv2.INTER_LINEAR) * PANEL_MASK
    return np.maximum(sh_acc, sa), a


def brad(canvas, x, y, r):
    yy, xx = np.ogrid[:canvas.shape[0], :canvas.shape[1]]
    d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2)
    rim = np.clip(r + 1.2 - d, 0, 1); disc = np.clip(r - d, 0, 1)
    hi = np.clip(r * 0.45 - np.sqrt((xx - x + r * 0.35) ** 2 + (yy - y + r * 0.35) ** 2), 0, 1)
    comp(canvas, np.array((70, 56, 38), np.float32), rim * 0.9)
    comp(canvas, np.array(BRASS, np.float32), disc)
    comp(canvas, np.array((214, 186, 120), np.float32), hi)


LOG = {"frames": []}


def render_page(f):
    """The visible band of the sheet at film frame f (page px)."""
    fa = f - (f % 2)                                              # puppets on 2s
    can = SHEET[CY0:CY1].copy()
    # annotations, inked by the board artist once the pose is held
    xs = np.arange(PW, dtype=np.float32)
    if f >= 541:
        arc = ANN_ARC * min(1.0, (f - 541) / 8); comp(can, np.array(GRAPH, np.float32), arc * 0.7)
    if f >= 547:
        comp(can, np.array(GRAPH, np.float32), ANN_35 * 0.75 * min(1.0, (f - 547) / 4))
    if f >= 543:
        can = pen.put_ink(can, ANN_A * min(1.0, (f - 543) / 3), ink=PENINK, seed=9)
    if f >= 549:
        can = pen.put_ink(can, ANN_B * min(1.0, (f - 549) / 3), ink=PENINK, seed=10)
    # puppets
    sh = np.zeros(can.shape[:2], np.float32)
    u, v, th = glider_pose(fa); phi = PHI[fa]
    P = (P2[0] + u, P2[1] + v - CY0); height = GROUND - v
    Mg, Ml = M(glider, P, th), M(legs, P, phi)
    rel = phi - th
    lim = rig["pieces"]["legs"]["limits_deg"]
    drift = float(np.linalg.norm(apply(Mg, glider["pv"]) - apply(Ml, legs["pv"])))
    layer = can.copy()
    sh, _ = put_piece(layer, sh, legs, Ml, height)
    sh, _ = put_piece(layer, sh, glider, Mg, height)
    pin = (P[0], P[1])
    bp = bird_pose(fa); bird_log = None
    if bp:
        bu, bv, ba, ha, wa = bp
        Pb = (P2[0] + bu, P2[1] + bv - CY0)
        Mb = M(cbody, Pb, ba)
        neck = apply(Mb, cbody["pv"]); sho = apply(Mb, cwing["pp"])
        Mh = M(chead, neck, ba + ha); Mw = M(cwing, sho, ba + wa)
        bh = max(0.0, POST[1] + 40 - bv)
        sh, _ = put_piece(layer, sh, cbody, Mb, bh)
        sh, _ = put_piece(layer, sh, chead, Mh, bh)
        sh, _ = put_piece(layer, sh, cwing, Mw, bh)
        bird_log = {"neck_drift": float(np.linalg.norm(apply(Mh, chead["pv"]) - neck)),
                    "shoulder_drift": float(np.linalg.norm(apply(Mw, cwing["pv"]) - sho)), "wing": wa, "head": ha}
    # soft warm cast shadow under lifted pieces, then the pieces over it
    shb = cv2.GaussianBlur(sh, (0, 0), 5) * 0.26
    comp(can, SHADOW, shb)
    tmp = can.copy()
    for pc, Mx in [(legs, Ml), (glider, Mg)]:
        _, a = put_piece(tmp, sh * 0, pc, Mx, 0)
    if bp:
        for pc, Mx in [(cbody, Mb), (chead, Mh), (cwing, Mw)]:
            _, a = put_piece(tmp, sh * 0, pc, Mx, 0)
    can = tmp
    if 0 < pin[0] - P2[0] < PWID - 4:
        brad(can, pin[0], pin[1], 3.2)
    # slips in the right-hand column
    def place_slip(rgba, x, y, ang, lift):
        rgb, a = rgba; h, w = a.shape
        Mx = cv2.getRotationMatrix2D((w / 2, h / 2), ang, 1.0); Mx[0, 2] += x; Mx[1, 2] += y - CY0
        A = cv2.warpAffine(a, Mx, (PW, CY1 - CY0)); Rg = cv2.warpAffine(rgb * a[..., None], Mx, (PW, CY1 - CY0))
        Ms = Mx.copy(); Ms[0, 2] += 2 + lift; Ms[1, 2] += 3 + lift * 1.4
        S = cv2.GaussianBlur(cv2.warpAffine(a, Ms, (PW, CY1 - CY0)), (0, 0), 2.5 + lift * 0.5) * 0.24
        comp(can, SHADOW, S)
        can[:] = can * (1 - A[..., None]) + Rg
        return apply(Mx, (14, 18))
    if f >= F0:
        lift = max(0.0, 6 - 2 * (f - F0))
        pn = place_slip(slip_rgba(S5, S5L, f, S5FIX, strike_at=528), 806 - lift, 652 - lift * 2, 1.2, lift)
        brad(can, pn[0], pn[1], 4.2)
        gl = reveal(GLOSS, f, GLW, GLH)
        can[818 - CY0:818 - CY0 + GLH, 808:808 + GLW] = pen.put_ink(can[818 - CY0:818 - CY0 + GLH, 808:808 + GLW], gl * 0.75, ink=GRAPH, seed=13, bleed=0.4)
    if f >= 550:
        lift = max(0.0, 6 - 2 * (f - 550))
        pn = place_slip(slip_rgba(S5B, S5BL, f), 812 - lift, 872 - lift * 2, -1.6, lift)
        brad(can, pn[0], pn[1], 4.2)
    LOG["frames"].append({"f": int(f), "pose_f": int(fa), "hip_u": round(u, 2), "hip_v": round(v, 2), "theta": round(th, 2),
                          "phi": round(phi, 2), "rel": round(rel, 2), "rel_in_limits": bool(lim[0] <= rel <= lim[1]),
                          "hip_drift_px": round(drift, 4), "bird": bird_log})
    return can


def camera(f):
    s = smooth((f - 488) / 52)
    z = 0.85 + (0.94 - 0.85) * s
    cx = 605 + (560 - 605) * s; cy = 828
    return z, cx, cy


def frame_img(f):
    can = render_page(f)
    z, cx, cy = camera(f)
    Mx = np.array([[z, 0, 480 - z * cx], [0, z, 270 - z * (cy - CY0)]], np.float32)
    out = cv2.warpAffine(np.clip(can, 0, 255), Mx, (960, 540), flags=cv2.INTER_AREA if z < 1 else cv2.INTER_LINEAR, borderValue=tuple(float(c) for c in PAPER))
    return Image.fromarray(out.astype(np.uint8))


film = kit.Film("test-shot", seconds=(F1 - F0) / 24, boil=0, wobble=0)


@film.picture
def picture(t, ink):
    f = F0 + int(round(t * 24))
    ink.paste(frame_img(f))


AIR = os.path.join(SRC, "mia_9be990a5.wav")


@film.sound
def sound(mix):
    import wave
    w = wave.open(AIR); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    r = mix.rate; seg = x[int(0.1 * r):int(2.5 * r)]                    # the marsh before the narrator speaks
    n = mix.n; bed = np.zeros(n); L = len(seg); xf = int(0.4 * r); pos = 0
    fade = np.linspace(0, 1, xf)
    while pos < n:
        s = seg.copy(); s[:xf] *= fade; s[-xf:] *= fade[::-1]
        e = min(n, pos + L); bed[pos:e] += s[:e - pos]; pos += L - xf
    bed = mix.band(bed, 60, 9000)
    bed *= 0.45 / (np.sqrt((bed ** 2).mean()) * 30 + 1e-9)
    mix.add(bed, 0, 1.0)
    T = lambda fr: (fr - F0) / 24
    # wind on the wing as he glides in; it cuts out at f528 (the strike)
    dur = T(528); wn = mix.band(mix.noise(dur, "pink"), 120, 2400)
    env = np.linspace(0.5, 1.0, len(wn)) * (0.8 + 0.2 * np.sin(np.linspace(0, 9, len(wn))))
    env[-int(0.04 * r):] *= np.linspace(1, 0, int(0.04 * r))
    mix.add(wn * env * 0.22, 0, 1.0, pan=0.2)
    # paper: slip 5 pressed down at f480, slip 5b at f550 (soft card flap)
    for fr in (480, 550):
        fl = mix.band(mix.noise(0.12), 400, 3500) * np.exp(-np.linspace(0, 9, int(0.12 * r)))
        mix.add(fl, T(fr) + 0.05, 0.22, pan=0.5)
    # the pin tick as the strike lands (f528)
    mix.click(T(528), gain=0.55, pan=0.45, bright=6500, seconds=0.025)
    # f540-f554: declared silence, air bed only.  Then the bird: wing beats on 2s and a passing whoosh
    for fr in range(556, 562, 4):
        bt = mix.band(mix.noise(0.09), 150, 1400) * np.hanning(int(0.09 * r)); mix.add(bt, T(fr), 0.20, pan=0.2 - (fr - 554) * 0.06)
    mix.whoosh(T(554), seconds=0.36, gain=0.16, pan=-0.1)
    mix.whoosh(T(562), seconds=0.22, gain=0.10, pan=-0.5)               # the flare: brakes
    mix.click(T(578), gain=0.12, pan=-0.6, bright=1800, seconds=0.04)   # claws on the post
    # the glider slides back: a dry creak of the frame and air over the card
    sl = mix.band(mix.noise(T(612) - T(556), "pink"), 200, 1800)
    sl *= np.linspace(0, 1, len(sl)) ** 1.5 * 0.08; mix.add(sl, T(556), 1.0, pan=0.5)
    for fr in (558, 570, 586):
        cr = mix.band(mix.noise(0.06), 600, 2600) * np.exp(-np.linspace(0, 6, int(0.06 * r))); mix.add(cr, T(fr), 0.10, pan=0.5)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        for k in sys.argv[2:]:
            frame_img(int(k)).save(os.path.join(HERE, f"still_{int(k)}.png"))
        sys.exit()
    film.render(out_dir=OUTDIR)
    json.dump(LOG, open(os.path.join(HERE, "exposure_log.json"), "w"), indent=0)
    try:
        os.remove(OUTDIR / "test-shot.webp")
    except OSError:
        pass
