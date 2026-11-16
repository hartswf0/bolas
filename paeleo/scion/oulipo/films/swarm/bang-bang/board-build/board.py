# Bang Bang, board unit: handmade pieces, rig (SCION #2), secondary dynamics (SCION #41), exposure sheet on 2s for
# BB-00..BB-10 (720 frames, 24 fps), and the BB-08 test render (f504-576, silent, 960x540, ffmpeg).
#   python3 -I board.py            (run cut.py first)
# Writes: films/swarm/bang-bang/{rig.json, exposure.json, bb08_test.mp4, bb08_sheet.jpg}
#         films/sources/bang-bang/board/  handmade RGBA pieces, sheets, test media copies
import os, sys, json, math, subprocess, shutil, hashlib
import numpy as np, cv2
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
FILMS = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(HERE, "..", "proposals"))
import pen                                                     # Ink (jittered pen strokes), put_ink

SW = os.path.join(FILMS, "swarm", "bang-bang")
BD = os.path.join(FILMS, "sources", "bang-bang", "board")
ED = os.path.join(FILMS, "sources", "bang-bang", "board-artist-and-puppet-cutter-cutout-rig-exposure-sheet-bb-08-test-shot-")
os.makedirs(ED, exist_ok=True)
MAN = json.load(open(os.path.join(BD, "cut_manifest.json")))

PAPER = np.array((242, 228, 212), np.float32)
PANEL = np.array((228, 216, 202), np.float32)
MARGIN = np.array((234, 220, 203), np.float32)
GHOST = np.array((206, 195, 185), np.float32)
INK = (45, 38, 32)                    # engraving print ink
PENINK = (52, 42, 34)                 # felt pen
GRAPH = (118, 110, 104)               # graphite
SHADOW = np.array((150, 130, 110), np.float32)
BRASS = (176, 138, 62)
DESK = np.array((247, 243, 237), np.float32)   # the white the reference sheet is photographed on
FPS, NF = 24, 720

# ------------------------------------------------------------------ page geometry (page px); reference grammar
PW, PH = 2200, 1800
PX, PWID, PHT = 253, 715, 493          # 1.45:1 panels, left column ~32 % of the page
PYS = [108, 646, 1184]
TX0 = 1010                             # commentary column starts here
GROUND = 430                           # panel-local ground line (v)


def paper(w, h, seed, tone):
    r = np.random.default_rng(seed)
    lo = cv2.resize(r.normal(0, 1, (h // 60 + 2, w // 60 + 2)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    mid = cv2.resize(r.normal(0, 1, (h // 8 + 2, w // 8 + 2)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    fib = cv2.GaussianBlur(r.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 0.7)
    k = 1 + 0.008 * lo + 0.005 * mid + 0.009 * fib            # tooth and low mottling, no vignette
    return np.asarray(tone, np.float32)[None, None, :] * k[..., None]


def comp(dst, rgb, a):
    a = a[..., None]; dst *= (1 - a); dst += np.asarray(rgb, np.float32) * a


# ------------------------------------------------------------------ the hand (the bird's): per-letter, not a typeface
ACC = pen.ACC
FONT = cv2.FONT_HERSHEY_SCRIPT_SIMPLEX


def hand2(W, H, text, x, y, size=1.0, width=1.6, seed=0, line_h=None, maxw=None, cps=12.0, t0=0.0):
    """A loose French pen hand.  Every LETTER is set separately from the Hershey script strokes with its own size,
    tilt, baseline offset and nib pressure; each word has its own slant; each line drifts.  Returns a list of
    (coverage(H,W) float32 for that letter, t_start_frame, t_end_frame) so the slip can be written on letter by letter
    at `cps` characters per second starting at frame t0, and the pen position at the end."""
    r = np.random.default_rng(seed)
    SS = 2
    out = []
    line_h = line_h or 64 * size
    cx, cy = x, y; tf = t0; drift = r.normal(0, 1.2)
    for wi, wd in enumerate(text.split(" ")):
        if wd == "\\n":
            cx, cy = x + r.normal(0, 4), cy + line_h * r.uniform(0.95, 1.08); drift = r.normal(0, 1.2); continue
        base_letters = [ACC.get(ch, (ch, None)) for ch in wd]
        est = sum(cv2.getTextSize(b, FONT, 1.25 * size * SS, 1)[0][0] for b, _ in base_letters) / SS * 0.9
        if maxw and cx + est > x + maxw and cx > x:
            cx, cy = x + r.normal(0, 4), cy + line_h * r.uniform(0.95, 1.08); drift = r.normal(0, 1.2)
        slant = r.normal(-9, 4)                                  # forward slant varies by word
        wscale = r.uniform(0.9, 1.12); press = r.uniform(0.75, 1.3)
        for li, (b, acc) in enumerate(base_letters):
            sc = 1.25 * size * SS * wscale * r.uniform(0.9, 1.1)
            (tw, th), bl = cv2.getTextSize(b, FONT, sc, 1)
            m = np.zeros((th + bl + 70, tw + 50), np.uint8); org = (25, th + 35)
            cv2.putText(m, b, org, FONT, sc, 255, 1, cv2.LINE_AA)
            if acc:
                cxa = org[0] + tw * 0.55; top = org[1] - th * 0.55; s = sc * 9
                if acc == "acute": cv2.line(m, (int(cxa - s * .3), int(top)), (int(cxa + s * .6), int(top - s * 1.0)), 255, 1, cv2.LINE_AA)
                elif acc == "grave": cv2.line(m, (int(cxa + s * .3), int(top)), (int(cxa - s * .6), int(top - s * 1.0)), 255, 1, cv2.LINE_AA)
                elif acc == "circ": cv2.polylines(m, [np.int32([(cxa - s * .5, top), (cxa, top - s * .9), (cxa + s * .5, top)])], False, 255, 1, cv2.LINE_AA)
                elif acc == "ced": cv2.ellipse(m, (int(cxa - s * .1), int(org[1] + s * .5)), (int(s * .35), int(s * .45)), 0, -90, 120, 255, 1, cv2.LINE_AA)
            ang = r.normal(0, 3.5)
            M = cv2.getRotationMatrix2D((org[0], org[1]), ang, 1.0)
            sh = math.tan(math.radians(slant)); M[0, 1] -= sh; M[0, 2] += sh * org[1]
            m = cv2.warpAffine(m, M, (m.shape[1] + 20, m.shape[0]), flags=cv2.INTER_LINEAR)
            H0, W0 = m.shape; k = (max(2, H0 // 10), max(2, W0 // 10))
            gx, gy = np.meshgrid(np.arange(W0, dtype=np.float32), np.arange(H0, dtype=np.float32))
            dx = cv2.resize(r.normal(0, 0.9 * SS, k).astype(np.float32), (W0, H0), interpolation=cv2.INTER_CUBIC)
            dy = cv2.resize(r.normal(0, 0.9 * SS, k).astype(np.float32), (W0, H0), interpolation=cv2.INTER_CUBIC)
            m = cv2.remap(m, gx + dx, gy + dy, cv2.INTER_LINEAR)
            nb = max(2, int(round(width * press * r.uniform(0.85, 1.15) * SS)))
            ker = np.zeros((nb + 2, nb + 2), np.uint8)
            cv2.ellipse(ker, ((nb + 1) // 2, (nb + 1) // 2), (max(1, nb // 2), max(1, int(nb * 0.33))), 35, 0, 360, 1, -1)
            m = cv2.dilate(m, ker).astype(np.float32) / 255
            # place: letters overlap a little so the script joins; baseline wanders and the line drifts
            bx = cx - 25 / SS; by = cy + r.normal(0, 1.3) + math.tan(math.radians(drift)) * (cx - x) - org[1] / SS
            cov = np.zeros((H, W), np.float32)
            mm = cv2.resize(m, (m.shape[1] // SS, m.shape[0] // SS), interpolation=cv2.INTER_AREA)
            X0, Y0 = int(round(bx)), int(round(by)); h_, w_ = mm.shape
            xa, ya, xb, yb = max(0, X0), max(0, Y0), min(W, X0 + w_), min(H, Y0 + h_)
            if xb > xa and yb > ya:
                cov[ya:yb, xa:xb] = mm[ya - Y0:yb - Y0, xa - X0:xb - X0]
            out.append((np.clip(cov * 1.1, 0, 1), tf, tf + FPS / cps))
            tf += FPS / cps
            cx += tw / SS * r.uniform(0.93, 1.02)
        cx += 15 * size * r.uniform(0.7, 1.5); tf += FPS / cps * 0.6
    return out, (cx, cy)


def reveal(letters, f):
    """Write-on: each letter is drawn left to right over its own frames."""
    if not letters:
        return None
    H, W = letters[0][0].shape; cov = np.zeros((H, W), np.float32); xs = np.arange(W, dtype=np.float32)
    for c, a, b in letters:
        if f < a:
            break
        if f >= b:
            cov = np.maximum(cov, c); continue
        cols = np.nonzero(c.max(0) > 0.05)[0]
        if not len(cols):
            continue
        xe = cols[0] + (cols[-1] - cols[0] + 1) * (f - a) / (b - a)
        cov = np.maximum(cov, c * np.clip((xe - xs) / 2, 0, 1)[None, :])
    return cov


def letters_bbox(letters, i0, i1):
    c = np.max([l[0] for l in letters[i0:i1]], 0); ys, xs = np.nonzero(c > 0.1)
    return xs.min(), ys.min(), xs.max(), ys.max()


# ------------------------------------------------------------------ handmade pieces
def torn_slip(w, h, seed):
    r = np.random.default_rng(seed); m = np.zeros((h, w), np.float32); xs = np.arange(w)
    top = 7 + 6 * np.interp(xs, np.linspace(0, w, 20), r.normal(0, 0.6, 20)) + r.normal(0, 0.8, w)
    bot = h - 7 - 6 * np.interp(xs, np.linspace(0, w, 20), r.normal(0, 0.6, 20)) - r.normal(0, 0.8, w)
    lft = 3 + np.abs(r.normal(0, 1.2)); rgt = w - 3 - abs(r.normal(0, 4))
    for x in xs:
        if lft <= x <= rgt:
            m[int(max(0, top[x])):int(min(h, bot[x])), x] = 1
    rgb = paper(w, h, seed + 1, PAPER)
    rim = (cv2.dilate((1 - m).astype(np.uint8), np.ones((4, 4), np.uint8)) > 0) & (m > 0)
    rgb[rim] = np.minimum(255, rgb[rim] + 8)                                  # torn fibre edge reads lighter
    return rgb, cv2.GaussianBlur(m, (0, 0), 0.6)


def brass_pin(r=6, seed=0):
    S = 2 * r + 6; c = S / 2; yy, xx = np.mgrid[:S, :S].astype(np.float32)
    d = np.sqrt((xx - c) ** 2 + (yy - c) ** 2)
    a = np.clip(r + 1.0 - d, 0, 1)
    rgb = np.zeros((S, S, 3), np.float32) + np.array((70, 56, 38), np.float32)
    disc = np.clip(r - 0.8 - d, 0, 1)[..., None]
    rgb = rgb * (1 - disc) + np.array(BRASS, np.float32) * disc
    hi = np.clip(r * 0.45 - np.sqrt((xx - c + r * .35) ** 2 + (yy - c + r * .35) ** 2), 0, 1)[..., None]
    rgb = rgb * (1 - hi) + np.array((216, 188, 124), np.float32) * hi
    return rgb, a


def paper_wing():
    """The A1 wing (repair 2: redrawn as a wing, not a ladder).  A real cut piece of the cream stock, in two segments
    (root on the arm, tip on a crease pin) so the tip can lag and fold (#41).  Each segment is a curved membrane: a
    thick bowed leading-edge spar along the top, a cambered scalloped trailing edge, two or three faint creases fanning
    from the root (folded paper, not rungs), and on the tip a turned-down corner (fold line + the back of the sheet).
    Pivots unchanged: root pin (8,11), tip_pin (w-9,10).  Returns {'root':(rgb,a,pivots), 'tip':(rgb,a,pivots)}."""
    out = {}
    for name, L, Hh, seed in (("root", 92, 46, 61), ("tip", 78, 40, 62)):
        w, h = L + 16, Hh + 16
        rgb = paper(w, h, seed, PAPER)
        r = np.random.default_rng(seed)
        N = 24
        xs = np.linspace(8, w - 8, N)
        t = (xs - 8) / (w - 16)
        lead = 11 - 3.0 * np.sin(np.pi * t) * (1 if name == "root" else 0.6) + r.normal(0, 0.25, N)  # bowed spar
        if name == "root":
            depth = (h - 9) - 10 * t ** 1.6                       # deep at the root, narrowing outward
        else:
            depth = (h - 13) - 22 * t ** 1.3                      # tapering to a rounded tip
        scal = 3.2 * np.abs(np.sin(np.pi * t * (4 if name == "root" else 3.5)))   # feathered scallop
        trail = depth - scal
        top = list(zip(xs, lead)); bot = list(zip(xs[::-1], trail[::-1]))
        if name == "tip":                                     # rounded end
            ang = np.linspace(-np.pi / 2, np.pi / 2, 9)
            cy = (lead[-1] + trail[-1]) / 2; ry = (trail[-1] - lead[-1]) / 2
            end = [(w - 8 + 5 * np.cos(a), cy + ry * np.sin(a)) for a in ang]
            top = top + end
        poly = np.float32(top + bot)
        m = np.zeros((h * 4, w * 4), np.uint8); cv2.fillPoly(m, [np.int32(poly * 4)], 255, cv2.LINE_AA)
        a = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
        k = pen.Ink(w, h, seed + 5)
        k.line([(float(x), float(y)) for x, y in zip(xs, lead)], width=2.6, jit=0.25)         # the leading-edge spar (a pen-inked straw)
        k.line([(float(x), float(y)) for x, y in zip(xs, trail)], width=1.0, jit=0.3)          # cut edge
        nf = 3 if name == "root" else 2
        for q in range(1, nf + 1):                            # creases fanning from the root (faint, broken)
            tt = np.linspace(0.05, 0.9, 10); yy = np.interp(tt, t, lead) + (np.interp(tt, t, trail) - np.interp(tt, t, lead)) * (q / (nf + 1)) * (0.4 + 0.6 * tt)
            xx = 8 + (w - 16) * tt
            seg = [(float(x), float(y)) for x, y in zip(xx, yy)]
            k.line(seg[:6], width=0.7, jit=0.4); k.line(seg[7:], width=0.7, jit=0.4)
        if name == "tip":                                     # the turned-down corner: a fold line and the sheet's back
            fx0, fy0 = w - 30, float(np.interp((w - 30 - 8) / (w - 16), t, trail))
            fx1, fy1 = w - 12, float(np.interp((w - 12 - 8) / (w - 16), t, lead)) + 6
            tri = np.float32([(fx0, fy0), (fx1, fy1), (fx0 + 10, fy0 + 9)])
            mm = np.zeros((h * 4, w * 4), np.uint8); cv2.fillPoly(mm, [np.int32(tri * 4)], 255, cv2.LINE_AA)
            ta = cv2.resize(mm, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
            a = np.maximum(a, ta)
            rgb = rgb * (1 - ta[..., None] * 0.35) + np.array((214, 200, 184), np.float32) * ta[..., None] * 0.35
            k.line([(fx0, fy0), (fx1, fy1)], width=1.3, jit=0.2)
            k.line([(fx1, fy1), (fx0 + 10, fy0 + 9), (fx0, fy0)], width=0.9, jit=0.3)
        cov = k.coverage() * np.clip(a * 1.5, 0, 1)
        rgb = pen.put_ink(rgb, cov, ink=PENINK, seed=seed)
        piv = {"pin": [8.0, 11.0], "tip_pin": [w - 9.0, 10.0]}
        out[name] = (rgb, a, piv)
        Image.fromarray(np.dstack([rgb, a * 255]).astype(np.uint8), "RGBA").save(os.path.join(BD, f"paper_wing_{name}.png"))
    return out


def set_pieces():
    """Pen set dressing drawn as ink layers (panel-local px): wall, flowerbed, gatepost, turf, hill, fence, post."""
    S = {}
    def layer(seed, fn):
        k = pen.Ink(PWID, PHT, seed); fn(k, np.random.default_rng(seed)); return k.coverage()
    def ground(k, r, y=GROUND):
        k.curve([(6, y), (240, y + 2), (480, y - 1), (708, y + 1)], width=1.8)
        for u in r.uniform(16, 700, 24):
            k.line([(u, y + 1), (u + r.uniform(-4, 4), y - r.uniform(5, 11))], width=1.0, jit=0.4)
    def wall(k, r):
        x0, x1, top = 420, 600, 300
        k.line([(x0, top), (x1, top + 1)], width=1.9); k.line([(x0, top), (x0 - 1, GROUND)], width=1.9); k.line([(x1, top + 1), (x1 + 1, GROUND)], width=1.9)
        for row in range(5):
            yy = top + 26 * (row + 1)
            if yy < GROUND - 4: k.line([(x0 + 2, yy), (x1 - 2, yy + r.normal(0, 1))], width=1.0, jit=0.5)
            for xx in np.arange(x0 + (24 if row % 2 else 8), x1 - 8, 46):
                k.line([(xx, yy - 26 + 3), (xx + r.normal(0, 1), yy - 2)], width=1.0, jit=0.4)
    def flowerbed(k, r, x0=170, x1=380):
        k.curve([(x0, GROUND), (x0 + 30, GROUND - 14), ((x0 + x1) / 2, GROUND - 20), (x1 - 30, GROUND - 13), (x1, GROUND)], width=1.6)
        for u in np.linspace(x0 + 20, x1 - 20, 9):
            h_ = r.uniform(26, 44); k.line([(u, GROUND - 14), (u + r.normal(0, 3), GROUND - h_)], width=1.1, jit=0.6)
            k.ellipse(u + r.normal(0, 2), GROUND - h_ - 5, 5, 4, width=1.2, jit=0.3)
    def gatepost(k, r, u=80, top=330):
        for dx in (-7, 7): k.line([(u + dx, top), (u + dx * 1.1, GROUND)], width=1.8, jit=0.5)
        k.line([(u - 10, top), (u + 10, top - 1)], width=1.8, jit=0.3)
    def hill(k, r):
        k.curve([(6, GROUND), (200, GROUND - 4), (420, GROUND - 60), (600, GROUND - 150), (708, GROUND - 190)], width=1.8)
        for u in r.uniform(20, 690, 20):
            y = np.interp(u, [6, 200, 420, 600, 708], [GROUND, GROUND - 4, GROUND - 60, GROUND - 150, GROUND - 190])
            k.line([(u, y), (u + r.uniform(-3, 3), y - r.uniform(5, 10))], width=1.0, jit=0.4)
    def fence(k, r, u=70, top=340):
        for dx in (-5, 5): k.line([(u + dx, top + 2), (u + dx * 1.2, GROUND + 1)], width=1.7, jit=0.6)
        k.line([(u - 8, top + 1), (u + 8, top)], width=1.7, jit=0.4)
        k.line([(u - 8, top + 40), (u - 60, top + 44)], width=1.3, jit=0.6)
    S["s1p1"] = layer(701, lambda k, r: (ground(k, r), wall(k, r), flowerbed(k, r), gatepost(k, r)))
    S["s1p2"] = layer(702, lambda k, r: (ground(k, r), gatepost(k, r, 90, 340)))
    S["s1p3"] = layer(703, lambda k, r: None)
    S["s2p1"] = layer(704, lambda k, r: (hill(k, r), fence(k, r)))
    S["s2p2"] = layer(705, lambda k, r: (ground(k, r), fence(k, r)))
    S["s2p3"] = layer(706, lambda k, r: (ground(k, r), flowerbed(k, r, 420, 640)))
    for n, c in S.items():
        Image.fromarray(np.dstack([np.zeros(c.shape + (3,), np.uint8) + np.array(PENINK, np.uint8), (c * 255).astype(np.uint8)]), "RGBA").save(os.path.join(BD, f"set_{n}.png"))
    return S


SETS = set_pieces()
WING = paper_wing()
PIN = brass_pin(6)


def build_sheet(n):
    """Planche n (1 or 2): cream sheet, duskier margin, mirrored show-through of the facing page, three stacked
    punched panels with their pen set, graphite headers and page number."""
    pg = paper(PW, PH, 10 + n, PAPER)
    xx = np.arange(PW, dtype=np.float32)
    mg = np.clip((90 - xx) / 60, 0, 1)[None, :, None]
    pg = pg * (1 - mg) + (pg / PAPER * MARGIN) * mg
    # show-through: the facing page's hand and panels, mirrored, soft (paper fibres scatter it)
    gk = pen.Ink(PW, PH, 300 + n); rg = np.random.default_rng(310 + n)
    lines = ["Planche", "Il s'est fait une aile", "en papier.  pof", "Ensuite un moulin", "à élastique", "clac", "Enfin les grandes ailes",
             "Il court face au vent", "Donc il se pose", "Un peu vite", "mais au bon endroit"]
    for i, s_ in enumerate(lines):
        pen.hand(gk, s_, 140 + rg.uniform(0, 80), 200 + i * 135, size=1.5, width=2.6, rng=rg)
    for y0 in PYS:
        X0 = PW - PX - PWID
        gk.line([(X0, y0), (X0 + PWID, y0 + 2)], width=2.4); gk.line([(X0 + PWID, y0 + 2), (X0 + PWID, y0 + PHT)], width=2.4)
        gk.line([(X0 + PWID, y0 + PHT), (X0, y0 + PHT)], width=2.4); gk.line([(X0, y0 + PHT), (X0, y0)], width=2.4)
    gc = cv2.GaussianBlur(gk.coverage()[:, ::-1], (0, 0), 2.2)
    comp(pg, GHOST, np.clip(cv2.GaussianBlur(gc, (0, 0), 1.5) * 0.42, 0, 0.32))
    k = pen.Ink(PW, PH, 320 + n)
    for i, y0 in enumerate(PYS):
        inner = np.zeros((PH, PW), np.float32); inner[y0 + 2:y0 + PHT - 2, PX + 2:PX + PWID - 2] = 1
        comp(pg, pg / PAPER * PANEL, inner)
        x0 = PX
        k.line([(x0, y0), (x0 + PWID, y0 + 1)], width=2.6, jit=1.0); k.line([(x0 + PWID, y0 + 1), (x0 + PWID + 1, y0 + PHT)], width=2.6, jit=1.0)
        k.line([(x0 + PWID + 1, y0 + PHT), (x0 - 1, y0 + PHT - 1)], width=2.6, jit=1.0); k.line([(x0 - 1, y0 + PHT - 1), (x0, y0)], width=2.6, jit=1.0)
        cov = SETS[f"s{n}p{i + 1}"]
        k.a[y0 * pen.SS:(y0 + PHT) * pen.SS, PX * pen.SS:(PX + PWID) * pen.SS] = np.maximum(
            k.a[y0 * pen.SS:(y0 + PHT) * pen.SS, PX * pen.SS:(PX + PWID) * pen.SS], cv2.resize(cov, (PWID * pen.SS, PHT * pen.SS)))
    pg = pen.put_ink(pg, k.coverage(), ink=PENINK, seed=330 + n)
    for y0 in PYS:                                     # the punched dot: a real hole showing the dark board below
        yy, xx2 = np.ogrid[:PH, :PW]; d = np.sqrt((xx2 - (PX + 26)) ** 2 + (yy - (y0 + 24)) ** 2)
        comp(pg, (58, 48, 40), np.clip(11.5 - d, 0, 1))
        comp(pg, (90, 78, 66), np.clip(5 - np.sqrt((xx2 - (PX + 23)) ** 2 + (yy - (y0 + 21)) ** 2), 0, 1) * 0.6)
    g = pen.Ink(PW, PH, 340 + n); rgr = np.random.default_rng(350 + n)
    heads = {1: ["BB-01   1,0 - 8,0 s   l'aile de papier", "BB-02/03   8,0 - 16,0 s   le moulin", "BB-04/05   (réservé)"],
             2: ["BB-07   18,0 - 21,0 s   l'élan", "BB-08   21,0 - 24,0 s   le décrochage", "BB-09   24,0 - 27,5 s   la chute"]}[n]
    for i, y0 in enumerate(PYS):
        pen.hand(g, heads[i], PX + 60, y0 - 16, size=0.62, width=1.1, rng=rgr)
    pen.hand(g, f"Bang Bang  -  planche {n}", PX, 60 if n else 60, size=0.0001, width=0.1, rng=rgr)
    pen.hand(g, str(n), PW - 120, 80, size=0.9, width=1.4, rng=rgr)
    pg = pen.put_ink(pg, g.coverage() * 0.8, ink=GRAPH, seed=360 + n, bleed=0.4)
    return pg


# ------------------------------------------------------------------ pieces (scaled), rig and transforms
SCALE = {"glider": 0.40, "legs": 0.40, "glider_core": 0.40, "glider_wingR": 0.40, "pilot_torso": 0.62, "pilot_legs": 0.62,
         "pilot_arm": 0.62, "heli_top": 0.62, "heli_shaft": 0.62, "heli_bottom": 0.62, "pie_body": 0.32, "pie_head": 0.32,
         "fly_body": 0.36, "fly_wingL": 0.36, "fly_wingR": 0.36, "paper_wing_root": 1.0, "paper_wing_tip": 1.0}


def load_piece(name, file=None, pivots=None):
    s = SCALE[name]
    if file is None:
        im = cv2.imread(os.path.join(BD, MAN["pieces"][name]["file"].split("/")[-1]), cv2.IMREAD_UNCHANGED)[..., [2, 1, 0, 3]].astype(np.float32)
        pv = MAN["pieces"][name]["pivots"]
    else:
        im = file; pv = pivots
    w = max(1, int(round(im.shape[1] * s))); h = max(1, int(round(im.shape[0] * s)))
    a = cv2.resize(im[..., 3] / 255, (w, h), interpolation=cv2.INTER_AREA)
    rgb = cv2.resize(im[..., :3] * (im[..., 3:] / 255), (w, h), interpolation=cv2.INTER_AREA)
    sx, sy = w / im.shape[1], h / im.shape[0]
    return {"name": name, "a": a, "rgb": rgb, "pv": {k: np.array([v[0] * sx, v[1] * sy], np.float32) for k, v in pv.items()}, "w": w, "h": h}


P = {n: load_piece(n) for n in ["glider", "legs", "glider_core", "glider_wingR", "pilot_torso", "pilot_arm", "heli_top", "heli_shaft",
                                 "heli_bottom", "pie_body", "pie_head", "fly_body", "fly_wingL", "fly_wingR"]}
P["pilot_legs"] = load_piece("pilot_legs", cv2.imread(os.path.join(BD, "legs.png"), cv2.IMREAD_UNCHANGED)[..., [2, 1, 0, 3]].astype(np.float32), MAN["pieces"]["legs"]["pivots"])
for nm in ("root", "tip"):
    rgb, a, pv = WING[nm]
    P["paper_wing_" + nm] = load_piece("paper_wing_" + nm, np.dstack([rgb, a * 255]).astype(np.float32), pv)

# joints: child, parent, pin name on the parent, pin name on the child, limits (child angle relative to parent, deg)
JOINTS = [
    ("legs", "glider", "hip", "hip", (-85, 45)),
    ("glider_wingR", "glider_core", "wing_root_R", "root", (-3, 62)),   # repair 2: the stop is the intact spar; it snaps at f605
    ("pilot_legs", "pilot_torso", "hip", "hip", (-90, 45)),
    ("pilot_arm", "pilot_torso", "shoulder_R", "shoulder", (-45, 75)),
    ("paper_wing_root", "pilot_arm", "hand", "pin", (-200, 200)),
    ("paper_wing_tip", "paper_wing_root", "tip_pin", "pin", (-20, 165)),
    ("heli_top", "heli_shaft", "top_hub", "hub", (-1, 1)),
    ("heli_bottom", "heli_shaft", "bottom_hub", "hub", (-1, 1)),
    ("pie_head", "pie_body", "neck", "neck", (-40, 55)),
    ("fly_wingL", "fly_body", "shoulder_L", "shoulder", (-75, 45)),
    ("fly_wingR", "fly_body", "shoulder_R", "shoulder", (-45, 75)),
]
JD = {c: (p, pp, cp, lim) for c, p, pp, cp, lim in JOINTS}


def Mx(piece, pin, P_world, ang, sx=1.0, sy=1.0):
    """Affine (2x3) mapping piece px -> world so that piece pin lands at P_world, rotated ang deg (+ = clockwise on screen = nose-up
    for the left-facing glider; legs + = feet swing forward/left), with local scale (foreshortening of a turning blade / flapping wing)."""
    a = math.radians(ang); c, s = math.cos(a), math.sin(a)
    R = np.array([[c, -s], [s, c]], np.float32) @ np.diag([sx, sy]).astype(np.float32)
    t = np.asarray(P_world, np.float32) - R @ piece["pv"][pin]
    return np.hstack([R, t[:, None]])


def ap(M, p):
    return M[:, :2] @ np.asarray(p, np.float32) + M[:, 2]


def pose_chain(root, root_pin, root_P, root_ang, rel, scl=None, mirror=False):
    """Forward kinematics (#32 in passing): returns {piece: (M, world_angle)} for the root and its descendants listed in rel."""
    scl = scl or {}
    out = {root: (Mx(P[root], root_pin, root_P, root_ang, *scl.get(root, (1, 1))), root_ang)}
    changed = True
    while changed:
        changed = False
        for ch, r_ang in rel.items():
            if ch in out: continue
            par, ppin, cpin, lim = JD[ch]
            if par in out:
                Mp, pa = out[par]; Pw = ap(Mp, P[par]["pv"][ppin]); wa = pa + r_ang
                out[ch] = (Mx(P[ch], cpin, Pw, wa, *scl.get(ch, (1, 1))), wa); changed = True
    return out


# ------------------------------------------------------------------ secondary dynamics (#41): semi-implicit Euler at 240 Hz
DT = 1 / 240.0; SUB = 10                     # 10 substeps per film frame


def spring_sim(f0, f1, drive, k, zeta, x0=0.0, v0=0.0, impulses=None, lim=None):
    """Angular spring-damper x'' = -k (x - target(f)) - c x' + inertial(f), semi-implicit Euler, 240 Hz.
    drive(f) -> (target, inertial_accel).  impulses {frame: dv}.  lim (lo, hi): joint stop (inelastic).
    Returns {frame: x} for integer frames f0..f1."""
    c = 2 * zeta * math.sqrt(k); x, v = x0, v0; out = {}; f = float(f0); hits = 0
    while f <= f1 + 1e-9:
        fi = int(round(f))
        if abs(f - fi) < 1e-9:
            out[fi] = x
            if impulses and fi in impulses: v += impulses[fi]
        tgt, ia = drive(f)
        v += (-k * (x - tgt) - c * v + ia) * DT
        x += v * DT
        if lim is not None and not (lim[0] <= x <= lim[1]):
            x = min(max(x, lim[0]), lim[1]); v = 0.0; hits += 1
        f += 1.0 / SUB
    out["_stops"] = hits
    return out


def smooth(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


# ---- A3 glider primary motion (panel-local hip u,v; pitch th deg nose-up; nose points LEFT, running right-to-left)
def glider_primary(f):
    if f < 504:                                     # BB-07: run down the hill, lift-off f490 (panel s2p1)
        s = (f - 432) / 72.0; u = 610 - 400 * s
        hill_v = np.interp(u, [6, 200, 420, 600, 708], [GROUND, GROUND - 4, GROUND - 60, GROUND - 150, GROUND - 190])
        lift = 0 if f < 490 else 2.2 * (f - 490) ** 1.4
        v = hill_v - 62 - lift; th = 3 + 2 * math.sin(f * 0.9) * (f < 490) + (2 * smooth((f - 490) / 14))
        return "s2p1", u, v, th, (lift + 62 - 62 if f >= 490 else 0) + 4
    if f < 576:                                     # BB-08 (panel s2p2): pitch 5->35 over f504-540, x-speed -> 0 by f540
        T = 36.0; v0 = 9.0
        if f <= 540:
            s = (f - 504) / T; u = 520 - v0 * T * (s - s ** 2 + s ** 3 / 3)        # du/df = -v0 (1-s)^2
        else:
            u = 520 - v0 * T / 3
        v = 250 - 30 * smooth((f - 504) / 36)      # repair 2: at rest from f540
        th = 5 + 30 * min(1.0, max(0.0, (f - 504) / 36)) ** 2.71
        if f > 564:                                 # repair 2: hang f540-564 (1 s on screen), then the tail-first slide
            d = f - 564; u += 0.40 * d * d; v += 0.18 * d * d; th = 35 - 9 * smooth(d / 12)
        return "s2p2", u, v, th, GROUND - v
    # BB-09 (panel s2p3): tail-first slide steepens, nose drops through the horizon f590, impact f605
    if f < 605:
        s = (f - 576) / 29.0
        u = 260 + 150 * s ** 1.3; v = 170 + (GROUND - 30 - 170) * s ** 1.7
        th = 26 - 40 * smooth((f - 576) / 26)
        return "s2p3", u, v, th, max(0.0, GROUND - 30 - v)
    u = 410; v = GROUND - 30; th = -14 + 6 * math.exp(-(f - 605) / 3.0) * math.cos((f - 605) * 0.9)
    return "s2p3", u, v, th, 0.0


def body_kin(prim, f, h=0.5):
    p0, u0, v0, t0, _ = prim(f - h); _, u1, v1, t1, _ = prim(f); p2, u2, v2, t2, _ = prim(f + h)
    if p0 != p2:                                     # repair 2: a cut between panels is not an acceleration (fixes the f576 leg pop)
        return np.array([0.0, 0.0]), 0.0
    sc = FPS * FPS / (h * h)
    return np.array([(u2 - 2 * u1 + u0), (v2 - 2 * v1 + v0)]) * sc, (t2 - t0) / (2 * h) * FPS


LEG_KICK = {540: 6.0}            # repair 2: rad/s added to the hip pendulum when the body stops dead (the legs fly on)


def legs_pendulum(prim, f0, f1, hold_from=None, run=None, kicks=None):
    """Hip pin pendulum: phi = leg angle in WORLD (deg, 0 = hanging, + = swinging forward/left).
    phi'' = [-(g - a_y) sin phi + a_x' cos phi]/L - c (phi' - theta'), with joint stops from the rig."""
    g, L = 9.81 * 60, 18.0; c = 4.2
    pr = (lambda f: prim(min(f, hold_from))) if hold_from else prim
    phi, w = 0.0, 0.0; out = {}; f = float(f0); stops = 0
    lim = JD["legs"][3]
    while f <= f1 + 1e-9:
        fi = int(round(f))
        if abs(f - fi) < 1e-9:
            out[fi] = math.degrees(phi)
            if kicks and fi in kicks: w += kicks[fi]
        acc, thd = body_kin(pr, f)
        ax = -acc[0]                                     # forward is -u
        drive = 0.0
        if run and run[0] <= f < run[1]:                 # running: the legs are driven, not free
            tgt = math.radians(28 * (1 if (int(f) // 4) % 2 else -1))
            drive = -60 * (phi - tgt)
        cc = 9.0 if f >= 605 else (8.6 if 540 <= f < 564 else c)   # hang: the legs swing on a stiff hip pin; after the crash they drag
        al = (-(g - (-acc[1])) * math.sin(phi) + ax * math.cos(phi)) / L - cc * (w - math.radians(thd)) + drive
        w += al * DT; phi += w * DT
        th = pr(f)[3]
        rel = math.degrees(phi) - th
        if not (lim[0] <= rel <= lim[1]):
            rel = min(max(rel, lim[0]), lim[1]); phi = math.radians(rel + th); w = math.radians(thd); stops += 1
        f += 1.0 / SUB
    out["_stops"] = stops
    return out


LEGS = legs_pendulum(glider_primary, 432, 719, run=(432, 490), kicks=LEG_KICK)
LEGS_HOLD = legs_pendulum(glider_primary, 432, 719, hold_from=540, run=(432, 490), kicks=LEG_KICK)
# wing-root droop at impact: rest goes 0 -> 12 deg (the spar cracks), impulse at f605, zeta 0.6 (one visible bounce)
# repair 2: the spar SNAPS at impact: the outer wing whips down to 58 deg and is held there 3 drawings (f605-610), then sags
# back onto the broken root at 40 deg with one bounce.  Once broken, the joint stop is gone (limit -3..62).
DROOP_REST = 40.0
_DR = spring_sim(611, 719, lambda f: (DROOP_REST, 0.0), k=700.0, zeta=0.45, x0=58.0, lim=(-3, 62))
DROOP = {f: (0.0 if f < 605 else (58.0 if f < 611 else _DR[f])) for f in range(576, 720)}
DROOP["_stops"] = _DR["_stops"]
SNAP_F = (605, 611)


# ---- A1 (BB-01, s1p1): the pilot alone on the wall, three flaps, hop at f134, sits on the flowerbed at f154
def pilot_a1(f):
    if f < 134:
        u, v = 520, 300 - 2; tor = 0.0
    elif f < 154:
        s = (f - 134) / 20.0; u = 520 - 230 * s; v = (300 - 2) - 40 * math.sin(math.pi * s) + (GROUND - 22 - 298) * s ** 2; tor = 8 * math.sin(math.pi * s)
    else:
        u, v = 290, GROUND - 22; tor = -6 * math.exp(-(f - 154) / 4.0)
    return u, v, tor


def arm_a1(f):
    if 40 <= f < 130:
        s = (f - 40) / 30.0; return -5 + 39 * math.sin(2 * math.pi * s)
    if 134 <= f < 154: return 55
    return -10 if f < 154 else 20


ARM_W = {fi: arm_a1(fi) for fi in range(0, 720)}
def arm_acc(f):
    return (arm_a1(f + 0.5) - 2 * arm_a1(f) + arm_a1(f - 0.5)) * 4 * FPS * FPS
# paper wing tip: lags the arm (inertial drive = -arm angular accel), crease on the 3rd flap (rest 0 -> 150 deg)
TIP = spring_sim(24, 200, lambda f: (150.0 if f >= 106 else 0.0, -0.9 * arm_acc(f)), k=420.0, zeta=0.18, lim=JD["paper_wing_tip"][3])
A1LEGS = spring_sim(24, 200, lambda f: (-80.0 if f >= 150 else (25.0 if 134 <= f < 150 else 0.0), 0.0), k=500.0, zeta=0.3, lim=JD["pilot_legs"][3])


# ---- A2 (BB-02/03, s1p2): winding f192-252, release f254, rise ~120 px, snap f312, drop to turf f331
def heli_a2(f):
    hand_u, hand_v = 330, 250
    if f < 254:
        return hand_u, hand_v, 0.0
    if f < 312:
        s = (f - 254) / 58.0; return hand_u + 20 * s, hand_v - 120 * (1 - (1 - s) ** 2), 0.0
    if f < 331:
        s = (f - 312) / 19.0; return hand_u + 20 + 40 * s, hand_v - 120 + (GROUND - 40 - (hand_v - 120)) * s * s, 70 * s
    return hand_u + 60, GROUND - 40 + 4 * math.exp(-(f - 331) / 3) * math.cos((f - 331)), 88


def rotor_phase(f):
    if f < 192: return 0.0
    if f < 252: return 144.0 * ((f - 192) // 2)                  # winding, stepped on 2s; 12 turns -> tally
    if f < 312:
        w0 = 70.0; tau = 40.0; return 144 * 30 + w0 * tau * (1 - math.exp(-(f - 252) / tau))
    return 144 * 30 + 70 * 40 * (1 - math.exp(-60 / 40)) + 20 * (1 - math.exp(-(f - 312) / 6))


BAND = spring_sim(300, 384, lambda f: (0.0, 0.0), k=700.0, zeta=0.15, impulses={312: 900.0})   # snapped band whip amplitude (px)


# ---- the magpie (PIE)
def pie_s1(f):
    """perched on the gatepost in s1p1, head in held steps (bird-like jerks) tracking the man."""
    steps = [(24, -10), (60, 5), (100, 18), (134, 30), (150, 42), (170, 35)]
    ha = [a for t, a in steps if f >= t][-1] if f >= 24 else -10
    return 80, 330, -18, ha


def fly_s2(f):
    """BB-08: flies level past him right-to-left f538-560, flares f560-568, lands on the post f568-580.
    BB-09: re-enters f620, lands beside the wreck f638, two-hop settle, one peck f652."""
    flap = [-55, -20, 25, -20][(int(f) // 2) % 4]
    if f < 554: return None          # repair 2: enters after the hang's first second, high over the glider (whoosh peak f557)
    if f <= 566:
        s = (f - 554) / 12.0; return ("fly", "s2p2", 760 - 600 * s, 52 + 50 * s * s, 18, flap)
    if f <= 571:
        s = (f - 566) / 5.0; return ("fly", "s2p2", 160 - 70 * s, 102 + 120 * s, 18 + 50 * s, -60)      # flare: nose up, wings forward
    if f < 576:
        s = smooth((f - 571) / 5.0); return ("perch", "s2p2", 90 - 20 * s, 222 + (340 - 2 - 222) * s, -18 + 10 * (1 - s), 10)
    if f < 620: return ("perch", "s2p2", 70, 338, -18, 20)
    if f <= 632:
        s = (f - 620) / 12.0; return ("fly", "s2p3", 720 - 160 * s, 260 + 40 * s, 25, flap)
    if f <= 638:
        s = (f - 632) / 6.0; return ("fly", "s2p3", 560 - 30 * s, 300 + 40 * s, 25 + 45 * s, -60)
    hop = 0
    for t in (642, 648):
        if t <= f < t + 4: hop = 10 * math.sin(math.pi * (f - t) / 4)
    du = 0 if f < 642 else (-8 if f < 648 else -16)
    peck = 30 if 652 <= f < 656 else 0
    return ("perch", "s2p3", 520 + du, GROUND - 40 - hop, -10, 5 + peck)


# ------------------------------------------------------------------ exposure sheet (on 2s)
CAM_WIDE = (PW / 2, PH / 2, 540 / (PH + 80))


def cam_panel(i, frac):
    """camera on panel i so the panel fills `frac` of frame width; slip column kept in frame at right."""
    z = frac * 960 / PWID
    fw = 960 / z
    cx = PX - 18 + fw / 2; cy = PYS[i] + PHT / 2 + 10
    return cx, cy, z


def lerp_cam(a, b, s):
    s = smooth(s); return tuple(a[k] + (b[k] - a[k]) * s for k in range(3))


def camera(f):
    W_ = CAM_WIDE
    if f < 24: return 1, W_, "wide"
    if f < 192: return 1, lerp_cam(W_, cam_panel(0, 0.64), (f - 24) / 30), "push panel 1"
    if f < 384: return 1, lerp_cam(cam_panel(0, 0.64), cam_panel(1, 0.64), (f - 192) / 14), "wipe/slide to panel 2"
    if f < 432:
        if f < 396: return 1, lerp_cam(cam_panel(1, 0.64), W_, (f - 384) / 12), "pull out"
        if f < 420: return (1 if f < 408 else 2), W_, "page turn"
        return 2, lerp_cam(W_, cam_panel(0, 0.64), (f - 420) / 12), "push panel 1"
    if f < 504: return 2, cam_panel(0, 0.64), "hold panel 1"
    if f < 576: return 2, lerp_cam(cam_panel(1, 0.64), cam_panel(1, 0.72), (f - 504) / 40), "push-in panel 2"
    if f < 660: return 2, lerp_cam(cam_panel(2, 0.66), cam_panel(2, 0.68), (f - 576) / 84), "panel 3"
    if f < 684: return 2, lerp_cam(cam_panel(2, 0.68), W_, (f - 660) / 18), "pull out"
    return 2, W_, "wide"


KEYPOSE = {"s2p1": 482, "s2p2": 548, "s2p3": 656, "s1p1": 170, "s1p2": 340}


def scene(f):
    """All puppet placements for drawing f: list of (panel, piece, M(2x3, panel-local), height_px).  Panels other than
    the active one hold their key pose (still form) once the board has been played."""
    out = []
    def add(panel, chain, height, order):
        for nm in order:
            if nm in chain: out.append((panel, nm, chain[nm][0], height))
    def glider_at(ff):
        panel, u, v, th, hgt = glider_primary(ff)
        phi = (LEGS if ff < 719 else LEGS)[min(719, int(ff))]
        lo, hi = JD["legs"][3]; rel = {"legs": min(hi, max(lo, phi - th))}
        if ff >= 605:
            ch = pose_chain("glider_core", "hip", (u, v), th, {"legs": rel["legs"], "glider_wingR": DROOP[min(719, int(ff))]})
            add(panel, ch, hgt, ["legs", "glider_wingR", "glider_core"])
        else:
            ch = pose_chain("glider", "hip", (u, v), th, rel); add(panel, ch, hgt, ["legs", "glider"])
        return panel
    def pilot_at(ff, with_heli):
        u, v, tor = pilot_a1(ff) if not with_heli else (380, GROUND - 22 - 64, 0.0)
        panel = "s1p1" if not with_heli else "s1p2"
        if not with_heli:
            rel = {"pilot_legs": A1LEGS[min(200, max(24, int(ff)))], "pilot_arm": arm_a1(ff), "paper_wing_root": -60, "paper_wing_tip": TIP[min(200, max(24, int(ff)))]}
        else:
            rel = {"pilot_legs": 0, "pilot_arm": 70 if ff < 254 else (40 if ff < 300 else 10)}
        ch = pose_chain("pilot_torso", "hip", (u, v), tor, rel)
        add(panel, ch, 0, ["pilot_legs", "paper_wing_root", "paper_wing_tip", "pilot_torso", "pilot_arm"])
        if with_heli:
            hu, hv, ha = heli_a2(ff)
            if ff < 254:
                Ma = ch["pilot_arm"][0]; hand = ap(Ma, P["pilot_arm"]["pv"]["hand"]); hu, hv = hand[0], hand[1] - 2
            ph = math.radians(rotor_phase(ff))
            ch2 = pose_chain("heli_shaft", "grip", (hu, hv), ha, {"heli_top": 0, "heli_bottom": 0},
                             scl={"heli_top": (max(0.12, abs(math.cos(ph))), 1), "heli_bottom": (max(0.12, abs(math.cos(-ph * 0.9))), 1)})
            add(panel, ch2, max(0.0, GROUND - 40 - hv), ["heli_bottom", "heli_shaft", "heli_top"])
    def pie_perched(panel, u, v, ang, head):
        ch = pose_chain("pie_body", "feet", (u, v), ang, {"pie_head": head})
        add(panel, ch, max(0.0, GROUND - v - 0), ["pie_head", "pie_body"])
    def pie_flying(panel, u, v, ang, flap):
        sL = max(0.25, math.cos(math.radians(flap)));
        ch = pose_chain("fly_body", "centre", (u, v), ang - 40, {"fly_wingL": flap * 0.6, "fly_wingR": -flap * 0.4},
                        scl={"fly_wingL": (1, sL), "fly_wingR": (1, max(0.3, sL))})
        add(panel, ch, max(0.0, GROUND - v), ["fly_wingR", "fly_body", "fly_wingL"])
    sheet = 1 if f < 408 else 2
    if sheet == 1:
        pilot_at(f if 24 <= f < 192 else KEYPOSE["s1p1"], False) if f >= 24 else None
        if f >= 24: pie_perched("s1p1", *pie_s1(min(f, 191)))
        if f >= 192: pilot_at(min(f, 383), True); pie_perched("s1p2", 70, GROUND - 2, -12, 35 if 254 <= f < 312 else (50 if f >= 312 else 0))
    else:
        glider_at(f if 432 <= f < 504 else KEYPOSE["s2p1"])
        glider_at(f if 504 <= f < 576 else KEYPOSE["s2p2"])
        glider_at(f if 576 <= f < 660 else KEYPOSE["s2p3"])
        b = fly_s2(f if 554 <= f else 0)
        held = []
        if b is None or b[1] != "s2p2":
            held.append(fly_s2(600) if f >= 576 else None)   # repair 2: no bird on the post before it has flown there (it enters f554)
        for bb in [b] + held:
            if bb is None: continue
            kind, panel, u, v, ang, x = bb
            if kind == "fly": pie_flying(panel, u, v, ang, x)
            else: pie_perched(panel, u, v, ang, x)
        if f >= 660 or (420 <= f < 576):
            bb = fly_s2(656); pie_perched(bb[1], bb[2], bb[3], bb[4], bb[5])
    return sheet, out


def panel_origin(panel):
    i = int(panel[-1]) - 1; return PX, PYS[i]


# ------------------------------------------------------------------ slips (the bird's), annotations
SLIPS = {}   # id -> dict(rgb, a, letters, x, y, ang, t_paste, strike)


def make_slip(sid, text, x, y, t_paste, w=270, size=0.66, seed=0, ang=0.0, extra=None, cps=12.5):
    lines = 1 + len(text) // 15
    h = int(30 + 60 * size * max(1, lines))
    rgb, a = torn_slip(w, h, 900 + seed)
    letters, _ = hand2(w, h, text, 18, 34 + 40 * size, size=size, width=1.25, seed=910 + seed, maxw=w - 36, cps=cps, t0=t_paste + 4)
    SLIPS[sid] = {"rgb": rgb, "a": a, "letters": letters, "x": x, "y": y, "ang": ang, "t": t_paste, "text": text, "extra": extra or []}
    return SLIPS[sid]


# BB-08's slips (the test shot); the other boards' slips are the writer unit's (cues.json); exposure records their paste frames
s5 = make_slip("S5", "Il lève le nez pour monter", TX0 + 4, PYS[1] + 30, 474, w=250, size=0.92, seed=5, ang=1.0, cps=14.0)
# where 'monter' sits on the slip (the last 6 letters)
mx0, my0, mx1, my1 = letters_bbox(s5["letters"], len(s5["letters"]) - 6, len(s5["letters"]))
fix_letters, _ = hand2(s5["a"].shape[1], s5["a"].shape[0], "s'arrêter", mx0 - 6, my0 - 4, size=0.72, width=1.4, seed=947, cps=12.0, t0=531)
s5["fix"] = fix_letters
stk = pen.Ink(s5["a"].shape[1], s5["a"].shape[0], 948); stk.line([(mx0 - 5, (my0 + my1) / 2 + 3), (mx1 + 6, (my0 + my1) / 2 - 2)], width=2.2, jit=0.5, press=0.3)
s5["strike"] = stk.coverage()
STRIKE_F = 528
make_slip("S5b", "Moi aussi, quand je veux me poser.", TX0 + 10, PYS[1] + 285, 552, w=250, size=0.86, seed=6, ang=-1.4)
GLOSS_L, _ = hand2(330, 50, "he lifts his nose to stop", 6, 32, size=0.42, width=1.0, seed=960, cps=16, t0=552)


def annotations():
    _, u, v, th, _ = glider_primary(548)
    ch = pose_chain("glider", "hip", (u, v), th, {"legs": 0})
    M = ch["glider"][0]; hip = (u, v)
    nose = ap(M, P["glider"]["pv"]["nose"]); wing = ap(M, P["glider"]["pv"]["wing_root_R"])
    ka = pen.Ink(PWID, PHT, 501); pen.hand(ka, "A", wing[0] + 10, wing[1] + 40, size=0.9, width=1.7, rng=np.random.default_rng(502))
    kb = pen.Ink(PWID, PHT, 503); pen.hand(kb, "B", nose[0] - 10, nose[1] - 18, size=0.9, width=1.7, rng=np.random.default_rng(504))
    gh = pen.Ink(PWID, PHT, 505)
    gh.line([(hip[0] - 190, hip[1]), (hip[0] - 6, hip[1])], width=1.0, jit=0.3, dash=7)
    R = 120; gh.ellipse(hip[0], hip[1], R, R, a0=180, a1=180 + 35, width=1.0, jit=0.3)
    pen.hand(gh, "35°", hip[0] - R - 56, hip[1] - 26, size=0.5, width=0.9, rng=np.random.default_rng(507))
    return ka.coverage(), kb.coverage(), gh.coverage()


ANN_A, ANN_B, ANN_G = annotations()


# ------------------------------------------------------------------ rendering one frame (page-space crop -> 960x540)
SHEETS = {}


def sheet(n):
    if n not in SHEETS:
        SHEETS[n] = build_sheet(n)
        Image.fromarray(np.clip(SHEETS[n], 0, 255).astype(np.uint8)).save(os.path.join(BD, f"sheet{n}.png"))
    return SHEETS[n]


TESTLOG = {"drift": [], "limits": []}


def render(f):
    fa = f - (f % 2)                                      # on 2s
    sh_n, cam, _ = camera(fa)
    cx, cy, z = cam
    fw, fh = 960 / z, 540 / z
    X0, Y0 = int(math.floor(cx - fw / 2)) - 2, int(math.floor(cy - fh / 2)) - 2
    Wc, Hc = int(fw) + 6, int(fh) + 6
    # page on the desk
    can = np.zeros((Hc, Wc, 3), np.float32) + DESK
    S = sheet(sh_n)
    xa, ya, xb, yb = max(0, X0), max(0, Y0), min(PW, X0 + Wc), min(PH, Y0 + Hc)
    if xb > xa and yb > ya:
        # soft drop shadow of the sheet on the desk
        dm = np.zeros((Hc, Wc), np.float32); dm[max(0, -Y0 + 8):PH - Y0 + 8, max(0, -X0 + 6):PW - X0 + 6] = 1
        comp(can, SHADOW, cv2.GaussianBlur(dm, (0, 0), 6) * 0.18)
        can[ya - Y0:yb - Y0, xa - X0:xb - X0] = S[ya:yb, xa:xb]
    # BB-08 annotations by the board artist once the pose is held
    ox, oy = PX - X0, PYS[1] - Y0
    def put_cov(cov, ink, alpha, x, y):
        h, w = cov.shape; x, y = int(x), int(y)
        xa_, ya_, xb_, yb_ = max(0, x), max(0, y), min(Wc, x + w), min(Hc, y + h)
        if xb_ > xa_ and ya_ < yb_:
            sub = can[ya_:yb_, xa_:xb_]
            can[ya_:yb_, xa_:xb_] = pen.put_ink(sub, cov[ya_ - y:yb_ - y, xa_ - x:xb_ - x] * alpha, ink=ink, seed=f // 4, bleed=0.4)
    if sh_n == 2 and fa >= 541:
        put_cov(ANN_G, GRAPH, 0.75 * min(1, (fa - 541) / 8), ox, oy)
    if sh_n == 2 and fa >= 543: put_cov(ANN_A, PENINK, min(1, (fa - 543) / 3), ox, oy)
    if sh_n == 2 and fa >= 549: put_cov(ANN_B, PENINK, min(1, (fa - 549) / 3), ox, oy)
    # puppets: shadows first (offset encodes height), then pieces, clipped to their panel
    _, items = scene(fa)
    shadow = np.zeros((Hc, Wc), np.float32); layers = []
    for panel, nm, M, hgt in items:
        px0, py0 = panel_origin(panel)
        Mw = M.copy(); Mw[0, 2] += px0 - X0; Mw[1, 2] += py0 - Y0
        clip = np.zeros((Hc, Wc), np.float32)
        clip[max(0, py0 - Y0 + 3):max(0, py0 - Y0 + PHT - 3), max(0, px0 - X0 + 3):max(0, px0 - X0 + PWID - 3)] = 1
        pc = P[nm]
        a = cv2.warpAffine(pc["a"], Mw, (Wc, Hc), flags=cv2.INTER_LINEAR) * clip
        rgb = cv2.warpAffine(pc["rgb"], Mw, (Wc, Hc), flags=cv2.INTER_LINEAR) * clip[..., None]
        dx, dy = 0.07 * hgt + 3, 0.10 * hgt + 4
        Ms = Mw.copy(); Ms[0, 2] += dx; Ms[1, 2] += dy
        shadow = np.maximum(shadow, cv2.warpAffine(pc["a"], Ms, (Wc, Hc)) * clip)
        layers.append((a, rgb))
    comp(can, SHADOW, cv2.GaussianBlur(shadow, (0, 0), 4) * 0.26)
    for a, rgb in layers:
        can *= (1 - a[..., None]); can += rgb
    # brass split pins on the visible joints of the glider (the hip) in the active panel
    for panel, nm, M, hgt in items:
        if nm in ("glider", "glider_core"):
            px0, py0 = panel_origin(panel); hp = ap(M, P[nm]["pv"]["hip"])
            pin_at(can, hp[0] + px0 - X0, hp[1] + py0 - Y0, 0.55)
    # slips (BB-08)
    if sh_n == 2 and 474 <= fa < 660:
        for sid in ("S5", "S5b"):
            sl = SLIPS[sid]
            if f < sl["t"]: continue
            cov = reveal(sl["letters"], f)
            if sid == "S5":
                if f >= STRIKE_F:
                    xs = np.arange(cov.shape[1], dtype=np.float32); xe = mx0 - 5 + (mx1 - mx0 + 11) * min(1.0, (f - STRIKE_F + 1) / 3)
                    cov = np.maximum(cov, sl["strike"] * np.clip((xe - xs) / 2, 0, 1)[None, :])
                fc = reveal(sl["fix"], f)
                if fc is not None: cov = np.maximum(cov, fc)
            rgb = pen.put_ink(sl["rgb"].copy(), cov, ink=PENINK, seed=7)
            lift = max(0.0, 6 - 2 * (f - sl["t"]))
            h, w = sl["a"].shape
            M = cv2.getRotationMatrix2D((w / 2, h / 2), sl["ang"], 1.0); M[0, 2] += sl["x"] - X0 - lift; M[1, 2] += sl["y"] - Y0 - lift * 2
            A = cv2.warpAffine(sl["a"], M, (Wc, Hc)); Rg = cv2.warpAffine(rgb * sl["a"][..., None], M, (Wc, Hc))
            Ms = M.copy(); Ms[0, 2] += 2 + lift; Ms[1, 2] += 3 + lift * 1.4
            comp(can, SHADOW, cv2.GaussianBlur(cv2.warpAffine(sl["a"], Ms, (Wc, Hc)), (0, 0), 2.5) * 0.24)
            can = can * (1 - A[..., None]) + Rg
            pn = ap(M, (16, 14)); pin_at(can, pn[0], pn[1], 1.0)
        if f >= 552:
            gl = reveal(GLOSS_L, f)
            put_cov(gl, GRAPH, 0.8, TX0 + 12 - X0, PYS[1] + 236 - Y0)
    # camera: page crop -> 960x540
    M = np.array([[z, 0, -z * (cx - fw / 2 - X0)], [0, z, -z * (cy - fh / 2 - Y0)]], np.float32)
    out = cv2.warpAffine(np.clip(can, 0, 255), M, (960, 540), flags=cv2.INTER_AREA if z < 1 else cv2.INTER_LINEAR, borderValue=tuple(float(c) for c in DESK))
    return out.astype(np.uint8)


def pin_at(can, x, y, s):
    rgb, a = PIN; h, w = a.shape
    if s != 1.0:
        w2, h2 = max(3, int(w * s)), max(3, int(h * s)); rgb = cv2.resize(rgb, (w2, h2), interpolation=cv2.INTER_AREA); a = cv2.resize(a, (w2, h2), interpolation=cv2.INTER_AREA); h, w = h2, w2
    x0, y0 = int(round(x - w / 2)), int(round(y - h / 2))
    if x0 < 0 or y0 < 0 or x0 + w > can.shape[1] or y0 + h > can.shape[0]: return
    sub = can[y0:y0 + h, x0:x0 + w]; sub *= (1 - a[..., None]); sub += rgb * a[..., None]


# ------------------------------------------------------------------ tests (on the rig and exposure, every drawing)
def tests():
    T = {}
    worst = 0.0; lim_viol = []
    for f in range(0, NF, 2):
        _, items = scene(f)
        byp = {}
        for panel, nm, M, hgt in items:
            byp.setdefault(panel, []).append((nm, M))
        for panel, lst in byp.items():
            d = {}
            for nm, M in lst: d.setdefault(nm, []).append(M)
            for ch, (par, ppin, cpin, lim) in JD.items():
                if ch in d and par in d:
                    for Mc, Mp in zip(d[ch], d[par]):
                        e = float(np.linalg.norm(ap(Mc, P[ch]["pv"][cpin]) - ap(Mp, P[par]["pv"][ppin])))
                        worst = max(worst, e)
                        rel = math.degrees(math.atan2(Mc[1, 0], Mc[0, 0]) - math.atan2(Mp[1, 0], Mp[0, 0]))
                        rel = (rel + 180) % 360 - 180
                        if ch in ("heli_top", "heli_bottom"): continue
                        if not (lim[0] - 0.01 <= rel <= lim[1] + 0.01) and ch != "paper_wing_root":
                            lim_viol.append({"f": f, "joint": ch, "rel": round(rel, 2), "lim": lim})
    T["pivot_drift_max_px"] = round(worst, 5); T["pivot_drift_pass"] = worst <= 1.0
    T["angle_limit_violations"] = lim_viol[:20]; T["angle_limits_pass"] = not lim_viol
    T["joint_stop_hits"] = {"legs": LEGS["_stops"], "glider_wingR": DROOP["_stops"], "paper_wing_tip": TIP["_stops"], "pilot_legs": A1LEGS["_stops"]}
    # secondary decay: legs after the body comes to rest at f540 (counterfactual hold run) and after the impact f605
    # repair 2: measured on the ON-SCREEN run (LEGS), body at rest f540-564; no counterfactual
    rest = None
    for f in range(540, 565):
        if max(abs(LEGS[g]) for g in range(f, 565)) < 1.0: rest = f; break
    T["legs_decay_after_rest_f540"] = {"rest_frame": rest, "frames": None if rest is None else rest - 540,
                                       "pass": rest is not None and rest <= 564 and abs(LEGS[542]) >= 8,
                                       "phi_f540": round(LEGS[540], 2), "phi_f542": round(LEGS[542], 2), "peak_abs_deg_f540_564": round(max(abs(LEGS[g]) for g in range(540, 565)), 2),
                                       "phi_f564": round(LEGS[564], 2), "trace_on_2s": {g: round(LEGS[g], 2) for g in range(536, 568, 2)}}
    _, _, _, th_w, _ = glider_primary(700)
    for f in range(605, 719):
        if max(abs(LEGS[g] - LEGS[718]) for g in range(f, 719)) < 1.0: break
    T["legs_decay_after_impact_f605"] = {"rest_frame": f, "frames": f - 605, "pass": f - 605 <= 24}
    for f in range(605, 719):
        if max(abs(DROOP[g] - DROOP_REST) for g in range(f, 719)) < 1.0: break
    T["wing_droop_decay_f605"] = {"rest_frame": f, "frames": f - 605, "pass": f - 605 <= 30, "snap_hold": "58 deg held f605-610 (3 drawings)",
                                  "bounces": int(sum(1 for g in range(612, 660) if (DROOP[g] - DROOP_REST) * (DROOP[g - 1] - DROOP_REST) < 0 and abs(DROOP[g - 1] - DROOP_REST) > 0.5))}
    for f in range(154, 200):
        if max(abs(TIP[g] - 150) for g in range(f, 200)) < 1.0: break
    T["paper_tip_decay_after_sit_f154"] = {"rest_frame": f, "frames": f - 154, "pass": f - 154 <= 24}
    bf = [k for k in BAND if k != "_stops"]
    for f in range(312, max(bf)):
        if max(abs(BAND[g]) for g in range(f, max(bf))) < 1.0: break
    T["band_whip_decay_f312"] = {"rest_frame": f, "frames": f - 312, "pass": f - 312 <= 24}
    # first readable failure frame: pitch >= 15 deg and x-advance < 0.5 px/frame (page px) in BB-08
    ff = None
    for f in range(504, 576):
        _, u0, _, _, _ = glider_primary(f - 1); _, u1, _, th, _ = glider_primary(f)
        if th >= 15 and abs(u1 - u0) < 0.5: ff = f; break
    _, u0, _, _, _ = glider_primary(ff - 1); _, u1, _, th, _ = glider_primary(ff)
    T["first_failure_frame"] = {"frame": ff, "pitch_deg": round(th, 2), "x_advance_px_per_frame_page": round(abs(u1 - u0), 3),
                                "x_advance_px_per_frame_screen_at_zoom": round(abs(u1 - u0) * camera(ff)[1][2], 3), "in_window_f520_545": 520 <= ff <= 545}
    th15 = next(f for f in range(504, 576) if glider_primary(f)[3] >= 15)
    T["strike_vs_nose_15deg"] = {"nose_15deg_frame": th15, "strike_frame": STRIKE_F, "pass": abs(th15 - STRIKE_F) <= 1}
    xs = [glider_primary(f)[1] for f in range(540, 565)]
    ys = [glider_primary(f)[2] for f in range(540, 565)]
    T["hang_f540_564_still"] = {"x_range_px": round(max(xs) - min(xs), 4), "y_range_px": round(max(ys) - min(ys), 4), "pass": max(xs) - min(xs) < 0.5 and max(ys) - min(ys) < 0.5}
    return T


def exposure():
    rows = []
    for f in sorted(set(range(0, NF, 2)) | {605}):     # repair 2: f605 (impact, spar snap) is drawn on ones
        sh_n, cam, move = camera(f)
        _, items = scene(f)
        pcs = []
        for panel, nm, M, hgt in items:
            ang = math.degrees(math.atan2(M[1, 0], M[0, 0]))
            sx = float(np.hypot(M[0, 0], M[1, 0])); sy = float(np.hypot(M[0, 1], M[1, 1]))
            pin = ap(M, list(P[nm]["pv"].values())[0])
            pcs.append({"panel": panel, "piece": nm, "M": [[round(float(v), 4) for v in r] for r in M], "angle": round(ang, 2),
                        "scale": [round(sx, 3), round(sy, 3)], "first_pin_xy": [round(float(pin[0]), 2), round(float(pin[1]), 2)], "height": round(float(hgt), 1)})
        board = next(b for b, (a, z) in BOARDS.items() if a <= f < z)
        row = {"f": f, "hold": [f] if f in (604, 605) else [f, f + 1], "t": round(f / FPS, 3), "board": board, "sheet": sh_n, "camera": {"cx": round(cam[0], 1), "cy": round(cam[1], 1), "zoom": round(cam[2], 4), "move": move},
               "pieces": pcs}
        if 504 <= f < 660:
            _, u, v, th, hgt = glider_primary(f); row["glider"] = {"hip_u": round(u, 2), "hip_v": round(v, 2), "pitch": round(th, 2), "legs_world": round(LEGS[f], 2), "height": round(hgt, 1)}
        if 24 <= f < 200:
            row["a1"] = {"arm": round(arm_a1(f), 2), "paper_tip": round(TIP[f], 2), "legs": round(A1LEGS[f], 2)}
        if 192 <= f < 384:
            row["a2"] = {"rotor_phase": round(rotor_phase(f) % 360, 1), "tally": int(min(12, max(0, (f - 192) // 5))), "band_whip_px": round(BAND.get(f, 0.0), 2)}
        rows.append(row)
    return rows


BOARDS = {"BB-00": (0, 24), "BB-01": (24, 192), "BB-02/03": (192, 340), "BB-04/05": (340, 384), "BB-06": (384, 432), "BB-07": (432, 504), "BB-08": (504, 576),
          "BB-09": (576, 660), "BB-10": (660, 720)}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


if __name__ == "__main__":
    T = tests(); print(json.dumps(T, indent=1))
    rows = exposure()
    json.dump({"fps": FPS, "frames": NF, "on": 2, "page_px": [PW, PH], "panels": {"x": PX, "w": PWID, "h": PHT, "ys": PYS},
               "coords": "piece M maps piece px (after SCALE) to panel-local px; panel origin = (x, ys[i]) on the sheet; angle + = clockwise on screen (nose-up for the left-facing glider)",
               "boards": BOARDS, "strike_frame": STRIKE_F, "impact_frame": 605, "key_poses": KEYPOSE, "drawings": rows},
              open(os.path.join(SW, "exposure.json"), "w"))
    # BB-08 test render
    tmp = os.path.join(BD, "bb08_frames"); os.makedirs(tmp, exist_ok=True)
    frames = {}
    for f in range(504, 577):
        im = render(f); frames[f] = im
        Image.fromarray(im).save(os.path.join(tmp, f"f{f:04d}.png"))
    mp4 = os.path.join(SW, "bb08_test.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-start_number", "504", "-i", os.path.join(tmp, "f%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-an", mp4], check=True)
    pick = [504, 516, 528, 534, 540, 546, 552, 556, 560, 566, 572, 576]
    th = [Image.fromarray(frames[f]).resize((480, 270), Image.LANCZOS) for f in pick]
    sheet_im = Image.new("RGB", (480 * 4 + 50, 290 * 3 + 40), (30, 28, 26))
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet_im)
    for i, (f, t) in enumerate(zip(pick, th)):
        x, y = 10 + (i % 4) * 490, 10 + (i // 4) * 300
        sheet_im.paste(t, (x, y)); d.text((x + 4, y + 272), f"f{f}  {f / 24:.2f}s  pitch {glider_primary(f)[3]:.1f}", fill=(230, 220, 205))
    sheet_im.save(os.path.join(SW, "bb08_sheet.jpg"), quality=90)
    shutil.copy(mp4, os.path.join(BD, "bb08_test.mp4")); shutil.copy(os.path.join(SW, "bb08_sheet.jpg"), os.path.join(BD, "bb08_sheet.jpg"))
    for f in (504, 528, 540, 548, 556, 576):
        Image.fromarray(frames[f]).save(os.path.join(ED, f"bb08_f{f}.png"))
    # wide page stills for the editor and the aesthetic check (f0 sheet 1 empty panels; f700 sheet 2 key poses)
    for f in (0, 700):
        Image.fromarray(render(f)).save(os.path.join(ED, f"wide_f{f}.png"))
    json.dump(T, open(os.path.join(BD, "tests.json"), "w"), indent=1)
    print("ok")
