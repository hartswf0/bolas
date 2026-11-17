"""Moins d'un quart de seconde pour vivre -- one plate, two strips.

Editor assembly (SCION swarm, Direction 1 'Brush plate, written balloons').
Everything on screen is HANDMADE: the brush plate (plate-artist, recorded stroke
ledger), the balloons and page lettering (writer-letterer, single-stroke pen hand
written in pen order). Sound is FORAGED from Wikimedia Commons (a real ink-pen
recording cut into one grain per stroke, and a real night insect chorus),
placed by the sound unit's cue engine.

The film is a camera over the handmade page. At every panel hold the camera is
at 1:1 with integer offsets, so the 540 px panel in the frame is the page panel
pixel for pixel (I1/I4). No grain, no vignette, no fades.

    python3 films/moins-dun-quart-de-seconde-pour-vivre.py            # page + film
    python3 films/moins-dun-quart-de-seconde-pour-vivre.py --stills 12 25 40
    python3 films/moins-dun-quart-de-seconde-pour-vivre.py --page      # page and art files only
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from kit import Film, ease  # noqa: E402

SLUG = "moins-dun-quart-de-seconde-pour-vivre"
ROOT = HERE.parent
SWARM = HERE / "swarm" / SLUG
SRC = HERE / "sources" / SLUG
DELIV = SWARM / "deliverables"
PAGE_OUT = ROOT / "assets" / "pages" / f"{SLUG}.png"

sys.path.insert(0, str(SWARM / "letterer-build"))
sys.path.insert(0, str(SWARM / "sound-build"))
import letter  # noqa: E402  (writer-letterer's code, read only)

FPS = 24
PAPER = 250            # plate paper #FAFAFA; page paper is the same value
INK_BLACK = 20         # cut-to-black value (ink #141414)
P = 540
PAGE_W, PAGE_H = 2480, 1754
PAD = 600
XS = [106, 682, 1258, 1834]
YS = {"A": 290, "B": 990}
PANELS = ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4"]
POS = {k: (XS[int(k[1]) - 1], YS[k[0]]) for k in PANELS}
LETTERED = ["A1", "A2", "A4", "B1", "B2", "B3", "B4"]

PLATE_PATH = SRC / "plate" / "plate-540.png"
PLATE = np.asarray(Image.open(PLATE_PATH).convert("L")).copy()
PLATE_SHA = "55b62d4cc2a235d0a66e9b64c9ff263dfa45cec20e59626171bc7412ce76b827"
assert hashlib.sha256(PLATE.tobytes()).hexdigest() == PLATE_SHA, "plate drift: quarantine (I1)"
PROLOGUE = [np.asarray(Image.open(SRC / "plate-artist" / "prologue" / f"f{i:03d}.png").convert("L")) for i in range(144)]
assert (PROLOGUE[-1] == PLATE).all(), "prologue must land on the canonical plate"

BJ = json.load(open(SWARM / "balloons.json"))
FINAL = {k: np.asarray(Image.open(BJ["panels"][k]["file"]).convert("RGBA")) for k in LETTERED}
_BAL = None


def balloons():
    global _BAL
    if _BAL is None:
        _BAL = letter.load_balloons()
    return _BAL


def composite(base, rgba):
    """Integer composite of an RGBA layer (R=G=B) over an L array (same as letter.composite)."""
    a = rgba[..., 3].astype(np.int32)
    c = rgba[..., 0].astype(np.int32)
    p = base.astype(np.int32)
    return ((p * (255 - a) + c * a + 127) // 255).astype(np.uint8)


# ---------------------------------------------------------------- timeline
def F(t):
    return int(round(t * FPS))


F0 = {"A1": F(10.0), "A2": F(15.6), "A3": F(21.6), "A4": F(26.6),
      "B1": F(35.0), "B2": F(41.0), "B3": F(45.0), "B4": F(50.0)}
HOLD_END = {"A1": F(15.0) - 1, "A2": F(21.0) - 1, "A3": F(26.0) - 1, "A4": F(31.0) - 1,
            "B1": F(40.5) - 1, "B2": F(44.5) - 1, "B3": F(49.5) - 1, "B4": F(57.0) - 1}
STAMP_K0 = 162                         # 6.75 s: first panel stamp (after the pull-back)
STAMP_EVERY = 4
STAMP_ORDER = ["A2", "A3", "A4", "B1", "B2", "B3", "B4"]
HEADER_K0 = STAMP_K0 + 6 * STAMP_EVERY + 2          # 188: 2 frames after the 7th stamp
HEADER_FRAMES = 19
FOOTER_K0, FOOTER_FRAMES = F(58.5), 60
SWAP_K0, SWAP_EVERY, SWAP_N = F(61.0), 18, 4
TOTAL = F(66.0)
BLACK_K0 = TOTAL - 6
STAMP_T0 = STAMP_K0 / FPS
HEADER_T0 = HEADER_K0 / FPS

# ---------------------------------------------------------------- page lettering (written in pen order)
ITEMS = ["header", "header-right", "label-A", "label-B", "footer"]
ITEM_FINAL = {k: np.asarray(Image.open(BJ["page_lettering"][k]["file"]).convert("RGBA")) for k in ITEMS}
ITEM_XY = {k: tuple(BJ["page_lettering"][k]["page_xy"]) for k in ITEMS}


def item_partial(key, nat_t):
    """The page item as written up to natural time nat_t (frames), re-brushed with the
    letterer's own brush, layout and seeds (letter.page_item with a pen position)."""
    if nat_t >= 1e8:
        return ITEM_FINAL[key]
    text, x, y, size, seed, w, anchor, emph = letter.PAGE_ITEMS[key]
    if text is None:
        text = BJ["page_lettering"][key]["text"]
    K = letter.K
    glyphs, (tw, th) = letter.layout([text], size * K, seed, emph=emph, loose=0.8)
    pad = int(size * 0.6) * K
    Wd, Ht = int(tw) + 2 * pad, int(th) + 2 * pad
    C = Image.new("L", (Wd, Ht), letter.PAPER_V)
    A = Image.new("L", (Wd, Ht), 0)
    dc, da = ImageDraw.Draw(C), ImageDraw.Draw(A)
    sched = BJ["page_lettering"][key]["strokes"]
    n = 0
    for g in glyphs:
        for si, s in enumerate(g["strokes"]):
            st = sched[n]
            t0, t1 = st["t0_f"], st["t1_f"]
            if nat_t > t0:
                u = 1.0 if nat_t >= t1 else (nat_t - t0) / max(1e-6, t1 - t0)
                s2 = [(px + pad, py + pad) for px, py in s]
                for img, col in ((dc, letter.INK_V), (da, 255)):
                    rng = np.random.default_rng(seed * 97 + n)
                    letter.brush(img, s2, w * K * g["widths"][si], rng, col=col, taper=(0.12, 0.22), press=0.2, upto=u)
            n += 1
    c = np.asarray(C.resize((Wd // K, Ht // K), Image.LANCZOS), np.float64)
    a = np.asarray(A.resize((Wd // K, Ht // K), Image.LANCZOS), np.float64)
    c = np.clip(np.round(c), letter.INK_V, letter.PAPER_V).astype(np.uint8)
    a = np.clip(np.round(a), 0, 255).astype(np.uint8)
    a[a < 3] = 0
    rgba = np.dstack([c, c, c, a])
    rgba[a == 0, :3] = 0
    return rgba


def put_item(page, key, rgba):
    x, y = ITEM_XY[key]
    h, w = rgba.shape[:2]
    page[y:y + h, x:x + w] = composite(page[y:y + h, x:x + w], rgba)


# ---------------------------------------------------------------- page builder
def build_page(plates=None, balloons_=None, items=None):
    """plates: {panel: L array or None}; balloons_: {panel: RGBA}; items: {key: RGBA}."""
    page = np.full((PAGE_H, PAGE_W), PAPER, np.uint8)
    plates = {k: PLATE for k in PANELS} if plates is None else plates
    for k, art in plates.items():
        if art is None:
            continue
        x, y = POS[k]
        page[y:y + P, x:x + P] = art
    for k, rgba in (balloons_ or {}).items():
        if rgba is None:
            continue
        x, y = POS[k]
        page[y:y + P, x:x + P] = composite(page[y:y + P, x:x + P], rgba)
    for k, rgba in (items or {}).items():
        put_item(page, k, rgba)
    return page


def final_page():
    return build_page(None, dict(FINAL), dict(ITEM_FINAL))


def write_page_files():
    DELIV.mkdir(parents=True, exist_ok=True)
    PAGE_OUT.parent.mkdir(parents=True, exist_ok=True)
    page = final_page()
    Image.fromarray(page).convert("RGB").save(PAGE_OUT, optimize=True)
    Image.fromarray(build_page()).convert("RGB").save(DELIV / "page-unlettered.png", optimize=True)
    Image.fromarray(PLATE).save(DELIV / "plate-canonical.png")
    m = 18
    for s in "AB":
        y = YS[s]
        Image.fromarray(page[y - m:y + P + m, XS[0] - m:XS[3] + P + m]).convert("RGB").save(DELIV / f"strip-{s}.png", optimize=True)
    bdir = DELIV / "balloons"
    bdir.mkdir(exist_ok=True)
    for k in LETTERED:
        Image.fromarray(FINAL[k]).save(bdir / f"{k}.png")
    bj = json.load(open(SWARM / "balloons.json"))
    for k in LETTERED:
        bj["panels"][k]["file"] = str(bdir / f"{k}.png")
        bj["panels"][k]["sha256"] = hashlib.sha256(open(bdir / f"{k}.png", "rb").read()).hexdigest()
    json.dump(bj, open(bdir / "balloons.json", "w"), indent=1)
    return page


# ---------------------------------------------------------------- state at frame k
ART_ONLY = False          # equality fixture: balloon plane removed (I2)
_cache = {}


def balloon_at(key, k):
    f = k - F0[key]
    if f < 0:
        return None
    b = balloons()[key]
    if f >= b.end_f:
        return FINAL[key]
    ck = (key, f)
    if ck not in _cache:
        _cache.clear() if len(_cache) > 64 else None
        _cache[ck] = b.frame(f)
    return _cache[ck]


def items_at(k):
    out = {}
    sc_h = {key: HEADER_FRAMES / BJ["page_lettering"][key]["natural_write_frames"] for key in ITEMS}
    for key in ITEMS[:4]:
        if k >= HEADER_K0 + HEADER_FRAMES + 1:
            out[key] = ITEM_FINAL[key]
        elif k >= HEADER_K0:
            out[key] = item_partial(key, ((k + 1) - HEADER_K0) / sc_h[key])
    scf = FOOTER_FRAMES / BJ["page_lettering"]["footer"]["natural_write_frames"]
    if k >= FOOTER_K0 + FOOTER_FRAMES + 1:
        out["footer"] = ITEM_FINAL["footer"]
    elif k >= FOOTER_K0:
        out["footer"] = item_partial("footer", ((k + 1) - FOOTER_K0) / scf)
    return out


def page_at(k):
    plates = {}
    for key in PANELS:
        if key == "A1":
            plates[key] = PROLOGUE[k] if k < 144 else PLATE
        else:
            i = STAMP_ORDER.index(key)
            plates[key] = PLATE if k >= STAMP_K0 + i * STAMP_EVERY else None
    bal = {}
    if not ART_ONLY:
        for key in LETTERED:
            bal[key] = balloon_at(key, k)
        if SWAP_K0 <= k < SWAP_K0 + SWAP_EVERY * SWAP_N and ((k - SWAP_K0) // SWAP_EVERY) % 2 == 0:
            for i in range(4):            # top row carries strip B's balloon set over the same art
                bal["A%d" % (i + 1)] = FINAL["B%d" % (i + 1)]
    return build_page(plates, bal, items_at(k))


# ---------------------------------------------------------------- camera
def at_panel(key):
    x, y = POS[key]
    return (x + 270.0, y + 270.0, 1.0)


FULL = (1240.0, 877.0, 0.30)
STRIP_A = (1240.0, 560.0, 960 / 2390)


def cam_lerp(a, b, u):
    s = math.exp(math.log(a[2]) + (math.log(b[2]) - math.log(a[2])) * u)
    # keep the zoom feeling straight: interpolate the centre by how far the scale has gone
    if a[2] != b[2]:
        w = (1 / s - 1 / a[2]) / (1 / b[2] - 1 / a[2])
    else:
        w = u
    return (a[0] + (b[0] - a[0]) * w, a[1] + (b[1] - a[1]) * w, s)


def move(k, k0, k1, a, b):
    return cam_lerp(a, b, ease(k, k0, k1))


def camera(k):
    if k < 144:
        return at_panel("A1")
    if k < 216:
        return move(k, 144, 162, at_panel("A1"), FULL)
    if k < F0["A1"]:
        return move(k, 216, F0["A1"], FULL, at_panel("A1"))
    seq = ["A1", "A2", "A3", "A4"]
    for a, b in zip(seq, seq[1:]):
        if k <= HOLD_END[a]:
            return at_panel(a)
        if k < F0[b]:
            return move(k, HOLD_END[a] + 1, F0[b], at_panel(a), at_panel(b))
    if k <= HOLD_END["A4"]:
        return at_panel("A4")
    s3 = HOLD_END["A4"] + 1                         # 31.0 s: pull back to strip A
    if k < F(33.5):
        return move(k, s3, s3 + 14, at_panel("A4"), STRIP_A)
    if k < F0["B1"]:
        return move(k, F(33.5), F0["B1"], STRIP_A, at_panel("B1"))
    seq = ["B1", "B2", "B3", "B4"]
    for a, b in zip(seq, seq[1:]):
        if k <= HOLD_END[a]:
            return at_panel(a)
        if k < F0[b]:
            return move(k, HOLD_END[a] + 1, F0[b], at_panel(a), at_panel(b))
    if k <= HOLD_END["B4"]:
        return at_panel("B4")
    return move(k, F(57.0), F(58.5), at_panel("B4"), FULL)


def shoot(page, cam, W=960, H=540):
    cx, cy, s = cam
    if abs(s - 1.0) < 1e-9:
        x0, y0 = int(round(cx - W / 2)), int(round(cy - H / 2))
        padded = np.full((H, W), PAPER, np.uint8)
        sx0, sy0 = max(0, x0), max(0, y0)
        sx1, sy1 = min(PAGE_W, x0 + W), min(PAGE_H, y0 + H)
        if sx1 > sx0 and sy1 > sy0:
            padded[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = page[sy0:sy1, sx0:sx1]
        return padded
    big = np.full((PAGE_H + 2 * PAD, PAGE_W + 2 * PAD), PAPER, np.uint8)
    big[PAD:PAD + PAGE_H, PAD:PAD + PAGE_W] = page
    w, h = W / s, H / s
    box = (cx - w / 2 + PAD, cy - h / 2 + PAD, cx + w / 2 + PAD, cy + h / 2 + PAD)
    return np.asarray(Image.fromarray(big).resize((W, H), Image.BOX, box=box))


def frame_L(k):
    if k >= BLACK_K0:
        return np.full((540, 960), INK_BLACK, np.uint8)
    return shoot(page_at(k), camera(k))


# ---------------------------------------------------------------- film
film = Film(SLUG, seconds=66.0, boil=0, wobble=0.0, seed=17)
film.poster_at = 47.5   # B3 hold: AND LOOK - STILL SEALED


@film.picture
def picture(t, ink):
    k = int(round(t * FPS))
    ink.paper(color=(PAPER, PAPER, PAPER), grain=False)
    ink.img = Image.fromarray(frame_L(k)).convert("RGB")
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


SOUND = {}


@film.sound
def sound(mix):
    import cues
    S = cues.build(s1=dict(stamp_t0=STAMP_T0, header_t0=HEADER_T0))
    SOUND["checks"] = S["checks"]
    SOUND["cues"] = S["cues"]
    assert S["checks"]["all_pass"], S["checks"]
    pen = S["pen"].copy()
    # footer, written in S5 at page scale: one real grain per stroke from the same bank, far and soft
    bank = cues.Bank()
    rs = np.random.RandomState(58)
    scf = FOOTER_FRAMES / BJ["page_lettering"]["footer"]["natural_write_frames"]
    foot = []
    for st in BJ["page_lettering"]["footer"]["strokes"]:
        t0 = (FOOTER_K0 + st["t0_f"] * scf) / FPS
        t1 = (FOOTER_K0 + st["t1_f"] * scf) / FPS
        sig, _ = bank.grain(max(0.035, t1 - t0), rs)
        sig = cues.lowpass(sig, 6000) * 0.32
        i = int(round(t0 * cues.SR))
        j = min(len(pen), i + len(sig))
        pen[i:j] += sig[: j - i]
        foot.append(dict(src="S5:footer", idx=st["idx"], t=round(t0, 4), ref_frame=int(math.floor(t0 * FPS + 1e-9))))
    SOUND["footer_cues"] = foot
    mix.add(S["ambience"], 0.0, pan=-0.1)
    mix.add(pen, 0.0, pan=0.08)


if __name__ == "__main__":
    write_page_files()
    if len(sys.argv) > 1 and sys.argv[1] == "--page":
        print("page ->", PAGE_OUT)
        sys.exit(0)
    film.render()
    if SOUND:
        json.dump(dict(checks=SOUND["checks"], footer_cues=SOUND["footer_cues"],
                       s1=dict(stamp_t0=STAMP_T0, header_t0=HEADER_T0, stamp_frames=[STAMP_K0 + i * STAMP_EVERY for i in range(7)])),
                  open(SWARM / "deliverables" / "film-sound-checks.json", "w"), indent=1)
