"""Direction 2: cut-paper silhouette puppets on a backlit comic page (Reiniger / tabletop paper capture)."""
import math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
from page import font, PAPER, INK

OUT = '/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways-subjective/proposals/'
Wd, Ht = 1280, 720
rng = np.random.default_rng(11)

# ---- backlit paper: fibre noise + glow
def fibre(h, w, seed):
    r = np.random.default_rng(seed)
    n = r.normal(0, 1, (h, w)).astype(np.float32)
    a = cv2.GaussianBlur(n, (0, 0), 1.0) * 0.5 + cv2.GaussianBlur(n, (0, 0), 6) * 2.5
    k = np.zeros((1, 25), np.float32); k[0] = 1 / 25
    a += cv2.filter2D(n, -1, k) * 1.5          # long fibres
    return a

def lightbox(box, seed):
    x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    g = 1 - 0.35 * (((xx - w * .45) / w) ** 2 + ((yy - h * .4) / h) ** 2)
    f = fibre(h, w, seed)
    L = np.clip(g * 238 + f * 5, 150, 255)
    rgb = np.stack([L, L * 0.965, L * 0.90], -1)
    return rgb

page = np.zeros((Ht, Wd, 3), np.float32)
# gutters: grey board card, opaque
card = fibre(Ht, Wd, 2)
page[...] = np.stack([58 + card * 3, 55 + card * 3, 50 + card * 3], -1)
P = {1: (28, 28, 436, 350), 2: (450, 28, 846, 350), 3: (860, 28, 1252, 350),
     4: (28, 364, 640, 692), 5: (654, 364, 944, 692), 6: (958, 364, 1252, 692)}
for k, b in P.items():
    x0, y0, x1, y1 = b
    page[y0:y1, x0:x1] = lightbox(b, k)

# silhouettes are drawn into a mask per depth plane: 0 = against the screen (sharp), 1 = nearer the lamp (soft shadow)
ACC_S = np.zeros((Ht, Wd), np.float32); ACC_F = np.zeros((Ht, Wd), np.float32)
sharp = soft = None; CUR = None
def begin(k):
    global sharp, soft, S, F, CUR
    flush()
    sharp = Image.new('L', (Wd, Ht), 0); soft = Image.new('L', (Wd, Ht), 0)
    S = ImageDraw.Draw(sharp); F = ImageDraw.Draw(soft); CUR = P.get(k)
def flush():
    global ACC_S, ACC_F
    if CUR is None: return
    m = np.zeros((Ht, Wd), np.float32); x0, y0, x1, y1 = CUR; m[y0:y1, x0:x1] = 1
    ACC_S = np.maximum(ACC_S, np.asarray(sharp, np.float32) / 255 * m)
    ACC_F = np.maximum(ACC_F, np.asarray(soft, np.float32) / 255 * m)

def snip(pts, amp=1.0):
    """scissor-cut edge: tiny straight facets with slight jitter"""
    out = []
    for i in range(len(pts)):
        p, q = pts[i], pts[(i + 1) % len(pts)]
        n = max(1, int(math.dist(p, q) / 9))
        for j in range(n):
            t = j / n
            out.append((p[0] + (q[0] - p[0]) * t + rng.normal(0, amp), p[1] + (q[1] - p[1]) * t + rng.normal(0, amp)))
    return out

def rect(d, x0, y0, x1, y1, fill=255):
    d.polygon(snip([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]), fill=fill)

def seg(d, p, ang, ln, w0, w1, fill=255):
    """one puppet limb piece from pivot p along ang; returns end pivot"""
    ca, sa = math.cos(ang), math.sin(ang)
    q = (p[0] + ca * ln, p[1] + sa * ln)
    nx, ny = -sa, ca
    poly = [(p[0] + nx * w0, p[1] + ny * w0), (q[0] + nx * w1, q[1] + ny * w1), (q[0] - nx * w1, q[1] - ny * w1), (p[0] - nx * w0, p[1] - ny * w0)]
    d.polygon(snip(poly, .6), fill=fill)
    d.ellipse([p[0] - w0, p[1] - w0, p[0] + w0, p[1] + w0], fill=fill)
    d.ellipse([q[0] - w1, q[1] - w1, q[0] + w1, q[1] + w1], fill=fill)
    return q

PINS = []
def hand(d, base, a_fore, a_palm, fingers, s=1.0, thumb=0.6):
    """FK chain: forearm -> palm -> 4 fingers (2 segments) + thumb. angles in radians."""
    wrist = seg(d, base, a_fore, 210 * s, 34 * s, 26 * s)
    PINS.append(wrist + (CUR,))
    ca, sa = math.cos(a_palm), math.sin(a_palm)
    knuck = (wrist[0] + ca * 62 * s, wrist[1] + sa * 62 * s)
    nx, ny = -sa, ca
    palm = [(wrist[0] + nx * 28 * s, wrist[1] + ny * 28 * s), (knuck[0] + nx * 34 * s, knuck[1] + ny * 34 * s),
            (knuck[0] - nx * 30 * s, knuck[1] - ny * 30 * s), (wrist[0] - nx * 26 * s, wrist[1] - ny * 26 * s)]
    d.polygon(snip(palm, .6), fill=255)
    for i, (f1, f2) in enumerate(fingers):
        off = (i - 1.5) * 20 * s
        root = (knuck[0] + nx * off, knuck[1] + ny * off)
        ln = [36, 42, 40, 30][i] * s
        m = seg(d, root, a_palm + f1, ln, 9 * s, 8 * s); PINS.append(m + (CUR,))
        seg(d, m, a_palm + f1 + f2, ln * .8, 8 * s, 6.5 * s)
    tb = (wrist[0] + nx * 26 * s + ca * 14 * s, wrist[1] + ny * 26 * s + sa * 14 * s)
    m = seg(d, tb, a_palm + thumb + 0.6, 34 * s, 11 * s, 9 * s); PINS.append(m + (CUR,))
    seg(d, m, a_palm + thumb + 0.2, 26 * s, 9 * s, 7 * s)

def clipdraw(box):
    """return a draw context for one panel (we clip by masking later)"""
    return box

# ---- panel 1: two hands on a typewriter keyboard (cut paper), seen from the typist's eyes
begin(1)
x0, y0, x1, y1 = P[1]
S.polygon(snip([(x0 + 70, y0 + 120), (x1 - 70, y0 + 120), (x1 - 20, y1), (x0 + 20, y1)]), fill=255)   # machine body in perspective
S.polygon(snip([(x0 + 120, y0 + 20), (x1 - 120, y0 + 20), (x1 - 110, y0 + 118), (x0 + 110, y0 + 118)]), fill=255)  # paper bail/sheet card
keys = Image.new('L', (Wd, Ht), 0); KD = ImageDraw.Draw(keys)
for r in range(4):
    for i in range(10 - r % 2):
        cx = x0 + 105 + i * (21 + r * 3) + r * 8 - r * r * 4; cy = y0 + 150 + r * 38
        KD.ellipse([cx - 8 - r, cy - 7 - r, cx + 8 + r, cy + 7 + r], fill=255)
sheet = Image.new('L', (Wd, Ht), 0); ImageDraw.Draw(sheet).polygon(snip([(x0 + 132, y0 + 28), (x1 - 132, y0 + 28), (x1 - 124, y0 + 108), (x0 + 124, y0 + 108)]), fill=255)
hand(F, (x0 + 40, y1 + 90), -0.95, -1.15, [(-.2, .7), (-.08, .8), (.05, .8), (.18, .7)], s=.75, thumb=.9)
hand(F, (x1 - 40, y1 + 90), -2.19, -1.99, [(.2, -.7), (.08, -.8), (-.05, -.8), (-.18, -.7)], s=.75, thumb=-2.6)

# ---- panel 2: the note, pinned, and a pencil hand
begin(2)
x0, y0, x1, y1 = P[2]
rect(S, x0, y1 - 80, x1, y1)                                         # desk edge
S.polygon(snip([(x0 + 120, y0 + 60), (x0 + 300, y0 + 48), (x0 + 312, y0 + 210), (x0 + 128, y0 + 222)]), fill=255)
note = Image.new('L', (Wd, Ht), 0); ND = ImageDraw.Draw(note)
ND.polygon(snip([(x0 + 132, y0 + 72), (x0 + 290, y0 + 62), (x0 + 300, y0 + 198), (x0 + 140, y0 + 208)]), fill=255)
fnt = font(44, 'serif')
ND.text((x0 + 160, y0 + 100), 'MILK', font=fnt, fill=0)
ND.text((x0 + 172, y0 + 150), '— now', font=font(30, 'serif'), fill=0)
hand(F, (x1 + 10, y1 + 20), -2.4, -2.75, [(.25, .9), (.2, 1.1), (.1, 1.2), (0, 1.2)], s=.85, thumb=-1.9)
seg(F, (x0 + 255, y0 + 230), -2.6, 110, 5, 3)                        # pencil

# ---- panel 3: hallway, the stair rising out of frame; the offscreen voice arrives on a rod from above the panel
begin(3)
x0, y0, x1, y1 = P[3]
rect(S, x0, y0, x0 + 60, y1); rect(S, x1 - 70, y0, x1, y1)           # door jambs (we look out through the doorway)
rect(S, x0, y0, x1, y0 + 26)
for i in range(7):                                                     # stair rising left to right, out of the top
    sx = x0 + 70 + i * 44; sy = y1 - 20 - i * 40
    S.polygon(snip([(sx, sy), (sx + 44, sy), (sx + 44, sy - 40), (sx + 88, sy - 40), (sx + 88, y1), (sx, y1)]), fill=255)
for i in range(7):                                                     # banister posts
    bx = x0 + 96 + i * 44; by = y1 - 40 - i * 40
    rect(S, bx, by - 90, bx + 6, by)
S.line([(x0 + 96, y1 - 130), (x0 + 96 + 7 * 44, y1 - 130 - 7 * 40)], fill=255, width=10)
bal3 = (x0 + 150, y0 + 105)

# ---- panel 4: the head turn: the kitchen strip has slid left; the clock enters at the right edge
begin(4)
x0, y0, x1, y1 = P[4]
shift = 170                                                           # strip offset at this frame
rect(S, x0, y1 - 70, x1, y1)                                          # counter
rect(S, x0 + 40 - shift, y0 + 40, x0 + 300 - shift, y0 + 200)         # window frame (sliding out left)
S.rectangle([x0 + 52 - shift, y0 + 52, x0 + 288 - shift, y0 + 188], fill=0)
rect(S, x0 + 164 - shift, y0 + 40, x0 + 176 - shift, y0 + 200)
rect(S, x0 + 40 - shift, y0 + 114, x0 + 300 - shift, y0 + 126)
rect(S, x0 + 330, y0 + 210, x0 + 400, y1 - 70)                        # kettle body
S.ellipse([x0 + 318, y0 + 190, x0 + 412, y0 + 240], fill=255)
cx, cy, r = x1 - 150, y0 + 130, 86                                    # wall clock
S.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
dial = Image.new('L', (Wd, Ht), 0); DD = ImageDraw.Draw(dial)
DD.ellipse([cx - r + 12, cy - r + 12, cx + r - 12, cy + r - 12], fill=255)
for k in range(12):
    a = k * math.pi / 6
    DD.polygon(snip([(cx + math.sin(a) * (r - 18) - 3, cy - math.cos(a) * (r - 18)), (cx + math.sin(a) * (r - 18) + 3, cy - math.cos(a) * (r - 18)),
                     (cx + math.sin(a) * (r - 34) + 3, cy - math.cos(a) * (r - 34)), (cx + math.sin(a) * (r - 34) - 3, cy - math.cos(a) * (r - 34))], .3), fill=0)
for frac, ln, w in ((1.25 / 12, 42, 7), (0.25, 62, 4)):
    a = frac * 2 * math.pi
    seg(DD, (cx, cy), a - math.pi / 2, ln, w, w * .6, fill=0)
hand(F, (x0 + 120, y1 + 50), -1.2, -1.45, [(-.1, .3), (0, .2), (.05, .3), (.1, .5)], s=.9)  # hand resting on counter

# ---- panel 5: arm opens the refrigerator door
begin(5)
x0, y0, x1, y1 = P[5]
rect(S, x0 + 40, y0 + 20, x0 + 210, y1)                               # fridge body
S.rectangle([x0 + 60, y0 + 40, x0 + 190, y1], fill=0)
for i in range(4):
    rect(S, x0 + 60, y0 + 90 + i * 60, x0 + 190, y0 + 98 + i * 60)
S.polygon(snip([(x0 + 210, y0 + 20), (x1 - 10, y0 + 50), (x1 - 10, y1 - 10), (x0 + 210, y1)]), fill=255)  # door swung toward us
hand(F, (x1 + 60, y1 + 30), -2.5, -2.9, [(.5, 1.0), (.45, 1.1), (.4, 1.1), (.35, 1.0)], s=.85, thumb=-2.2)

# ---- panel 6: fridge shelves, an empty hand hanging in front of them
begin(6)
x0, y0, x1, y1 = P[6]
rect(S, x0, y0, x0 + 30, y1); rect(S, x1 - 30, y0, x1, y1)
for i in range(3):
    sy = y0 + 110 + i * 90
    rect(S, x0 + 30, sy, x1 - 30, sy + 10)
    for j, (bw, bh) in enumerate([(40, 70), (26, 50), (60, 40), (34, 64)]):
        bx = x0 + 50 + j * 60 + (i * 17) % 23
        S.rounded_rectangle([bx, sy - bh, bx + bw, sy], 8, fill=255)
hand(F, (x0 + 130, y1 + 70), -1.5, -1.5, [(.3, .4), (.25, .5), (.2, .5), (.15, .5)], s=.95, thumb=.2)

# --- clip each silhouette layer to the panel windows
begin(None)
win = Image.new('L', (Wd, Ht), 0); WD = ImageDraw.Draw(win)
for b in P.values():
    WD.rectangle(b, fill=255)
wa = np.asarray(win, np.float32) / 255
sh = ACC_S * wa
sf = ACC_F
# soft (nearer the lamp) layer casts a penumbra on the screen and is itself slightly blurred
sf_shadow = cv2.GaussianBlur(np.roll(sf, (10, 8), (0, 1)), (0, 0), 9) * 0.45 * wa
sf_body = cv2.GaussianBlur(sf, (0, 0), 1.3) * wa
dl = np.asarray(dial, np.float32) / 255 * wa
nt = np.asarray(note, np.float32) / 255 * wa
sh_b = cv2.GaussianBlur(sh, (0, 0), .7)
dark = np.clip(np.maximum(sh_b, sf_body), 0, 1)
dark = np.maximum(dark, sf_shadow)
# the note and dial are translucent paper inlays: lighter than black
dark = np.where((dl > .5), np.maximum(sf_body, 0.0), dark)
for lay in (np.asarray(keys, np.float32) / 255, np.asarray(sheet, np.float32) / 255):
    dark = np.where(lay > .5, np.maximum(np.maximum(sf_body, sf_shadow), 0.0) * 1 + 0.0, dark) if lay is not None else dark
nt_paper = nt > .5
dark = np.where(nt_paper, np.maximum(sf_body, sf_shadow), dark)
lit = page * (1 - dark[..., None] * 0.93)
# note paper: laid on top of a cut card window -> slightly greyer, letters show black
notemask = nt
lit = np.where(notemask[..., None] > .5, lit * np.array([0.93, 0.9, 0.84]) * (1 - np.maximum(sf_body, sf_shadow)[..., None] * .9) + np.array([30, 28, 20]) * 0, lit)
img = Image.fromarray(np.clip(lit, 0, 255).astype(np.uint8), 'RGB')

# ---- balloons: white card cut-outs on black rods poking in from outside the panel
from page import balloon
def rod_balloon(cx, cy, text, rod_from, box, size=26):
    d = ImageDraw.Draw(img)
    m = Image.new('L', (Wd, Ht), 0); ImageDraw.Draw(m).rectangle(box, fill=255)
    rodl = Image.new('RGB', (Wd, Ht), (14, 13, 12)); rm = Image.new('L', (Wd, Ht), 0)
    ImageDraw.Draw(rm).line([rod_from, (cx, cy)], fill=255, width=6)
    rm = Image.fromarray(np.minimum(np.asarray(rm), np.asarray(m)))
    img.paste(rodl, (0, 0), rm)
    balloon(img, cx, cy, text, (cx, cy), size=size, clip=box, rng=np.random.default_rng(int(cx)), fill=(246, 242, 230))

rod_balloon(bal3[0], bal3[1], 'What time\nis it?', (P[3][0] + 120, -40), P[3])
balloon(img, P[4][0] + 170, P[4][1] + 260, 'Quarter\npast one!', (P[4][0] + 120, P[4][3]), size=25, clip=P[4], fill=(246, 242, 230))
rod_balloon(P[5][0] + 140, P[5][1] + 60, 'Thanks!', (P[5][2] + 120, P[5][1] - 60), P[5], size=24)
balloon(img, P[6][0] + 150, P[6][1] + 52, 'What was I after?', (P[6][2] - 60, P[6][3]), size=22, clip=P[6], fill=(246, 242, 230))
# pins at puppet joints (brass fasteners catching a little front light)
d = ImageDraw.Draw(img)
for (px, py, b) in PINS:
    if b[0] + 4 < px < b[2] - 4 and b[1] + 4 < py < b[3] - 4:
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(120, 98, 52))
# the pull-tab of the kitchen panorama strip sticks out into the gutter: the head turn is this strip being drawn left
x0, y0, x1, y1 = P[4]
tab = [(x0 - 22, y0 + 210), (x0 + 2, y0 + 204), (x0 + 2, y0 + 262), (x0 - 22, y0 + 256)]
d.polygon(tab, fill=(214, 204, 182), outline=(40, 36, 30))
d.line([(x0 - 2, y0 + 205), (x1 - 2, y0 + 205)], fill=(150, 140, 120), width=1)  # faint strip edge, seen through the screen
img.save(OUT + 'kf-2.png')
print('ok')
