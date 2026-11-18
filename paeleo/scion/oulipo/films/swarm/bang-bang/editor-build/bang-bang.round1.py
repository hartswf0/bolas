# Bang Bang (after Jabely / Queneau's storyboard dossier): SCION proof film, Direction 2 "Planche gravée".
#
# A magpie narrates three flying attempts by a fictional inventor (Monsieur Pique-Vent). The picture is
# articulated cut-paper puppets cut (GrabCut, SCION #29) from public-domain engravings (Popular Science Monthly
# 1894-95 Lilienthal apparatus; Pénaud's flying models 1875; Bowen/Audubon magpie, 1840s), pinned with brass split
# pins (Reiniger, SCION #2) and posed frame by frame on 2s from the board unit's exposure sheet, with spring-damper
# follow-through (SCION #41). The commentary is the bird's: torn cream slips written on letter by letter in a loose
# pen hand, one struck word (monter -> s'arrêter) at the stall.
#
#   python3 films/bang-bang.py                 -> assets/films/bang-bang.mp4 + .webp (1280x720, repair 1)
#   python3 films/bang-bang.py --stills 22 ... -> films/stills/bang-bang/
#   python3 films/bang-bang.py --variants      -> films/swarm/bang-bang/baseline_bb07-09.mp4, swap_bb07-09.mp4
#   python3 films/bang-bang.py --checks        -> saved frames, side-by-side, measurements (films/swarm/bang-bang/)
#
# Inputs (built by the swarm units, read here, not edited): swarm/bang-bang/{exposure.json, cues.json,
# cues_swap.json, stems.json, rig.json, ledger.json}; the rig/dynamics code in swarm/bang-bang/board-build/board.py
# (imported for the puppet pieces, pins, joint chain and the same spring-damper runs that produced exposure.json);
# the pieces and sheets in sources/bang-bang/board/; the stems in sources/bang-bang/sound/.
import json, math, os, sys, wave
from pathlib import Path

import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

FILMS = Path(__file__).resolve().parent
PROJ = FILMS.parent
SW = FILMS / "swarm" / "bang-bang"
SND = FILMS / "sources" / "bang-bang" / "sound"
sys.path.insert(0, str(FILMS))
sys.path.insert(0, str(SW / "board-build"))
sys.path.insert(0, str(SW / "proposals"))
sys.path.insert(0, str(SW / "editor-build"))
from kit import Film, Mix  # noqa: E402
import pen  # noqa: E402  (the board unit's ink layer; imported here first so the hand can be replaced)
import hand_shim  # noqa: E402  (editor repair 1: the handmade joined cursive, editor-build/cursive.py)
pen.hand = hand_shim.pen_hand
import board as B  # noqa: E402
B.hand2 = hand_shim.hand2

FPS, NF = 24, 720
OW, OH = 1280, 720                                     # repair 1: 1280x720 so hatching and glosses survive
KZ = OW / 960                                          # the board camera is written for a 960-wide frame
PX, PWID, PHT, PYS, TX0, GROUND, PW, PH = B.PX, B.PWID, B.PHT, B.PYS, B.TX0, B.GROUND, B.PW, B.PH
PENINK, GRAPH, SHADOW, DESK = B.PENINK, B.GRAPH, B.SHADOW, B.DESK

CUES = json.load(open(SW / "cues.json"))
SWAP = json.load(open(SW / "cues_swap.json"))
EXPO = json.load(open(SW / "exposure.json"))
assert EXPO["frames"] == NF and EXPO["strike_frame"] == 528 and EXPO["impact_frame"] == 605

# ------------------------------------------------------------------ editor's fixes to the staging (writer unit's open items)
# (1) 'Krach !' witness: from f576 to f620 the magpie perches at the right edge of panel 3, head lowered to the wreck,
#     instead of on the post in panel 2 (out of frame during BB-09). Panel 2 keeps the post pose as its held key.
_fly0 = B.fly_s2
_CALLS = {"n": 0}


def fly_s2(f):
    _CALLS["n"] += 1
    if 576 <= f < 620:
        if f == 600 and _CALLS["n"] > 1:
            return _fly0(600)                              # panel 2's held key pose (bird on the post)
        hop = 8 * math.sin(math.pi * (f - 576) / 6) if f < 582 else 0.0
        head = 18 if f < 590 else 34                       # two held head angles: watching, then down at the wreck
        return ("perch", "s2p3", 655, GROUND - 4 - hop, -14, head)
    return _fly0(f)


B.fly_s2 = fly_s2

# (2) S3 ('Enfin, les grandes ailes.') needs its referent: the glider puppet is laid into sheet 1 panel 3 at f340,
#     dropped onto the card (cast shadow shrinking as it lands), and stays there as that panel's key pose.
_scene0 = B.scene


def scene(f):
    _CALLS["n"] = 0
    sh, out = _scene0(f)
    if sh == 1 and f >= 340:
        s = B.smooth((f - 340) / 6.0); hgt = 46 * (1 - s)
        ch = B.pose_chain("glider", "hip", (440 - 10 * (1 - s), GROUND - 64 - 30 * (1 - s)), 3 + 4 * (1 - s), {"legs": -3})
        for nm in ("legs", "glider"):
            out.append(("s1p3", nm, ch[nm][0], hgt + 4))
    return sh, out


B.scene = scene


# ------------------------------------------------------------------ the sheets (replaces board.build_sheet: headers with
# frame ranges, the BB-06 header on sheet 1 panel 3, the inked A/B labels, the vertical graphite margin note)
HEADS = {1: ["BB-01   1,0 - 8,0 s   f24-192   l'aile de papier", "BB-02/03   8,0 - 16,0 s   f192-384   le moulin",
             "BB-06   16,0 - 18,0 s   f384-432   les grandes ailes"],
         2: ["BB-07   18,0 - 21,0 s   f432-504   l'élan", "BB-08   21,0 - 24,0 s   f504-576   le décrochage",
             "BB-09   24,0 - 27,5 s   f576-660   la chute"]}


FICTION = "M. Pique-Vent, inventeur inventé - vols imaginés"


def build_sheet(n):
    pg = B.paper(PW, PH, 10 + n, B.PAPER)
    xx = np.arange(PW, dtype=np.float32)
    mg = np.clip((90 - xx) / 60, 0, 1)[None, :, None]
    pg = pg * (1 - mg) + (pg / B.PAPER * B.MARGIN) * mg
    gk = pen.Ink(PW, PH, 300 + n); rg = np.random.default_rng(310 + n)
    lines = ["Planche", "Il s'est fait une aile", "en papier.  pof", "Ensuite un moulin", "à élastique", "clac",
             "Enfin les grandes ailes", "Il court face au vent", "Donc il se pose", "Un peu vite", "mais au bon endroit"]
    for i, s_ in enumerate(lines):
        pen.hand(gk, s_, 140 + rg.uniform(0, 80), 200 + i * 135, size=1.5, width=2.6, rng=rg)
    for y0 in PYS:
        X0 = PW - PX - PWID
        gk.line([(X0, y0), (X0 + PWID, y0 + 2)], width=2.4); gk.line([(X0 + PWID, y0 + 2), (X0 + PWID, y0 + PHT)], width=2.4)
        gk.line([(X0 + PWID, y0 + PHT), (X0, y0 + PHT)], width=2.4); gk.line([(X0, y0 + PHT), (X0, y0)], width=2.4)
    gc = cv2.GaussianBlur(gk.coverage()[:, ::-1], (0, 0), 2.2)
    B.comp(pg, B.GHOST, np.clip(cv2.GaussianBlur(gc, (0, 0), 1.5) * 0.42, 0, 0.32))
    k = pen.Ink(PW, PH, 320 + n)
    for i, y0 in enumerate(PYS):
        # repair 1: no toned card inside the panel; the panel is the same paper as the page, as in the reference
        x0 = PX
        k.line([(x0, y0), (x0 + PWID, y0 + 1)], width=2.6, jit=1.0); k.line([(x0 + PWID, y0 + 1), (x0 + PWID + 1, y0 + PHT)], width=2.6, jit=1.0)
        k.line([(x0 + PWID + 1, y0 + PHT), (x0 - 1, y0 + PHT - 1)], width=2.6, jit=1.0); k.line([(x0 - 1, y0 + PHT - 1), (x0, y0)], width=2.6, jit=1.0)
        cov = B.SETS[f"s{n}p{i + 1}"]
        k.a[y0 * pen.SS:(y0 + PHT) * pen.SS, PX * pen.SS:(PX + PWID) * pen.SS] = np.maximum(
            k.a[y0 * pen.SS:(y0 + PHT) * pen.SS, PX * pen.SS:(PX + PWID) * pen.SS], cv2.resize(cov, (PWID * pen.SS, PHT * pen.SS)))
    pg = pen.put_ink(pg, k.coverage(), ink=PENINK, seed=330 + n)
    yy, xx2 = np.ogrid[:PH, :PW]
    for y0 in PYS:                                     # the punched dot: a hole showing the dark board below
        d = np.sqrt((xx2 - (PX + 26)) ** 2 + (yy - (y0 + 24)) ** 2)
        B.comp(pg, (58, 48, 40), np.clip(11.5 - d, 0, 1))
        B.comp(pg, (90, 78, 66), np.clip(5 - np.sqrt((xx2 - (PX + 23)) ** 2 + (yy - (y0 + 21)) ** 2), 0, 1) * 0.6)
    g = pen.Ink(PW, PH, 340 + n); rgr = np.random.default_rng(350 + n)
    for i, y0 in enumerate(PYS):
        pen.hand(g, HEADS[n][i], PX + 60, y0 - 14, size=0.85, width=1.3, rng=rgr)
    pen.hand(g, f"Bang Bang  -  planche {n}", TX0 + 20, 50, size=1.1, width=1.5, rng=rgr)
    # repair 1 (reviewer): the fiction is declared on the page itself, readable in the wide shots
    pen.hand(g, FICTION, TX0 + 20, 98, size=1.55, width=1.9, rng=rgr)
    pen.hand(g, str(n), PW - 120, 80, size=1.2, width=1.6, rng=rgr)
    cov_g = g.coverage()
    if n == 2:                                         # the reference's marginal device: a vertical note beside panel 2
        m = pen.Ink(560, 70, 361); pen.hand(m, "BB-08  f504-576  voir B", 10, 46, size=0.85, width=1.3, rng=np.random.default_rng(362))
        mc = cv2.rotate(m.coverage(), cv2.ROTATE_90_COUNTERCLOCKWISE)
        y0 = PYS[1] + 20; x0 = PX + PWID + 6
        cov_g[y0:y0 + mc.shape[0], x0:x0 + mc.shape[1]] = np.maximum(cov_g[y0:y0 + mc.shape[0], x0:x0 + mc.shape[1]], mc)
    pg = pen.put_ink(pg, cov_g * 0.8, ink=GRAPH, seed=360 + n, bleed=0.4)
    return pg


# inked part labels, written in by the board artist as each board plays: A at the paper wing (BB-01, from f60),
# B at the rubber band (BB-02/03, from f300); panel-local coverage
def _label(ch, x, y, seed):
    L = pen.Ink(PWID, PHT, seed); pen.hand(L, ch, x, y, size=0.9, width=1.7, rng=np.random.default_rng(seed + 1)); return L.coverage()


LAB_A, LAB_B = _label("A", 560, 150, 370), _label("B", 412, 190, 372)

# camera (repair 1): the slips are wider (larger hand), so every push-in keeps the panel at ~60 % of frame width with
# the frame's right edge just past the slip column; BB-08 still pushes in (58 -> 61 %), one move per board.
def cam_panel(i, frac):
    z = frac * 960 / PWID; fw = 960 / z
    right = TX0 + 4 + SLIP_W + 26
    return right - fw / 2, PYS[i] + PHT / 2 + 14, z


def camera(f):
    W_ = B.CAM_WIDE; L = B.lerp_cam
    if f < 24: return 1, W_, "wide"
    if f < 192: return 1, L(W_, cam_panel(0, 0.60), (f - 24) / 30), "push panel 1"
    if f < 384: return 1, L(cam_panel(0, 0.60), cam_panel(1, 0.60), (f - 192) / 14), "slide to panel 2"
    if f < 432:
        if f < 396: return 1, L(cam_panel(1, 0.60), W_, (f - 384) / 12), "pull out"
        if f < 420: return (1 if f < 408 else 2), W_, "page turn"
        return 2, L(W_, cam_panel(0, 0.60), (f - 420) / 12), "push panel 1"
    if f < 504: return 2, cam_panel(0, 0.60), "hold panel 1"
    if f < 576: return 2, L(cam_panel(1, 0.58), cam_panel(1, 0.61), (f - 504) / 40), "push-in panel 2"
    if f < 660: return 2, L(cam_panel(2, 0.60), cam_panel(2, 0.61), (f - 576) / 84), "panel 3"
    if f < 684: return 2, L(cam_panel(2, 0.61), W_, (f - 660) / 18), "pull out"
    return 2, W_, "wide"


B.camera = camera


SHEETS = {}


def sheet(n):
    if n not in SHEETS:
        SHEETS[n] = build_sheet(n)
    return SHEETS[n]


# ------------------------------------------------------------------ the bird's slips (from cues.json), typed baseline strips
PANEL_OF = {"BB-01": (1, 0), "BB-02/03": (1, 1), "BB-03/06": (1, 2), "BB-07": (2, 0), "BB-08": (2, 1), "BB-09": (2, 2)}
SLIP_W, SLIP_SIZE = 384, 1.55                          # repair 1: x-height ~23 page px, the reference's hand size
XH = hand_shim.XH * SLIP_SIZE; LINE_H = 2.85 * XH
GLOSS_X, GLOSS_W, GLOSS_SIZE = TX0 + 4 + SLIP_W + 46, 640, 1.75  # graphite English gloss: one paragraph per panel


def cps_for(text, a, b):
    L = len(text.replace(" ", "")); Wd = len(text.split(" "))
    return (L + 0.6 * (Wd - 1)) * FPS / max(1, b - a)


def build_slips(cues):
    """One torn slip per non-continuation cue; continuation cues (line_of) are written on their slip's next line.
    Returns {sheet: [slip dict]} with page positions stacked one group per panel in the right column."""
    rows = [c for c in cues if c.get("kind", "slip") == "slip" or c["cue"].startswith("S")]
    base = [c for c in rows if not c.get("line_of")]
    out = {1: [], 2: []}; ystack = {}
    for k, c in enumerate(base):
        sh, pi = PANEL_OF[c["board_id"]]
        seed = 40 + k * 7
        Wc, Hc = SLIP_W, 520
        y0 = 26 + 2.0 * XH + (0.9 * XH if any(d.get("line_of") == c["cue"] and d["cue"].endswith("-corr") for d in rows) else 0)
        letters, (ex, ey) = B.hand2(Wc, Hc, c["text"], 20, y0, size=SLIP_SIZE, width=2.4, seed=900 + seed, maxw=Wc - 44,
                                    line_h=LINE_H + (1.0 * XH if any(d.get("line_of") == c["cue"] and d["cue"].endswith("-corr") for d in rows) else 0),
                                    cps=cps_for(c["text"], c["write_start_frame"], c["write_end_frame"]), t0=c["write_start_frame"])
        sl = {"id": c["cue"], "text": c["text"], "letters": letters, "t": c["paste_frame"], "w0": c["write_start_frame"],
              "end": c["write_end_frame"], "gloss": c.get("gloss_en_graphite", ""), "cont": [], "strike": None, "fix": None}
        for cc in [d for d in rows if d.get("line_of") == c["cue"]]:
            if cc["cue"].endswith("-strike"):
                n6 = len(c["text"].split(" ")[-1])
                mx0, my0, mx1, my1 = B.letters_bbox(letters, len(letters) - n6, len(letters))
                stk = pen.Ink(Wc, Hc, 948); stk.line([(mx0 - 5, (my0 + my1) / 2 + 3), (mx1 + 6, (my0 + my1) / 2 - 2)], width=3.0, jit=0.6, press=0.3)
                sl["strike"] = (stk.coverage(), cc["write_start_frame"], mx0, mx1)
                sl["fixpos"] = (mx0 - 6, my0 - 4)
            elif cc["cue"].endswith("-corr"):
                fx, fy = sl["fixpos"]
                sl["fix"], _ = B.hand2(Wc, Hc, cc["text"], fx, fy, size=SLIP_SIZE * 0.78, width=2.2, seed=947,
                                       cps=len(cc["text"]) * FPS / max(1, cc["write_end_frame"] - cc["write_start_frame"]), t0=cc["write_start_frame"])
            else:
                lt, (ex, ey) = B.hand2(Wc, Hc, cc["text"], 26, ey + LINE_H, size=SLIP_SIZE, width=2.4, seed=930 + seed,
                                       maxw=Wc - 44, line_h=LINE_H, cps=cps_for(cc["text"], cc["write_start_frame"], cc["write_end_frame"]), t0=cc["write_start_frame"])
                sl["cont"].append(lt); sl["gloss"] += "  " + cc.get("gloss_en_graphite", "")
        allc = np.max([l[0] for l in letters + sum(sl["cont"], [])], 0)
        h = int(np.nonzero(allc.max(1) > 0.05)[0].max()) + 20
        sl["h"] = h
        for key in ("letters",):
            sl[key] = [(cv[:h], a, b) for cv, a, b in sl[key]]
        sl["cont"] = [[(cv[:h], a, b) for cv, a, b in lt] for lt in sl["cont"]]
        if sl["fix"]: sl["fix"] = [(cv[:h], a, b) for cv, a, b in sl["fix"]]
        if sl["strike"]: sl["strike"] = (sl["strike"][0][:h],) + sl["strike"][1:]
        sl["rgb"], sl["a"] = B.torn_slip(Wc, h, 900 + seed)
        y = ystack.get((sh, pi), PYS[pi] + 22)
        sl["x"] = TX0 + 4 + (k % 3) * 5; sl["y"] = y; sl["ang"] = [1.0, -1.4, 0.6, -0.8, 1.3][k % 5]
        ystack[(sh, pi)] = y + h + 16
        sl["gloss_txt"] = sl["gloss"].replace("~~climb~~ ", "").strip(); sl["panel"] = (sh, pi)
        sl["gloss_t"] = max([sl["end"]] + [cc["write_end_frame"] for cc in rows if cc.get("line_of") == c["cue"]]) + 3
        out[sh].append(sl)
    # the graphite English gloss: the slips of one panel make ONE paragraph in the right half of the column, each
    # sentence appearing once its slip is written (the reference's one-paragraph-per-panel grammar)
    for sh in out:
        for pi in range(3):
            group = [sl for sl in out[sh] if sl.get("panel") == (sh, pi)]
            if not group: continue
            text = "  ".join(sl["gloss_txt"] for sl in group)
            Wg, Hg = GLOSS_W + 60, PHT
            lets, _ = B.hand2(Wg, Hg, text, 8, 60, size=GLOSS_SIZE, width=1.7, seed=970 + 10 * sh + pi, maxw=GLOSS_W,
                              line_h=2.9 * hand_shim.XH * GLOSS_SIZE, cps=99, t0=0)
            k = 0
            for sl in group:
                n = len(sl["gloss_txt"].replace(" ", ""))
                part = lets[k:k + n]; k += n
                sl["gloss_cov"] = np.max([c for c, _, _ in part], 0) if part else None
                sl["gloss_xy"] = (GLOSS_X, PYS[pi] + 24)
    return out


def build_typed(rcues):
    """Human reporter's typed newspaper strips: typewriter face on a greyer newsprint strip, straight-cut, no correction."""
    fnt = ImageFont.truetype(str(PROJ / "assets" / "fonts" / "ibm-plex-mono.woff2"), 25)
    out = {2: []}; groups = []
    for c in rcues:
        if c.get("paste_frame") is None and groups: groups[-1]["lines"].append(c)
        else: groups.append({"lead": c, "lines": [c]})
    for k, g in enumerate(groups):
        sh, pi = PANEL_OF[g["lead"]["board_id"]]
        w = SLIP_W; h = 26 + 38 * len(g["lines"])
        r = np.random.default_rng(700 + k)
        rgb = B.paper(w, h, 710 + k, (231, 225, 213)); a = np.zeros((h, w), np.float32); a[3:h - 3, 2:w - 2] = 1
        lines = []
        for j, c in enumerate(g["lines"]):
            im = Image.new("L", (w, h), 0); d = ImageDraw.Draw(im)
            xs = [16]
            for ch in c["text"]:
                d.text((xs[-1], 12 + 38 * j + r.normal(0, 0.4)), ch, font=fnt, fill=int(225 * r.uniform(0.8, 1.0)))
                xs.append(xs[-1] + fnt.getlength(ch))
            lines.append((np.asarray(im, np.float32) / 255, xs, c["write_start_frame"], c["write_end_frame"]))
        out[sh].append({"id": g["lead"]["cue"], "typed": lines, "rgb": rgb, "a": a, "h": h, "t": g["lead"]["paste_frame"],
                        "x": TX0 + 4, "y": PYS[pi] + 22, "ang": 0.0, "gloss_cov": None})
    return out


def slip_cov(sl, f):
    if "typed" in sl:
        cov = np.zeros_like(sl["a"])
        for img, xs, a, b in sl["typed"]:
            if f < a: continue
            n = len(xs) - 1; k = n if f >= b else int(n * (f - a + 1) / max(1, b - a + 1))
            cov[:, :int(xs[k])] = np.maximum(cov[:, :int(xs[k])], img[:, :int(xs[k])])
        return cov
    cov = B.reveal(sl["letters"], f)
    for lt in sl["cont"]:
        c2 = B.reveal(lt, f)
        if c2 is not None: cov = np.maximum(cov, c2)
    if sl["strike"] is not None:
        sc, sf, mx0, mx1 = sl["strike"]
        if f >= sf:
            xs = np.arange(cov.shape[1], dtype=np.float32); xe = mx0 - 5 + (mx1 - mx0 + 11) * min(1.0, (f - sf + 1) / 3)
            cov = np.maximum(cov, sc * np.clip((xe - xs) / 2, 0, 1)[None, :])
    if sl["fix"]:
        fc = B.reveal(sl["fix"], f)
        if fc is not None: cov = np.maximum(cov, fc)
    return cov


SLIPSETS = {}


def slipset(name):
    if name not in SLIPSETS:
        if name == "bird": SLIPSETS[name] = build_slips(CUES["cues"])
        elif name == "swap": SLIPSETS[name] = build_slips(SWAP["cues"])
        else:
            s = build_slips([c for c in CUES["cues"] if PANEL_OF[c["board_id"]][0] == 1])
            s[2] = build_typed(CUES["baseline_human_reporter"]["slips"])[2]
            SLIPSETS[name] = s
    return SLIPSETS[name]


# ------------------------------------------------------------------ the rubber band (BB-02/03), drawn by the board artist each drawing
def band_cov(items, fa):
    hub = None
    for panel, nm, M, hgt in items:
        if panel == "s1p2" and nm == "heli_shaft":
            pv = B.P["heli_shaft"]["pv"]; top = B.ap(M, pv["top_hub"]); bot = B.ap(M, pv["bottom_hub"]); hub = (top, bot)
    if hub is None or fa < 192:
        return None
    top, bot = hub
    k = pen.Ink(PWID, PHT, 600 + fa // 4)
    d = bot - top; L = float(np.hypot(*d)) + 1e-6; nrm = np.array([-d[1], d[0]]) / L
    if fa < 312:                                       # the twisted skein: more kinks as it is wound
        turns = min(12, max(0, (fa - 192) // 5)) if fa < 252 else 12 - 9 * min(1.0, (fa - 254) / 58)
        n = int(4 + 2 * turns); ts = np.linspace(0, 1, 4 * n + 1)
        amp = 3.0 + 0.25 * turns
        pts = [top + d * t + nrm * (amp * math.sin(t * n * math.pi) + 7) for t in ts]
        k.line(pts, width=1.3, jit=0.25, press=0.2)
    else:                                              # snapped: the loose end whips (spring amplitude BAND[f]) and hangs
        A = B.BAND.get(fa, 0.0) if fa <= 384 else 0.0
        ts = np.linspace(0, 1, 40)
        pts = [bot + np.array([10 + 34 * t + A * 0.5 * t * math.sin(t * 7 + fa * 0.8), -8 + 26 * t * t + A * 0.3 * t * math.cos(t * 5)]) for t in ts]
        k.line(pts, width=1.3, jit=0.3, press=0.2)
    if 192 <= fa < 260:                                # graphite tally of turns
        g = pen.Ink(PWID, PHT, 620)
        n = min(12, max(0, (fa - 192) // 5))
        for i in range(n):
            gx = 560 + (i % 5) * 9 + (i // 5) * 62
            g.line([(gx, 52), (gx + 1, 78)], width=1.0, jit=0.2) if (i % 5) < 4 else g.line([(gx - 40, 72), (gx + 4, 56)], width=1.0, jit=0.2)
        return k.coverage(), g.coverage()
    return k.coverage(), None


# ------------------------------------------------------------------ one frame (page-space crop -> 960x540); board.render generalised
PIN_SCALE = 0.55


def put_cov(can, cov, ink, alpha, x, y, seed):
    if cov is None: return
    h, w = cov.shape; x, y = int(x), int(y); Hc, Wc = can.shape[:2]
    xa_, ya_, xb_, yb_ = max(0, x), max(0, y), min(Wc, x + w), min(Hc, y + h)
    if xb_ > xa_ and yb_ > ya_:
        sub = can[ya_:yb_, xa_:xb_]
        can[ya_:yb_, xa_:xb_] = pen.put_ink(sub, cov[ya_ - y:yb_ - y, xa_ - x:xb_ - x] * alpha, ink=ink, seed=seed, bleed=0.4)


def render(f, slips="bird", force_sheet=None):
    fa = f - (f % 2)                                   # on 2s
    sh_n, cam, _ = B.camera(fa)
    if force_sheet: sh_n = force_sheet
    cx, cy, z = cam
    fw, fh = 960 / z, 540 / z
    X0, Y0 = int(math.floor(cx - fw / 2)) - 2, int(math.floor(cy - fh / 2)) - 2
    Wc, Hc = int(fw) + 6, int(fh) + 6
    can = np.zeros((Hc, Wc, 3), np.float32) + DESK
    S = sheet(sh_n)
    xa, ya, xb, yb = max(0, X0), max(0, Y0), min(PW, X0 + Wc), min(PH, Y0 + Hc)
    if xb > xa and yb > ya:
        dm = np.zeros((Hc, Wc), np.float32); dm[max(0, -Y0 + 8):max(0, PH - Y0 + 8), max(0, -X0 + 6):max(0, PW - X0 + 6)] = 1
        B.comp(can, SHADOW, cv2.GaussianBlur(dm, (0, 0), 6) * 0.18)
        can[ya - Y0:yb - Y0, xa - X0:xb - X0] = S[ya:yb, xa:xb]
    ox, oy = PX - X0, PYS[1] - Y0
    if sh_n == 2:                                      # BB-08 board-artist annotations, once the pose is held (kept after)
        if fa >= 541: put_cov(can, B.ANN_G, GRAPH, 0.75 * min(1, (fa - 541) / 8), ox, oy, f // 4)
        if fa >= 543: put_cov(can, B.ANN_A, PENINK, min(1, (fa - 543) / 3), ox, oy, f // 4)
        if fa >= 549: put_cov(can, B.ANN_B, PENINK, min(1, (fa - 549) / 3), ox, oy, f // 4)
    _, items = B.scene(fa if (force_sheet is None or force_sheet == (1 if fa < 408 else 2)) else (406 if force_sheet == 1 else 420))
    if sh_n == 1:
        if fa >= 60: put_cov(can, LAB_A, PENINK, min(1, (fa - 60) / 3), PX - X0, PYS[0] - Y0, 11)
        if fa >= 300: put_cov(can, LAB_B, PENINK, min(1, (fa - 300) / 3), PX - X0, PYS[1] - Y0, 12)
        bc = band_cov(items, fa)
        if bc:
            put_cov(can, bc[0], B.INK, 1.0, PX - X0, PYS[1] - Y0, 5)
            if bc[1] is not None: put_cov(can, bc[1], GRAPH, 0.8, PX - X0, PYS[1] - Y0, 6)
    shadow = np.zeros((Hc, Wc), np.float32); layers = []
    for panel, nm, M, hgt in items:
        px0, py0 = B.panel_origin(panel)
        Mw = M.copy(); Mw[0, 2] += px0 - X0; Mw[1, 2] += py0 - Y0
        # clip to the panel, and skip pieces whose panel is outside the view
        cy0, cy1 = max(0, py0 - Y0 + 3), min(Hc, max(0, py0 - Y0 + PHT - 3)); cx0, cx1 = max(0, px0 - X0 + 3), min(Wc, max(0, px0 - X0 + PWID - 3))
        if cy1 <= cy0 or cx1 <= cx0: continue
        pc = B.P[nm]
        # warp only inside the panel's visible window
        Mw2 = Mw.copy(); Mw2[0, 2] -= cx0; Mw2[1, 2] -= cy0
        ww, hh = cx1 - cx0, cy1 - cy0
        a = np.zeros((Hc, Wc), np.float32); rgb = np.zeros((Hc, Wc, 3), np.float32)
        a[cy0:cy1, cx0:cx1] = cv2.warpAffine(pc["a"], Mw2, (ww, hh), flags=cv2.INTER_LINEAR)
        rgb[cy0:cy1, cx0:cx1] = cv2.warpAffine(pc["rgb"], Mw2, (ww, hh), flags=cv2.INTER_LINEAR)
        dx, dy = 0.07 * hgt + 3, 0.10 * hgt + 4
        Ms = Mw2.copy(); Ms[0, 2] += dx; Ms[1, 2] += dy
        shadow[cy0:cy1, cx0:cx1] = np.maximum(shadow[cy0:cy1, cx0:cx1], cv2.warpAffine(pc["a"], Ms, (ww, hh)))
        layers.append((a, rgb))
    B.comp(can, SHADOW, cv2.GaussianBlur(shadow, (0, 0), 4) * 0.26)
    for a, rgb in layers:
        can *= (1 - a[..., None]); can += rgb
    for panel, nm, M, hgt in items:                    # brass split pins at the visible joints
        px0, py0 = B.panel_origin(panel)
        pins = {"glider": ["hip"], "glider_core": ["hip", "wing_root_R"], "pilot_torso": ["hip", "shoulder_R"], "pie_body": ["neck"],
                "fly_body": ["shoulder_L"], "heli_shaft": ["top_hub", "bottom_hub"]}.get(nm, [])
        for pn in pins:
            if pn in B.P[nm]["pv"]:
                hp = B.ap(M, B.P[nm]["pv"][pn]); B.pin_at(can, hp[0] + px0 - X0, hp[1] + py0 - Y0, PIN_SCALE)
    # the slips: pasted (lift + shadow settle over 3 frames), pinned, written on
    for sl in slipset(slips).get(sh_n, []):
        if sl["t"] is None or f < sl["t"]: continue
        cov = slip_cov(sl, f)
        ink = PENINK if "typed" not in sl else (38, 36, 34)
        rgb = pen.put_ink(sl["rgb"].copy(), cov, ink=ink, seed=7)
        lift = max(0.0, 6 - 2 * (f - sl["t"]))
        h, w = sl["a"].shape
        M = cv2.getRotationMatrix2D((w / 2, h / 2), sl["ang"], 1.0); M[0, 2] += sl["x"] - X0 - lift; M[1, 2] += sl["y"] - Y0 - lift * 2
        A = cv2.warpAffine(sl["a"], M, (Wc, Hc)); Rg = cv2.warpAffine(rgb * sl["a"][..., None], M, (Wc, Hc))
        Ms = M.copy(); Ms[0, 2] += 2 + lift; Ms[1, 2] += 3 + lift * 1.4
        B.comp(can, SHADOW, cv2.GaussianBlur(cv2.warpAffine(sl["a"], Ms, (Wc, Hc)), (0, 0), 2.5) * 0.24)
        can = can * (1 - A[..., None]) + Rg
        pn = B.ap(M, (16, 14)); B.pin_at(can, pn[0], pn[1], 1.0)
        if sl.get("gloss_cov") is not None and f >= sl["gloss_t"]:
            put_cov(can, sl["gloss_cov"], GRAPH, 0.95 * min(1, (f - sl["gloss_t"]) / 8), sl["gloss_xy"][0] - X0, sl["gloss_xy"][1] - Y0, 9)
    zo = z * KZ
    M = np.array([[zo, 0, -zo * (cx - fw / 2 - X0)], [0, zo, -zo * (cy - fh / 2 - Y0)]], np.float32)
    out = cv2.warpAffine(np.clip(can, 0, 255), M, (OW, OH), flags=cv2.INTER_AREA if zo < 1 else cv2.INTER_LINEAR,
                         borderValue=tuple(float(c) for c in DESK))
    return out


def page_turn(f, slips="bird"):
    """f396-f418 at the wide shot: planche 1 flips up on its top binding (foreshortened in y, edge shadow on planche 2)."""
    base = render(f, slips, force_sheet=2)
    if f >= 408:
        s = (f - 408) / 10.0
        cx, cy, z = B.CAM_WIDE; z *= KZ; top = (0 - (cy - OH / z / 2)) * z
        band = np.exp(-((np.arange(OH) - top) / 14.0) ** 2) * 0.22 * (1 - s)
        return base * (1 - band[:, None, None]) + SHADOW * band[:, None, None]
    up = render(f, slips, force_sheet=1)
    cx, cy, z = B.CAM_WIDE; z *= KZ
    top = (0 - (cy - OH / z / 2)) * z; bot = (PH - (cy - OH / z / 2)) * z
    x0 = int((0 - (cx - OW / z / 2)) * z); x1 = int(math.ceil((PW - (cx - OW / z / 2)) * z))
    s = (f - 396) / 12.0; c = max(0.02, math.cos(math.pi / 2 * s))
    t0, t1 = int(top), int(math.ceil(bot)); hh = t1 - t0; nh = max(1, int(hh * c))
    pg = cv2.resize(up[t0:t1, x0:x1], (x1 - x0, nh), interpolation=cv2.INTER_AREA)
    pg = pg * (0.93 + 0.07 * c)                        # the lifting page catches a little less light
    out = base.copy()
    ys = np.arange(OH, dtype=np.float32)
    edge = t0 + nh
    sh = np.exp(-np.clip(ys - edge, 0, None) / (18 + 40 * (1 - c))) * (ys >= edge) * 0.30 * (1 - c * 0.6)
    out = out * (1 - sh[:, None, None]) + SHADOW * sh[:, None, None]
    out[t0:t0 + nh, x0:x1] = pg
    return out


def frame_rgb(f, slips="bird"):
    if 396 <= f < 418:
        return page_turn(f, slips)
    return render(f, slips)


# ------------------------------------------------------------------ sound: the writer unit's stems, rebalanced, via mix.add
GAINS = {"air": 1.5, "magpie": 0.9, "paper": 1.5, "action": 0.85, "pin": 1.1}


def read_wav(p):
    w = wave.open(str(p)); n = w.getnframes(); ch = w.getnchannels(); assert w.getframerate() == 44100
    a = np.frombuffer(w.readframes(n), np.int16).astype(np.float64) / 32768
    return a.reshape(-1, ch) if ch > 1 else np.stack([a, a], 1)


def add_stereo(mix, st, gain, at=0.0):
    mix.add(st[:, 0], at, gain=gain / 1.414, pan=-1.0); mix.add(st[:, 1], at, gain=gain / 1.414, pan=1.0)


def stems_sound(mix, f0=0, f1=NF, drop=()):
    a, b = int(f0 / FPS * 44100), int(f1 / FPS * 44100)
    for name, g in GAINS.items():
        if name in drop: continue
        add_stereo(mix, read_wav(SND / f"bang-bang_stem_{name}.wav")[a:b], g)


# ------------------------------------------------------------------ films
def make_film(slug, f0, f1, slips, sound_fn):
    film = Film(slug, seconds=(f1 - f0) / FPS, size=(OW, OH))

    @film.picture
    def _(t, ink):
        k = int(round(t * FPS)) + f0
        ink.img = Image.fromarray(np.clip(frame_rgb(k, slips), 0, 255).astype(np.uint8))

    film.sound(sound_fn)
    return film


def main_film():
    film = make_film("bang-bang", 0, NF, "bird", lambda mix: stems_sound(mix))
    film.poster_at = 548 / FPS                        # the stall, struck word visible
    return film


def baseline_sound(mix):
    add_stereo(mix, read_wav(SND / "baseline_bb07-09_mix.wav"), 1.2)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--variants":
        make_film("baseline_bb07-09", 432, 660, "baseline", baseline_sound).render(out_dir=SW)
        make_film("swap_bb07-09", 432, 660, "swap", lambda mix: stems_sound(mix, 432, 660)).render(out_dir=SW)
    elif len(sys.argv) > 1 and sys.argv[1] == "--frames":
        for a in sys.argv[2:]:
            f = int(a); film = main_film(); film.frame(f).save(SW / f"frame_f{f:03d}.png")
            print("frame", f)
    else:
        main_film().render()
