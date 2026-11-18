"""Quatre-vingt-quinze: three proposal keyframes + board.

python3 -I kf.py <oulipo root>
Deterministic. Reads foraged sources only through PIL / cv2 (PNG frames were
extracted beforehand with ffmpeg from the local Moving Image Archive cache).

All three keyframes stop at the same beat: t = 44.5 s of a ~60 s film, the DOWN
reading (A D G B E H C F I) entering the centre cell E from B.
"""
import sys, os, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = sys.argv[1] if len(sys.argv) > 1 else '/home/user/bolas/paeleo/scion/oulipo'
SRC = os.path.join(ROOT, 'films/sources')
MINE = os.path.join(SRC, 'quatre-vingt-quinze')
LOC = os.path.join(SRC, 'la-machine-a-tuer-le-temps')
OUT = os.path.join(ROOT, 'films/swarm/quatre-vingt-quinze/proposals')
REF = os.path.join(ROOT, 'assets/references/extract-003.webp')

S = 2                       # supersample
W, H = 1280, 720
FB = '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf'
FS = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
FM = '/usr/share/fonts/X11/Type1/c0583bt_.pfb'
def font(p, sz): return ImageFont.truetype(p, int(sz * S))

# ---------------- grid registry and Hard-proof fixture ----------------
IDS = 'ABCDEFGHI'
ACROSS = list('ABCDEFGHI')
DOWN = [IDS[r * 3 + c] for c in range(3) for r in range(3)]
assert ''.join(DOWN) == 'ADGBEHCFI'
assert sorted(ACROSS) == sorted(DOWN) == list(IDS)
def rc(cid): i = IDS.index(cid); return divmod(i, 3)
def legal(path, step):
    for a, b in zip(path, path[1:]):
        (r0, c0), (r1, c1) = rc(a), rc(b)
        ok = (r1, c1) == step(r0, c0)
        if not ok: return False
    return True
assert legal(ACROSS, lambda r, c: (r, c + 1) if c < 2 else (r + 1, 0))
assert legal(DOWN, lambda r, c: (r + 1, c) if r < 2 else (0, c + 1))
assert ACROSS[-1] == DOWN[-1] == 'I'            # both endings use the same final cell
assert ACROSS[ACROSS.index('E') - 1] == 'D' and DOWN[DOWN.index('E') - 1] == 'B'

# One immutable text per cell (shared by every traversal and every direction).
TEXT = dict(
    A=('cap', 'GARE DE ST-ROCH, 6 H 10.', 'bal', 'PERSONNE ?'),
    B=('sfx', 'DING ! DING !'),
    C=('bal', 'UNE CLÉ ?'),
    D=('cap', 'DERRIÈRE LA PORTE DE SERVICE...'),
    E=('bal', "C'EST POUR MOI ?"),
    F=('bal', 'TANT PIS.'),
    G=('cap', 'IL TIRE LA CORDE.'),
    H=('cap', 'PLUS PERSONNE.'),
    I=('bal', 'MERCI.'),
)
# film clock: title 0-3, ACROSS 3-30 (3 s / cell), turn 30-32, DOWN 32-59, end 59-62
def t_cell(path, cid, t0): return t0 + 3 * path.index(cid)
T_BEAT = 44.5
assert t_cell(DOWN, 'E', 32) <= T_BEAT < t_cell(DOWN, 'E', 32) + 3

# ---------------- palette (sampled by eye from the reference) ----------------
PAPER = (246, 240, 230); INK = (22, 16, 15)
SAL_L = (240, 184, 160); SAL = (226, 128, 100); SAL_D = (190, 80, 62)
RED = (196, 44, 30); KEYC = (246, 205, 160)
BG = dict(A='W', B='S', C='W', D='S', E='S', F='W', G='S', H='W', I='S')

# ---------------- page geometry (1x units) ----------------
PW, PH, GU = 290, 190, 34
GX0 = (W - (3 * PW + 2 * GU)) // 2; GY0 = 66
def cell_box(cid):
    r, c = rc(cid); x = GX0 + c * (PW + GU); y = GY0 + r * (PH + GU)
    return x, y, x + PW, y + PH

rng = np.random.default_rng(95)

def wobble_rect(dr, box, width, fill=None, outline=INK, seed=0):
    """ink border drawn as a slightly irregular quadrilateral (hand-ruled)."""
    r = np.random.default_rng(seed)
    x0, y0, x1, y1 = [v * S for v in box]
    pts = [(x0 + r.normal(0, .7 * S), y0 + r.normal(0, .7 * S)), (x1 + r.normal(0, .7 * S), y0 + r.normal(0, .7 * S)),
           (x1 + r.normal(0, .7 * S), y1 + r.normal(0, .7 * S)), (x0 + r.normal(0, .7 * S), y1 + r.normal(0, .7 * S))]
    if fill is not None: dr.polygon(pts, fill=fill)
    dr.line(pts + [pts[0]], fill=outline, width=int(width * S), joint='curve')

def crossing_mark(dr, cx, cy, mode, sz=13, seed=0):
    """Lécroart's red crossing mark: a cross with barbed ends. mode 'across' lengthens
    the horizontal arms, 'down' the vertical arms (the axis cue, legible in grey)."""
    r = np.random.default_rng(seed)
    long_h = 1.7 if mode == 'across' else 0.85
    long_v = 1.7 if mode == 'down' else 0.85
    cx, cy, sz = cx * S, cy * S, sz * S
    for ang, ln in ((0, long_h), (180, long_h), (90, long_v), (270, long_v), (45, .7), (135, .7), (225, .7), (315, .7)):
        a = math.radians(ang + r.normal(0, 3)); L = sz * ln
        ex, ey = cx + L * math.cos(a), cy + L * math.sin(a)
        dr.line([(cx, cy), (ex, ey)], fill=RED, width=int(2.6 * S))
        if ln > 1:                                      # barbs = direction of reading
            for da in (150, -150):
                b = a + math.radians(da)
                dr.line([(ex, ey), (ex + .45 * sz * math.cos(b), ey + .45 * sz * math.sin(b))], fill=RED, width=int(2.6 * S))
    dr.ellipse([cx - 3 * S, cy - 3 * S, cx + 3 * S, cy + 3 * S], fill=RED)

def flipped_title(page, text, cx, y, size):
    """'quatre-vingt-quinze' lettered with every other glyph turned upside down, as on the page."""
    f = font(FS, size); xs = []; tot = 0
    for ch in text:
        w = f.getbbox(ch)[2] - f.getbbox(ch)[0] + 2 * S; xs.append(w); tot += w
    x = cx * S - tot / 2
    for i, ch in enumerate(text):
        g = Image.new('L', (int(size * 1.6 * S), int(size * 1.6 * S)), 0)
        ImageDraw.Draw(g).text((int(.2 * size * S), int(.1 * size * S)), ch, font=f, fill=255)
        if i % 2 == 1 and ch not in '-': g = g.rotate(180)
        bb = g.getbbox()
        if bb:
            gg = g.crop(bb); off = (int(x), int(y * S + (size * S - gg.size[1]) * (0.5 if ch == '-' else 0.85)))
            col = Image.new('RGB', gg.size, (150, 40, 28)); page.paste(col, off, gg)
        x += xs[i]

def text_block(dr, xy, lines, f, fill=INK, spacing=1.15, anchor_center=True):
    x, y = xy
    for ln in lines:
        w = dr.textlength(ln, font=f)
        dr.text((x - w / 2 if anchor_center else x, y), ln, font=f, fill=fill)
        y += f.size * spacing

def wrap(text, f, maxw, dr):
    words = text.split(); lines = []; cur = ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if dr.textlength(t, font=f) <= maxw: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

def balloon(dr, box, text, tail, size=13):
    """speech balloon in a panel (box in page 1x units); tail = (x, y) tip in page units."""
    f = font(FB, size)
    x0, y0, x1, y1 = box
    lines = wrap(text, f, (x1 - x0 - 16) * S, dr)
    th = len(lines) * f.size * 1.15
    cx, cy = (x0 + x1) / 2 * S, (y0 + y1) / 2 * S
    bw = max(dr.textlength(l, font=f) for l in lines) / 2 + 12 * S; bh = th / 2 + 9 * S
    tx, ty = tail[0] * S, tail[1] * S
    dr.polygon([(cx - 7 * S, cy + bh * .6), (cx + 7 * S, cy + bh * .6), (tx, ty)], fill='white', outline=INK)
    dr.ellipse([cx - bw - 2 * S, cy - bh - 2 * S, cx + bw + 2 * S, cy + bh + 2 * S], fill=INK)
    dr.polygon([(cx - 5 * S, cy + bh * .6), (cx + 5 * S, cy + bh * .6), (tx, ty)], fill='white')
    dr.line([(cx - 7 * S, cy + bh * .7), (tx, ty), (cx + 7 * S, cy + bh * .7)], fill=INK, width=int(1.6 * S))
    dr.ellipse([cx - bw, cy - bh, cx + bw, cy + bh], fill='white')
    text_block(dr, (cx, cy - th / 2 + 1 * S), lines, f)

def caption(dr, xy, text, size=11, maxw=150):
    f = font(FB, size); x, y = xy
    lines = wrap(text, f, maxw * S, dr)
    w = max(dr.textlength(l, font=f) for l in lines) + 10 * S; h = len(lines) * f.size * 1.15 + 6 * S
    dr.rectangle([x * S, y * S, x * S + w, y * S + h], fill=PAPER, outline=INK, width=int(1.5 * S))
    text_block(dr, (x * S + 5 * S, y * S + 3 * S), lines, f, anchor_center=False)

def sfx(dr, xy, text, size=22, angle=-8, page=None):
    f = font(FB, size)
    g = Image.new('L', (int(len(text) * size * .9 * S), int(size * 1.6 * S)), 0)
    gd = ImageDraw.Draw(g); gd.text((4 * S, 2 * S), text, font=f, fill=255)
    g = g.rotate(angle, expand=True, resample=Image.BICUBIC)
    ol = g.filter(ImageFilter.MaxFilter(5))
    page.paste(Image.new('RGB', g.size, INK), (int(xy[0] * S), int(xy[1] * S)), ol)
    page.paste(Image.new('RGB', g.size, RED), (int(xy[0] * S), int(xy[1] * S)), g)

def letter_cell_text(page, dr, cid, art_boxes):
    """letter the immutable text of each cell. art_boxes maps cid -> dict of placement hints."""
    hint = art_boxes.get(cid, {})
    x0, y0, x1, y1 = cell_box(cid)
    t = TEXT[cid]
    i = 0
    while i < len(t):
        kind, s = t[i], t[i + 1]; i += 2
        if kind == 'cap': caption(dr, (x0 + 6, y0 + 6) if 'cap' not in hint else hint['cap'], s, maxw=hint.get('capw', 170))
        elif kind == 'bal':
            bx = hint.get('bal', (x0 + 150, y0 + 8, x1 - 8, y0 + 58)); tl = hint.get('tail', (x0 + 180, y0 + 90))
            balloon(dr, bx, s, tl, size=hint.get('bsz', 13))
        elif kind == 'sfx': sfx(dr, hint.get('sfx', (x0 + 120, y0 + 20)), s, page=page)

def page_frame(cells, hints, title=True, active='E', visited=('A', 'D', 'G', 'B'), mode='down'):
    """cells: cid -> RGB PIL image (PW*S x PH*S) of the cell artwork.
    Builds the page: paper, title, panels, borders, crossing marks, route rail, lettering."""
    page = Image.new('RGB', (W * S, H * S), PAPER)
    # faint paper tooth
    tooth = (rng.normal(0, 3.2, (H * S // 4, W * S // 4))).astype(np.float32)
    tooth = cv2.resize(tooth, (W * S, H * S), interpolation=cv2.INTER_CUBIC)
    a = np.asarray(page, np.float32) + tooth[..., None]
    page = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    dr = ImageDraw.Draw(page)
    if title: flipped_title(page, 'quatre-vingt-quinze', W / 2, 12, 40)
    for k, cid in enumerate(IDS):
        x0, y0, x1, y1 = cell_box(cid)
        art = cells[cid]
        if cid not in visited and cid != active:          # not yet read on this route: paper wash
            art = Image.blend(art, Image.new('RGB', art.size, PAPER), .38)
        page.paste(art, (x0 * S, y0 * S))
    dr = ImageDraw.Draw(page)
    for cid in IDS:
        letter_cell_text(page, dr, cid, hints)
    for k, cid in enumerate(IDS):
        box = cell_box(cid)
        wobble_rect(dr, box, 4.2 if cid == active else 2.6, seed=k)
        # cell id tab (route registry), red when visited on the current route
        x0, y0, x1, y1 = box
        f = font(FM, 11)
        col = RED if (cid in visited or cid == active) else (150, 140, 130)
        dr.rectangle([(x1 - 17) * S, (y1 - 16) * S, (x1 - 2) * S, (y1 - 2) * S], fill=PAPER, outline=col, width=S)
        dr.text(((x1 - 14) * S, (y1 - 16) * S), cid, font=f, fill=col)
    # crossing marks: on the row gutters, at the panel edges and between columns (as on the page)
    for r in range(2):
        gy = GY0 + (r + 1) * PH + r * GU + GU / 2
        for c in range(4):
            gx = GX0 + c * (PW + GU) - GU / 2
            crossing_mark(dr, gx, gy, mode, seed=r * 7 + c)
    # the transition being read: B -> E, a red cut-paper arrow in the gutter
    bx0, by0, bx1, by1 = cell_box('B'); ex0, ey0, ex1, ey1 = cell_box('E')
    mx = (bx0 + bx1) / 2; gy0, gy1 = by1 + 3, ey0 - 3
    dr.polygon([((mx - 9) * S, gy0 * S), ((mx + 9) * S, gy0 * S), ((mx + 9) * S, (gy1 - 12) * S), ((mx + 18) * S, (gy1 - 12) * S),
                (mx * S, gy1 * S + 6 * S), ((mx - 18) * S, (gy1 - 12) * S), ((mx - 9) * S, (gy1 - 12) * S)], fill=RED, outline=INK)
    # route rail, left margin: the DOWN route as a vertical column; right: the ACROSS route, done
    f = font(FM, 15); f2 = font(FM, 12)
    lx = 40
    dr.text((lx * S, 92 * S), 'II', font=font(FS, 26), fill=RED)
    dr.text((lx * S, 128 * S), 'en bas', font=f2, fill=INK)
    for i, cid in enumerate(DOWN):
        y = 160 + i * 52
        col = RED if (cid in visited or cid == active) else (150, 140, 130)
        if cid == active:
            dr.ellipse([(lx - 8) * S, (y - 6) * S, (lx + 22) * S, (y + 24) * S], outline=RED, width=int(2.5 * S))
        dr.text((lx * S, y * S), cid, font=f, fill=col)
        if i < 8: dr.line([((lx + 7) * S, (y + 24) * S), ((lx + 7) * S, (y + 44) * S)], fill=col, width=int(1.5 * S))
    rx = W - 140
    dr.text((rx * S, 92 * S), 'I', font=font(FS, 26), fill=(150, 140, 130))
    dr.text((rx * S, 128 * S), 'en travers', font=f2, fill=(150, 140, 130))
    for i, cid in enumerate(ACROSS):
        dr.text(((rx + (i % 3) * 30) * S, (160 + (i // 3) * 40) * S), cid, font=f, fill=(150, 140, 130))
    dr.line([(rx * S, 300 * S), ((rx + 90) * S, 300 * S)], fill=(150, 140, 130), width=S)
    dr.text((rx * S, 640 * S), '44,5 s', font=f2, fill=INK)
    dr.text((rx * S, 658 * S), 'B > E', font=f2, fill=RED)
    return page.resize((W, H), Image.LANCZOS)

# ======================================================================
# drawing helpers (handmade cut-paper pieces, used by direction 1 and 2)
# ======================================================================
def cap_line(dr, p, q, w, fill):
    dr.line([p, q], fill=fill, width=int(w))
    r = w / 2
    for (x, y) in (p, q): dr.ellipse([x - r, y - r, x + r, y + r], fill=fill)

class Puppet:
    """Articulated silhouette (Reiniger rig): hip root, torso, head, two 2-bone arms,
    two legs. Angles in degrees, 0 = hanging straight down, positive = forward (facing)."""
    def __init__(self, kind='visitor', face=1):
        self.kind, self.face = kind, face
    def draw(self, dr, x, y, u, pose, fill=INK, key=None, env=None):
        f = self.face
        P = lambda dx, dy: (x + f * dx * u, y + dy * u)
        hip = P(0, -46); sh = P(1, -84); neck = P(2, -88)
        # legs (FK: thigh, shin)
        for side, (a1, a2) in (('b', pose.get('legB', (-8, 4))), ('f', pose.get('legF', (10, -2)))):
            k = (hip[0] + f * 24 * u * math.sin(math.radians(a1)), hip[1] + 24 * u * math.cos(math.radians(a1)))
            a = a1 + a2
            ft = (k[0] + f * 23 * u * math.sin(math.radians(a)), k[1] + 23 * u * math.cos(math.radians(a)))
            cap_line(dr, hip, k, 7 * u, fill); cap_line(dr, k, ft, 6 * u, fill)
            dr.polygon([(ft[0] - f * 2 * u, ft[1] - 2 * u), (ft[0] + f * 9 * u, ft[1] - 1 * u), (ft[0] + f * 9 * u, ft[1] + 2.5 * u), (ft[0] - f * 2 * u, ft[1] + 2.5 * u)], fill=fill)
        # coat
        if self.kind == 'visitor':
            coat = [P(-8, -86), P(10, -86), P(17, -30), P(-15, -28)]
        else:
            coat = [P(-9, -86), P(11, -86), P(15, -18), P(-13, -16)]
        dr.polygon(coat, fill=fill)
        # head: Lécroart big-nose profile
        hc = P(3, -97)
        dr.ellipse([hc[0] - 8 * u, hc[1] - 9 * u, hc[0] + 8 * u, hc[1] + 9 * u], fill=fill)
        tilt = math.radians(pose.get('head', 0))
        def rot(dx, dy):
            cx, cy = dx * math.cos(tilt) - dy * math.sin(tilt), dx * math.sin(tilt) + dy * math.cos(tilt)
            return (hc[0] + f * cx * u, hc[1] + cy * u)
        dr.polygon([rot(5, -4), rot(19, 1), rot(17, 5), rot(5, 4)], fill=fill)         # nose
        cap_line(dr, P(2, -90), P(2, -84), 7 * u, fill)                                  # neck
        if self.kind == 'visitor':                                                        # cloche hat
            dr.chord([rot(-11, -18)[0] - 0, rot(-11, -18)[1], rot(11, -18)[0], rot(11, 2)[1]], 180, 360, fill=fill) if False else None
            dr.polygon([rot(-11, -2), rot(-10, -12), rot(-3, -17), rot(7, -16), rot(11, -9), rot(14, -4)], fill=fill)
            dr.polygon([rot(-12, 9), rot(-11, -2), rot(-6, -2), rot(-6, 9)], fill=fill)    # hair
        else:                                                                             # peaked cap
            dr.polygon([rot(-9, -6), rot(-9, -14), rot(9, -15), rot(10, -7)], fill=fill)
            dr.polygon([rot(8, -7), rot(18, -5), rot(17, -3), rot(8, -4)], fill=fill)
        # arms (FK: shoulder -> elbow -> wrist); back arm first
        hands = []
        for side in ('armB', 'armF'):
            a1, a2 = pose.get(side, (10, 10))
            s0 = P(-1, -82) if side == 'armB' else P(3, -82)
            e = (s0[0] + f * 17 * u * math.sin(math.radians(a1)), s0[1] + 17 * u * math.cos(math.radians(a1)))
            a = a1 + a2
            w_ = (e[0] + f * 16 * u * math.sin(math.radians(a)), e[1] + 16 * u * math.cos(math.radians(a)))
            cap_line(dr, s0, e, 6 * u, fill); cap_line(dr, e, w_, 5 * u, fill)
            dr.ellipse([w_[0] - 3.3 * u, w_[1] - 3.3 * u, w_[0] + 3.3 * u, w_[1] + 3.3 * u], fill=fill)
            hands.append((w_, a))
        return hands

def draw_key(dr, x, y, u, ang, fill=KEYC, out=INK):
    """cut-paper key: bow ring, shank, bit. (x,y) = bow centre."""
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    T = lambda dx, dy: (x + (dx * c - dy * s) * u, y + (dx * s + dy * c) * u)
    shank = [T(5, -1.6), T(26, -1.6), T(26, 1.6), T(5, 1.6)]
    bit = [T(20, 1.6), T(20, 6.5), T(23, 6.5), T(23, 4.5), T(25.5, 4.5), T(25.5, 1.6)]
    for poly in (shank, bit): dr.polygon(poly, fill=out)
    sh2 = [T(5, -.8), T(25.2, -.8), T(25.2, .8), T(5, .8)]
    dr.polygon(sh2, fill=fill)
    dr.ellipse([x - 6.5 * u, y - 6.5 * u, x + 6.5 * u, y + 6.5 * u], fill=out)
    dr.ellipse([x - 5.2 * u, y - 5.2 * u, x + 5.2 * u, y + 5.2 * u], fill=fill)
    dr.ellipse([x - 2.4 * u, y - 2.4 * u, x + 2.4 * u, y + 2.4 * u], fill=out)

def draw_bell(dr, cx, cy, u, ang, fill=INK):
    """wall bell on a bracket; ang = swing (deg) about the bracket pivot."""
    dr.line([(cx - 26 * u, cy - 6 * u), (cx, cy - 6 * u)], fill=fill, width=int(4 * u))
    dr.line([(cx - 26 * u, cy - 16 * u), (cx - 26 * u, cy + 6 * u)], fill=fill, width=int(5 * u))
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    T = lambda dx, dy: (cx + (dx * c - dy * s) * u, cy + (dx * s + dy * c) * u)
    prof = [(-3, -6), (3, -6), (6, -2), (8, 8), (10, 16), (15, 22), (-15, 22), (-10, 16), (-8, 8), (-6, -2)]
    dr.polygon([T(*p) for p in prof], fill=fill)
    ca = math.radians(ang * 1.9)
    clap = (cx + (math.sin(-ca) * 26) * u, cy + (math.cos(ca) * 26) * u)
    dr.ellipse([clap[0] - 3.5 * u, clap[1] - 3.5 * u, clap[0] + 3.5 * u, clap[1] + 3.5 * u], fill=fill)

def panel_bg(kind, w, h, light=(0.5, 0.35)):
    """flat stage: white, or salmon with a soft pool of light (the reference panels)."""
    if kind == 'W':
        return Image.new('RGB', (w, h), (250, 246, 240))
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xx / w - light[0]) * 1.2) ** 2 + ((yy / h - light[1]) * 1.0) ** 2)
    t = np.clip(d / 0.75, 0, 1)[..., None]
    a = np.array(SAL_L, np.float32) * (1 - t) + np.array(SAL_D, np.float32) * t
    return Image.fromarray(a.astype(np.uint8))

def floor(dr, w, h, y, fill=INK):
    dr.rectangle([0, y, w, h], fill=fill)

# ======================================================================
# DIRECTION 1 - articulated shadow theatre on the grid (handmade)
# ======================================================================
def dir1_cells():
    w, h = PW * S, PH * S; u = 1.2 * S
    V = Puppet('visitor', 1); M = Puppet('man', -1)
    cells = {}
    def new(cid, light=(.5, .35)):
        im = panel_bg(BG[cid], w, h, light); return im, ImageDraw.Draw(im)
    # A: empty platform, the visitor walks in with the envelope
    im, d = new('A'); floor(d, w, h, h - 30 * S)
    d.rectangle([w - 70 * S, 40 * S, w - 64 * S, h - 30 * S], fill=INK)          # lamp post
    d.polygon([(w - 82 * S, 40 * S), (w - 52 * S, 40 * S), (w - 60 * S, 28 * S), (w - 74 * S, 28 * S)], fill=INK)
    d.rectangle([w - 120 * S, 70 * S, w - 64 * S, 86 * S], fill=INK)              # station sign
    d.rectangle([w - 117 * S, 73 * S, w - 67 * S, 83 * S], fill=(250, 246, 240))
    hs = V.draw(d, 60 * S, h - 30 * S, u, dict(legB=(-18, 8), legF=(20, -4), armB=(-14, 6), armF=(28, 30)))
    (hx, hy), _ = hs[1]
    d.polygon([(hx - 4 * S, hy - 8 * S), (hx + 20 * S, hy - 12 * S), (hx + 22 * S, hy + 2 * S), (hx - 2 * S, hy + 6 * S)], fill=(250, 246, 240), outline=INK, width=S * 2)
    cells['A'] = im
    # B: the bell, mid-swing (frame 0 of an 8-drawing swing cycle)
    im, d = new('B', (.3, .4)); draw_bell(d, 120 * S, 70 * S, 2.6 * S, 18)
    for k in range(3):                                                             # ring lines
        d.arc([60 * S - k * 14 * S, 30 * S - k * 10 * S, 190 * S + k * 14 * S, 160 * S + k * 10 * S], 200, 250, fill=INK, width=2 * S)
    cells['B'] = im
    # C: she opens the envelope, the key slides out
    im, d = new('C'); floor(d, w, h, h - 18 * S)
    V2 = Puppet('visitor', 1)
    hs = V2.draw(d, 80 * S, h + 72 * S, 1.9 * S, dict(armB=(70, 30), armF=(100, -40), head=18))
    (hx, hy), _ = hs[1]
    d.polygon([(hx - 10 * S, hy - 14 * S), (hx + 36 * S, hy - 20 * S), (hx + 40 * S, hy + 8 * S), (hx - 6 * S, hy + 14 * S)], fill=(250, 246, 240), outline=INK, width=2 * S)
    d.line([(hx - 10 * S, hy - 14 * S), (hx + 18 * S, hy + 4 * S), (hx + 36 * S, hy - 20 * S)], fill=INK, width=2 * S)
    draw_key(d, hx + 34 * S, hy - 32 * S, 2.0 * S, -35)
    cells['C'] = im
    # D: the service door; a capped man behind its lit window
    im, d = new('D', (.62, .4)); floor(d, w, h, h - 22 * S)
    d.rectangle([130 * S, 16 * S, 236 * S, h - 22 * S], fill=INK)                  # door
    d.rectangle([146 * S, 34 * S, 220 * S, 100 * S], fill=(250, 232, 210))         # window, lit
    lay = Image.new('L', im.size, 0); M.draw(ImageDraw.Draw(lay), 190 * S, 200 * S, 1.5 * S, dict(head=-6, armB=(5, 5), armF=(5, 5)), fill=255)
    win = Image.new('L', im.size, 0); ImageDraw.Draw(win).rectangle([146 * S, 34 * S, 220 * S, 100 * S], fill=255)
    from PIL import ImageChops
    im.paste(Image.new('RGB', im.size, (60, 26, 20)), (0, 0), ImageChops.multiply(lay, win).filter(ImageFilter.GaussianBlur(1.5 * S)))
    d.rectangle([146 * S, 100 * S, 220 * S, 106 * S], fill=INK)
    d.line([(183 * S, 34 * S), (183 * S, 100 * S)], fill=INK, width=3 * S)
    d.ellipse([140 * S, 118 * S, 148 * S, 126 * S], fill=(250, 232, 210))           # knob glint
    cells['D'] = im
    # E: centre. She lifts the key; head turns up toward the bell & door (FK arm raise, frame 7 of 12)
    im, d = new('E', (.55, .3)); floor(d, w, h, h - 16 * S)
    hs = V.draw(d, 104 * S, h - 14 * S, 1.45 * S, dict(legB=(-4, 2), legF=(6, 0), armB=(8, 12), armF=(112, 30), head=-20))
    (hx, hy), a = hs[1]
    draw_key(d, hx + 8 * S, hy - 8 * S, 1.6 * S, -50)
    for k in range(4):                                                              # glint
        aa = math.radians(k * 45 + 20)
        d.line([(hx + 4 * S + 18 * S * math.cos(aa), hy - 40 * S + 14 * S * math.sin(aa)), (hx + 4 * S + 20 * S * math.cos(aa), hy - 40 * S + 20 * S * math.sin(aa))], fill=INK, width=2 * S)
    cells['E'] = im
    # F: bench; key left on it; she walks off right
    im, d = new('F'); floor(d, w, h, h - 24 * S)
    d.rectangle([30 * S, 120 * S, 150 * S, 128 * S], fill=INK)
    for xb in (40, 140): d.rectangle([xb * S, 128 * S, (xb + 6) * S, h - 24 * S], fill=INK)
    d.rectangle([30 * S, 96 * S, 150 * S, 102 * S], fill=INK); d.rectangle([34 * S, 96 * S, 40 * S, 120 * S], fill=INK); d.rectangle([140 * S, 96 * S, 146 * S, 120 * S], fill=INK)
    draw_key(d, 84 * S, 114 * S, 1.3 * S, 4)
    V.draw(d, 232 * S, h - 24 * S, 1.2 * S, dict(legB=(-20, 10), legF=(22, -4), armB=(20, 6), armF=(-18, 8)))
    cells['F'] = im
    # G: behind the door: the man pulls the bell rope
    im, d = new('G', (.35, .3)); floor(d, w, h, h - 20 * S)
    M2 = Puppet('man', 1)
    hs = M2.draw(d, 112 * S, h - 20 * S, 1.3 * S, dict(armB=(120, 20), armF=(160, -10), head=-15, legB=(-6, 2), legF=(8, 0)))
    (rx_, ry_), _ = hs[1]
    d.line([(rx_, 0), (rx_, ry_ + 30 * S)], fill=INK, width=3 * S); d.ellipse([rx_ - 6 * S, ry_ + 26 * S, rx_ + 6 * S, ry_ + 42 * S], fill=INK)
    cells['G'] = im
    # H: the bench again; nothing on it
    im, d = new('H'); floor(d, w, h, h - 24 * S)
    d.rectangle([70 * S, 120 * S, 190 * S, 128 * S], fill=INK)
    for xb in (80, 180): d.rectangle([xb * S, 128 * S, (xb + 6) * S, h - 24 * S], fill=INK)
    d.rectangle([70 * S, 96 * S, 190 * S, 102 * S], fill=INK); d.rectangle([74 * S, 96 * S, 80 * S, 120 * S], fill=INK); d.rectangle([180 * S, 96 * S, 186 * S, 120 * S], fill=INK)
    cells['H'] = im
    # I: the service door stays closed; the key sits in its lock
    im, d = new('I', (.4, .4)); floor(d, w, h, h - 22 * S)
    d.rectangle([90 * S, 16 * S, 196 * S, h - 22 * S], fill=INK)
    d.rectangle([90 * S, h - 25 * S, 196 * S, h - 22 * S], fill=(250, 232, 210))    # light under the door
    draw_key(d, 172 * S, 104 * S, 1.3 * S, 180)
    cells['I'] = im
    hints = {
        'A': dict(cap=None, bal=(GX0 + 104, GY0 + 36, GX0 + 214, GY0 + 72), tail=(GX0 + 78, GY0 + 62)),
        'C': dict(bal=(cell_box('C')[0] + 170, GY0 + 110, cell_box('C')[2] - 10, GY0 + 150), tail=(cell_box('C')[0] + 140, GY0 + 100)),
        'E': dict(bal=(cell_box('E')[0] + 160, cell_box('E')[1] + 56, cell_box('E')[2] - 8, cell_box('E')[1] + 106), tail=(cell_box('E')[0] + 126, cell_box('E')[1] + 58), bsz=15),
        'F': dict(bal=(cell_box('F')[0] + 120, cell_box('F')[1] + 12, cell_box('F')[0] + 214, cell_box('F')[1] + 48), tail=(cell_box('F')[0] + 228, cell_box('F')[1] + 56)),
        'I': dict(bal=(cell_box('I')[0] + 190, cell_box('I')[1] + 14, cell_box('I')[2] - 12, cell_box('I')[1] + 52), tail=(cell_box('I')[0] + 190, cell_box('I')[1] + 80)),
        'B': dict(sfx=(cell_box('B')[0] + 160, cell_box('B')[1] + 110)),
    }
    hints['A']['cap'] = (cell_box('A')[0] + 6, cell_box('A')[1] + 6)
    return cells, hints

# ======================================================================
# DIRECTION 2 - photo-collage cutout animation (foraged FSA/OWI, PD)
# ======================================================================
def loc(n): return cv2.imread(os.path.join(LOC, 'loc_%d.jpg' % n), cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.

def duotone(g, gamma=1.0, white=(250, 244, 236)):
    """two-ink print: black ink + salmon ink over paper (a print process, not a look filter:
    each panel of the page is printed in the same two inks)."""
    g = np.clip(g, 0, 1) ** gamma
    k = np.array(INK, np.float32); s = np.array(SAL, np.float32); wv = np.array(white, np.float32)
    t = g[..., None]
    out = np.where(t < .5, k + (s - k) * (t / .5), s + (wv - s) * ((t - .5) / .5))
    return out

def fit_crop(g, box, w, h):
    x0, y0, x1, y1 = box
    c = g[y0:y1, x0:x1]
    return cv2.resize(c, (w, h), interpolation=cv2.INTER_AREA)

def levels(g, lo, hi): return np.clip((g - lo) / (hi - lo), 0, 1)

def grabcut(gray, rect, fg_hint=None):
    im = cv2.cvtColor((gray * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    mask = np.zeros(gray.shape, np.uint8); bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(im, mask, rect, bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
    m = np.where((mask == 1) | (mask == 3), 1, 0).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n > 1: m = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    return m

def key_cutout():
    k = cv2.imread(os.path.join(MINE, 'skeletonkey.png'), cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.
    k = k[40:650, 150:450]
    m = (cv2.GaussianBlur(k, (5, 5), 0) < .55).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    m = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    ff = m.copy(); fm = np.zeros((m.shape[0] + 2, m.shape[1] + 2), np.uint8)
    cv2.floodFill(ff, fm, (0, 0), 2); hole = (ff == 0)
    m2 = m.copy(); m2[hole] = 0                                      # keep the bow hole open
    return k, m2

def paste(dst, src_rgb, mask, x, y, ang=0, scale=1.0, shadow=True):
    """paste a cut piece with its scissor edge and a thin drop shadow (cut paper on a page)."""
    h, w = mask.shape
    M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, scale)
    cos, sin = abs(M[0, 0]), abs(M[0, 1]); nw, nh = int(h * sin + w * cos), int(h * cos + w * sin)
    M[0, 2] += nw / 2 - w / 2; M[1, 2] += nh / 2 - h / 2
    s = cv2.warpAffine(src_rgb, M, (nw, nh)); m = cv2.warpAffine(mask.astype(np.float32), M, (nw, nh))
    m = cv2.GaussianBlur(m, (3, 3), 0)
    H_, W_ = dst.shape[:2]
    x0, y0 = int(x - nw / 2), int(y - nh / 2)
    for (ox, oy, col, mm) in ((((5, 5, np.array([60, 30, 24], np.float32), .35)) if shadow else (0, 0, None, 0)), (0, 0, None, 1)):
        if mm == 0: continue
        xa, ya, xb, yb = max(0, x0 + ox), max(0, y0 + oy), min(W_, x0 + ox + nw), min(H_, y0 + oy + nh)
        if xb <= xa or yb <= ya: continue
        sm = m[ya - y0 - oy:yb - y0 - oy, xa - x0 - ox:xb - x0 - ox][..., None]
        if col is not None:
            dst[ya:yb, xa:xb] = dst[ya:yb, xa:xb] * (1 - sm * mm) + col * sm * mm
        else:
            ss = s[ya - y0 - oy:yb - y0 - oy, xa - x0 - ox:xb - x0 - ox]
            dst[ya:yb, xa:xb] = dst[ya:yb, xa:xb] * (1 - sm) + ss * sm
    return dst

def dir2_cells():
    w, h = PW * S, PH * S; cells = {}
    def tone(g, gamma=1.0): return duotone(g, gamma * 1.35)
    # A: the empty waiting room (2017843779): rows of benches, one figure far off
    g = loc(2017843779); a = tone(levels(fit_crop(g, (90, 300, 965, 870), w, h), .05, .85), .9)
    cells['A'] = a
    # B: window wall with ceiling lamp (2017843789); the bell is cut from paper and hung on the photo
    g = loc(2017843789); b = tone(levels(fit_crop(g, (80, 90, 900, 625), w, h), .05, .9))
    cells['B'] = b
    # C: the counter of 2017843913 with its papers: the envelope + key are cut and laid on it
    g = loc(2017843913); c = tone(levels(fit_crop(g, (300, 430, 983, 878), w, h), .05, .9))
    cells['C'] = c
    # D: the dispatcher behind his window (2017844012) = the man behind the service door
    g = loc(2017844012); dd = tone(levels(fit_crop(g, (0, 30, 820, 566), w, h), .05, .85))
    cells['D'] = dd
    # E: window wall (2017843789) as stage; the woman in fur (2017843935) cut out by GrabCut,
    #    arm cut from her own coat sleeve and re-hinged at the shoulder, key (CC0) in the hand.
    g = loc(2017843789); e = tone(levels(fit_crop(g, (60, 380, 880, 916), w, h), .02, .8), 1.1)
    gw = loc(2017843935)
    # scissor line, placed by hand around the woman in fur (her back to us, facing the train door)
    poly = np.array([(440, 488), (400, 505), (378, 545), (366, 600), (318, 628), (286, 680), (268, 760), (258, 880),
                     (276, 968), (548, 968), (544, 860), (502, 800), (474, 720), (482, 640), (506, 600), (512, 540), (494, 502)], np.int32)
    cx0, cy0, cx1, cy1 = 250, 480, 560, 972
    pm = np.zeros(gw.shape, np.uint8); cv2.fillPoly(pm, [poly], 1); pm = pm[cy0:cy1, cx0:cx1]
    rgb = tone(levels(gw[cy0:cy1, cx0:cx1], .05, .95), 1.5)
    sc = 0.74
    ph, pw = pm.shape; ox = int(w * .44); oy = int(h + 24 * S - ph * sc / 2)
    # the raised arm: a strip of the same fur sleeve, hinged at her left shoulder (FK, frame 7 of 12)
    sl = gw[700:880, 292:346]; slm = np.ones(sl.shape, np.uint8)
    slm[:, :3] = 0; slm[:, -3:] = 0; slm[:4] = 0
    slr = tone(levels(sl, .05, .95), 1.5)
    shx = ox + (300 - cx0 - pw / 2) * sc; shy = oy + (650 - cy0 - ph / 2) * sc
    ang = 22                                        # degrees from vertical; 0 at rest, 34 at the top of the lift
    L = sl.shape[0] * sc
    ax = shx - math.sin(math.radians(ang)) * L / 2; ay = shy - math.cos(math.radians(ang)) * L / 2
    e = paste(e, slr, slm, int(ax), int(ay), ang, sc)
    e = paste(e, rgb, pm, ox, oy, 0, sc)
    k, km = key_cutout(); krgb = duotone(np.clip(k * 1.6 + .25, 0, 1), .8, (255, 236, 205))
    hx = shx - math.sin(math.radians(ang)) * L; hy = shy - math.cos(math.radians(ang)) * L
    e = paste(e, krgb, km, int(hx - 2 * S), int(hy + 2 * S), ang - 30, .085 * S)
    cells['E'] = e
    # F: the bench row, close (2017843779 lower right), the key left on the seat
    g = loc(2017843779); f_ = tone(levels(fit_crop(g, (430, 640, 965, 990), w, h), .05, .85), .9)
    f_ = paste(f_, krgb, km, int(w * .46), int(h * .42), 78, .11 * S)
    cells['F'] = f_
    # G: the conductor (2017844115) looking up; a paper bell-rope is laid into his hand
    g = loc(2017844115); gg = tone(levels(fit_crop(g, (0, 320, 791, 838), w, h), .05, .9))
    cells['G'] = gg
    # H: the same benches, further along: empty (2017843779 left)
    g = loc(2017843779); hh = tone(levels(fit_crop(g, (90, 470, 560, 778), w, h), .05, .85), .9)
    cells['H'] = hh
    # I: the barred window (2017844010) - closed; the key cut and set into its lock
    g = loc(2017844010); ii = tone(levels(fit_crop(g, (120, 20, 1000, 594), w, h), .05, .9))
    ii = paste(ii, krgb, km, int(w * .47), int(h * .63), 90, .10 * S)
    cells['I'] = ii
    out = {}
    for cid, arr in cells.items():
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)); out[cid] = im
    # hand-cut paper pieces (bell, envelope, rope) on top of the photographs
    d = ImageDraw.Draw(out['B']); draw_bell(d, 150 * S, 40 * S, 2.2 * S, 16, fill=INK)
    d = ImageDraw.Draw(out['C'])
    ex, ey = 150 * S, 70 * S
    d.polygon([(ex - 50 * S, ey), (ex + 50 * S, ey - 8 * S), (ex + 54 * S, ey + 52 * S), (ex - 46 * S, ey + 60 * S)], fill=(250, 244, 236), outline=INK, width=2 * S)
    d.line([(ex - 50 * S, ey), (ex + 2 * S, ey + 28 * S), (ex + 50 * S, ey - 8 * S)], fill=INK, width=2 * S)
    Image.Image.paste(out['C'], Image.fromarray(np.zeros((1, 1, 3), np.uint8)), (0, 0)) if False else None
    arr = np.asarray(out['C'], np.float32).copy(); arr = paste(arr, krgb, km, int(ex + 40 * S), int(ey - 6 * S), -50, .14 * S)
    out['C'] = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(out['G']); d.line([(150 * S, 0), (156 * S, 62 * S)], fill=(250, 244, 236), width=5 * S); d.line([(150 * S, 0), (156 * S, 62 * S)], fill=INK, width=2 * S)
    hints = {
        'A': dict(cap=(cell_box('A')[0] + 6, cell_box('A')[1] + 6), bal=(cell_box('A')[0] + 150, cell_box('A')[1] + 50, cell_box('A')[2] - 10, cell_box('A')[1] + 90), tail=(cell_box('A')[0] + 236, cell_box('A')[1] + 140)),
        'B': dict(sfx=(cell_box('B')[0] + 170, cell_box('B')[1] + 120)),
        'C': dict(bal=(cell_box('C')[0] + 170, cell_box('C')[1] + 110, cell_box('C')[2] - 8, cell_box('C')[1] + 150), tail=(cell_box('C')[0] + 150, cell_box('C')[1] + 180)),
        'E': dict(bal=(cell_box('E')[0] + 160, cell_box('E')[1] + 10, cell_box('E')[2] - 8, cell_box('E')[1] + 60), tail=(cell_box('E')[0] + 130, cell_box('E')[1] + 70), bsz=15),
        'F': dict(bal=(cell_box('F')[0] + 170, cell_box('F')[1] + 10, cell_box('F')[2] - 10, cell_box('F')[1] + 48), tail=(cell_box('F')[0] + 250, cell_box('F')[1] + 70)),
        'G': dict(cap=(cell_box('G')[0] + 6, cell_box('G')[1] + 150)),
        'I': dict(bal=(cell_box('I')[0] + 180, cell_box('I')[1] + 120, cell_box('I')[2] - 12, cell_box('I')[1] + 160), tail=(cell_box('I')[0] + 150, cell_box('I')[1] + 110)),
    }
    return out, hints

# ======================================================================
# DIRECTION 3 - nine archive screens (Moving Image Archive cache)
# ======================================================================
MIA = dict(A='b6e217eb_0.5', B='381d177e_4', C='9199c819_2', D='6a336c56_4', E='7102b861_2',
           F='a267fee7_0.5', G='ef7bfc89_12', H='46cd8d58_0.5', I='bb5ffe06_0.5')
def dir3_cells():
    w, h = PW * S, PH * S; out = {}
    for cid, k in MIA.items():
        im = cv2.imread(os.path.join(MINE, 'mia', k + '.png'))
        g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.
        hh, ww = g.shape; ar = w / h
        cw = min(ww, int(hh * ar)); ch = int(cw / ar); x0 = (ww - cw) // 2; y0 = (hh - ch) // 2
        g = cv2.resize(g[y0:y0 + ch, x0:x0 + cw], (w, h), interpolation=cv2.INTER_CUBIC)
        g = levels(g, np.percentile(g, 2), np.percentile(g, 98))
        if BG[cid] == 'W': arr = duotone(g ** 1.2)
        else: arr = duotone((g * .85) ** 1.35)                 # salmon panels print darker
        out[cid] = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(out['E'])                            # the key is the only cut-paper piece
    hints = {
        'A': dict(cap=(cell_box('A')[0] + 6, cell_box('A')[1] + 6), bal=(cell_box('A')[0] + 150, cell_box('A')[1] + 120, cell_box('A')[2] - 10, cell_box('A')[1] + 160), tail=(cell_box('A')[0] + 140, cell_box('A')[1] + 150)),
        'B': dict(sfx=(cell_box('B')[0] + 160, cell_box('B')[1] + 120)),
        'C': dict(bal=(cell_box('C')[0] + 8, cell_box('C')[1] + 10, cell_box('C')[0] + 110, cell_box('C')[1] + 50), tail=(cell_box('C')[0] + 130, cell_box('C')[1] + 80)),
        'E': dict(bal=(cell_box('E')[0] + 8, cell_box('E')[1] + 10, cell_box('E')[0] + 190, cell_box('E')[1] + 50), tail=(cell_box('E')[0] + 200, cell_box('E')[1] + 76), bsz=15),
        'F': dict(bal=(cell_box('F')[0] + 180, cell_box('F')[1] + 10, cell_box('F')[2] - 10, cell_box('F')[1] + 48), tail=(cell_box('F')[0] + 160, cell_box('F')[1] + 80)),
        'I': dict(bal=(cell_box('I')[0] + 180, cell_box('I')[1] + 10, cell_box('I')[2] - 12, cell_box('I')[1] + 48), tail=(cell_box('I')[0] + 150, cell_box('I')[1] + 90)),
    }
    return out, hints

# ======================================================================
NAMES = ['1  Ombres en croix (shadow puppets)', '2  Collage de gare (FSA cutouts)', '3  Neuf écrans (archive panels)']

def board(kfs):
    ref = Image.open(REF).convert('RGB')
    th = 380; ref = ref.resize((int(ref.size[0] * th * 2 / ref.size[1]), th * 2))
    cw = 675; ch = 380
    Wb = ref.size[0] + 2 * cw + 30; Hb = 2 * ch + 2 * 40 + 20
    sc = min(1, 2000 / Wb)
    bd = Image.new('RGB', (Wb, Hb), (30, 26, 24)); d = ImageDraw.Draw(bd)
    f = ImageFont.truetype(FB, 20)
    bd.paste(ref, (10, 40)); d.text((14, 10), 'reference: Lécroart, Quatre-vingt-quinze', font=f, fill='white')
    pos = [(ref.size[0] + 20, 40), (ref.size[0] + 30 + cw, 40), (ref.size[0] + 20, 40 + ch + 40)]
    for (x, y), k, n in zip(pos, kfs, NAMES):
        bd.paste(k.resize((cw, ch), Image.LANCZOS), (x, y)); d.text((x + 4, y - 28), n, font=f, fill='white')
    d.text((pos[2][0] + cw + 20, pos[2][1] + 20), 'all three at t = 44.5 s', font=f, fill='white')
    d.text((pos[2][0] + cw + 20, pos[2][1] + 50), 'DOWN route A D G B [E] H C F I', font=f, fill=(240, 140, 110))
    d.text((pos[2][0] + cw + 20, pos[2][1] + 80), 'entering E from B', font=f, fill='white')
    if sc < 1: bd = bd.resize((int(Wb * sc), int(Hb * sc)), Image.LANCZOS)
    return bd

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    kfs = []
    for i, fn in enumerate((dir1_cells, dir2_cells, dir3_cells), 1):
        cells, hints = fn()
        kf = page_frame(cells, hints)
        kf.save(os.path.join(OUT, 'kf-%d.png' % i)); kfs.append(kf)
    board(kfs).save(os.path.join(OUT, 'board.jpg'), quality=90)
    print('ok')
