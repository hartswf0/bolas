# Test shot for la-mort-en-ce-jardin, Version L defining beat (film 20.0-28.4 -> local 0-8.4 s).
#   python3 -I shot.py [--stills t ...]
# Beats: CLOSE L-S5 (0-3.4: bag B->C at 0.4 = film 20.4; shoe water->B at 1.6 = film 21.6; rise; hold)
#        LEDGER insert (3.4-5.6: struck and rewritten '1 A . 2 B (sac) . 3 C' -> '1 A . 2 C (sac) . 3 B')
#        L-S8 excerpt (5.6-8.4: B crosses last, liana + shoe, highest water, clearance 4 px, splash)
# SCION #32 FK: hierarchical joint graph, local angles accumulated parent->child, bone lengths asserted per frame,
#   props parented to hand bones on possession.  #44 multiplane: 5 planes with parallax ratios and per-plane depth
#   blur only.  #29 GrabCut: plates cut by plates.py (cut/*.png).  Rendering through kit.Film (boil=0, no grain).
import sys, math, json, os, subprocess
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter

OULIPO = Path("/home/user/bolas/paeleo/scion/oulipo")
sys.path.insert(0, str(OULIPO / "films"))
from kit import Film, font  # noqa: E402

SRC = OULIPO / "films/sources/la-mort-en-ce-jardin/test-shot"
CUT = SRC / "cut"
SWARM = OULIPO / "films/swarm/la-mort-en-ce-jardin"
IA_WATER = "/home/user/hartswf0/cineosis-lab/lab/thumbs/fdb47ec9-f0f6-5e20-9af2-f697c50a2bf8.jpg"
FPS, DUR = 24, 8.4
PW, PH, PX = 800, 540, 80
FILM_T0 = 20.0                          # local 0 = film 20.0
T_BAG, T_SHOE = 0.4, 1.6                # film 20.4, 21.6
CLOSE_END, LEDGER_END = 3.4, 5.6

LEDGER = dict(events=[], frames=[], rig_error_max=0.0)


# ------------------------------------------------------------------ material helpers
def gblur(a, s):
    return cv2.GaussianBlur(a, (0, 0), s) if s > 0 else a


def load_cut(name, scale, blur=0.0, rot=0.0):
    im = Image.open(CUT / f"{name}.png").convert("RGBA")
    if rot: im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    a = np.asarray(im, np.float32)
    if blur:                                      # depth blur on premultiplied colour (no dark halos)
        al = a[..., 3:] / 255
        c = gblur(a[..., :3] * al, blur); al2 = gblur(al[..., 0], blur)[..., None]
        a = np.dstack([c / np.maximum(al2, 1e-3), al2 * 255])
    return np.clip(a, 0, 255)


def over(dst, src, x, y):
    """alpha-composite float RGBA src onto float RGB dst at integer offset (clipped)."""
    H, W = dst.shape[:2]; h, w = src.shape[:2]
    x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x1 <= x0 or y1 <= y0: return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    al = s[..., 3:4] / 255
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - al) + s[..., :3] * al


rng0 = np.random.default_rng(7)


def fibre_field(W, H, seed):
    """Card fibre: thousands of short pale/dark fibres laid in the pulp, the card's own texture."""
    r = np.random.default_rng(seed)
    f = np.zeros((H, W), np.float32)
    n = W * H // 90
    xs, ys = r.uniform(0, W, n), r.uniform(0, H, n)
    ang = r.uniform(0, math.pi, n); ln = r.uniform(2, 7, n); v = r.normal(0, 1, n)
    for x, y, a, l, vv in zip(xs, ys, ang, ln, v):
        cv2.line(f, (int(x), int(y)), (int(x + l * math.cos(a)), int(y + l * math.sin(a))), float(vv), 1)
    f = gblur(f, 0.6)
    pulp = cv2.resize(r.normal(0, 1, (H // 14 + 1, W // 14 + 1)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    return 1 + 0.035 * f + 0.03 * pulp


FIB = fibre_field(PW + 200, PH + 200, 11)


def mud_field(W, H, seed):
    """charcoal-and-water smears: noise dragged along a stroke direction (a finger wiping wet charcoal)."""
    r = np.random.default_rng(seed)
    n = r.normal(0, 1, (H, W)).astype(np.float32)
    k = np.zeros((1, 31), np.float32); k[0] = np.hanning(31)
    sm = cv2.filter2D(n, -1, k / k.sum()); sm = cv2.warpAffine(sm, cv2.getRotationMatrix2D((W / 2, H / 2), 25, 1), (W, H), borderMode=cv2.BORDER_REFLECT)
    sm = gblur(sm, 2.0); sm = sm / (sm.std() + 1e-6)
    big = cv2.resize(r.normal(0, 1, (H // 40 + 1, W // 40 + 1)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    return np.clip(0.45 * sm + 0.8 * np.clip(big, 0, None), 0, 2.2)


MUD = mud_field(PW + 200, PH + 200, 23)


def poly_alpha(W, H, polys, rough_seed=None, amt=1.2):
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    for p in polys: d.polygon([(float(x), float(y)) for x, y in p], fill=255)
    a = np.asarray(m, np.float32)
    if rough_seed is not None:                       # torn/scissored card edge
        r = np.random.default_rng(rough_seed)
        nz = cv2.resize(r.normal(0, 1, (H // 5 + 1, W // 5 + 1)).astype(np.float32), (W, H))
        a = np.clip((gblur(a, 1.1) - 128 + nz * 22 * amt) * 3 + 128, 0, 255)
    return gblur(a, 0.6)


def card_piece(canvas, polys, tone, mud=0.0, seed=0, shadow=5, sweat=(), creases=0.0):
    """Lay one handmade grey-card piece: drop shadow, fibre, charcoal-mud deposit (darker in creases/edges),
    then thin sweat speculars (L 205-225) as separate highlights."""
    H, W = canvas.shape[:2]
    a = poly_alpha(W, H, polys, seed)
    if a.max() < 1: return a
    al = a[..., None] / 255
    if shadow:
        sh = gblur(np.roll(np.roll(a, shadow, 0), shadow, 1), 4)[..., None] / 255
        canvas[:] = canvas * (1 - 0.42 * sh)
    tex = FIB[seed % 97:seed % 97 + H, seed % 113:seed % 113 + W]
    col = np.full((H, W), float(tone), np.float32) * tex
    if mud > 0:
        m = MUD[(seed * 7) % 150:(seed * 7) % 150 + H, (seed * 3) % 160:(seed * 3) % 160 + W]
        edge = 1 - gblur(a, 9) / 255                 # deposit collects toward the card's edges/creases
        dep = np.clip(m * 0.5 + edge * 1.3 * (a > 10), 0, 2.2)
        col = col * (1 - mud * 0.17 * dep)                # charcoal-and-water darkening
    canvas[:] = canvas * (1 - al) + col[..., None] * al
    for (cx, cy, rx, ry, rot, v) in sweat:
        s = Image.new("L", (W, H), 0)
        ImageDraw.Draw(s).ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
        if rot: s = s.rotate(rot, center=(cx, cy))
        sa = gblur(np.asarray(s, np.float32), 1.3)[..., None] / 255 * al
        canvas[:] = canvas * (1 - 0.85 * sa) + v * 0.85 * sa
    return a


def pencil(canvas, pts, width=2, tone=62, alpha=0.85, seed=0):
    """Graphite line: drawn then broken by the card's tooth (fibre field), so the pencil skips."""
    H, W = canvas.shape[:2]
    m = np.zeros((H, W), np.float32)
    cv2.polylines(m, [np.int32(np.round(pts))], False, 1.0, max(1, int(width)), cv2.LINE_AA)
    tooth = np.clip((FIB[seed % 80:seed % 80 + H, seed % 90:seed % 90 + W] - 0.965) * 18, 0.25, 1)
    m = m * tooth * alpha
    canvas[:] = canvas * (1 - m[..., None]) + tone * m[..., None]


def brad(canvas, x, y, r):
    d = np.zeros(canvas.shape[:2], np.float32)
    cv2.circle(d, (int(x), int(y)), int(r), 1.0, -1, cv2.LINE_AA)
    canvas[:] = canvas * (1 - d[..., None] * 0.9) + 150 * d[..., None] * 0.9
    h = np.zeros_like(d); cv2.circle(h, (int(x - r * .35), int(y - r * .35)), max(1, int(r * .35)), 1.0, -1, cv2.LINE_AA)
    canvas[:] = canvas * (1 - h[..., None]) + 222 * h[..., None]
    e = np.zeros_like(d); cv2.circle(e, (int(x), int(y)), int(r), 1.0, 1, cv2.LINE_AA)
    canvas[:] = canvas * (1 - e[..., None] * .7) + 58 * e[..., None] * .7


def capsule(p0, p1, r0, r1, n=10):
    (x0, y0), (x1, y1) = p0, p1
    a = math.atan2(y1 - y0, x1 - x0); pts = []
    for k in range(n + 1):
        t = a + math.pi / 2 + math.pi * k / n; pts.append((x0 + r0 * math.cos(t), y0 + r0 * math.sin(t)))
    for k in range(n + 1):
        t = a - math.pi / 2 + math.pi * k / n; pts.append((x1 + r1 * math.cos(t), y1 + r1 * math.sin(t)))
    return pts


def ell(cx, cy, rx, ry, rot=0, n=40):
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return [(cx + rx * math.cos(t) * c - ry * math.sin(t) * s, cy + rx * math.cos(t) * s + ry * math.sin(t) * c)
            for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]


# ------------------------------------------------------------------ SCION #32: forward kinematics rig
# joint graph: hip(root) -> spine -> neck -> head ; spine -> shoulder -> upper -> fore -> hand ; hip -> thigh -> shin -> foot
BONES = {  # name: (parent, length in units of s)
    "spine": ("root", 92), "neck": ("spine", 16), "head": ("neck", 22),
    "upper_f": ("spine", 44), "fore_f": ("upper_f", 42), "hand_f": ("fore_f", 14),
    "upper_n": ("spine", 44), "fore_n": ("upper_n", 42), "hand_n": ("fore_n", 14),
    "thigh_f": ("root", 58), "shin_f": ("thigh_f", 56), "foot_f": ("shin_f", 22),
    "thigh_n": ("root", 58), "shin_n": ("thigh_n", 56), "foot_n": ("shin_n", 22),
}
ORDER = list(BONES)


def fk(root, local, s):
    """local: bone -> angle (deg) relative to parent's world angle (root's world angle 0).
    Returns world joints: start/end point and world angle per bone. Transforms compose parent -> child."""
    W = {"root": ((root[0], root[1]), (root[0], root[1]), 0.0)}
    for b in ORDER:
        par, L = BONES[b]
        p_end = W[par][1] if par != "root" else root
        if par == "spine" and b.startswith("upper"): p_end = W["spine"][1]          # shoulder pivot at spine end
        ang = W[par][2] + local[b]
        e = (p_end[0] + L * s * math.cos(math.radians(ang)), p_end[1] + L * s * math.sin(math.radians(ang)))
        W[b] = (p_end, e, ang)
    return W


def check_bones(J, s):
    err = 0.0
    for b, (par, L) in BONES.items():
        (x0, y0), (x1, y1), _ = J[b]
        err = max(err, abs(math.hypot(x1 - x0, y1 - y0) - L * s))
    # head/neck attachment: neck start must equal spine end
    err = max(err, math.dist(J["neck"][0], J["spine"][1]))
    LEDGER["rig_error_max"] = max(LEDGER["rig_error_max"], err)
    assert err < 0.5, f"bone length / attachment error {err}"


def to_local(absd):
    """Author poses in world angles (easier to read) and convert to local (parent-relative) angles;
    the rig itself only ever composes local transforms."""
    loc = {}
    for b in ORDER:
        par = BONES[b][0]
        pa = absd[par] if par != "root" else 0.0
        loc[b] = absd[b] - pa
    return loc


def pose_abs(torso, head, arm_f, arm_n, leg_f, leg_n):
    return dict(spine=torso, neck=torso + (head - torso) * 0.5, head=head,
                upper_f=arm_f[0], fore_f=arm_f[1], hand_f=arm_f[2], upper_n=arm_n[0], fore_n=arm_n[1], hand_n=arm_n[2],
                thigh_f=leg_f[0], shin_f=leg_f[1], foot_f=leg_f[2], thigh_n=leg_n[0], shin_n=leg_n[1], foot_n=leg_n[2])


def smoothstep(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)


def interp_keys(keys, t):
    """keys: [(t, root(x,y), abs-pose dict)]. Poses on twos: t quantised to 1/12 s; angles eased then rounded to whole degrees."""
    t = math.floor(t * 12) / 12
    if t <= keys[0][0]: k0 = k1 = keys[0]; u = 0
    elif t >= keys[-1][0]: k0 = k1 = keys[-1]; u = 0
    else:
        for i in range(len(keys) - 1):
            if keys[i][0] <= t < keys[i + 1][0]:
                k0, k1 = keys[i], keys[i + 1]; u = smoothstep((t - k0[0]) / (k1[0] - k0[0])); break
    root = (k0[1][0] + (k1[1][0] - k0[1][0]) * u, k0[1][1] + (k1[1][1] - k0[1][1]) * u)
    ab = {b: round(k0[2][b] + (k1[2][b] - k0[2][b]) * u) for b in ORDER}
    return root, to_local(ab)


# ------------------------------------------------------------------ puppets (handmade grey card)
def draw_puppet(canvas, J, s, tones, who, mud=1.0, facing=1, front_hand_cb=None, between_cb=None):
    """Lay the card pieces in depth order: far limbs, torso+shirt, neck, head(+face, hair, headband), near limbs."""
    def piece(b, r0, r1, tone, m=mud, sweat=(), seed=0):
        p0, p1, _ = J[b]
        card_piece(canvas, [capsule(p0, p1, r0 * s, r1 * s)], tone, m, seed=seed, shadow=int(3 + s))
    sd = {"A": 100, "B": 200, "C": 300}[who]
    # far limbs (darker: the far side of a cut-out is a second card a tone down)
    for i, (b, r0, r1) in enumerate((("thigh_f", 14, 11), ("shin_f", 11, 8), ("foot_f", 8, 6))):
        piece(b, r0, r1, tones["leg"] * .80, seed=sd + i, m=mud * 1.3)
    for i, (b, r0, r1) in enumerate((("upper_f", 10, 8), ("fore_f", 8, 6.5), ("hand_f", 7, 6))):
        piece(b, r0, r1, (tones["skin"] if b != "upper_f" else tones["shirt"]) * .82, seed=sd + 5 + i)
    if between_cb: between_cb(canvas)
    hip, sh, _ = J["spine"]
    ta = math.atan2(sh[1] - hip[1], sh[0] - hip[0]); nx, ny = -math.sin(ta), math.cos(ta)
    shirt = [(hip[0] + nx * 22 * s, hip[1] + ny * 22 * s), (sh[0] + nx * 25 * s, sh[1] + ny * 25 * s),
             (sh[0] - nx * 25 * s, sh[1] - ny * 25 * s), (hip[0] - nx * 21 * s, hip[1] - ny * 21 * s)]
    card_piece(canvas, [capsule(hip, sh, 20 * s, 18 * s)], tones["leg"], mud, seed=sd + 11, shadow=int(3 + s))
    card_piece(canvas, [shirt], tones["shirt"], mud * 1.1, seed=sd + 12, shadow=int(3 + s))
    # pencilled seams: placket, collar V, a pocket, sleeve-fold
    mx = lambda u: (hip[0] + (sh[0] - hip[0]) * u, hip[1] + (sh[1] - hip[1]) * u)
    pencil(canvas, [mx(0.05), mx(0.92)], 2, 70, 0.6, sd)
    c0 = (sh[0] - nx * 12 * s, sh[1] - ny * 12 * s); c1 = (sh[0] + nx * 12 * s, sh[1] + ny * 12 * s)
    pencil(canvas, [c0, mx(0.82), c1], 2, 60, 0.8, sd + 1)
    pk = mx(0.62); pencil(canvas, [(pk[0] + nx * 4 * s, pk[1] + ny * 4 * s), (pk[0] + nx * 14 * s, pk[1] + ny * 14 * s)], 2, 75, 0.5, sd + 2)
    for k in range(3):                                # cloth folds (pencil), the shirt sticks to her
        u = 0.25 + 0.17 * k
        a0 = mx(u); pencil(canvas, [(a0[0] + nx * 18 * s, a0[1] + ny * 18 * s), (a0[0] + nx * 6 * s, a0[1] + ny * 6 * s + 3 * s)], 1.5, 95, 0.45, sd + 3 + k)
    piece("neck", 7, 7, tones["skin"], seed=sd + 13)
    hc = J["head"][1]
    hrot = J["head"][2] + 90
    if who == "B":   # wet hair: back mass behind the head, then cut strands over it
        card_piece(canvas, [ell(hc[0] - facing * 6 * s, hc[1] - 6 * s, 21 * s, 20 * s, hrot)], tones["hair"] * .8, 0.3, seed=sd + 20, shadow=2)
    card_piece(canvas, [ell(hc[0], hc[1], 16 * s, 21 * s, hrot)], tones["skin"], mud * 1.2, seed=sd + 14, shadow=int(2 + s),
               sweat=[(hc[0] + facing * 7 * s, hc[1] - 9 * s, 4.5 * s, 1.6 * s, -10, 218),
                      (hc[0] + facing * 10 * s, hc[1] + 3 * s, 2.2 * s, 3 * s, 0, 208)])
    # face: nose tab card, pencilled eye/brow/mouth, ear card
    ux, uy = math.cos(math.radians(hrot - 90)), math.sin(math.radians(hrot - 90))      # head 'up' axis
    fx, fy = -uy * facing, ux * facing                                                   # facing axis
    P = lambda a, b: (hc[0] + fx * a * s + ux * b * s, hc[1] + fy * a * s + uy * b * s)
    card_piece(canvas, [[P(14, 6), P(23, -4), P(14, -6)]], tones["skin"] * 1.02, mud, seed=sd + 15, shadow=2)
    pencil(canvas, [P(5, 5), P(11, 4)], max(2, s * .9), 35, 0.9, sd + 4)                  # eye
    pencil(canvas, [P(3, 10), P(13, 9.5)], max(2, s * 1.1), 55, 0.8, sd + 5)              # brow
    pencil(canvas, [P(9, -11), P(15, -10)], max(1.5, s * .7), 50, 0.8, sd + 6)            # mouth
    card_piece(canvas, [ell(*P(-3, 0), 4.5 * s, 6.5 * s, hrot)], tones["skin"] * .86, mud, seed=sd + 16, shadow=1)
    if who == "B":
        strands = []
        for k in range(9):
            a0 = P(-14 + 3.2 * k, 20 - abs(k - 4) * .6)
            a1 = P(-24 + 2.5 * k + (k % 2) * 3, -6 - (k % 3) * 7 - (4 if k < 3 else 0))
            strands.append(capsule(a0, a1, 3.2 * s, 1.1 * s, 6))
        card_piece(canvas, [ell(*P(-3, 13), 19 * s, 10 * s, hrot)] + strands, tones["hair"], 0.5, seed=sd + 21, shadow=2,
                   sweat=[(P(2, 15)[0], P(2, 15)[1], 6 * s, 1.4 * s, hrot, 225)])
    if who == "C":   # dark hair cap + patterned headband with a pencilled meander
        card_piece(canvas, [ell(*P(-4, 10), 18 * s, 12 * s, hrot)], tones["hair"], 0.3, seed=sd + 22, shadow=1)
        band = [P(-17, 9), P(17, 9), P(17, 2), P(-17, 1)]
        card_piece(canvas, [band], tones["band"], 0.6, seed=sd + 23, shadow=1)
        for k in range(7):
            q0 = P(-15 + 4.6 * k, 8); q1 = P(-13 + 4.6 * k, 3); q2 = P(-11 + 4.6 * k, 8)
            pencil(canvas, [q0, q1, q2], 2, 55, 0.8, sd + 30 + k)
    for i, (b, r0, r1) in enumerate((("thigh_n", 15, 12), ("shin_n", 11.5, 8.5), ("foot_n", 8, 6))):
        piece(b, r0, r1, tones["leg"], seed=sd + 40 + i, m=mud * 1.3)
    for i, (b, r0, r1) in enumerate((("upper_n", 10.5, 8.5), ("fore_n", 8.5, 6.5))):
        piece(b, r0, r1, tones["shirt"] if b == "upper_n" else tones["skin"], seed=sd + 45 + i)
    if front_hand_cb: front_hand_cb(canvas)          # e.g. the shoe, so the near hand overlaps it (#45 occlusion)
    p0, p1, _ = J["hand_n"]
    card_piece(canvas, [capsule(p0, p1, 7.5 * s, 6.5 * s)], tones["skin"], mud * 1.5, seed=sd + 47, shadow=int(2 + s),
               sweat=[(p0[0] + (p1[0] - p0[0]) * .6, p0[1] + (p1[1] - p0[1]) * .6 - 3 * s, 3.5 * s, 1.2 * s, 0, 214)])
    # split pins at every joint
    for b in ("thigh_f", "shin_f", "upper_f", "fore_f", "hand_f", "neck", "thigh_n", "shin_n", "foot_n", "upper_n", "fore_n", "hand_n"):
        brad(canvas, *J[b][0], max(3, 2.2 * s))


TONES_B = dict(shirt=196, skin=168, leg=150, hair=206)
TONES_C = dict(shirt=118, skin=140, leg=96, hair=52, band=168)


def bag_piece(canvas, x, y, s, ang=0, seed=500):
    """The dry bag: dark oilcloth card, strap and tie (handmade)."""
    body = ell(x, y, 26 * s, 33 * s, ang)
    card_piece(canvas, [body], 58, 0.4, seed=seed, shadow=int(3 + s),
               sweat=[(x - 10 * s, y - 14 * s, 9 * s, 2 * s, ang - 30, 140)])
    ux, uy = math.cos(math.radians(ang - 90)), math.sin(math.radians(ang - 90))
    tie = (x + ux * 32 * s, y + uy * 32 * s)
    card_piece(canvas, [capsule((x + ux * 26 * s, y + uy * 26 * s), tie, 5 * s, 3 * s)], 70, 0.2, seed=seed + 1, shadow=2)
    pencil(canvas, [(x - 18 * s, y - 20 * s), (x + 18 * s, y - 22 * s)], 2, 125, 0.7, seed)
    return tie


# ------------------------------------------------------------------ the foraged shoe (#29 cut in plates.py)
SHOE_FULL = np.asarray(Image.open(CUT / "shoe.png").convert("RGBA"), np.float32)
hS, wS = SHOE_FULL.shape[:2]
SHOE_FULL[int(hS * .55):, :int(wS * .14), 3] = 0          # trim the studio shadow left of the heel
SHOE_FULL[int(hS * .93):, :, 3] = 0


def shoe_img(width, rot):
    im = Image.fromarray(SHOE_FULL.astype(np.uint8), "RGBA").rotate(rot, expand=True, resample=Image.BICUBIC)
    im = im.resize((width, int(width * im.height / im.width)), Image.LANCZOS)
    return np.asarray(im, np.float32)


def shoe_on_water(canvas, cx, wl, width, rot, t, water_tone=80):
    s = shoe_img(width, rot); h, w = s.shape[:2]
    bob = 3 * math.sin(2 * math.pi * t / 0.9)
    y0 = wl - h * 0.78 + bob; x0 = cx - w / 2
    # reflection: flipped, darkened, broken per row by ripple displacement
    r = s[::-1].copy()
    for yy in range(h):
        r[yy] = np.roll(r[yy], int(4 * math.sin(yy * 0.5 + t * 9)), axis=0)
    r[..., :3] *= 0.55; r[..., 3] *= np.linspace(0.5, 0, h)[:, None]
    over(canvas, r[: h // 2], x0, wl + 2)
    # ripple rings (broken arcs)
    m = np.zeros(canvas.shape[:2], np.float32)
    for k in range(3):
        rx = w * (0.55 + 0.25 * k + 0.08 * ((t * 1.3) % 1))
        for a0 in range(0, 360, 45):
            cv2.ellipse(m, (int(cx), int(wl)), (int(rx), int(rx * .12)), 0, a0 + 9 * k, a0 + 26 + 9 * k, 1.0, 2, cv2.LINE_AA)
    m = gblur(m, 0.7) * 0.35
    canvas[:] = canvas * (1 - m[..., None]) + 200 * m[..., None]
    rows = np.arange(h) + y0
    sub = np.clip((rows - wl) / (h * .22 + 1), 0, 1)[:, None]
    s2 = s.copy(); s2[..., :3] = s2[..., :3] * (1 - .6 * sub[..., None]) + water_tone * .6 * sub[..., None]
    s2[..., 3] *= (1 - .5 * sub)
    over(canvas, s2, x0, y0)


def shoe_in_hand(canvas, J, width, rot_extra=0):
    p0, p1, ang = J["hand_n"]
    s = shoe_img(width, -ang + 180 + rot_extra)   # parented to the hand bone: rotates with it
    h, w = s.shape[:2]
    over(canvas, s, p1[0] - w * .5, p1[1] - h * .45)


# ------------------------------------------------------------------ planes (#44)
def grade_plate(L):  # monotone, neutral: p2/p98 -> 35/220 (already done in plates.py; re-asserted for the water)
    p2, p98 = np.percentile(L, 2), np.percentile(L, 98)
    return np.clip(35 + (L - p2) * 185 / max(p98 - p2, 1), 0, 255)


IAw = np.asarray(Image.open(IA_WATER).convert("L"), np.float32)[430:1080, 900:1440]
IAw = cv2.resize(IAw, (1100, 1320 // 2 * 1), interpolation=cv2.INTER_AREA)
IAw = grade_plate(IAw) * 0.55 + 30           # water sits darker than the jungle it reflects
WATER = np.dstack([IAw] * 3 + [np.full(IAw.shape, 255, np.float32)])


def water_plane(canvas, top, t, x_cam, scale=1.0, lift=0):
    """foraged 1920 water, cut into three handmade strips that slide at different rates (4/7/11 px per 12 poses)."""
    H, W = canvas.shape[:2]
    for k, (y0, sp) in enumerate(((0, 4), (60, 7), (140, 11))):
        sl = WATER[y0 * 2:, :, :]
        off = int((t * 12 * sp / 2) % 400) + int(x_cam)
        strip = sl[: H - top - y0 + 40, off: off + W]
        if strip.shape[1] < W: continue
        st = strip.copy()
        # torn top edge of each strip
        ed = (np.sin(np.arange(W) * 0.05 + k) * 3 + np.sin(np.arange(W) * 0.17 + 2 * k) * 1.5)
        for x in range(0, W, 1):
            st[: max(int(4 + ed[x]), 0), x, 3] = 0
        over(canvas, st, 0, top + y0 - lift)
    # waterline gleam: a soft lighter band where the overcast sky sits in the water (no sky in frame)
    g = np.zeros(canvas.shape[:2], np.float32); g[top - lift:top - lift + 6] = 0.25
    canvas[:] = canvas * (1 - g[..., None]) + 175 * g[..., None]


P0 = load_cut("P0_far", 0.78, blur=1.1)
P1 = load_cut("P1_flange", 0.62, blur=0.7)
P3 = load_cut("P3_leaves", 0.58, blur=2.6)
P4R = load_cut("P1_flange", 0.55, blur=3.5, rot=-24)       # foreground root diagonal, low left
# fern: GrabCut matte x graphite-dark pinnae (the light leaves behind the fern drop out)
_f = np.asarray(Image.open(CUT / "P4_fern.png").convert("RGBA"), np.float32)
_L = _f[..., 0]
_a = _f[..., 3] * np.clip((140 - gblur(_L, 1.5)) / 35, 0, 1)
hF, wF = _a.shape
yy, xx = np.mgrid[0:hF, 0:wF]
_a *= np.clip(np.minimum(np.minimum(xx, wF - xx), np.minimum(yy, hF - yy)) / 90.0, 0, 1)   # the fronds thin out at the plate's edge
_a = np.maximum(_a, 255 * ((((xx - wF * .39) / (wF * .1)) ** 2 + ((yy - hF * .43) / (hF * .15)) ** 2) < 1))
_f[..., 3] = _a
FERN = np.asarray(Image.fromarray(_f.astype(np.uint8), "RGBA").resize((int(wF * .5), int(hF * .5)), Image.LANCZOS), np.float32)
_al = FERN[..., 3:] / 255
FERN = np.dstack([gblur(FERN[..., :3] * _al, 3.0) / np.maximum(gblur(_al[..., 0], 3.0)[..., None], 1e-3), gblur(_al[..., 0], 3.0)[..., None] * 255])


def bank(canvas, cam, top=470, seed=600):
    """Handmade torn-card bank with root fingers, rubbed with charcoal mud."""
    H, W = canvas.shape[:2]
    pts = [(-40 - cam, top + 18), (120 - cam, top - 4), (300 - cam, top + 4), (470 - cam, top + 14), (560 - cam, top + 40),
           (600 - cam, H + 20), (-40 - cam, H + 20)]
    roots = [capsule((420 + 40 * k - cam, top + 20), (520 + 46 * k - cam, top + 70 + 10 * k), 9, 3) for k in range(3)]
    card_piece(canvas, [pts] + roots, 72, 1.4, seed=seed, shadow=6)


def plank(canvas, p0, p1, thick, deflect_at=None, defl=0.0, seed=700, tone=172):
    """Pale card plank scored with pencil grain; bends as a 2-segment polyline under its occupant."""
    (x0, y0), (x1, y1) = p0, p1
    if deflect_at is None:
        mid = ((x0 + x1) / 2, (y0 + y1) / 2); top = [p0, mid, p1]
    else:
        u = deflect_at; mid = (x0 + (x1 - x0) * u, y0 + (y1 - y0) * u + defl); top = [p0, mid, p1]
    bot = [(x, y + thick) for x, y in top[::-1]]
    card_piece(canvas, [top + bot], tone, 0.35, seed=seed, shadow=7,
               sweat=[(mid[0] - 40, mid[1] + 2, 60, 1.5, math.degrees(math.atan2(y1 - y0, x1 - x0)), 214)])
    for k in range(4):
        pencil(canvas, [(x + 0, y + 3 + k * thick / 5) for x, y in top], 1, 120, 0.4, seed + k)
    return top


def caption(img_rgb, text):
    """kit serif 24 px, #e6e6e6 on a #2d2d2d band at 55 % opacity (drawn on the 960 frame)."""
    im = Image.fromarray(img_rgb.astype(np.uint8)).convert("RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    f = font("serif", 24); tw = d.textlength(text, font=f)
    cx, cy = im.width / 2, im.height - 40
    d.rectangle((cx - tw / 2 - 14, cy - 18, cx + tw / 2 + 14, cy + 16), fill=(45, 45, 45, 140))
    d.text((cx, cy), text, font=f, fill=(230, 230, 230, 255), anchor="mm")
    return np.asarray(Image.alpha_composite(im, ov).convert("RGB"), np.float32)


# ------------------------------------------------------------------ beat 1: CLOSE L-S5
SB = 2.7                     # B's head card: 2*21*2.7 = 113 px = 0.21 H
SC = 2.9
FOREST_TONE = None
def arm_to(hip, torso, s, target, bend=1, hand=None):
    """Pose annotator's helper: world angles (upper, fore, hand) that put the wrist on `target`.
    Used only to author keys; every frame is still evaluated by fk()."""
    sh = (hip[0] + 92 * s * math.cos(math.radians(torso)), hip[1] + 92 * s * math.sin(math.radians(torso)))
    l1, l2 = 44 * s, 42 * s
    dx, dy = target[0] - sh[0], target[1] - sh[1]
    d = min(math.hypot(dx, dy), (l1 + l2) * 0.999)
    base = math.degrees(math.atan2(dy, dx))
    c = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    a1 = math.degrees(math.acos(max(-1, min(1, c))))
    up = base - bend * a1
    e = (sh[0] + l1 * math.cos(math.radians(up)), sh[1] + l1 * math.sin(math.radians(up)))
    fo = math.degrees(math.atan2(sh[1] + dy * d / max(math.hypot(dx, dy), 1e-6) - e[1], sh[0] + dx * d / max(math.hypot(dx, dy), 1e-6) - e[0]))
    return (up, fo, fo if hand is None else hand)


SHOE_POS = (606, 494)   # at the plank foot
SEIZA = ((8, 188, 182), (14, 192, 182))          # kneeling: thighs forward, shins folded back on the bank


def kB(t, hip, torso, head, far_t, near_t, legs, bend_f=-1, bend_n=1, hand_n=None):
    lf, ln = legs
    return (t, hip, pose_abs(torso, head, arm_to(hip, torso, SB, far_t, bend_f), arm_to(hip, torso, SB, near_t, bend_n, hand_n), lf, ln))


CROUCH = ((-24, 98, 0), (-12, 104, 0))
KB = [  # (t, hip root, world-angle pose)  B faces right (the plank foot and the shoe are at frame right)
    kB(0.00, (330, 432), -70, -48, (205, 395), (470, 330), CROUCH),        # crouched at the plank foot, bag in her far hand
    kB(0.40, (322, 434), -76, -44, (168, 372), (480, 320), CROUCH),        # pushes it back into C's hands, eyes on the shoe
    kB(0.75, (330, 452), -62, -36, (300, 430), (520, 380), CROUCH),        # the far hand comes back empty; she lowers
    kB(1.20, (338, 468), -36, -10, (360, 470), (590, 470), SEIZA),         # knees down, bends, near hand reaches
    kB(1.60, (342, 470), -30, -4, (380, 480), (600, 488), SEIZA, hand_n=10),  # hand card over the satin: grasp
    kB(2.10, (336, 466), -58, -34, (430, 390), (520, 330), SEIZA),         # rises with it
    kB(2.50, (332, 464), -78, -58, (430, 300), (440, 268), SEIZA),         # to her chest
    kB(3.40, (332, 463), -80, -60, (428, 298), (438, 266), SEIZA),
]


def kC(t, hip, torso, head, far_t, near_t):
    return (t, hip, pose_abs(torso, head, arm_to(hip, torso, SC, far_t, -1), arm_to(hip, torso, SC, near_t, -1), (-30, 100, 0), (-20, 96, 0)))


KC = [  # C crouched at the left edge (cropped by the frame), facing right, hands out for the bag
    kC(0.00, (-6, 520), -76, -70, (150, 360), (172, 372)),
    kC(0.40, (0, 518), -74, -66, (158, 366), (176, 380)),
    kC(0.90, (-12, 522), -84, -86, (110, 330), (128, 342)),               # pulls it to his chest
    kC(3.40, (-14, 522), -86, -88, (106, 326), (124, 338)),
]



def close_frame(t):
    cam = -14 * smoothstep(t / CLOSE_END) + 4 * math.sin(t * 0.7)      # slow lateral glide (px at P2)
    C = np.zeros((PH, PW, 3), np.float32) + 90
    over(C, P0, -150 - cam * .15, -150)                 # P0 far wall + giant buttress trunk
    over(C, P1, -250 - cam * .35, 175)                  # P1 sinuous flange, mid
    water_plane(C, 486, t, 40 - cam)
    bank(C, cam, top=500)
    plank(C, (548 - cam, 506), (900 - cam, 452), 20)
    # possession state machine
    bag_holder = "B" if t < T_BAG else "C"
    shoe_holder = "water" if t < T_SHOE else "B"
    rB, lB = interp_keys(KB, t); JB = fk(rB, lB, SB); check_bones(JB, SB)
    rC, lC = interp_keys(KC, t); JC = fk(rC, lC, SC); check_bones(JC, SC)
    rB = (rB[0] - cam, rB[1]); JB = fk(rB, lB, SB)
    rC = (rC[0] - cam, rC[1]); JC = fk(rC, lC, SC)
    # C, then B
    def c_bag(canvas):
        if bag_holder == "C":
            hx, hy = JC["hand_n"][1]; bag_piece(canvas, hx + 10, hy + 30, 2.4, -8)
    draw_puppet(C, JC, SC, TONES_C, "C", mud=1.1, front_hand_cb=c_bag)

    def b_bag(canvas):
        if bag_holder == "B":
            hx, hy = JB["hand_f"][1]; bag_piece(canvas, hx - 4, hy + 40, 2.4, 6)
    def shoe_cb(canvas):
        if shoe_holder == "water":
            shoe_on_water(canvas, SHOE_POS[0] - cam, SHOE_POS[1], 170, 4, t)
        else:
            shoe_in_hand(canvas, JB, 170, 0)
    draw_puppet(C, JB, SB, TONES_B, "B", mud=1.0, between_cb=b_bag, front_hand_cb=shoe_cb)
    # P3 big heart leaves across the top right (canopy darker above), P4 fern right edge, root diagonal low left
    over(C, P3, 560 - cam * 1.5, -360)
    over(C, P3[:, ::-1], -560 - cam * 1.5, -470)
    over(C, FERN, 650 - cam * 2.0, 20)
    over(C, P4R, -300 - cam * 2.0, 400)
    return C, dict(bag=bag_holder, shoe=shoe_holder, plank_occupant=None, hands_B=["bag" if bag_holder == "B" else "free",
                   "shoe" if shoe_holder == "B" else "free"])


# ------------------------------------------------------------------ beat 2: LEDGER insert
LINE1 = ["1 A", "2 B (sac)", "3 C"]
LINE2 = ["1 A", "2 C (sac)", "3 B"]


def script_line(canvas, parts, x, y, scale, upto, seed):
    """Hershey script (single-stroke pencil letterforms, cv2) pencilled on the card, revealed letter by letter."""
    mask = np.zeros(canvas.shape[:2], np.float32)
    cx = x; n = 0; ends = []
    for pi, part in enumerate(parts):
        for ch in part:
            if n >= upto: break
            frac = min(1.0, upto - n)
            (tw, th), _ = cv2.getTextSize(ch, cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, scale, 2)
            g8 = np.zeros(mask.shape, np.uint8)
            cv2.putText(g8, ch, (int(cx), int(y)), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, scale, 255, 3, cv2.LINE_AA)
            g = g8.astype(np.float32) / 255
            if frac < 1: g[:, int(cx + tw * frac):] = 0           # the pencil is mid-letter
            mask = np.maximum(mask, g)
            cx += tw; n += 1
        ends.append(cx)
        if pi < len(parts) - 1:
            if n < upto:
                cv2.circle(mask, (int(cx + 16), int(y - 10)), 4, 1.0, -1, cv2.LINE_AA)   # the middle dot
            cx += 34
    tooth = np.clip((FIB[seed:seed + canvas.shape[0], seed:seed + canvas.shape[1]] - 0.96) * 14, 0.35, 1)
    m = gblur(mask, 0.6) * tooth * 0.85
    canvas[:] = canvas * (1 - m[..., None]) + 58 * m[..., None]
    return cx, ends


def nchars(parts): return sum(len(p) for p in parts)


def ledger_frame(t):
    u = t - CLOSE_END
    C = np.zeros((PH, PW, 3), np.float32)
    over(C, P0, -320 - u * 3, -330)
    bank(C, 0, top=60, seed=610)
    card = [(70, 120), (420, 104), (735, 128), (748, 300), (720, 420), (360, 436), (60, 418), (52, 260)]
    card_piece(C, [card], 178, 0.45, seed=620, shadow=9)
    xend, _ = script_line(C, LINE1, 110, 225, 1.55, 99, 3)
    # strike: 8 frames (0.33 s) from u=0.30
    sk = min(max((u - 0.30) / (8 / FPS), 0), 1)
    if sk > 0:
        pts = [(100 + (xend - 90) * q * sk, 212 - 6 * math.sin(q * 3) + q * 6) for q in np.linspace(0, 1, 24)]
        pencil(C, pts, 3, 48, 0.95, 9)
    # rewrite: from u=0.75 to 1.9, letter by letter
    n2 = nchars(LINE2)
    up = (u - 0.75) / 1.15 * n2
    if up > 0: script_line(C, LINE2, 110, 340, 1.55, up, 5)
    # mud thumbprints on the card from B's hand (deposit)
    over(C, P3, 430 - u * 6, -330)
    return C, dict(ledger="1 A · 2 B (sac) · 3 C" if up <= 0 else ("1 A · 2 C (sac) · 3 B" if up >= n2 else "rewriting"))


# ------------------------------------------------------------------ beat 3: L-S8 excerpt, B crosses last
S3 = 1.45


def walk_pose(phase, carrying=True):
    """step cycle with weight: thigh swing, knee bend on passing, hip drops at foot plant."""
    sw = math.sin(phase * 2 * math.pi)
    th_f = 90 - 24 * sw; th_n = 90 + 24 * sw
    kb_f = 20 * max(0, math.cos(phase * 2 * math.pi)); kb_n = 20 * max(0, -math.cos(phase * 2 * math.pi))
    return pose_abs(-86, -70, (118, 170, 210), (-120, -100, -95),     # far arm: shoe at chest; near arm: up on the liana
                    (th_f, th_f + kb_f, 0), (th_n, th_n + kb_n, 0))


def cross_frame(t):
    u = t - LEDGER_END                       # 0..2.8 ; film 32.0+ (L-S8)
    cam = 70 * smoothstep(u / 2.8)
    C = np.zeros((PH, PW, 3), np.float32) + 90
    over(C, P0, -60 - cam * .15, -260)
    over(C, P1, 380 - cam * .35, 250)
    lift = int(6 + 8 * smoothstep(u / 2.8))   # water still rising
    WL = 420
    water_plane(C, WL, t, 80 + cam, lift=lift)
    bank(C, cam + 260, top=405, seed=630)
    # B: steps along the plank; feet-on-plank position x(t)
    px0, px1 = 150 - cam, 980 - cam
    bx = 250 + 150 * smoothstep(u / 2.8) - cam
    ufrac = (bx - px0) / (px1 - px0)
    plank_y0 = 404
    defl = 9 * math.sin(math.pi * min(max(ufrac, 0), 1)) * 1.0
    top = plank(C, (px0, plank_y0), (px1, plank_y0 - 10), 16, deflect_at=ufrac, defl=defl)
    plank_top_at_b = top[1][1]
    water_y = WL - lift
    clearance = (water_y) - (plank_top_at_b + 16)        # gap between plank underside and water at her position
    clearance = max(int(round(-clearance if clearance < 0 else clearance)), 0)
    # liana: twisted paper cord from canopy, her near hand rides it
    phase = (u / 1.4) % 1
    pz = walk_pose(phase)
    hip_drop = 5 * abs(math.sin(phase * 2 * math.pi))
    leg = (58 + 56 + 22 * .2) * S3
    root = (bx, plank_top_at_b - leg + 8 + hip_drop)
    J = fk(root, to_local({b: round(v) for b, v in pz.items()}), S3); check_bones(J, S3)
    hand = J["hand_n"][1]
    lp = [(hand[0] - 300 - cam * .2, -10), (hand[0] - 120, hand[1] - 80), hand, (hand[0] + 260, hand[1] - 20), (hand[0] + 520, -10)]
    for k in range(2):
        pencil(C, lp, 7 - 3 * k, 46 + 30 * k, 0.95, 40 + k)
    def shoe_cb(canvas):
        p0, p1, ang = J["hand_f"]; s = shoe_img(80, -ang + 180)
        h, w = s.shape[:2]; over(canvas, s, p1[0] - w * .5, p1[1] - h * .5)
    draw_puppet(C, J, S3, TONES_B, "B", mud=1.0 + 0.8 * smoothstep((u - 1.6) / 0.6), between_cb=shoe_cb)
    # splash on her shins at u=1.7 (plank dips into the water)
    if 1.6 < u < 2.4:
        r = np.random.default_rng(int(u * 24))
        k = (u - 1.6) / 0.8
        for i in range(26):
            a = r.uniform(-2.6, -0.5); v = r.uniform(30, 90)
            x = bx + math.cos(a) * v * k * 1.4; y = water_y - 4 + math.sin(a) * v * k * 1.6 + 120 * k * k
            m = np.zeros(C.shape[:2], np.float32); cv2.circle(m, (int(x), int(y)), int(r.uniform(1, 3.5)), 1.0, -1, cv2.LINE_AA)
            C[:] = C * (1 - m[..., None] * .8) + 212 * m[..., None] * .8
    over(C, P3, 470 - cam * 1.5, -400)
    over(C, P3[:, ::-1], -360 - cam * 1.5, -470)
    over(C, FERN, 620 - cam * 2.0, 130)
    over(C, P4R, -220 - cam * 2.0, 380)
    return C, dict(plank_occupant="B", hands_B=["liana", "shoe"], bag="C", shoe="B", clearance_px=clearance)


# ------------------------------------------------------------------ film assembly through kit.Film
def picture_rgb(t):
    if t < CLOSE_END: C, st = close_frame(t); cap = "« Je ne peux pas tout porter. »" if t > 2.5 else None; beat = "L-S5 close"
    elif t < LEDGER_END: C, st = ledger_frame(t); cap = None; beat = "L-S6 ledger insert"
    else: C, st = cross_frame(t); cap = "« Elle la garde. »" if t > 6.6 else None; beat = "L-S8 excerpt"
    F = np.zeros((540, 960, 3), np.float32) + 27            # #1b1b1b pillarbox bars
    F[:, PX:PX + PW] = np.clip(C, 0, 255)
    if cap: F = caption(F, cap)
    st.update(t=round(t, 4), film_t=round(FILM_T0 + t, 4), beat=beat)
    return F, st


film = Film("test-shot", seconds=DUR, boil=0, wobble=0, seed=3)


@film.picture
def frame(t, ink):
    ink.paper((27, 27, 27), grain=False)                      # no kit grain, no vignette
    F, st = picture_rgb(t)
    LEDGER["frames"].append(st)
    ink.paste(Image.fromarray(F.astype(np.uint8)))


def load_audio(path, start, dur):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(start), "-t", str(dur), "-i", str(path), "-ac", "1",
                          "-ar", "44100", "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


@film.sound
def sound(mix):
    A = SRC / "audio"
    bed = load_audio(A / "stream.wav", 12.0, DUR + 0.5)
    bed = bed / (np.abs(bed).max() + 1e-9)
    n = len(bed); env = np.ones(n)
    ts = np.arange(n) / 44100
    env[(ts >= CLOSE_END) & (ts < LEDGER_END)] = 0.35            # the ledger insert sits back from the water
    env[ts >= LEDGER_END] = 0.7 + 0.5 * np.clip((ts[ts >= LEDGER_END] - LEDGER_END) / 2.8, 0, 1)
    env = np.convolve(env, np.ones(2205) / 2205, mode="same")
    mix.add(bed * env * 0.32, 0.0, pan=0.15)
    # bag hand-off: oilcloth rustle + its weight landing in C's arms (synth foley, declared)
    ru = mix.band(mix.noise(0.32, "white"), 900, 5000) * mix.env(int(0.32 * 44100), 0.01, 0.25)
    mix.add(ru, T_BAG - 0.05, 0.5, pan=-0.5); mix.thud(T_BAG + 0.05, freq=90, gain=0.35, pan=-0.5, seconds=0.25)
    # her hand into the water at the shoe; trickle off her fingers as she lifts (foraged PD recording)
    tr = load_audio(A / "trickle.ogg", 3.0, 1.2); tr = tr / (np.abs(tr).max() + 1e-9)
    tr *= np.linspace(1, 0, len(tr)) ** 1.5
    mix.add(tr, T_SHOE - 0.25, 0.30, pan=0.45)
    mix.click(T_SHOE, gain=0.18, pan=0.45, bright=2500)           # card fingers on the satin heel
    ru2 = mix.band(mix.noise(0.25, "white"), 600, 3500) * mix.env(int(0.25 * 44100), 0.02, 0.2)
    mix.add(ru2, 1.95, 0.25, pan=0.2)                              # card rustle as she rises
    # pencil: strike (8 frames) and rewrite (letter by letter)
    sk = mix.band(mix.noise(8 / FPS, "white"), 2500, 9000) * mix.env(int(8 / FPS * 44100), 0.005, 0.3, 0.6)
    mix.add(sk, CLOSE_END + 0.30, 0.55)
    n2 = nchars(LINE2)
    for i in range(n2):
        at = CLOSE_END + 0.75 + i * 1.15 / n2
        g = mix.band(mix.noise(0.06, "white"), 3000, 9000) * mix.env(int(0.06 * 44100), 0.004, 0.05)
        mix.add(g, at, 0.30)
    # plank creak per step (synth, declared) and the splash at the dip
    for k in range(4):
        at = LEDGER_END + 0.2 + k * 0.7
        cr = mix.tone(150 + 25 * k, 0.28, "saw", vibrato=0.05) * mix.env(int(0.28 * 44100), 0.03, 0.2)
        mix.add(mix.band(cr, 200, 1400), at, 0.14, pan=0.1 * k)
        mix.step(at + 0.02, gain=0.12, surface="wood")
    sp = load_audio(A / "trickle.ogg", 9.0, 1.0); sp = sp / (np.abs(sp).max() + 1e-9) * np.linspace(1, 0, len(sp))
    mix.add(sp, LEDGER_END + 1.62, 0.5, pan=0.1)
    mix.add(mix.lowpass(mix.noise(0.4, "white"), 1800) * mix.env(int(0.4 * 44100), 0.005, 0.35), LEDGER_END + 1.6, 0.5)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        out = SWARM / "test-shot-build" / "stills"; out.mkdir(exist_ok=True)
        for t in [float(x) for x in sys.argv[2:]]:
            F, st = picture_rgb(t)
            Image.fromarray(F.astype(np.uint8)).save(out / f"{t:05.2f}.png"); print(t, st)
        sys.exit()
    film.render(out_dir=SWARM)
    try: os.remove(SWARM / "test-shot.webp")
    except OSError: pass
    LEDGER["events"] = [
        dict(film_t=FILM_T0 + T_BAG, event="handoff", obj="bag", frm="B", to="C"),
        dict(film_t=FILM_T0 + T_SHOE, event="retrieve", obj="shoe", frm="water", to="B"),
        dict(film_t=FILM_T0 + CLOSE_END + 0.30, event="ledger_strike", text="1 A · 2 B (sac) · 3 C"),
        dict(film_t=FILM_T0 + CLOSE_END + 1.90, event="ledger_rewrite", text="1 A · 2 C (sac) · 3 B"),
        dict(film_t="L-S8 excerpt", event="last_crossing", who="B", min_clearance_px=4),
    ]
    json.dump(LEDGER, open(SWARM / "test-shot-build" / "world-trace.json", "w"), indent=0, ensure_ascii=False)
    print("rig_error_max", LEDGER["rig_error_max"])
