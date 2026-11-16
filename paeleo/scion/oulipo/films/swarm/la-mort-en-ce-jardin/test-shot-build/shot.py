# Test shot r2 for la-mort-en-ce-jardin, Version L defining beat (film 20.0-28.8 -> local 0-8.8 s).
#   python3 -I shot.py [--stills t ...]
# Beats: S5 MEDIUM-CLOSE (0-3.6): B kneels at the plank foot; bag B->C at 0.4 (film 20.4); shoe water->B at 1.6
#        (film 21.6); she rises with it to her chest. The plank, the water and A (already across) are in frame.
#        LEDGER insert (3.6-6.0): pencil card on the bank; C's hand strikes '1 A . 2 B (sac) . 3 C' and writes
#        '1 A . 2 C (sac) . 3 B'.  S8 WIDE (6.0-8.8): B crosses last, liana + shoe, highest water (clearance 4 px);
#        C waits on the near bank with the bag, A on the far bank: one on the plank at a time.
# r2 changes: puppets rebuilt as flat cut-card figures (designed silhouette pieces per bone: profile head with
#   nose/chin, hair masses, blouse/shirt with collar and tucked trousers, rolled sleeves, mitten hands with thumbs,
#   boots), card faces from a foraged CC0 cardboard scan, cut-edge darkening, drop shadow + contact shadow, figure
#   plane sharp while planes behind carry depth blur; ledger card is a foraged paper scan with wobbling pencil script.
# SCION #32 FK: joint graph, local angles composed parent->child, bone lengths asserted every frame, every card
#   piece is defined in its bone's local frame, props (bag, shoe, pencil) parented to hand bones.
# SCION #44 multiplane: 5 planes (P0 far wall, P1 trunks, P2 figures/plank, P3 leaves, P4 fern/root) with parallax
#   ratios 0.15/0.35/1/1.5/2.0 and per-plane depth blur only.  SCION #29 GrabCut: plates cut by plates.py.
import sys, math, json, os, subprocess
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw

OULIPO = Path("/home/user/bolas/paeleo/scion/oulipo")
sys.path.insert(0, str(OULIPO / "films"))
from kit import Film, font  # noqa: E402

SRC = OULIPO / "films/sources/la-mort-en-ce-jardin/test-shot"
CUT = SRC / "cut"
SWARM = OULIPO / "films/swarm/la-mort-en-ce-jardin"
IA_WATER = "/home/user/hartswf0/cineosis-lab/lab/thumbs/fdb47ec9-f0f6-5e20-9af2-f697c50a2bf8.jpg"
FPS, DUR = 24, 8.8
PW, PH, PX = 800, 540, 80
FILM_T0 = 20.0
T_BAG, T_SHOE = 0.4, 1.6
CLOSE_END, LEDGER_END = 3.6, 6.0

LEDGER = dict(events=[], frames=[], rig_error_max=0.0)
SOUND_SRC = []


def gblur(a, s):
    return cv2.GaussianBlur(a, (0, 0), s) if s > 0 else a


def neutral_L(path):
    return np.asarray(Image.open(path).convert("L"), np.float32)


# ------------------------------------------------------------------ real card and paper surfaces (foraged scans)
def tile_to(a, W, H):
    while a.shape[0] < H or a.shape[1] < W:
        a = np.concatenate([a, a[::-1]], 0) if a.shape[0] < H else a
        a = np.concatenate([a, a[:, ::-1]], 1) if a.shape[1] < W else a
    return a[:H, :W]


_cb = neutral_L(SRC / "paper/Cardboard_546867_jpg.jpg")
_cb = _cb[: _cb.shape[0] // 2 * 2, :]
_hp = _cb - gblur(_cb, 18)
_hp = np.clip(_hp / (_hp.std() + 1e-6), -3, 3)
CARD = 1 + 0.055 * tile_to(_hp, PW + 400, PH + 400)            # the grey card's own pulp and fibre, from a real scan

PAPER_FILE = None
for cand in ("Vintage_Paper_Texture_9789792113_jpg.jpg", "Kraft_tileable_1024x1024_png.jpg", "Free_paper_texture_27_jpg.jpg",
             "Cattail_handmade_paper_1280_jpg.jpg"):
    if (SRC / "paper" / cand).exists(): PAPER_FILE = cand; break
if PAPER_FILE:
    _pp = neutral_L(SRC / "paper" / PAPER_FILE)
else:
    _pp = _cb.copy()
_pp = cv2.resize(_pp, (900, int(900 * _pp.shape[0] / _pp.shape[1])), interpolation=cv2.INTER_AREA)
_lo, _hi = np.percentile(_pp, 2), np.percentile(_pp, 98)
PAPER = tile_to(np.clip(176 + (_pp - _lo) * 44 / max(_hi - _lo, 1), 120, 232), 900, 640)   # monotone, neutral, L176-220
PAPER_TOOTH = np.clip(((_pp - gblur(_pp, 3)) / ((_pp - gblur(_pp, 3)).std() + 1e-6)), -3, 3)
PAPER_TOOTH = tile_to(PAPER_TOOTH, 900, 640)


def mud_field(W, H, seed):
    """charcoal-and-water deposit: noise dragged along a wiping direction."""
    r = np.random.default_rng(seed)
    n = r.normal(0, 1, (H, W)).astype(np.float32)
    k = np.zeros((1, 25), np.float32); k[0] = np.hanning(25)
    sm = cv2.filter2D(n, -1, k / k.sum())
    sm = cv2.warpAffine(sm, cv2.getRotationMatrix2D((W / 2, H / 2), 25, 1), (W, H), borderMode=cv2.BORDER_REFLECT)
    sm = gblur(sm, 1.6); sm = sm / (sm.std() + 1e-6)
    big = cv2.resize(r.normal(0, 1, (H // 30 + 1, W // 30 + 1)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    return np.clip(0.4 * sm + 0.9 * np.clip(big, 0, None), 0, 2.2)


MUD = mud_field(PW + 400, PH + 400, 23)


# ------------------------------------------------------------------ compositing primitives
def over(dst, src, x, y):
    H, W = dst.shape[:2]; h, w = src.shape[:2]
    x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x1 <= x0 or y1 <= y0: return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    al = s[..., 3:4] / 255
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - al) + s[..., :3] * al


def lay(C, polys, tone, mud=0.0, seed=0, shadow=4, sweat=(), edge=0.45, smudges=(), tex=True):
    """Lay one cut-card piece (bbox-cropped): soft drop shadow on what is behind, card face = tone x real card scan,
    charcoal-mud deposit (stronger toward cut edges), darkened cut edge, sweat speculars L205-225."""
    H, W = C.shape[:2]
    P = [np.asarray(p, np.float32) for p in polys if len(p) >= 3]
    if not P: return
    allp = np.concatenate(P)
    pad = 14 + shadow
    x0, y0 = int(max(allp[:, 0].min() - pad, 0)), int(max(allp[:, 1].min() - pad, 0))
    x1, y1 = int(min(allp[:, 0].max() + pad, W)), int(min(allp[:, 1].max() + pad, H))
    if x1 <= x0 + 1 or y1 <= y0 + 1: return
    w, h = x1 - x0, y1 - y0
    m = Image.new("L", (w * 2, h * 2), 0); d = ImageDraw.Draw(m)
    for p in P: d.polygon([(float(px - x0) * 2, float(py - y0) * 2) for px, py in p], fill=255)
    a = cv2.resize(np.asarray(m, np.float32), (w, h), interpolation=cv2.INTER_AREA)
    a = gblur(a, 0.35)
    al = a[..., None] / 255
    reg = C[y0:y1, x0:x1]
    if shadow:
        sh = np.zeros_like(a)
        sh[shadow:, shadow:] = a[:h - shadow, :w - shadow]
        sh = gblur(sh, 2.0 + shadow * 0.6)[..., None] / 255
        reg[:] = reg * (1 - 0.5 * sh)
    col = np.full((h, w), float(tone), np.float32)
    if tex: col = col * CARD[(y0 + seed * 13) % 380:(y0 + seed * 13) % 380 + h, (x0 + seed * 29) % 380:(x0 + seed * 29) % 380 + w]
    ed = np.clip(1 - gblur(a, 6) / 255 * 1.6, 0, 1) * (a > 20)
    if mud > 0:
        mm = MUD[(y0 + seed * 7) % 380:(y0 + seed * 7) % 380 + h, (x0 + seed * 3) % 380:(x0 + seed * 3) % 380 + w]
        col = col * (1 - mud * 0.16 * np.clip(mm * 0.5 + ed * 1.6, 0, 2.2))
    for (cx, cy, rx, ry, rot, k) in smudges:              # placed mud smears (a thumb wiping wet charcoal)
        sm = np.zeros((h, w), np.float32)
        cv2.ellipse(sm, (int(cx - x0), int(cy - y0)), (max(int(rx), 1), max(int(ry), 1)), rot, 0, 360, 1.0, -1, cv2.LINE_AA)
        mm = MUD[(seed * 5) % 380:(seed * 5) % 380 + h, (seed * 11) % 380:(seed * 11) % 380 + w]
        sm = gblur(sm, max(rx, ry) * 0.45) * np.clip(0.55 + 0.3 * gblur(mm, 2.5), 0, 1.1)
        col = col * (1 - k * sm)
    if edge:                                              # the cut edge of grey card reads as a thin dark line
        er = cv2.erode(a, np.ones((3, 3), np.uint8), iterations=1)
        e = np.clip((a - er) / 255, 0, 1)
        col = col * (1 - edge * e)
    reg[:] = reg * (1 - al) + col[..., None] * al
    for (cx, cy, rx, ry, rot, v) in sweat:
        s = np.zeros((h, w), np.float32)
        cv2.ellipse(s, (int(cx - x0), int(cy - y0)), (max(int(rx), 1), max(int(ry), 1)), rot, 0, 360, 1.0, -1, cv2.LINE_AA)
        s = gblur(s, 1.0)[..., None] * al
        reg[:] = reg * (1 - 0.8 * s) + v * 0.8 * s


def pencil(C, pts, width=2, tone=60, alpha=0.85, seed=0):
    """graphite line, broken by the tooth of the card (pencil skips on the scan's low points)."""
    H, W = C.shape[:2]
    pts = np.asarray(pts, np.float32)
    x0, y0 = int(max(pts[:, 0].min() - 6, 0)), int(max(pts[:, 1].min() - 6, 0))
    x1, y1 = int(min(pts[:, 0].max() + 7, W)), int(min(pts[:, 1].max() + 7, H))
    if x1 <= x0 or y1 <= y0: return
    m = np.zeros((y1 - y0, x1 - x0), np.float32)
    cv2.polylines(m, [np.int32(np.round((pts - [x0, y0]) * 4))], False, 1.0, max(1, int(width * 4)), cv2.LINE_AA, shift=2)
    tooth = np.clip(0.86 + 0.10 * (CARD[(y0 + seed) % 380:(y0 + seed) % 380 + y1 - y0, (x0 + seed) % 380:(x0 + seed) % 380 + x1 - x0] - 1) / 0.055, 0.6, 1)
    m = np.clip(gblur(m, 0.4) * tooth * alpha, 0, 1)[..., None]
    C[y0:y1, x0:x1] = C[y0:y1, x0:x1] * (1 - m) + tone * m


def brad(C, x, y, r):
    """brass split pin, painted grey (neutral)."""
    x0, y0 = int(x - r - 3), int(y - r - 3)
    if x0 < 0 or y0 < 0 or x0 + 2 * r + 6 > C.shape[1] or y0 + 2 * r + 6 > C.shape[0]: return
    n = int(2 * r + 6)
    reg = C[y0:y0 + n, x0:x0 + n]
    for (cx, cy, rr, v, k) in ((x + 1, y + 1, r, 40, .5), (x, y, r, 150, .95), (x - r * .3, y - r * .35, r * .38, 225, 1)):
        d = np.zeros((n, n), np.float32)
        cv2.circle(d, (int((cx - x0) * 4), int((cy - y0) * 4)), max(1, int(rr * 4)), 1.0, -1, cv2.LINE_AA, shift=2)
        d = gblur(d, 0.5)[..., None] * k
        reg[:] = reg * (1 - d) + v * d


def soft_shadow(C, cx, cy, rx, ry, k=0.5):
    """contact shadow on the ground under a figure (soft overcast: no hard cast shadow)."""
    H, W = C.shape[:2]
    m = np.zeros((H, W), np.float32)
    cv2.ellipse(m, (int(cx), int(cy)), (int(rx), int(ry)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    m = gblur(m, ry * 0.7 + 2)[..., None]
    C[:] = C * (1 - k * m)


def capsule(p0, p1, r0, r1, n=8):
    (x0, y0), (x1, y1) = p0, p1
    a = math.atan2(y1 - y0, x1 - x0); pts = []
    for k in range(n + 1):
        t = a + math.pi / 2 + math.pi * k / n; pts.append((x0 + r0 * math.cos(t), y0 + r0 * math.sin(t)))
    for k in range(n + 1):
        t = a - math.pi / 2 + math.pi * k / n; pts.append((x1 + r1 * math.cos(t), y1 + r1 * math.sin(t)))
    return pts


# ------------------------------------------------------------------ SCION #32: forward kinematics rig
BONES = {  # name: (parent, length in units of s)
    "spine": ("root", 92), "neck": ("spine", 16), "head": ("neck", 22),
    "upper_f": ("spine", 44), "fore_f": ("upper_f", 42), "hand_f": ("fore_f", 14),
    "upper_n": ("spine", 44), "fore_n": ("upper_n", 42), "hand_n": ("fore_n", 14),
    "thigh_f": ("root", 58), "shin_f": ("thigh_f", 56), "foot_f": ("shin_f", 22),
    "thigh_n": ("root", 58), "shin_n": ("thigh_n", 56), "foot_n": ("shin_n", 22),
}
ORDER = list(BONES)


def fk(root, local, s):
    W = {"root": ((root[0], root[1]), (root[0], root[1]), 0.0)}
    for b in ORDER:
        par, L = BONES[b]
        p_end = W[par][1] if par != "root" else root
        ang = W[par][2] + local[b]
        e = (p_end[0] + L * s * math.cos(math.radians(ang)), p_end[1] + L * s * math.sin(math.radians(ang)))
        W[b] = (p_end, e, ang)
    return W


def check_bones(J, s):
    err = 0.0
    for b, (par, L) in BONES.items():
        (x0, y0), (x1, y1), _ = J[b]
        err = max(err, abs(math.hypot(x1 - x0, y1 - y0) - L * s))
        if par != "root": err = max(err, math.dist(J[b][0], J[par][1]))      # child pivot sits on parent's end
    LEDGER["rig_error_max"] = max(LEDGER["rig_error_max"], err)
    assert err < 0.5, f"bone length / attachment error {err}"


def to_local(absd):
    return {b: absd[b] - (absd[BONES[b][0]] if BONES[b][0] != "root" else 0.0) for b in ORDER}


def pose_abs(torso, head, arm_f, arm_n, leg_f, leg_n):
    return dict(spine=torso, neck=torso + (head - torso) * 0.5, head=head,
                upper_f=arm_f[0], fore_f=arm_f[1], hand_f=arm_f[2], upper_n=arm_n[0], fore_n=arm_n[1], hand_n=arm_n[2],
                thigh_f=leg_f[0], shin_f=leg_f[1], foot_f=leg_f[2], thigh_n=leg_n[0], shin_n=leg_n[1], foot_n=leg_n[2])


def smoothstep(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)


def interp_keys(keys, t):
    """poses on twos: t quantised to 1/12 s; angles eased, rounded to whole degrees."""
    t = math.floor(t * 12) / 12
    if t <= keys[0][0]: k0 = k1 = keys[0]; u = 0
    elif t >= keys[-1][0]: k0 = k1 = keys[-1]; u = 0
    else:
        for i in range(len(keys) - 1):
            if keys[i][0] <= t < keys[i + 1][0]:
                k0, k1 = keys[i], keys[i + 1]; u = smoothstep((t - k0[0]) / (k1[0] - k0[0])); break
    root = (k0[1][0] + (k1[1][0] - k0[1][0]) * u, k0[1][1] + (k1[1][1] - k0[1][1]) * u)
    def lerp_ang(a, b): d = (b - a + 180) % 360 - 180; return a + d * u
    ab = {b: round(lerp_ang(k0[2][b], k1[2][b])) for b in ORDER}
    return root, to_local(ab)


def shift(J, dx, dy=0):
    return {k: ((v[0][0] + dx, v[0][1] + dy), (v[1][0] + dx, v[1][1] + dy), v[2]) for k, v in J.items()}


# ------------------------------------------------------------------ cut-card figure pieces, defined per bone frame
def bframe(J, b):
    p0, p1, ang = J[b]
    L = math.dist(p0, p1); ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return p0, L, (ux, uy), (-uy, ux)


def bpoly(J, b, shape, s, facing):
    """shape: [(u = fraction along bone, v = across in s units, +v = facing side)]"""
    p0, L, (ux, uy), (nx, ny) = bframe(J, b)
    return [(p0[0] + u * L * ux + v * s * facing * nx, p0[1] + u * L * uy + v * s * facing * ny) for u, v in shape]


def hframe(J, s, facing):
    """head frame: origin at head centre; f toward the face, up along the head bone."""
    p0, p1, ang = J["head"]
    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    fx, fy = -uy * facing, ux * facing
    hc = (p0[0] + ux * 6 * s, p0[1] + uy * 6 * s)
    return lambda f, up: (hc[0] + (f * fx + up * ux) * s, hc[1] + (f * fy + up * uy) * s)


def tube(u0, u1, r0, r1):
    return [(u0, -r0 * .9), (u0 - .04, 0), (u0, r0 * .9), (u1, r1), (u1 + .05, 0), (u1, -r1)]


HEAD = [(-15, 3), (-14, 12), (-9, 18.5), (-1, 21), (7, 19.5), (12, 15), (14.5, 9), (14, 5.5), (16, 3), (19.5, -2.5),
        (18.6, -4), (15.5, -4.8), (16.4, -7.6), (15, -9.4), (15.8, -11.6), (13.6, -15.4), (9.5, -18.4), (3, -17),
        (-4, -12.5), (-8.5, -9), (-12, -4)]
NECK = [(-0.2, -7.5), (1.2, -8.5), (1.2, 8.5), (-0.2, 7)]
BOOT = [(-0.15, -8), (0.25, -8.5), (0.62, -6), (1.0, -4.5), (1.18, -1), (1.12, 4.2), (0.2, 5.6), (-0.35, 5.2), (-0.38, -4)]
HAND = [(-0.2, -5.6), (0.55, -6.2), (1.25, -5.4), (1.62, -3.2), (1.72, 0.2), (1.5, 3.8), (1.0, 5.0), (0.95, 5.2),
        (1.25, 8.6), (1.05, 9.8), (0.6, 7.0), (0.2, 5.8), (-0.2, 5.2)]

TONES = {
    "B": dict(shirt=174, collar=198, skin=178, leg=88, boot=50, hair=214, hairline=120),
    "C": dict(shirt=96, collar=110, skin=146, leg=66, boot=44, hair=46, hairline=30, band=198),
    "A": dict(shirt=142, collar=156, skin=150, leg=58, boot=40, hair=50, hairline=30, hat=88),
}


def draw_figure(C, J, s, who, facing=1, mud=1.0, gaze=0.0, between_cb=None, front_hand_cb=None, contact=None):
    T = TONES[who]; sd = {"A": 100, "B": 200, "C": 300}[who]
    shd = max(2, int(1.2 * s + 1))
    if contact: soft_shadow(C, *contact)
    # far leg + far arm: a second card a tone down
    lay(C, [bpoly(J, "thigh_f", tube(-.08, 1.02, 15, 12), s, facing)], T["leg"] * .8, mud * 1.2, sd + 1, shd)
    lay(C, [bpoly(J, "shin_f", tube(0, 1.0, 11.5, 8.5), s, facing)], T["leg"] * .8, mud * 1.5, sd + 2, shd)
    lay(C, [bpoly(J, "foot_f", BOOT, s, facing)], T["boot"] * .85, mud, sd + 3, shd)
    sl = .62 if who == "B" else 1.0
    lay(C, [bpoly(J, "upper_f", tube(-.15, sl, 11, 9.5), s, facing)], T["shirt"] * .82, mud, sd + 4, shd)
    lay(C, [bpoly(J, "fore_f", tube(-.1, 1.02, 7.5, 5.8) if who == "B" else tube(-.1, .95, 9, 7.5), s, facing)],
        (T["skin"] if who == "B" else T["shirt"]) * .82, mud, sd + 5, shd)
    lay(C, [bpoly(J, "hand_f", HAND, s, facing)], T["skin"] * .85, mud * 1.6, sd + 6, shd)
    if between_cb: between_cb(C)
    # torso: blouse / shirt, then the trouser top with its belt over the tuck
    if who == "B":
        tor = [(0.02, -19), (0.0, 16), (0.25, 17), (0.5, 21.5), (0.66, 23), (0.8, 20), (0.93, 14), (1.02, 7),
               (1.05, -2), (1.03, -12), (0.95, -19.5), (0.6, -20.5), (0.3, -20)]
    else:
        tor = [(0.02, -21), (0.0, 19), (0.3, 20), (0.6, 21), (0.85, 20), (1.0, 14), (1.06, 4), (1.05, -8),
               (1.0, -19), (0.85, -24), (0.5, -23), (0.2, -22)]
    TJ = bpoly(J, "spine", tor, s, facing)
    lay(C, [TJ], T["shirt"], mud * 1.1, sd + 7, shd + 1,
        smudges=[(*bpoly(J, "spine", [(0.42, 8)], s, facing)[0], 9 * s, 5 * s, 30, 0.35),
                 (*bpoly(J, "spine", [(0.78, -10)], s, facing)[0], 7 * s, 4 * s, -20, 0.3)])
    # pencilled placket, pocket, fold lines; collar flaps cut from a lighter card
    pencil(C, bpoly(J, "spine", [(0.1, 15), (0.5, 17.5 if who == "B" else 17), (0.94, 10)], s, facing), max(1.5, s * .6), 70, .6, sd)
    if who != "B":
        pencil(C, bpoly(J, "spine", [(0.66, 1), (0.66, 10), (0.52, 10), (0.52, 1), (0.66, 1)], s, facing), max(1, s * .4), 95, .4, sd + 1)
    for k in range(3):
        u = 0.22 + 0.18 * k
        pencil(C, bpoly(J, "spine", [(u, -16), (u + 0.06, -6)], s, facing), max(1, s * .45), 95, .45, sd + 2 + k)
    lay(C, [bpoly(J, "spine", [(0.86, 4), (1.06, 13), (1.02, -1)], s, facing),
            bpoly(J, "spine", [(0.9, -6), (1.07, -13), (1.04, 1)], s, facing)], T["collar"], mud * .6, sd + 8, 2)
    for k in range(3):   # buttons
        bx, by = bpoly(J, "spine", [(0.36 + 0.17 * k, 16.5 if who == "B" else 17.5)], s, facing)[0]
        brad(C, bx, by, max(1.5, s * 1.0))
    lay(C, [bpoly(J, "spine", [(-0.16, -21), (-0.16, 19), (0.1, 19.5), (0.1, -21)], s, facing)], T["leg"], mud * 1.2, sd + 9, 2)
    pencil(C, bpoly(J, "spine", [(0.07, -20), (0.07, 18)], s, facing), max(1.5, s * .8), 40, .8, sd + 3)
    # neck, back hair, head, face, front hair / headband / hat
    lay(C, [bpoly(J, "neck", NECK, s, facing)], T["skin"] * .92, mud, sd + 10, 2)
    s0 = s; s = s * 1.22                         # puppet heads cut a size large, for legibility (as in shadow-play rigs)
    H = hframe(J, s, facing)
    if who == "B":
        back = [(9, 17), (2, 23.5), (-8, 23), (-17, 15), (-21, 3), (-21, -9), (-20, -24), (-17.5, -15), (-16, -29),
                (-13.5, -17), (-11, -27), (-9.5, -14), (-7.5, -22), (-6.5, -10), (-9, -4), (-8, 7), (0, 14), (8, 13)]
        lay(C, [[H(*p) for p in back]], T["hair"] * .82, 0.2, sd + 11, 2)
        for k in range(6):
            q = -19 + 2.4 * k
            pencil(C, [H(q, 8), H(q - 0.6, -10 - (k % 3) * 5)], max(1, s * .35), 96, .5, sd + 50 + k)
    hsw = [(*H(9, 13), 2.4 * s, 0.6 * s, -8, 222), (*H(18.6, -2.4), 0.9 * s, 0.6 * s, 0, 216),
           (*H(7.5, -2.5), 1.6 * s, 0.5 * s, 35, 208)]
    lay(C, [[H(*p) for p in HEAD]], T["skin"], mud * 0.5, sd + 12, shd, sweat=hsw, edge=0.6,
        smudges=[(*H(4, -11), 5 * s, 3 * s, 20, 0.22), (*H(-4, 12), 5 * s, 2.4 * s, -10, 0.16)])
    lay(C, [[H(-7.5 + 2.8 * math.cos(q), -1.5 + 4.2 * math.sin(q)) for q in np.linspace(0, 6.28, 16, endpoint=False)]],
        T["skin"] * .9, 0, sd + 13, 0, edge=0)
    pencil(C, [H(-6, 2), H(-9, 0.5), H(-9, -3.5), H(-6.5, -5)], max(1, s * .3), 110, .5, sd + 4)          # ear
    # eye: a white of thin card, a pencilled iris that drops with her gaze, a heavy upper lid
    lay(C, [[H(*p) for p in ((7.6, 6.2), (9.8, 7.5), (12.4, 7.3), (13.6, 6.1), (12.2, 4.9), (9.6, 4.9))]], 212, 0, sd + 14, 0, edge=0, tex=False)
    gy = 6.0 - 1.1 * gaze
    pencil(C, [H(11.6, gy), H(12.2, gy)], max(2, s * 1.05), 30, 1, sd + 7)
    lidy = 7.4 - 1.6 * gaze
    pencil(C, [H(7.4, 6.0), H(9.6, lidy), H(12.4, lidy - 0.1), H(13.8, 6.0)], max(1.4, s * .55), 32, 1, sd + 5)
    pencil(C, [H(9.0, 4.8), H(12.2, 4.8)], max(1, s * .3), 92, .6, sd + 6)
    pencil(C, [H(6, 10.4), H(10, 11.6), H(14, 10.2)], max(1.5, s * .7), 40 if who != "B" else 82, .95, sd + 8)  # brow
    pencil(C, [H(16.2, -4.0), H(17.2, -4.3)], max(1, s * .45), 50, .8, sd + 9)                             # nostril
    pencil(C, [H(13.2, -10.0), H(15.4, -10.2)], max(1.2, s * .5), 42, .9, sd + 10)                         # mouth
    pencil(C, [H(12.8, -12.6), H(14.6, -12.4)], max(1, s * .3), 110, .5, sd + 11)                          # under-lip
    for k in range(4):                                                                                     # cheek hatching
        pencil(C, [H(2 + 2.2 * k, -3 - 0.5 * k), H(0 + 2.2 * k, -9 - 0.5 * k)], max(1, s * .28), 108, .45, sd + 60 + k)
    if who == "B":
        fr = [(13.5, 15), (9, 21), (1, 23), (-6, 21), (-2, 17.5), (2, 16.5), (4, 12.5), (6.5, 15.5), (8.5, 11.5), (10.2, 14.6), (12.4, 11.8)]
        strands = [[H(-6 + k * 2.6, 19 - k), H(-14 - k * 1.5, 2 - 5 * k), H(-9 + k * 2.4, 16 - k)] for k in range(3)]
        lay(C, [[H(*p) for p in fr]] + strands, T["hair"], 0.15, sd + 15, 2,
            sweat=[(*H(2, 21.5), 3 * s, .6 * s, -15, 230), (*H(-15, 2), .6 * s, 3 * s, 0, 224)])
        for k in range(6):
            q = -6 + 3.2 * k
            pencil(C, [H(q, 22 - abs(q) * .15), H(q - 2.5, 15 - k * .6)], max(1, s * .33), T["hairline"], .55, sd + 20 + k)
    if who == "C":
        cap = [(12, 15), (4, 21.5), (-8, 21), (-16, 13), (-17, 1), (-13.5, -6), (-11, 3), (-5, 11), (8, 12)]
        lay(C, [[H(*p) for p in cap]], T["hair"], 0.2, sd + 15, 2)
        band = [(15, 14.5), (5, 16.6), (-8, 16), (-17.5, 12.5), (-17, 6), (-8, 9.5), (5, 10), (14.6, 8.6)]
        tails = [[H(-16, 11), H(-25, 1), H(-23, -1.5), H(-15.5, 7)], [H(-16, 9.5), H(-21, -6), H(-18.5, -7), H(-15, 7)]]
        lay(C, [[H(*p) for p in band]] + tails, T["band"], 0.5, sd + 16, 2, sweat=[(*H(8, 14), 3 * s, .7 * s, 0, 222)])
        for k in range(9):            # pencilled pattern on the band: zigzag and dots
            q = 13 - 3.4 * k
            pencil(C, [H(q, 10.5), H(q - 1.7, 15), H(q - 3.4, 10.5)], max(1, s * .45), 50, .85, sd + 30 + k)
            pencil(C, [H(q - 1.7, 11.7), H(q - 1.5, 11.8)], max(1.5, s * .7), 40, .9, sd + 40 + k)
    if who == "A":
        brim = [(22, 13), (-21, 12.5), (-22, 9), (21, 10)]
        crown = [(13, 11), (11, 23), (-10, 24), (-13, 11)]
        lay(C, [[H(*p) for p in crown], [H(*p) for p in brim]], T["hat"], 0.5, sd + 17, 2)
    s = s0
    # near leg, near arm, (prop), near hand
    lay(C, [bpoly(J, "thigh_n", tube(-.1, 1.03, 16, 12.5), s, facing)], T["leg"], mud * 1.2, sd + 18, shd,
        smudges=[(*bpoly(J, "thigh_n", [(0.75, 2)], s, facing)[0], 10 * s, 6 * s, 0, 0.35)])
    lay(C, [bpoly(J, "shin_n", tube(0, 1.0, 12, 9), s, facing)], T["leg"], mud * 1.6, sd + 19, shd)
    lay(C, [bpoly(J, "foot_n", BOOT, s, facing)], T["boot"], mud, sd + 20, shd)
    lay(C, [bpoly(J, "upper_n", tube(-.15, sl, 11.5, 10), s, facing)], T["shirt"], mud, sd + 21, shd)
    if who == "B":    # rolled sleeve cuff: a separate lighter band
        lay(C, [bpoly(J, "upper_n", [(.5, -11), (.72, -10.5), (.72, 10.5), (.5, 11)], s, facing)], T["collar"], mud * .5, sd + 22, 2)
        lay(C, [bpoly(J, "upper_f", [(.5, -10.5), (.72, -10), (.72, 10), (.5, 10.5)], s, facing)], T["collar"] * .85, mud * .5, sd + 23, 1)
        lay(C, [bpoly(J, "upper_n", tube(.66, 1.02, 8.2, 7.6), s, facing)], T["skin"], mud, sd + 24, 2)
    lay(C, [bpoly(J, "fore_n", tube(-.1, 1.02, 8, 6) if who == "B" else tube(-.1, .95, 9.5, 8), s, facing)],
        T["skin"] if who == "B" else T["shirt"], mud * 1.2, sd + 25, shd)
    if front_hand_cb: front_hand_cb(C)
    p0, L, (ux, uy), _ = bframe(J, "hand_n")
    lay(C, [bpoly(J, "hand_n", HAND, s, facing)], T["skin"], mud * 1.8, sd + 26, shd,
        sweat=[(p0[0] + ux * L * .9, p0[1] + uy * L * .9, 2.6 * s, 0.8 * s, 0, 214)])
    for b in ("thigh_f", "shin_f", "upper_f", "fore_f", "hand_f", "thigh_n", "shin_n", "foot_n", "upper_n", "fore_n", "hand_n"):
        brad(C, *J[b][0], max(2, 1.6 * s))


def bag_piece(C, hx, hy, s, ang=0, seed=500):
    """the dry bag: dark oilcloth roll-top (handmade card), hanging from the hand point (hx, hy) by its strap."""
    c, sn = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    R = lambda x, y: (hx + (x * c - y * sn) * s, hy + (x * sn + y * c) * s)
    strap = [R(-3, 0), R(3, 0), R(11, 16), R(7, 17), R(0, 4), R(-7, 17), R(-11, 16)]
    body = [R(-21, 18), R(21, 18), R(24, 30), R(25, 60), R(22, 70), R(-22, 70), R(-25, 60), R(-24, 30)]
    roll = [R(-23, 14), R(23, 14), R(24, 24), R(-24, 24)]
    lay(C, [strap], 132, 0.3, seed, 2)
    lay(C, [body], 60, 0.5, seed + 1, max(2, int(s * 2)), sweat=[(*R(-14, 30), 6 * s, 1.0 * s, -8, 104)])
    lay(C, [roll], 82, 0.4, seed + 2, 2)
    pencil(C, [R(-22, 19), R(22, 19)], max(1, s * .6), 40, .8, seed)
    brad(C, *R(0, 19), max(2, 1.6 * s))


# ------------------------------------------------------------------ the foraged shoe (#29 cut in plates.py)
SHOE_FULL = np.asarray(Image.open(CUT / "shoe.png").convert("RGBA"), np.float32)
hS, wS = SHOE_FULL.shape[:2]
SHOE_FULL[int(hS * .55):, :int(wS * .14), 3] = 0
SHOE_FULL[int(hS * .93):, :, 3] = 0


def shoe_img(width, rot):
    im = Image.fromarray(SHOE_FULL.astype(np.uint8), "RGBA").rotate(rot, expand=True, resample=Image.BICUBIC)
    im = im.resize((width, max(1, int(width * im.height / im.width))), Image.LANCZOS)
    return np.asarray(im, np.float32)


def shoe_on_water(C, cx, wl, width, rot, t, water_tone=80):
    s = shoe_img(width, rot); h, w = s.shape[:2]
    bob = 2.5 * math.sin(2 * math.pi * t / 0.9)
    y0 = wl - h * 0.78 + bob; x0 = cx - w / 2
    r = s[::-1].copy()
    for yy in range(h):
        r[yy] = np.roll(r[yy], int(3 * math.sin(yy * 0.5 + t * 9)), axis=0)
    r[..., :3] *= 0.55; r[..., 3] *= np.linspace(0.45, 0, h)[:, None]
    over(C, r[: h // 2], x0, wl + 2)
    m = np.zeros(C.shape[:2], np.float32)
    for k in range(3):
        rx = w * (0.55 + 0.25 * k + 0.08 * ((t * 1.3) % 1))
        for a0 in range(0, 360, 45):
            cv2.ellipse(m, (int(cx), int(wl)), (int(rx), int(rx * .12)), 0, a0 + 9 * k, a0 + 26 + 9 * k, 1.0, 2, cv2.LINE_AA)
    m = gblur(m, 0.7) * 0.3
    C[:] = C * (1 - m[..., None]) + 200 * m[..., None]
    rows = np.arange(h) + y0
    sub = np.clip((rows - wl) / (h * .22 + 1), 0, 1)[:, None]
    s2 = s.copy(); s2[..., :3] = s2[..., :3] * (1 - .6 * sub[..., None]) + water_tone * .6 * sub[..., None]
    s2[..., 3] *= (1 - .5 * sub)
    over(C, s2, x0, y0)


def shoe_at(C, J, bone, width, rot_extra=0, du=1.0):
    """parented to a hand bone (FK): the heel sits in the hand and rotates with it."""
    p0, p1, ang = J[bone]
    s = shoe_img(width, -ang + rot_extra); h, w = s.shape[:2]
    px = p0[0] + (p1[0] - p0[0]) * du; py = p0[1] + (p1[1] - p0[1]) * du
    over(C, s, px - w * .5, py - h * .5)


# ------------------------------------------------------------------ planes (#44)
def grade_plate(L):
    p2, p98 = np.percentile(L, 2), np.percentile(L, 98)
    return np.clip(35 + (L - p2) * 185 / max(p98 - p2, 1), 0, 255)


def load_cut(name, scale, blur=0.0, rot=0.0, flip=False, gamma=0.8):
    im = Image.open(CUT / f"{name}.png").convert("RGBA")
    if gamma != 1:   # the plate's one monotone curve: (already p2/p98 -> L35/220) with a lifted midtone, neutral
        a0 = np.asarray(im, np.float32); c = np.clip((a0[..., :3] - 35) / 185, 0, 1)
        a0[..., :3] = 35 + 185 * c ** gamma
        im = Image.fromarray(np.clip(a0, 0, 255).astype(np.uint8), "RGBA")
    if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if rot: im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    a = np.asarray(im, np.float32)
    if blur:
        al = a[..., 3:] / 255
        c = gblur(a[..., :3] * al, blur); al2 = gblur(al[..., 0], blur)[..., None]
        a = np.dstack([c / np.maximum(al2, 1e-3), al2 * 255])
    return np.clip(a, 0, 255)


IAw = np.asarray(Image.open(IA_WATER).convert("L"), np.float32)[430:1080, 900:1440]
IAw = cv2.resize(IAw, (1200, 660), interpolation=cv2.INTER_AREA)
IAw = grade_plate(IAw) * 0.55 + 30
WATER = np.dstack([IAw] * 3 + [np.full(IAw.shape, 255, np.float32)])


def water_plane(C, top, t, x_cam, x0=0, x1=None):
    """foraged 1920 water, cut into three torn strips sliding at different rates (4/7/11 px per 12 poses)."""
    H, W = C.shape[:2]; x1 = W if x1 is None else x1
    # the jungle already laid above the waterline, mirrored into the water (darker, rippled per row)
    hh = H - top
    src = C[max(top - hh, 0):top][::-1].copy()
    if src.shape[0] < hh: src = np.concatenate([src, np.repeat(src[-1:], hh - src.shape[0], 0)], 0)
    ph = math.floor(t * 12) / 12
    for yy in range(hh):
        src[yy] = np.roll(src[yy], int(round((1 + yy * 0.02) * math.sin(yy * 0.16 + ph * 6))), axis=0)
    src = gblur(src, 1.2) * 0.66 + 14
    for k, (y0, sp) in enumerate(((0, 4), (50, 7), (120, 11))):
        if top + y0 >= H: continue
        off = int((math.floor(t * 12) * sp / 2) % 300) + int(x_cam) % 300
        strip = WATER[y0:, off: off + W]
        st = strip[: H - top - y0].copy()
        ed = (np.sin(np.arange(W) * 0.05 + k) * 3 + np.sin(np.arange(W) * 0.17 + 2 * k) * 1.5 + 4).astype(int)
        rows = np.arange(st.shape[0])[:, None]
        st[..., 3] *= (rows >= ed[None, :st.shape[1]])
        st[:, :x0, 3] = 0; st[:, x1:, 3] = 0
        rr = src[y0:y0 + st.shape[0], :st.shape[1]]
        st[..., :3] = st[..., :3] * 0.45 + rr * 0.55                    # foraged water texture x mirrored jungle
        over(C, st, 0, top + y0)
    g = np.zeros(C.shape[:2], np.float32); g[top:top + 5, x0:x1] = 0.25
    C[:] = C * (1 - g[..., None]) + 175 * g[..., None]


P0 = load_cut("P0_far", 0.70, blur=0.6)          # far wall: deepest plane, most blur
P0w = load_cut("P0_far", 0.78, blur=0.4)
P1 = load_cut("P1_flange", 0.62, blur=0.5)
P1w = load_cut("P1_flange", 0.45, blur=0.3)
P3 = load_cut("P3_leaves", 0.58, blur=1.6); P3[..., :3] *= 0.78
P3f = P3[:, ::-1].copy()
P4R = load_cut("P1_flange", 0.55, blur=3.0, rot=-24)
_f = np.asarray(Image.open(CUT / "P4_fern.png").convert("RGBA"), np.float32)
_a = _f[..., 3] * np.clip((140 - gblur(_f[..., 0], 1.5)) / 35, 0, 1)
hF, wF = _a.shape
yy, xx = np.mgrid[0:hF, 0:wF]
_a *= np.clip(np.minimum(np.minimum(xx, wF - xx), np.minimum(yy, hF - yy)) / 90.0, 0, 1)
_f[..., 3] = _a
FERN = np.asarray(Image.fromarray(_f.astype(np.uint8), "RGBA").resize((int(wF * .5), int(hF * .5)), Image.LANCZOS), np.float32)
_al = FERN[..., 3:] / 255
FERN = np.dstack([gblur(FERN[..., :3] * _al, 1.0) / np.maximum(gblur(_al[..., 0], 1.0)[..., None], 1e-3), gblur(_al[..., 0], 1.0)[..., None] * 255])


def bank_card(C, pts, seed, tone=58, roots=()):
    lay(C, [pts] + list(roots), tone, 1.5, seed=seed, shadow=6, edge=0.3)


def plank(C, p0, p1, th0, th1, deflect_at=None, defl=0.0, seed=700, tone=192):
    """pale card plank, pencil-scored grain; bends as a 2-segment polyline under its occupant; thinner where far."""
    (x0, y0), (x1, y1) = p0, p1
    u = 0.5 if deflect_at is None else deflect_at
    mid = (x0 + (x1 - x0) * u, y0 + (y1 - y0) * u + (defl if deflect_at is not None else 0))
    top = [p0, mid, p1]
    thm = th0 + (th1 - th0) * u
    bot = [(x1, y1 + th1), (mid[0], mid[1] + thm), (x0, y0 + th0)]
    lay(C, [top + bot], tone, 0.4, seed=seed, shadow=6,
        sweat=[(mid[0] - 30, mid[1] + 1.5, 50, 1.2, math.degrees(math.atan2(y1 - y0, x1 - x0)), 216)])
    for k in range(3):
        q = (k + 1) / 4
        pencil(C, [(x0, y0 + th0 * q), (mid[0], mid[1] + thm * q), (x1, y1 + th1 * q)], 1, 118, 0.45, seed + k)
    return top


def liana(C, pts, seed=650, r=5):
    """twisted paper cord from the canopy (handmade), pencilled twist."""
    P = []
    for i in range(len(pts) - 1):
        for q in np.linspace(0, 1, 10, endpoint=False):
            P.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * q, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * q))
    P.append(pts[-1])
    lay(C, [capsule(P[i], P[i + 1], r, r, 4) for i in range(len(P) - 1)], 70, 0.6, seed=seed, shadow=4)
    for i in range(0, len(P) - 1):
        a, b = P[i], P[i + 1]
        pencil(C, [(a[0], a[1] - r * .8), (b[0], b[1] + r * .8)], 1.4, 128, 0.6, seed + i)


def sag(a, b, depth, n=8):
    return [(a[0] + (b[0] - a[0]) * q, a[1] + (b[1] - a[1]) * q + depth * math.sin(math.pi * q)) for q in np.linspace(0, 1, n)]


def caption(img, text):
    im = Image.fromarray(img.astype(np.uint8)).convert("RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    f = font("serif", 24); tw = d.textlength(text, font=f)
    cx, cy = im.width / 2, im.height - 40
    d.rectangle((cx - tw / 2 - 14, cy - 18, cx + tw / 2 + 14, cy + 16), fill=(45, 45, 45, 140))
    d.text((cx, cy), text, font=f, fill=(230, 230, 230, 255), anchor="mm")
    return np.asarray(Image.alpha_composite(im, ov).convert("RGB"), np.float32)


# ------------------------------------------------------------------ pose authoring helper (keys only; frames use fk)
def arm_to(hip, torso, s, target, bend=1, hand=None):
    sh = (hip[0] + 92 * s * math.cos(math.radians(torso)), hip[1] + 92 * s * math.sin(math.radians(torso)))
    l1, l2 = 44 * s, 42 * s
    dx, dy = target[0] - sh[0], target[1] - sh[1]
    D = math.hypot(dx, dy); d = min(D, (l1 + l2) * 0.999)
    base = math.degrees(math.atan2(dy, dx))
    c = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    a1 = math.degrees(math.acos(max(-1, min(1, c))))
    if bend == "down":            # choose the elbow solution that hangs lower (forearm comes up to the chest)
        cand = [base - a1, base + a1]
        up = max(cand, key=lambda q: sh[1] + l1 * math.sin(math.radians(q)))
    else:
        up = base - bend * a1
    e = (sh[0] + l1 * math.cos(math.radians(up)), sh[1] + l1 * math.sin(math.radians(up)))
    tx, ty = sh[0] + dx * d / max(D, 1e-6), sh[1] + dy * d / max(D, 1e-6)
    fo = math.degrees(math.atan2(ty - e[1], tx - e[0]))
    return (up, fo, fo if hand is None else hand)


# ------------------------------------------------------------------ beat 1: S5 medium-close (plank, water, A across)
SB, SC, SA = 1.85, 1.95, 0.72
GROUND = 452                      # near-bank top under B's knees
SHOE_POS = (452, 478)             # in the water at the plank foot
SEIZA = ((10, 186, 182), (18, 190, 182))
CROUCH = ((-22, 98, 0), (-10, 104, 0))


def kB(t, hip, torso, head, far_t, near_t, legs, bf=-1, bn=1, hand_n=None, hand_f=None):
    return (t, hip, pose_abs(torso, head, arm_to(hip, torso, SB, far_t, bf, hand_f), arm_to(hip, torso, SB, near_t, bn, hand_n), *legs))


KB = [  # B faces right: the plank foot and the shoe are frame right. Hip heights follow the ground (452).
    kB(0.00, (236, 384), -74, -60, (172, 330), (360, 300), CROUCH),       # crouched, bag in her far hand, sees the shoe
    kB(0.40, (228, 386), -84, -64, (156, 318), (370, 300), CROUCH),       # pushes it back into C's hands
    kB(0.80, (240, 396), -60, -40, (250, 360), (400, 360), CROUCH),       # far hand returns empty; she lowers
    kB(1.25, (248, 412), -36, -16, (330, 420), (440, 452), SEIZA),        # knees down, bends, near hand reaches
    kB(1.60, (252, 413), -30, -10, (350, 430), (452, 468), SEIZA, hand_n=20),  # her hand card over the satin: grasp
    kB(2.10, (248, 412), -58, -38, (360, 330), (400, 330), SEIZA),        # rises with it
    kB(2.60, (246, 410), -84, -74, (296, 300), (306, 304), SEIZA, bf="down", bn="down", hand_n=-50, hand_f=-140),   # to her chest
    kB(3.60, (246, 409), -86, -76, (294, 298), (304, 302), SEIZA, bf="down", bn="down", hand_n=-50, hand_f=-140),
]


def kC(t, hip, torso, head, far_t, near_t, hf=None, hn=None):
    return (t, hip, pose_abs(torso, head, arm_to(hip, torso, SC, far_t, -1, hf), arm_to(hip, torso, SC, near_t, -1, hn),
                             (-28, 100, 0), (-18, 96, 0)))


KC = [  # C crouched on the near bank at frame left, facing right, hands out for the bag
    kC(0.00, (30, 410), -78, -72, (140, 330), (154, 342)),
    kC(0.40, (36, 408), -76, -66, (150, 326), (164, 338)),
    kC(0.90, (24, 412), -86, -84, (100, 300), (114, 312)),            # pulls it to his chest
    kC(3.60, (22, 412), -88, -86, (96, 296), (110, 308)),
]
A_POSE = pose_abs(-90, -96, (100, 94, 94), (-150, -110, -100), (96, 92, 0), (84, 88, 0))   # A on the far bank, one hand up on the liana


def close_frame(t):
    cam = -16 * smoothstep(t / CLOSE_END) + 3 * math.sin(t * 0.7)
    C = np.zeros((PH, PW, 3), np.float32) + 90
    over(C, P0, -150 - cam * .15, -170)                                  # P0 far wall (parallax 0.15)
    over(C, P1, -320 - cam * .35, 130)                                   # P1 buttress flange (0.35)
    water_plane(C, 372, t, 40 - cam)
    fb = lambda x: x - cam * .7                                          # the far bank sits behind the figures' plane
    bank_card(C, [(fb(560), 338), (fb(680), 326), (840, 330), (840, 372), (fb(600), 376), (fb(555), 360)], 640, 66,
              roots=[capsule((fb(600), 356), (fb(560), 392), 5, 2)])
    JA = fk((fb(690), 334 - (58 + 56) * SA * .99), to_local(A_POSE), SA); check_bones(JA, SA)
    draw_figure(C, JA, SA, "A", facing=-1, mud=1.2, contact=(fb(690), 335, 18, 3, .5))
    liana(C, [(-30, 70), (200, 128), (420, 150), JA["hand_n"][1], (850, 120)], r=4)
    plank(C, (380 - cam, 466), (fb(612), 336), 18, 9)
    bank_card(C, [(-40 - cam, GROUND - 2), (150 - cam, GROUND - 8), (300 - cam, GROUND), (390 - cam, GROUND + 10),
                  (420 - cam, GROUND + 40), (440 - cam, PH + 20), (-40 - cam, PH + 20)], 600, 58,
              roots=[capsule((330 + 40 * k - cam, GROUND + 20), (410 + 40 * k - cam, GROUND + 70 + 12 * k), 8, 3) for k in range(2)])
    bag_holder = "B" if t < T_BAG else "C"
    shoe_holder = "water" if t < T_SHOE else "B"
    rB, lB = interp_keys(KB, t); JB = fk(rB, lB, SB); check_bones(JB, SB); JB = shift(JB, -cam)
    rC, lC = interp_keys(KC, t); JC = fk(rC, lC, SC); check_bones(JC, SC); JC = shift(JC, -cam)
    gaze = smoothstep((t - 0.3) / 0.6) * (1 - smoothstep((t - 2.4) / 0.6))

    draw_figure(C, JC, SC, "C", 1, mud=1.1, contact=(JC["root"][1][0] + 50, 480, 100, 10, .45))
    b_bag = None

    def shoe_cb(Cn):
        if shoe_holder == "water":
            shoe_on_water(Cn, SHOE_POS[0] - cam, SHOE_POS[1], 118, 4, t)
        else:
            rise = smoothstep((t - 1.9) / 0.7)
            p0, p1, ang = JB["hand_n"]
            rot = (1 - rise) * (-ang + 30) + rise * 6                    # parented to the hand; settles upright at her chest
            sh = shoe_img(118, rot); h, w = sh.shape[:2]
            px = p0[0] + (p1[0] - p0[0]) * .7; py = p0[1] + (p1[1] - p0[1]) * .7
            over(Cn, sh, px - w * (.5 - .05 * rise), py - h * (.5 - .1 * rise))
    draw_figure(C, JB, SB, "B", 1, mud=1.0, gaze=gaze, between_cb=b_bag, front_hand_cb=shoe_cb,
                contact=(JB["root"][1][0] + 40, GROUND + 2, 110, 9, .5))
    # the bag hangs nearest the camera, from whichever hand holds it (FK-parented); its holder's hand is re-laid over the strap
    if bag_holder == "B":
        hx, hy = JB["hand_f"][1]; bag_piece(C, hx, hy - 4, 1.8, 4)
        lay(C, [bpoly(JB, "hand_f", HAND, SB, 1)], TONES["B"]["skin"] * .9, 1.6, 206, 2)
    else:
        hx, hy = JC["hand_n"][1]; bag_piece(C, hx + 4, hy - 4, 1.8, -6)
        lay(C, [bpoly(JC, "hand_n", HAND, SC, 1)], TONES["C"]["skin"], 1.8, 326, 2)
    over(C, P3, 600 - cam * 1.5, -420)                                   # P3 big leaves (1.5), canopy darker above
    over(C, P3f, -620 - cam * 1.5, -520)
    over(C, FERN, 700 - cam * 2.0, -60)                                  # P4 fern (2.0) and the root diagonal low left
    over(C, P4R, -360 - cam * 2.0, 440)
    return C, dict(bag=bag_holder, shoe=shoe_holder, plank_occupant=None,
                   hands_B=["bag" if bag_holder == "B" else "free", "shoe" if shoe_holder == "B" else "free"])


# ------------------------------------------------------------------ beat 2: LEDGER insert (paper scan, pencil script)
LINE1 = ["1 A", "2 B (sac)", "3 C"]
LINE2 = ["1 A", "2 C (sac)", "3 B"]
RNG_H = np.random.default_rng(41)
JIT = RNG_H.normal(0, 1, (80, 3))


def script_mask(shape, parts, x, y, scale, upto, seed):
    """single-stroke Hershey script letters, each with its own hand jitter (baseline, size, slant), revealed
    stroke by stroke; returns mask and pen position."""
    H, W = shape
    mask = np.zeros((H * 2, W * 2), np.uint8)
    cx = x; n = 0; pen = (x, y)
    for pi, part in enumerate(parts):
        for ch in part:
            if n >= upto: break
            frac = min(1.0, upto - n)
            j = JIT[(n + seed) % 80]
            sc = scale * (1 + 0.05 * j[0])
            (tw, th), _ = cv2.getTextSize(ch, cv2.FONT_HERSHEY_SCRIPT_COMPLEX, sc, 2)
            g = np.zeros_like(mask)
            by = y + 2.2 * j[1] + 3 * math.sin(n * 0.4 + seed)
            cv2.putText(g, ch, (int(cx * 2), int(by * 2)), cv2.FONT_HERSHEY_SCRIPT_COMPLEX, sc * 2, 255, 3, cv2.LINE_AA)
            if abs(j[2]) > 0.05:                         # each letter leans its own way
                M = cv2.getRotationMatrix2D((cx * 2 + tw, by * 2), 6 * j[2], 1.0); g = cv2.warpAffine(g, M, (g.shape[1], g.shape[0]))
            if frac < 1: g[:, int((cx + tw * frac) * 2):] = 0
            mask = np.maximum(mask, g)
            pen = (cx + tw * frac, by - th * 0.3)
            cx += tw * 0.98; n += 1
        if pi < len(parts) - 1:
            if n < upto:
                cv2.circle(mask, (int((cx + 15) * 2), int((y - 9) * 2)), 5, 255, -1, cv2.LINE_AA)
            cx += 32
    m = cv2.resize(mask.astype(np.float32) / 255, (W, H), interpolation=cv2.INTER_AREA)
    return m, pen, cx


def wobble(m, seed, amp=2.2):
    r = np.random.default_rng(seed)
    H, W = m.shape
    dx = cv2.resize(r.normal(0, 1, (H // 28 + 2, W // 28 + 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC) * amp
    dy = cv2.resize(r.normal(0, 1, (H // 28 + 2, W // 28 + 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC) * amp
    gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    return cv2.remap(m, gx + dx, gy + dy, cv2.INTER_LINEAR)


def graphite(C, m, ox, oy, tone=52, k=1.15):
    """pencil on paper: graphite catches the scan's raised tooth, skips in its hollows; pressure varies."""
    H, W = m.shape
    tooth = PAPER_TOOTH[oy:oy + H, ox:ox + W]
    press = 0.8 + 0.2 * np.sin(np.arange(W) / 37.0)[None, :]
    a = np.clip(m * (0.62 + 0.22 * tooth) * press * k, 0, 1)[..., None]
    C[:] = C * (1 - a) + tone * a


def ledger_frame(t):
    u = t - CLOSE_END
    cam = 6 * u
    C = np.zeros((PH, PW, 3), np.float32) + 60
    over(C, P0, -200 - cam * .15, -260)
    over(C, P1, -260 - cam * .5, 120)
    bank_card(C, [(-40, 300), (300, 270), (840, 290), (840, 560), (-40, 560)], 610, 56,
              roots=[capsule((-40, 520), (300, 420), 30, 14), capsule((560, 300), (840, 360), 22, 26)])
    # the card: a torn piece of paper (foraged paper scan, neutral) lying on the muddy bank, slightly rotated
    cw, ch = 640, 300
    card = np.dstack([PAPER[40:40 + ch, 60:60 + cw]] * 3).astype(np.float32)
    m_line1, _, x_end = script_mask((ch, cw), LINE1, 52, 120, 1.55, 99, 3)
    graphite(card, wobble(m_line1, 7), 60, 40)
    sk = smoothstep((u - 0.25) / 0.35)
    pen = None
    if sk > 0:
        n = 30
        pts = [(40 + (x_end - 30) * q * sk, 108 + 5 * math.sin(q * 5.0) - 4 * q) for q in np.linspace(0, 1, n)]
        sm = np.zeros((ch, cw), np.float32)
        cv2.polylines(sm, [np.int32(np.round(np.asarray(pts) * 4))], False, 1.0, 7, cv2.LINE_AA, shift=2)
        pts2 = [(p[0], p[1] + 3 + 2 * math.sin(i * .3)) for i, p in enumerate(pts)]
        cv2.polylines(sm, [np.int32(np.round(np.asarray(pts2) * 4))], False, 0.75, 5, cv2.LINE_AA, shift=2)
        graphite(card, gblur(sm, .5), 60, 40, tone=58)
        if sk < 1: pen = pts[-1]
    n2 = sum(len(p) for p in LINE2)
    up = (u - 0.75) / 1.25 * n2
    if up > 0:
        m2, pen2, _ = script_mask((ch, cw), LINE2, 52, 230, 1.55, up, 5)
        graphite(card, wobble(m2, 9), 60, 40)
        if up < n2: pen = pen2
    # mud thumbprints from her hand on the card's edge
    yy, xx = np.mgrid[0:ch, 0:cw]
    for (mx, my, r) in ((600, 40, 26), (28, 270, 20)):
        d = np.exp(-(((xx - mx) ** 2 + (yy - my) ** 2) / (2 * r * r))) * np.clip(0.4 + 0.4 * PAPER_TOOTH[:ch, :cw], 0, 1)
        card *= (1 - 0.35 * d)[..., None]
    # torn edge alpha, rotate, lay on the bank with a drop shadow
    al = np.ones((ch, cw), np.float32) * 255
    r = np.random.default_rng(3)
    nz = cv2.resize(r.normal(0, 1, (ch // 6 + 1, cw // 6 + 1)).astype(np.float32), (cw, ch))
    dist = np.minimum(np.minimum(xx, cw - 1 - xx), np.minimum(yy, ch - 1 - yy)).astype(np.float32)
    al = np.clip((dist - 6 - 4 * nz) * 120, 0, 255)
    rgba = np.dstack([card, al]).astype(np.uint8)
    im = Image.fromarray(rgba, "RGBA").rotate(-3.5 + 0.4 * u, expand=True, resample=Image.BICUBIC)
    A = np.asarray(im, np.float32)
    ox, oy = 92 - cam, 108
    sh = gblur(A[..., 3], 7) / 255
    Hh, Ww = sh.shape
    reg = C[oy + 10:oy + 10 + Hh, int(ox) + 10:int(ox) + 10 + Ww]
    reg[:] = reg * (1 - 0.55 * sh[:reg.shape[0], :reg.shape[1], None])
    over(C, A, ox, oy)
    # C's hand (cut card, FK chain forearm -> hand -> pencil) follows the pen point
    if pen is None: pen = (x_end + 40, 250) if up >= n2 else (40, 108)
    th = math.radians(-3.5 + 0.4 * u)
    px, py = pen[0] - cw / 2, pen[1] - ch / 2
    wx = ox + Ww / 2 + px * math.cos(-th) - py * math.sin(-th)
    wy = oy + Hh / 2 + px * math.sin(-th) + py * math.cos(-th)
    sH = 3.4
    pa = 52                                                     # pencil axis (deg): from tip up-right toward the hand
    pux, puy = math.cos(math.radians(pa)), math.sin(math.radians(pa))
    tip = (wx, wy); butt = (wx + pux * 200, wy + puy * 200)
    grip = (wx + pux * 62, wy + puy * 62)
    # hand bone: from wrist (down-right) to the grip; forearm continues off frame
    wrist = (grip[0] + 30, grip[1] + 52)
    hang = math.degrees(math.atan2(grip[1] - wrist[1], grip[0] - wrist[0]))
    JH = {"fore_n": ((wrist[0] + 300, wrist[1] + 260), wrist, hang), "hand_n": (wrist, grip, hang)}
    lay(C, [capsule(JH["fore_n"][0], wrist, 13 * sH, 10 * sH)], 92, 0.8, 803, 7)               # C's dark sleeve
    lay(C, [capsule((wrist[0] + 8, wrist[1] + 8), (wrist[0] + 60, wrist[1] + 55), 8.5 * sH, 8.5 * sH)], 140, 1.2, 805, 4)  # wrist
    def PENCIL_CB():
        lay(C, [capsule((tip[0] + pux * 18, tip[1] + puy * 18), butt, 5.5, 6.5, 4)], 120, 0.1, 801, 4)   # pencil stub (card)
        lay(C, [[tip, (tip[0] + pux * 20 - puy * 5.5, tip[1] + puy * 20 + pux * 5.5),
                 (tip[0] + pux * 20 + puy * 5.5, tip[1] + puy * 20 - pux * 5.5)]], 205, 0, 802, 0, edge=0.3)  # bare wood
        pencil(C, [tip, (tip[0] + pux * 6, tip[1] + puy * 6)], 2.0, 38, 1, 3)                          # graphite point
    lay(C, [bpoly(JH, "hand_n", HAND, sH, -1)], 146, 1.6, 804, 5, sweat=[(*bpoly(JH, "hand_n", [(0.9, -2)], sH, -1)[0], 9, 2, hang, 214)],
        smudges=[(*bpoly(JH, "hand_n", [(0.5, 1)], sH, -1)[0], 20, 12, hang, 0.3)])
    PENCIL_CB()
    lay(C, [bpoly(JH, "hand_n", [(0.7, 5), (1.15, 10.5), (1.45, 9), (1.05, 4)], sH, -1)], 150, 1.2, 806, 2)   # thumb over the pencil
    for k in range(3):                                                                            # pencilled knuckles
        q0 = bpoly(JH, "hand_n", [(1.1 + 0.18 * k, -5), (1.25 + 0.18 * k, -1)], sH, -1)
        pencil(C, q0, 1.5, 85, .55, 20 + k)
    brad(C, *wrist, 5)
    over(C, P3, 610 - cam * 1.5, -450)
    over(C, FERN, -330 + cam * 1.5, 400)
    st = "1 A · 2 B (sac) · 3 C" if up <= 0 else ("1 A · 2 C (sac) · 3 B" if up >= n2 else "rewriting")
    return C, dict(ledger=st)


# ------------------------------------------------------------------ beat 3: S8 wide, B crosses last
S3 = 1.0
WALK0, WALK1 = 0.32, 0.70


def walk_pose(phase):
    sw = math.sin(phase * 2 * math.pi)
    th_f = 90 - 22 * sw; th_n = 90 + 22 * sw
    kb_f = 22 * max(0, math.cos(phase * 2 * math.pi)); kb_n = 22 * max(0, -math.cos(phase * 2 * math.pi))
    return pose_abs(-86, -70, (-104, -94, -94), (70, -40, -110), (th_f, th_f + kb_f, 0), (th_n, th_n + kb_n, 0))


C_WAIT = pose_abs(-92, -82, (50, -30, -60), (40, -40, -70), (94, 92, 0), (86, 90, 0))


def cross_frame(t):
    u = t - LEDGER_END
    span = DUR - LEDGER_END
    cam = 40 * smoothstep(u / span)
    C = np.zeros((PH, PW, 3), np.float32) + 90
    over(C, P0w, -120 - cam * .15, -170)
    over(C, P1w, -330 - cam * .35, 150)
    px0, px1 = 170 - cam, 690 - cam
    plank_y0, plank_y1 = 392, 384
    ufrac = WALK0 + (WALK1 - WALK0) * smoothstep(u / span)
    bx = px0 + (px1 - px0) * ufrac
    defl = 8 * math.sin(math.pi * ufrac)
    clearance = int(round(14 - 10 * smoothstep(u / (span * .8))))
    ptop_b = plank_y0 + (plank_y1 - plank_y0) * ufrac + defl
    water_y = int(ptop_b + clearance)
    water_plane(C, water_y, t, 80 + cam)
    bank_card(C, [(690 - cam, 390), (770 - cam, 378), (840, 380), (840, 560), (720 - cam, 560), (700 - cam, 450)], 640, 64,
              roots=[capsule((720 - cam, 400), (690 - cam, 440), 5, 2)])
    bank_card(C, [(-40, 396), (120 - cam, 388), (200 - cam, 398), (230 - cam, 430), (200 - cam, 560), (-40, 560)], 630, 58,
              roots=[capsule((150 - cam, 420), (230 - cam, 470), 6, 2)])
    top = plank(C, (px0, plank_y0), (px1, plank_y1), 12, 12, deflect_at=ufrac, defl=defl)
    wet = np.zeros(C.shape[:2], np.float32); wet[water_y:water_y + 14, int(px0):int(px1)] = 0.45
    C[:] = C * (1 - wet[..., None]) + 72 * wet[..., None]
    plank_top_at_b = top[1][1]
    # C on the near bank with the bag, A on the far bank (both off the plank: occupancy 1)
    leg = (58 + 56) * S3
    JC = fk((90 - cam, 390 - leg * .99), to_local(C_WAIT), S3); check_bones(JC, S3)
    draw_figure(C, JC, S3, "C", 1, mud=1.2, front_hand_cb=lambda Cn: bag_piece(Cn, *JC["hand_n"][1], 0.95, -10),
                contact=(90 - cam, 392, 30, 4, .5))
    JA = fk((728 - cam, 382 - leg * .99), to_local(A_POSE), S3); check_bones(JA, S3)
    draw_figure(C, JA, S3, "A", -1, mud=1.3, contact=(728 - cam, 384, 28, 4, .5))
    phase = (u / 1.3) % 1
    pz = walk_pose(phase)
    hip_drop = 4 * abs(math.sin(phase * 2 * math.pi))
    root = (bx, plank_top_at_b - (58 + 56 + 6) * S3 + 6 + hip_drop)
    J = fk(root, to_local({b: round(v) for b, v in pz.items()}), S3); check_bones(J, S3)
    hand = J["hand_f"][1]                       # far hand rides the liana; near hand holds the shoe to her chest
    liana(C, [(-40, 40), (hand[0] - 200, hand[1] - 50), hand, (hand[0] + 200, hand[1] - 30), (JA["hand_n"][1][0], JA["hand_n"][1][1]), (860, 20)], r=3.5)

    def shoe_cb(Cn):
        sh = shoe_img(64, 6); h, w = sh.shape[:2]; p1 = J["hand_n"][1]
        over(Cn, sh, p1[0] - w * .45, p1[1] - h * .55)
    draw_figure(C, J, S3, "B", 1, mud=1.0 + 0.6 * smoothstep((u - 1.6) / 0.6), front_hand_cb=shoe_cb)
    if 1.5 < u < 2.4:
        r = np.random.default_rng(int(u * 12))
        k = (u - 1.5) / 0.9
        for i in range(24):
            a = r.uniform(-2.6, -0.5); v = r.uniform(25, 70)
            x = bx + math.cos(a) * v * k * 1.3; y = water_y - 3 + math.sin(a) * v * k * 1.5 + 110 * k * k
            cv2.circle(C, (int(x), int(y)), int(r.uniform(1, 3)), (205, 205, 205), -1, cv2.LINE_AA)
    over(C, P3, 520 - cam * 1.5, -470)
    over(C, P3f, -420 - cam * 1.5, -520)
    over(C, FERN, 790 - cam * 2.0, -140)
    over(C, P4R, -300 - cam * 2.0, 440)
    return C, dict(plank_occupant="B", hands_B=["liana", "shoe"], bag="C", shoe="B", clearance_px=clearance)


# ------------------------------------------------------------------ assembly through kit.Film
def picture_rgb(t):
    if t < CLOSE_END:
        C, st = close_frame(t); cap = "« Prends le sac. »" if 0.2 < t < 1.3 else None; beat = "L-S5 close"
    elif t < LEDGER_END:
        C, st = ledger_frame(t); cap = None; beat = "L-S6 ledger insert"
    else:
        C, st = cross_frame(t); cap = "« Elle la garde. »" if t > 7.4 else None; beat = "L-S8 excerpt"
    F = np.zeros((540, 960, 3), np.float32) + 27
    F[:, PX:PX + PW] = np.clip(C, 0, 255)
    if cap: F = caption(F, cap)
    st.update(t=round(t, 4), film_t=round(FILM_T0 + t, 4), beat=beat)
    return F, st


film = Film("test-shot", seconds=DUR, boil=0, wobble=0, seed=3)


@film.picture
def frame(t, ink):
    ink.paper((27, 27, 27), grain=False)
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
    SOUND_SRC.clear()
    bed = load_audio(A / "stream.mp3", 12.0, DUR + 0.5); SOUND_SRC.append("stream.mp3 (CC0, jackthemurray)")
    bed = bed / (np.abs(bed).max() + 1e-9)
    n = len(bed); ts = np.arange(n) / 44100; env = np.ones(n)
    env[(ts >= CLOSE_END) & (ts < LEDGER_END)] = 0.35
    env[ts >= LEDGER_END] = 0.7 + 0.5 * np.clip((ts[ts >= LEDGER_END] - LEDGER_END) / 2.8, 0, 1)
    env = np.convolve(env, np.ones(2205) / 2205, mode="same")
    mix.add(bed * env * 0.32, 0.0, pan=0.15)
    ru = mix.band(mix.noise(0.32, "white"), 900, 5000) * mix.env(int(0.32 * 44100), 0.01, 0.25)
    mix.add(ru, T_BAG - 0.05, 0.5, pan=-0.5); mix.thud(T_BAG + 0.1, freq=90, gain=0.35, pan=-0.5, seconds=0.25)
    tr = mix.band(mix.noise(1.2, "white"), 1500, 6000) * 0.3
    tr = tr / (np.abs(tr).max() + 1e-9) * np.linspace(1, 0, len(tr)) ** 1.5
    mix.add(tr, T_SHOE - 0.25, 0.25, pan=0.45); SOUND_SRC.append("synth drip (kit Mix)")
    mix.click(T_SHOE, gain=0.18, pan=0.45, bright=2500)
    ru2 = mix.band(mix.noise(0.25, "white"), 600, 3500) * mix.env(int(0.25 * 44100), 0.02, 0.2)
    mix.add(ru2, 2.1, 0.25, pan=0.2)
    sk = mix.band(mix.noise(0.35, "white"), 2500, 9000) * mix.env(int(0.35 * 44100), 0.005, 0.3, 0.6)
    mix.add(sk, CLOSE_END + 0.25, 0.55)
    n2 = sum(len(p) for p in LINE2)
    for i in range(n2):
        at = CLOSE_END + 0.75 + i * 1.25 / n2
        g = mix.band(mix.noise(0.06, "white"), 3000, 9000) * mix.env(int(0.06 * 44100), 0.004, 0.05)
        mix.add(g, at, 0.30)
    for k in range(4):
        at = LEDGER_END + 0.2 + k * 0.65
        cr = mix.tone(150 + 25 * k, 0.28, "saw", vibrato=0.05) * mix.env(int(0.28 * 44100), 0.03, 0.2)
        mix.add(mix.band(cr, 200, 1400), at, 0.14, pan=0.1 * k)
        mix.step(at + 0.02, gain=0.12, surface="wood")
    sp = load_audio(A / "stream.mp3", 30.0, 1.0)
    sp = sp / (np.abs(sp).max() + 1e-9) * np.linspace(1, 0, len(sp))
    mix.add(sp, LEDGER_END + 1.52, 0.5, pan=0.1)
    mix.add(mix.lowpass(mix.noise(0.4, "white"), 1800) * mix.env(int(0.4 * 44100), 0.005, 0.35), LEDGER_END + 1.5, 0.5)


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
        dict(film_t=FILM_T0 + CLOSE_END + 0.25, event="ledger_strike", text="1 A · 2 B (sac) · 3 C"),
        dict(film_t=FILM_T0 + CLOSE_END + 2.0, event="ledger_rewrite", text="1 A · 2 C (sac) · 3 B"),
        dict(film_t="L-S8 excerpt", event="last_crossing", who="B", min_clearance_px=4),
    ]
    LEDGER["sound_sources"] = SOUND_SRC
    LEDGER["paper_scan"] = PAPER_FILE
    json.dump(LEDGER, open(SWARM / "test-shot-build" / "world-trace.json", "w"), indent=0, ensure_ascii=False)
    print("rig_error_max", LEDGER["rig_error_max"], SOUND_SRC)
