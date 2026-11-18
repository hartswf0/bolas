"""99 Ways to Tell a Story - Template (baseline b1), Direction 2: Photo-Fumetti Cutout.

The film PERFORMS the page assets/pages/99-ways-template.png. Nothing here redraws the page its own way:

* page art            assets/pages/99-ways-template.png (page-cartoonist, page/build_page.py)
* per-frame panels    films/swarm/99-ways-template/anim/panels.py (rig-animator): FK joint overrides on the
                      page builder's own panel functions; with every override at rest a panel IS the page crop
* derivative pages    assets/pages/99-ways-template-{compressed,platform}.png + variants/rest/<D>/<panel> layers
* lettering           page/glyphs.json pen strokes (+ variants/glyphs_extra.json '2','F'; + one '3' authored here
                      in the same pen for the ledger card)
* sound               anim/sound/*.wav stems (foraged: Moving Image Archive room tone, Commons PD/CC BY foley;
                      counter bell + paper handling synthesized and declared by the rig-animator)

Shot list (plan.md section 6): S0 borders rule in, S1-S8 route R0 P1..P8, S9 full-page reading lift,
S10 D1 compressed, S11 D2 from the platform, S12 ledger card E0-E5 x B/D1/D2.

Panels not yet read show the first pose of their shot (the page "before it happens"); panels already read show
their rest pose = page art. Every action resolves to the page (asserted below).

Run from the project root:  python3 films/99-ways-template.py [--stills t ...]
"""
import json
import math
import sys
import wave
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SW = HERE / "swarm" / "99-ways-template"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SW / "anim"))
from kit import Film  # noqa: E402
import panels as PN  # noqa: E402  (rig-animator; imports page/build_page.py as PN.bp)

bp = PN.bp
PL = sys.modules["penlib"]
FPS = 24
OW, OH = 960, 540
SURROUND = np.array([24, 23, 22], np.uint8)       # the table the sheet lies on (near-black, the page's ink)
PAGES = {"B": ROOT / "assets/pages/99-ways-template.png",
         "D1": ROOT / "assets/pages/99-ways-template-compressed.png",
         "D2": ROOT / "assets/pages/99-ways-template-platform.png"}
PAGE = {k: np.asarray(Image.open(p).convert("RGB")).copy() for k, p in PAGES.items()}
PH_, PW_ = PAGE["B"].shape[:2]
assert max(PH_, PW_) >= 2400 and (PW_, PH_) == (2550, 3300), "page proof size"
TIMING = json.load(open(SW / "anim" / "timing.json"))

# ------------------------------------------------------------------------------------------- schedule (frames)
SEQ = [("S0", 96), ("S1", 120), ("S2", 120), ("S3", 120), ("S4", 120), ("S5", 120), ("S6", 120), ("S7", 120),
       ("S8", 168), ("S9", 144), ("S10", 168), ("S11", 228), ("S12", 96)]
START = {}
_g = 0
for _s, _n in SEQ:
    START[_s] = _g
    _g += _n
TOTAL = _g
for _s in ["S%d" % i for i in range(9)]:
    assert TIMING["shots"][_s]["film_in_f"] == START[_s], (_s, "film offsets drifted from timing.json")
ROUTE = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]
SHOT_OF = {p: "S%d" % (i + 1) for i, p in enumerate(ROUTE)}


def which(g):
    for s, n in SEQ:
        if START[s] <= g < START[s] + n:
            return s, g - START[s]
    return SEQ[-1][0], g - START[SEQ[-1][0]]


# ------------------------------------------------------------------------------------------- panel images
_U8 = {}


def u8(a):
    return np.clip(np.round(a), 0, 255).astype(np.uint8)


def panel_img(shot, f):
    st = PN.state_at(shot, f) if shot != "S0" else {}
    key = (shot, json.dumps(st, sort_keys=True, default=str))
    if key not in _U8:
        if len(_U8) > 300:
            _U8.pop(next(iter(_U8)))
        _U8[key] = u8(PN.render_panel(SHOTS_PANEL[shot], st))
    return _U8[key]


SHOTS_PANEL = {s: PN.SHOTS[s]["panel"] for s in PN.SHOTS}
FIRST = {}


def first_img(p):
    """The first pose of panel p's shot (shown while p is still unread)."""
    if p not in FIRST:
        FIRST[p] = panel_img(SHOT_OF[p], 0)
    return FIRST[p]


# ------------------------------------------------------------------------------------------- derivative layers
def _load_stack(d):
    L = json.load(open(d / "layers.json"))
    bg = None
    stat, groups, border = [], {}, None
    for l in L["layers"]:
        a = np.asarray(Image.open(d / l["file"]).convert("RGBA")).astype(np.float32)
        if bg is None:
            bg = a[..., :3].copy()
            continue
        nm = l["name"]
        ys, xs = np.nonzero(a[..., 3] > 0)
        if len(xs) == 0:
            continue
        x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
        item = (a[y0:y1, x0:x1, :3].copy(), a[y0:y1, x0:x1, 3:4] / 255.0, int(x0), int(y0))
        if nm == "border":
            border = item
        elif nm.startswith("b_") or nm.startswith("visitor"):
            gid = nm.split(".")[0]
            groups.setdefault(gid, []).append(item)
        else:
            stat.append(item)
    base = bg
    for it in stat:
        _over(base, it, 0, 0)
    return {"bounds": tuple(L["bounds_page_px"]), "base": base, "groups": groups, "border": border}


def _over(out, item, dx, dy):
    rgb, a, x0, y0 = item
    h, w = out.shape[:2]
    X0, Y0 = x0 + int(dx), y0 + int(dy)
    X1, Y1 = X0 + rgb.shape[1], Y0 + rgb.shape[0]
    cx0, cy0, cx1, cy1 = max(0, X0), max(0, Y0), min(w, X1), min(h, Y1)
    if cx0 >= cx1 or cy0 >= cy1:
        return
    r = rgb[cy0 - Y0:cy1 - Y0, cx0 - X0:cx1 - X0]
    aa = a[cy0 - Y0:cy1 - Y0, cx0 - X0:cx1 - X0]
    o = out[cy0:cy1, cx0:cx1]
    o *= (1 - aa)
    o += r * aa


STACK = {}
for _d, _ps in (("D1", ["C1", "C2"]), ("D2", ["V1", "V2", "V3", "V4"])):
    for _p in _ps:
        STACK[(_d, _p)] = _load_stack(SW / "variants" / "rest" / _d / _p)
_DC = {}


def dpanel(page, p, state):
    """Derivative panel composite. state: {group_id: None (rest) | 'hidden' | (dx, dy)}."""
    key = (page, p, json.dumps(state, sort_keys=True))
    if key in _DC:
        return _DC[key]
    S = STACK[(page, p)]
    out = S["base"].copy()
    for gid, items in S["groups"].items():
        st = state.get(gid)
        if st == "hidden":
            continue
        dx, dy = (0, 0) if st is None else st
        for it in items:
            _over(out, it, dx, dy)
    if S["border"] is not None:
        _over(out, S["border"], 0, 0)
    if len(_DC) > 200:
        _DC.pop(next(iter(_DC)))
    _DC[key] = u8(out)
    return _DC[key]


def drop(f, land):
    """Balloon as an impact object, on ones: -150, -55, +9 (bounce), land; hidden before (rig-animator's rule)."""
    if f < land - 3:
        return "hidden"
    return {land - 3: (0, -150), land - 2: (0, -55), land - 1: (0, 9)}.get(f)


# ------------------------------------------------------------------------------------------- camera
def cam_panel(b, pad=60):
    x0, y0, x1, y1 = b
    s = min(OH / (y1 - y0 + pad), OW / (x1 - x0 + pad * 2))
    return ((x0 + x1) / 2, (y0 + y1) / 2, s)


S_FULL = (OH - 20) / PH_
CAM_FULL = (PW_ / 2, PH_ / 2, S_FULL)
CAM_FILL = (PW_ / 2, 760, OW / PW_)               # the sheet fills the frame (S0 opening)
CAM = {p: cam_panel(bp.PANELS[p]) for p in ROUTE}
MEMO = (150 + (149 + 392) / 2, 150 + (732 + 884) / 2)   # memo slip centre, page px (page/rest/P1/10_memo.png)
CAM_MEMO = (MEMO[0] + 60, MEMO[1] - 40, 1.18)


def smooth(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def lerp_cam(a, b, u):
    u = smooth(u)
    # zoom in log space so the scale change reads evenly
    s = math.exp(math.log(a[2]) + (math.log(b[2]) - math.log(a[2])) * u)
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, s)


def path(f, keys):
    """keys: [(frame, cam)], held between, eased from one to the next."""
    if f <= keys[0][0]:
        return keys[0][1]
    for (fa, ca), (fb, cb) in zip(keys, keys[1:]):
        if f < fb:
            return lerp_cam(ca, cb, (f - fa) / max(1, fb - fa))
    return keys[-1][1]


def b_cam(shot, f):
    if shot == "S0":
        return path(f, [(0, CAM_FILL), (8, CAM_FILL), (40, CAM_FULL), (70, CAM_FULL), (94, CAM["P1"])])
    if shot == "S1":
        return path(f, [(0, CAM["P1"]), (40, CAM["P1"]), (58, CAM_MEMO), (94, CAM_MEMO), (112, CAM["P1"])])
    i = ROUTE.index(SHOTS_PANEL[shot])
    prev, cur = CAM[ROUTE[i - 1]], CAM[ROUTE[i]]
    T = 16 if ROUTE[i] in ("P4", "P7") else 10
    return path(f, [(0, prev), (T, cur)])


# ------------------------------------------------------------------------------------------- view renderer
def view(page_arr, cam, overrides=(), lift=None):
    """Render a camera view of a page. overrides: [(x0, y0, img)] pasted at page px; lift: (bounds, d)."""
    cx, cy, s = cam
    w, h = OW / s, OH / s
    # keep the camera on the sheet while the frame is smaller than it
    if w <= PW_:
        cx = min(max(cx, w / 2), PW_ - w / 2)
    else:
        cx = PW_ / 2
    if h <= PH_:
        cy = min(max(cy, h / 2), PH_ - h / 2)
    else:
        cy = PH_ / 2
    X0, Y0 = cx - w / 2, cy - h / 2
    ix0, iy0 = max(0, int(math.floor(X0))), max(0, int(math.floor(Y0)))
    ix1, iy1 = min(PW_, int(math.ceil(X0 + w))), min(PH_, int(math.ceil(Y0 + h)))
    reg = page_arr[iy0:iy1, ix0:ix1].copy()
    for (ox, oy, img) in overrides:
        hh, ww = img.shape[:2]
        a0, b0 = max(ix0, ox), max(iy0, oy)
        a1, b1 = min(ix1, ox + ww), min(iy1, oy + hh)
        if a0 < a1 and b0 < b1:
            reg[b0 - iy0:b1 - iy0, a0 - ix0:a1 - ix0] = img[b0 - oy:b1 - oy, a0 - ox:a1 - ox]
    if lift is not None:
        (bx0, by0, bx1, by1), d = lift
        if d > 0:
            reg = _lifted(reg, page_arr, (bx0 - ix0, by0 - iy0, bx1 - ix0, by1 - iy0), d)
    out = np.empty((OH, OW, 3), np.uint8)
    out[:] = SURROUND
    ox0, oy0 = max(0, int(round((ix0 - X0) * s))), max(0, int(round((iy0 - Y0) * s)))
    ow_, oh_ = int(round((ix1 - ix0) * s)), int(round((iy1 - iy0) * s))
    ow_, oh_ = min(ow_, OW - ox0), min(oh_, OH - oy0)
    small = cv2.resize(reg, (ow_, oh_), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    out[oy0:oy0 + oh_, ox0:ox0 + ow_] = small
    return out


GROUND = None


def _lifted(reg, page_arr, b, d):
    """Reading-order lift: the panel's paper rises one shadow-step up-left, its soft paper shadow falls down-right."""
    global GROUND
    if GROUND is None:
        GROUND = u8(bp.sheet())
    x0, y0, x1, y1 = b
    panel = reg[y0:y1, x0:x1].copy()
    out = reg.astype(np.float32)
    out[y0:y1, x0:x1] = GROUND[:y1 - y0, :x1 - x0]          # the sheet under the panel
    m = np.zeros(reg.shape[:2], np.float32)
    off = int(6 + d * 0.6)
    m[y0 + off:y1 + off, x0 + off:x1 + off] = 1
    m = cv2.GaussianBlur(m, (0, 0), 4 + d * 0.4) * 0.35
    out *= (1 - m[..., None])
    out[y0 - d:y1 - d, x0 - d:x1 - d] = panel
    return u8(out)


def b_overrides(cur_idx, cur_img):
    """Panels before the current one rest (= page), the current one animates, later ones hold their first pose."""
    ov = []
    for j, p in enumerate(ROUTE):
        x0, y0 = bp.PANELS[p][:2]
        if j == cur_idx:
            ov.append((x0, y0, cur_img))
        elif j > cur_idx:
            ov.append((x0, y0, first_img(p)))
    return ov


# ------------------------------------------------------------------------------------------- S0
def s0_page(f):
    page = u8(PN.s0_frame(f))
    pose = max(0, (f - PN.S0_START) // PN.S0_POSE_FRAMES + 1) if f >= PN.S0_START else 0
    for j, p in enumerate(ROUTE):
        if pose - (4 * j + 3) >= 2 and j > 0:          # box closed: lay the panel's first pose, not its rest
            x0, y0, x1, y1 = bp.PANELS[p]
            page[y0:y1, x0:x1] = first_img(p)
    return page


# ------------------------------------------------------------------------------------------- full-page renders
_SMALL = {}


def full(page_id, extra_ov=(), lift=None):
    if not extra_ov and lift is None:
        if page_id not in _SMALL:
            _SMALL[page_id] = view(PAGE[page_id], CAM_FULL)
        return _SMALL[page_id]
    return view(PAGE[page_id], CAM_FULL, extra_ov, lift)


def turn(under, over, u):
    """Page turn: the next sheet slides in from the right over the last, a soft shadow at its leading edge."""
    u = smooth(u)
    dx = int(round(OW * (1 - u)))
    out = under.astype(np.float32)
    if dx < OW:
        x = np.arange(OW)[None, :, None]
        sh = np.clip(1 - (dx - x) / 40.0, 0, 1) * (x < dx) * 0.45
        out *= (1 - sh)
        out[:, dx:] = over[:, :OW - dx]
    return u8(out)


# ------------------------------------------------------------------------------------------- S9-S11
LIFT_START, LIFT_EACH = 30, 12
LIFT_POSES = [0, 14, 28, 28, 14, 0]        # page px, on twos


def s9(f):
    if f < 24:
        return view(PAGE["B"], lerp_cam(CAM["P8"], CAM_FULL, f / 24))
    k = (f - LIFT_START) // LIFT_EACH
    if 0 <= k < 8 and f >= LIFT_START:
        d = LIFT_POSES[min(5, ((f - LIFT_START) % LIFT_EACH) // 2)]
        return full("B", lift=(bp.PANELS[ROUTE[k]], d))
    return full("B")


D1P = {p["id"]: tuple(p["bounds_px"]) for p in json.load(open(SW / "variants/d1_panels.json"))["panels"]}
D2P = {p["id"]: tuple(p["bounds_px"]) for p in json.load(open(SW / "variants/d2_panels.json"))["panels"]}
S10_LAND = {"b_what_time": 62, "b_ten_past": 86, "b_thanks": 126, "b_forgot": 148}
S11_LAND = {"b_what_time": 62, "b_ten_past": 136, "b_thanks": 194}   # r1: her lines in V1 and V4, tails to her mouth
V4_WALK = (168, 190)                        # visitor walks off on twos, from her V1 place to her V4 rest
V4_FROM = (1201, -9)


def d1_ov(f):
    c1 = {g: drop(f, S10_LAND[g]) for g in ("b_what_time", "b_ten_past")}
    c2 = {g: drop(f, S10_LAND[g]) for g in ("b_thanks", "b_forgot")}
    return [(D1P["C1"][0], D1P["C1"][1], dpanel("D1", "C1", c1)), (D1P["C2"][0], D1P["C2"][1], dpanel("D1", "C2", c2))]


def s10(f):
    ov = d1_ov(f)
    if f < 12:
        return turn(full("B"), full("D1", ov), f / 12)
    cam = path(f, [(12, CAM_FULL), (30, CAM_FULL), (48, cam_panel(D1P["C1"])), (102, cam_panel(D1P["C1"])),
                   (118, cam_panel(D1P["C2"]))])
    return view(PAGE["D1"], cam, ov)


def v4_state(f):
    a, b = V4_WALK
    if f >= b:
        return None
    pose = max(0, (f - a)) // 2                 # on twos
    n = (b - a) // 2
    u = min(1.0, pose / n)
    u = u * u * (3 - 2 * u) * 0.25 + u * 0.75   # walk, easing into the exit
    bob = -10 if pose % 2 else 0                # Gilliam stepping: no legs, the whole cut-out bobs a step
    return (int(round(V4_FROM[0] * (1 - u))), int(round(V4_FROM[1] * (1 - u) + (bob if u < 1 else 0))))


def d2_ov(f):
    ov = []
    st = {"V1": {"b_what_time": drop(f, S11_LAND["b_what_time"])}, "V2": {},
          "V3": {"b_ten_past": drop(f, S11_LAND["b_ten_past"])},
          "V4": {"visitor": v4_state(f), "b_thanks": drop(f, S11_LAND["b_thanks"])}}
    for p in ["V1", "V2", "V3", "V4"]:
        ov.append((D2P[p][0], D2P[p][1], dpanel("D2", p, st[p])))
    return ov


def s11(f):
    ov = d2_ov(f)
    if f < 12:
        return turn(full("D1"), full("D2", ov), f / 12)
    cam = path(f, [(12, CAM_FULL), (26, CAM_FULL), (42, cam_panel(D2P["V1"])), (96, cam_panel(D2P["V1"])),
                   (108, cam_panel(D2P["V2"])), (118, cam_panel(D2P["V2"])), (128, cam_panel(D2P["V3"])),
                   (156, cam_panel(D2P["V3"])), (166, cam_panel(D2P["V4"]))])
    return view(PAGE["D2"], cam, ov)


# ------------------------------------------------------------------------------------------- S12 ledger card
PL.GLYPHS.update({k: (v[0], [tuple(st) for st in v[1]])
                  for k, v in json.load(open(SW / "variants/glyphs_extra.json"))["glyphs"].items()})
# '3' in the same pen (cap height 1, baseline 0, y up), authored for the ledger card's E3/E3b rows (HANDMADE)
PL.GLYPHS["3"] = (0.48, [("L", ((0.05, 0.88), (0.17, 0.99), (0.31, 1.0), (0.42, 0.9), (0.42, 0.74),
                                (0.33, 0.6), (0.18, 0.55))),
                         ("L", ((0.18, 0.55), (0.36, 0.5), (0.46, 0.34), (0.44, 0.14), (0.32, 0.02),
                                (0.17, 0.0), (0.03, 0.1)))])
COV = json.load(open(SW / "coverage.json"))["pages"]
EV = [("E0", "reads the memo"), ("E1", "leaves the desk"), ("E2", "What time is it?"), ("E3", "Ten past four!"),
      ("E3b", "Thanks!"), ("E4", "opens the cupboard"), ("E5", "forgets the key")]
CW_, CH_ = 1920, 1080
COLS = [(130, 930), (930, 1240), (1240, 1560), (1560, 1860)]
ROW0, ROWH = 300, 82
CUES = ["implied, by its cue:  D1 E4 - the door is already open on its hinge,",
        "D2 E1 - the desk is empty through the glass,  D2 E4 - the open cupboard, far back.",
        "Outcome on every page: the key stays on its hook, the SERVICE door stays closed."]


def _text(lines, cap, seed):
    for ln in lines:
        for c in ln:
            assert c in PL.GLYPHS, ("no glyph", c, ln)
    return PL.letter_lines(lines, cap, seed)


def _ledger_setup():
    g = bp.sheet().astype(np.float32)
    band = g[900:900 + int(2550 * CH_ / CW_)]
    ground = cv2.resize(band, (CW_, CH_), interpolation=cv2.INTER_AREA)
    items = []          # (appear_frame, mask_full, reveal_axis_box)

    def put(mask, x, y, anchor="l"):
        m = np.zeros((CH_, CW_), np.uint8)
        h, w = mask.shape
        if anchor == "c":
            x = int(x - w / 2)
        y = int(y - h / 2)
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(CW_, x + w), min(CH_, y + h)
        m[y0:y1, x0:x1] = np.maximum(m[y0:y1, x0:x1], mask[y0 - y:y1 - y, x0 - x:x1 - x])
        return m, (x0, x1)

    items.append((14,) + put(_text(["Time-table of events  (ledger b1)"], 46, 501), COLS[0][0] - 20, 110))
    for i, (lab, sub) in enumerate([("B", "the page"), ("D1", "compressed"), ("D2", "platform")]):
        cx = (COLS[i + 1][0] + COLS[i + 1][1]) / 2
        items.append((22 + 2 * i,) + put(_text([lab], 42, 510 + i), cx, 205, "c"))
        items.append((22 + 2 * i,) + put(_text([sub], 22, 520 + i), cx, 252, "c"))
    for r, (eid, what) in enumerate(EV):
        y = ROW0 + ROWH * r + ROWH / 2
        fr = 30 + 5 * r
        items.append((fr,) + put(_text([eid], 36, 600 + r), COLS[0][0], y))
        items.append((fr,) + put(_text([what], 30, 620 + r), COLS[0][0] + 130, y))
        for c, pg in enumerate(["B", "D1", "D2"]):
            stt = COV[pg]["events"][eid]["status"]
            cx = (COLS[c + 1][0] + COLS[c + 1][1]) / 2
            items.append((fr + 2,) + put(_text([stt], 30, 640 + 10 * r + c), cx, y, "c"))
    for i, ln in enumerate(CUES):
        items.append((62 + 2 * i,) + put(_text([ln], 21, 700 + i), COLS[0][0], ROW0 + ROWH * 7 + 42 + 34 * i))
    rules = []          # (start_frame, mask)
    yb = ROW0 + ROWH * 7
    specs = [((COLS[0][0] - 20, 160), (COLS[-1][1], 160), 7), ((COLS[0][0] - 20, ROW0), (COLS[-1][1], ROW0), 6),
             ((COLS[0][0] - 20, yb), (COLS[-1][1], yb), 7)]
    specs += [((COLS[0][0] - 20, ROW0 + ROWH * r), (COLS[-1][1], ROW0 + ROWH * r), 2.5) for r in range(1, 7)]
    specs += [((x, 160), (x, yb), 3.5) for x in (COLS[1][0], COLS[2][0], COLS[3][0])]
    for k, (a, b, w) in enumerate(specs):
        m = np.zeros((CH_, CW_), np.uint8)
        PL.brush_line(m, [a, b], w, 800 + k)
        rules.append((2 + 2 * k, m, a, b))
    return {"ground": ground, "items": items, "rules": rules}


LEDGER = {}


def ledger_card(f):
    if not LEDGER:
        LEDGER.update(_ledger_setup())
    L = LEDGER
    out = L["ground"].copy()
    for (fr, m, a, b) in L["rules"]:
        if f < fr:
            continue
        prog = min(1.0, (f - fr) // 2 * 0.5 + 0.5)      # each rule over two poses (half, whole), on twos
        mm = m.copy()
        if a[1] == b[1]:
            cut = int(a[0] + (b[0] - a[0]) * prog)
            mm[:, cut + 6:] = 0
        else:
            cut = int(a[1] + (b[1] - a[1]) * prog)
            mm[cut + 6:, :] = 0
        PL.ink_onto(out, mm)
    for (fr, m, (x0, x1)) in L["items"]:
        if f < fr:
            continue
        prog = min(1.0, ((f - fr) // 2 + 1) / 2.0)       # the pen writes left to right over two poses
        mm = m.copy()
        mm[:, int(x0 + (x1 - x0) * prog):] = 0
        PL.ink_onto(out, mm)
    return cv2.resize(u8(out), (OW, OH), interpolation=cv2.INTER_AREA)


def s12(f):
    if f < 12:
        return turn(full("D2"), ledger_card(0), f / 12)
    return ledger_card(f)


# ------------------------------------------------------------------------------------------- the picture
def render_frame(g):
    shot, f = which(g)
    if shot == "S0":
        return view(s0_page(f), b_cam("S0", f))
    if shot in SHOT_OF.values():
        i = ROUTE.index(SHOTS_PANEL[shot])
        return view(PAGE["B"], b_cam(shot, f), b_overrides(i, panel_img(shot, f)))
    if shot == "S9":
        return s9(f)
    if shot == "S10":
        return s10(f)
    if shot == "S11":
        return s11(f)
    return s12(f)


# ------------------------------------------------------------------------------------------- checks
def checks():
    rep = {"rest_vs_page_mean_abs": {}, "film_rest_vs_page_view_mean_abs": {}, "balloon_land": {}, "variants": {}}
    pg = PAGE["B"].astype(np.float32)
    for p in ROUTE:
        s = SHOT_OF[p]
        x0, y0, x1, y1 = bp.PANELS[p]
        crop = pg[y0:y1, x0:x1]
        ae = max([TIMING["shots"][s]["action_end_f"]] + [b["land"] for b in TIMING["shots"][s]["balloons"]])
        last = TIMING["shots"][s]["frames"] - 1
        d_end = float(np.abs(panel_img(s, ae).astype(np.float32) - crop).mean())
        d_last = float(np.abs(panel_img(s, last).astype(np.float32) - crop).mean())
        assert d_end <= 4 and d_last <= 4, (s, d_end, d_last)
        rep["rest_vs_page_mean_abs"][s] = {"action_and_balloons_end_f": ae, "at_action_end": round(d_end, 3),
                                          "at_last_frame": round(d_last, 3)}
        # film scale: the rendered film frame vs the same camera over the untouched page, inside this panel
        g = START[s] + last
        cam = b_cam(s, last)
        a = render_frame(g).astype(np.float32)
        ref = view(PAGE["B"], cam).astype(np.float32)
        cx, cy, sc = cam
        w, h = OW / sc, OH / sc
        cx = min(max(cx, w / 2), PW_ - w / 2)
        cy = min(max(cy, h / 2), PH_ - h / 2)
        X0, Y0 = cx - w / 2, cy - h / 2
        bx0, by0 = int((x0 - X0) * sc) + 3, int((y0 - Y0) * sc) + 3
        bx1, by1 = int((x1 - X0) * sc) - 3, int((y1 - Y0) * sc) - 3
        bx0, by0, bx1, by1 = max(0, bx0), max(0, by0), min(OW, bx1), min(OH, by1)
        dv = float(np.abs(a[by0:by1, bx0:bx1] - ref[by0:by1, bx0:bx1]).mean())
        assert dv <= 4, (s, "film view", dv)
        rep["film_rest_vs_page_view_mean_abs"][s] = round(dv, 3)
        for b in PN.SHOTS[s].get("balloons", []):
            land = b["land"]
            assert land in [bb["land"] for bb in TIMING["shots"][s]["balloons"]], (s, land)   # timing.json land frames
            assert b["id"] not in PN.state_at(s, land).get("balloons", {}), (s, "balloon not at rest on land")
            assert PN.state_at(s, land - 1)["balloons"][b["id"]] == (0, 9), (s, "no bounce before land")
            assert PN.state_at(s, land - 4)["balloons"][b["id"]] == "hidden"
            rep["balloon_land"][f"{s}.{b['id']}"] = {"land_f": land, "film_f": START[s] + land,
                                                   "film_s": round((START[s] + land) / FPS, 3)}
    for (d, p), S in STACK.items():
        x0, y0, x1, y1 = S["bounds"]
        dv = float(np.abs(dpanel(d, p, {}).astype(np.float32) - PAGE[d][y0:y1, x0:x1].astype(np.float32)).mean())
        assert dv <= 4, (d, p, dv)
        rep["variants"][f"{d}.{p}"] = round(dv, 3)
    fk = json.load(open(SW / "anim" / "fk_test.json"))
    rep["fk_test"] = {k: fk[k] for k in fk if k in ("pass", "summary", "invariants", "result")} or "see anim/fk_test.json"
    rep["S10_land_film_s"] = {k: round((START["S10"] + v) / FPS, 3) for k, v in S10_LAND.items()}
    rep["S11_land_film_s"] = {k: round((START["S11"] + v) / FPS, 3) for k, v in S11_LAND.items()}
    rep["frames"], rep["seconds"] = TOTAL, TOTAL / FPS
    json.dump(rep, open(SW / "editor_checks.json", "w"), indent=1)
    print("checks passed ->", SW / "editor_checks.json")


# ------------------------------------------------------------------------------------------- sound
SND = SW / "anim" / "sound"
_W = {}


def wav(name):
    if name not in _W:
        with wave.open(str(SND / f"{name}.wav")) as wf:
            n, ch = wf.getnframes(), wf.getnchannels()
            a = np.frombuffer(wf.readframes(n), np.int16).astype(np.float64) / 32768
            _W[name] = a.reshape(-1, ch).mean(1) if ch > 1 else a
    return _W[name]


def db(x):
    return 10 ** (x / 20)


def sound(mix):
    sec = lambda g: g / FPS
    # room tone (Moving Image Archive, Panama by Air 1914: the print's noise floor), an 11 s seamless loop
    rt = wav("room_tone")
    t = 0.0
    while t < TOTAL / FPS:
        mix.add(rt, t, 1.0)
        t += len(rt) / 44100
    step_k = [0]

    def step(at, gain):
        step_k[0] += 1
        mix.add(wav(f"footstep_{(step_k[0] - 1) % 6 + 1}"), at, gain, pan=0.1)

    for s in ["S%d" % i for i in range(9)]:
        for c in TIMING["shots"][s]["sounds"]:
            at = sec(START[s] + c["f"])
            cue = c["cue"]
            if cue == "room_tone":
                continue
            if cue == "footstep":
                step(at, db(-6) if s in ("S2", "S3") else db(-9))
            elif cue == "counter_bell":
                mix.add(wav("counter_bell"), at, 1.0, pan=-0.3)
            elif cue == "platform_distant":
                sig = wav("platform_distant")[: int(c.get("len_f", 96) / FPS * 44100)].copy()
                fade = 4410
                sig[-fade:] *= np.linspace(1, 0, fade)
                mix.add(sig, at, db(-6), pan=-0.5)
            elif cue == "steps_receding":
                mix.add(wav("steps_receding"), at, db(-3), pan=-0.5)
            elif cue == "paper_handling":
                mix.add(wav("paper_handling"), at, 1.0)
            else:
                mix.add(wav(cue), at, 1.0)
    # S9: the reading lift is quiet: room tone only. Page turns (declared synthesized paper handling).
    for s in ("S10", "S11", "S12"):
        mix.add(wav("paper_handling"), sec(START[s]), 1.0)
    # S10 D1 compressed: bell, taps, creak
    b = START["S10"]
    mix.add(wav("counter_bell"), sec(b + 52), db(-3), pan=-0.3)
    for g in S10_LAND.values():
        mix.add(wav("paper_tap"), sec(b + g), 1.0)
    mix.add(wav("door_creak"), sec(b + 106), db(-3))
    # S11 D2 from the platform: the platform (CC BY 3.0, Glaneur de sons), the bell from outside, her steps
    b = START["S11"]
    sig = wav("platform_distant")[: int(228 / FPS * 44100)].copy()
    sig[:4410] *= np.linspace(0, 1, 4410)
    sig[-8820:] *= np.linspace(1, 0, 8820)
    mix.add(sig, sec(b), 1.0, pan=-0.2)
    mix.add(wav("counter_bell"), sec(b + 46), db(-6), pan=0.2)
    for g in S11_LAND.values():
        mix.add(wav("paper_tap"), sec(b + g), 1.0)
    for g in range(V4_WALK[0], V4_WALK[1], 4):
        step(sec(b + g), db(-12))
    mix.add(wav("steps_receding"), sec(b + V4_WALK[1] - 6), db(-6), pan=-0.6)
    # S12 ledger: a tick, then a single bell
    b = START["S12"]
    mix.add(wav("clock_tick"), sec(b + 30), 1.0)
    mix.add(wav("clock_tick"), sec(b + 54), 1.0)
    mix.add(wav("counter_bell"), sec(b + 78), db(-4), pan=-0.1)


# ------------------------------------------------------------------------------------------- film
film = Film("99-ways-template", seconds=TOTAL / FPS, boil=0, wobble=0)
film.poster_at = (START["S8"] + 140) / FPS        # the defining beat's hold: key on its hook, pencil at chin


@film.picture
def picture(t, ink):
    ink.paper(grain=False)                          # no synthetic grain: only the photographs' own
    g = min(TOTAL - 1, int(round(t * FPS)))
    ink.img.paste(Image.fromarray(render_frame(g)), (0, 0))


film.sound(sound)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--checks":
        checks()
    else:
        if not (len(sys.argv) > 1 and sys.argv[1] == "--stills"):
            checks()
        film.render()
