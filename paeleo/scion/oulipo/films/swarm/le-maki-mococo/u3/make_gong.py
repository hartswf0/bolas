"""U3 · HANDMADE bronze-card gong, cut into 12 wedges, plus twisted cord and knot (built in code, deterministic).

What it is: a disc of card (166 film px across, <= 180) painted bronze and hammered: a repoussé height field of
~420 overlapping hammer dimples laid in concentric courses (as gong smiths raise a gong), a raised boss, a
flat shoulder ring and a turned rim lip. Lit soft from the upper left (same light as the mouth). Cut with
scissors into 12 radial wedges; every cut edge shows the pale card core (lit on the up-left facing side).
Not wood grain: no periodic rings; marks are discrete facets with specular glints.
Outputs (2x film resolution) in imagecue/: gong_full.png, wedge_00..11.png (each a tight RGBA crop),
wedges.json (crop offsets + centroids relative to the gong centre), cord_tile.png, knot.png, gong_sheet.png
"""
import json, math
import numpy as np, cv2
from PIL import Image
D = "/home/user/bolas/paeleo/scion/oulipo/films/sources/le-maki-mococo/imagecue/"
S = 2
R = 83.0 * S                # disc radius (2x px) -> 166 film px across
PAD = int(10 * S)
N = int(2 * R + 2 * PAD)
C = N / 2.0
rs = np.random.RandomState(1895)
yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
dx, dy = xx - C, yy - C
r = np.hypot(dx, dy); th = np.arctan2(dy, dx)

# ---------------- height field (in 2x px units) ----------------
h = np.zeros((N, N), np.float32)
boss_r = 21 * S
h += 9.0 * S * np.clip(1 - (r / boss_r) ** 2, 0, 1) ** 0.8                 # domed boss
h += 1.6 * S * np.clip((r - (boss_r + 3 * S)) / (3 * S), 0, 1) * np.clip((0.60 * R - r) / (3 * S), 0, 1) * -1  # sunk face
h += 2.2 * S * np.exp(-((r - (R - 5 * S)) / (2.6 * S)) ** 2)               # turned rim lip
h += -1.2 * S * np.exp(-((r - 0.62 * R) / (1.5 * S)) ** 2)                  # shoulder groove
# hammer dimples in courses
courses = np.arange(boss_r + 6 * S, R - 9 * S, 7.2 * S)
for ci, cr in enumerate(courses):
    n = int(2 * math.pi * cr / (8.5 * S))
    off = rs.uniform(0, 2 * math.pi)
    for k in range(n):
        a = off + 2 * math.pi * k / n + rs.uniform(-0.08, 0.08)
        rr = cr + rs.uniform(-1.6, 1.6) * S
        x, y = C + rr * math.cos(a), C + rr * math.sin(a)
        e = rs.uniform(3.6, 5.4) * S
        x0, x1, y0, y1 = int(x - e - 2), int(x + e + 3), int(y - e - 2), int(y + e + 3)
        sx, sy = xx[y0:y1, x0:x1] - x, yy[y0:y1, x0:x1] - y
        # elongated along the course (tangential), like real hammer blows
        ca, sa = math.cos(a), math.sin(a)
        u = (sx * -sa + sy * ca) / (e * 1.25); v = (sx * ca + sy * sa) / e
        d2 = u * u + v * v
        h[y0:y1, x0:x1] -= rs.uniform(0.9, 1.7) * S * np.clip(1 - d2, 0, 1) ** 1.5
# a few stray blows on the boss and rim
for _ in range(40):
    a, rr = rs.uniform(0, 2 * math.pi), rs.choice([rs.uniform(0, boss_r * 0.8), rs.uniform(R - 9 * S, R - 3 * S)])
    x, y = C + rr * math.cos(a), C + rr * math.sin(a); e = rs.uniform(2.5, 4) * S
    d2 = ((xx - x) ** 2 + (yy - y) ** 2) / e ** 2
    h -= 0.7 * S * np.clip(1 - d2, 0, 1) ** 1.5
h = cv2.GaussianBlur(h, (0, 0), 0.8)

# ---------------- shading ----------------
gy, gx = np.gradient(h)
nrm = np.dstack([-gx, -gy, np.ones_like(h)]); nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
L = np.array([-0.45, -0.60, 0.66]); L /= np.linalg.norm(L)
Hh = L + np.array([0, 0, 1.0]); Hh /= np.linalg.norm(Hh)
diff = np.clip(nrm @ L, 0, 1)
spec = np.clip(nrm @ Hh, 0, 1) ** 38
# bronze albedo with patina (low-frequency, oxidised brown; a little darker in the hammered field)
pat = cv2.GaussianBlur(rs.randn(N, N).astype(np.float32), (0, 0), 14 * S); pat = pat / (np.abs(pat).max() + 1e-6)
grit = cv2.GaussianBlur(rs.randn(N, N).astype(np.float32), (0, 0), 0.9) * 0.05
alb = np.array([138, 96, 52], np.float32)[None, None] * (1 + 0.12 * pat[..., None] + grit[..., None])
alb = alb * (1 - 0.10 * ((r > boss_r) & (r < 0.6 * R))[..., None])
rgb = alb * (0.38 + 0.85 * diff[..., None]) + np.array([250, 214, 160], np.float32) * (0.50 * spec[..., None])
rgb = np.clip(rgb, 0, 255)

# ---------------- scissor-cut outline and wedges ----------------
def wobble(seed, n, amp):
    q = np.random.RandomState(seed).randn(n).astype(np.float32)
    q = np.convolve(np.r_[q, q, q], np.ones(9) / 9, "same")[n:2 * n]
    return q / (np.abs(q).max() + 1e-6) * amp
ANG = np.linspace(-math.pi, math.pi, 1440, endpoint=False)
rim_w = wobble(7, 1440, 0.9 * S)
# snips: tiny straight facets every ~6 px as scissors leave them
idx = ((th + math.pi) / (2 * math.pi) * 1440).astype(int) % 1440
disc = (r < R + rim_w[idx]).astype(np.float32)
wedges = []; meta = []
cut_a = [-math.pi / 2 + 2 * math.pi * k / 12 + np.random.RandomState(40 + k).uniform(-0.05, 0.05) for k in range(12)]
for k in range(12):
    a0, a1 = cut_a[k], cut_a[(k + 1) % 12] + (2 * math.pi if k == 11 else 0)
    # wobbly radial cut lines: the angle of each cut line drifts a little with radius
    w0 = wobble(100 + k, 512, 0.9 * S); w1 = wobble(100 + (k + 1) % 12, 512, 0.9 * S)
    ri = np.clip((r / (R + 2) * 511).astype(int), 0, 511)
    t = (th - a0) % (2 * math.pi)
    span = (a1 - a0) % (2 * math.pi)
    # perpendicular distance from each cut line (positive inside the wedge), with wobble
    d0 = r * np.sin(np.clip(t, -1, 1.6)) - w0[ri]
    d1 = r * np.sin(np.clip(span - t, -1, 1.6)) + w1[ri]
    inside = (t < span + 0.3) & (d0 > 0.3) & (d1 > 0.3)     # 0.3 px kerf: hairline seams when assembled
    m = disc * inside
    m = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 0.6)
    # pale card core on cut edges; lit on the side facing the light
    gm_y, gm_x = np.gradient(cv2.GaussianBlur(m, (0, 0), 1.0))
    edge = np.hypot(gm_x, gm_y); edge = edge / (edge.max() + 1e-6)
    facing = np.clip(-(gm_x * L[0] + gm_y * L[1]) / (np.hypot(gm_x, gm_y) + 1e-6), -1, 1)
    core = np.array([214, 196, 166], np.float32)
    wr = rgb * (1 - 0.5 * edge[..., None] * (facing[..., None] > 0)) + core * 0.5 * edge[..., None] * (facing[..., None] > 0)
    wr = wr * (1 - 0.35 * edge[..., None] * (facing[..., None] <= 0))
    a8 = np.clip(m * 255, 0, 255)
    ys, xs = np.nonzero(a8 > 3)
    x0, x1, y0, y1 = xs.min() - 2, xs.max() + 3, ys.min() - 2, ys.max() + 3
    spr = np.dstack([np.clip(wr, 0, 255), a8])[y0:y1, x0:x1].astype(np.uint8)
    # cord hole in the top wedge (and its neighbour) where the loop goes through
    hx, hy = C, C - R + 9 * S
    cy_, cx_ = np.mgrid[y0:y1, x0:x1]
    hole = np.hypot(cx_ - hx, cy_ - hy) < 3.0 * S
    spr[..., 3][hole] = 0
    ringh = (np.hypot(cx_ - hx, cy_ - hy) >= 3.0 * S) & (np.hypot(cx_ - hx, cy_ - hy) < 4.2 * S) & (spr[..., 3] > 0)
    spr[..., :3][ringh] = (spr[..., :3][ringh] * 0.55 + core * 0.45).astype(np.uint8)
    Image.fromarray(spr, "RGBA").save(D + f"wedge_{k:02d}.png")
    wy, wx = np.nonzero(spr[..., 3] > 127)
    cxw, cyw = wx.mean() + x0, wy.mean() + y0
    meta.append(dict(k=k, file=f"wedge_{k:02d}.png", offset_2x=[int(x0 - C), int(y0 - C)],
                     centroid_rel_centre_2x=[float(cxw - C), float(cyw - C)], cut_angles_rad=[float(a0), float(a1)],
                     mid_angle_rad=float(a0 + span / 2), area_2x=int((spr[..., 3] > 127).sum())))
    wedges.append((spr, x0, y0))
full = np.zeros((N, N, 4), np.float32)
for spr, x0, y0 in wedges:
    a = spr[..., 3:4] / 255.0
    reg = full[y0:y0 + spr.shape[0], x0:x0 + spr.shape[1]]
    reg[..., :3] = spr[..., :3] * a + reg[..., :3] * (1 - a); reg[..., 3:4] = a + reg[..., 3:4] * (1 - a)
Image.fromarray(np.dstack([full[..., :3], full[..., 3] * 255]).astype(np.uint8), "RGBA").save(D + "gong_full.png")
json.dump(dict(scale=S, radius_2x=R, diameter_film_px=2 * R / S, canvas_2x=N, centre_2x=C,
               hole_rel_centre_2x=[0.0, float(-R + 9 * S)], wedges=meta,
               made="HANDMADE in code: hammered bronze card disc, 12 scissor-cut wedges (make_gong.py, seed 1895)"),
          open(D + "wedges.json", "w"), indent=1)

# ---------------- twisted two-ply cord (tile) and knot ----------------
CW_, CH_ = int(8 * S), int(200 * S)
cy2, cx2 = np.mgrid[0:CH_, 0:CW_].astype(np.float32)
pitch = 4.2 * S
xc = CW_ / 2.0
half = 1.7 * S                                   # cord ~3.4 film px thick
d = (cx2 - xc) / half                            # -1..1 across the cord
a = np.clip((1 - np.abs(d)) * 3.0, 0, 1)
round_ = np.sqrt(np.clip(1 - d * d, 0, 1))       # cylinder shading, lit from the left
lit = np.clip(0.55 + 0.45 * (-d * 0.6 + round_ * 0.8), 0, 1.2)
twist = 0.5 + 0.5 * np.cos(2 * math.pi * ((cy2 - d * half * 1.1) / pitch))   # diagonal ply grooves
col = np.array([158, 124, 86], np.float32)[None, None] * (lit * (0.80 + 0.28 * twist))[..., None]
col *= (1 - 0.30 * (twist < 0.18))[..., None]    # the groove between plies
fib = cv2.GaussianBlur(rs.randn(CH_, CW_).astype(np.float32), (0, 0), 0.6) * 9
col = np.clip(col + fib[..., None], 0, 255)
# stray fibres (hairs) off the cord
hair = np.zeros((CH_, CW_), np.float32)
for _ in range(22):
    y = rs.uniform(0, CH_); side = rs.choice([-1, 1]); L_ = rs.uniform(1.0, 2.5) * S
    for s_ in np.linspace(0, 1, 8):
        yy_ = int(y + s_ * L_ * 0.6) % CH_; xx_ = int(np.clip(xc + side * (half + s_ * L_ * 0.8), 0, CW_ - 1))
        hair[yy_, xx_] = 0.35
a = np.maximum(a, hair)
cord = np.dstack([col, a * 255])
Image.fromarray(cord.astype(np.uint8), "RGBA").save(D + "cord_tile.png")
KN = int(26 * S)
kn = np.zeros((KN, KN, 4), np.float32)
ky, kx = np.mgrid[0:KN, 0:KN].astype(np.float32)
krs = np.random.RandomState(3)
for i in range(11):   # wraps of cord around the knot, each a short lit twist
    a = krs.uniform(0, 2 * math.pi); ox, oy = krs.uniform(-3.5, 3.5) * S, krs.uniform(-3, 3.5) * S
    ex, ey = krs.uniform(3.0, 4.6) * S, krs.uniform(1.6, 2.4) * S
    u = ((kx - KN / 2 - ox) * math.cos(a) + (ky - KN / 2 - oy) * math.sin(a)) / ex
    v = (-(kx - KN / 2 - ox) * math.sin(a) + (ky - KN / 2 - oy) * math.cos(a)) / ey
    d2 = u * u + v * v
    al = np.clip((1 - d2) * 4, 0, 1)
    lit = np.clip(1 - ((u + 0.35) ** 2 + (v + 0.45) ** 2), 0, 1)
    col = np.array([128, 94, 62], np.float32) * (0.75 + 0.5 * lit[..., None])
    kn[..., :3] = col * al[..., None] + kn[..., :3] * (1 - al[..., None]); kn[..., 3] = np.maximum(kn[..., 3], al)
Image.fromarray(np.dstack([np.clip(kn[..., :3], 0, 255), kn[..., 3] * 255]).astype(np.uint8), "RGBA").save(D + "knot.png")

# sheet for inspection: gong on white, exploded wedges, cord, knot
sheet = Image.new("RGB", (N * 3, N), (255, 255, 255))
g = Image.open(D + "gong_full.png"); sheet.paste(g, (0, 0), g)
for k, (spr, x0, y0) in enumerate(wedges):
    m = meta[k]["mid_angle_rad"]
    im = Image.fromarray(spr, "RGBA"); sheet.paste(im, (int(N + x0 + 30 * math.cos(m)), int(y0 + 30 * math.sin(m))), im)
c = Image.open(D + "cord_tile.png").resize((CW_ * 3, CH_ * 3 // 2)); sheet.paste(c, (2 * N + 40, 0), c)
k_ = Image.open(D + "knot.png").resize((KN * 4, KN * 4)); sheet.paste(k_, (2 * N + 120, 60), k_)
sheet.save(D + "gong_sheet.png")
print("gong", 2 * R / S, "film px; canvas", N)
