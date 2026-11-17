"""99 Ways to Tell a Story - Template: the two DERIVATIVE pages of baseline b1 (VARIANT-BUILDERS unit).

Each changes exactly one dimension of b1 (plan.md section 3, central operation derive(b1, op)):
  D1 'Compressed'        op = panel_count/time 8 -> 2   assets/pages/99-ways-template-compressed.png
  D2 'From the platform' op = viewpoint (the VISITOR's side of the window), 4 panels
                                                         assets/pages/99-ways-template-platform.png
Pinned: the same FORAGED pieces at revision b1 (page-cartoonist pieces: Rothstein 1937 clerk/office/cupboard set,
Rothstein clock, ANRC key; plus the Bubley 1943 visitor re-cut by GrabCut from the LoC master, cut_visitor.py),
the same HANDMADE lettering (page/glyphs.json strokes, + glyphs_extra.json '2','F' in the same pen), the same 1934
sheet ground, borders, cut-paper balloons, scissor margins and paper shadow, and the same tonal rule (one levels
curve per source photograph; no filters). Outcome unchanged: key stays on its hook, SERVICE door stays closed.
The through-glass views of D2 are optical composites of real plates: interior x transmission + the window's own
pixels (reflection / display) x (1 - transmission); the neon sign and blind hanging inside the glass stay in front.
Writes the two pages, variants/rest/<D1|D2>/<panel>/ layers (+ layers.json), variants/d1_panels.json, d2_panels.json,
variants/variant_checks.json.  Run: python3 -I build_variants.py"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "page"))
import build_page as B          # noqa: E402  (baseline b1 rig, pieces, balloons, memo, sign-card, door/key)
import penlib as PL             # noqa: E402
from penlib import *            # noqa: E402,F401

PL.GLYPHS.update({k: (v[0], [tuple(st) for st in v[1]]) for k, v in json.load(open(HERE / "glyphs_extra.json"))["glyphs"].items()})

ROOTD = B.ROOT
VB = ROOTD / "films" / "sources" / "99-ways-template" / "variant-builders"
OUT_D1 = ROOTD / "assets" / "pages" / "99-ways-template-compressed.png"
OUT_D2 = ROOTD / "assets" / "pages" / "99-ways-template-platform.png"
REST = HERE / "rest"

BUB_LEVELS = (16, 212, 0.85)          # Bubley 1943 (8d33109u master): one curve for every crop of it
BUB = levels(cv2.imread(str(VB / "loc" / "8d33109u.png"), cv2.IMREAD_GRAYSCALE), *BUB_LEVELS)
VIS_IM = cv2.imread(str(VB / "pieces" / "bubley.visitor.hi.png"), cv2.IMREAD_UNCHANGED)
VIS = json.load(open(VB / "pieces" / "bubley.visitor.hi.json"))
VIS_G = levels(VIS_IM[..., 0], *BUB_LEVELS)
VIS_A = VIS_IM[..., 3].copy()
VIS_O = VIS["bbox_src"][:2]
VIS_HIP = VIS["pivots_local"]["hip"]

BUB_CLEAN, BUB_HOLE = None, None
W2P, MIR, view_plate = B.W2P, B.MIR, B.view_plate
ROOT_, CX = B.ROOT_, B.CX


# ------------------------------------------------------------------ handmade label strip (small caps in the page hand)
def small_caps_mask(text, cap_big, cap_small, seed):
    """Small caps: the first letter of each word (and digits) at cap_big, the rest as capitals at cap_small, one baseline."""
    pieces, x = [], 0.0
    first = True
    for i, ch in enumerate(text):
        if ch == " ":
            x += cap_big * 0.42
            first = True
            continue
        big = (first and ch.isupper()) or ch.isdigit()
        cap = cap_big if big else cap_small
        c = ch.upper() if ch.isalpha() else ch
        m = letter_lines([c], cap, seed + i)
        cols = np.nonzero(m.max(0) > 0)[0]
        if len(cols) == 0:
            continue
        m = m[:, cols[0]:cols[-1] + 1]
        base = cap * 1.15
        pieces.append((m, x, base))
        x += m.shape[1] + cap_big * 0.09
        first = False
    W = int(x + 4)
    asc = max(b for _, _, b in pieces)
    H = int(asc + max(m.shape[0] - b for m, _, b in pieces) + 4)
    out = np.zeros((H, W), np.uint8)
    for m, px, b in pieces:
        oy = int(round(asc - b))
        h, w = m.shape
        out[oy:oy + h, int(px):int(px) + w] = np.maximum(out[oy:oy + h, int(px):int(px) + w], m)
    return out, asc


def label_strip(pg, text, y0, seed):
    """HANDMADE: a cut-paper label strip laid on the sheet at the head of the page, lettered in the page hand."""
    lm, asc = small_caps_mask(text, 60, 44, seed)
    h, w = lm.shape
    x0 = 150 + 10
    pad_x, pad_y = 34, 22
    box = np.zeros(pg.shape[:2], np.uint8)
    pts = np.array([(x0, y0 + 3), (x0 + w + 2 * pad_x, y0), (x0 + w + 2 * pad_x + 2, y0 + h + 2 * pad_y), (x0 - 1, y0 + h + 2 * pad_y + 2)])
    cv2.fillPoly(box, [np.int32(pts * 4)], 255, cv2.LINE_AA, shift=2)
    shadow_onto(pg, box)
    pa = box.astype(np.float32)[..., None] / 255
    pg[:] = pg * (1 - pa) + BALLOON * pa
    ink = np.zeros(pg.shape[:2], np.uint8)
    ink[y0 + pad_y:y0 + pad_y + h, x0 + pad_x:x0 + pad_x + w] = lm
    ink_onto(pg, ink)
    return [int(x0), int(y0), int(x0 + w + 2 * pad_x), int(y0 + h + 2 * pad_y)]


# ------------------------------------------------------------------ through-glass composite (D2)
def glass_mask(shape, poly):
    return B.fillmask(shape, poly).astype(np.float32) / 255


def through_glass(P, interior, gmask, plate_view, transmission_top=0.80, transmission_bottom=0.52, decal=None):
    """interior seen through the window: interior*t + window's own pixels*(1-t) inside the glass; t falls toward the
    display shelf at the bottom of the pane (the window's plants stand in front). Decals (neon sign, blind) re-laid on top."""
    h, w = gmask.shape
    ys = np.nonzero(gmask.max(1) > 0)[0]
    t = np.ones((h, w), np.float32) * transmission_top
    if len(ys):
        yy = np.clip((np.arange(h) - ys[0]) / max(1, ys[-1] - ys[0]), 0, 1)
        t = (transmission_top + (transmission_bottom - transmission_top) * yy ** 1.6)[:, None] * np.ones((1, w), np.float32)
    P.over("interior_through_glass", interior, gmask * t, {"through_glass": f"interior x t (t {transmission_top}->{transmission_bottom} down the pane) + window pixels x (1-t)"})
    if decal is not None and decal.max() > 0:
        P.over("glass_decals", plate_view, decal, {"through_glass": "neon sign / blind hanging inside the glass, re-laid in front"})


def neon_decal(plate_view, poly_px):
    """Bright tubes and the card of the neon sign (plate's own pixels) within the sign's box."""
    h, w = plate_view.shape[:2]
    box = B.fillmask((h, w), poly_px)
    g = plate_view[..., 0]
    m = ((g > 175) & (box > 0)).astype(np.uint8) * 255
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    return cv2.GaussianBlur(m, (0, 0), 1.2).astype(np.float32) / 255


def lay_visitor(P, M, name="visitor", margin=8):
    P.piece(name, VIS_G, VIS_A, M @ T(*VIS_O), margin=margin, meta={"piece": "bubley.visitor.hi"})


def bp(Mplate, p):            # Bubley master px -> panel px
    return apply(Mplate, p)


# ------------------------------------------------------------------ D1: Compressed (2 panels)
D1_PANELS = {"C1": (150, 330, 2400, 1700), "C2": (150, 1770, 2400, 3150)}
D2_PANELS = {"V1": (150, 330, 2400, 1250), "V2": (150, 1320, 1245, 2160), "V3": (1305, 1320, 2400, 2160), "V4": (150, 2230, 2400, 3150)}
SPEECH, FK = {}, {}


def size(PANELS, k):
    x0, y0, x1, y1 = PANELS[k]
    return x1 - x0, y1 - y0


def C1():
    w, h = size(D1_PANELS, "C1")
    V = (0.516, 0, 380)
    P = B.Panel("C1", view_plate(B.OFFICE, *V, w, h))
    Mw = W2P(*V)
    # the office clock on the wall above the cabinet, its own hands set to 4:10 (same pieces as P5)
    lay_clock(P, apply(Mw, (2700, 600)), 0.933 * V[0])
    lift = T(900, 40) @ about(ROOT_, R(-4))              # P2's rising pose, nearer his chair: up and leaving right
    Ms = B.lay_clerk(P, Mw @ lift, dict(B.POSE_ARRIVE, head=3.0), rec=FK)
    # foreground: the desk top of the same photograph laid back over his cut waist (he stands behind the desk), as P3
    desk = np.zeros((h, w), np.uint8)
    dp = [apply(Mw, p) for p in [(2560, 2640), (3000, 2610), (3900, 2600), (4360, 2620), (4360, 3200), (2560, 3200)]]
    cv2.fillPoly(desk, [np.int32(dp)], 255, cv2.LINE_AA)
    P.shadow("desk_front", desk)
    P.over("desk_front", view_plate(B.OFFICE, *V, w, h), desk.astype(np.float32) / 255)
    B.memo_slip(P, apply(Mw, (2740, 2790)), 232 * V[0] / 0.423, 5)
    mouth = apply(Ms["clerk.head"], (2992, 2018))
    b1 = B.balloon(P, "b_what_time", ["What time", "is it?"], 70, (440, 205), (-30, 430), 121, tail_w=0.26, bend=0.12)
    b1.update(speaker="VISITOR", tail_target="off-panel left, through the TICKET OFFICE window (the platform)")
    b2 = B.balloon(P, "b_ten_past", ["Ten past", "four!"], 70, (1520, 640), (mouth[0] - 40, mouth[1] + 6), 133, tail_w=0.22, bend=-0.10)
    b2.update(speaker="CLERK", tail_target="clerk's mouth")
    SPEECH["C1"] = [b1, b2]
    return P


def lay_clock(P, arbor_px, scale):
    cc = B.PC["clock.case"]
    arb = cc["piv"]["arbor"]
    Mclk = T(*arbor_px) @ S(scale) @ T(-arb[0], -arb[1])
    P.piece("clock.case", cc["g"], cc["a"], Mclk @ T(*cc["o"]), margin=7, meta={"piece": "clock.case"})
    h, w = P.c.shape[:2]
    for n, ang in [("clock.hour", 4 * 30 + 10 * 0.5), ("clock.minute", 10 * 6)]:
        pc = B.PC[n]
        rot = ang - B.man["pieces"][n]["source_angle_deg"]
        Mh = Mclk @ about(arb, R(rot)) @ T(*pc["o"])
        hg = cv2.warpAffine(pc["g"], Mh[:2], (w, h), flags=cv2.INTER_CUBIC)
        ha = cv2.warpAffine(pc["a"], Mh[:2], (w, h), flags=cv2.INTER_LINEAR).astype(np.float32) / 255
        P.over(n, np.repeat(hg[..., None], 3, 2), ha, {"piece": n, "set_to_deg": ang, "matrix": Mh.round(6).tolist()})


def C2():
    w, h = size(D1_PANELS, "C2")
    V = (0.80, 1550, 500)
    P = B.Panel("C2", view_plate(B.SETP, *V, w, h))
    Mw = W2P(*V)
    B.sign_card(P, apply(Mw, (4110, 900)), 0.80 * 330, -2)
    B.lay_door_key(P, *V, swing=0.34, rec=FK)
    Mc = T(760 + (2790 - 1550) * 0.8, 1010 + (600 - 500) * 0.8 + 330) @ S(0.74) @ T(-ROOT_[0], -ROOT_[1]) @ MIR()
    Ms = B.lay_clerk(P, Mc, B.POSE_CHIN, rec=FK)
    mouth = apply(Ms["clerk.head"], (2992, 2018))
    b1 = B.balloon(P, "b_thanks", ["Thanks!"], 50, (330, 150), (-30, 250), 161, tail_w=0.30, bend=0.10)
    b1.update(speaker="VISITOR", tail_target="off-panel left (the platform; she is leaving)")
    b2 = B.balloon(P, "b_forgot", ["What the hell", "was I looking", "for, anyway?"], 68, (1180, 260), (mouth[0] - 6, mouth[1] - 4), 183, tail_w=0.22, bend=0.08)
    b2.update(speaker="CLERK", tail_target="clerk's mouth")
    SPEECH["C2"] = [b1, b2]
    return P


# ------------------------------------------------------------------ D2: From the platform (4 panels)
K1 = (2250 / 4140, 320, 500)           # V1: the station front, Bubley master px -> panel px
K2 = (1095 / 1520, 1000, 1050)         # V2: closer on the window
K3 = (1095 / 1300, 1150, 1180)         # V3: closer still, on the glass
# V4 uses K1 (same camera as V1)          # V4: the window again, she walks off past the left edge
GLASS = [(1032, 1236), (3046, 1236), (3046, 2212), (1032, 2212)]          # clear pane below the blind (master px)
SIGN = [(1560, 1060), (2560, 1060), (2560, 1520), (1560, 1520)]           # neon sign + its card (master px)


def clean_plate():
    """The station front with the visitor lifted off it (for V4, same camera as V1). Her hole (alpha dilated 24 px) is
    filled from the same photograph: the window's bottom rail row-wise from its left, everything else column-wise from
    just above her head, reflected (vertical boards, glass); the glass part is then behind the through-glass composite."""
    img = BUB.copy()
    hole = np.zeros(img.shape, np.uint8)
    x0, y0 = VIS_O
    hole[y0:y0 + VIS_A.shape[0], x0:x0 + VIS_A.shape[1]] = VIS_A
    hole = cv2.dilate((hole > 20).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (49, 49)))
    ys, xs = np.nonzero(hole)
    top = int(ys.min()) - 2
    for x in np.unique(xs):
        col = np.nonzero(hole[:, x])[0]
        for y in col:
            if 2190 <= y <= 2312 and x < 3050:
                img[y, x] = img[y, 2470 - ((x - 2470) % 60)]
            else:
                d = (y - top) % 360
                img[y, x] = img[top - (d if d < 180 else 360 - d), x]
    feather = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), 3)
    return BUB * (1 - feather) + img * feather, hole


def V1():
    w, h = size(D2_PANELS, "V1")
    plate = view_plate(BUB, *K1, w, h)
    P = B.Panel("V1", plate)
    Mp = W2P(*K1)
    # far back through the station window: the office wall and the closed cupboards with the SERVICE card
    Vi = (0.30, -577, -633)
    I = B.Panel("interior", view_plate(B.OFFICE, *Vi, w, h))
    B.sign_card(I, apply(W2P(*Vi), (4110, 900)), Vi[0] * 330, -2)
    gm = glass_mask((h, w), [bp(Mp, p) for p in GLASS])
    through_glass(P, I.c, gm, plate, transmission_top=0.62, transmission_bottom=0.40, decal=neon_decal(plate, [bp(Mp, p) for p in SIGN]))
    lay_visitor(P, Mp)                   # she is a cut piece laid back on her own place at the window
    SPEECH["V1"] = []
    return P, I


def interior_office(w, h, V, clerk=None, memo=True, clock=None):
    I = B.Panel("interior", view_plate(B.OFFICE, *V, w, h))
    Mw = W2P(*V)
    Ms = None
    if clock:
        lay_clock(I, apply(Mw, clock[0]), clock[1] * V[0])
    if memo:
        B.memo_slip(I, apply(Mw, (2740, 2790)), 232 * V[0] / 0.423, 5)
    if clerk is not None:
        Ms = B.lay_clerk(I, Mw @ clerk[0], clerk[1])
    return I, Ms


def V2():
    w, h = size(D2_PANELS, "V2")
    plate = view_plate(BUB, *K2, w, h)
    P = B.Panel("V2", plate)
    Mp = W2P(*K2)
    # through the glass: the office, its desk already empty (E1 happened out of view); memo too small to read
    I, _ = interior_office(w, h, (0.2854, 523, 220))
    gm = glass_mask((h, w), [bp(Mp, p) for p in GLASS])
    through_glass(P, I.c, gm, plate, decal=neon_decal(plate, [bp(Mp, p) for p in SIGN]))
    b = B.balloon(P, "b_what_time", ["What time", "is it?"], 66, (700, 430), (w * 0.52, h + 30), 221, tail_w=0.26, bend=0.10)
    b.update(speaker="VISITOR", tail_target="off-panel bottom: the viewpoint is hers")
    SPEECH["V2"] = [b]
    return P, I


def V3():
    w, h = size(D2_PANELS, "V3")
    plate = view_plate(BUB, *K3, w, h)
    P = B.Panel("V3", plate)
    Mp = W2P(*K3)
    # the clerk passing behind the glass, his head turned on the collar toward her (head hinge -6 deg)
    lift = T(150, -120)
    Vi = (0.62, 2237, 863)
    I, Ms = interior_office(w, h, Vi, clerk=(lift, dict(B.POSE_ARRIVE, head=-6.0)), memo=False, clock=((2560, 1650), 0.70))
    gm = glass_mask((h, w), [bp(Mp, p) for p in GLASS])
    through_glass(P, I.c, gm, plate, transmission_top=0.84, transmission_bottom=0.62, decal=neon_decal(plate, [bp(Mp, p) for p in SIGN]))
    mouth = apply(Ms["clerk.head"], (2992, 2018))
    b1 = B.balloon(P, "b_ten_past", ["Ten past", "four!"], 66, (300, 175), (mouth[0] - 40, mouth[1] + 4), 233, tail_w=0.22, bend=-0.08)
    b1.update(speaker="CLERK", tail_target="clerk's mouth, through the glass")
    b2 = B.balloon(P, "b_thanks", ["Thanks!"], 62, (780, 700), (w * 0.60, h + 30), 261, tail_w=0.30, bend=0.10)
    b2.update(speaker="VISITOR", tail_target="off-panel bottom: hers")
    SPEECH["V3"] = [b1, b2]
    FK["V3"] = {"mouth_px": list(map(float, mouth))}
    return P, I


def V4():
    w, h = size(D2_PANELS, "V4")
    plate = view_plate(BUB_CLEAN, *K1, w, h)          # the same camera as V1: Madden's objective repeat
    P = B.Panel("V4", plate)
    Mp = W2P(*K1)
    # far back through the glass: the cupboard open on its jamb, the clerk before it, pencil at his temple
    # (scratching his head = the Rothstein source pose); the key a small glint on its hook; SERVICE door still closed.
    Vi = (0.30, -577, -633)
    I = B.Panel("interior", view_plate(B.SETP, *Vi, w, h))
    Mw = W2P(*Vi)
    B.sign_card(I, apply(Mw, (4110, 900)), Vi[0] * 330, -2)
    B.lay_door_key(I, *Vi, swing=0.34)
    kc = 0.74 * Vi[0] / 0.80
    Mc = T(*apply(Mw, (3740, 1862))) @ S(kc) @ T(-ROOT_[0], -ROOT_[1]) @ MIR()
    B.lay_clerk(I, Mc, B.POSE_SOURCE)
    gm = glass_mask((h, w), [bp(Mp, p) for p in GLASS])
    through_glass(P, I.c, gm, plate, transmission_top=0.62, transmission_bottom=0.40, decal=neon_decal(plate, [bp(Mp, p) for p in SIGN]))
    # she walks off past the left edge: the same cut piece, moved along the station front, pitched into the step
    Mv = Mp @ T(-2372, 10) @ T(*VIS_O) @ about(VIS_HIP, R(-5)) @ T(-VIS_O[0], -VIS_O[1])
    lay_visitor(P, Mv)
    SPEECH["V4"] = []
    return P, I


# ------------------------------------------------------------------ assemble, record
def save_layers(P, page_key, panels, border_crop, extra=None):
    d = REST / page_key / P.key
    d.mkdir(parents=True, exist_ok=True)
    for f in d.glob("*.png"):
        f.unlink()
    rows = []
    for i, (name, rgba, meta) in enumerate(P.layers + [("border", np.dstack([np.broadcast_to(INK, P.c.shape), border_crop]), {})]):
        fn = f"{i:02d}_{name}.png"
        Image.fromarray(np.clip(np.round(rgba), 0, 255).astype(np.uint8), "RGBA").save(d / fn, compress_level=3)
        rows.append({"order": i, "file": fn, "name": name, **{k: v for k, v in meta.items() if k in ("piece", "matrix", "pose", "jamb_top_px", "jamb_bottom_px", "swing_scaleX", "hook_px", "set_to_deg", "through_glass")}})
    json.dump({"panel": P.key, "page": page_key, "bounds_page_px": panels[P.key], "composite": "over, in order, starting from 00_bg (opaque)",
               "layers": rows, **(extra or {})}, open(d / "layers.json", "w"), indent=1)


def recompose(d):
    L = json.load(open(d / "layers.json"))["layers"]
    c = None
    for r in L:
        im = np.asarray(Image.open(d / r["file"])).astype(np.float32)
        if c is None:
            c = im[..., :3]
            continue
        a = im[..., 3:4] / 255
        c = c * (1 - a) + im[..., :3] * a
    return c


def build_page(page_key, panels, builders, label, out_path, seed):
    pg = sheet()
    lab_box = label_strip(pg, label, 168, seed)
    built, interiors = {}, {}
    for key, fn in builders:
        r = fn()
        P, I = (r if isinstance(r, tuple) else (r, None))
        built[key] = P
        if I is not None:
            interiors[key] = I
        x0, y0, x1, y1 = panels[key]
        pg[y0:y1, x0:x1] = P.c
    bm = border_mask((PAGE_H, PAGE_W), [panels[k] for k in panels], 9, seed + 900)
    ink_onto(pg, bm)
    out = np.clip(np.round(pg), 0, 255).astype(np.uint8)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out).save(out_path, dpi=(300, 300))
    checks = {}
    for key, P in built.items():
        x0, y0, x1, y1 = panels[key]
        save_layers(P, page_key, panels, bm[y0:y1, x0:x1])
        if key in interiors:      # the interior seen through the glass, kept as its own layered panel for the film
            I = interiors[key]
            I.key = key + "_interior"
            save_layers(I, page_key, {I.key: panels[key]}, np.zeros((y1 - y0, x1 - x0), np.uint8),
                        {"note": "the room behind the glass; enters the panel only through 'interior_through_glass'"})
        rc = recompose(REST / page_key / key)
        diff = np.abs(np.clip(np.round(rc), 0, 255) - out[y0:y1, x0:x1].astype(np.float32))
        checks[key] = {"rest_layers_vs_page_mean_abs": round(float(diff.mean()), 3), "max_abs": float(diff.max())}
    tone = {"page": B.tone(out), "panels_only": B.tone(np.concatenate([out[b[1]:b[3], b[0]:b[2]].reshape(-1, 3) for b in panels.values()]))}
    return out, checks, tone, lab_box


def main():
    global BUB_CLEAN, BUB_HOLE
    BUB_CLEAN, BUB_HOLE = clean_plate()
    cv2.imwrite(str(VB / "pieces" / "bubley.front.clean_hole_mask.png"), BUB_HOLE * 255)
    d1, c1, t1, lb1 = build_page("D1", D1_PANELS, [("C1", C1), ("C2", C2)], "Derivative 1 - Compressed (2 panels)", OUT_D1, 4100)
    d2, c2, t2, lb2 = build_page("D2", D2_PANELS, [("V1", V1), ("V2", V2), ("V3", V3), ("V4", V4)], "Derivative 2 - From the platform", OUT_D2, 4200)
    recs = {}
    for pk, panels, lb, route, op in [("D1", D1_PANELS, lb1, ["C1", "C2"], "panel_count/time 8->2"),
                                      ("D2", D2_PANELS, lb2, ["V1", "V2", "V3", "V4"], "viewpoint: the VISITOR's side of the ticket window")]:
        recs[pk] = {"slug": "99-ways-template", "derived_from": "b1", "operator": op,
                    "page": str((OUT_D1 if pk == "D1" else OUT_D2).relative_to(ROOTD)), "page_px": [PAGE_W, PAGE_H], "dpi": 300,
                    "label_box_px": lb, "route": route, "balloon_order": "top-left first within a panel",
                    "panels": [{"id": k, "bounds_px": list(panels[k]), "speech": SPEECH.get(k, []),
                                "rest_layers": str((REST / pk / k / "layers.json").relative_to(ROOTD))} for k in route]}
    json.dump(recs["D1"], open(HERE / "d1_panels.json", "w"), indent=1)
    json.dump(recs["D2"], open(HERE / "d2_panels.json", "w"), indent=1)
    json.dump({"D1": {"tone": t1, "rest_identity": c1}, "D2": {"tone": t2, "rest_identity": c2}, "fk": FK,
               "levels": {"bubley_8d33109u": BUB_LEVELS}}, open(HERE / "variant_checks.json", "w"), indent=1, default=float)
    print(json.dumps(t1), json.dumps(c1))
    print(json.dumps(t2), json.dumps(c2))


if __name__ == "__main__":
    main()
