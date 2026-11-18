"""KF2 · LIGHTBOX PUPPET, HINGED BALLOONS (silhouette theatre).
One scissor-cut black-card puppet pinned identically in four lit windows. The
foraged 1865 prisoner's-letter envelope (LoC, PD) is cut out and laid in its
hands, so the backlight shows its handwriting and the examiner's stamp.
Balloons are black cards with the letters knife-cut out, carried in on rods and
unfolded on a hinge. Frame shown: 0:41, strip B panel 3, balloon half-open."""
import os, sys, math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from hand import catmull, arc, resample, layout, letter, brush, balloon_shape

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, '..')
SRC = os.path.normpath(os.path.join(HERE, '../../../../sources/moins-dun-quart-de-seconde-pour-vivre'))
K = 2
PW, PH = 296, 490
G = 18
X0 = (1280 - (4 * PW + 3 * G)) // 2
Y0 = 140
SC = 350        # puppet scene square (px), cropped by the window
SKY = PH - SC   # lit space above the puppet scene
SHIFT = 6       # scene x offset inside the window
CARD = (22, 19, 17)

B = [["ME? I'VE BEEN", "ON THIS BENCH", "SINCE NINE."], ["ASK THE LAMP."], ["AND LOOK -", "STILL SEALED."], None]


def facet(ctrl, rng, step=13, jit=1.6, closed=True):
    """Scissor cut: smooth curve -> straight snips with slight wander."""
    pts = catmull(ctrl, 16, closed=closed)
    pts = resample(pts + ([pts[0]] if closed else []), step)
    return [(x + rng.normal(0, jit), y + rng.normal(0, jit)) for x, y in pts]


def puppet_mask(size, seed=3):
    """Silhouette alpha (255 = card) for the scene in 1000 units, rendered at size px."""
    s = size / 1000.0
    m = Image.new('L', (size, size), 0)
    d = ImageDraw.Draw(m)
    rng = np.random.default_rng(seed)
    P = lambda pts: [(x * s, y * s) for x, y in pts]
    def cut(ctrl, fill=255):
        d.polygon(P(facet(ctrl, rng)), fill=fill)
    def bar(x0, y0, x1, y1):
        cut([(x0, y0), ((x0 + x1) / 2, y0), (x1, y0), (x1, y1), ((x0 + x1) / 2, y1), (x0, y1)])
    # lamp
    bar(140, 205, 162, 470)
    cut([(110, 205), (190, 205), (170, 232), (130, 232)])
    cut([(150, 50), (215, 75), (235, 140), (200, 200), (150, 210), (98, 200), (66, 140), (88, 75)])
    # bench
    for x in (150, 830):
        bar(x - 16, 650, x + 16, 865)
    for x in (200, 870):
        bar(x - 13, 420, x + 13, 640)
    bar(105, 430, 905, 478); bar(105, 510, 905, 558); bar(75, 630, 935, 690)
    # creature
    cut([(520, 220), (470, 260), (440, 360), (450, 450), (480, 470), (505, 400), (530, 300)])
    cut([(330, 470), (360, 380), (440, 330), (560, 330), (640, 380), (680, 480), (680, 600), (650, 665), (520, 690), (380, 680), (320, 610)])
    for fx in (430, 560):
        cut([(fx - 35, 680), (fx + 30, 680), (fx + 55, 760), (fx + 40, 790), (fx - 20, 792), (fx - 40, 760)])
    cut([(470, 250), (500, 160), (580, 110), (670, 120), (730, 170), (800, 210), (860, 250), (880, 300), (850, 335), (770, 335), (700, 345), (620, 360), (530, 345), (480, 310)])
    cut([(560, 165), (520, 190), (500, 270), (510, 380), (540, 420), (565, 380), (575, 270)])
    cut([(600, 420), (650, 440), (640, 560), (600, 600), (565, 580), (590, 520)])
    cut([(360, 560), (410, 540), (440, 560), (430, 600), (390, 615), (355, 600)])
    cut([(600, 560), (645, 545), (670, 575), (655, 615), (610, 620)])
    cut([(400, 400), (440, 410), (430, 500), (420, 560), (380, 580), (360, 540), (370, 460)])
    # ground strip
    cut([(-30, 862), (300, 848), (600, 856), (1030, 842), (1030, 1030), (-30, 1030)])
    # --- knife work (holes that let light through)
    ex, ey, er = 650, 210, 52
    low = arc(ex, ey + 2, er * 0.92, er * 0.95, 180, 360, 24)
    d.polygon(P(low), fill=0)                                   # lower eye open
    d.ellipse(P([(ex - 34, ey + 4), (ex - 6, ey + 34)]), fill=255)  # pupil left as card (bridged)
    d.polygon(P([(ex - 22, ey + 2), (ex - 18, ey + 2), (ex - 18, ey + 8), (ex - 22, ey + 8)]), fill=255)
    for (x0, y0, x1, y1) in [(640, 322, 800, 316)]:             # mouth slit
        d.line(P([(x0, y0), ((x0 + x1) / 2, y0 + 2), (x1, y1)]), fill=0, width=max(1, int(4 * s)))
    d.ellipse(P([(846, 266), (862, 282)]), fill=0)              # nostril
    for i in range(60):                                          # fur slits
        x = rng.uniform(350, 670); y = rng.uniform(370, 660)
        if ((x - 505) / 175) ** 2 + ((y - 510) / 175) ** 2 > 0.75:
            continue
        if 380 < x < 640 and 505 < y < 665:
            continue
        a = rng.uniform(-0.5, 0.5)
        d.line(P([(x, y), (x + 12 * math.sin(a), y + 18 * math.cos(a))]), fill=0, width=max(1, int(3 * s)))
    for (x, y) in ((600, 160), (690, 150), (640, 290), (560, 300)):
        d.line(P([(x, y), (x + 3, y + 14)]), fill=0, width=max(1, int(3 * s)))
    for k in range(4):                                           # lamp slits
        x0 = 118 + k * 16
        d.line(P([(x0, 95 + k * 4), (x0 + 8, 125 + k * 4)]), fill=0, width=max(1, int(4 * s)))
    return m


def envelope_cut(size_wh):
    """Foraged envelope: trim scan border, return transmissivity map (0..1) at size."""
    im = Image.open(os.path.join(SRC, 'env1865.jpg')).convert('RGB')
    a = np.asarray(im).astype(np.float32) / 255
    L = a.mean(2)
    ys, xs = np.where(L > 0.35)
    x0, x1 = np.percentile(xs, 0.5), np.percentile(xs, 99.5)
    y0, y1 = np.percentile(ys, 0.5), np.percentile(ys, 99.5)
    a = a[int(y0) + 4:int(y1) - 4, int(x0) + 4:int(x1) - 4]
    return a


def warp_into(dst_wh, img, quad):
    h, w = img.shape[:2]
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), np.float32(quad))
    out = cv2.warpPerspective(img, M, dst_wh, flags=cv2.INTER_AREA)
    msk = cv2.warpPerspective(np.ones((h, w), np.float32), M, dst_wh, flags=cv2.INTER_LINEAR)
    return out, msk


def backlight(w, h, seed):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w * 0.42, h * 0.38
    r = np.sqrt(((xx - cx) / w) ** 2 + ((yy - cy) / h) ** 2)
    base = 1.0 - 0.55 * r ** 1.4
    fib = rng.normal(0, 1, (h, w)).astype(np.float32)
    fib = cv2.GaussianBlur(fib, (0, 0), 1.4)
    fib2 = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 14)
    fib3 = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 45)
    # a few long fibres
    fl = np.zeros((h, w), np.float32)
    for i in range(int(w * h / 9000)):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        a = rng.uniform(0, 3.14); L = rng.uniform(15, 70)
        cv2.line(fl, (int(x), int(y)), (int(x + L * np.cos(a)), int(y + L * np.sin(a))), 1.0, 1)
    fl = cv2.GaussianBlur(fl, (0, 0), 0.8)
    T = np.clip(base * (1 + 0.035 * fib / fib.std() + 0.05 * fib2 / fib2.std() + 0.07 * fib3 / fib3.std() - 0.10 * fl), 0.2, 1.1)
    warm = np.array([255, 226, 172], np.float32) / 255
    return T[..., None] * warm[None, None]


def balloon_card(lines, size, seed, tail, hinge=1.0):
    """Black card balloon with letters knife-cut out; returns (alpha_card, alpha_cut) on a canvas.
    hinge: 1 = fully open, <1 = right leaf turned on the vertical hinge (foreshortened)."""
    rng = np.random.default_rng(seed)
    st, (tw, th) = layout(lines, size, rng)
    rw, rh = tw / 2 + size * 1.25, th / 2 + size * 1.15
    W, H = int(rw * 2 + 220), int(rh * 2 + 220)
    cx, cy = W / 2, rh + 40
    card = Image.new('L', (W, H), 0)
    cut = Image.new('L', (W, H), 0)
    pts = balloon_shape(cx, cy, rw, rh, rng, (cx + tail[0], cy + tail[1]))
    ImageDraw.Draw(card).polygon([tuple(p) for p in facet(pts, rng, step=10, jit=1.2)], fill=255)
    cd = ImageDraw.Draw(cut)
    letter(cd, st, cx - tw / 2, cy - th / 2, size * 0.17, seed + 1, col=255)
    if hinge < 1.0:
        hx = int(cx)
        for im in (card, cut):
            right = im.crop((hx, 0, W, H))
            nw = max(1, int((W - hx) * hinge))
            right = right.resize((nw, H), Image.LANCZOS)
            im.paste(0, (hx, 0, W, H))
            im.paste(right, (hx, 0))
    return card, cut, (cx, cy - rh)


def build(out='kf-2.png'):
    Wk, Hk = 1280 * K, 720 * K
    # board (opaque card) with faint grain
    rng = np.random.default_rng(1)
    board = np.ones((Hk, Wk, 3), np.float32) * np.array(CARD, np.float32) / 255
    board *= (1 + 0.08 * cv2.GaussianBlur(rng.normal(0, 1, (Hk, Wk)).astype(np.float32), (0, 0), 2))[..., None]
    page = board.copy()
    pw, ph, sky = PW * K, PH * K, SKY * K
    sc = SC * K
    pm = np.asarray(puppet_mask(sc)).astype(np.float32) / 255
    pm = cv2.GaussianBlur(pm, (0, 0), 0.7)
    env = envelope_cut(None)
    s = sc / 1000.0
    q0 = [(400, 535), (620, 515), (632, 640), (412, 660)]
    qc = np.mean(q0, 0)
    quad = [((qc[0] + (x - qc[0]) * 1.22) * s, (qc[1] + (y - qc[1]) * 1.22 - 8) * s) for x, y in q0]
    ew, emsk = warp_into((sc, sc), env, quad)
    # transmissivity of the old envelope paper: lighter paper passes more; ink and stamp block
    eL = ew.mean(2)
    eT = np.clip((eL - 0.22) / 0.5, 0.04, 1.0) ** 1.25 * 0.95
    tint = np.clip(ew / np.maximum(1e-3, ew.max(2, keepdims=True)), 0, 1)
    plate_hashes = []
    for c in range(4):
        x, y = (X0 + c * (PW + G)) * K, Y0 * K
        light = backlight(pw, ph, 10 + c * 0 + 0)   # same lamp, same paper in every window
        win = light.copy()
        # puppet scene occupies the lower square of the window
        trans = (1 - pm)[..., None]
        # envelope on top of the puppet card (it is laid over the hands)
        env_t = (eT[..., None] * tint * 1.05)
        trans = trans * (1 - emsk[..., None]) + env_t * emsk[..., None] * 1.0
        # the hands overlap the envelope edges (card in front)
        hands = Image.new('L', (sc, sc), 0)
        hd = ImageDraw.Draw(hands)
        r2 = np.random.default_rng(3)
        for ctrl in ([(360, 560), (410, 540), (440, 560), (430, 600), (390, 615), (355, 600)], [(600, 560), (645, 545), (670, 575), (655, 615), (610, 620)]):
            hd.polygon([(px * s, py * s) for px, py in facet(ctrl, r2)], fill=255)
        hm = cv2.GaussianBlur(np.asarray(hands).astype(np.float32) / 255, (0, 0), 0.7)[..., None]
        trans = trans * (1 - hm)
        # brass paper-fastener pins at the joints (the puppet is articulated, pinned for this cut)
        pins = Image.new('L', (sc, sc), 0); pd = ImageDraw.Draw(pins)
        for (px, py) in ((420, 412), (618, 432), (548, 300), (470, 680)):
            pd.ellipse([(px - 9) * s, (py - 9) * s, (px + 9) * s, (py + 9) * s], fill=255)
        pa = cv2.GaussianBlur(np.asarray(pins).astype(np.float32) / 255, (0, 0), 0.8)[..., None]
        ox = (pw - sc) // 2 + SHIFT * K
        tcrop = trans[:, -ox:-ox + pw] if ox < 0 else trans
        pcrop = pa[:, -ox:-ox + pw]
        scene = win[sky:sky + sc] * tcrop
        # pins catch the front light a little: dull brass
        scene = scene * (1 - pcrop) + pcrop * np.array([0.42, 0.33, 0.17], np.float32) * (0.8 + 0.2 * tcrop)
        win[sky:sky + sc] = scene
        plate_hashes.append(hash(scene.tobytes()))
        # balloons: black card with cut letters, carried on a rod
        if B[c]:
            hinge = 0.38 if c == 2 else 1.0
            card, cutl, top = balloon_card(B[c], 30, 300 + c, tail=(70, 190), hinge=hinge)
            if c == 2:  # mid-swing on the rod: rotate the card about its rod pin
                card = card.rotate(11, resample=Image.BICUBIC, center=top)
                cutl = cutl.rotate(11, resample=Image.BICUBIC, center=top)
            ca = np.asarray(card).astype(np.float32) / 255
            cu = np.asarray(cutl).astype(np.float32) / 255
            ca = cv2.GaussianBlur(ca, (0, 0), 0.8); cu = cv2.GaussianBlur(cu, (0, 0), 0.6)
            bx, by = int(pw * 0.5 - card.size[0] / 2 - 40), -10
            if c == 2:
                by -= 26  # still swinging down on its rod
                bx += 26
            hh, ww = ca.shape
            x0, y0 = max(0, bx), max(0, by)
            x1, y1 = min(pw, bx + ww), min(ph, by + hh)
            A_ = ca[y0 - by:y1 - by, x0 - bx:x1 - bx][..., None]
            C_ = cu[y0 - by:y1 - by, x0 - bx:x1 - bx][..., None]
            region = win[y0:y1, x0:x1]
            # card blocks light; letters cut through let it back (slightly brighter: no paper fibre under the cut? same light)
            open_ = (1 - A_) + A_ * C_
            win[y0:y1, x0:x1] = region * open_ + 0.0 * (1 - open_)
            # rod (black wire) from the top edge to the balloon top
            rod = Image.new('L', (pw, ph), 0)
            rd = ImageDraw.Draw(rod)
            tx = bx + top[0]
            tilt = -70 if c == 2 else 0
            rd.line([(tx + tilt, 0), (tx, by + top[1] + 6)], fill=255, width=5)
            rd.ellipse([tx - 8, by + top[1] - 4, tx + 8, by + top[1] + 12], fill=255)
            ra = cv2.GaussianBlur(np.asarray(rod).astype(np.float32) / 255, (0, 0), 1.6 if c == 2 else 0.8)[..., None]
            win = win * (1 - ra)
        page[y:y + ph, x:x + pw] = win
    assert len(set(plate_hashes)) == 1, 'puppet drift'
    img = Image.fromarray((np.clip(page, 0, 1) * 255).astype(np.uint8), 'RGB')
    d = ImageDraw.Draw(img)
    # chalk labels on the board
    rng = np.random.default_rng(5)
    st, _ = layout(["B  -  THE ALIBI"], 30, rng)
    letter(d, st, X0 * K, (Y0 - 46) * K, 4, 5, col=(214, 200, 176))
    rng = np.random.default_rng(6)
    st, (tw, _) = layout(["0:41"], 30, rng)
    letter(d, st, (1280 - X0) * K - tw, (Y0 - 46) * K, 4, 6, col=(214, 200, 176))
    # rod clamps on the top board, above each window that has a rod
    img = img.resize((1280, 720), Image.LANCZOS)
    img.save(os.path.join(OUT, out))
    print('puppet scene identical across 4 windows')


if __name__ == '__main__':
    build()
