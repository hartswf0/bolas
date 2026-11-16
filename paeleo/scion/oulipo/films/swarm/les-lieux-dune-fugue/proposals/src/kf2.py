"""KF2 La marche (rotoscoped line walk).
Walker rotoscoped frame by frame from Alice in Wonderland (W. W. Young, 1915, PD),
Moving Image Archive cache clip 147f497d, t = 1.5..3.3 s (6 fps sampling).
Background doorway traced from the Highsmith Columbus doorway (LoC 2010719611).
Each pose is GrabCut-matted, its outline and inner edges re-drawn as jittered ink strokes;
earlier poses stay as coloured-pencil roughs (onion skin)."""
import sys, random
sys.path.insert(0, sys.path[0])
from common import *
import cv2

W, H = 1280, 720
S = "/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/alice/a_%03d.png"
rng = np.random.default_rng(7)
random.seed(7)

# ---------------------------------------------------------------- paper
PAPER = np.array([0.905, 0.862, 0.770])
g = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
g = cv2.resize(cv2.GaussianBlur(g, (0, 0), 1.2), (W, H))
fib = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 0.6)
page = PAPER[None, None, :] * (1 + 0.018 * g[..., None] + 0.012 * fib[..., None])

# ---------------------------------------------------------------- traced facade (background)
door = load(SRC + "/hs_10700_10776.jpg")
fx0, fy0, fx1, fy1 = 160, 40, 1760, 1135          # facade crop in source px
sc = 0.40
fw, fh = int((fx1 - fx0) * sc), int((fy1 - fy0) * sc)
fac = fit_crop(door, (fx0, fy0, fx1, fy1), (fw, fh))
# placement: doorway centred where the walker starts (source frame 9 feet)
door_cx_src = (628 + 995) / 2
px = int(715 - (door_cx_src - fx0) * sc)
py = int(432 - (1115 - fy0) * sc)

L = lum(fac)
# wash: three tones, like a watercolour lay-in, warm stone + dark door
wash = np.zeros_like(fac)
tone = np.digitize(L, [0.22, 0.45, 0.62])
cols = [np.array(c) for c in [(0.20, 0.17, 0.14), (0.62, 0.54, 0.41), (0.76, 0.68, 0.54), (0.85, 0.79, 0.66)]]
for k, c in enumerate(cols):
    wash[tone == k] = c
wash = cv2.GaussianBlur(wash, (0, 0), 1.0)
# fade the drawing out toward its edges (a background sketch, not a photo)
yy, xx = np.mgrid[0:fh, 0:fw]
edge = np.minimum.reduce([xx, fw - xx, yy * 1.6, (fh - yy) * 3]) / 70.0
fade = np.clip(edge, 0, 1) ** 1.5
wash_a = (0.55 * fade)[..., None]
wash_a = np.where((tone == 0)[..., None], np.minimum(1.0, wash_a * 1.6), wash_a)
reg = page[py:py + fh, px:px + fw]
page[py:py + fh, px:px + fw] = reg * (1 - wash_a) + wash * wash_a

im = Image.fromarray((np.clip(page, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
ink = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(ink)


def jit(pts, a=0.9):
    return [(x + random.gauss(0, a), y + random.gauss(0, a)) for x, y in pts]


def stroke(pts, col, w, a=0.9, close=False):
    if len(pts) < 2:
        return
    p = jit(pts, a)
    if close:
        p = p + [p[0]]
    d.line(p, fill=col, width=w, joint="curve")


# trace facade edges -> contours -> simplified strokes
fg = (cv2.GaussianBlur((lum(fac) * 255).astype(np.uint8), (0, 0), 1.6))
ed = cv2.Canny(fg, 28, 70)
cs, _ = cv2.findContours(ed, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
for c in cs:
    if cv2.arcLength(c, False) < 22:
        continue
    ap = cv2.approxPolyDP(c, 1.2, False)[:, 0, :]
    mx, my = ap.mean(0)
    f = fade[int(min(my, fh - 1)), int(min(mx, fw - 1))]
    if f < 0.05:
        continue
    stroke([(px + x, py + y) for x, y in ap], (62, 46, 32, int(200 * f)), 1, a=0.35)

# pavement: hand-ruled seam and kerb running from the door toward the viewer
base = py + fh - int((1135 - 1115) * sc)
for x0, x1, al in [(px - 40, -200, 150), (px + fw + 40, W + 260, 150), (715, 700, 120)]:
    n = 30
    pts = [(x0 + (x1 - x0) * (i / n) ** 1.0, base + 2 + (H - base) * (i / n)) for i in range(n + 1)]
    stroke(pts, (70, 52, 36, al), 2, a=0.6)
stroke([(0, base + 3), (W, base + 3)], (70, 52, 36, 170), 2, a=0.5)
for i in range(1, 7):               # pavement joints in perspective
    y = base + (H - base) * (i / 7) ** 1.6
    stroke([(0, y), (W, y)], (70, 52, 36, 60 + 10 * i), 1, a=0.8)

# ---------------------------------------------------------------- rotoscope the walker
s, ox, oy = 3.0, 160, 0
poses = [9, 11, 13, 15, 17, 19]


def matte(i):
    a = cv2.imread(S % i)
    gl = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
    m = (gl > 200).astype(np.uint8)
    n, l, st, c = cv2.connectedComponentsWithStats(m)
    k = max(range(1, n), key=lambda k: st[k, 4] - (1000 if st[k, 1] < 60 or st[k, 3] < st[k, 2] * 0.7 else 0))
    x, y, w, h = st[k, :4]
    head = int(h * 0.42) + 4
    rect = (max(0, x - 8), max(0, y - head), w + 16, h + head + 10)
    big = cv2.resize(a, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    gm = np.zeros(big.shape[:2], np.uint8)
    bg, fgm = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    R = tuple(int(v * 4) for v in rect)
    cv2.grabCut(big, gm, R, bg, fgm, 5, cv2.GC_INIT_WITH_RECT)
    sure = cv2.resize((l == k).astype(np.uint8), None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST)
    gm[sure > 0] = cv2.GC_FGD
    cv2.grabCut(big, gm, R, bg, fgm, 3, cv2.GC_INIT_WITH_MASK)
    mm = np.where((gm == 1) | (gm == 3), 1, 0).astype(np.uint8)
    mm = cv2.morphologyEx(mm, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n2, l2, st2, _ = cv2.connectedComponentsWithStats(mm)
    if n2 > 1:
        kk = 1 + int(np.argmax(st2[1:, 4]))
        mm = (l2 == kk).astype(np.uint8)
    mm = cv2.GaussianBlur(mm.astype(np.float32), (0, 0), 3) > 0.5
    return big, mm.astype(np.uint8)


def to_kf(x, y):
    return (ox + x / 4 * s, oy + y / 4 * s)


pencil = [(196, 92, 64), (86, 112, 160)]
s, ox, oy = 2.6, 220, -20


def to_kf2(x, y):            # source px -> keyframe
    return (ox + x * s, oy + y * s)


# roughs: the dress matte of each earlier frame (threshold + largest blob), head as an oval
for j, i in enumerate(poses[:-1]):
    gl = cv2.cvtColor(cv2.imread(S % i), cv2.COLOR_BGR2GRAY)
    gl4 = cv2.resize(gl, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    m = (cv2.GaussianBlur(gl4, (0, 0), 2) > 196).astype(np.uint8)
    m[:int(55 * 4)] = 0
    n, l, st, _ = cv2.connectedComponentsWithStats(m)
    cand = [k for k in range(1, n) if st[k, 3] > st[k, 2] * 0.8 and st[k, 4] > 200]
    k = max(cand, key=lambda k: st[k, 4])
    cs, _ = cv2.findContours((l == k).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    ap = cv2.approxPolyDP(cs[0], 3.0, True)[:, 0, :]
    pts = [to_kf2(x / 4, y / 4) for x, y in ap]
    col = pencil[j % 2]
    alpha = int(80 + 130 * j / len(poses))
    stroke(pts, col + (alpha,), 2, a=1.0, close=True)
    stroke(pts, col + (alpha // 2,), 1, a=2.2, close=True)
    x, y, w, h = st[k, :4]
    r = w / 4 * 0.2 * s
    cx, cy = to_kf2((x + w / 2) / 4, y / 4)
    hp = [(cx + r * np.cos(t) * 0.85, cy - r * 1.1 + r * 1.15 * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 18)]
    stroke(hp, col + (alpha,), 2, a=0.8)
    d.text((cx + r + 6, cy - 2.6 * r), str(i).zfill(2), font=font("mono", 12), fill=col + (alpha,))

# key drawing (frame 19): traced by hand over a 4x enlargement of the source frame.
# crop origin (110, 100) in source px, enlargement 4.
K = {
 "hair_l": [(250,25),(228,32),(215,55),(210,85),(212,118)],
 "hair_r": [(250,25),(275,32),(290,55),(298,90),(306,114)],
 "face":   [(231,50),(229,76),(237,98),(250,107),(263,98),(271,74),(268,50)],
 "slv_l":  [(214,124),(186,134),(173,160),(177,188),(197,199)],
 "slv_r":  [(288,124),(318,134),(331,160),(326,188),(306,200)],
 "bodice": [(214,124),(250,118),(288,124)],
 "arm_l":  [(197,199),(204,214),(238,206),(255,211)],
 "arm_r":  [(306,200),(300,214),(264,207),(255,211)],
 "waist":  [(203,232),(250,236),(300,232)],
 "skirt_l":[(203,232),(176,300),(150,368),(130,420),(160,428)],
 "skirt_r":[(300,232),(330,300),(368,380),(400,438),(360,444)],
 "hem":    [(130,420),(175,430),(250,440),(320,446),(400,438)],
 "fold1":  [(232,250),(214,330),(200,425)],
 "fold2":  [(272,252),(290,340),(312,440)],
 "leg_l1": [(176,432),(173,482),(171,536)],
 "leg_l2": [(201,434),(201,482),(198,536)],
 "leg_r1": [(240,442),(240,495),(244,540)],
 "leg_r2": [(266,442),(268,495),(262,540)],
}
def spline(P, n=8):
    if len(P) < 3:
        return P
    P = [P[0]] + list(P) + [P[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = [np.array(P[k], float) for k in (i - 1, i, i + 1, i + 2)]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(tuple(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)))
    out.append(tuple(P[-2]))
    return out


def kp(p):
    x, y = p
    return to_kf2(110 + x / 4, 100 + y / 4)
fill = spline([kp(p) for p in K["slv_l"][::-1] + K["bodice"] + K["slv_r"] + [(300,232)] + K["skirt_r"][1:] + K["hem"][::-1] + K["skirt_l"][::-1][1:]], 4)
ImageDraw.Draw(ink).polygon(fill, fill=(240, 233, 216, 245))
headfill = spline([kp(p) for p in K["hair_l"] + K["hair_r"][::-1]])
ImageDraw.Draw(ink).polygon(headfill, fill=(62, 44, 30, 200))
ImageDraw.Draw(ink).polygon(spline([kp(p) for p in K["face"]]), fill=(236, 222, 200, 255))
for name, pts in K.items():
    w = 1 if name.startswith("fold") else 2
    col = (24, 18, 14, 150 if name.startswith("fold") else 255)
    P = spline([kp(p) for p in pts])
    stroke(P, col, w + 1, a=0.35)
    stroke(P, (24, 18, 14, 90), 1, a=0.9)
# hatching of the hair, line by line
for t in np.linspace(0.05, 0.95, 22):
    a_ = kp(K["hair_l"][int(t * 4.99)]); b_ = kp(K["hair_r"][int(t * 4.99)])
    xm = a_[0] + (b_[0] - a_[0]) * (0.12 if t > 0.25 else 0.5)
    d.line([(a_[0] + 2, a_[1] + t * 4), (a_[0] + 4, a_[1] + 14)], fill=(30, 22, 16, 160), width=1)
    d.line([(b_[0] - 2, b_[1] + t * 4), (b_[0] - 4, b_[1] + 14)], fill=(30, 22, 16, 160), width=1)

im = Image.alpha_composite(im, ink).convert("RGB")
dd = ImageDraw.Draw(im)
mono = font("mono", 14)
dd.text((24, 20), "P01 porte -> P02 carrefour   ·   rotoscopie, 12 i/s, en deux", font=mono, fill=(80, 60, 42))
dd.text((24, 40), "dessin 19 / roughs 09–17 (crayon) · source 1915, DP", font=mono, fill=(150, 90, 60))
dd.text((W - 120, 20), "00:14 / 00:56", font=mono, fill=(80, 60, 42))
ser = font("serif", 33)
cap = "« Je suis sortie par la porte cochère. Personne ne l'a vue se refermer. »"
tw = dd.textlength(cap, font=ser)
dd.text(((W - tw) / 2, H - 60), cap, font=ser, fill=(40, 28, 20))
im.save(OUT + "/kf-2.png")
print("ok")
