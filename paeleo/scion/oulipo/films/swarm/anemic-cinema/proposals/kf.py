"""Anemic cinema: three proposal keyframes plus the board. Deterministic.

kf-1  Cire chaude          foraged 1942 record-pressing footage, printed negative,
                           an original pun engraved as a spiral on the poured pool.
kf-2  Le cerne se delie     procedural eccentric-ring disc caught mid-substitution:
                           outer rings have become the spiral sentence.
kf-3  Anneaux de clefs      collage optical disc: one foraged key photograph,
                           GrabCut matte, laid out as eccentric rings of keys.

Run: python3 -I kf.py   (from anywhere; paths are absolute)
"""
import math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = "/home/user/bolas/paeleo/scion/oulipo"
SRC = ROOT + "/films/sources/anemic-cinema"
OUT = ROOT + "/films/swarm/anemic-cinema/proposals"
REF = ROOT + "/assets/references"
W, H = 1280, 720
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
rng = np.random.default_rng(1926)


def font(px):
    return ImageFont.truetype(FONT, px)


def glyph_spiral(n, phrase, r_out, pitch, px, a0=-math.pi * 0.62, r_min=40, track=0.78):
    """Glyphs on an inward Archimedean spiral, clockwise, tops facing outward.

    Returns an L image n x n and the list of (char, radius, angle) in token order,
    which is the GlyphPath the proof checks (order preserved by construction)."""
    img = Image.new("L", (n, n), 0)
    c = n / 2
    f = font(px)
    rr, a = r_out, a0
    path = []
    for ch in phrase:
        g = Image.new("L", (px * 2, px * 2), 0)
        ImageDraw.Draw(g).text((px, px), ch, font=f, fill=255, anchor="mm")
        g = g.rotate(-math.degrees(a) - 90, resample=Image.BICUBIC)
        x, y = c + rr * math.cos(a), c + rr * math.sin(a)
        img.paste(255, (int(round(x - px)), int(round(y - px))), g)
        path.append((ch, rr, a))
        w = f.getlength(ch) if ch != " " else px * 0.45
        step = (w + px * (1 - track) + 2) / rr
        a += step
        rr -= pitch * step / (2 * math.pi)
        if rr < r_min:
            break
    return img, path


def sphere(n, light=(0.45, -0.5, 0.74), lo=50, hi=205, gamma=1.3):
    y, x = (np.mgrid[0:n, 0:n].astype(np.float32) - n / 2) / (n / 2)
    r = np.hypot(x, y)
    z = np.sqrt(np.clip(1 - r * r, 0, 1))
    lum = np.clip(x * light[0] + y * light[1] + z * light[2], 0, 1) ** gamma
    alpha = np.clip((1 - r) * n * 0.45, 0, 1)
    return lo + (hi - lo) * lum, alpha, r


def put_center(canvas, arr, alpha, cx, cy):
    """Composite a grey array with alpha onto canvas (float HxW) centred at cx, cy."""
    h, w = arr.shape
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    sub = canvas[y0:y0 + h, x0:x0 + w]
    sub[:] = sub * (1 - alpha) + arr * alpha


def to_rgb(grey, tint=(1.0, 1.0, 1.0)):
    g = np.clip(grey, 0, 255)[..., None] * np.array(tint)[None, None]
    return Image.fromarray(np.clip(g, 0, 255).astype(np.uint8), "RGB")


# ---------------------------------------------------------------- kf-1
PUN1 = ("ON SONNE LE BAN SUR LE BANC DE LA GARE · LA CLEF DES CHAMPS "
        "N'OUVRE QUE LE CHAMP DES CLEFS (PORTE CLOSE) · ")


def kf1():
    src = np.asarray(Image.open(SRC + "/cp_pour_7.8.png").convert("L"), np.float32)
    sh, sw = src.shape                                  # 240 x 320
    S = 3                                               # 960 x 720, 4:3 pillarbox
    big = cv2.resize(cv2.GaussianBlur(src, (0, 0), 0.6), (sw * S, sh * S), interpolation=cv2.INTER_CUBIC)
    # the pool: darkest connected region in the middle of the frame
    small = cv2.GaussianBlur(src, (5, 5), 0)
    m = (small < 70).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    nlab, lab, stats, cents = cv2.connectedComponentsWithStats(m)
    k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    pool = (lab == k).astype(np.uint8)
    cnts, _ = cv2.findContours(pool, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    (ex, ey), (ea, eb), eang = cv2.fitEllipse(max(cnts, key=cv2.contourArea))
    ex, ey, ea, eb = ex * S, ey * S, ea * S, eb * S
    pool_big = cv2.resize(pool.astype(np.float32), (sw * S, sh * S), interpolation=cv2.INTER_LINEAR)
    pool_big = cv2.GaussianBlur(pool_big, (0, 0), 3)
    # negative print, then a tone curve so the pool sits at a lit mid-grey
    neg = 255 - big
    t = neg / 255.0
    neg = 255 * np.clip((t - 0.38) / 0.62, 0, 1) ** 1.6
    neg = cv2.bilateralFilter(neg.astype(np.float32), 9, 18, 6)
    neg = neg * (0.04 + 0.96 * np.clip(pool_big * 1.15 - 0.1, 0, 1) ** 1.5) * 0.9
    # keep only the poured plate: outside a slightly enlarged fitted ellipse goes to black
    vign = np.zeros_like(neg, np.float32)
    cv2.ellipse(vign, ((ex, ey), (ea * 1.04, eb * 1.04), eang), 1.0, -1)
    vign = cv2.GaussianBlur(vign, (0, 0), 6)
    neg = neg * vign
    edge = np.clip(np.arange(sw * S, dtype=np.float32)[None, :] / 40 - 0.4, 0, 1)   # source frame's
    neg = neg * edge * edge[:, ::-1]                                                  # gate edge
    # spiral sentence on a flat disc, then mapped onto the pool's plane
    n = 1000
    gl, path = glyph_spiral(n, PUN1, r_out=440, pitch=74, px=46, a0=math.radians(150), r_min=150)
    gl = np.asarray(gl, np.float32) / 255
    # affine: unit disc -> fitted ellipse (cv2 gives full axes and rotation in degrees)
    th = math.radians(eang)
    ax, by = ea / 2 * 0.74, eb / 2 * 0.74
    A = np.array([[ax * math.cos(th), -by * math.sin(th)], [ax * math.sin(th), by * math.cos(th)]]) / (n / 2)
    spin = math.radians(-24)                            # this frame's turn of the text plate
    Rm = np.array([[math.cos(spin), -math.sin(spin)], [math.sin(spin), math.cos(spin)]])
    A = A @ Rm
    off = np.array([ex, ey]) - A @ np.array([n / 2, n / 2])
    M = np.hstack([A, off[:, None]]).astype(np.float32)
    warp = cv2.warpAffine(gl, M, (sw * S, sh * S), flags=cv2.INTER_LINEAR)
    warp = warp * np.clip(pool_big * 1.2 - 0.1, 0, 1)
    shadow = cv2.GaussianBlur(warp, (0, 0), 2.2)
    bloom = cv2.GaussianBlur(warp, (0, 0), 4.0)
    plate = neg * (1 - 0.45 * np.roll(shadow, (3, 3), (0, 1)))
    plate = plate * (1 - warp) + 236 * warp + 30 * bloom
    canvas = np.zeros((H, W), np.float32)
    canvas[:, 160:160 + sw * S] = plate
    img = to_rgb(canvas, (1.0, 0.985, 0.95))
    img.save(OUT + "/kf-1.png")
    return path


# ---------------------------------------------------------------- kf-2
PUN2 = ("LA PORTE DE SERVICE NE REND PAS SERVICE · LE SERVICE DE LA PORTE "
        "NE REND PAS LA PORTE · ")


def kf2():
    n = 640
    R = n / 2
    base, alpha, r = sphere(n, lo=40, hi=128, gamma=1.0)
    y, x = (np.mgrid[0:n, 0:n].astype(np.float32) - R)
    # nested eccentric rings: centres walk along a diagonal; widths alternate
    rings = []
    for k in range(7):
        rk = 300 - k * 40
        off = 0.32 * (300 - rk)
        cx, cy = off * 0.55, -off * 0.42
        rings.append((rk, cx, cy, 15 + 5 * (k % 2)))
    band = np.zeros((n, n), np.float32)
    groove = np.zeros((n, n), np.float32)
    owner = -np.ones((n, n), np.int32)
    for k, (rk, cx, cy, wd) in enumerate(rings):
        d = np.hypot(x - cx, y - cy)
        inb = np.clip(1 - np.abs(d - rk) / wd, 0, 1)
        inb = np.clip(inb * 3, 0, 1)
        band = np.maximum(band, inb)
        groove += inb * (0.5 + 0.5 * np.cos(d * 2 * math.pi / 3.1)) * 0.22
        owner[inb > 0.0] = k
    # the substitution: rings 0..2 are now letters, ring 3 is breaking, 4..6 intact
    gl, path = glyph_spiral(n, PUN2, r_out=292, pitch=44, px=30, a0=math.radians(200), r_min=150)
    gl = np.asarray(gl, np.float32) / 255
    rad = np.hypot(x, y)
    keep = np.ones((n, n), np.float32)
    for k in range(3):
        keep[owner == k] = 0
    # ring 3 is cut into letter-length dashes where the glyph line passes
    d3 = np.hypot(x - rings[3][1], y - rings[3][2])
    ang = np.arctan2(y, x)
    dash = (np.sin(ang * 23 + 1.1) > -0.1).astype(np.float32)
    keep = np.where(owner == 3, dash, keep)
    band_k = band * keep
    letters = gl * (rad > 150)
    stock = (0.86 + groove) * 255                     # warm cream paper of the rings
    disc = base * (1 - band_k) + stock * band_k
    sh = cv2.GaussianBlur(letters, (0, 0), 1.6)
    disc = disc * (1 - 0.55 * np.roll(sh, (2, 2), (0, 1)))
    disc = disc * (1 - letters) + stock * letters + 18 * cv2.GaussianBlur(letters, (0, 0), 3)
    # motion blur of the turn on intact rings would hide the grooves; keep the still
    canvas = np.zeros((H, W), np.float32)
    put_center(canvas, disc, alpha, W / 2, H / 2)
    to_rgb(canvas, (1.0, 0.955, 0.87)).save(OUT + "/kf-2.png")
    return path


# ---------------------------------------------------------------- kf-3
def key_cutout():
    im = cv2.imread(SRC + "/key_yale_towne_1280.png", cv2.IMREAD_UNCHANGED)
    if im.shape[2] == 4:
        im = im[:, :, :3]
    h, w = im.shape[:2]
    mask = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    mask[g < 90] = cv2.GC_PR_FGD
    mask[g < 60] = cv2.GC_FGD
    mask[:12, :] = mask[-12:, :] = cv2.GC_BGD
    mask[:, :12] = mask[:, -12:] = cv2.GC_BGD
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(im, mask, None, bgd, fgd, 5, cv2.GC_INIT_WITH_MASK)
    a = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1.0, 0.0).astype(np.float32)
    a = cv2.morphologyEx(a, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    # keep the largest component (the key)
    nl, lab, st, _ = cv2.connectedComponentsWithStats((a > 0.5).astype(np.uint8))
    kk = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    a = (lab == kk).astype(np.float32)
    a = cv2.GaussianBlur(a, (0, 0), 1.0)
    grey = g.astype(np.float32)
    ys, xs = np.nonzero(a > 0.5)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    return grey[y0:y1, x0:x1], a[y0:y1, x0:x1]


def kf3():
    kg, ka = key_cutout()
    # iron key -> pale print: stretch so the rust reads as engraved silver on black
    lo, hi = np.percentile(kg[ka > 0.5], [3, 97])
    kg = np.clip((kg - lo) / (hi - lo), 0, 1)
    kg = 70 + 175 * kg ** 0.8
    n = 660
    R = n / 2
    plate = np.full((n, n), 6.0, np.float32)            # black card disc
    pa = np.zeros((n, n), np.float32)
    acc = np.zeros((n, n), np.float32)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    rr = np.hypot(xx - R, yy - R)
    disc_alpha = np.clip((R - 2 - rr), 0, 1)
    # thin grey rim like an engraved plate edge
    plate += 40 * np.clip(1 - np.abs(rr - (R - 6)) / 2.0, 0, 1)
    spin = math.radians(17)                             # plate angle of this frame
    rings = []
    kw0 = kg.shape[1]
    for k in range(5):
        ring_r = 282 - k * 52
        off = 0.40 * (282 - ring_r)
        scale = 0.15 * (ring_r / 282) ** 0.7
        count = int(2 * math.pi * ring_r * 0.97 / (kw0 * scale))
        rings.append((ring_r, off * 0.6, off * 0.35, count, scale))
    for k, (ring_r, ox, oy, count, scale) in enumerate(rings):
        kh, kw = kg.shape
        tw, tht = int(kw * scale), int(kh * scale)
        kgs = cv2.resize(kg, (tw, tht), interpolation=cv2.INTER_AREA)
        kas = cv2.resize(ka, (tw, tht), interpolation=cv2.INTER_AREA)
        # rotate ring centre with the plate
        cx = R + ox * math.cos(spin) - oy * math.sin(spin)
        cy = R + ox * math.sin(spin) + oy * math.cos(spin)
        for i in range(count):
            a = spin + 2 * math.pi * i / count + (k % 2) * math.pi / count
            # key lies along the tangent so a ring of keys reads as a ring, bow leading
            px, py = cx + ring_r * math.cos(a), cy + ring_r * math.sin(a)
            deg = -math.degrees(a) - 90 + 180
            M = cv2.getRotationMatrix2D((tw / 2, tht / 2), deg, 1.0)
            big = int(math.hypot(tw, tht)) + 4
            M[0, 2] += big / 2 - tw / 2
            M[1, 2] += big / 2 - tht / 2
            g2 = cv2.warpAffine(kgs, M, (big, big), flags=cv2.INTER_LINEAR)
            a2 = cv2.warpAffine(kas, M, (big, big), flags=cv2.INTER_LINEAR)
            x0, y0 = int(px - big / 2), int(py - big / 2)
            xa, ya = max(0, x0), max(0, y0)
            xb, yb = min(n, x0 + big), min(n, y0 + big)
            if xb <= xa or yb <= ya:
                continue
            gs = g2[ya - y0:yb - y0, xa - x0:xb - x0]
            asub = a2[ya - y0:yb - y0, xa - x0:xb - x0]
            # cast shadow of the paper cutout on the card
            sub = plate[ya:yb, xa:xb]
            sub[:] = sub * (1 - asub) + gs * asub
            pa[ya:yb, xa:xb] = np.maximum(pa[ya:yb, xa:xb], asub)
    # soft light from the upper right, as on the lit plates of the reference
    lum = 0.78 + 0.32 * np.clip(((xx - R) * 0.5 - (yy - R) * 0.6) / R, -1, 1)
    plate = plate * lum
    canvas = np.zeros((H, W), np.float32)
    put_center(canvas, plate, disc_alpha, W / 2, H / 2)
    to_rgb(canvas, (1.0, 0.965, 0.9)).save(OUT + "/kf-3.png")


# ---------------------------------------------------------------- board
def board():
    names = ["Reference (Pompidou strip; MoMA disc)", "1 · Cire chaude", "2 · Le cerne se délie",
             "3 · Anneaux de clefs"]
    cw, chh = 960, 540
    ref = Image.new("RGB", (cw, chh), (0, 0, 0))
    a = Image.open(REF + "/spiralTextPom.webp").convert("RGB")
    b = Image.open(REF + "/duchamp2.webp").convert("RGB")
    a.thumbnail((cw // 2 - 10, chh)); b.thumbnail((cw // 2 - 10, chh))
    ref.paste(a, ((cw // 2 - a.width) // 2, (chh - a.height) // 2))
    ref.paste(b, (cw // 2 + (cw // 2 - b.width) // 2, (chh - b.height) // 2))
    tiles = [ref] + [Image.open(OUT + f"/kf-{i}.png").convert("RGB").resize((cw, chh), Image.LANCZOS) for i in (1, 2, 3)]
    lab = 44
    bd = Image.new("RGB", (cw * 2 + 30, (chh + lab) * 2 + 30), (24, 24, 24))
    f = font(26)
    for i, t in enumerate(tiles):
        x = 10 + (i % 2) * (cw + 10)
        y = 10 + (i // 2) * (chh + lab + 10)
        bd.paste(t, (x, y + lab))
        ImageDraw.Draw(bd).text((x + 4, y + 8), names[i], font=f, fill=(235, 230, 215))
    bd.save(OUT + "/board.jpg", quality=90)


if __name__ == "__main__":
    p1 = kf1()
    p2 = kf2()
    kf3()
    board()
    print("kf-1 glyphs", len(p1), "kf-2 glyphs", len(p2))
    print("kf-1 reads:", "".join(c for c, _, _ in p1))
    print("kf-2 reads:", "".join(c for c, _, _ in p2))
