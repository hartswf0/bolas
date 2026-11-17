"""Exercises in Style (Mauro Martino) - SCION controlled variation, Direction 1 'Cut-Paper Platform'.

One small bus incident (the shove on the rear platform) frozen as an exposure sheet and re-rendered
under single-field instructions: baseline, Δ treatment = photographic-plate, Δ camera = overhead,
each at seeds 0417 and 0418. Built on films/kit.py (Film, Mix); the stage is
swarm/<slug>/stage/stage.py, the puppets swarm/<slug>/rig/rig.py (both imported, not edited).

FORAGED: Agence Rol 1916 bus plate, Agence Rol 1919 crowd plates (Gallica via Commons, PD);
engine (CC BY 4.0), street (PD) and bell (CC0) recordings via Commons. HANDMADE: facade, pavement,
platform, board, puppets, plan stage, cards. SYNTHETIC (declared): kit thud at the shove, kit click
at the stanchion and on the cards.

Run from the project root:  python3 films/mauro-martino-exercises-in-style.py   [--stills t ...]
"""
import functools, hashlib, importlib.util, json, math, os, subprocess, sys
from multiprocessing import get_context
from pathlib import Path

import numpy as np, cv2
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kit
from kit import Film

SLUG = "mauro-martino-exercises-in-style"
ROOT = HERE.parent
WS = HERE / "swarm" / SLUG
SRC = HERE / "sources" / SLUG
U1 = SRC / "plates"
CACHE = Path(os.environ.get("MMES_CACHE", "/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/mmes-cache"))

# ------------------------------------------------------------------ stage + rig (one shared stage module)
def _load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m)
    return m

S = _load("stage", WS / "stage/stage.py")
R = _load("rig", WS / "rig/rig.py")
W, H = 960, 540
FPS = 24
CLIP = 7.0
NF = 168
PAPER = tuple(S.PALETTE["paper"]); INKC = tuple(S.PALETTE["ink"]); SHADE = tuple(S.PALETTE["shade"])
TINT = tuple(S.PALETTE["tint"]); DTINT = tuple(S.PALETTE["dtint"])

# ------------------------------------------------------------------ manifests (one changed field per delta)
BASE = R.baseline_manifest()
BASE_SHA1 = R.manifest_sha1(BASE)
DELTAS = {"baseline": {}, "d-treatment": {"treatment": "photographic-plate"}, "d-camera": {"camera": "overhead"}}
LABEL = {"baseline": "baseline", "d-treatment": "Δ treatment", "d-camera": "Δ camera"}


def manifest(cond):
    M = dict(BASE); M.update(DELTAS[cond])
    diff = {k for k in set(M) | set(BASE) if M.get(k) != BASE.get(k)}
    assert len(diff) == (0 if cond == "baseline" else 1), (cond, diff)   # each delta changes exactly one field
    return M


# ------------------------------------------------------------------ waiting crowd: Agence Rol 1919 GrabCut cutouts
# U1 replaced the 1933 Bourse plate (PD basis not verifiable in the US); this re-implements stage._crowd
# with U1's accepted Vilgrain 1919 cutouts A-H at the same two placements (right of platform, left of cab).
CROWD_RIGHT = ["C_man_overcoat", "A_woman_shawl", "G_man_bowler_right", "F_woman_basket", "E_woman_white", "H_man_far"]
CROWD_LEFT = ["D_man_back", "B_woman_walking"]


@functools.lru_cache(None)
def _cut(name):
    a = np.asarray(Image.open(U1 / "crowd" / f"{name}_rgba.png").convert("RGBA")).astype(np.float32)
    return a[..., 0], a[..., 3] / 255.0



# ------------------------------------------------------------------ photographic puppet fills (U1 swatches)
SWATCH_FOR = {"man": "coat_dark_long", "jostler": "coat_light_overcoat", "conductor": "cape_officer"}
RUN_SWATCHES = ["coat_black_shawl", "trouser_wilson", "coat_dark_long", "cape_officer", "trouser_dark", "coat_light_overcoat"]


@functools.lru_cache(None)
def _tex(name):
    g = np.asarray(Image.open(U1 / "swatches" / f"{name}.png").convert("L")).astype(np.float32)
    g = np.concatenate([g, g[:, ::-1]], 1); g = np.concatenate([g, g[::-1]], 0)      # mirror tile: no seams
    t = np.tile(g, (H // g.shape[0] + 2, W // g.shape[1] + 2))[:H, :W]
    lo, hi = np.percentile(t, 2), np.percentile(t, 98)
    t = np.clip((t - lo) / max(hi - lo, 1), 0, 1) * 0.44             # keep the cloth dark: ink .. 44 % toward paper
    return S._grade(t * 255)


def photo_fill(P):
    out = {}
    for k, pp in enumerate(P["puppets"]):
        pid = pp["id"]
        if pid in SWATCH_FOR:
            nm = SWATCH_FOR[pid]
        elif pid.startswith("runner"):
            nm = RUN_SWATCHES[int(pid[6:] or 0) % len(RUN_SWATCHES)]
        else:
            nm = "cape_officer"
        out[pid] = np.roll(_tex(nm), int(round(pp.get("x", 0))), axis=1)   # texture rides with the puppet
    out["default"] = _tex("coat_dark_long")
    return out


R._bourse_fill = lambda: _tex("coat_dark_long")   # the 1933 plate is not used anywhere in the film

# ------------------------------------------------------------------ puppet silhouettes (repair round 2)
# The critic found capsule limbs: uniform rims, closed knife loops round each limb segment, visible
# doll joints. The rig's drawings are re-cut here (same skeleton, same pins, same exposure sheet):
# tapered limbs, larger replacement hands with a clear thumb notch, a filled elbow/knee web so each
# arm and leg prints as one tapered silhouette, scalloped hems, and hem flutter on the runners.
def _taper(pts, y0, y1, k):
    out = []
    for x, y in pts:
        if y <= y1:
            u = max(0.0, min(1.0, (y - y0) / (y1 - y0)))
            x = x * (1 - k * u)
        out.append((x, y))
    return out


def _hand(pts, ywr=16.5, g=1.32):
    return [(x * g, ywr + (y - ywr) * g) if y > ywr else (x, y) for x, y in pts]


_NEW = dict(R.SHAPES)
_NEW["uarm"] = [(-4.7, -2.4), (-4.3, 8), (-3.4, 19), (-2.6, 24.4), (-0.6, 26.2), (1.6, 25.8), (2.9, 23.4), (3.6, 15), (4.2, 6), (4.9, -2.6)]
for _k in ("farm_fist", "farm_open", "farm_flat", "farm_grip"):
    _NEW[_k] = _hand(_taper(R.SHAPES[_k], 0, 17, 0.30))
_NEW["thigh"] = [(-6.2, -2), (-5.8, 10), (-4.6, 24), (-3.6, 31.2), (0, 33.2), (3.4, 31.4), (4.6, 22), (5.6, 10), (6.2, -2.4)]
_NEW["shin"] = _taper(R.SHAPES["shin"], 0, 27, 0.32)
_NEW["shin_b"] = _taper(R.SHAPES["shin_b"], 0, 27, 0.30)
_NEW["b_skirt"] = [(-8, -2), (8, -2), (11.5, 14), (16.5, 33), (13, 35.2), (9.5, 33.4), (5.5, 37.4), (0.5, 34.6), (-4.5, 37.8), (-9, 35.0), (-14, 36.6), (-10.5, 16)]
_NEW["e_skirt"] = [(-8.5, -2), (8.5, -2), (11.5, 13), (14.5, 27), (10.5, 28.4), (6.5, 26.6), (2.5, 31.0), (-3, 28.2), (-8, 30.6), (-13, 28.8), (-11, 14)]
_NEW["a_tail"] = [(-1, -2), (-6, 12), (-12.5, 25), (-9, 25.6), (-7.5, 29.4), (-3, 26.4), (2, 26.0), (7, 13), (9, -2)]
_NEW["d_tail"] = [(-8, -2), (-12, 16), (-18, 36), (-13, 36.4), (-11, 40.6), (-5, 38), (0, 40.4), (5, 37.6), (9.5, 18), (10.5, -2)]
for _k, _v in _NEW.items():
    R.SHAPES[_k] = _v
    R.SM[_k] = R.smooth_closed(_v) * R.SCALE.get(_k, 1.0)

_JOINTS = (("fore_n", 4.6), ("fore_f", 4.6), ("shin_n", 6.0), ("shin_f", 6.0))
_orig_puppet_mask = R._puppet_mask


def _puppet_mask(P, pose_, cut_braid=True, crop=None):
    """Rig outline plus a filled web at elbow and knee, so a limb prints as one tapered shape."""
    m = _orig_puppet_mask(P, pose_, cut_braid=cut_braid, crop=crop)
    ox, oy = (crop[0], crop[1]) if crop else (0, 0)
    polys, pins, _ = R.parts_world(P)
    by = {n: p for z, n, p in polys}
    k = R.SS
    im = Image.new("L", (m.shape[1], m.shape[0]), 0); d = ImageDraw.Draw(im)
    for child, rad in _JOINTS:
        if child not in by or child not in pins:
            continue
        parent = pins[child][2]; c = np.asarray(pins[child][1])
        r_ = rad * P["s"]
        pts = [q for q in by[parent] if np.hypot(*(q - c)) < r_] + [q for q in by[child] if np.hypot(*(q - c)) < r_]
        if len(pts) < 3:
            continue
        hull = cv2.convexHull(np.array(pts, np.float32)).reshape(-1, 2)
        d.polygon([((u - ox) * k, (v - oy) * k) for u, v in hull], fill=255)
    web = np.asarray(im, np.float32) / 255.0
    rr = R._clip_rect(P, pose_)
    if rr is not None:
        x0, y0, x1, y1 = [int(round((v - o) * k)) for v, o in zip(rr, (ox, oy, ox, oy))]
        cc = np.zeros_like(web); cc[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = 1.0
        web *= cc
    return np.maximum(m, web)


R._puppet_mask = _puppet_mask
_orig_pose = R.pose


def _flutter_pose(seed, t):
    """Hem and coat-tail flutter on the runners (not the protected cast): a deterministic function of
    the drawing number and puppet id, so it snaps on twos and never draws an RNG."""
    P_ = _orig_pose(seed, t)
    d = P_["drawing"]
    for P in P_["puppets"]:
        if P["id"].startswith("runner") and any(q[0] == "tail" for q in R.RIGS[P["kind"]]["parts"]):
            ph = int(hashlib.sha1(P["id"].encode()).hexdigest()[:6], 16) % 628 / 100.0
            amp = 11.0 if P.get("note") == "run" else 4.0
            P["ang"] = dict(P["ang"]); P["ang"]["tail"] = P["ang"].get("tail", 0.0) - amp * (0.55 + 0.45 * math.sin(2 * math.pi * d / 3.0 + ph))
    return P_


R.pose = _flutter_pose

# Cut gap: a gouge-width (1-3 px, irregular, fixed per seed) gap of shade paper is cleared only where a
# figure crosses DARK ground. Dark ground is judged on the cut-paper stage (and the figures already
# printed), so the gap is identical in both treatments: the treatment delta stays fill-only.


@functools.lru_cache(None)
def _gapwidth(seed):
    g = cv2.GaussianBlur(R._grain(seed), (0, 0), 2.2)
    g = (g - g.min()) / max(1e-6, g.max() - g.min())
    return g


def draw_side_gap(layer, pose_, fill, group, dark):
    """Print puppets of `group` with the irregular dark-ground gap. `dark` (HxW 0..1) is updated in place."""
    sd = pose_["seed"]
    base = np.asarray(layer.convert("RGBA"), np.float32).copy()
    hcol = np.array(SHADE, np.float32); gw = _gapwidth(sd)
    for P in pose_["puppets"]:
        if not R._group_ok(P, group):
            continue
        a, bb = R._puppet_alpha(P, pose_, sd)
        if a is None:
            continue
        x0, y0, x1, y1 = bb
        reg = base[y0:y1, x0:x1]
        if P.get("clip") != "window":
            ab = (a > 0.35).astype(np.uint8)
            d1 = cv2.dilate(ab, np.ones((3, 3), np.uint8)).astype(np.float32)
            d2 = cv2.dilate(ab, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))).astype(np.float32)
            d3 = cv2.dilate(ab, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))).astype(np.float32)
            g = gw[y0:y1, x0:x1]
            ring = np.where(g > 0.78, d3, np.where(g > 0.42, d2, d1))
            ring = cv2.GaussianBlur(ring, (0, 0), 0.6) * (1 - a)
            ha = (np.clip(ring, 0, 1) * dark[y0:y1, x0:x1] * 0.95)[..., None]
            reg[..., :3] = reg[..., :3] * (1 - ha) + hcol * ha
        fl = R._fill_for(fill, P["id"])
        col = fl[y0:y1, x0:x1, :3].astype(np.float32) if isinstance(fl, np.ndarray) else np.array(fl[:3], np.float32)[None, None]
        a3 = a[..., None]
        reg[..., :3] = reg[..., :3] * (1 - a3) + col * a3
        reg[..., 3:] = np.maximum(reg[..., 3:], a3 * 255)
        base[y0:y1, x0:x1] = reg
        dark[y0:y1, x0:x1] = np.maximum(dark[y0:y1, x0:x1], np.clip(a * 1.3, 0, 1))
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGBA")


def _darkness(img):
    L = np.asarray(img.convert("L"), np.float32)
    L = cv2.GaussianBlur(L, (0, 0), 1.2)
    return np.clip((150.0 - L) / 55.0, 0, 1)

# ------------------------------------------------------------------ outline-preserving stage (repair round 1)
# Treatment is a FILL change only: every stage layer keeps the baseline's outline (same block masks,
# same printed alpha) and is refilled with real plate texture in photographic-plate.
SSs = S.SS
OUTLINES = {}          # (layer, seed, treatment) -> the binary outline mask actually laid (for IoU checks)


@functools.lru_cache(None)
def _shop_hatch(seed):
    """Cut-paper: dense horizontal gouge hatching cut through the dark arcade band (cream streaks)."""
    r = S.rng(seed, "shop-hatch")
    im, d = S.canvas()
    shop0, shop1 = S.WORLD["shop_band"]
    for _ in range(520):
        S.gouge(d, r.uniform(-80, W), r.uniform(shop0 + 5, shop1 - 1), r.uniform(14, 90), r.uniform(.45, 1.25), r.uniform(-.004, .004), r=r)
    x = r.uniform(0, 20)
    while x < W:                                    # vertical pier joints, short knife nicks
        for y in np.arange(shop0 + 8, shop1 - 4, r.uniform(9, 14)):
            d.line([(x * SSs, y * SSs), (x * SSs, (y + r.uniform(4, 7)) * SSs)], fill=255, width=SSs)
        x += r.uniform(38, 60)
    m = S.arr(im)
    band = np.zeros_like(m); band[int((shop0 + 3) * SSs):int(shop1 * SSs)] = 1
    return m * band


@functools.lru_cache(None)
def _blocks(seed):
    fk, ft, fd, fs, fc = S._facade_blocks(seed)
    sk, st, ss_, sc = S._street_blocks(seed)
    return dict(shade=np.clip(fs + ss_, 0, 1), tint=np.clip(ft + st, 0, 1), cut=np.clip(fc + sc, 0, 1), fcut=np.clip(fc, 0, 1),
                dtint=fd, key=np.clip(fk + sk, 0, 1))


@functools.lru_cache(None)
def _plate_tex(seed):
    """Full-frame grey texture from the Rol 1916 plate: rectified upper-storey stone for the facade and
    shop band (no shopfront crop, so no real pedestrians enter), rectified cobbles for the street."""
    (fac, _shp), _ = S._rol_facade_plate()
    cob, _ = S._rol_cobble_plate()
    Hd, Wd = H * SSs, W * SSs
    shop1 = S.WORLD["shop_band"][1]
    off = int(S.rng(seed, "photo-facade").uniform(0, 200))
    fh = int(shop1 * SSs)
    t = cv2.resize(fac, (int(fac.shape[1] * fh / fac.shape[0]), fh), interpolation=cv2.INTER_AREA).astype(np.float32)
    t = np.concatenate([t] * (Wd // t.shape[1] + 3), 1)[:, off:off + Wd]
    out = np.zeros((Hd, Wd), np.float32); out[:fh] = t
    out[fh:] = cv2.resize(cob, (Wd, Hd - fh), interpolation=cv2.INTER_AREA).astype(np.float32)
    return out


def _photo_col(tex, tone, gain=1.0):
    """Real plate texture placed at a block's tone: high-pass detail of the plate around that level."""
    g0 = float((np.asarray(tone, np.float32) - S.INK).mean() / (S.PAPER - S.INK).mean()) * 255
    hp = tex - cv2.GaussianBlur(tex, (0, 0), 14)
    lo = tex - tex.mean()
    return S._grade(np.clip(g0 + hp * 1.5 * gain + lo * 0.30 * gain, 0, 255))


@functools.lru_cache(None)
def _backdrop_cut(seed):
    B = _blocks(seed)
    img = S.paper_ground(seed)
    img = S.lay(img, B["shade"], S.SHADE)
    img = S.lay(img, S.print_block(B["tint"], seed, "tint-bg", starve=0, edge=0.25) * 0.9, S.TINT)
    img = S.lay(img, B["cut"] * 0.85, S.SHADE)
    img = S.lay(img, S.print_block(B["dtint"], seed, "dtint-bg", starve=0.05, edge=0.25) * 0.95, S.DTINT)
    img = S.lay(img, B["fcut"] * 0.85, S.SHADE)
    img = S.lay(img, _shop_hatch(seed) * B["dtint"] * 0.62, S.SHADE)          # gouged arcade band
    key = S.print_block(B["key"], seed, "key-bg", starve=0.08)
    OUTLINES[("backdrop", seed, "cut-paper")] = key > 0.5
    return S.lay(img, key, S.INK)


@functools.lru_cache(None)
def _backdrop_photo(seed):
    """Photographic-plate: the SAME carved blocks (same masks, same printed key), each refilled with the
    Rol 1916 plate's own texture at the block's tone. No new architecture, no new figures."""
    B = _blocks(seed); tex = _plate_tex(seed)
    img = _photo_col(tex, S.PAPER, 0.8)
    img = S.lay(img, B["shade"], _photo_col(tex, S.SHADE))
    img = S.lay(img, S.print_block(B["tint"], seed, "tint-bg", starve=0, edge=0.25) * 0.9, _photo_col(tex, S.TINT))
    img = S.lay(img, B["cut"] * 0.85, _photo_col(tex, S.SHADE))
    img = S.lay(img, S.print_block(B["dtint"], seed, "dtint-bg", starve=0.05, edge=0.25) * 0.95, _photo_col(tex, S.DTINT))
    img = S.lay(img, B["fcut"] * 0.85, _photo_col(tex, S.SHADE))
    img = S.lay(img, _shop_hatch(seed) * B["dtint"] * 0.62, _photo_col(tex, S.SHADE))
    key = S.print_block(B["key"], seed, "key-bg", starve=0.08)
    OUTLINES[("backdrop", seed, "photographic-plate")] = key > 0.5
    return S.lay(img, key, _photo_col(tex, S.INK, 0.7))


S._backdrop_cut = _backdrop_cut
S._backdrop_photo = _backdrop_photo


def backdrop_outline(seed, tr):
    """Binary key-block outline laid by the backdrop in treatment tr (SS px)."""
    S.backdrop(seed, tr)
    if (("backdrop", seed, tr)) not in OUTLINES:     # lru-cached before OUTLINES was filled in this process
        (_backdrop_cut if tr == "cut-paper" else _backdrop_photo).__wrapped__(seed)
    return OUTLINES[("backdrop", seed, tr)]


@functools.lru_cache(None)
def _crowd(seed, treatment):
    """Waiting crowd from U1's Vilgrain 1919 GrabCut cutouts. One printed alpha for both treatments;
    cut-paper = ink with a few cream gouge lines inside, photographic-plate = the cutouts' own greys."""
    SS = SSs; Hd, Wd = H * SS, W * SS
    alpha = np.zeros((Hd, Wd), np.float32); fill = np.full((Hd, Wd), 128, np.float32)
    r = S.rng(seed, "crowd")
    feet_y = S.side_ground_y(S.WORLD["crowd_z"])
    plan = []
    x = 728 + r.uniform(-4, 10)
    for nm in CROWD_RIGHT:
        plan.append((nm, x)); x += r.uniform(30, 44)
    x = 6 + r.uniform(-6, 6)
    for nm in CROWD_LEFT:
        plan.append((nm, x)); x += r.uniform(40, 52)
    for nm, x0 in plan:
        g, a = _cut(nm)
        ys = np.nonzero(a.sum(1) > 0)[0]
        hh = ys.max() - ys.min() + 1
        target = r.uniform(100, 114) * (0.86 if nm.startswith(("E_", "H_", "F_")) else 1.0)
        sc = target / hh * SS
        tw, th = max(1, int(a.shape[1] * sc)), max(1, int(a.shape[0] * sc))
        cm = cv2.resize(a, (tw, th), interpolation=cv2.INTER_AREA)
        cg = cv2.resize(g, (tw, th), interpolation=cv2.INTER_AREA)
        X = int(x0 * SS); Y = int(feet_y * SS - ys.max() * sc)
        x0_, y0_ = max(0, X), max(0, Y); x1_, y1_ = min(Wd, X + tw), min(Hd, Y + th)
        if x1_ <= x0_ or y1_ <= y0_:
            continue
        aa = cm[y0_ - Y:y1_ - Y, x0_ - X:x1_ - X]
        fill[y0_:y1_, x0_:x1_] = fill[y0_:y1_, x0_:x1_] * (1 - aa) + cg[y0_ - Y:y1_ - Y, x0_ - X:x1_ - X] * aa
        alpha[y0_:y1_, x0_:x1_] = np.maximum(alpha[y0_:y1_, x0_:x1_], aa)
    a = S.print_block(np.clip(alpha * 1.15, 0, 1), seed, "crowd", starve=0.04, edge=0.3)   # one outline, both treatments
    if treatment == "cut-paper":
        img = np.empty((Hd, Wd, 3), np.float32); img[:] = S.INK2
        inner = cv2.erode((alpha > 0.5).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(np.float32)
        rr = S.rng(seed, "crowd-carve")
        n = S.smooth_noise(rr, Hd, Wd, 2, 40)
        streak = np.clip((n - 0.80) * 9, 0, 1)                 # sparse long horizontal gouges, fixed per seed
        g = np.clip(fill / 255.0, 0, 1)
        lit = np.clip((g - 0.62) * 4, 0, 1)                    # where the real 1919 cloth catches light
        img = S.lay(img, np.clip(streak * 0.55 + lit * 0.45, 0, 1) * inner, S.SHADE)
        return img, a
    return S._grade(fill), a


S._crowd = _crowd


def bus_front(seed, treatment="cut-paper"):
    """Stanchion + chain: same printed alpha in both treatments; photographic fill from the bus plate."""
    hw = S._hardware(seed)
    a = S.print_block(hw["front_ink"], seed, "front", starve=0, edge=0.2)
    if treatment == "cut-paper":
        img = np.empty(a.shape + (3,), np.float32); img[:] = S.INK
    else:
        dark, _ = S._photo_textures()
        img = S._grade(dark * 0.8)
    return S.to_rgba(img, a)


S.bus_front = bus_front

# ------------------------------------------------------------------ carved interior lines in the cut-paper puppets
CARVE = tuple(S.PALETTE["shade"])


LEAD = {"arm_n": "f", "fore_n": "f", "arm_f": "f", "fore_f": "f", "leg_n": "f", "shin_n": "f",
        "tail": "down", "hat": "down"}


def _outward(p):
    t_ = np.roll(p, -1, 0) - np.roll(p, 1, 0)
    n = np.stack([t_[:, 1], -t_[:, 0]], 1); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-6)
    c = p.astype(np.float32).reshape(-1, 1, 2)
    probe = p + n * 0.8
    flip = np.array([cv2.pointPolygonTest(c, (float(u), float(v)), False) > 0 for u, v in probe])
    n[flip] *= -1
    return n


def _longest_run(ok):
    N = len(ok)
    if ok.all() or not ok.any():
        return None
    s0 = int(np.argmin(ok))                       # start just after a False: runs never wrap
    best, cur, bs, cs = 0, 0, 0, 0
    for j in range(1, N + 1):
        i = (s0 + j) % N
        if ok[i]:
            if cur == 0:
                cs = i
            cur += 1
            if cur > best:
                best, bs = cur, cs
        else:
            cur = 0
    return bs, best


CARVE_LOG = []      # (puppet, part, run_len, contour_len) for the open-stroke check


def _carve_fill(P, pose_):
    """INK fill with cream gouge strokes cut along ONE edge of a front part where it overlaps the
    body (the leading edge of a sleeve or near leg, the hem of a coat tail, the under-brim of a hat).
    Each stroke is an open run of the outline, tapered to nothing at both ends like a gouge, never a
    loop round a limb. Derived from the drawn geometry, so it moves on twos and never boils."""
    bb = R._bbox(P, pose_)
    out = np.empty((H, W, 3), np.float32); out[:] = R.INK
    if bb is None:
        return out
    x0, y0, x1, y1 = bb
    k = 3
    polys, _, _ = R.parts_world(P)
    acc = Image.new("L", ((x1 - x0) * k, (y1 - y0) * k), 0); da = ImageDraw.Draw(acc)
    lines = Image.new("L", acc.size, 0); dl = ImageDraw.Draw(lines)
    f = P["facing"]
    for z, nm, p in polys:                             # back to front
        q = [((u - x0) * k, (v - y0) * k) for u, v in p]
        if nm in LEAD:
            prev = cv2.erode(np.asarray(acc, np.uint8), np.ones((2 * k + 1, 2 * k + 1), np.uint8))
            dirv = np.array([f, 0.15]) if LEAD[nm] == "f" else np.array([0.0, 1.0])
            dirv = dirv / np.linalg.norm(dirv)
            nrm = _outward(np.asarray(p, float))
            Q = np.asarray(q)
            xi = np.clip(Q[:, 0].astype(int), 0, prev.shape[1] - 1); yi = np.clip(Q[:, 1].astype(int), 0, prev.shape[0] - 1)
            ok = (prev[yi, xi] > 0) & (nrm @ dirv > 0.35)
            run = _longest_run(ok)
            if run is not None:
                bs, L = run
                L = min(L, int(0.42 * len(Q)))
                if L >= 5:
                    CARVE_LOG.append((P["id"], nm, L, len(Q)))
                    idx = [(bs + j) % len(Q) for j in range(L)]
                    for j in range(L - 1):
                        u = (j + 0.5) / (L - 1)
                        wd = max(1, int(round(k * (0.25 + 1.05 * math.sin(math.pi * u) ** 0.8))))
                        dl.line([tuple(Q[idx[j]]), tuple(Q[idx[j + 1]])], fill=255, width=wd)
        da.polygon(q, fill=255)
    ln = cv2.resize(np.asarray(lines, np.float32) / 255.0, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    ln = np.clip(ln * 1.5, 0, 1)[..., None] * 0.85
    reg = out[y0:y1, x0:x1]
    out[y0:y1, x0:x1] = reg * (1 - ln) + np.array(CARVE, np.float32) * ln
    return out


def carve_fill(pose_):
    f = {P["id"]: _carve_fill(P, pose_) for P in pose_["puppets"]}
    f["default"] = R.INK
    return f


# ------------------------------------------------------------------ overhead: the rear-bay roof-light (seat A cell)
# From above the seat is under the roof. The plan roof gets one cut opening over seat A (the rear bay
# of the saloon), so the seat being vacated (A5v) and taken (A6) read as hat discs leaving/entering
# the cell. Same world x/z as the side pose; nothing drawn from any RNG.
CELL = (571.0, 184.0, 610.0, 283.0)      # plan screen px at rest (x0, y0, x1, y1)


def cell_rect(dx):
    x0, y0, x1, y1 = CELL
    return (x0 + dx, y0, x1 + dx, y1)


def seat_cell_mask(pose_, ids=None, ss=False):
    """Plan forms of the seated (window-group) puppets, clipped to the roof-light cell."""
    P2 = dict(pose_)
    P2["puppets"] = [dict(q, plan_visible=True) for q in pose_["puppets"]
                     if q["group"] == "window" and (ids is None or q["id"] in ids)]
    m = R.plan_mask(P2, ss=True)
    x0, y0, x1, y1 = cell_rect(pose_["dx"])
    c = np.zeros_like(m); k = R.SS
    c[int((y0 + 2) * k):int((y1 - 2) * k), int((x0 + 2) * k):int((x1 - 2) * k)] = 1
    m = m * c
    return m if ss else cv2.resize(m, (W, H), interpolation=cv2.INTER_AREA)


def draw_cell(img, pose_):
    seed = pose_["seed"]; r = S.rng(seed, "roof-light")
    im, d = S.canvas(); fl, df = S.canvas(); bn, db = S.canvas()
    x0, y0, x1, y1 = cell_rect(pose_["dx"])
    S.wobbly_quad(d, r, x0 - 3, y0 - 3, x1 + 3, y1 + 3, amp=0.4)            # ink rim of the cut
    S.wobbly_quad(df, r, x0, y0, x1, y1, amp=0.4)                           # saloon floor seen below
    S.wobbly_quad(db, r, x0, y1 - 22, x1, y1 - 3, amp=0.3)                  # near-side bench
    S.wobbly_quad(db, r, x0, y0 + 3, x1, y0 + 14, amp=0.3)                  # far-side bench
    rim, flo, ben = S.arr(im), S.arr(fl), S.arr(bn)
    base = np.asarray(img.convert("RGB"), np.float32)
    big = cv2.resize(base, (W * SSs, H * SSs), interpolation=cv2.INTER_LINEAR)
    big = S.lay(big, S.print_block(np.clip(rim - flo, 0, 1), seed, "cell-rim", starve=0, edge=0.2), S.INK)
    big = S.lay(big, flo, S.SHADE)
    big = S.lay(big, S.print_block(ben, seed, "cell-bench", starve=0, edge=0.2) * 0.9, S.TINT)
    out = S.to_rgba(big)
    a = R.print_puppets(seat_cell_mask(pose_, ss=True), seed)[..., None]
    o = np.asarray(out, np.float32).copy()
    o[..., :3] = o[..., :3] * (1 - a) + np.array(R.INK, np.float32) * a
    return Image.fromarray(np.clip(o, 0, 255).astype(np.uint8), "RGBA")

# ------------------------------------------------------------------ render(M, seed, t)
def render(M, seed, t):
    """One clip frame (untagged RGB) for manifest M at clip time t."""
    seed = int(seed)
    P = R.pose(seed, t)
    if M["camera"] == "overhead":
        img = draw_cell(S.plan_stage(seed, t), P)
        return R.draw_plan(img, P, R.INK).convert("RGB")
    tr = M["treatment"]
    dx = P["dx"]
    layers = [S.backdrop(seed, tr), S.crowd(seed, tr), S.bus_shadow(seed, dx), S.shift(S.bus_body(seed, tr), dx)]
    travel = S.bus_x(0) - S.bus_x(t)                 # rolls in, stops at A1, rolls again after A8 (v/r)
    for name in ("front", "rear"):
        tile, (cx, cy) = S.wheel(seed, name, S.wheel_angle_for(travel), tr)
        layers.append((tile, (cx + dx - tile.size[0] / 2, cy - tile.size[1] / 2)))
    img = S.compose(layers)
    fill = carve_fill(P) if tr == "cut-paper" else photo_fill(P)
    # dark ground for the cut gap is judged on the cut-paper stage in BOTH treatments (fill-only delta)
    ref = img if tr == "cut-paper" else _cut_ref(seed, t, dx)
    dark = _darkness(ref)
    img = draw_side_gap(img, P, fill, "window", dark)
    img = draw_side_gap(img, P, fill, "platform", dark)
    bf = S.shift(S.bus_front(seed, tr), dx)
    img.alpha_composite(bf)
    dark = np.maximum(dark, np.clip(np.asarray(S.shift(S.bus_front(seed, "cut-paper"), dx), np.float32)[..., 3] / 255.0 * 1.2, 0, 1))
    img.alpha_composite(S.shift(S.bell_tassel(seed, P["bell_pull"], tr), dx))
    img.alpha_composite(S.shadow_slivers(seed, "runners", R.feet(P), 150))
    img = draw_side_gap(img, P, fill, "street", dark)
    return img.convert("RGB")


def _cut_ref(seed, t, dx):
    layers = [S.backdrop(seed, "cut-paper"), S.crowd(seed, "cut-paper"), S.bus_shadow(seed, dx), S.shift(S.bus_body(seed, "cut-paper"), dx)]
    travel = S.bus_x(0) - S.bus_x(t)
    for name in ("front", "rear"):
        tile, (cx, cy) = S.wheel(seed, name, S.wheel_angle_for(travel), "cut-paper")
        layers.append((tile, (cx + dx - tile.size[0] / 2, cy - tile.size[1] / 2)))
    return S.compose(layers)


def dtext(d, xy, s, font, fill, spacing=2):
    """Text with a hand-drawn delta: the kit fonts carry no Δ glyph, so the triangle is drawn."""
    x, y = xy
    if "Δ" not in s:
        d.text((x, y), s, font=font, fill=fill, spacing=spacing)
        return d.textlength(s, font=font)
    x0 = x
    for i, part in enumerate(s.split("Δ")):
        if i:
            sz = font.size
            asc = d.textbbox((0, 0), "H", font=font)
            top, bot = y + asc[1], y + asc[3]
            w_ = (bot - top) * 0.95
            d.polygon([(x, bot), (x + w_ / 2, top), (x + w_, bot)], outline=fill, fill=None, width=max(1, int(sz / 11)))
            x += w_ + sz * 0.15
        if part:
            d.text((x, y), part, font=font, fill=fill)
            x += d.textlength(part, font=font)
    return x - x0


def tag(img, text, size=13, xy=(12, None)):
    d = ImageDraw.Draw(img)
    f = kit.font("mono", size)
    b = d.textbbox((0, 0), text.replace("Δ", "M"), font=f)
    tw, th = b[2] - b[0], b[3] - b[1]
    x = xy[0]; y = (img.size[1] - th - 22) if xy[1] is None else xy[1]
    d.rectangle([x, y, x + tw + 14, y + th + 10], fill=INKC)
    dtext(d, (x + 7, y + 5 - b[1]), text, f, PAPER)
    return img


def clip_tag(cond, seed, t):
    extra = {"baseline": "", "d-treatment": " photographic-plate · composite · staged", "d-camera": " overhead"}[cond]
    return f"{LABEL[cond]}{extra} · seed {seed:04d} · t {t:4.2f}"


# ------------------------------------------------------------------ frame cache (precomputed in parallel)
CONDS = ("baseline", "d-treatment", "d-camera")
SEEDS = (417, 418)


def _cpath(cond, seed, f):
    return CACHE / f"{cond}_{seed}_{f:03d}.png"


def _job(args):
    cond, seed, fs = args
    M = manifest(cond)
    for f in fs:
        p = _cpath(cond, seed, f)
        if not p.exists():
            render(M, seed, f / FPS).save(p, compress_level=1)
    return len(fs)


def precompute():
    CACHE.mkdir(parents=True, exist_ok=True)
    jobs = []
    for c in CONDS:
        for s in SEEDS:
            for k in range(4):
                jobs.append((c, s, list(range(k, NF, 4))))
    ctx = get_context("fork")                       # forked workers: nothing is pickled
    procs = [ctx.Process(target=lambda js=jobs[w::4]: [_job(j) for j in js]) for w in range(4)]
    for p_ in procs:
        p_.start()
    for p_ in procs:
        p_.join()
        assert p_.exitcode == 0, "frame worker failed"


@functools.lru_cache(maxsize=64)
def clip_frame(cond, seed, f):
    f = max(0, min(NF - 1, f))
    p = _cpath(cond, seed, f)
    if p.exists():
        return Image.open(p).convert("RGB")
    return render(manifest(cond), seed, f / FPS)


# ------------------------------------------------------------------ cards (paper and ink)
def _paper():
    return Image.new("RGB", (W, H), PAPER)


MANIFEST_LINES = [("scene", "platform-bus encounter"), ("camera", "street-side"), ("treatment", "cut-paper"),
                  ("seeds", "0417 0418"), ("duration", "7.0 s · 24 fps · puppets on twos"),
                  ("destination", "MADELEINE – BASTILLE")]


def _ink_tab(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=INKC)


def card_manifest(k):
    """S0: title + baseline manifest typing out, cream on an ink tab."""
    img = _paper(); d = ImageDraw.Draw(img)
    d.text((64, 70), "one incident, three instructions", font=kit.font("serif", 50), fill=INKC)
    d.text((66, 132), "Exercises in Style (after Mauro Martino) · baseline manifest", font=kit.font("mono", 14), fill=DTINT)
    _ink_tab(d, 60, 176, 600, 6 * 34 + 26)
    f = kit.font("mono", 18)
    chars = max(0, k - 8) * 2.4
    used = 0
    for i, (key, val) in enumerate(MANIFEST_LINES):
        s = f"{key}: {val}"
        n = int(max(0, min(len(s), chars - used)))
        used += len(s)
        if n:
            d.text((80, 192 + i * 34), s[:n] + ("_" if n < len(s) and (k // 6) % 2 == 0 else ""), font=f, fill=PAPER)
    if k > 70:
        d.text((64, 430), f"manifest sha1 {BASE_SHA1}", font=kit.font("mono", 14), fill=INKC)
        d.text((64, 452), "rendered by render(M, seed, t) · same exposure sheet for every condition", font=kit.font("mono", 13), fill=DTINT)
    return img


def card_delta(k, field, old, new, effect, note=""):
    """S3/S6: the changed line is struck through over 6 frames, then the new value is typed."""
    img = _paper(); d = ImageDraw.Draw(img)
    dtext(d, (64, 56), f"Δ {field}", kit.font("serif", 50), INKC)
    d.text((66, 118), "PromptDelta · one field changed · everything else frozen", font=kit.font("mono", 14), fill=DTINT)
    _ink_tab(d, 60, 160, 640, 6 * 34 + 26)
    f = kit.font("mono", 18)
    for i, (key, val) in enumerate(MANIFEST_LINES):
        y = 176 + i * 34
        if key != field:
            d.text((80, y), f"{key}: {val}", font=f, fill=(150, 144, 135))
            continue
        head = f"{key}: "
        d.text((80, y), head + old, font=f, fill=PAPER)
        b0 = d.textbbox((80, y), head, font=f); b1 = d.textbbox((80, y), head + old, font=f)
        strike = kit.clamp((k - 4) / 6)                              # 6 frames
        if strike > 0:
            ym = (b1[1] + b1[3]) / 2
            d.line([(b0[2], ym), (b0[2] + (b1[2] - b0[2]) * strike, ym)], fill=PAPER, width=3)
        n = int(max(0, min(len(new), (k - 12) * 1.2)))
        if n:
            d.text((b1[2] + 18, y), new[:n], font=f, fill=PAPER)
    if k > 30:
        d.text((64, 410), f"diff keys: {{{field}}}   (asserted: exactly one)", font=kit.font("mono", 15), fill=INKC)
        d.text((64, 434), f"intended effect: “{effect}”", font=kit.font("mono", 15), fill=INKC)
        if note:
            d.text((64, 460), note, font=kit.font("mono", 13), fill=DTINT)
    return img


@functools.lru_cache(None)
def coverage():
    return json.loads((WS / "verify/coverage.json").read_text())


@functools.lru_cache(None)
def drift_strip():
    im = Image.open(WS / "verify/rejected-drift-strip.jpg").convert("RGB")
    im = im.crop((0, 283, im.size[0], im.size[1]))   # overhead rows only (accepted vs drift); the side row is not reused
    w = 340; return im.resize((w, int(im.size[1] * w / im.size[0])), Image.LANCZOS)


def card_coverage(k):
    C = coverage()
    img = _paper(); d = ImageDraw.Draw(img)
    d.text((40, 26), "coverage report", font=kit.font("serif", 40), fill=INKC)
    d.text((42, 74), "observed in 6 inspected samples of one procedural engine (stage.py + rig.py on kit.py)",
           font=kit.font("mono", 12), fill=DTINT)
    ie = C["intended_effect_rate"]
    lost = C["lost_anchor_ids"]["d-camera"]; part = C["partial_anchor_ids"]["d-camera"]
    pred = C["predicted_losses_overhead"]["predicted"]
    iou = min(C["outline_iou"]["puppets"]["min"], C["outline_iou"].get("stage_min", 0.0))
    au = C.get("audio_pcm", {})
    if au.get("status") == "measured" and au.get("identical"):
        snd = "bed+bell PCM identical: 6 clip windows + grid"
        sha = next(iter(au["clips"].values()))["pcm_sha1"]
        snd2 = "pre-encode sha1 %s (7 of 7)" % sha[:16]
    else:
        snd = "PCM identity NOT verified (%s)" % au.get("status", "missing"); snd2 = ""
    aac = au.get("aac_decoded") or {}
    snd3 = ("AAC 96k is lossy: decoded windows differ, min SNR %.0f dB" % aac["min_snr_db"]) if aac.get("min_snr_db") is not None else "AAC 96k is lossy: decoded windows not bit-identical"
    rows = [
        ("intended effect", ""),
        ("  baseline", ie["baseline"]["rate"]),
        ("  Δ treatment", ie["d-treatment"]["rate"] + f" · IoU {iou:.1f} all layers"),
        ("  Δ camera", ie["d-camera"]["rate"] + " · shove = shift"),
        ("lost in overhead", " ".join(lost)),
        ("  predicted", " ".join(pred) + (" · others unpredicted" if set(lost) - set(pred) else " · no others")),
        ("partial in overhead", " ".join(part)),
        ("seeds", "procedural generator, seeds repeatable,"),
        ("", "verified by frame hash (frames 0 29 132 × 6)"),
        ("", "seed moves runners (7 vs 8) only;"),
        ("", "protected masks identical"),
        ("sound", snd),
        ("", snd2),
        ("", snd3 + " · hold: silence"),
        ("not claimed", "anything about text-to-video"),
        ("", "generators in general"),
    ]
    f = kit.font("mono", 13)
    y = 108
    for i, (a, b) in enumerate(rows):
        if k < 6 + i * 4:
            break
        dtext(d, (42, y), a, f, INKC)
        d.text((200, y), b, font=f, fill=INKC)
        y += 27 if a and not a.startswith(" ") else 22
    if k > 40:
        st = drift_strip()
        x0, y0 = 590, 140
        _ink_tab(d, x0 - 6, y0 - 30, st.size[0] + 12, st.size[1] + 36)
        d.text((x0 + 2, y0 - 24), "REJECTED DRIFT · RNG-coupled overhead projector", font=kit.font("mono", 12), fill=PAPER)
        img.paste(st, (x0, y0))
        ce = C["counterexample"]
        d = ImageDraw.Draw(img)
        d.text((x0, y0 + st.size[1] + 16), f"seed 0417: {ce['observed']['runners_overhead_drift']} runners overhead vs "
               f"{ce['observed']['runners_side']} side", font=kit.font("mono", 12), fill=INKC)
        for j, b in enumerate(ce["broken"]):
            d.text((x0, y0 + st.size[1] + 34 + j * 15), ("fails: " if j == 0 else "       ") + b, font=kit.font("mono", 11), fill=INKC)
    if k > 20:
        d = ImageDraw.Draw(img)
        d.text((42, 485), "photographs: Agence Rol 1916, 1919 (BnF Gallica via Wikimedia Commons, public domain) · street: cori (PD) · bell: qubodup (CC0)",
               font=kit.font("mono", 10), fill=DTINT)
        d.text((42, 500), "engine: WWS CityBusMANSG220engine, Work With Sounds / Technical Museum of Slovenia, CC BY 4.0",
               font=kit.font("mono", 10), fill=DTINT)
        d.text((42, 515), "(creativecommons.org/licenses/by/4.0), trimmed and mixed · thud, clicks synthesized · everything else handmade",
               font=kit.font("mono", 10), fill=DTINT)
    return img


# ------------------------------------------------------------------ S9 comparison grid
CHIPS = [("stop", "A1", 0.90), ("shove", "A3", 1.20), ("stanchion", "A4", 1.333), ("cord", "A4c", 1.25),
         ("protest", "A5", 2.00), ("vacate", "A5v", 3.60), ("seat", "A6", 5.50), ("seat-in-window", "A6w", 5.00),
         ("bell", "A7", 6.00), ("destination", "A0", 0.00), ("neck", "A-neck", 0.00)]


def grid_frame(tt, hold):
    C = coverage()
    img = Image.new("RGB", (W, H), PAPER); d = ImageDraw.Draw(img)
    f = 29 if hold else min(NF - 1, int(round(tt * FPS)))
    t = f / FPS
    cw, ch = 300, 169
    fs = kit.font("mono", 10)
    for r_, cond in enumerate(CONDS):
        y = 8 + r_ * 178
        lab = {"baseline": ["baseline"], "d-treatment": ["Δ treat-", "  ment"], "d-camera": ["Δ camera"]}[cond]
        for j, ln in enumerate(lab):
            dtext(d, (8, y + 4 + j * 15), ln, kit.font("mono", 12), INKC)
        d.text((8, y + 40), {"baseline": "street-side\ncut-paper", "d-treatment": "photo-\ngraphic-\nplate\n\ncomposite\n· staged", "d-camera": "overhead"}[cond],
               font=fs, fill=DTINT, spacing=2)
        for c_, seed in enumerate(SEEDS):
            x = 88 + c_ * 304
            cell = clip_frame(cond, seed, f).resize((cw, ch), Image.LANCZOS)
            img.paste(cell, (x, y))
            tag(img, f"{seed:04d}", size=9, xy=(x + 4, y + ch - 20))
        # anchor chips for this row, one box per seed
        px = 700
        lost = set(C["lost_anchor_ids"][cond]); part = set(C["partial_anchor_ids"][cond])
        dd = ImageDraw.Draw(img)
        for i, (nm, aid, at) in enumerate(CHIPS):
            yy = y + 1 + i * 15
            on = hold or tt >= at
            is_lost = aid in lost
            col = DTINT if is_lost else INKC
            dd.text((px + 34, yy + 1), nm, font=fs, fill=col)
            for s_ in range(2):
                bx = px + s_ * 15
                if is_lost and on:
                    dd.rectangle([bx, yy + 1, bx + 11, yy + 12], fill=PAPER, outline=DTINT)
                    dd.line([(bx, yy + 12), (bx + 11, yy + 1)], fill=INKC, width=1)
                elif on and aid in part:
                    dd.rectangle([bx, yy + 1, bx + 11, yy + 12], fill=PAPER, outline=INKC)
                    dd.polygon([(bx, yy + 12), (bx + 11, yy + 1), (bx + 11, yy + 12)], fill=INKC)
                else:
                    dd.rectangle([bx, yy + 1, bx + 11, yy + 12], fill=INKC if on else PAPER, outline=INKC)
            if is_lost and on:
                tw = dd.textlength(nm, font=fs)
                dd.line([(px + 34, yy + 7), (px + 34 + tw, yy + 7)], fill=INKC, width=1)
                dd.text((px + 40 + tw, yy + 1), "lost", font=fs, fill=INKC)
    d = ImageDraw.Draw(img)
    tag(img, ("HOLD" if hold else "sync"), size=11, xy=(8, 470))
    tag(img, f"t {t:4.2f}", size=11, xy=(8, 498))
    return img


# ------------------------------------------------------------------ the shot list (plan.md section 5)
SHOTS = [  # (start, end, kind, args)
    (0.0, 4.0, "card0", None),
    (4.0, 11.0, "clip", ("baseline", 417)),
    (11.0, 18.0, "clip", ("baseline", 418)),
    (18.0, 20.0, "delta", ("treatment", "cut-paper", "photographic-plate", "same outlines, photographic fill",
                           "fill = Rol 1916 bus + facade/cobble texture, Rol 1919 crowd + cloth; board handmade")),
    (20.0, 27.0, "clip", ("d-treatment", 417)),
    (27.0, 34.0, "clip", ("d-treatment", 418)),
    (34.0, 36.0, "delta", ("camera", "street-side", "overhead", "plan view; shove as displacement")),
    (36.0, 43.0, "clip", ("d-camera", 417)),
    (43.0, 50.0, "clip", ("d-camera", 418)),
    (50.0, 58.0, "grid", None),
    (58.0, 64.0, "report", None),
]
CLIP_WINDOWS = [s for s, e, kind, a in SHOTS if kind == "clip"] + [50.0]
SECONDS = 64.0

film = Film(SLUG, seconds=SECONDS, boil=0, wobble=0, seed=417)
film.poster_at = 5.25


@film.picture
def picture(t, ink):
    ink._grain = False              # the stage carries its own fixed paper grain; no per-frame boil
    k = int(round(t * FPS))
    for s, e, kind, a in SHOTS:
        if s <= t < e or (kind == "report" and t >= s):
            break
    ks = k - int(round(s * FPS))
    if kind == "card0":
        img = card_manifest(ks)
    elif kind == "delta":
        img = card_delta(ks, *a)
    elif kind == "clip":
        cond, seed = a
        img = clip_frame(cond, seed, ks).copy()
        tag(img, clip_tag(cond, seed, ks / FPS))
    elif kind == "grid":
        img = grid_frame(ks / FPS, ks >= NF)
    else:
        img = card_coverage(ks)
    ink.img = img
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


# ------------------------------------------------------------------ sound
def _decode(path, rate=kit.RATE):
    """Decode a foraged wav with ffmpeg to float stereo at the kit rate."""
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "s16le", "-ac", "2", "-ar", str(rate), "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.int16).reshape(-1, 2).astype(np.float64) / 32768.0


@functools.lru_cache(None)
def clip_audio():
    """The one 7.0 s clip track: foraged bed + foraged bell at A7, kit thud at A3 and click at A4
    (both declared synthetic). Built once; the identical array is laid under every clip window."""
    n = int(round(CLIP * kit.RATE))
    m = kit.Mix(CLIP, seed=1201)
    bed = _decode(U1 / "audio/bed_7.0s.wav")[:n]
    bell = _decode(U1 / "audio/bell_conductor_2.6s.wav")
    m.thud(1.20, freq=62, gain=0.55, seconds=0.3)
    m.click(1.333, gain=0.25, bright=6000)
    st = np.stack([m.L, m.R], 1)
    st[:len(bed)] += bed * 0.85
    i = int(round((6.00 - 0.011) * kit.RATE))
    b = bell[:n - i].copy() * 0.7
    tail = int(0.06 * kit.RATE)
    b[-tail:] *= np.linspace(1, 0, tail)[:, None]                 # cut at the clip end: no spill into the next window
    st[i:i + len(b)] += b
    return st


@functools.lru_cache(None)
def pcm_report():
    """Rebuild the film's mix exactly as Film.render does and hash each 7.0 s clip window (s16 PCM)."""
    m = kit.Mix(SECONDS, seed=film.seed)
    sound(m)
    pcm = np.asarray(m.master()).reshape(-1, 2)
    hs = []
    for at in CLIP_WINDOWS:
        a0 = int(round(at * kit.RATE)); a1 = a0 + int(round(CLIP * kit.RATE))
        hs.append(hashlib.sha1(pcm[a0:a1].tobytes()).hexdigest())
    return dict(windows=CLIP_WINDOWS, sha1=hs, identical=len(set(hs)) == 1, rate=kit.RATE)


def _lay(mix, st, at):
    i = int(round(at * kit.RATE))
    n = min(len(st), mix.n - i)
    mix.L[i:i + n] += st[:n, 0]; mix.R[i:i + n] += st[:n, 1]


@film.sound
def sound(mix):
    clip = clip_audio()
    for at in CLIP_WINDOWS:
        _lay(mix, clip, at)
    street = _decode(U1 / "audio/street_bed_7.0s.wav")
    def bed(at, dur, fade_in, fade_out, gain=0.35):
        seg = street[:int(round(dur * kit.RATE))].copy() * gain
        n = len(seg); env = np.ones(n)
        fi, fo = int(fade_in * kit.RATE), int(fade_out * kit.RATE)
        if fi: env[:fi] = np.linspace(0, 1, fi)
        if fo: env[-fo:] = np.linspace(1, 0, fo)
        _lay(mix, seg * env[:, None], at)
    bed(0.0, 4.0, 2.5, 0.12, gain=0.25)            # S0: bed fades in (about -18 dB at the start)
    bed(18.0, 2.0, 0.1, 0.12)                      # S3
    bed(34.0, 2.0, 0.1, 0.12)                      # S6
    bed(58.0, 6.0, 0.1, 5.0)                       # S10: bed fades out
    # 57.0-58.0: the grid hold is declared silence.
    for c in range(32):                            # key clicks under the typing (kit click, declared synthetic)
        mix.click(0.36 + c * 0.083, gain=0.08, bright=5000)
    for at in (18.18, 18.6, 18.66, 18.72, 18.78, 34.18, 34.6, 34.66, 34.72):
        mix.click(at, gain=0.09, bright=5000)


if __name__ == "__main__":
    if not (len(sys.argv) > 1 and sys.argv[1] == "--stills"):
        precompute()
    film.render()
