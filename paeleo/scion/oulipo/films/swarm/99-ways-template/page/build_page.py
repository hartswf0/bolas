"""99 Ways to Tell a Story - Template, baseline b1: the HANDMADE photo-comic page (Direction 2, Photo-Fumetti Cutout).
FORAGED pieces (cut_pieces.py: Rothstein 1937 Randolph agent + clock, Bubley 1943 visitor, ANRC 1922 key) laid as
cut paper with white scissor margins and one soft down-right paper shadow on the real 1934 LoC sheet; hand-ruled
tremored borders; cut-paper balloons lettered from the HANDMADE glyph-stroke table glyphs.json; handmade memo slip,
SERVICE sign-card, hook and key tag. Tone by plate choice, crop and one levels curve per source photo only.
FK (SCION #32): source-coord joint transforms  clerk: torso -> collar -> head; torso -> elbow -> forearm -> grip -> pencil;
set -> jamb -> door -> hook -> key -> tag; clock -> arbor -> hour/minute hands.
Writes assets/pages/99-ways-template.png (2550x3300, 300 dpi), page/rest/P1..P8 layers, panels.json.
Run: python3 -I build_page.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from penlib import *  # noqa

PAGE_OUT = ROOT / "assets" / "pages" / "99-ways-template.png"
REST = BUILD / "rest"
man = json.load(open(PIECES / "manifest.json"))
INK3 = INK

PANELS = {
    "P1": (150, 150, 890, 1090), "P2": (950, 150, 1610, 1090), "P3": (1670, 150, 2400, 1090),
    "P4": (150, 1160, 710, 2100), "P5": (770, 1160, 1740, 2100), "P6": (1800, 1160, 2400, 2100),
    "P7": (150, 2170, 1150, 3150), "P8": (1210, 2170, 2400, 3150),
}


def load(name):
    im = cv2.imread(str(PIECES / f"{name}.png"), cv2.IMREAD_UNCHANGED)
    p = man["pieces"][name]
    return dict(g=im[..., 0].astype(np.float32), a=im[..., 3].copy(), o=p["bbox_src"][:2],
                piv={k: (v[0] + p["bbox_src"][0], v[1] + p["bbox_src"][1]) for k, v in p["pivots_local"].items()})


PC = {n: load(n) for n in ["clerk.torso", "clerk.head", "clerk.forearm", "clerk.pencil", "clock.case", "clock.hour",
                           "clock.minute", "visitor", "key"]}
PC["key"]["o"] = (0, 0)
PC["key"]["piv"] = {"ring_top": tuple(man["pieces"]["key"]["pivots_local"]["ring_top"])}
# r1 (editor): the clerk-removed plates with the head ghost, arm residue and desk smear repaired from the same
# photograph (films/swarm/99-ways-template/editor/plate_repair.py; same-column/plank-period copies + interpolation)
EDIT = SRC / "editor"
OFFICE = cv2.imread(str(EDIT / "office.plate.r1.png"), cv2.IMREAD_GRAYSCALE).astype(np.float32)
SETP = cv2.imread(str(EDIT / "set.plate.r1.png"), cv2.IMREAD_GRAYSCALE).astype(np.float32)
DOOR = cv2.imread(str(PIECES / "cupboard.door.png"), cv2.IMREAD_GRAYSCALE).astype(np.float32)
DOOR_BOX = man["set_plate"]["opening_src"]
S3 = levels(cv2.imread(str(TEST / "rothstein_master_s3.png"), cv2.IMREAD_GRAYSCALE), *man["levels"]["rothstein_8b16710"])

CP = PC["clerk.torso"]["piv"]
COLLAR, ELBOW, ROOT_ = CP["collar"], CP["elbow"], CP["root"]
GRIP, TIP = PC["clerk.pencil"]["piv"]["grip"], PC["clerk.pencil"]["piv"]["tip"]
CHIN = PC["clerk.head"]["piv"]["chin"]
CX = 2990.0                      # vertical axis the clerk is mirrored about (through his head)


# ------------------------------------------------------------------ layer recorder (rest layers == page)
class Panel:
    def __init__(self, key, bg):
        self.key = key
        self.c = bg.astype(np.float32).copy()
        self.layers = [("bg", np.dstack([np.clip(bg, 0, 255), np.full(bg.shape[:2], 255.0)]), {})]

    def over(self, name, rgb, a, meta=None):
        """canvas = canvas*(1-a) + rgb*a ; a in 0..1 (h,w)."""
        a = np.clip(a, 0, 1).astype(np.float32)
        if a.max() <= 0:
            return
        rgb = np.broadcast_to(rgb, self.c.shape).astype(np.float32)
        a8 = np.round(a * 255) / 255
        self.c = self.c * (1 - a8[..., None]) + rgb * a8[..., None]
        self.layers.append((name, np.dstack([rgb, a8 * 255]), meta or {}))

    def shadow(self, name, paper_mask, off=6, blur=4, opacity=0.35):
        sh = np.zeros_like(paper_mask)
        h, w = sh.shape
        sh[off:, off:] = paper_mask[:h - off, :w - off]
        sh = cv2.GaussianBlur(sh, (0, 0), blur).astype(np.float32) / 255.0 * opacity
        self.over(name + ".shadow", np.zeros(3, np.float32), sh)

    def piece(self, name, g, a, M, margin=8, shade=1.0, glass=None, meta=None):
        h, w = self.c.shape[:2]
        gw = cv2.warpPerspective(g, M, (w, h), flags=cv2.INTER_CUBIC, borderValue=0)
        aw = cv2.warpPerspective(a, M, (w, h), flags=cv2.INTER_LINEAR, borderValue=0)
        ab = (aw > 127).astype(np.uint8) * 255
        af = aw.astype(np.float32) / 255
        pa = np.zeros_like(af)
        if margin:
            pm = scissor(ab, margin)
            self.shadow(name, pm)
            pa = pm.astype(np.float32) / 255
        else:
            self.shadow(name, ab)
        A = 1 - (1 - pa) * (1 - af)
        col = (PAPER_CUT[None, None] * (pa * (1 - af))[..., None] + np.clip(gw * shade, 0, 255)[..., None] * af[..., None]) / np.maximum(A, 1e-6)[..., None]
        self.over(name, col, A, dict(meta or {}, matrix=np.asarray(M).round(6).tolist()))

    def ink(self, name, m, color=INK3):
        self.over(name, color, m.astype(np.float32) / 255)

    def paper(self, name, m, color, shadow=True):
        if shadow:
            self.shadow(name, m)
        self.over(name, np.array(color, np.float32), m.astype(np.float32) / 255)


def W2P(k, x0, y0):
    return S(k) @ T(-x0, -y0)


def MIR(cx=CX):
    return T(cx, 0) @ S(-1, 1) @ T(-cx, 0)


def view_plate(img, k, x0, y0, w, h):
    M = W2P(k, x0, y0)[:2]
    g = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return np.repeat(g[..., None], 3, 2)


def psize(key):
    x0, y0, x1, y1 = PANELS[key]
    return x1 - x0, y1 - y0


# ------------------------------------------------------------------ the clerk rig
def clerk_mats(Mw, pose):
    """Mw: source(S3)->panel for the whole clerk. Joint transforms act in source coords."""
    Jh = about(COLLAR, R(pose.get("head", 0.0)))
    Jf = about(ELBOW, R(pose.get("arm", 0.0)))
    Jp = Jf @ about(GRIP, R(pose.get("pencil", 0.0)))
    return {"clerk.torso": Mw, "clerk.head": Mw @ Jh, "clerk.forearm": Mw @ Jf, "clerk.pencil": Mw @ Jp}


def lay_clerk(P, Mw, pose, order=("clerk.torso", "clerk.head", "clerk.forearm", "clerk.pencil"), rec=None):
    Ms = clerk_mats(Mw, pose)
    for n in order:
        pc = PC[n]
        P.piece(n, pc["g"], pc["a"], Ms[n] @ T(*pc["o"]), margin=8 if n != "clerk.pencil" else 2,
                meta={"piece": n, "pose": pose})
    if rec is not None:
        rec[P.key] = {"pose": pose, "Mw": np.asarray(Mw).round(6).tolist(),
                      "collar_px": list(apply(Ms["clerk.head"], COLLAR)), "elbow_px": list(apply(Ms["clerk.forearm"], ELBOW)),
                      "pencil_tip_px": list(apply(Ms["clerk.pencil"], TIP)), "chin_px": list(apply(Ms["clerk.head"], CHIN))}
    return Ms


def solve_pencil_to_chin(target, head=0.0):
    """FK solve (in source coords): forearm angle about the elbow + pencil angle about the grip so the tip meets the chin.
    The chin target rides on the head, so it is carried through the collar hinge first (head angle)."""
    target = apply(about(COLLAR, R(head)), target)
    L = np.linalg.norm(np.subtract(TIP, GRIP))
    best = None
    for a in np.arange(-40, 40.01, 0.25):
        g = apply(about(ELBOW, R(a)), GRIP)
        d = np.linalg.norm(g - target)
        if g[1] > target[1] + 20 and (best is None or abs(d - L) < best[0]):
            best = (abs(d - L), a, g)
    _, a, g = best
    t0 = apply(about(ELBOW, R(a)), TIP)
    ang0 = math.degrees(math.atan2(t0[1] - g[1], t0[0] - g[0]))
    ang1 = math.degrees(math.atan2(target[1] - g[1], target[0] - g[0]))
    return dict(arm=float(a), pencil=float(ang1 - ang0), head=float(head))


# r1: the point of the chin itself (source px, read off the master between the mouth and the jaw line), not the
# collar-height 'chin' pivot, which sits on his neck
CHIN_TOUCH = (3012.0, 2060.0)
H8 = -11.0                       # P8: head tipped up on the collar hinge (he faces right; the key is on his left)
H5 = -7.0                        # P5: head up toward the clock
POSE_CHIN = solve_pencil_to_chin(np.array(CHIN_TOUCH), head=H8)
POSE_SOURCE = dict(arm=0.0, pencil=0.0, head=0.0)                       # as photographed: pencil at the temple
POSE_ARRIVE = dict(arm=-34.0, pencil=24.0, head=0.0)                      # arm lowered across his front, walking
POSE_WALK = dict(arm=-52.0, pencil=30.0, head=-3.0)                       # r1 P3: arm swung down, pencil in hand


# ------------------------------------------------------------------ balloons, lettering, handmade print
def balloon(P, name, lines, cap, at, tip, seed, tail_w=0.30, bend=0.10):
    """at: balloon centre (panel px); tip: tail tip (panel px; may lie outside = off-panel source)."""
    b = balloon_piece(lines, cap, (tip[0] - at[0], tip[1] - at[1]), seed, tail_w=tail_w, bend=bend)
    h, w = P.c.shape[:2]
    cx, cy = b["center"]
    ox, oy = int(round(at[0] - cx)), int(round(at[1] - cy))

    def put(m):
        out = np.zeros((h, w), np.uint8)
        Hc, Wc = m.shape
        ys, xs = max(0, oy), max(0, ox)
        ye, xe = min(h, oy + Hc), min(w, ox + Wc)
        if ye > ys and xe > xs:
            out[ys:ye, xs:xe] = m[ys - oy:ye - oy, xs - ox:xe - ox]
        return out
    pm, im = put(b["paper"]), put(b["ink"])
    P.shadow(name, pm)
    P.over(name + ".paper", BALLOON, pm.astype(np.float32) / 255)
    P.ink(name + ".ink", im)
    ys, xs = np.nonzero(pm)
    return {"id": name, "box_panel_px": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
            "centre_panel_px": [float(at[0]), float(at[1])], "tail_tip_panel_px": [float(tip[0]), float(tip[1])],
            "tail_exits_panel": bool(tip[0] < 0 or tip[1] < 0 or tip[0] >= w or tip[1] >= h), "cap_px": cap, "lines": lines}


def lettering_onto(m, lines, cap, center, angle, seed, weight=0.13):
    lt = letter_lines(lines, cap, seed, weight=weight)
    Ml = cv2.getRotationMatrix2D((lt.shape[1] / 2, lt.shape[0] / 2), angle, 1.0)
    Ml[:, 2] += np.array(center) - np.array([lt.shape[1] / 2, lt.shape[0] / 2])
    return np.maximum(m, cv2.warpAffine(lt, Ml, (m.shape[1], m.shape[0])))


def rect_poly(c, w, h, ang, notch=0):
    p = np.array([(-w / 2 + notch, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2), (-w / 2, -h / 2 + notch)])
    a = math.radians(ang)
    return np.stack([p[:, 0] * math.cos(a) - p[:, 1] * math.sin(a), p[:, 0] * math.sin(a) + p[:, 1] * math.cos(a)], 1) + c


def fillmask(shape, pts):
    m = np.zeros(shape, np.uint8)
    cv2.fillPoly(m, [np.int32(np.array(pts) * 4)], 255, cv2.LINE_AA, shift=2)
    return m


def memo_slip(P, c, w, ang, seed=41):
    """HANDMADE: a railway memo form (ruled, printed heading) with a pencilled note, laid on the ledger."""
    shp = P.c.shape[:2]
    h = w * 0.56
    m = fillmask(shp, rect_poly(c, w, h, -ang))
    P.paper("memo", m, (246, 244, 236))
    ink = np.zeros(shp, np.uint8)
    a = math.radians(-ang)
    rot = lambda dx, dy: (c[0] + dx * math.cos(a) - dy * math.sin(a), c[1] + dx * math.sin(a) + dy * math.cos(a))
    for fy in (-0.335, -0.095, 0.175, 0.405):   # printed rules: writing lines of the form (pencil sits on them)
        brush_line(ink, [rot(-w * .44, fy * h), rot(w * .44, fy * h)], 1.6, seed + int(fy * 100), tremor=0.2)
    ink = lettering_onto(ink, ["MEMO  C.V.RY."], w * 0.050, rot(-w * 0.13, -h * 0.385), ang, seed + 1, weight=0.16)
    P.ink("memo.print", ink, np.array([70, 66, 62], np.float32))
    pen = np.zeros(shp, np.uint8)
    pen = lettering_onto(pen, ["4:15 — open"], w * 0.088, rot(-w * 0.05, -h * 0.12), ang, seed + 2, weight=0.15)
    pen = lettering_onto(pen, ["SERVICE door."], w * 0.088, rot(0, h * 0.15), ang, seed + 3, weight=0.15)
    pen = lettering_onto(pen, ["Key in cupboard."], w * 0.074, rot(0, h * 0.385), ang, seed + 4, weight=0.15)
    P.ink("memo.pencil", pen, np.array([40, 38, 38], np.float32))


def sign_card(P, c, w, ang, seed=77):
    """HANDMADE: the SERVICE sign-card tacked to the door (white card, lettered in the page hand, two tacks)."""
    shp = P.c.shape[:2]
    h = w * 0.36
    m = fillmask(shp, rect_poly(c, w, h, ang))
    P.paper("service_card", m, (243, 241, 234))
    ink = np.zeros(shp, np.uint8)
    ink = lettering_onto(ink, ["SERVICE"], h * 0.48, (c[0], c[1] + h * 0.02), -ang, seed, weight=0.17)
    a = math.radians(ang)
    for dx in (-w * 0.42, w * 0.42):
        p = (c[0] + dx * math.cos(a) - (-h * 0.3) * math.sin(a), c[1] + dx * math.sin(a) + (-h * 0.3) * math.cos(a))
        cv2.circle(ink, (int(p[0]), int(p[1])), max(2, int(w * 0.018)), 255, -1, cv2.LINE_AA)
    P.ink("service_card.ink", ink)


# ------------------------------------------------------------------ set pieces: door, hook, key, tag
def lay_door_key(P, k, x0, y0, swing=0.34, rec=None):
    """Door hinged on its left jamb, swung open toward us (we see its inner face, in shade). Key on a hook on it."""
    Wm = W2P(k, x0, y0)
    dh, dw = DOOR.shape
    jx, jy = DOOR_BOX[0], DOOR_BOX[1]
    jt, jb = apply(Wm, (jx, jy)), apply(Wm, (jx, jy + dh))
    ow = dw * k * swing
    grow = dh * k * 0.05
    src = np.float32([[0, 0], [dw, 0], [dw, dh], [0, dh]])
    dst = np.float32([[jt[0] - ow, jt[1] - grow], jt, jb, [jb[0] - ow, jb[1] + grow]])
    Md = cv2.getPerspectiveTransform(src, dst).astype(np.float64)
    P.piece("cupboard.door", DOOR[:, ::-1].copy(), np.full(DOOR.shape, 255, np.uint8), Md, margin=8, shade=0.78,
            meta={"piece": "cupboard.door", "jamb_top_px": list(jt), "jamb_bottom_px": list(jb), "swing_scaleX": swing})
    hp = apply(Md, (dw * 0.52, dh * 0.40))           # hook on the inner face of the door
    s = k / 0.8
    shp = P.c.shape[:2]
    hm = np.zeros(shp, np.uint8)
    cv2.rectangle(hm, (int(hp[0] - 6 * s), int(hp[1] - 22 * s)), (int(hp[0] + 6 * s), int(hp[1] - 4 * s)), 255, -1, cv2.LINE_AA)
    cv2.ellipse(hm, (int(hp[0]), int(hp[1] + 4 * s)), (int(11 * s), int(12 * s)), 0, 0, 200, 255, max(2, int(6 * s)), cv2.LINE_AA)
    P.paper("hook.paper", scissor(hm, 5), PAPER_CUT)
    P.ink("hook", hm)
    kp = PC["key"]
    ring = kp["piv"]["ring_top"]
    ks = 0.41 * k * 0.92
    Mk = T(hp[0], hp[1] + 8 * s) @ R(1.5) @ S(ks) @ T(-ring[0], -ring[1])
    tagc = apply(Mk, (ring[0] + 190, ring[1] + 420))
    ringc = apply(Mk, (ring[0] + 20, ring[1] + 60))
    tw, th = 168 * s, 58 * s
    tm = fillmask(shp, rect_poly(tagc, tw, th, 12, notch=10 * s))
    P.paper("tag", tm, (236, 232, 220))
    thread = np.zeros(shp, np.uint8)
    brush_line(thread, [ringc, tagc + np.array([-tw / 2 + 16 * s, -th / 2 + 10 * s])], max(2, 3 * s), 5, tremor=0.4)
    thread = lettering_onto(thread, ["SERVICE"], 22 * s, tagc + np.array([4 * s, 2 * s]), -12, 7, weight=0.15)
    P.ink("tag.ink", thread)
    P.piece("key", kp["g"], kp["a"], Mk, margin=6, meta={"piece": "key", "hook_px": list(hp)})
    if rec is not None:
        rec[P.key + ".key"] = {"hook_px": list(map(float, hp)), "ring_px": list(map(float, apply(Mk, ring))),
                               "offset": list(map(float, apply(Mk, ring) - hp))}


# ------------------------------------------------------------------ panels
FK = {}
SPEECH = {}

V1 = (0.423, 2100, 880)            # P1/P2 shared view of the desk (S3 px -> page px, origin)


def P1():
    w, h = psize("P1")
    P = Panel("P1", view_plate(OFFICE, *V1, w, h))
    Mw = W2P(*V1)
    lay_clerk(P, Mw, POSE_SOURCE, rec=FK)
    memo_slip(P, apply(Mw, (2740, 2790)), 232, 5)
    SPEECH["P1"] = []
    return P


P2_RIGHT = 1640.0
P3_VIEW = (0.49, 2790, 470)             # r1: the closed double cupboard, framed above the desk (no desk in frame)
P3_STEP = (640.0, -290.0, 4.0)          # r1: raised to standing height, pitched into the step


def P2():
    w, h = psize("P2")
    V = (V1[0], 2290, V1[2])
    P = Panel("P2", view_plate(OFFICE, *V, w, h))
    Mw = W2P(*V)
    memo_slip(P, apply(Mw, (2740, 2790)), 232, 5)
    # he has risen and is going out to the right: torso lifted with a lean, head lagging one pose (overlap)
    lift = T(P2_RIGHT, -170) @ about(ROOT_, R(-5))      # r1: only his shoulder is left at the edge: the desk is empty
    lay_clerk(P, Mw @ lift, dict(POSE_ARRIVE, head=3.0), rec=FK)
    SPEECH["P2"] = []
    return P


def P3():
    """r1: he walks past the closed SERVICE door. Camera on the double cupboard of the same office, above the desk;
    the SERVICE card on the right leaf's upper panel, clear of the lamp cord; he is cut by the panel's lower edge
    at the waist (standing height), pitched into the step, arm swung down."""
    w, h = psize("P3")
    V = P3_VIEW
    P = Panel("P3", view_plate(OFFICE, *V, w, h))
    Mw = W2P(*V)
    sign_card(P, apply(Mw, P3_CARD), 150, -2)
    dx, dy, pitch = P3_STEP
    step = T(dx, dy) @ about(ROOT_, R(pitch))
    lay_clerk(P, Mw @ step, POSE_WALK, order=("clerk.torso", "clerk.head"), rec=FK)   # arm hangs below the frame
    SPEECH["P3"] = []
    return P


P3_CARD = (3900, 905)


VW = (0.538, 60, 600)
H4 = -6.0              # ticket window from inside (P4) and (P6 uses its own crop)


def P4():
    w, h = psize("P4")
    P = Panel("P4", view_plate(S3, *VW, w, h))
    Mw = W2P(*VW)
    # r1: nobody is drawn behind the glass: the asker is off-panel, on the platform (the tail goes out through the window)
    # the clerk's head and shoulder enter at the right edge, turned back toward the window (mirrored: facing left)
    kc = 0.70
    Mc = T(505, 430) @ S(kc) @ T(-CX, -1660) @ MIR()
    # r1: head and shoulders only (the pencil hand stays below the frame, so nothing reads as a look at a wristwatch);
    # head up on the collar, toward the voice at the window
    lay_clerk(P, Mc, dict(POSE_ARRIVE, head=H4), order=("clerk.torso", "clerk.head"), rec=FK)
    SPEECH["P4"] = [balloon(P, "b_what_time", ["What time", "is it?"], 66, (250, 165), (-30, 500), 21, tail_w=0.28, bend=0.12)]
    SPEECH["P4"][0].update(speaker="VISITOR", tail_target="off-panel left, through the ticket-window glass (the platform)")
    return P


P5_AT = (600, 395)


def P5():
    w, h = psize("P5")
    V = (0.75, 2210, 980)
    P = Panel("P5", view_plate(OFFICE, *V, w, h))
    # the office clock on the wall, its hands set to 4:10 (the hands are the clock's own, re-set on the arbor)
    cc = PC["clock.case"]
    kk = 0.70
    arb = cc["piv"]["arbor"]
    Mclk = T(845, 200) @ S(kk) @ T(-arb[0], -arb[1])
    P.piece("clock.case", cc["g"], cc["a"], Mclk @ T(*cc["o"]), margin=7, meta={"piece": "clock.case"})
    for n, ang in [("clock.hour", 4 * 30 + 10 * 0.5), ("clock.minute", 10 * 6)]:
        pc = PC[n]
        rot = ang - man["pieces"][n]["source_angle_deg"]
        Mh = Mclk @ about(arb, R(rot)) @ T(*pc["o"])
        hg = cv2.warpAffine(pc["g"], Mh[:2], (w, h), flags=cv2.INTER_CUBIC)
        ha = cv2.warpAffine(pc["a"], Mh[:2], (w, h), flags=cv2.INTER_LINEAR).astype(np.float32) / 255
        P.over(n, np.repeat(hg[..., None], 3, 2), ha, {"piece": n, "set_to_deg": ang, "matrix": Mh.round(6).tolist()})
    kc = 0.95
    Mc = T(P5_AT[0], P5_AT[1]) @ S(kc) @ T(-CX, -1660)          # r1: un-mirrored, so he faces the clock (upper right)
    lay_clerk(P, Mc, dict(POSE_SOURCE, head=H5), rec=FK)
    mouth = apply(Mc @ about(COLLAR, R(H5)), (2992, 2018))
    SPEECH["P5"] = [balloon(P, "b_ten_past", ["Ten past", "four!"], 70, (250, 160), (mouth[0] - 14, mouth[1] + 4), 33, tail_w=0.24, bend=0.10)]
    SPEECH["P5"][0].update(speaker="CLERK", tail_target="clerk's mouth")
    return P


def P6():
    w, h = psize("P6")
    V = (0.577, 60, 600)
    P = Panel("P6", view_plate(S3, *V, w, h))
    SPEECH["P6"] = [balloon(P, "b_thanks", ["Thanks!"], 70, (345, 170), (-30, 330), 61, tail_w=0.30, bend=0.10)]
    SPEECH["P6"][0].update(speaker="VISITOR", tail_target="off-panel left, out through the ticket window (she is leaving)")
    return P


VC7 = (0.665, 2780, 500)
VC8 = (0.84, 2860, 640)
P8_ROOT = (640, 1150)
FORGOT = ["Now... what", "did I come over", "here for?"]       # r1: the production's own words


def P7():
    w, h = psize("P7")
    P = Panel("P7", view_plate(SETP, *VC7, w, h))
    Mw = W2P(*VC7)
    sign_card(P, apply(Mw, (4060, 790)), 0.665 * 330, -2)
    lay_door_key(P, *VC7, swing=0.34, rec=FK)
    kc = 0.62
    Mc = T(890, 1010) @ S(kc) @ T(-ROOT_[0], -ROOT_[1]) @ MIR()
    lay_clerk(P, Mc, POSE_ARRIVE, rec=FK)
    SPEECH["P7"] = []
    return P


B8_AT = (390, 160)


def P8():
    w, h = psize("P8")
    P = Panel("P8", view_plate(SETP, *VC8, w, h))
    Mw = W2P(*VC8)
    sign_card(P, apply(Mw, (4110, 900)), VC8[0] * 330, -2)
    lay_door_key(P, *VC8, swing=0.34, rec=FK)
    # r1: un-mirrored, so he faces right, AWAY from the key on the door at the left; head tipped up on the collar;
    # he stands nearer the door, the key just beyond his left elbow
    kc = 0.74
    Mc = T(P8_ROOT[0], P8_ROOT[1]) @ S(kc) @ T(-ROOT_[0], -ROOT_[1])
    lay_clerk(P, Mc, POSE_CHIN, rec=FK)
    mouth = apply(Mc @ about(COLLAR, R(H8)), (2992, 2018))
    SPEECH["P8"] = [balloon(P, "b_forgot", FORGOT, 62, B8_AT, (mouth[0] + 10, mouth[1] - 6), 83, tail_w=0.22, bend=0.08)]
    SPEECH["P8"][0].update(speaker="CLERK", tail_target="clerk's mouth")
    return P


# ------------------------------------------------------------------ page
def tone(a):
    L = a.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    return {"pct_L_gt_220": round(float((L > 220).mean() * 100), 1), "pct_L_gt_230": round(float((L > 230).mean() * 100), 1),
            "pct_L_lt_40": round(float((L < 40).mean() * 100), 1), "median": float(np.median(L))}


def save_layers(P, border_crop):
    d = REST / P.key
    d.mkdir(parents=True, exist_ok=True)
    for f in d.glob("*.png"):
        f.unlink()
    rows = []
    for i, (name, rgba, meta) in enumerate(P.layers + [("border", np.dstack([np.broadcast_to(INK, P.c.shape), border_crop]), {})]):
        fn = f"{i:02d}_{name}.png"
        Image.fromarray(np.clip(np.round(rgba), 0, 255).astype(np.uint8), "RGBA").save(d / fn, optimize=False, compress_level=3)
        rows.append({"order": i, "file": fn, "name": name, **{k: v for k, v in meta.items() if k in ("piece", "matrix", "pose", "jamb_top_px", "jamb_bottom_px", "swing_scaleX", "hook_px", "set_to_deg", "through_glass")}})
    json.dump({"panel": P.key, "bounds_page_px": PANELS[P.key], "composite": "over, in order, starting from 00_bg (opaque)",
               "layers": rows}, open(d / "layers.json", "w"), indent=1)


def recompose(key):
    d = REST / key
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


def main():
    pg = sheet()
    built = {}
    for key, fn in [("P1", P1), ("P2", P2), ("P3", P3), ("P4", P4), ("P5", P5), ("P6", P6), ("P7", P7), ("P8", P8)]:
        built[key] = fn()
        x0, y0, x1, y1 = PANELS[key]
        pg[y0:y1, x0:x1] = built[key].c
    bm = border_mask((PAGE_H, PAGE_W), [PANELS[k] for k in PANELS], 9, 900)
    ink_onto(pg, bm)
    out = np.clip(np.round(pg), 0, 255).astype(np.uint8)
    PAGE_OUT.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out).save(PAGE_OUT, dpi=(300, 300))
    checks = {}
    for key, P in built.items():
        x0, y0, x1, y1 = PANELS[key]
        save_layers(P, bm[y0:y1, x0:x1])
        rc = recompose(key)
        diff = np.abs(np.clip(np.round(rc), 0, 255) - out[y0:y1, x0:x1].astype(np.float32))
        checks[key] = {"rest_layers_vs_page_mean_abs": round(float(diff.mean()), 3), "max_abs": float(diff.max())}
    st = {"page": tone(out), "panels_only": tone(np.concatenate([out[b[1]:b[3], b[0]:b[2]].reshape(-1, 3) for b in PANELS.values()]))}
    json.dump({"tone": st, "rest_identity": checks, "fk": FK, "pose_chin": POSE_CHIN}, open(BUILD / "page_checks.json", "w"), indent=1)
    json.dump(SPEECH, open(BUILD / "speech.json", "w"), indent=1)
    print(json.dumps(st), json.dumps(checks)[:400], POSE_CHIN)


if __name__ == "__main__":
    main()
