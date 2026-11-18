"""U2 STAGE: the linocut carver's handmade world, in both projections, for
"Exercises in Style" (Mauro Martino), SCION controlled variation.

Every public function is a pure, deterministic function of (seed, element_id[, treatment])
and returns PIL RGBA layers at 960x540 (or a small tile plus its rest-centre). The renderer
draws no RNG: every random stream here is keyed by sha1((seed, element_id)).

Treatments: "cut-paper" (baseline: key block + tint block relief print) and
"photographic-plate" (delta: untreated rectified plates, same handmade outlines filled
with photographic texture). Cameras: side elevation (layers below) and overhead plan
(plan_* functions), both projected from ONE world (WORLD, side_xy, plan_xy).

FORAGED  : Agence Rol 1916 "nouvel autobus Madeleine-Bastille" (Gallica/BnF via Commons, PD):
           bus + wheels plate (U1 plates if present, else the test-shot rectification), the
           right-hand facade and the cobbles (rectified here). Peyriras 1933 "Greve des autobus -
           Place de la Bourse" (Gallica/BnF via Commons, PD): waiting crowd, GrabCut mass.
HANDMADE : carved Haussmann facade, gouged roadway/pavement, platform floor/chain/stanchion/
           bell cord, carved-capital destination board, overhead roof/kerb/cornice shadow.

Layer order for the side view (back to front):
    backdrop(seed, tr)  -> crowd(seed, tr)  -> bus_shadow(seed, dx) -> bus_body(seed, tr)
    -> wheel(...) x2 -> [puppets behind the rail] -> bus_front(seed, tr) -> [runners, shadows]
Bus layers are at REST position; translate by dx = bus_x(t) - BUS_REST_X (layer slide).

Run:  python3 -I stage.py            (prepares frozen sources, writes stage-sheet.jpg + evidence)
"""
import json, math, hashlib, functools
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path("/home/user/bolas/paeleo/scion/oulipo")
SLUG = "mauro-martino-exercises-in-style"
WS = ROOT / "films/swarm" / SLUG
SRC = ROOT / "films/sources" / SLUG
MEDIA = SRC / "stage"
U1 = SRC / "plates"                      # U1's plates, preferred when present
TS = SRC / "test-shot/plates"            # test-shot plates (fallback)
ROL = SRC / "commons/rol1916.jpg"
BOURSE = SRC / "commons/bourse1933.jpg"
REF = ROOT / "assets/references/martinoCharcoal.webp"

W, H, SS = 960, 540, 2
GENERATOR_REV = "stage-2"

# ------------------------------------------------------------------ palette tokens
INK = np.array((34, 33, 31), np.float32)
INK2 = np.array((45, 44, 42), np.float32)     # worn ink
DTINT = np.array((71, 68, 63), np.float32)    # dark tint (overprint)
TINT = np.array((149, 142, 133), np.float32)  # grey tint block
SHADE = np.array((211, 203, 188), np.float32)  # shaded paper
PAPER = np.array((238, 230, 214), np.float32)
PALETTE = dict(ink=(34, 33, 31), ink2=(45, 44, 42), dtint=(71, 68, 63), tint=(149, 142, 133),
               shade=(211, 203, 188), paper=(238, 230, 214))
TREATMENTS = ("cut-paper", "photographic-plate")

# ------------------------------------------------------------------ one world, two projections
# World: x = film px along the street (side-view x at rest), z = depth from the facade line (px,
# same scale as x; ~72.5 px per metre), h = height above the ground (px).
WORLD = dict(
    facade_z=0.0, far_kerb_z=40.0, crowd_z=20.0,
    bus_z0=70.0, bus_z1=237.0, bus_zc=153.5,
    near_kerb_z=270.0, runner_z=(282.0, 322.0),   # runners' feet y ~424-462: heads reach the window band
    facade_band=(0, 189), shop_band=(189, 356), pavement_band=(405, 540),
)
_ZK = [0.0, 40.0, 153.5, 270.0, 330.0, 480.0]      # stage depth -> ground line in the elevation
_YK = [356.0, 362.0, 402.0, 412.0, 470.0, 530.0]   # (theatre-flat layering, not linear perspective)


def side_ground_y(z):
    return float(np.interp(z, _ZK, _YK))


def side_xy(x, z, h=0.0):
    """World (x, z, h) -> side elevation screen px."""
    return float(x), side_ground_y(z) - float(h)


PLAN_Y0 = 50.0


def plan_xy(x, z):
    """World (x, z) -> overhead plan screen px (1:1, facade line at the top)."""
    return float(x), PLAN_Y0 + float(z)


# ------------------------------------------------------------------ bus placement (plate px -> screen)
K_BUS = 0.80                 # plate film px -> screen px
CAB_X, CAB_K = 270.0, 0.75   # cab/bonnet foreshortening fix: plate x < 270 compressed toward 270
PLATE_CUT = 688.0            # real body ends; handmade platform begins
PLAT_END = 820.0
WHEEL_CONTACT_PLATE = 281.0
BUS_REST_X = 720.0 - PLAT_END * K_BUS          # screen x of plate x=0 at rest (platform rear at 720)
BUS_Y0 = side_ground_y(WORLD["bus_zc"]) - WHEEL_CONTACT_PLATE * K_BUS


def cab_x(px):
    """Plate x -> corrected plate x (compress the stretched cab front)."""
    px = np.asarray(px, np.float64)
    return np.where(px < CAB_X, CAB_X - (CAB_X - px) * CAB_K, px)


def bus_pt(px, py):
    """Bus plate (film px, uncorrected) -> screen px at rest."""
    return float(BUS_REST_X + cab_x(px) * K_BUS), float(BUS_Y0 + py * K_BUS)


def bus_x(t):
    """Default layer slide (matches anchors A1=0.90 stop, pull-away 6.20): returns screen x of
    plate origin. Enters from the right moving left (cab leads). Smooth: not drawn on twos."""
    d_in = 80.0
    if t < 0.90:
        u = 1 - t / 0.90
        return BUS_REST_X + d_in * u * u
    if t < 6.20:
        return BUS_REST_X
    return BUS_REST_X - 0.5 * 160 * (t - 6.20) ** 2


# key world points (screen px at rest, and world coords) for the rig / verifier
def anchors_world():
    sx0, _ = bus_pt(PLATE_CUT, 0)
    sx1, _ = bus_pt(PLAT_END, 0)
    st_x = bus_pt(PLAT_END - 12, 0)[0]
    return dict(
        bus_rest_x=BUS_REST_X, bus_y0=BUS_Y0, k_bus=K_BUS,
        platform_x=(sx0, sx1), platform_floor_y=bus_pt(0, 222)[1], step_y=bus_pt(0, 248)[1],
        stanchion=dict(x=st_x, y_top=bus_pt(0, 30)[1], y_bot=bus_pt(0, 226)[1],
                       world=dict(x=st_x, z=WORLD["bus_z1"] - 6)),
        bell_cord=dict(x=bus_pt(PLAT_END - 30, 0)[0], y=bus_pt(0, 37)[1]),
        rear_window=dict(x0=bus_pt(580, 0)[0], x1=bus_pt(681, 0)[0], y0=bus_pt(0, 48)[1], y1=bus_pt(0, 118)[1]),
        board=board_rect(), wheel_contact_y=side_ground_y(WORLD["bus_zc"]),
        bus_extent_x=(bus_pt(36.5, 0)[0], sx1),
        ground_y=dict(zip(map(str, _ZK), _YK)),
    )


def board_rect():
    x0, y0 = bus_pt(290, -24); x1, y1 = bus_pt(600, 6)
    return (x0, y0, x1, y1)


# ------------------------------------------------------------------ deterministic RNG
def rng(seed, *key):
    h = hashlib.sha1(repr((int(seed),) + key).encode()).digest()
    return np.random.RandomState(int.from_bytes(h[:4], "little"))


def smooth_noise(r, h, w, sy, sx):
    n = r.rand(h // sy + 3, w // sx + 3).astype(np.float32)
    n = cv2.resize(n, ((w // sx + 3) * sx, (h // sy + 3) * sy), interpolation=cv2.INTER_CUBIC)
    return n[sy:sy + h, sx:sx + w]


# ------------------------------------------------------------------ carving primitives (SS px)
def canvas():
    im = Image.new("L", (W * SS, H * SS), 0)
    return im, ImageDraw.Draw(im)


def gouge(d, x, y, length, width, slope=0.0, fill=255, r=None, bow=0.0):
    """Tapered V-gouge stroke (lens), with an optional hand bow and wobble. Args in film px."""
    n = 16
    top, bot = [], []
    wob = r.uniform(-0.25, 0.25, n + 1) if r is not None else np.zeros(n + 1)
    a0 = r.uniform(0.45, 0.9) if r is not None else 0.7
    for i in range(n + 1):
        u = i / n
        w = width * (math.sin(math.pi * u) ** a0) * (1 + wob[i] * 0.6)
        px = x + u * length
        py = y + u * length * slope + bow * math.sin(math.pi * u)
        top.append((px * SS, (py - w / 2) * SS)); bot.append((px * SS, (py + w / 2) * SS))
    d.polygon(top + bot[::-1], fill=fill)


def wobbly_quad(d, r, x0, y0, x1, y1, amp=0.7, fill=255, n=3):
    """A hand-cut rectangle: each side is a slightly irregular knife line."""
    pts = []
    for (ax, ay, bx, by) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        for k in range(n):
            u = k / n
            pts.append(((ax + (bx - ax) * u + r.uniform(-amp, amp)) * SS,
                        (ay + (by - ay) * u + r.uniform(-amp, amp)) * SS))
    d.polygon(pts, fill=fill)


def wobbly_poly(d, r, pts, amp=0.6, fill=255):
    d.polygon([((x + r.uniform(-amp, amp)) * SS, (y + r.uniform(-amp, amp)) * SS) for x, y in pts], fill=fill)


def arr(im):
    return np.asarray(im, np.float32) / 255.0


def print_block(m, seed, eid, starve=0.10, edge=0.35, feather=0.75):
    """Relief-print a block mask (SS px float): ink-starved broken edges + sparse interior starving,
    seeded per (seed, element) - static, never per frame - then a 0.6-1 px feather."""
    r = rng(seed, "print", eid)
    h, w = m.shape
    soft = cv2.GaussianBlur(m, (0, 0), 1.3)
    n1 = smooth_noise(r, h, w, 3, 9)           # edge bite, horizontally streaked (paper fibre direction)
    n2 = r.rand(h, w).astype(np.float32)
    v = soft + (n1 - 0.5) * edge + (n2 - 0.5) * 0.12
    out = np.clip((v - 0.5) * 6 + 0.5, 0, 1) * (soft > 0.02)
    if starve > 0:
        inner = cv2.erode((m > 0.5).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(np.float32)
        n3 = smooth_noise(r, h, w, 2, 34)
        hole = ((n3 > 1 - starve) & (n2 > 0.4)).astype(np.float32) * inner
        out = out * (1 - 0.8 * hole)
    return cv2.GaussianBlur(out, (0, 0), feather * SS / 2)


def paper_ground(seed, eid="paper"):
    """Cream paper with fibre grain and faint press mottle (static per seed)."""
    r = rng(seed, eid)
    img = np.empty((H * SS, W * SS, 3), np.float32); img[:] = PAPER
    fib = smooth_noise(r, H * SS, W * SS, 1, 7) - 0.5
    mot = smooth_noise(r, H * SS, W * SS, 60, 90) - 0.5
    img += (fib * 7 + mot * 6)[..., None]
    return img


def lay(img, m, col):
    m = m[..., None]
    return img * (1 - m) + col * m


def to_rgba(img, alpha=None):
    """SS float RGB (+alpha) -> 960x540 RGBA."""
    rgb = np.clip(img, 0, 255).astype(np.uint8)
    if alpha is None:
        a = np.full(rgb.shape[:2], 255, np.uint8)
    else:
        a = np.clip(alpha * 255, 0, 255).astype(np.uint8)
    im = Image.fromarray(np.dstack([rgb, a]), "RGBA")
    # premultiplied downsample to avoid dark fringes
    pm = np.asarray(im, np.float32); pm[..., :3] *= pm[..., 3:4] / 255
    pmi = Image.fromarray(pm.astype(np.uint8), "RGBA").resize((W, H), Image.LANCZOS) if False else None
    small = Image.fromarray(np.clip(pm, 0, 255).astype(np.uint8), "RGBA").resize((W, H), Image.BOX)
    s = np.asarray(small, np.float32)
    a2 = s[..., 3:4]
    s[..., :3] = np.where(a2 > 0, s[..., :3] * 255 / np.maximum(a2, 1), 0)
    return Image.fromarray(np.clip(s, 0, 255).astype(np.uint8), "RGBA")


# ------------------------------------------------------------------ frozen sources
def _gray(path):
    return np.asarray(Image.open(path).convert("L"))


@functools.lru_cache(None)
def bus_plate():
    """(gray 2x plate, alpha 2x, meta) - U1's plate when present, else the test-shot rectification."""
    d = U1 if (U1 / "bus_rect_rgba.png").exists() and (U1 / "plates.json").exists() else TS
    meta = json.loads((d / "plates.json").read_text())
    rgba = np.asarray(Image.open(d / "bus_rect_rgba.png"))
    meta["_dir"] = str(d)
    return rgba[..., 0].copy(), rgba[..., 3].astype(np.float32) / 255, meta


def _plate_to_screen(g, S, interp=cv2.INTER_AREA):
    """Warp a 2x bus plate image to screen SS px at rest (cab compression + K_BUS + placement)."""
    Hd, Wd = H * SS, W * SS
    yy, xx = np.mgrid[0:Hd, 0:Wd].astype(np.float32)
    pxc = (xx / SS - BUS_REST_X) / K_BUS                 # corrected plate x
    px = np.where(pxc < CAB_X, CAB_X - (CAB_X - pxc) / CAB_K, pxc)
    py = (yy / SS - BUS_Y0) / K_BUS
    return cv2.remap(g.astype(np.float32), (px * S).astype(np.float32), (py * S).astype(np.float32),
                     cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)


@functools.lru_cache(None)
def _rol_facade_plate():
    """Right-hand Haussmann building of the Rol plate (Grand Hotel side), rectified to an elevation.
    Upper storeys (above the bus roof) and the shopfront storey are rectified separately, since the
    bus hides the ground floor in the middle of the plate. Quads hand-picked on the source."""
    g = _gray(ROL)
    up = np.float32([[930, 98], [1212, 40], [1212, 421], [930, 402]])   # stops short of the '47052' negative number
    Hu = cv2.getPerspectiveTransform(up, np.float32([[0, 0], [540, 0], [540, 400], [0, 400]]))
    shop = np.float32([[1080, 425], [1215, 420], [1215, 570], [1080, 566]])
    Hs = cv2.getPerspectiveTransform(shop, np.float32([[0, 0], [230, 0], [230, 200], [0, 200]]))
    return (cv2.warpPerspective(g, Hu, (540, 400), flags=cv2.INTER_CUBIC),
            cv2.warpPerspective(g, Hs, (230, 200), flags=cv2.INTER_CUBIC)), (Hu, Hs)


@functools.lru_cache(None)
def _rol_cobble_plate():
    g = _gray(ROL)
    quad = np.float32([[40, 690], [1240, 690], [1240, 860], [40, 860]])
    Hm = cv2.getPerspectiveTransform(quad, np.float32([[0, 0], [1200, 0], [1200, 200], [0, 200]]))
    return cv2.warpPerspective(g, Hm, (1200, 200), flags=cv2.INTER_CUBIC), Hm


@functools.lru_cache(None)
def crowd_mask_src():
    """GrabCut of the Bourse 1933 waiting crowd: rect + scribble seeds, alpha cleanup.
    Computed once and frozen to MEDIA (GrabCut's GMM init is not guaranteed bit-stable)."""
    MEDIA.mkdir(parents=True, exist_ok=True)
    fz = MEDIA / "crowd_mask.png"
    if (U1 / "crowd_mask.png").exists():
        return np.asarray(Image.open(U1 / "crowd_mask.png").convert("L"))
    if fz.exists():
        return np.asarray(Image.open(fz).convert("L"))
    g = _gray(BOURSE)
    b = cv2.GaussianBlur(g, (0, 0), 1.5)
    img3 = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
    mask = np.full(g.shape, cv2.GC_BGD, np.uint8)
    band = np.zeros(g.shape, bool); band[395:848, 150:862] = True    # box seed: the left/middle crowd
    dark = b < 95
    mask[band] = cv2.GC_PR_BGD
    mask[band & dark] = cv2.GC_PR_FGD
    core = cv2.erode(((b < 60) & band).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    mask[core] = cv2.GC_FGD                                          # scribble: dark coat cores
    bright = cv2.dilate(((b > 150) & band).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    mask[bright] = cv2.GC_BGD                                        # scribble: lit bus bodies, ground
    mask[835:, :] = np.where(mask[835:, :] == cv2.GC_FGD, cv2.GC_PR_FGD, cv2.GC_BGD)
    bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
    cv2.setRNGSeed(417)
    cv2.grabCut(img3, mask, None, bgd, fgd, 4, cv2.GC_INIT_WITH_MASK)
    fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
    keep = np.zeros_like(fg)
    for i in range(1, n):                               # alpha cleanup: no background islands
        if st[i, cv2.CC_STAT_AREA] > 1500:
            keep[lab == i] = 255
    fail = cv2.bitwise_and(((mask == cv2.GC_PR_BGD) & dark & band).astype(np.uint8) * 255, cv2.bitwise_not(keep))
    Image.fromarray(keep).save(fz)
    Image.fromarray(fail).save(MEDIA / "crowd_failmask.png")
    return keep


# ------------------------------------------------------------------ H1 · carved Haussmann facade
def _facade_blocks(seed):
    """Key block, tint block, dark-tint block and shade block for the facade + shop band (SS)."""
    r = rng(seed, "facade")
    ki, dk = canvas(); ti, dt = canvas(); di, dd = canvas(); si, ds = canvas(); ci, dc = canvas()
    top, base = WORLD["facade_band"]
    shop0, shop1 = WORLD["shop_band"]
    # several buildings of unequal width and storey height (a street, not a pattern)
    x = -r.uniform(10, 60)
    bld = []
    while x < W + 20:
        nb = int(r.choice([3, 4, 5, 6]))
        bw = r.uniform(36, 48)
        bld.append((x, nb, bw))
        x += nb * bw + r.uniform(4, 14)
    for bi, (bx, nb, bw) in enumerate(bld):
        rb = rng(seed, "facade-bld", bi)
        x0, x1 = bx, bx + nb * bw
        roof = rb.uniform(4, 22)                        # mansard height varies per building
        cor = roof + rb.uniform(26, 36)
        st_h = rb.uniform(42, 52)                       # storey height
        # sky gaps between buildings stay paper; mansard: dark tint with slate gouges
        wobbly_poly(dd, rb, [(x0 + 6, roof), (x1 - 6, roof), (x1, cor), (x0, cor)], amp=0.8)
        for y in np.arange(roof + 3, cor, rb.uniform(3.2, 4.4)):
            for _ in range(int((x1 - x0) / 60) + 1):
                gouge(dc, rb.uniform(x0 - 20, x1), y + rb.uniform(-.6, .6), rb.uniform(18, 70), rb.uniform(.7, 1.5), rb.uniform(-.01, .01), r=rb)
        for k in range(nb):                             # dormers (some missing, sizes vary)
            if rb.rand() < 0.18:
                continue
            cx = x0 + (k + 0.5) * bw + rb.uniform(-2, 2)
            dw_ = rb.uniform(11, 16); dh_ = (cor - roof) * rb.uniform(.55, .8)
            y1 = cor - 2; y0 = y1 - dh_
            wobbly_poly(dk, rb, [(cx - dw_ / 2 - 2, y0 + 3), (cx, y0 - rb.uniform(4, 7)), (cx + dw_ / 2 + 2, y0 + 3),
                                 (cx + dw_ / 2, y1), (cx - dw_ / 2, y1)], amp=0.6)
            if rb.rand() < 0.7:                         # some lit dormers: cream panes cut in
                wobbly_quad(dk, rb, cx - dw_ / 2 + 2.5, y0 + 4.5, cx + dw_ / 2 - 2.5, y1 - 2, amp=0.5, fill=0)
                dk.line([(cx * SS, (y0 + 4) * SS), (cx * SS, (y1 - 2) * SS)], fill=255, width=SS)
        for k in range(rb.randint(1, 3)):               # chimney stacks
            cx = rb.uniform(x0 + 10, x1 - 20)
            wobbly_quad(dk, rb, cx, roof - rb.uniform(6, 14), cx + rb.uniform(7, 14), roof + 2, amp=0.6)
        # cornice: ink band with irregular dentil cuts
        wobbly_quad(dk, rb, x0 - 2, cor, x1 + 2, cor + rb.uniform(5, 8), amp=0.6)
        xx = x0
        while xx < x1:
            ww = rb.uniform(1.6, 2.8)
            dk.rectangle([xx * SS, (cor + 3.3) * SS, (xx + ww) * SS, (cor + 4.8 + rb.uniform(0, .8)) * SS], fill=0)
            xx += ww + rb.uniform(2.2, 3.6)
        wall0 = cor + 7
        # wall: shade paper (stone) + tint ashlar gouges whose direction changes per building
        wobbly_quad(ds, rb, x0, wall0, x1, shop0, amp=0.5)
        horiz = rb.rand() < 0.65
        for _ in range(int((x1 - x0) * (shop0 - wall0) / 150)):
            if horiz:
                gouge(dt if rb.rand() < 0.75 else dd, rb.uniform(x0 - 30, x1), rb.uniform(wall0, shop0), rb.uniform(20, 90), rb.uniform(.8, 2.2), rb.uniform(-.01, .01), r=rb)
            else:
                gx = rb.uniform(x0, x1); gy = rb.uniform(wall0, shop0)
                gouge(dt, gx, gy, rb.uniform(6, 16), rb.uniform(.6, 1.4), rb.uniform(-.3, .3), r=rb)
        y = wall0 + 4
        fl = 0
        while y + st_h * 0.6 < shop0:
            wh = st_h * rb.uniform(.62, .72)
            for k in range(nb):
                cx = x0 + (k + 0.5) * bw + rb.uniform(-1.5, 1.5)
                ww = bw * rb.uniform(.5, .6)
                wx0, wx1, wy0, wy1 = cx - ww / 2, cx + ww / 2, y + rb.uniform(-1, 1), y + wh + rb.uniform(-1, 1)
                # dark window in ink; cream cross-mullion cut; sometimes a half-open lit casement
                wobbly_quad(dk, rb, wx0, wy0, wx1, wy1, amp=0.55)
                lit = rb.rand()
                if lit < 0.22:
                    wobbly_quad(dk, rb, cx + 0.8, wy0 + 1.6, wx1 - 1.6, wy1 - 1.6, amp=0.4, fill=0)
                elif lit < 0.5:
                    wobbly_quad(dt, rb, wx0 + 1.4, wy0 + 1.6, cx - 0.8, wy1 - 1.6, amp=0.4)
                mx = cx + rb.uniform(-.4, .4)
                dk.line([(mx * SS, (wy0 + 2) * SS), (mx * SS, (wy1 - 1.5) * SS)], fill=0, width=int(SS * rb.uniform(1.1, 1.6)))
                ty = wy0 + wh * rb.uniform(.28, .36)
                dk.line([((wx0 + 1.5) * SS, ty * SS), ((wx1 - 1.5) * SS, ty * SS)], fill=0, width=int(SS * 1.1))
                if fl % 2 == 0:                          # pediments on the noble floors
                    wobbly_poly(dk, rb, [(wx0 - 3, wy0 - 2), (cx, wy0 - rb.uniform(5, 8)), (wx1 + 3, wy0 - 2)], amp=0.5)
                else:
                    wobbly_quad(dk, rb, wx0 - 2.5, wy0 - 4, wx1 + 2.5, wy0 - 2, amp=0.4)
                wobbly_quad(dk, rb, wx0 - 2.5, wy1, wx1 + 2.5, wy1 + 2.2, amp=0.4)   # sill
            if fl in (0, 2) or (fl == 1 and rb.rand() < 0.3):
                yb = y + wh + 3                          # continuous balcony: rail + wavy ironwork cuts
                wobbly_quad(dk, rb, x0, yb, x1, yb + rb.uniform(7, 9), amp=0.6)
                xx = x0 + rb.uniform(0, 3)
                while xx < x1:
                    hh = rb.uniform(3.2, 4.6)
                    dk.ellipse([xx * SS, (yb + 2) * SS, (xx + rb.uniform(2.2, 3.4)) * SS, (yb + 2 + hh) * SS], fill=0)
                    xx += rb.uniform(3.6, 5.2)
                dd.rectangle([x0 * SS, (yb + 9) * SS, x1 * SS, (yb + 11.5) * SS], fill=255)  # balcony shadow
            y += st_h
            fl += 1
        # party wall shadow strip between buildings
        dd.rectangle([(x1 - 1.5) * SS, cor * SS, (x1 + 2.5) * SS, shop0 * SS], fill=255)
    # shop band (behind the bus): entresol ink fascia, lit arched shopfronts, dark doorways
    dk.rectangle([0, shop0 * SS, W * SS, (shop0 + 3) * SS], fill=255)
    wobbly_quad(dd, r, -2, shop0 + 3, W + 2, shop1, amp=0.4)
    for _ in range(140):
        gouge(dc, r.uniform(-50, W), r.uniform(shop0 + 4, shop1), r.uniform(20, 120), r.uniform(.6, 1.6), r=r)
    x = -r.uniform(0, 30)
    while x < W:
        aw = r.uniform(34, 54)
        top_ = shop0 + r.uniform(30, 44)
        kind = r.rand()
        if kind < 0.7:                                    # lit arched window: cream with ink glazing bars
            ap, dap = canvas()
            dap.pieslice([(x + 4) * SS, (top_ - aw / 2 + 6) * SS, (x + aw - 4) * SS, (top_ + aw / 2 - 2) * SS], 180, 360, fill=255)
            wobbly_quad(dap, r, x + 4, top_ + 2, x + aw - 4, shop1 - 6, amp=0.6)
            ci.paste(255, mask=ap)
            for k in range(1, 3):
                bxk = x + 4 + k * (aw - 8) / 3
                dk.line([(bxk * SS, (top_ - 6) * SS), (bxk * SS, (shop1 - 6) * SS)], fill=255, width=int(1.3 * SS))
            dk.line([((x + 4) * SS, (top_ + 14) * SS), ((x + aw - 4) * SS, (top_ + 14) * SS)], fill=255, width=int(1.2 * SS))
        else:                                             # dark doorway
            wobbly_quad(dk, r, x + 8, top_ - 4, x + aw - 8, shop1, amp=0.6)
        x += aw + r.uniform(6, 16)
    dk.rectangle([0, (shop1 - 4) * SS, W * SS, shop1 * SS], fill=255)          # pavement edge line
    return arr(ki), arr(ti), arr(di), arr(si), arr(ci)


# ------------------------------------------------------------------ H2 · gouged roadway and pavement
def _street_blocks(seed):
    r = rng(seed, "street")
    ki, dk = canvas(); ti, dt = canvas(); si, ds = canvas(); ci, dc = canvas()
    shop1 = WORLD["shop_band"][1]
    road0 = side_ground_y(WORLD["far_kerb_z"])
    kerb = side_ground_y(WORLD["near_kerb_z"])
    # far pavement strip (crowd stands here) : shade with ink gouges
    ds.rectangle([0, shop1 * SS, W * SS, road0 * SS], fill=255)
    dk.rectangle([0, road0 * SS, W * SS, (road0 + 2.2) * SS], fill=255)          # far kerb
    # roadway behind/below the bus: tint block, long cream gouges
    dt.rectangle([0, (road0 + 2) * SS, W * SS, kerb * SS], fill=255)
    for _ in range(160):
        gouge(dc, r.uniform(-200, W), r.uniform(road0 + 3, kerb - 1), r.uniform(40, 260), r.uniform(.8, 2.6), r.uniform(-.004, .004), r=r)
    # near kerb: ink edge with irregular stone joints cut
    wobbly_quad(dk, r, -2, kerb, W + 2, kerb + 4.5, amp=0.5)
    x = r.uniform(0, 30)
    while x < W:
        dk.rectangle([x * SS, (kerb + 4) * SS, (x + r.uniform(1.2, 2.2)) * SS, (kerb + r.uniform(7, 10)) * SS], fill=255)
        x += r.uniform(36, 64)
    # pavement: paper with long horizontal V-gouges, denser toward the bottom (wet-cut feel)
    for _ in range(150):
        y = r.uniform(kerb + 6, H + 4)
        dens = 0.3 + 0.7 * (y - kerb) / (H - kerb)
        if r.rand() > dens:
            continue
        gouge(dk, r.uniform(-260, W), y, r.uniform(30, 300), r.uniform(.7, 2.4) * (0.5 + dens), r.uniform(-.006, .006), r=r, bow=r.uniform(-1, 1))
    for _ in range(70):
        gouge(dt, r.uniform(-200, W), r.uniform(kerb + 6, H + 4), r.uniform(60, 360), r.uniform(1.5, 5), r.uniform(-.004, .004), r=r)
    for _ in range(60):
        gouge(ds, r.uniform(-200, W), r.uniform(kerb + 6, H + 4), r.uniform(60, 300), r.uniform(4, 10), r=r)
    return arr(ki), arr(ti), arr(si), arr(ci)


@functools.lru_cache(None)
def _backdrop_cut(seed):
    fk, ft, fd, fs, fc = _facade_blocks(seed)
    sk, st, ss_, sc = _street_blocks(seed)
    img = paper_ground(seed)
    img = lay(img, np.clip(fs + ss_, 0, 1), SHADE)
    img = lay(img, print_block(np.clip(ft + st, 0, 1), seed, "tint-bg", starve=0, edge=0.25) * 0.9, TINT)
    img = lay(img, np.clip(fc + sc, 0, 1) * 0.85, SHADE)      # cream cuts through the tint
    img = lay(img, print_block(fd, seed, "dtint-bg", starve=0.05, edge=0.25) * 0.95, DTINT)
    img = lay(img, np.clip(fc, 0, 1) * 0.85, SHADE)
    key = print_block(np.clip(fk + sk, 0, 1), seed, "key-bg", starve=0.08)
    return lay(img, key, INK)


@functools.lru_cache(None)
def _backdrop_photo(seed):
    """Photographic-plate world: the rectified Rol facade, shopfronts and cobbles (straight repeats,
    never mirrored, so the real lettering stays readable), graded only to unify."""
    (fac, shp), _ = _rol_facade_plate()
    cob, _ = _rol_cobble_plate()
    Hd, Wd = H * SS, W * SS
    shop0, shop1 = WORLD["shop_band"]
    out = np.zeros((Hd, Wd), np.float32)
    off = int(rng(seed, "photo-facade").uniform(0, 200))
    def strip(img, h):
        t = cv2.resize(img, (int(img.shape[1] * h / img.shape[0]), h), interpolation=cv2.INTER_AREA).astype(np.float32)
        t = np.concatenate([t] * (Wd // t.shape[1] + 3), 1)
        return t[:, off:off + Wd]
    fh = int(shop0 * SS)
    out[:fh] = strip(fac, fh)
    sh = int(shop1 * SS) - fh
    out[fh:fh + sh] = strip(shp, sh)
    ch = Hd - fh - sh
    out[fh + sh:] = cv2.resize(cob, (Wd, ch), interpolation=cv2.INTER_AREA).astype(np.float32)
    return _grade(out)


def _grade(g):
    """Map a grey plate onto the paper/ink tone range (unifying grade, not a look)."""
    g = np.clip(g, 0, 255) / 255.0
    return INK[None, None] * (1 - g[..., None]) + PAPER[None, None] * g[..., None]


def backdrop(seed, treatment="cut-paper"):
    """Full-frame facade + shop band + roadway + pavement. RGBA 960x540 (opaque)."""
    img = _backdrop_cut(seed) if treatment == "cut-paper" else _backdrop_photo(seed)
    return to_rgba(img)


# ------------------------------------------------------------------ Bourse crowd mid-layer
@functools.lru_cache(None)
def _crowd(seed, treatment):
    m = crowd_mask_src().astype(np.float32) / 255
    g = _gray(BOURSE).astype(np.float32)
    r = rng(seed, "crowd")
    Hd, Wd = H * SS, W * SS
    alpha = np.zeros((Hd, Wd), np.float32); fill = np.zeros((Hd, Wd), np.float32)
    feet_y = side_ground_y(WORLD["crowd_z"])
    sc = 0.31 * r.uniform(0.96, 1.04)                     # ~110 px tall at the far pavement
    pieces = [((400 + r.uniform(-30, 30), 862), 724 + r.uniform(-4, 16)),    # right of the platform
              ((150, 560 + r.uniform(-30, 20)), 8 + r.uniform(-20, 4))]      # left of the cab
    for (sx0, sx1), dx in pieces:
        sx0, sx1 = int(sx0), int(sx1)
        crop_m = m[395:850, sx0:sx1]; crop_g = g[395:850, sx0:sx1]
        ys = np.nonzero(crop_m.sum(1) > 0)[0]
        if len(ys) == 0:
            continue
        foot = ys.max()
        tw, th = int(crop_m.shape[1] * sc * SS), int(crop_m.shape[0] * sc * SS)
        cm = cv2.resize(crop_m, (tw, th), interpolation=cv2.INTER_AREA)
        cg = cv2.resize(crop_g, (tw, th), interpolation=cv2.INTER_AREA)
        X = int(dx * SS); Y = int((feet_y - foot * sc) * SS)
        x0, y0 = max(0, X), max(0, Y); x1, y1 = min(Wd, X + tw), min(Hd, Y + th)
        if x1 <= x0 or y1 <= y0:
            continue
        a = cm[y0 - Y:y1 - Y, x0 - X:x1 - X]
        alpha[y0:y1, x0:x1] = np.maximum(alpha[y0:y1, x0:x1], a)
        fill[y0:y1, x0:x1] = np.where(a > 0, cg[y0 - Y:y1 - Y, x0 - X:x1 - X], fill[y0:y1, x0:x1])
    if treatment == "cut-paper":
        a = print_block(np.clip(alpha * 1.2, 0, 1), seed, "crowd", starve=0.04, edge=0.3)
        img = np.empty((Hd, Wd, 3), np.float32); img[:] = INK2
        return img, a
    return _grade(fill), cv2.GaussianBlur(alpha, (0, 0), 0.6)


def crowd(seed, treatment="cut-paper"):
    """The waiting crowd (Bourse 1933 GrabCut mass): black mid-layer behind the bus."""
    img, a = _crowd(seed, treatment)
    return to_rgba(img, a)


# ------------------------------------------------------------------ H3 · platform hardware + board
_LETTERS = {   # carved capitals as chisel strokes in a 0..1 (w) x 0..1 (h) box; arcs as ('a', cx, cy, rx, ry, a0, a1)
    "M": [((0, 1), (0.05, 0)), ((0.05, 0), (0.5, 0.75)), ((0.5, 0.75), (0.95, 0)), ((0.95, 0), (1, 1))],
    "A": [((0, 1), (0.5, 0)), ((0.5, 0), (1, 1)), ((0.22, 0.62), (0.78, 0.62))],
    "D": [((0.05, 0), (0.05, 1)), ((0.05, 0), (0.45, 0)), ((0.05, 1), (0.45, 1)), ("a", 0.45, 0.5, 0.5, 0.5, -90, 90)],
    "E": [((0.05, 0), (0.05, 1)), ((0.05, 0), (0.92, 0)), ((0.05, 0.5), (0.75, 0.5)), ((0.05, 1), (0.95, 1))],
    "L": [((0.05, 0), (0.05, 1)), ((0.05, 1), (0.95, 1))],
    "I": [((0.5, 0), (0.5, 1))],
    "N": [((0.05, 1), (0.05, 0)), ((0.05, 0), (0.95, 1)), ((0.95, 1), (0.95, 0))],
    "B": [((0.05, 0), (0.05, 1)), ((0.05, 0), (0.5, 0)), ((0.05, 0.48), (0.55, 0.48)), ((0.05, 1), (0.55, 1)),
          ("a", 0.5, 0.24, 0.4, 0.24, -90, 90), ("a", 0.55, 0.74, 0.42, 0.26, -90, 90)],
    "S": [("p", (0.9, 0.16), (0.72, 0.03), (0.45, 0.0), (0.18, 0.07), (0.08, 0.24), (0.2, 0.41), (0.5, 0.5),
          (0.8, 0.59), (0.93, 0.76), (0.84, 0.93), (0.56, 1.0), (0.28, 0.98), (0.08, 0.85))],
    "T": [((0, 0), (1, 0)), ((0.5, 0), (0.5, 1))],
    "–": [((0.1, 0.55), (0.9, 0.55))],
    " ": [],
}
_WIDTH = {"M": 1.0, "A": 0.85, "D": 0.8, "E": 0.66, "L": 0.62, "I": 0.2, "N": 0.82, "B": 0.72, "S": 0.68, "T": 0.75, "–": 0.7, " ": 0.35}


def carve_text(d, r, text, x, y, cap_h, stroke, fill=0):
    """Cut capitals with a chisel: each stroke a wedge that swells mid-stroke, ends bitten.
    Returns the advance width. Coordinates in film px, drawn on an SS canvas."""
    adv = 0.0
    for ch in text:
        w = _WIDTH[ch] * cap_h * 0.78
        for s in _LETTERS[ch]:
            if s[0] == "p":
                pts = list(s[1:])
            elif s[0] == "a":
                _, cx, cy, rx, ry, a0, a1 = s
                pts = [(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a)))
                       for a in np.linspace(a0, a1, 10)]
            else:
                pts = [s[0], s[1]]
            P = [(x + adv + px * w, y + py * cap_h) for px, py in pts]
            for i in range(len(P) - 1):
                (ax, ay), (bx, by) = P[i], P[i + 1]
                for k in range(6):
                    u0, u1 = k / 6, (k + 1) / 6
                    sw = stroke * (0.75 + 0.45 * math.sin(math.pi * (u0 + u1) / 2)) * r.uniform(0.85, 1.15)
                    d.line([((ax + (bx - ax) * u0) * SS, (ay + (by - ay) * u0) * SS),
                            ((ax + (bx - ax) * u1 + r.uniform(-.15, .15)) * SS, (ay + (by - ay) * u1 + r.uniform(-.15, .15)) * SS)],
                           fill=fill, width=max(1, int(sw * SS)))
            if s[0] not in ("a", "p") and r.rand() < 0.8:          # bracketed serif nicks at stroke ends
                for (ex, ey) in (P[0], P[-1]):
                    if ey in (y, y + cap_h) or abs(ey - y) < .5 or abs(ey - y - cap_h) < .5:
                        d.line([((ex - stroke * 1.1) * SS, ey * SS), ((ex + stroke * 1.1) * SS, ey * SS)], fill=fill, width=max(1, int(stroke * 0.7 * SS)))
        adv += w + cap_h * 0.16
    return adv


def text_width(text, cap_h):
    return sum(_WIDTH[c] * cap_h * 0.78 + cap_h * 0.16 for c in text) - cap_h * 0.16


@functools.lru_cache(None)
def _hardware(seed):
    """Masks (SS) of the handmade rear platform and the destination board, at rest.
    Returns dict(back_ink, back_paper, front_ink, board_ink, board_cut)."""
    r = rng(seed, "hardware")
    bi, db = canvas(); bp, dbp = canvas(); fi, df = canvas(); oi, do = canvas()
    P = lambda px, py: bus_pt(px, py)
    def R(d, x0, y0, x1, y1, amp=0.35):
        a, b = P(x0, y0), P(x1, y1)
        wobbly_quad(d, r, a[0], a[1], b[0], b[1], amp=amp)
    X0, X1 = PLATE_CUT - 2, PLAT_END
    R(dbp, X0, 18, X1, 226)                                   # lit platform opening (paper)
    R(db, X0, 14, X1, 34)                                     # canopy
    a, b = P(X0 + 8, 30), P(X1 - 4, 74)                       # arched lit head cut in the canopy
    db.rectangle([a[0] * SS, a[1] * SS, b[0] * SS, (a[1] + b[1]) / 2 * SS], fill=255)
    db.pieslice([a[0] * SS, a[1] * SS, b[0] * SS, b[1] * SS], 180, 360, fill=0)
    R(db, X0, 14, X0 + 7, 226)                                # rear bulkhead post
    R(db, X0, 220, X1, 233)                                   # platform floor (end grain gouges cut in later)
    R(db, X0 + 12, 247, X1 - 8, 254)                          # step
    for hx in (X0 + 20, X1 - 16):                             # step hangers
        R(db, hx, 232, hx + 3.5, 249)
    R(db, X0 + 7, 150, X1 - 16, 156)                          # waist rail behind the passenger
    # front layer: stanchion (in front of the puppet), chain loop, grab rail
    sx = X1 - 15
    R(df, sx, 30, sx + 6.5, 226, amp=0.25)
    a = P(sx - 2, 28); b = P(sx + 8.5, 33); df.ellipse([a[0] * SS, a[1] * SS, b[0] * SS, b[1] * SS], fill=255)
    for k in range(18):                                       # chain: rings sag between post and stanchion
        u = k / 17; x = X0 + 8 + u * (sx - X0 - 8); y = 184 + 13 * math.sin(math.pi * u)
        c = P(x, y); rx, ry = 2.0 * K_BUS * 1.4, 1.7 * K_BUS
        if k % 2:
            df.ellipse([(c[0] - rx) * SS, (c[1] - ry) * SS, (c[0] + rx) * SS, (c[1] + ry) * SS], outline=255, width=max(2, int(0.9 * SS)))
        else:
            df.line([((c[0] - rx) * SS, c[1] * SS), ((c[0] + rx) * SS, c[1] * SS)], fill=255, width=max(2, int(1.1 * SS)))
    # bell cord along the canopy
    a = P(X0 + 9, 37); b = P(X1 - 10, 37)
    db.line([(a[0] * SS, a[1] * SS), (b[0] * SS, (b[1] + 0.6) * SS)], fill=255, width=int(1.2 * SS))
    # destination board on the roof: ink board, capitals carved out (paper shows through)
    x0, y0, x1, y1 = board_rect()
    wobbly_poly(do, r, [(x0 - 2, y0 + 1), (x1 + 2, y0), (x1 + 1, y1), (x0 - 1, y1 + 0.5)], amp=0.5)
    for bx in (x0 + 26, x1 - 30):                             # board brackets
        wobbly_quad(do, r, bx, y1, bx + 3.2, y1 + 6, amp=0.3)
    cut, dcut = canvas()
    txt = "MADELEINE – BASTILLE"
    cap = (y1 - y0) * 0.56; stroke = cap * 0.15
    tw = text_width(txt, cap)
    carve_text(dcut, r, txt, (x0 + x1) / 2 - tw / 2, (y0 + y1) / 2 - cap / 2, cap, stroke, fill=255)
    wobbly_quad(dcut, r, x0 + 2.5, y0 + 2.0, x1 - 2.5, y0 + 2.9, amp=0.2)   # inner border gouges
    wobbly_quad(dcut, r, x0 + 2.5, y1 - 2.8, x1 - 2.5, y1 - 1.9, amp=0.2)
    return dict(back_ink=arr(bi), back_paper=arr(bp), front_ink=arr(fi), board_ink=arr(oi), board_cut=arr(cut))


# ------------------------------------------------------------------ H3 · two-tone print of the Rol bus
WINDOWS = [(278, 400), (404, 512), (518, 575), (580, 681)]   # glass panes (plate film px), y 48..118
REAR_PANE = 3                                                # re-cut light so the A6 seat reads


def print_levels(gray):
    """CLAHE + median + threshold into key, tint, shade (photo-linocut transfer)."""
    cl = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray.astype(np.uint8))
    cl = cv2.medianBlur(cl, 3)
    g = cv2.GaussianBlur(cl.astype(np.float32), (0, 0), 1.0)
    ink = np.clip((92 - g) / 8, 0, 1)
    tint = np.clip((150 - g) / 8, 0, 1) * (1 - ink)
    shade = np.clip((196 - g) / 10, 0, 1) * (1 - ink) * (1 - tint)
    return ink, tint, shade


def _region(px0, py0, px1, py1):
    m = np.zeros((H * SS, W * SS), np.float32)
    a, b = bus_pt(px0, py0), bus_pt(px1, py1)
    m[int(a[1] * SS):int(b[1] * SS), int(a[0] * SS):int(b[0] * SS)] = 1
    return m


@functools.lru_cache(None)
def _bus_cut(seed):
    gray2, alpha2, meta = bus_plate()
    S = meta.get("scale", 2)
    g = _plate_to_screen(gray2, S)
    a = np.clip(_plate_to_screen(alpha2, S), 0, 1)
    cutx = (BUS_REST_X + PLATE_CUT * K_BUS) * SS
    a[:, int(cutx):] = 0
    pi, pt_, ps = print_levels(np.clip(g, 0, 255))
    win = sum(_region(x0, 48, x1, 118) for x0, x1 in WINDOWS)
    rear = _region(*WINDOWS[REAR_PANE][:1], 48, WINDOWS[REAR_PANE][1], 118)
    letters = _region(272, 31, 678, 47)
    roofstrip = _region(36, 14, 690, 31)
    rail = _region(276, 118, 690, 130)
    cabwin = _region(36, 44, 276, 124)
    # BODY: solid black key block; real highlights (mouldings, panel edges) survive as thin cream cuts
    hl = cv2.morphologyEx(np.clip(g, 0, 255).astype(np.uint8), cv2.MORPH_TOPHAT, np.ones((1, 15), np.uint8)).astype(np.float32)
    hl2 = cv2.morphologyEx(np.clip(g, 0, 255).astype(np.uint8), cv2.MORPH_TOPHAT, np.ones((15, 1), np.uint8)).astype(np.float32)
    cuts = np.clip((np.maximum(hl, hl2) - 62) / 10, 0, 1)
    cuts = cuts * (cv2.morphologyEx((cuts > 0.5).astype(np.uint8), cv2.MORPH_OPEN, np.ones((1, 31), np.uint8)) > 0)  # keep only long moulding lines
    body = a * (1 - np.clip(win + letters + roofstrip + rail + cabwin, 0, 1))
    ink = body * (1 - cuts * 0.9)
    tint = np.zeros_like(ink); shade = body * cuts * 0.9
    # WINDOWS: printed photo levels - the real 1916 passengers as ink heads on light glass
    wi, wt, ws = print_levels(np.clip(g * 1.25 + 20, 0, 255))
    wv = np.clip(win - rear, 0, 1) * a
    ink += wi * wv; tint += wt * wv * 0.7; shade += np.clip(ws + wt * 0.3, 0, 1) * wv
    shade += rear * a * 0.65                                   # rear bay re-cut light (seat reads)
    # CAB OPENINGS: background seen through the cab is cut away; driver/pillars keep their ink
    ci_, ct_, _ = print_levels(np.clip(g, 0, 255))
    cv_ = cabwin * a
    ink += np.clip(ci_ * 1.2, 0, 1) * cv_; tint += ct_ * cv_ * 0.4
    # COMPAGNIE lettering strip and roof: light boards, the real letters stay ink
    li, lt, _ = print_levels(np.clip(g, 0, 255))
    lv = letters * a
    ink += li * lv; shade += (1 - li) * lv * 0.4
    shade += roofstrip * a * 0.75; tint += roofstrip * a * np.clip((150 - g) / 40, 0, 1) * 0.6
    ink += rail * a * 0.0; shade += rail * a * 0.5
    ink = np.clip(ink, 0, 1); tint = np.clip(tint, 0, 1) * (1 - ink); shade = np.clip(shade, 0, 1) * (1 - ink)
    hw = _hardware(seed)
    paper_a = np.clip(a + hw["back_paper"] + hw["back_ink"] + hw["board_ink"], 0, 1)
    ink = np.clip(ink + hw["back_ink"] + hw["board_ink"] * (1 - hw["board_cut"]), 0, 1)
    tint *= (1 - hw["board_ink"]); shade *= (1 - hw["board_ink"])
    floor = _region(PLATE_CUT, 222, PLAT_END, 231)            # end-grain cuts in the platform floor
    rr = rng(seed, "floor")
    stripes = (np.sin(np.arange(W * SS)[None, :] / (3.1 * SS) + rr.uniform(0, 6)) > 0.75).astype(np.float32)
    ink = ink * (1 - floor * stripes * 0.8)
    key = print_block(ink, seed, "bus-key", starve=0.015, edge=0.30)
    alpha = cv2.GaussianBlur(paper_a, (0, 0), 0.8)
    img = paper_ground(seed, "bus-paper")
    img = lay(img, shade, SHADE)
    img = lay(img, print_block(tint, seed, "bus-tint", starve=0, edge=0.2), TINT)
    img = lay(img, key, INK)
    return img, alpha


@functools.lru_cache(None)
def _photo_textures():
    """Photographic fills for the handmade outlines in the photographic-plate treatment:
    dark-panel and light-roof textures sampled from the Rol bus plate itself (tiled)."""
    gray2, alpha2, meta = bus_plate()
    S = meta.get("scale", 2)
    dark = gray2[int(150 * S):int(205 * S), int(300 * S):int(660 * S)].astype(np.float32)
    light = gray2[int(16 * S):int(28 * S), int(300 * S):int(660 * S)].astype(np.float32)
    def tile(t):
        reps = (H * SS // t.shape[0] + 2, W * SS // t.shape[1] + 2)
        return np.tile(t, reps)[:H * SS, :W * SS]
    sky = _gray(ROL)[60:300, 560:900].astype(np.float32)               # real 1916 sky over the Opera
    sky = cv2.resize(sky, (W * SS, H * SS), interpolation=cv2.INTER_CUBIC)
    return tile(dark), sky


@functools.lru_cache(None)
def _bus_photo(seed):
    gray2, alpha2, meta = bus_plate()
    S = meta.get("scale", 2)
    g = _plate_to_screen(gray2, S)
    a = np.clip(_plate_to_screen(alpha2, S), 0, 1)
    a[:, int((BUS_REST_X + PLATE_CUT * K_BUS) * SS):] = 0
    hw = _hardware(seed)
    dark, light = _photo_textures()
    lit = light
    gg = g * a
    gg = gg * (1 - hw["back_paper"]) + lit * hw["back_paper"] * (1 - a)
    inkm = np.clip(hw["back_ink"] + hw["board_ink"] * (1 - hw["board_cut"]), 0, 1)
    gg = gg * (1 - inkm) + dark * inkm
    gg = gg * (1 - hw["board_ink"] * hw["board_cut"]) + lit * hw["board_ink"] * hw["board_cut"]
    alpha = cv2.GaussianBlur(np.clip(a + hw["back_paper"] + hw["back_ink"] + hw["board_ink"], 0, 1), (0, 0), 0.8)
    return _grade(gg), alpha


def bus_body(seed, treatment="cut-paper"):
    """The bus at rest: printed Rol body (wheels removed) + handmade platform back + board."""
    img, a = _bus_cut(seed) if treatment == "cut-paper" else _bus_photo(seed)
    return to_rgba(img, a)


def bus_front(seed, treatment="cut-paper"):
    """In front of the platform puppet: stanchion, chain loop."""
    hw = _hardware(seed)
    m = hw["front_ink"]
    if treatment == "cut-paper":
        img = np.empty(m.shape + (3,), np.float32); img[:] = INK
        return to_rgba(img, print_block(m, seed, "front", starve=0, edge=0.2))
    dark, _ = _photo_textures()
    return to_rgba(_grade(dark * 0.8), cv2.GaussianBlur(m, (0, 0), 0.6))


def bell_tassel(seed, pull=0.0, treatment="cut-paper"):
    """The conductor's bell-cord tassel at the bell_cord anchor; pull in 0..1 (A7)."""
    im, d = canvas()
    an = anchors_world()["bell_cord"]
    tx, ty = an["x"], an["y"]
    d.line([(tx * SS, ty * SS), (tx * SS, (ty + 15 + 6 * pull) * SS)], fill=255, width=int(1.3 * SS))
    d.polygon([((tx - 2.2) * SS, (ty + 15 + 6 * pull) * SS), ((tx + 2.2) * SS, (ty + 15 + 6 * pull) * SS),
               ((tx + 1.4) * SS, (ty + 21 + 6 * pull) * SS), ((tx - 1.4) * SS, (ty + 21 + 6 * pull) * SS)], fill=255)
    m = arr(im)
    img = np.empty(m.shape + (3,), np.float32); img[:] = INK if treatment == "cut-paper" else INK2
    return to_rgba(img, cv2.GaussianBlur(m, (0, 0), 0.7))


def wheel_rest(name):
    """Rest centre (screen px) and radius of a wheel."""
    _, _, meta = bus_plate()
    w = meta["wheels"][name]
    cx, cy = bus_pt(w["center"][0], w["center"][1])
    return cx, cy, w["r"] * K_BUS


def wheel_angle_for(dx_travel):
    """Rolling: angle (deg) for a travelled distance in screen px (v/r)."""
    r = 41.0 * K_BUS
    return math.degrees(dx_travel / r)


@functools.lru_cache(maxsize=256)
def _wheel_tile(seed, name, treatment):
    gray2, _, meta = bus_plate()
    d = Path(meta["_dir"])
    t = np.asarray(Image.open(d / f"wheel_{name}.png"))
    r = meta["wheels"][name]["r"] * K_BUS * SS
    n = int(2 * r) | 1
    return cv2.resize(t[..., 0], (n, n), interpolation=cv2.INTER_AREA).astype(np.float32), n


def wheel(seed, name, angle_deg, treatment="cut-paper"):
    """A rotating cut wheel: (RGBA tile, (cx, cy) rest centre in screen px). Printed AFTER rotation,
    so the ink grain stays fixed to the spokes. The tyre is a solid carved ring."""
    g, n = _wheel_tile(seed, name, treatment)
    M = cv2.getRotationMatrix2D((n / 2, n / 2), angle_deg, 1.0)
    rt = cv2.warpAffine(g, M, (n, n), flags=cv2.INTER_LINEAR, borderValue=40)
    yy, xx = np.mgrid[0:n, 0:n]
    rad = np.hypot(xx - n / 2, yy - n / 2)
    circ = np.clip((n / 2 - 1 - rad) / 1.3, 0, 1).astype(np.float32)
    ring = circ * np.clip((rad - (n / 2 - 5.5 * SS)) / 1.2, 0, 1)
    if treatment == "cut-paper":
        wi, wt, ws = print_levels(np.clip(rt * 1.15, 0, 255))
        img = np.empty((n, n, 3), np.float32); img[:] = PAPER
        img = lay(img, ws, SHADE); img = lay(img, wt, TINT); img = lay(img, np.clip(wi + ring, 0, 1), INK)
    else:
        img = _grade(rt)
        img = lay(img, ring * 0.6, INK)
    small = to_rgba_tile(img, circ, n)
    cx, cy, _ = wheel_rest(name)
    return small, (cx, cy)


def to_rgba_tile(img, a, n):
    m = n // SS
    rgb = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((m, m), Image.LANCZOS)
    al = Image.fromarray((a * 255).astype(np.uint8)).resize((m, m), Image.LANCZOS)
    rgb.putalpha(al)
    return rgb


# ------------------------------------------------------------------ cast shadows (long horizontal strokes)
def bus_shadow(seed, dx=0.0):
    """The bus's long horizontal cast-shadow strokes on the road, shifted with the layer slide."""
    im, d = canvas()
    r = rng(seed, "bus-shadow")
    gy = side_ground_y(WORLD["bus_zc"])
    x0 = bus_pt(36, 0)[0] + dx; x1 = bus_pt(PLAT_END, 0)[0] + dx
    gouge(d, x0 - 30, gy + 2, x1 - x0 + 40, 8.5, r=r)
    gouge(d, x0 - 70, gy + 8.5, x1 - x0 - 10, 3, r=r)
    gouge(d, x0 + 40, gy + 12.5, x1 - x0 - 120, 1.6, r=r)
    m = arr(im)
    img = np.empty(m.shape + (3,), np.float32); img[:] = INK
    return to_rgba(img, cv2.GaussianBlur(m, (0, 0), 0.9))


def shadow_slivers(seed, element_id, feet, length=150.0):
    """Puppet cast shadows: horizontal slivers trailing behind feet. feet = [(x, y), ...] screen px.
    Shape is keyed by (seed, element_id) only, so the shadow does not boil between drawings."""
    im, d = canvas()
    r = rng(seed, "shadow", element_id)
    w0, l0, l1 = r.uniform(3.4, 4.6), r.uniform(.8, .95), r.uniform(.45, .65)
    for x, y in feet:
        gouge(d, x - length * l0, y + 1.5, length, w0)
        gouge(d, x - length * l0 + length * 0.3, y + 6, length * l1, 2.0)
    m = arr(im)
    img = np.empty(m.shape + (3,), np.float32); img[:] = INK2
    return to_rgba(img, cv2.GaussianBlur(m, (0, 0), 0.6 * SS))


# ------------------------------------------------------------------ H5 · overhead plan stage
@functools.lru_cache(None)
def _plan_backdrop(seed):
    r = rng(seed, "plan")
    ki, dk = canvas(); ti, dt = canvas(); si, ds = canvas(); ci, dc = canvas(); di, dd = canvas()
    fy = plan_xy(0, WORLD["facade_z"])[1]
    fk_ = plan_xy(0, WORLD["far_kerb_z"])[1]
    nk = plan_xy(0, WORLD["near_kerb_z"])[1]
    # roofs from above: zinc mansards (dark tint) with seam ribs, chimney blocks, courtyards
    dd.rectangle([0, 0, W * SS, fy * SS], fill=255)
    x = -r.uniform(0, 40)
    while x < W:
        bw = r.uniform(130, 260)
        for xx in np.arange(x + 3, x + bw - 3, r.uniform(5, 7)):
            dc.line([(xx * SS, 2 * SS), ((xx + r.uniform(-.6, .6)) * SS, (fy - 8) * SS)], fill=255, width=SS)
        for _ in range(r.randint(2, 5)):
            cx = r.uniform(x + 10, x + bw - 20)
            wobbly_quad(dk, r, cx, r.uniform(8, 22), cx + r.uniform(8, 16), r.uniform(26, 36), amp=0.5)
        dk.rectangle([(x + bw - 1.5) * SS, 0, (x + bw + 1.5) * SS, fy * SS], fill=255)   # party walls
        x += bw
    wobbly_quad(dk, r, -2, fy - 8, W + 2, fy, amp=0.4)                  # cornice edge from above
    # cornice shadow falling across the far pavement
    wobbly_quad(dt, r, -2, fy, W + 2, fy + 22, amp=1.2)
    ds.rectangle([0, fy * SS, W * SS, fk_ * SS], fill=255)
    dk.rectangle([0, fk_ * SS, W * SS, (fk_ + 3) * SS], fill=255)        # far kerb
    # roadway: tint, setts gouged as short arcs in rows (plan gouges)
    dt.rectangle([0, (fk_ + 3) * SS, W * SS, nk * SS], fill=255)
    for yy in np.arange(fk_ + 6, nk - 2, 7.5):
        xx = r.uniform(-8, 0)
        while xx < W:
            l = r.uniform(5, 9)
            gouge(dc, xx, yy + r.uniform(-.7, .7), l, r.uniform(.8, 1.6), bow=r.uniform(-.8, .8))
            xx += l + r.uniform(1.5, 3.5)
    wobbly_quad(dk, r, -2, nk, W + 2, nk + 5, amp=0.5)                   # near kerb
    for _ in range(170):                                                 # near pavement: long gouges
        gouge(dk, r.uniform(-200, W), r.uniform(nk + 8, H + 4), r.uniform(40, 300), r.uniform(.8, 3.0), r=r)
    for _ in range(50):
        gouge(dt, r.uniform(-200, W), r.uniform(nk + 8, H + 4), r.uniform(60, 300), r.uniform(1.5, 5), r=r)
    img = paper_ground(seed, "plan-paper")
    img = lay(img, arr(si), SHADE)
    img = lay(img, print_block(arr(ti), seed, "plan-tint", starve=0, edge=0.2) * 0.9, TINT)
    img = lay(img, arr(ci) * 0.8, SHADE)
    img = lay(img, print_block(arr(di), seed, "plan-dtint", starve=0.05) * 0.95, DTINT)
    img = lay(img, arr(ci) * 0.6, SHADE)
    return lay(img, print_block(arr(ki), seed, "plan-key", starve=0.06), INK)


def plan_backdrop(seed, treatment="cut-paper"):
    """Overhead: roofs, cornice edge and shadow, kerbs, sett gouges, pavement gouges."""
    return to_rgba(_plan_backdrop(seed))


def plan_bus_rect():
    x0 = bus_pt(36.5, 0)[0]; x1 = bus_pt(PLAT_END, 0)[0]
    y0 = plan_xy(0, WORLD["bus_z0"])[1]; y1 = plan_xy(0, WORLD["bus_z1"])[1]
    return x0, y0, x1, y1


@functools.lru_cache(None)
def _plan_bus(seed):
    r = rng(seed, "plan-bus")
    ki, dk = canvas(); ti, dt = canvas(); si, ds = canvas(); ci, dc = canvas(); al, da = canvas()
    x0, y0, x1, y1 = plan_bus_rect()
    px0 = bus_pt(PLATE_CUT, 0)[0]
    # silhouette: roof with rounded front (cab at left), open platform at the rear
    da.rounded_rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], radius=int(14 * SS), fill=255)
    da.rectangle([(x0 + 20) * SS, y0 * SS, x1 * SS, y1 * SS], fill=255)
    dk.rounded_rectangle([x0 * SS, y0 * SS, px0 * SS, y1 * SS], radius=int(14 * SS), fill=255)
    dk.rectangle([(x0 + 20) * SS, y0 * SS, px0 * SS, y1 * SS], fill=255)
    # roof: light canvas roof (the real CGO roof is pale) cut out of the ink silhouette, leaving
    # a black rim; carved ribs (hoops) and a lantern strip
    rim, drim = canvas()
    drim.rounded_rectangle([(x0 + 7) * SS, (y0 + 7) * SS, (px0 - 5) * SS, (y1 - 7) * SS], radius=int(10 * SS), fill=255)
    dk.bitmap((0, 0), rim, fill=0)
    wobbly_quad(ds, r, x0 + 7, y0 + 7, px0 - 5, y1 - 7, amp=0.5)
    for xx in np.arange(x0 + 58, px0 - 12, 34 + r.uniform(-2, 2)):
        wobbly_quad(dk, r, xx, y0 + 9, xx + 3.2, y1 - 9, amp=0.4)
    for _ in range(60):
        gouge(dt, r.uniform(x0 + 40, px0 - 60), r.uniform(y0 + 12, y1 - 12), r.uniform(20, 90), r.uniform(.8, 2.0), r=r)
    wobbly_quad(dt, r, x0 + 46, (y0 + y1) / 2 - 6, px0 - 8, (y0 + y1) / 2 + 6, amp=0.4)
    # bonnet/cab hood (dark tint) at the front
    wobbly_quad(dt, r, x0 + 6, y0 + 22, x0 + 40, y1 - 22, amp=0.5)
    # destination board laid along the near roof edge: carved capitals readable from above
    by0, by1 = y1 - 9 - 26, y1 - 9 - 4
    bx0, bx1 = x0 + 120, x0 + 120 + 310
    wobbly_quad(dk, r, bx0, by0, bx1, by1, amp=0.4)
    txt = "MADELEINE – BASTILLE"; cap = (by1 - by0) * 0.56
    carve_text(dc, r, txt, (bx0 + bx1) / 2 - text_width(txt, cap) / 2, (by0 + by1) / 2 - cap / 2, cap, cap * 0.15, fill=255)
    # open platform from above: floor boards (shade + ink seams), rail, the stanchion dot
    wobbly_quad(ds, r, px0, y0 + 2, x1 - 1, y1 - 2, amp=0.4)
    for yy in np.arange(y0 + 8, y1 - 4, 9):
        gouge(dk, px0 + 2, yy, x1 - px0 - 6, 1.2, r=r)
    wobbly_quad(dk, r, px0 - 1, y0, x1, y0 + 4, amp=0.3)                # far-side rail
    wobbly_quad(dk, r, x1 - 4, y0, x1, y1 - 24, amp=0.3)                # rear dash
    sx = anchors_world()["stanchion"]["x"] + 3; sy = plan_xy(0, WORLD["bus_z1"] - 6)[1]
    dk.ellipse([(sx - 4.5) * SS, (sy - 4.5) * SS, (sx + 4.5) * SS, (sy + 4.5) * SS], fill=255)
    for k in range(10):                                                  # chain (from above) to the dot
        u = k / 9; cx = px0 + 4 + u * (sx - px0 - 4); cy = sy + 1.5 * math.sin(math.pi * u)
        dk.ellipse([(cx - 1.6) * SS, (cy - 1.1) * SS, (cx + 1.6) * SS, (cy + 1.1) * SS], outline=255, width=SS)
    m = arr(al)
    img = paper_ground(seed, "plan-bus-paper")
    img = lay(img, arr(si) * m, SHADE)
    img = lay(img, print_block(arr(ti), seed, "plan-bus-tint", starve=0, edge=0.2) * m, TINT)
    key = print_block(np.clip(arr(ki) - arr(ci), 0, 1), seed, "plan-bus-key", starve=0.05)
    img = lay(img, key * m, INK)
    img = lay(img, arr(ci) * arr(ki) * 0.0, PAPER)
    return img, cv2.GaussianBlur(m, (0, 0), 0.8)


def plan_bus(seed, treatment="cut-paper"):
    """Overhead bus roof at rest (translate by the same dx as the side layer)."""
    img, a = _plan_bus(seed)
    return to_rgba(img, a)


def plan_bus_shadow(seed, dx=0.0):
    """Bus shadow in plan: a dark sliver offset toward the near kerb (flat frontal light, from the
    facade side), shifted with the layer slide."""
    im, d = canvas()
    x0, y0, x1, y1 = plan_bus_rect()
    r = rng(seed, "plan-bus-shadow")
    wobbly_quad(d, r, x0 + 10 + dx, y1 - 2, x1 - 4 + dx, y1 + 9, amp=0.8)
    m = arr(im)
    img = np.empty(m.shape + (3,), np.float32); img[:] = INK2
    return to_rgba(img, cv2.GaussianBlur(m, (0, 0), 1.0) * 0.85)


def plan_crowd(seed):
    """The waiting crowd seen from above: hat discs + shoulder ellipses on the far pavement,
    at the same x as the side-view mass pieces (same seed stream)."""
    im, d = canvas()
    r = rng(seed, "crowd")                       # same stream as the side crowd (same x placement)
    _ = r.uniform(0.96, 1.04)
    a0 = 726 + 0 * r.uniform(-30, 30); r2 = rng(seed, "plan-crowd")
    for (xa, xb) in ((726, 960), (0, 140)):
        n = int((xb - xa) / 13)
        for k in range(n):
            x = xa + (k + r2.uniform(0, 1)) * (xb - xa) / n
            z = r2.uniform(4, 38)
            px, py = plan_xy(x, z)
            sw = r2.uniform(7, 9.5)
            d.ellipse([(px - sw) * SS, (py - 4.5) * SS, (px + sw) * SS, (py + 4.5) * SS], fill=255)
            hr = r2.uniform(3.8, 5.4)
            d.ellipse([(px - hr + 1) * SS, (py - hr) * SS, (px + hr + 1) * SS, (py + hr) * SS], fill=255)
    m = arr(im)
    img = np.empty(m.shape + (3,), np.float32); img[:] = INK2
    return to_rgba(img, print_block(m, seed, "plan-crowd", starve=0, edge=0.25))


# ------------------------------------------------------------------ convenience compositor
def compose(layers):
    base = Image.new("RGBA", (W, H), tuple(PALETTE["paper"]) + (255,))
    for item in layers:
        if isinstance(item, tuple):
            im, (x, y) = item
            base.alpha_composite(im, (int(round(x)), int(round(y))))
        else:
            base.alpha_composite(item)
    return base


def shift(im, dx, dy=0):
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(im, (int(round(dx)), int(round(dy)))) if dx >= 0 and dy >= 0 else out.paste(im, (int(round(dx)), int(round(dy))), im)
    return out


def side_stage(seed, t=1.20, treatment="cut-paper"):
    """Stage-only side frame at clip time t (no puppets): editor/verify helper."""
    dx = bus_x(t) - BUS_REST_X
    travel = bus_x(0) - bus_x(min(t, 0.90 - 1 / 12))
    lay_ = [backdrop(seed, treatment), crowd(seed, treatment), bus_shadow(seed, dx), shift(bus_body(seed, treatment), dx)]
    for name in ("front", "rear"):
        tile, (cx, cy) = wheel(seed, name, wheel_angle_for(travel), treatment)
        lay_.append((tile, (cx + dx - tile.size[0] / 2, cy - tile.size[1] / 2)))
    lay_ += [shift(bus_front(seed, treatment), dx), shift(bell_tassel(seed, 0, treatment), dx)]
    return compose(lay_)


def plan_stage(seed, t=1.20):
    dx = bus_x(t) - BUS_REST_X
    return compose([plan_backdrop(seed), plan_crowd(seed), plan_bus_shadow(seed, dx), shift(plan_bus(seed), dx)])


# ------------------------------------------------------------------ measurement + sheet
def measure(im):
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    L = a @ np.array([0.299, 0.587, 0.114], np.float32)
    mx, mn = a.max(2), a.min(2)
    small = im.convert("RGB").resize((200, 120))
    q = small.quantize(6, method=Image.MEDIANCUT)
    pal = q.getpalette()[:18]; cnt = sorted(q.getcolors(), reverse=True)
    cols = [("#%02x%02x%02x" % tuple(pal[3 * i:3 * i + 3]), c / (200 * 120)) for c, i in cnt]
    return dict(p=[round(float(v)) for v in np.percentile(L, [2, 25, 50, 75, 98])],
                mid=round(float(((L > 55) & (L < 175)).mean()), 3), chroma=round(float((mx - mn).mean()), 1),
                palette=cols)


def _placeholder_puppets(img, seed, treatment):
    """Test-shot rig puppets placed into THIS stage geometry at the shove instant (sheet only;
    the film uses U3's rig/rig.py). Fill follows the treatment (ink / Bourse coat texture)."""
    import importlib.util, sys
    p = WS / "rig/rig.py"
    if p.exists():
        try:
            spec = importlib.util.spec_from_file_location("rig", p); rig = importlib.util.module_from_spec(spec)
            sys.modules["rig"] = rig; spec.loader.exec_module(rig)
            if hasattr(rig, "draw_side"):
                return rig.draw_side(img, seed, 1.20, treatment=treatment, stage=sys.modules[__name__]), "rig/rig.py (U3)"
        except Exception as e:  # noqa: BLE001  (sheet falls back to the test-shot rig)
            print("rig import failed:", e)
    spec = importlib.util.spec_from_file_location("tsbuild", WS / "test-shot-build/build.py")
    tb = importlib.util.module_from_spec(spec); spec.loader.exec_module(tb)
    km, dk = canvas()
    an = anchors_world()
    floor = an["platform_floor_y"]
    def place(kind, pose, x, gy, s, facing, hands=None, pr=None):
        pp, _ = tb.puppet_polys(kind, pose, 0, 0, s, facing, hands=hands)
        low = tb.foot_low(pp)
        pp, pa = tb.puppet_polys(kind, pose, x, gy - low, s, facing, hands=hands, pivot_rot=pr)
        for z, n, q in pp:
            dk.polygon([tuple(v * SS) for v in q], fill=255)
        return pa
    # long-necked man pushed back against the stanchion; jostler's flat hand on his chest
    mp = tb.stand_pose(); mp.update(torso=6, neck=14, head=8, arm_n=30, fore_n=34, arm_f=18, fore_f=30, leg_n=14, shin_n=-20)
    pa = place("man", mp, an["stanchion"]["x"] - 14, floor, 0.95, -1, pr=((0.0, 60.0), 12))
    tb.cut_braid(dk, pa, 0.95, -1)
    jp = dict(torso=-24, leg_n=34, shin_n=-30, leg_f=-30, shin_f=-14, arm_n=92, fore_n=4, arm_f=-36, fore_f=60, neck=8, head=8)
    place("jostler", jp, an["platform_x"][0] + 30, floor, 1.0, 1, hands={"fore_n": "farm_flat"})
    feet = []
    r = rng(seed, "sheet-runners")
    xs = [585, 500, 430, 350, 270, 200, 545]
    for i, x in enumerate(xs[:6 + int(r.rand() < 0.5)]):
        kind = "runA" if i % 2 == 0 else "runB"
        gy = side_ground_y(r.uniform(*WORLD["runner_z"]))
        s = r.uniform(1.2, 1.4) * (gy / 445)
        place(kind, tb.run_pose(int(r.randint(0, 6)), lean=-12), x + r.uniform(-15, 15), gy, s, 1)
        feet.append((x, gy))
    m = cv2.GaussianBlur(arr(km), (0, 0), 0.8 * SS / 2)
    out = img.copy()
    out.alpha_composite(shadow_slivers(seed, "runners", feet, 170))
    if treatment == "cut-paper":
        fill = np.empty(m.shape + (3,), np.float32); fill[:] = INK
    else:
        g = _gray(BOURSE).astype(np.float32)[560:760, 300:1100]
        g = np.tile(cv2.resize(g, (g.shape[1] * 2, g.shape[0] * 2)), (6, 2))[:H * SS, :W * SS]
        fill = _grade(g * 0.9)
    out.alpha_composite(to_rgba(fill, m))
    return out, "test-shot rig placeholder (U3 rig/rig.py not yet present)"


def make_sheet(seed=417):
    from PIL import ImageFont
    MEDIA.mkdir(parents=True, exist_ok=True)
    side_c = side_stage(seed, 1.20, "cut-paper")
    side_p = side_stage(seed, 1.20, "photographic-plate")
    plan = plan_stage(seed, 1.20)
    side_c.convert("RGB").save(MEDIA / "stage_side_cut_0417_t1.20.png")
    side_p.convert("RGB").save(MEDIA / "stage_side_photo_0417_t1.20.png")
    plan.convert("RGB").save(MEDIA / "stage_plan_0417_t1.20.png")
    side_c2, src = _placeholder_puppets(side_c, seed, "cut-paper")
    side_p2, _ = _placeholder_puppets(side_p, seed, "photographic-plate")
    side_c2.convert("RGB").save(MEDIA / "sheet_side_cut_with_puppets.png")
    ref = Image.open(REF).convert("RGB")
    hh = 360
    tiles = [("reference: martinoCharcoal.webp", ref), ("side · cut-paper · 0417 · t1.20", side_c2.convert("RGB")),
             ("side · photographic-plate · 0417 · t1.20", side_p2.convert("RGB")), ("overhead · cut-paper · 0417 · t1.20", plan.convert("RGB"))]
    rows = []
    f = ImageFont.truetype(str(ROOT / "assets/fonts/ibm-plex-mono.woff2"), 13)
    tw = int(hh * 16 / 9)
    sheet = Image.new("RGB", (2 * tw + 60, 2 * (hh + 120) + 70), tuple(PALETTE["shade"]))
    d = ImageDraw.Draw(sheet)
    d.text((20, 14), f"U2 stage · {SLUG} · seed 0417 · shove instant t=1.20 · puppets: {src}", font=f, fill=PALETTE["ink"])
    for i, (lab, im) in enumerate(tiles):
        m = measure(im)
        im2 = im.resize((int(im.width * hh / im.height), hh), Image.LANCZOS)
        x = 20 + (i % 2) * (tw + 20); y = 44 + (i // 2) * (hh + 120)
        sheet.paste(im2, (x, y))
        d.text((x, y + hh + 6), lab, font=f, fill=PALETTE["ink"])
        d.text((x, y + hh + 24), f"L p2/25/50/75/98 = {'/'.join(map(str, m['p']))}   mid(55-175) = {m['mid']:.1%}   chroma = {m['chroma']}", font=f, fill=PALETTE["ink"])
        for k, (hx, share) in enumerate(m["palette"]):
            c = tuple(int(hx[j:j + 2], 16) for j in (1, 3, 5))
            d.rectangle([x + k * 92, y + hh + 46, x + k * 92 + 20, y + hh + 66], fill=c, outline=PALETTE["ink"])
            d.text((x + k * 92 + 24, y + hh + 49), f"{hx[1:]} {share:.0%}", font=ImageFont.truetype(str(ROOT / "assets/fonts/ibm-plex-mono.woff2"), 10), fill=PALETTE["ink"])
        rows.append(dict(label=lab, **m))
    sheet.save(WS / "stage/stage-sheet.jpg", quality=90)
    (WS / "stage/stage-metrics.json").write_text(json.dumps(rows, indent=1))
    return rows


def write_evidence():
    rol = json.loads((MEDIA / "rol-meta.json").read_text()) if (MEDIA / "rol-meta.json").exists() else None
    bou = json.loads((MEDIA / "bourse-meta.json").read_text()) if (MEDIA / "bourse-meta.json").exists() else None
    def ii(d):
        p = list(d["query"]["pages"].values())[0]["imageinfo"][0]
        return p["url"].split("?")[0], p["sha1"], p["extmetadata"]["LicenseShortName"]["value"]
    sha = lambda p: hashlib.sha1(Path(p).read_bytes()).hexdigest()
    _, _, meta = bus_plate()
    ev = dict(foraged=[
        dict(id="F1-rol1916", title="1-6-16, nouvel autobus Madeleine-Bastille : [photographie de presse] / [Agence Rol]",
             author="Agence Rol (Bibliotheque nationale de France, Gallica)", license=ii(rol)[2] if rol else "Public domain",
             license_url="", source_url="https://commons.wikimedia.org/wiki/File:1-6-16,_nouvel_autobus_Madeleine-Bastille_-_btv1b6946541g.jpg",
             file_url=ii(rol)[0] if rol else "", commons_sha1=ii(rol)[1] if rol else "",
             local_path=str(ROL.relative_to(ROOT)), local_sha1=sha(ROL),
             what_it_shows="CGO motor bus on the Madeleine-Bastille line at Place de l'Opera, 1916; Grand Hotel facade at right; cobbled roadway",
             verified_date_or_place="Commons extmetadata (LicenseShortName 'Public domain', License 'pd', DateTimeOriginal 1916, Credit BnF), read 2026-11-16 (test-shot unit; re-request from this unit was HTTP 429, earlier response copied to stage/rol-meta.json)",
             used_as="side bus body (plate from %s, cab front re-compressed x<270 by 0.75), rotating wheel pieces, CLAHE+threshold+tint print; photographic-plate facade (homography of the right-hand building) and cobble plate; photographic fill textures for the handmade platform outlines" % Path(meta["_dir"]).relative_to(ROOT)),
        dict(id="F2-bourse1933", title="Greve des autobus - Place de la Bourse, le public attendant la reprise",
             author="Peyriras (photographe, actif vers 1930) (Bibliotheque nationale de France, Gallica)",
             license=ii(bou)[2] if bou else "unverified", license_url="",
             source_url="https://commons.wikimedia.org/wiki/File:Gr%C3%A8ve_des_autobus_-_Place_de_la_Bourse,_le_public_attendant_la_reprise_-_btv1b90350369.jpg",
             file_url=ii(bou)[0] if bou else "", commons_sha1=ii(bou)[1] if bou else "",
             local_path=str(BOURSE.relative_to(ROOT)), local_sha1=sha(BOURSE),
             what_it_shows="a crowd in overcoats and hats waiting for buses during the 1933 bus strike, Place de la Bourse, Paris",
             verified_date_or_place="Commons extmetadata read 2026-11-17 by this unit: LicenseShortName 'Public domain', License 'pd', UsageTerms 'Public domain', Copyrighted False, DateTimeOriginal 1933, Credit BnF. Photographer's death date not given (anonymous-ish credit 'actif vers 1930'): PD basis is Commons'/Gallica's tag, not independently established",
             used_as="GrabCut crowd mass (rect + dark-core scribbles + sure-BG bands, 5 iterations, islands <1500 px removed, failure mask exported) printed as a black mid-layer on the far pavement; in photographic-plate, its own greys; coat texture fill for placeholder puppets on the sheet only"),
    ], handmade=[
        dict(item="carved Haussmann facade", where="stage.py _facade_blocks/_backdrop_cut", how="unequal buildings (3-6 bays, own storey heights, mansard heights, horizontal or stippled ashlar gouges), hand-wobbled knife-cut windows with cross mullions, pediments, sills, irregular dormers and chimneys, continuous balconies with oval ironwork cuts; key + tint + dark-tint + shade blocks; shop band with lit arched shopfronts"),
        dict(item="gouged roadway and pavement, kerbs, long cast-shadow slivers", where="stage.py _street_blocks, bus_shadow, shadow_slivers"),
        dict(item="rear platform floor, step, hangers, canopy with arched lit head, waist rail, stanchion, chain, bell cord + tassel", where="stage.py _hardware, bus_front, bell_tassel"),
        dict(item="carved-capital destination board MADELEINE – BASTILLE", where="stage.py carve_text (chisel-stroke capitals defined in _LETTERS, no font), _hardware, _plan_bus"),
        dict(item="overhead plan stage: zinc roofs with seam ribs, cornice edge and shadow, kerbs, gouged setts, pavement gouges, carved bus roof with hoop ribs, roof-edge destination board, platform boards, stanchion dot, chain; plan crowd discs", where="stage.py _plan_backdrop, _plan_bus, plan_crowd"),
    ], absences=[
        dict(searched="fresh Commons extmetadata for F1 from this unit", result="HTTP 429 (rate-limited); the 2026-11-16 response from the test-shot unit is reused"),
        dict(searched="U1 plates (plates/bus_rect_rgba.png, facade/cobble plates, crowd cutouts)", result="not present at build time; stage.py prefers them automatically when they land (bus plate, wheels, crowd_mask.png); facade/cobble/crowd prepared here"),
    ], media=sorted(str(p.relative_to(ROOT)) for p in MEDIA.glob("*")))
    (WS / "stage/stage-evidence.json").write_text(json.dumps(ev, indent=1, ensure_ascii=False))
    (WS / "stage/anchors-world.json").write_text(json.dumps(anchors_world(), indent=1))


if __name__ == "__main__":
    rows = make_sheet(417)
    for r_ in rows:
        print(r_["label"], r_["p"], r_["mid"], r_["chroma"])
    write_evidence()
