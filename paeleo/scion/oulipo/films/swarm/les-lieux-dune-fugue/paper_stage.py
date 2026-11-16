"""paper_stage.py -- the simulated paper tabletop for *les-lieux-dune-fugue* (unit U2).

Every visible surface is a scissor-cut paper piece whose texture is a PRINT of a foraged
public-domain / CC photograph (one global tone curve per print run) on a foraged 1934 paper-stock
scan (LoC musftpsets.200218222). One lamp per capture state lights the table and casts true
height-based shadows; the cut core of each piece shows on its lamp side; the stock gives fibre and
age; each piece has a slight curl. The facade's two door leaves are FK flaps (SCION 32): wall ->
jamb -> leaf (revolute about a vertical hinge, pinhole f = 1100, Lambert shading) -> stud/panel
children. They lift toward the lens (the only way a tabletop flap can open), so their cut card
edge is genuinely visible and they cast their own lamp shadow on the stone. Depth below the
facade is a multiplane camera (SCION 44): parallax = 1 - depth, focus by plane, haze between the
memory planes. No kit grain, no vignette, no filters: softness comes from the lamp size, the
plane focus and the lens's veiling glare.

API
    render_shot(shot_id, t, overlay="none") -> PIL.Image 960x720
        shot_id 1..6, t = FILM time in seconds (plan sec. 5 windows, see SHOTS).
        overlay: "none" (picture only), "slate" (13 px mono present-tense slate),
                 "full" (slate + the plan's captions, for review renders only;
                 the editor sets captions from voice_score.json).
    render(t, overlay)      picks the shot by film time.
    EVENTS                  timestamped performance log (stage_events.json)

CLI  python3 paper_stage.py [bake|test|stills|compare|tests|all]
Pure numpy / PIL / cv2.  Does not import or edit kit.py.
"""
import os, sys, json, math, pickle, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = "/home/user/bolas/paeleo/scion/oulipo"
SRC = ROOT + "/films/sources/les-lieux-dune-fugue"
STAGE = SRC + "/stage"
CUT = STAGE + "/cut"
OUT = ROOT + "/films/swarm/les-lieux-dune-fugue"
REF = ROOT + "/assets/references/fugue1.webp"
W, H, P = 960, 720, 12
SW, SH = W + 2 * P, H + 2 * P
F_PIN = 1100.0
FPS = 24
os.makedirs(CUT, exist_ok=True)

# ------------------------------------------------------------------ source register (licences verified)
LOC_HS = "Public domain (Carol M. Highsmith Archive, Library of Congress: 'No known restrictions on publication')"
SOURCES = {
    "DOOR-C": dict(path=SRC + "/r2/hs_10700_10776.jpg", title="Exterior doorway, Joseph P. Kinnerary U.S. Courthouse, Columbus, Ohio",
                   author="Carol M. Highsmith", date="2009", license=LOC_HS, license_url="https://www.loc.gov/rr/print/res/482_high.html",
                   source_url="https://www.loc.gov/item/2010719611/", verified="loc.gov item JSON re-read 2026-11-16: rights_advisory 'No known restrictions on publication.'"),
    "DOOR-S": dict(path=SRC + "/r2/hs_25800_25800.jpg", title="Exterior door. U.S. Custom House, East Bay and Bull Streets, Savannah, Georgia",
                   author="Carol M. Highsmith", date="2013 November", license=LOC_HS, license_url="https://www.loc.gov/rr/print/res/482_high.html",
                   source_url="https://www.loc.gov/item/2014630119/", verified="loc.gov item JSON re-read 2026-11-16: 'No known restrictions on publication.'"),
    "BENCH": dict(path=SRC + "/r2/bench/sac_23429.jpg", title="Park bench in Sacramento, the capital city of the U.S. state of California and the county seat of Sacramento County",
                  author="Carol M. Highsmith", date="2012", license=LOC_HS, license_url="https://www.loc.gov/rr/print/res/482_high.html",
                  source_url="https://www.loc.gov/item/2013633886/", verified="loc.gov item JSON re-read 2026-11-16: 'No known restrictions on publication.'"),
    "STOCK": dict(path=STAGE + "/paper/ftp_blank_sheet.jpg", title="[Unidentified Production: Sketch no. 27, Blank Sheet of Paper]",
                  author="Federal Theatre Project (U.S.); Nels Astner", date="1934",
                  license="Public domain (U.S. government work; LoC: 'not aware of any copyright ... free to use and reuse')",
                  license_url="https://www.loc.gov/item/musftpsets.200218222/", source_url="https://www.loc.gov/item/musftpsets.200218222/",
                  verified="loc.gov item JSON re-read 2026-11-16: Federal Theatre Project restriction statement"),
    "JUNCTION-FB": dict(path=SRC + "/Rue_du_Soleil_rue_de_Belleville_Paris_20e.jpg", title="Rue du Soleil, rue de Belleville, Paris 20e.jpg",
                        author="Polymagou", date="unverified", license="CC BY-SA 4.0", license_url="https://creativecommons.org/licenses/by-sa/4.0",
                        source_url="https://commons.wikimedia.org/wiki/File:Rue_du_Soleil,_rue_de_Belleville,_Paris_20e.jpg",
                        verified="credits/les-lieux-dune-fugue.json record; Commons extmetadata re-check: see stage_tests.json 'licence_recheck'"),
}
JUNCTION_DIR = SRC + "/route/junction"


def load(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(np.float32) / 255.0


def lum(a):
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def to8(a):
    return (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)


rng = np.random.default_rng(1978)
DOOR_C = load(SOURCES["DOOR-C"]["path"])
DOOR_S = load(SOURCES["DOOR-S"]["path"])
BENCH = load(SOURCES["BENCH"]["path"])
STOCK = load(SOURCES["STOCK"]["path"])[300:2300, 400:2900]
STOCK_CREAM = STOCK.reshape(-1, 3).mean(0)
_SL = lum(STOCK)
_S_HI = _SL / (cv2.GaussianBlur(_SL, (0, 0), 20) + 1e-4)                      # fibre (high-pass)
_S_AGE = cv2.GaussianBlur(STOCK, (0, 0), 90) / STOCK_CREAM                     # age / foxing (low-pass, colour)


def fibre(h, w, hi=0.9, age=1.0):
    """multiplicative paper-stock modulation cut from a random spot of the 1934 sheet:
    fibre (high-pass luminance) x age (low-pass colour variation of the yellowed sheet)."""
    y = int(rng.integers(0, max(1, STOCK.shape[0] - h)))
    x = int(rng.integers(0, max(1, STOCK.shape[1] - w)))
    a, b = _S_HI[y:y + h, x:x + w], _S_AGE[y:y + h, x:x + w]
    if a.shape != (h, w):
        a, b = cv2.resize(a, (w, h)), cv2.resize(b, (w, h))
    return ((1 + hi * (a - 1))[..., None] * b ** age).astype(np.float32)


# ------------------------------------------------------------------ print runs (one global curve per run)
INK_DMAX = 0.085      # the darkest a print gets relative to the stock (ink cannot reach 0): lifts blacks


def print_run(img, target, ref_L, gamma, soft=0.7):
    """out_c = target_c * (L/ref_L)**gamma over the WHOLE photograph; dot gain softens it a little;
    ink density is limited so blacks sit on the paper, not at 0."""
    L = np.clip(lum(cv2.GaussianBlur(img, (0, 0), soft)), 1e-4, 1)
    r = np.clip((L / ref_L) ** gamma, 0, 1.6)
    out = r[..., None] * np.asarray(target, np.float32)[None, None] / 255.0
    return np.maximum(out, INK_DMAX * STOCK_CREAM * 0.6).astype(np.float32)


def cold_print(img):
    """the memory: a different print of the same photograph on a blue-grey ramp (not a filter)"""
    L = lum(cv2.GaussianBlur(img, (0, 0), 0.8))
    L = np.clip((L - 0.04) / 0.80, 0, 1) ** 0.95
    lo, hi = np.array([0.11, 0.13, 0.165]), np.array([0.60, 0.665, 0.74])
    return (lo + L[..., None] * (hi - lo)).astype(np.float32)


PRINTS_SPEC = {
    "PRINT-1 DOOR-C ochre": dict(src="DOOR-C", target=(102, 90, 64), ref_L=0.66, gamma=1.35),
    "PRINT-2 DOOR-C buff": dict(src="DOOR-C", target=(128, 121, 110), ref_L=0.62, gamma=0.5),
    "PRINT-3 DOOR-C iron": dict(src="DOOR-C", target=(52, 43, 29), ref_L=0.38, gamma=0.7),
    "PRINT-4 DOOR-S dark": dict(src="DOOR-S", target=(24, 21, 22), ref_L=0.42, gamma=0.25),
    "PRINT-7 DOOR-C return": dict(src="DOOR-C", target=(84, 72, 52), ref_L=0.66, gamma=1.35),
}
_SRCIMG = {"DOOR-C": DOOR_C, "DOOR-S": DOOR_S, "BENCH": BENCH}
PRINTS = {k: print_run(_SRCIMG[v["src"]], v["target"], v["ref_L"], v["gamma"]) for k, v in PRINTS_SPEC.items()}


def warm_print(img):
    return np.clip((img * np.array([1.0, 0.95, 0.84])) ** 1.1 * 0.88, 0, 1).astype(np.float32)


# ------------------------------------------------------------------ scissors
def scissor_alpha(w, h, inset=1.0, jit=0.7, nick=0.06, ss=4, top_only=False):
    """hand-scissored outline: straight facets of random length with small angle errors,
    occasional nicks; rasterised 4x and reduced (antialiased). Returns alpha, polyline."""
    pts = []
    corners = [(inset, inset), (w - inset, inset), (w - inset, h - inset), (inset, h - inset)]
    for k in range(4):
        (x0, y0), (x1, y1) = corners[k], corners[(k + 1) % 4]
        L = math.hypot(x1 - x0, y1 - y0)
        nx, ny = -(y1 - y0) / L, (x1 - x0) / L
        s = 0.0
        j = jit if (not top_only or k == 0) else 0.3
        while s < L:
            f = s / L
            off = abs(rng.normal(0, j))
            px, py = x0 + (x1 - x0) * f + nx * off, y0 + (y1 - y0) * f + ny * off
            pts.append((px, py))
            if rng.random() < nick and 6 < s < L - 6:
                d = rng.uniform(1.5, 3.0)
                pts.append((px + (x1 - x0) / L * 1.5 + nx * d, py + (y1 - y0) / L * 1.5 + ny * d))
            s += rng.uniform(9, 38)
    im = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(im).polygon([(x * ss, y * ss) for x, y in pts], fill=255)
    return np.asarray(im.resize((w, h), Image.LANCZOS)).astype(np.float32) / 255.0, pts


def mask_alpha(mask, jit=0.6, ss=1):
    """scissor-follow a GrabCut mask: contour -> faceted polyline (approxPolyDP) + jitter"""
    m8 = (mask > 0.5).astype(np.uint8)
    cs, _ = cv2.findContours(m8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    out = np.zeros(mask.shape, np.float32)
    for c in cs:
        if cv2.contourArea(c) < 30:
            continue
        a = cv2.approxPolyDP(c, 1.1, True).reshape(-1, 2).astype(np.float32)
        a += rng.normal(0, jit * 0.5, a.shape)
        big = np.zeros((mask.shape[0] * 4, mask.shape[1] * 4), np.uint8)
        cv2.fillPoly(big, [np.round(a * 4).astype(np.int32)], 255, cv2.LINE_AA)
        out = np.maximum(out, cv2.resize(big, mask.shape[::-1], interpolation=cv2.INTER_AREA).astype(np.float32) / 255)
    return out


# ------------------------------------------------------------------ lamp
class Lamp:
    """a single lamp over the table: position (stage px; z = height above the table), size (diffuser
    radius / height: sets penumbra), warmth, shadow density."""
    def __init__(self, name, x, y, z, size, warm, shadow):
        self.name, self.x, self.y, self.z, self.size = name, x, y, z, size
        self.warm = np.asarray(warm, np.float32)
        self.shadow = shadow
        yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32)
        r = np.sqrt((xx - x) ** 2 + (yy - y) ** 2 + z ** 2)
        E = (z / r) ** 3
        E0 = (z / math.sqrt((SW / 2 - x) ** 2 + (SH / 2 - y) ** 2 + z ** 2)) ** 3
        self.E = (0.84 + 0.16 * (E / E0) ** 0.5)[..., None] * self.warm      # diffuse lamp: weak falloff

    def offset(self, cx, cy, z_piece, dz):
        k = dz / max(self.z - z_piece, 1)
        return (cx - self.x) * k, (cy - self.y) * k, 0.6 + dz * self.size * 1.0

    def dirxy(self, cx, cy):
        v = np.array([self.x - cx, self.y - cy], np.float32)
        return v / (np.linalg.norm(v) + 1e-6)

    def row(self):
        return dict(name=self.name, x=self.x - P, y=self.y - P, z=self.z, size=self.size, warm=self.warm.tolist(), shadow=self.shadow)


# A: morning, upper left, low-ish warm, short soft shadows down-right.  B: evening, right, raking
# (lower and further out): longer shadows down-left, warmer, lower key.
LAMP_A = Lamp("A morning upper-left", x=P - 330, y=P - 300, z=1750, size=0.30, warm=(1.00, 0.985, 0.95), shadow=0.34)
LAMP_B = Lamp("B evening right raking", x=P + 1640, y=P - 40, z=1150, size=0.26, warm=(1.0, 0.95, 0.86), shadow=0.40)
MEM_LIGHT = dict(name="memory light (cold, upper left, its own direction; not a stage state)", dx=+5.0, dy=+6.0, blur=3.0,
                 strength=0.40, aperture_dx=+26, aperture_dy=+34)


def shift(a, dx, dy):
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(a, M, (a.shape[1], a.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def cut_core(alpha, lamp, x0, y0):
    """lighter cut core on the lamp-facing edge of a piece"""
    gy, gx = np.gradient(alpha)
    n = np.sqrt(gx * gx + gy * gy) + 1e-6
    h, w = alpha.shape
    yy, xx = np.mgrid[0:h, 0:w]
    lx, ly = lamp.x - (xx + x0), lamp.y - (yy + y0)
    ln = np.sqrt(lx * lx + ly * ly) + 1e-6
    lit = np.clip((-gx * lx - gy * ly) / (n * ln), 0, 1)
    edge = np.clip(n * 2.2, 0, 1) * alpha
    return (edge * lit) ** 0.8


class Piece:
    """a paper piece: texture (already a print), alpha (scissor cut), stage position, height z of
    its top above the table and zb of what it rests on (spacer), curl bow"""
    def __init__(self, name, rgb, alpha, x, y, z, zb, src, print_run="", curl=0.03, fib=True, crop=None, outline=None):
        self.name, self.rgb, self.a, self.x, self.y, self.z, self.zb, self.src = name, rgb, alpha, x, y, z, zb, src
        self.print_run, self.crop = print_run, crop
        self.outline_pts = 0 if outline is None else len(outline)
        h, w = alpha.shape
        self.curl_axis = rng.uniform(0, 2 * math.pi)
        self.curl_amt = curl
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        self.g = ((xx / w - .5) * math.cos(self.curl_axis) + (yy / h - .5) * math.sin(self.curl_axis))
        self.fib = fibre(h, w) if fib else np.ones((h, w, 1), np.float32)

    def curl_shade(self, lamp):
        """bowed piece: slope = 2*c*g along the curl axis; shading = 1 + slope . lamp direction"""
        h, w = self.a.shape
        d = lamp.dirxy(self.x + w / 2, self.y + h / 2)
        ax = np.array([math.cos(self.curl_axis), math.sin(self.curl_axis)])
        return (1 + self.curl_amt * 2 * self.g * float(ax @ d) * 2.0)[..., None]

    def row(self):
        h, w = self.a.shape
        return dict(piece=self.name, source=self.src, print_run=self.print_run, crop_in_source=self.crop,
                    stage_xy=[int(self.x - P), int(self.y - P)], size=[int(w), int(h)], height_px=self.z, rests_on_px=self.zb,
                    outline_vertices=self.outline_pts, curl=round(self.curl_amt, 3))


def compose(base, pieces, lamp, log=None, hmap=None):
    """composite pieces bottom-up with height-based lamp shadows; returns rgb, alpha (and fills hmap)"""
    can = base.copy()
    A = np.zeros(can.shape[:2], np.float32)
    for p in sorted(pieces, key=lambda q: q.z):
        h, w = p.a.shape
        cx, cy = p.x + w / 2, p.y + h / 2
        dx, dy, blur = lamp.offset(cx, cy, p.zb, p.z - p.zb)
        pad = int(abs(dx) + abs(dy) + 3 * blur + 4)
        X0, Y0 = max(p.x - pad, 0), max(p.y - pad, 0)
        X1, Y1 = min(p.x + w + pad, SW), min(p.y + h + pad, SH)
        if X1 > X0 and Y1 > Y0:
            sh = np.zeros((Y1 - Y0, X1 - X0), np.float32)
            ox, oy = p.x - X0, p.y - Y0
            ys0, xs0 = max(oy, 0), max(ox, 0)
            ys1, xs1 = min(oy + h, Y1 - Y0), min(ox + w, X1 - X0)
            sh[ys0:ys1, xs0:xs1] = p.a[ys0 - oy:ys1 - oy, xs0 - ox:xs1 - ox]
            sh = cv2.GaussianBlur(shift(sh, dx, dy) * 1.0, (0, 0), blur)
            can[Y0:Y1, X0:X1] *= (1 - lamp.shadow * sh)[..., None]
        px0, py0, px1, py1 = max(p.x, 0), max(p.y, 0), min(p.x + w, SW), min(p.y + h, SH)
        if px1 <= px0 or py1 <= py0:
            continue
        sl = (slice(py0 - p.y, py1 - p.y), slice(px0 - p.x, px1 - p.x))
        core = cut_core(p.a, lamp, p.x, p.y)[sl][..., None]
        col = p.rgb[sl] * p.fib[sl] * p.curl_shade(lamp)[sl]
        col = col * (1 - 0.5 * core) + STOCK_CREAM * 0.78 * 0.5 * core
        col = col * lamp.E[py0:py1, px0:px1]
        a = p.a[sl][..., None]
        can[py0:py1, px0:px1] = can[py0:py1, px0:px1] * (1 - a) + col * a
        A[py0:py1, px0:px1] = np.maximum(A[py0:py1, px0:px1], a[..., 0])
        if hmap is not None:
            hm = hmap[py0:py1, px0:px1]
            hmap[py0:py1, px0:px1] = np.where(a[..., 0] > 0.5, np.maximum(hm, p.z), hm)
        if log is not None:
            r = p.row(); r.update(lamp=lamp.name, shadow_dx=round(dx, 2), shadow_dy=round(dy, 2), shadow_blur=round(blur, 2))
            log.append(r)
    return can, A


def crop_resize(img, x0, y0, x1, y1, w, h):
    return cv2.resize(img[y0:y1, x0:x1], (w, h), interpolation=cv2.INTER_AREA)


_DC_L = cv2.GaussianBlur(lum(DOOR_C), (0, 0), 2)
_DC_G = cv2.GaussianBlur(np.hypot(cv2.Sobel(_DC_L, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(_DC_L, cv2.CV_32F, 0, 1, ksize=3)), (0, 0), 1)


def stone_patch(sw, sh, tries=300):
    """a patch of DOOR-C stone for one block: any of the acceptable (joint-free) candidates, chosen
    at random rather than the plainest, so blocks carry the photograph's real weathering"""
    areas = [((1230, 90, 1950, 780), [(1360, 380, 1570, 780)]), ((20, 60, 440, 700), [(40, 290, 240, 720)])]
    cands = []
    for _ in range(tries):
        (ax0, ay0, ax1, ay1), avoid = areas[int(rng.integers(0, 2))]
        if ax1 - ax0 <= sw + 2 or ay1 - ay0 <= sh + 2:
            (ax0, ay0, ax1, ay1), avoid = areas[0]
        x = int(rng.integers(ax0, ax1 - sw)); y = int(rng.integers(ay0, ay1 - sh))
        if any(not (x + sw < a0 or x > a1 or y + sh < b0 or y > b1) for a0, b0, a1, b1 in avoid):
            continue
        q = _DC_L[y:y + sh, x:x + sw]
        r, c = q.mean(1), q.mean(0)
        dip = max(np.abs(r - np.median(r)).max(), np.abs(c - np.median(c)).max(), float(np.percentile(_DC_G[y:y + sh, x:x + sw], 99.7)) * 0.6)
        cands.append((dip, x, y))
    cands.sort()
    ok = [c for c in cands if c[0] < 0.022] or cands[:8]
    d, x, y = ok[int(rng.integers(0, len(ok)))]
    return x, y


# ================================================================== P01 facade
OX0, OX1, OY0 = 125, 525, 216            # door opening (13.0 %-54.7 % of width, top at 30 %), exits the bottom
LEAF_W = (OX1 - OX0) // 2
JW = 52                                  # carved jamb, 5.4 % of width
JL0, JR0 = OX0 - 8 - JW, OX1 + 8          # jamb x
TOPY = 100                               # top of carved head band
PLY = 622                                # plinth top (86 %)
SILL_Y0, SILL_Y1 = 50, 72
BAL_H = 56                               # iron balcony band, top 8 %


def Fp(x, y):
    return int(x + P), int(y + P)


def build_facade():
    pcs = []
    st = PRINTS["PRINT-1 DOOR-C ochre"]
    # backing card (HANDMADE): pale mortar-toned card the blocks are butted on; seen only in the joints
    back = np.ones((SH, SW, 3), np.float32) * np.array([128, 113, 84], np.float32) / 255 * fibre(SH, SW, 0.6)

    def block(name, bx0, by0, bw, bh, z=2.0, zb=0.0, sc=2.2, tone_sd=0.09):
        sx, sy = stone_patch(int(bw / sc), int(bh / sc))
        tex = crop_resize(st, sx, sy, sx + int(bw / sc), sy + int(bh / sc), bw, bh)
        # each block a separate cut from the sheet: its own exposure and a slight warm/cool cast
        k = rng.normal(1.0, tone_sd)
        cast = np.array([1 + rng.normal(0, 0.012), 1.0, 1 + rng.normal(0, 0.02)], np.float32)
        tex = tex * k * cast
        a, pts = scissor_alpha(bw, bh, 0.6, 0.45, 0.05)
        pc = Piece(name, tex, a, *Fp(bx0, by0), z, zb, "DOOR-C", "PRINT-1 DOOR-C ochre",
                   crop=[sx, sy, int(bw / sc), int(bh / sc)], outline=pts, curl=rng.uniform(0.02, 0.05))
        pc.fib = fibre(bh, bw, 0.9, 1.8)          # each block from another spot of the aged sheet: stronger foxing
        pcs.append(pc)

    rows = [-P + BAL_H + 26, 128, 212, 298, 384, 470, 548, PLY]
    rows = [SILL_Y1, 128, 212, 298, 384, 470, 548, PLY]
    for xa, xb, tag in [(JR0 + JW, W + P, "R"), (-P, JL0, "L")]:
        for r in range(len(rows) - 1):
            y0, y1 = rows[r], rows[r + 1]
            x = xa - int(rng.integers(0, 140)) if tag == "R" else xa
            while x < xb:
                w = int(rng.integers(150, 250)) if tag == "R" else xb - xa
                gx, gy = rng.uniform(0.8, 1.4), rng.uniform(0.8, 1.3)        # gap = real cut tolerance
                bx0 = max(x, xa)
                bw, bh = int(min(x + w, xb) - bx0 - gx), int(y1 - y0 - gy)
                if bw > 12 and bh > 12:
                    block(f"ashlar-{tag}{r}-{x}", bx0, y0, bw, bh)
                x += w
    # shallow course between the sill and the carved head band
    for i, (a, b) in enumerate([(JL0 - 30, 190), (190, 380), (380, JR0 + JW)]):
        block(f"course-{i}", a + 1, SILL_Y1, b - a - 2, TOPY - SILL_Y1 - 1)
    # lintel course between the carved head band and the door
    for i, (a, b) in enumerate([(JL0 + JW, 262), (262, 392), (392, JR0)]):
        block(f"lintel-{i}", a + 1, TOPY + 30, b - a - 2, OY0 - (TOPY + 30) - 1, z=3.0)
    # narrow plain reveals beside the leaves
    for i, (a, b) in enumerate([(JL0 + JW, OX0 + 2), (OX1 - 2, JR0)]):
        bw, bh = b - a, PLY - (TOPY + 30)
        sx, sy = stone_patch(bw * 2, int(bh / 0.9))
        tex = crop_resize(st, sx, sy, sx + bw * 2, sy + int(bh / 0.9), bw, bh) * 0.9
        al, pts = scissor_alpha(bw, bh, 0.4, 0.3, 0.0)
        pcs.append(Piece(f"reveal-{i}", tex, al, *Fp(a, TOPY + 30), 2.5, 0.0, "DOOR-C", "PRINT-1 DOOR-C ochre",
                         crop=[sx, sy, bw * 2, int(bh / 0.9)], outline=pts))
    # carved vine jambs: the Columbus jamb panel cut narrow, two lengths per jamb (a real joint)
    jamb_src = st[312:1088, 480:606]
    js = cv2.resize(jamb_src, (JW, int(jamb_src.shape[0] * JW / jamb_src.shape[1])), interpolation=cv2.INTER_AREA)
    js = js * 0.96
    for side, jx in [("L", JL0), ("R", JR0)]:
        y, k = TOPY + 30, 0
        while y < PLY:
            hh = min(js.shape[0], PLY - y) - 1
            off = 0 if k == 0 else (int(rng.integers(0, js.shape[0] - hh)) if js.shape[0] > hh else 0)
            tex = js[off:off + hh] * rng.uniform(0.97, 1.03)
            al, pts = scissor_alpha(JW, hh, 0.7, 0.55, 0.07)
            pcs.append(Piece(f"jamb-{side}{k}", tex, al, *Fp(jx, y), 6.0, 2.0, "DOOR-C", "PRINT-1 DOOR-C ochre",
                             crop=[480, 312 + off, 126, 776], outline=pts))
            y += hh + 1; k += 1
    # carved head band: the same carving run horizontally
    band = np.rot90(js, 1).copy()
    x = JL0
    while x < JR0 + JW:
        ww = min(band.shape[1], JR0 + JW - x)
        al, pts = scissor_alpha(ww, 30, 0.7, 0.55, 0.07)
        pcs.append(Piece(f"headband-{x}", band[:30, :ww], al, *Fp(x, TOPY), 6.0, 2.0, "DOOR-C", "PRINT-1 DOOR-C ochre (rotated jamb)",
                         crop=[480, 312, 126, 776], outline=pts))
        x += ww + 1
    # sill under the balcony
    for i, (a, b) in enumerate([(-P + 2, 210), (210, 420), (420, 700), (700, W + P)]):
        block(f"sill-{i}", a, SILL_Y0, b - a - 1, SILL_Y1 - SILL_Y0, z=10.0, zb=2.0, tone_sd=0.03)
    # iron balcony band: Columbus window grille printed dark
    ir = PRINTS["PRINT-3 DOOR-C iron"][395:755, 1385:1525]
    irs = cv2.resize(ir, (int(ir.shape[1] * BAL_H / ir.shape[0]), BAL_H), interpolation=cv2.INTER_AREA)
    strip = np.concatenate([irs] * (SW // irs.shape[1] + 3), 1)
    for i, (a, b) in enumerate([(-P, 330), (330, W + P)]):
        ww = b - a
        al, pts = scissor_alpha(ww, BAL_H, 0.6, 0.6, 0.08)
        pcs.append(Piece(f"balcony-{i}", strip[:, 7 * i:7 * i + ww], al, *Fp(a, -P + 4), 7.0, 2.0, "DOOR-C", "PRINT-3 DOOR-C iron",
                         crop=[1385, 395, 140, 360], outline=pts))
    # plinth course (PRINT-2 of the Columbus marble base, low-contrast, darker)
    pb = PRINTS["PRINT-2 DOOR-C buff"]
    for i, (a, b) in enumerate([(-P, JL0 + JW), (JR0, 700), (700, 860), (860, W + P)]):
        ww, hh = b - a - 2, H + P - PLY
        sx, sy = 1240 + int(rng.integers(0, max(1, 300 - int(ww / 1.5)))), 950
        tex = crop_resize(pb, sx, sy, sx + int(ww / 1.5), sy + int(hh / 1.5), ww, hh) * rng.normal(1, 0.03)
        al, pts = scissor_alpha(ww, hh, 0.7, 0.5, 0.06)
        pcs.append(Piece(f"plinth-{i}", tex, al, *Fp(a + 1, PLY), 4.0, 0.0, "DOOR-C", "PRINT-2 DOOR-C buff",
                         crop=[sx, sy, int(ww / 1.5), int(hh / 1.5)], outline=pts))
    # house-number plaque: HANDMADE lettered card
    pw, ph = 34, 26
    pl = Image.new("RGB", (pw, ph), (30, 28, 31))
    ImageDraw.Draw(pl).text((pw / 2, ph / 2 + 1), "7", font=ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSerif.ttf", 20),
                            fill=(190, 180, 158), anchor="mm")
    al, pts = scissor_alpha(pw, ph, 0.5, 0.35, 0.0)
    pcs.append(Piece("plaque-7", np.asarray(pl).astype(np.float32) / 255, al, *Fp(626, 170), 5.0, 2.0, "HANDMADE", "lettered card",
                     curl=0.01, outline=pts))
    return back, pcs


def build_leaves():
    """leaf textures (2x) cut from the Savannah riveted door, printed dark; stud child per leaf;
    one texture per lamp state (the stud's own small shadow depends on the lamp)."""
    dk = PRINTS["PRINT-4 DOOR-S dark"]
    lh = 560
    half = [(232, 712), (718, 1192)]
    leaves = []
    w2, h2 = LEAF_W * 2, lh * 2
    for i, (a, b) in enumerate(half):
        hh = min(int(round((b - a) * h2 / w2)), dk.shape[0] - 78)
        base = cv2.resize(dk[78:78 + hh, a:b], (w2, h2), interpolation=cv2.INTER_AREA)
        alpha, pts = scissor_alpha(w2, h2, 1.0, 0.9, 0.03)
        fib = cv2.resize(fibre(lh, LEAF_W), (w2, h2))
        base = base * fib
        kx = 30 if i == 1 else w2 - 30          # stud near the meeting stile (child, fixed in leaf space)
        ky = 2 * 300
        stud = cv2.resize(dk[905:965, 455:515], (26, 26), interpolation=cv2.INTER_AREA) * 1.6
        sa = np.zeros((26, 26), np.float32); cv2.circle(sa, (13, 13), 12, 1.0, -1, cv2.LINE_AA)
        tex = {}
        for lamp in (LAMP_A, LAMP_B):
            d = lamp.dirxy(OX0 + P + 100, OY0 + P + 300)
            sdx, sdy = -d[0] * 6, -d[1] * 6
            shd = np.zeros(alpha.shape, np.float32)
            shd[ky - 13 + int(sdy):ky + 13 + int(sdy), kx - 13 + int(sdx):kx + 13 + int(sdx)] = sa
            t = base * (1 - 0.5 * cv2.GaussianBlur(shd, (0, 0), 3))[..., None]
            reg = (slice(ky - 13, ky + 13), slice(kx - 13, kx + 13))
            t[reg] = t[reg] * (1 - sa[..., None]) + stud * sa[..., None]
            tex[lamp.name] = t.astype(np.float32)
        u = np.tile(np.arange(w2, dtype=np.float32)[None, :] / 2, (h2, 1))     # distance from hinge, 1x px
        if i == 1:
            u = u[:, ::-1].copy()
        leaves.append(dict(tex=tex, a=alpha, u=u, knob=(kx / 2, ky / 2), w=LEAF_W, h=lh, outline=len(pts),
                           crop=[a, 78, b - a, hh]))
    return leaves


CARD_T = 5.0      # leaf card thickness (stage px)
CORE = STOCK_CREAM * np.array([0.80, 0.78, 0.74], np.float32)   # greyboard core colour of the cut edge


def leaf_points(theta_deg, left, cam):
    """FK chain wall -> jamb -> leaf: 3D points of a leaf at angle theta, projected by the pinhole.
    X right, Y down, Z = height above the table (toward the lens). Returns proj(u, v, n) where u is
    the distance from the hinge, v down the leaf from its top, n the depth into the card."""
    th = math.radians(theta_deg)
    hx = OX0 if left else OX1
    sgn = 1 if left else -1
    cx, cy = W / 2, H / 2

    def world(u, v, n=0.0):
        X = hx + sgn * (u * math.cos(th) + n * math.sin(th))
        Z = u * math.sin(th) - n * math.cos(th)
        return X, OY0 + v, Z

    def proj(u, v, n=0.0):
        X, Y, Z = world(u, v, n)
        k = F_PIN / (F_PIN - Z)
        return cx + (X - cam - cx) * k + P, cy + (Y - cy) * k + P

    return proj, world


def leaf_normal(theta_deg, left):
    th = math.radians(theta_deg)
    s = 1 if left else -1
    return np.array([-s * math.sin(th), 0.0, math.cos(th)]), np.array([s * math.cos(th), 0.0, math.sin(th)])


def lambert(n, lamp, X, Y, Z):
    l = np.array([lamp.x - P - X, lamp.y - P - Y, lamp.z - Z], np.float64)
    l /= np.linalg.norm(l)
    return max(float(n @ l), 0.0)


# ================================================================== memory planes (P01 shot 4) and P03
_BENCH_BOX = (700, 985, 1000, 1245)
_TRUNK_BOX = (300, 715, 710, 1392)
TRUNK_POLY = [(375, 722), (418, 716), (470, 724), (520, 717), (590, 722), (640, 726), (652, 800), (624, 900), (626, 1050),
              (642, 1150), (672, 1240), (692, 1300), (704, 1391), (306, 1391), (330, 1300), (372, 1200), (386, 1050), (380, 900), (393, 800)]


def grabcut(img, box, pad=(22, 18, 44, 40), iters=8, min_area=400):
    x0, y0, x1, y1 = box
    b8 = to8(img[y0:y1, x0:x1])[..., ::-1].copy()
    gm = np.zeros(b8.shape[:2], np.uint8)
    bg, fg = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(b8, gm, (pad[0], pad[1], b8.shape[1] - pad[2], b8.shape[0] - pad[3]), bg, fg, iters, cv2.GC_INIT_WITH_RECT)
    m = np.where((gm == 1) | (gm == 3), 1, 0).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    keep = np.zeros_like(m)
    for k in range(1, n):
        if stats[k, cv2.CC_STAT_AREA] > min_area:
            keep[lab == k] = 1
    full = np.zeros(img.shape[:2], np.uint8); full[y0:y1, x0:x1] = keep
    return full


def build_bench_masks():
    bm = grabcut(BENCH, _BENCH_BOX)
    # trunk: cut by hand along its silhouette (a scissor polygon; GrabCut merged it with the foliage)
    tm = np.zeros(BENCH.shape[:2], np.uint8)
    poly = np.array(TRUNK_POLY, np.float32) + np.random.default_rng(5).normal(0, 1.2, (len(TRUNK_POLY), 2))
    cv2.fillPoly(tm, [np.int32(poly)], 1)
    cv2.imwrite(CUT + "/bench_mask.png", bm[_BENCH_BOX[1]:_BENCH_BOX[3], _BENCH_BOX[0]:_BENCH_BOX[2]] * 255)
    cv2.imwrite(CUT + "/trunk_mask.png", tm[_TRUNK_BOX[1]:_TRUNK_BOX[3], _TRUNK_BOX[0]:_TRUNK_BOX[2]] * 255)
    return bm, tm


MSC = 0.62
BENCH_CENTER = (850, 1117)
BENCH_AT = (334, 556)


def memory_layers(bmask):
    """cold print of the Sacramento photograph: park (depth 1.0, with the bench inpainted out) and the
    GrabCut bench (depth 0.6) on its own plane; returned at stage res"""
    s = MSC
    hole = cv2.dilate(bmask, np.ones((9, 9), np.uint8))
    y0, y1, x0, x1 = 560, 1420, 520, 1200
    park8 = cv2.inpaint(to8(BENCH[y0:y1, x0:x1])[..., ::-1].copy(), hole[y0:y1, x0:x1], 9, cv2.INPAINT_TELEA)
    pc = cold_print(park8[..., ::-1].astype(np.float32) / 255)
    pw, ph = int(pc.shape[1] * s), int(pc.shape[0] * s)
    park = cv2.GaussianBlur(cv2.resize(pc, (pw, ph), interpolation=cv2.INTER_AREA), (0, 0), 1.8)
    park = park * cv2.resize(fibre(ph // 2, pw // 2, 0.5, 0.4), (pw, ph))
    canvas = np.zeros((SH, SW, 3), np.float32) + np.array([0.07, 0.08, 0.10], np.float32)
    px = BENCH_AT[0] - (BENCH_CENTER[0] - x0) * s
    py = BENCH_AT[1] - (BENCH_CENTER[1] - y0) * s
    X, Y = int(px + P), int(py + P)
    ys, xs = slice(max(Y, 0), min(Y + ph, SH)), slice(max(X, 0), min(X + pw, SW))
    canvas[ys, xs] = park[ys.start - Y:ys.stop - Y, xs.start - X:xs.stop - X]
    bx0, by0, bx1, by1 = _BENCH_BOX
    cold = cold_print(BENCH[by0:by1, bx0:bx1])
    bw, bh = int((bx1 - bx0) * s), int((by1 - by0) * s)
    bt = cv2.GaussianBlur(cv2.resize(cold, (bw, bh), interpolation=cv2.INTER_AREA), (0, 0), 0.8)
    ba = mask_alpha(cv2.resize(bmask[by0:by1, bx0:bx1].astype(np.float32), (bw, bh), interpolation=cv2.INTER_AREA), 0.4)
    ba = cv2.GaussianBlur(ba, (0, 0), 0.6)
    bpos = (BENCH_AT[0] - (BENCH_CENTER[0] - bx0) * s + P, BENCH_AT[1] - (BENCH_CENTER[1] - by0) * s + P)
    return dict(bg=canvas, bt=bt.astype(np.float32), ba=ba.astype(np.float32), bpos=bpos)


P03_BOX = (200, 400, 1520, 1390)


def p03_layers(bmask, tmask, log):
    """P03 present: warm print of the same photograph cut into planes:
    far park 1.0 (cutouts inpainted out: flagged invention, hidden by the pieces), trunk 0.7,
    bench 0.4 (each with its lamp-A shadow), litter strip 0 (scissored top edge)."""
    x0, y0, x1, y1 = P03_BOX
    s = W / (x1 - x0)
    warm = warm_print(BENCH)
    hole = np.maximum(cv2.dilate(bmask, np.ones((5, 5), np.uint8)), cv2.dilate(tmask, np.ones((9, 9), np.uint8)))
    park8 = cv2.inpaint(to8(warm)[..., ::-1].copy(), hole, 9, cv2.INPAINT_TELEA)[..., ::-1].astype(np.float32) / 255
    PAD = 20
    far = cv2.resize(park8[y0 - int(PAD / s):y1 + int(PAD / s), x0 - int(PAD / s):x1 + int(PAD / s)], (SW + 2 * PAD, SH + 2 * PAD),
                     interpolation=cv2.INTER_AREA)
    far = cv2.GaussianBlur(far, (0, 0), 1.3) * fibre(SH + 2 * PAD, SW + 2 * PAD, 0.7, 0.8)
    layers = {}
    for nm, m, box, z in [("trunk", tmask, _TRUNK_BOX, 3.0), ("bench", bmask, _BENCH_BOX, 4.0)]:
        bx0, by0, bx1, by1 = box
        bw, bh = int((bx1 - bx0) * s), int((by1 - by0) * s)
        bt = cv2.resize(warm[by0:by1, bx0:bx1], (bw, bh), interpolation=cv2.INTER_AREA)
        ba = mask_alpha(cv2.resize(m[by0:by1, bx0:bx1].astype(np.float32), (bw, bh), interpolation=cv2.INTER_AREA), 0.5)
        pc = Piece(f"p03-{nm}", bt, ba, int((bx0 - x0) * s) + P, int((by0 - y0) * s) + P, z, 0.0, "BENCH", "PRINT-6 BENCH warm",
                   crop=list(box), curl=0.0)
        layers[nm] = pc
    sy = int(H * 0.87)
    lt = cv2.resize(warm[y0:y1, x0:x1], (W, H), interpolation=cv2.INTER_AREA)[sy - 2:]
    lt = np.pad(lt, ((0, SH - P - sy + 2 - lt.shape[0]), (P, P), (0, 0)), mode="edge")
    la, pts = scissor_alpha(SW, lt.shape[0], 0.5, 2.2, 0.15)
    la[-6:] = 1
    layers["litter"] = Piece("p03-litter", lt, la, 0, P + sy - 2, 6.0, 0.0, "BENCH", "PRINT-6 BENCH warm (front strip)", curl=0.0,
                             crop=[x0, int(y0 + sy / s), x1 - x0, int((H - sy) / s)], outline=pts)
    return far, PAD, layers


# ================================================================== P02 junction
def junction_source():
    """U1's route/junction/ if present (first image), else the plan's fallback"""
    if os.path.isdir(JUNCTION_DIR):
        fs = sorted(f for f in os.listdir(JUNCTION_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png", ".tif")))
        if fs:
            return "route/junction/" + fs[0], load(JUNCTION_DIR + "/" + fs[0]), "U1 route/junction"
    return "JUNCTION-FB", load(SOURCES["JUNCTION-FB"]["path"]), "fallback (U1 route/junction/ absent at build time)"


def p02_layers(log):
    """far street (1.0 -> parallax 0.15), two stone corners (mid, 0.5), kerb + pavement (near, 1.0)"""
    jid, J, how = junction_source()
    out = dict(source=jid, how=how)
    if jid == "JUNCTION-FB":
        far_src = J[60:820, 960:1280]                    # the street receding (facades, balconies), above any sign
        kerb_src = J[1478:1707, 300:1260]                # pavement seam + kerb + gutter, no bollard, no shutter
        far_crop, kerb_crop = [960, 60, 320, 760], [300, 1478, 960, 229]
    else:
        h, w = J.shape[:2]
        far_src = J[: int(h * 0.5), int(w * 0.35):int(w * 0.65)]
        kerb_src = J[int(h * 0.7):, :]
        far_crop, kerb_crop = [int(w * 0.35), 0, int(w * 0.3), int(h * 0.5)], [0, int(h * 0.7), w, h - int(h * 0.7)]
    # graded as one warm print run so it sits with the stone (one global curve for the source)
    def junction_print(a):
        L = np.clip(lum(cv2.GaussianBlur(a, (0, 0), 0.7)), 1e-4, 1)
        tone = np.array([128, 113, 88], np.float32) / 255
        return np.maximum((L / 0.55) ** 1.1, 0.1)[..., None] * tone * 0.78 + a * 0.22 * tone / tone.mean()
    far = junction_print(far_src)
    fh = 600
    fw = int(far.shape[1] * fh / far.shape[0])
    far = cv2.GaussianBlur(cv2.resize(far, (fw, fh), interpolation=cv2.INTER_AREA), (0, 0), 1.8)
    far = far * 0.86 + np.array([0.48, 0.45, 0.40], np.float32) * 0.14            # haze toward the far plane
    far = far * fibre(fh, fw, 0.6, 0.6)
    kerb = junction_print(kerb_src)
    kh = 300
    kerb = cv2.resize(kerb, (SW + 40, kh), interpolation=cv2.INTER_AREA)
    st = PRINTS["PRINT-1 DOOR-C ochre"]; rt = PRINTS["PRINT-7 DOOR-C return"]
    corners = []
    # two corners: a lit front face and a narrower return face turned away (darker print run)
    for side, (fx0, fx1, rx0, rx1) in [("L", (-P - 30, 268, 268, 312)), ("R", (578, 622, 622, W + P + 30))]:
        y = -P
        k = 0
        while y < 470:
            hh = int(rng.integers(78, 96))
            for (a, b, pr, prn) in ([(fx0, fx1, st, "PRINT-1 DOOR-C ochre"), (rx0, rx1, rt, "PRINT-7 DOOR-C return")] if side == "L"
                                    else [(fx0, fx1, rt, "PRINT-7 DOOR-C return"), (rx0, rx1, st, "PRINT-1 DOOR-C ochre")]):
                bw = b - a - 1
                sx, sy = stone_patch(int(bw / 1.5), int(hh / 1.5))
                tex = crop_resize(pr, sx, sy, sx + int(bw / 1.5), sy + int(hh / 1.5), bw, hh - 1) * rng.normal(1, 0.05)
                al, pts = scissor_alpha(bw, hh - 1, 0.6, 0.5, 0.05)
                corners.append(Piece(f"p02-corner{side}-{k}-{a}", tex, al, a + P, y + P, 3.0, 0.0, "DOOR-C", prn,
                                     crop=[sx, sy, int(bw / 1.5), int(hh / 1.5)], outline=pts))
            y += hh; k += 1
    ka, kpts = scissor_alpha(SW + 40, kh, 0.5, 1.6, 0.1)
    kerb_piece = Piece("p02-kerb-pavement", kerb, ka, -20, SH - kh, 5.0, 0.0, jid, "PRINT-8 junction warm", crop=kerb_crop, outline=kpts)
    out.update(far=far, far_crop=far_crop, corners=corners, kerb=kerb_piece)
    return out


# route thread (HANDMADE): one ochre strip laid along the pavement seam, then the left branch
ROUTE = [(395, 437), (401, 450), (407, 462), (415, 478), (424, 494), (430, 505), (384, 508), (288, 510), (181, 512), (75, 513), (-11, 515)]


def route_strip(n_draw, lamp, kerb_off):
    """the strip in drawing n (0..6): the first n/6 of the polyline, cut from a print of the stone"""
    if n_draw <= 0:
        return None
    pts = np.array(ROUTE, np.float32)
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    Lk = seg[-1] * n_draw / 6
    keep = [p for p, s in zip(pts, seg) if s <= Lk]
    if len(keep) < len(pts):
        i = len(keep)
        f = (Lk - seg[i - 1]) / (seg[i] - seg[i - 1])
        keep.append(pts[i - 1] + (pts[i] - pts[i - 1]) * f)
    big = np.zeros((SH * 4, SW * 4), np.uint8)
    q = (np.array(keep) + [P + kerb_off, P]) * 4
    r = np.random.default_rng(7)
    for a, b in zip(q[:-1], q[1:]):
        cv2.line(big, tuple(np.int32(a)), tuple(np.int32(b)), 255, int(4 * (5.5 + r.normal(0, 0.4))), cv2.LINE_AA)
    return cv2.resize(big, (SW, SH), interpolation=cv2.INTER_AREA).astype(np.float32) / 255


# ================================================================== record card (shot 6)
def card_layers(log):
    SERIF = "/usr/share/fonts/truetype/freefont/FreeSerif.ttf"
    SERIF_I = "/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf"
    MONO = "/usr/share/fonts/truetype/freefont/FreeMono.ttf"
    table = np.ones((SH, SW, 3), np.float32) * np.array([44, 38, 33], np.float32) / 255 * fibre(SH, SW, 0.8, 0.5)
    cw, ch = 780, 560
    card = np.ones((ch, cw, 3), np.float32) * STOCK_CREAM * 0.86 * fibre(ch, cw, 1.0, 1.0)
    ink = Image.new("L", (cw, ch), 0)
    d = ImageDraw.Draw(ink)
    fs, fi, fm, fm_s = (ImageFont.truetype(SERIF, 22), ImageFont.truetype(SERIF_I, 19), ImageFont.truetype(MONO, 15),
                        ImageFont.truetype(MONO, 13))
    d.text((40, 34), "relevé · les lieux", font=fs, fill=230)
    nodes = [(110, 150, "P01", "porte, n° 7"), (390, 150, "P02", "carrefour"), (670, 150, "P03", "banc")]
    for x, y, a, b in nodes:
        d.ellipse((x - 9, y - 9, x + 9, y + 9), outline=230, width=2)
        d.text((x, y + 22), a, font=fm, fill=230, anchor="mt")
        d.text((x, y + 42), b, font=fi, fill=210, anchor="mt")
    lines = [
        ("P01  prise A · matin   /   prise B · soir   (même position)", fm),
        ("F1  un matin, avant huit heures ?        lien P01 : affirmé", fm_s),
        ("F2  le même jour, plus tard (ordre ?)    lien P02 : affirmé", fm_s),
        ("F3  inconnu (une heure ou un jour)       lien P03 : INFÉRÉ", fm_s),
        ("F4  âge 8–10 (source : un tiers)         sans lieu", fm_s),
        ("F5  vers l'hiver (déc.–fév.), année ?    lien P01→P03 : INFÉRÉ", fm_s),
    ]
    y = 250
    for s_, f in lines:
        d.text((40, y), s_, font=f, fill=225); y += 30 if f is fm else 26
    d.line((40, y + 10, cw - 40, y + 10), fill=120, width=1)
    d.text((40, y + 24), "photographies : Carol M. Highsmith, Library of Congress (domaine public)", font=fi, fill=215)
    d.text((40, y + 50), "carrefour : Polymagou, CC BY-SA 4.0 · papier : Federal Theatre Project, 1934 (LoC)", font=fi, fill=200)
    inkf = cv2.GaussianBlur(np.asarray(ink).astype(np.float32) / 255, (0, 0), 0.45)[..., None]
    inkc = np.array([0.16, 0.13, 0.11], np.float32)
    card = card * (1 - 0.88 * inkf) + inkc * card * 0.88 * inkf
    ca, cpts = scissor_alpha(cw, ch, 1.0, 0.8, 0.04)
    pcs = [Piece("card", card, ca, (SW - cw) // 2, (SH - ch) // 2 + 6, 1.5, 0.0, "HANDMADE+STOCK", "card on 1934 stock", curl=0.03,
                 fib=False, outline=cpts)]
    # the route as cut ochre strips glued on the card (raised 0.8 px)
    st = PRINTS["PRINT-1 DOOR-C ochre"]
    for i, ((xa, ya, *_), (xb, yb, *_)) in enumerate(zip(nodes[:-1], nodes[1:])):
        ln = xb - xa - 36
        sx, sy = stone_patch(int(ln / 1.5) + 2, 6)
        tex = crop_resize(st, sx, sy, sx + int(ln / 1.5), sy + 5, ln, 7)
        al, pts = scissor_alpha(ln, 7, 0.4, 0.4, 0.05)
        pcs.append(Piece(f"card-route-{i}", tex, al, pcs[0].x + xa + 18, pcs[0].y + ya - 3, 2.4, 1.5, "DOOR-C", "PRINT-1 DOOR-C ochre",
                         crop=[sx, sy, int(ln / 1.5), 5], outline=pts, curl=0.0))
    return table, pcs


# ================================================================== bake
BAKE = CUT + "/paper_stage_bake.pkl"
LOG = {"pieces": [], "prints": {}, "lamps": [LAMP_A.row(), LAMP_B.row(), MEM_LIGHT], "p02": {}}


def bake():
    global rng
    rng = np.random.default_rng(1978)
    LOG["pieces"].clear()
    back, pcs = build_facade()
    hole = np.zeros((SH, SW), np.float32); hole[OY0 + P:, OX0 + P:OX1 + P] = 1
    fac = {}
    for lamp in (LAMP_A, LAMP_B):
        hmap = np.where(hole > 0, -1.0, 0.0).astype(np.float32)
        rgb, fa = compose(back, pcs, lamp, LOG["pieces"], hmap)
        fa = np.maximum(fa, 1 - hole)
        # raised facade pieces' shadow onto the closed leaves (leaf level = card level 0)
        occ = np.clip((hmap > 0.5).astype(np.float32), 0, 1)
        dx, dy, blur = lamp.offset(OX1 + P, OY0 + P, 0, 5.0)
        ls = cv2.GaussianBlur(shift(occ, dx, dy), (0, 0), blur) * (1 - occ)
        fac[lamp.name] = dict(rgb=rgb, a=fa, hmap=hmap, leaf_shadow=ls)
    leaves = build_leaves()
    bm, tm = build_bench_masks()
    mem = memory_layers(bm)
    far3, pad3, lay3 = p03_layers(bm, tm, LOG["pieces"])
    # P03: everything static except the truck: bake per-plane rgb+alpha with lamp-A shadows
    p03 = dict(far=far3, pad=pad3)
    for nm in ("trunk", "bench", "litter"):
        pc = lay3[nm]
        z = np.zeros((SH, SW, 3), np.float32)
        rgb, a = compose(z, [pc], LAMP_A, LOG["pieces"])
        # its cast shadow lands on the plane behind: keep the shadow as a separate multiplier
        dx, dy, blur = LAMP_A.offset(pc.x + pc.a.shape[1] / 2, pc.y + pc.a.shape[0] / 2, 0, pc.z * 2.2)
        sh = np.zeros((SH, SW), np.float32)
        sh[pc.y:pc.y + pc.a.shape[0], pc.x:pc.x + pc.a.shape[1]] = pc.a[:SH - pc.y, :SW - pc.x]
        sh = cv2.GaussianBlur(shift(sh, dx, dy), (0, 0), blur) * LAMP_A.shadow
        p03[nm] = dict(rgb=rgb, a=a, sh=sh)
    p02 = p02_layers(LOG["pieces"])
    base2 = np.zeros((SH, SW, 3), np.float32)
    card2 = np.zeros((SH, SW, 3), np.float32); cm = np.zeros((SH, SW), np.float32)
    cm[:470 + P, :312 + P] = 1; cm[:470 + P, 578 + P:] = 1
    card2[:] = np.array([120, 106, 80], np.float32) / 255 * fibre(SH, SW, 0.6)
    c_rgb, c_a = compose(card2 * cm[..., None], p02["corners"], LAMP_A, LOG["pieces"])
    c_a = np.maximum(c_a, cm)
    k_rgb, k_a = compose(base2, [p02["kerb"]], LAMP_A, LOG["pieces"])
    # shadows of the corner pieces on the far plane / kerb on corners
    def plane_shadow(alpha, lamp, dz, cx, cy):
        dx, dy, blur = lamp.offset(cx, cy, 0, dz)
        return cv2.GaussianBlur(shift(alpha, dx, dy), (0, 0), blur) * lamp.shadow
    p02b = dict(far=p02["far"], c_rgb=c_rgb, c_a=c_a, c_sh=plane_shadow(c_a, LAMP_A, 14, SW / 2, SH / 3),
                k_rgb=k_rgb, k_a=k_a, k_sh=plane_shadow(k_a, LAMP_A, 6, SW / 2, SH * 0.8),
                source=p02["source"], how=p02["how"], far_crop=p02["far_crop"])
    LOG["p02"] = dict(source=p02["source"], how=p02["how"], far_crop=p02["far_crop"], kerb_crop=p02["kerb"].crop)
    table, cpcs = card_layers(LOG["pieces"])
    card_rgb, _ = compose(table, cpcs, LAMP_A, LOG["pieces"])
    LOG["prints"] = {k: dict(v, curve="out_c = target_c * (L/ref_L)**gamma over the whole photograph; ink Dmax limit") for k, v in PRINTS_SPEC.items()}
    LOG["prints"]["PRINT-5 BENCH cold"] = dict(src="BENCH", curve="blue-grey ramp lo(28,33,42)->hi(153,170,189) on L (memory print)")
    LOG["prints"]["PRINT-6 BENCH warm"] = dict(src="BENCH", curve="(rgb*(1.0,0.95,0.84))**1.1*0.88 (present print)")
    LOG["prints"]["PRINT-8 junction warm"] = dict(src=p02["source"], curve="tone(150,132,100)*0.78*((L/0.55)**1.1) + 0.22*rgb tint")
    B = dict(fac=fac, leaves=leaves, mem=mem, p03=p03, p02=p02b, card=card_rgb, log=LOG)
    pickle.dump(B, open(BAKE, "wb"), protocol=4)
    return B


_B = None


def B():
    global _B
    if _B is None:
        _B = pickle.load(open(BAKE, "rb")) if os.path.exists(BAKE) else bake()
    return _B


# ================================================================== motion (performance; paper on twos)
G_FALL = 3.9        # rad/s^2: the released flap falls back to the card (gravity torque ~ cos theta)
E_REST = 0.30       # restitution at contact


def fall(theta0_deg, t):
    """released flap: theta'' = -G cos(theta); bounce with restitution; returns degrees, contact time"""
    th, om, tt, dt = math.radians(theta0_deg), 0.0, 0.0, 1 / 960
    contact = None
    while tt < t:
        om -= G_FALL * math.cos(th) * dt
        th += om * dt
        if th <= 0:
            th = 0.0
            if contact is None:
                contact = tt
            om = -om * E_REST
            if om < 0.02:
                om = 0.0
        tt += dt
    return math.degrees(th), contact


def fall_time(theta0_deg):
    th, om, tt, dt = math.radians(theta0_deg), 0.0, 0.0, 1 / 960
    while th > 0:
        om -= G_FALL * math.cos(th) * dt; th += om * dt; tt += dt
    return tt


def spring_open(s, tmax, z=0.69, w=3.2):
    """lifted by a thread: under-damped approach (~3 deg overshoot), with inertia at the start"""
    if s <= 0:
        return 0.0
    s = max(0.0, s - 0.12 * (1 - math.exp(-s / 0.12)))
    wd = w * math.sqrt(1 - z * z)
    return tmax * (1 - math.exp(-z * w * s) * (math.cos(wd * s) + z / math.sqrt(1 - z * z) * math.sin(wd * s)))


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


SHOTS = {1: (0.0, 8.0), 2: (8.0, 19.0), 3: (19.0, 28.0), 4: (28.0, 44.0), 5: (44.0, 52.0), 6: (52.0, 57.0)}
SLATES = {1: "P01 · prise A · matin", 2: "P02 · carrefour", 3: "P03 · banc", 4: "P01 · prise B · soir",
          5: "P03 · retour · silence déclarée", 6: None}

# shot 1: left leaf lifted ~18 deg (5.5-6.1), held, released so it lands at 7.0 (thud)
S1_OPEN, S1_UP, S1_TH, S1_CONTACT = 5.5, 6.1, 18.0, 7.0
S1_REL = S1_CONTACT - fall_time(S1_TH)
# shot 4: open 31.0 (right 4 frames late), 58 / 64 deg; hold; lowered by hand from 41.0 and released
S4_OPEN, LAG, TH_L, TH_R = 31.0, 4 / 24, 58.0, 64.0
S4_LOWER_L, S4_LOWER_R, TH_REL = 41.0, 41.35, 24.0
S4_CONTACT_L, S4_CONTACT_R = 43.1, 43.5
S4_REL_L, S4_REL_R = S4_CONTACT_L - fall_time(TH_REL), S4_CONTACT_R - fall_time(TH_REL)


def q(t):
    return math.floor(t * 12 + 1e-6) / 12.0            # paper moves on twos (12 drawings / s)


def door_state(shot, t):
    tq = q(t)
    if shot == 1:
        if tq < S1_OPEN:
            tl = 0.0
        elif tq < S1_REL:
            tl = S1_TH * smooth((tq - S1_OPEN) / (S1_UP - S1_OPEN))
        else:
            tl = fall(S1_TH, tq - S1_REL)[0]
        return tl, 0.0, 0.0, 0.0
    # shot 4
    def leaf(t0, tmax, tlow, trel):
        if tq < t0:
            return 0.0
        if tq < tlow:
            return spring_open(tq - t0, tmax)
        if tq < trel:
            return tmax + (TH_REL - tmax) * smooth((tq - tlow) / (trel - tlow))
        return fall(TH_REL, tq - trel)[0]
    tl = leaf(S4_OPEN, TH_L, S4_LOWER_L, S4_REL_L)
    tr = leaf(S4_OPEN + LAG, TH_R, S4_LOWER_R, S4_REL_R)
    c = 6.0 * smooth((tq - S4_OPEN) / 3.2)
    settle = -2.0 * (1 - smooth((tq - S4_OPEN - 0.55) / 0.9))
    if tq < S4_OPEN + 0.55:
        settle = -2.0
    return tl, tr, c, settle + 2.0      # bench settles 2 px (from -2 to 0)


# ================================================================== frame assembly
EVENTS = []


def lens(img, focus_sigma=0.55, glare=0.035):
    """the camera over the table: plane focus (soft 16 mm-like acuity) and veiling glare (light
    scattered in the lens lifts the blacks). Physical optics, not a look filter."""
    if focus_sigma > 0:
        img = cv2.GaussianBlur(img, (0, 0), focus_sigma)
    return img + glare * cv2.GaussianBlur(img, (0, 0), 45)


def leaves_layer(tl, tr, cam, lamp, fac):
    """warp both leaves (2x supersampled) by their FK poses; card edge face; Z-buffer against the
    facade height map; lamp shadow of the lifted leaves on the facade. Returns rgb, alpha, shadow, poses"""
    S2 = (SW * 2, SH * 2)
    rgb = np.zeros((SH * 2, SW * 2, 3), np.float32); A = np.zeros((SH * 2, SW * 2), np.float32)
    Z = np.full((SH * 2, SW * 2), -9.0, np.float32)
    shadow = np.zeros((SH, SW), np.float32)
    poses = {}
    for i, (th, left) in enumerate([(tl, True), (tr, False)]):
        lf = B()["leaves"][i]
        proj, world = leaf_points(th, left, cam)
        w, h = lf["w"], lf["h"]
        u_far = w
        if left:
            src = [(0, 0), (w * 2, 0), (w * 2, h * 2), (0, h * 2)]
            dst = [proj(0, 0), proj(w, 0), proj(w, h), proj(0, h)]
        else:
            src = [(0, 0), (w * 2, 0), (w * 2, h * 2), (0, h * 2)]
            dst = [proj(w, 0), proj(0, 0), proj(0, h), proj(w, h)]
        M = cv2.getPerspectiveTransform(np.float32(src), np.float32(dst) * 2)
        t = cv2.warpPerspective(lf["tex"][lamp.name], M, S2, flags=cv2.INTER_LINEAR)
        a = cv2.warpPerspective(lf["a"], M, S2, flags=cv2.INTER_LINEAR)
        u = cv2.warpPerspective(lf["u"], M, S2, flags=cv2.INTER_LINEAR)
        n_front, n_edge = leaf_normal(th, left)
        Xc, Yc, Zc = world(w * 0.6, 300)
        sh0 = lambert(np.array([0, 0, 1.0]), lamp, Xc, Yc, 0)
        shade = min(1.0, 0.35 + 0.65 * lambert(n_front, lamp, Xc, Yc, Zc) / max(sh0, 1e-3))
        zl = u * math.sin(math.radians(th))
        # card edge face (free edge): front corner -> back corner (thickness CARD_T into the card)
        e_rgb = None
        if th > 0.8:
            quad = np.float32([proj(w, 0, 0), proj(w, 0, CARD_T), proj(w, h, CARD_T), proj(w, h, 0)]) * 2
            em = np.zeros((SH * 2, SW * 2), np.uint8)
            cv2.fillConvexPoly(em, np.int32(np.round(quad * 4)), 255, cv2.LINE_AA, shift=2)
            em = em.astype(np.float32) / 255
            le = 0.30 + 0.70 * lambert(n_edge, lamp, *world(w, 300))
            ec = CORE * le * lamp.warm
            e_rgb = (em, ec, w * math.sin(math.radians(th)))
        # Z-buffer: the leaf shows where it stands above the facade surface at that pixel
        fh = cv2.resize(fac["hmap"], S2, interpolation=cv2.INTER_NEAREST)
        vis = a * (zl + 0.5 >= fh)
        if th < 10:
            ls = cv2.resize(fac["leaf_shadow"], S2) * (1 - th / 10)
            t = t * (1 - lamp.shadow * ls)[..., None]
        sel = vis > Z * 0 + 1e-3
        rgb = rgb * (1 - vis[..., None]) + t * shade * vis[..., None]
        A = np.maximum(A, vis)
        Z = np.where(sel, np.maximum(Z, zl), Z)
        if e_rgb is not None:
            em, ec, ze = e_rgb
            ev = em * (ze + 0.5 >= fh)
            rgb = rgb * (1 - ev[..., None]) + ec * ev[..., None] * (0.92 + 0.16 * cv2.resize(_S_HI[:SH * 2, :SW * 2], S2)[..., None] - 0.08)
            A = np.maximum(A, ev)
        # lamp shadow of the lifted leaf on the card plane (Z = 0): project its corners along lamp rays
        if th > 0.8:
            pts = []
            for uu, vv in [(0, 0), (w, 0), (w, h), (0, h)]:
                X, Y, Zp = world(uu, vv)
                k = lamp.z / max(lamp.z - Zp, 1)
                Sx = (lamp.x - P) + (X - (lamp.x - P)) * k
                Sy = (lamp.y - P) + (Y - (lamp.y - P)) * k
                pts.append((Sx - cam + P, Sy + P))
            sm = np.zeros((SH * 4, SW * 4), np.uint8)
            cv2.fillConvexPoly(sm, np.int32(np.round(np.float32(pts) * 4)), 255, cv2.LINE_AA)
            sm = cv2.resize(sm, (SW, SH), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
            blur = 0.6 + (w * math.sin(math.radians(th))) * lamp.size * 0.5
            shadow = np.maximum(shadow, cv2.GaussianBlur(sm, (0, 0), blur))
        kx, ky = lf["knob"]
        ul = kx if left else (w - kx)
        knob_fk = [round(v - P, 3) for v in proj(ul, ky)]
        knob_h = [round(v / 2 - P, 3) for v in cv2.perspectiveTransform(np.float32([[[kx * 2, ky * 2]]]), M)[0, 0]]
        poses["L" if left else "R"] = dict(theta=round(th, 3), knob_fk=knob_fk, knob_tex=knob_h,
                                           hinge_top=[round(v - P, 3) for v in proj(0, 0)],
                                           hinge_bottom=[round(v - P, 3) for v in proj(0, h)],
                                           free_edge_top=[round(v - P, 2) for v in proj(w, 0)], shade=round(shade, 3),
                                           edge_px=round(CARD_T * math.sin(math.radians(th)), 2))
    rgb = cv2.resize(rgb, (SW, SH), interpolation=cv2.INTER_AREA)
    A = cv2.resize(A, (SW, SH), interpolation=cv2.INTER_AREA)
    return rgb, A, shadow, poses


def memory_frame(cam, settle):
    m = B()["mem"]
    mem = shift(m["bg"], -cam * 0.0, 0)                      # park, depth 1.0: parallax 0
    bx, by = m["bpos"][0] - cam * 0.4, m["bpos"][1] + settle  # bench, depth 0.6: parallax 0.4
    BA, BT = m["ba"], m["bt"]
    h, w = BA.shape
    X, Y = int(round(bx)), int(round(by))
    sh = np.zeros((SH, SW), np.float32); sh[Y:Y + h, X:X + w] = BA
    sh = shift(sh, bx - X + MEM_LIGHT["dx"], by - Y + MEM_LIGHT["dy"])
    mem = mem * (1 - MEM_LIGHT["strength"] * cv2.GaussianBlur(sh, (0, 0), MEM_LIGHT["blur"]))[..., None]
    bl = np.zeros((SH, SW), np.float32); bl[Y:Y + h, X:X + w] = BA
    bc = np.zeros((SH, SW, 3), np.float32); bc[Y:Y + h, X:X + w] = BT
    bl, bc = shift(bl, bx - X, by - Y), shift(bc, bx - X, by - Y)
    mem = mem * (1 - bl[..., None]) + bc * bl[..., None]
    ap = np.zeros((SH, SW), np.float32); ap[OY0 + P:, OX0 + P:OX1 + P] = 1
    ap = cv2.GaussianBlur(shift(ap, MEM_LIGHT["aperture_dx"], MEM_LIGHT["aperture_dy"]), (0, 0), 14)
    mem = mem * (0.42 + 0.58 * ap)[..., None]
    mem = mem * 0.86 + np.array([0.20, 0.22, 0.25], np.float32) * 0.14 * (0.5 + 0.5 * ap)[..., None]   # haze between planes
    return mem, dict(bench_x=round(bx - P, 2), bench_y=round(by - P, 2))


PASSAGE = None


def passage():
    """shot 1: what is under the door flap in the present: a dark passage card (black print on stock)"""
    global PASSAGE
    if PASSAGE is None:
        r = np.random.default_rng(3)
        g = np.linspace(0.06, 0.035, SH)[:, None, None]
        PASSAGE = (np.ones((SH, SW, 3), np.float32) * g * np.array([1.0, 0.93, 0.86], np.float32)
                   * cv2.resize(_S_AGE[:SH, :SW], (SW, SH)))
    return PASSAGE


def p01_frame(shot, t):
    lamp = LAMP_A if shot == 1 else LAMP_B
    fac = B()["fac"][lamp.name]
    tl, tr, cam, settle = door_state(shot, t)
    if shot == 4 and (tl > 0 or tr > 0):
        deep, mev = memory_frame(cam, settle)
    else:
        deep, mev = passage(), {}
    lr, la, lsh, poses = leaves_layer(tl, tr, cam, lamp, fac)
    fr, fa = shift(fac["rgb"], -cam, 0), shift(fac["a"], -cam, 0)
    fr = fr * (1 - lamp.shadow * 1.15 * lsh)[..., None]
    img = deep * (1 - fa[..., None]) + fr * fa[..., None]
    img = img * (1 - la[..., None]) + lr * la[..., None]
    img = lens(img)[P:P + H, P:P + W]
    ev = dict(t=round(t, 4), shot=shot, drawing_t=round(q(t), 4), lamp=lamp.name, theta_L=round(tl, 3), theta_R=round(tr, 3),
              truck_px=round(cam, 3), leaves=poses)
    if mev:
        ev.update(memory=mev, bench_settle=round(settle, 3))
    return img, ev


def p02_frame(t):
    b = B()["p02"]
    tq = q(t)
    g = 10.0 * smooth((tq - 8.3) / 4.2)                      # lateral glide 10 px
    near, mid, farr = g * 1.0, g * 0.5, g * 0.15
    far = b["far"]
    can = np.zeros((SH, SW, 3), np.float32) + np.array([0.40, 0.37, 0.32], np.float32)
    fh, fw = far.shape[:2]
    X = int(P + 445 - fw / 2 - farr); Y = P + 450 - fh
    xs0, xs1 = max(X, 0), min(X + fw, SW)
    ys0 = max(Y, 0)
    can[ys0:Y + fh, xs0:xs1] = far[ys0 - Y:, xs0 - X:xs1 - X]
    can = shift(can, -(farr - int(farr)), 0)
    can = can * (1 - shift(b["c_sh"], -mid, 0))[..., None]
    cr, ca = shift(b["c_rgb"], -mid, 0), shift(b["c_a"], -mid, 0)
    can = can * (1 - ca[..., None]) + cr * ca[..., None]
    can = can * (1 - shift(b["k_sh"], -near, 0))[..., None]
    kr, ka = shift(b["k_rgb"], -near, 0), shift(b["k_a"], -near, 0)
    can = can * (1 - ka[..., None]) + kr * ka[..., None]
    n_draw = 0 if tq < 13.0 else min(6, 1 + int((tq - 13.0) / (2.0 / 6)))
    strip = route_strip(n_draw, LAMP_A, -near)
    if strip is not None:
        dx, dy, blur = LAMP_A.offset(SW / 2, SH * 0.85, 0, 2.0)
        can = can * (1 - LAMP_A.shadow * cv2.GaussianBlur(shift(strip, dx, dy), (0, 0), blur))[..., None]
        sc = np.array([150, 112, 52], np.float32) / 255 * cv2.resize(fibre(SH // 2, SW // 2, 0.9, 0.5), (SW, SH))
        core = np.clip(strip - shift(strip, 1.0, 1.0), 0, 1)[..., None]       # lit cut core (lamp upper left)
        sc = sc * (1 - 0.5 * core) + STOCK_CREAM * 0.78 * 0.5 * core
        can = can * (1 - strip[..., None]) + sc * LAMP_A.E * strip[..., None]
    img = lens(can * LAMP_A.E)[P:P + H, P:P + W]
    return img, dict(t=round(t, 4), shot=2, drawing_t=round(tq, 4), glide_px=round(g, 3),
                     parallax=dict(near=round(near, 3), mid=round(mid, 3), far=round(farr, 3)), route_drawing=n_draw)


def p03_frame(t, shot):
    b = B()["p03"]
    tq = q(t)
    c = 8.0 if shot == 5 else 8.0 * smooth((tq - 19.4) / 4.6)      # slow 8 px truck, then hold; shot 5 = final state
    pad = b["pad"]
    far = b["far"]
    img = far[pad:pad + SH, int(pad + c * 0.0):int(pad + c * 0.0) + SW].copy()     # far 1.0: parallax 0
    for nm, ratio in [("trunk", 0.3), ("bench", 0.6), ("litter", 1.0)]:
        L = b[nm]
        img = img * (1 - shift(L["sh"], -c * ratio, 0))[..., None]
        r, a = shift(L["rgb"], -c * ratio, 0), shift(L["a"], -c * ratio, 0)
        img = img * (1 - a[..., None]) + r * a[..., None]
    img = lens(img * LAMP_A.E)[P:P + H, P:P + W]
    return img, dict(t=round(t, 4), shot=shot, drawing_t=round(tq, 4), truck_px=round(c, 3),
                     parallax=dict(litter=round(c, 3), bench=round(c * 0.6, 3), trunk=round(c * 0.3, 3), far=0.0),
                     audio=("digital silence" if shot == 5 else "park tone"))


def card_frame(t):
    img = lens(B()["card"])[P:P + H, P:P + W]
    return img, dict(t=round(t, 4), shot=6, audio="digital silence")


# ------------------------------------------------------------------ overlays
SERIF_I = "/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf"
MONO = ROOT + "/assets/fonts/ibm-plex-mono.woff2"
_f = {}


def fnt(k):
    if k not in _f:
        _f.update(cap=ImageFont.truetype(SERIF_I, 25), gl=ImageFont.truetype(SERIF_I, 15), mono=ImageFont.truetype(MONO, 13),
                  rec=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12))
    return _f[k]


CREAM, MUTED_L, MUTED_D = (236, 226, 200), (168, 156, 134), (96, 84, 64)
# review-only captions (U3's voice_score.json is authoritative for the film)
CAPTIONS = {
    1: [(1.0, 5.0, "« Le numéro sept. La porte était lourde ; je l'ai tirée seule. »", "Number seven. The door was heavy; I pulled it alone.", None)],
    2: [(9.5, 15.5, "« À l'angle, j'ai suivi la couture du trottoir, à gauche. Ou bien à droite. »", "At the corner I followed the seam in the pavement, left. Or right.", None)],
    3: [(20.5, 26.0, "« Ce banc, ou un autre. J'ai attendu longtemps ; qui, je ne sais plus. »", "This bench, or another. I waited a long time; for whom, I no longer know.", "lien P03 : INFÉRÉ")],
    4: [(28.4, 30.9, "« Plus tard, on m'a dit que j'avais neuf ans. »", "Later I was told I was nine.", "âge 8–10 · source : un tiers"),
        (36.0, 41.0, "« Le banc, c'était l'hiver, à peu près. »", "The bench: it was winter, roughly.",
         "souvenir · vers l'hiver (intervalle) · lien P01→P03 : INFÉRÉ")],
}


def overlay(im, shot, t, mode):
    if mode == "none":
        return im
    im = im.convert("RGBA")
    d = ImageDraw.Draw(im, "RGBA")
    sl = SLATES.get(shot)
    if sl:
        col = (70, 62, 48, 235) if shot in (3, 5) else MUTED_L + (230,)
        d.text((16, 12), sl, font=fnt("mono"), fill=col)
    if mode == "full":
        for a0, a1, fr_, en, rec in CAPTIONS.get(shot, []):
            al = min(1, max(0, (t - a0) / 0.35)) * min(1, max(0, (a1 - t) / 0.35))
            if al <= 0:
                continue
            lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
            x, y = 56, 664
            dl.text((x, y), fr_, font=fnt("cap"), fill=(12, 10, 10, int(190 * al)), anchor="ls")
            dl.text((x, y + 22), en, font=fnt("gl"), fill=(12, 10, 10, int(190 * al)), anchor="ls")
            im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(2.2)))
            d = ImageDraw.Draw(im, "RGBA")
            d.text((x, y), fr_, font=fnt("cap"), fill=CREAM + (int(255 * al),), anchor="ls")
            d.text((x, y + 22), en, font=fnt("gl"), fill=(200, 190, 168, int(235 * al)), anchor="ls")
            if rec:
                d.text((946, 706), rec, font=fnt("rec"), fill=(150, 140, 118, int(235 * al)), anchor="rs")
    return im.convert("RGB")


def render_shot(shot_id, t, overlay_mode="none", log=True):
    """shot_id 1..6; t = film time in seconds inside SHOTS[shot_id]. Returns PIL.Image 960x720."""
    a, b = SHOTS[shot_id]
    t = min(max(t, a), b - 1e-6)
    if shot_id in (1, 4):
        img, ev = p01_frame(shot_id, t)
    elif shot_id == 2:
        img, ev = p02_frame(t)
    elif shot_id in (3, 5):
        img, ev = p03_frame(t, shot_id)
    else:
        img, ev = card_frame(t)
    if log:
        EVENTS.append(ev)
    return overlay(Image.fromarray(to8(img)), shot_id, t, overlay_mode)


def shot_at(t):
    for k, (a, b) in SHOTS.items():
        if a <= t < b:
            return k
    return 6


def render(t, overlay_mode="none"):
    return render_shot(shot_at(t), t, overlay_mode)


# ================================================================== CLI tasks
def encode(frames_fn, n, path, fps=FPS):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", path]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(n):
        pr.stdin.write(np.asarray(frames_fn(k)).tobytes())
    pr.stdin.close(); pr.wait()


def task_test():
    a, b = SHOTS[4]
    n = int(round((b - a) * FPS))
    encode(lambda k: render_shot(4, a + k / FPS, "full"), n, OUT + "/test_shot.mp4")


STILL_T = {1: [3.0, 6.0], 2: [9.0, 14.0, 17.5], 3: [21.0, 26.0], 4: [29.0, 32.5, 38.5, 42.4], 5: [48.0], 6: [54.5]}


def task_stills():
    d = OUT + "/stills"; os.makedirs(d, exist_ok=True)
    for s, ts in STILL_T.items():
        for t in ts:
            render_shot(s, t, "slate").save(f"{d}/shot{s}_{t:05.2f}.jpg", quality=92)


def measure(a):
    a = np.asarray(a.convert("RGB")).astype(float); Hh, Ww = a.shape[:2]
    L = a @ [0.299, 0.587, 0.114]
    R = lambda x0, y0, x1, y1: a[int(y0 * Hh):int(y1 * Hh), int(x0 * Ww):int(x1 * Ww)]
    st = R(0.62, 0.28, 0.98, 0.80); door = R(0.16, 0.40, 0.50, 0.95); pl = R(0.62, 0.88, 0.98, 0.99)
    jb = R(0.565, 0.40, 0.605, 0.80); bal = R(0.10, 0.0, 0.55, 0.06)
    stL = st @ [0.299, 0.587, 0.114]
    rows = stL.mean(1)
    return dict(frame_mean=a.reshape(-1, 3).mean(0).round(1).tolist(), lum_p5=round(float(np.percentile(L, 5)), 1),
                lum_p50=round(float(np.median(L)), 1), lum_p95=round(float(np.percentile(L, 95)), 1),
                stone_mean=st.reshape(-1, 3).mean(0).round(1).tolist(), stone_sd=round(float(stL.std()), 1),
                stone_R_minus_B=round(float(st[..., 0].mean() - st[..., 2].mean()), 1),
                joint_row_min=round(float(rows.min()), 1), stone_row_median=round(float(np.median(rows)), 1),
                joint_darkness=round(float(np.median(rows) - rows.min()), 1),
                door_mean=door.reshape(-1, 3).mean(0).round(1).tolist(), door_lum=round(float((door @ [0.299, 0.587, 0.114]).mean()), 1),
                door_sd=round(float((door @ [0.299, 0.587, 0.114]).std()), 1),
                plinth_mean=pl.reshape(-1, 3).mean(0).round(1).tolist(), right_jamb_mean=jb.reshape(-1, 3).mean(0).round(1).tolist(),
                balcony_mean=bal.reshape(-1, 3).mean(0).round(1).tolist())


def task_compare():
    ref = Image.open(REF).convert("RGB")
    f1 = render_shot(1, 3.0, "none"); f4 = render_shot(4, 38.5, "none")
    hh = 480
    ims = [ref.resize((int(ref.width * hh / ref.height), hh)), f1.resize((640, 480)), f4.resize((640, 480))]
    sheet = Image.new("RGB", (sum(i.width for i in ims) + 20, hh + 28), (20, 18, 16))
    d = ImageDraw.Draw(sheet); x = 0
    for im, lab in zip(ims, ["REFERENCE fugue1.webp (INA still)", "shot 1  0:03  P01 prise A matin", "shot 4  0:38.5  P01 prise B, open"]):
        sheet.paste(im, (x, 28)); d.text((x + 6, 8), lab, fill=(200, 190, 170), font=fnt("rec")); x += im.width + 10
    sheet.save(OUT + "/compare_P01.jpg", quality=90)
    ref_m = dict(frame_mean=[89, 78, 57], lum_p5=19, lum_p50=89, lum_p95=149, stone_mean=[122, 104, 69], stone_sd=12,
                 jamb_mean=[127, 108, 72], door_mean=[21, 19, 21], door_sd=2, plinth_mean=[148, 137, 121], balcony_mean=[47, 39, 26],
                 joint_row_min=84, stone_row_median=98)
    out = dict(reference_plan_sec6=ref_m, reference_measured_same_regions=measure(ref), shot1_t3=measure(f1), shot4_t29_closed=measure(render_shot(4, 29.0)),
               shot4_t38_5_open=measure(f4),
               regions="stone x .62-.98 y .28-.80; door x .16-.50 y .40-.95; plinth x .62-.98 y .88-.99; right jamb x .565-.605; balcony y 0-.06")
    m = out["shot1_t3"]
    out["acceptance_5"] = dict(stone_within_18=bool(all(abs(a - b) <= 18 for a, b in zip(m["stone_mean"], (122, 104, 69)))),
                               stone_R_minus_B_ge_35=m["stone_R_minus_B"] >= 35, door_lum_le_35=m["door_lum"] <= 35,
                               p95_le_175=m["lum_p95"] <= 175, p5_ge_8=m["lum_p5"] >= 8, joint_le_30=m["joint_darkness"] <= 30)
    json.dump(out, open(OUT + "/compare_metrics.json", "w"), indent=1)
    return out


def task_tests():
    global EVENTS
    out = {}
    # I9 hinge / FK over the whole shot 4 and shot 1 (every frame)
    for shot in (4, 1):
        a, b = SHOTS[shot]
        evs = []
        for k in range(int((b - a) * FPS)):
            t = a + k / FPS
            tl, tr, cam, _ = door_state(shot, t)
            ev = dict(t=t, theta_L=tl, theta_R=tr, cam=cam, leaves={})
            for i, (th, left) in enumerate([(tl, True), (tr, False)]):
                proj, world = leaf_points(th, left, cam)
                lf = B()["leaves"][i]
                kx, ky = lf["knob"]
                ul = kx if left else (lf["w"] - kx)
                ev["leaves"]["L" if left else "R"] = dict(ht=proj(0, 0), hb=proj(0, lf["h"]), knob=proj(ul, ky))
            evs.append(ev)
        res = {}
        for s in "LR":
            hx = np.array([e["leaves"][s]["ht"][0] + e["cam"] for e in evs])
            hh = np.array([e["leaves"][s]["hb"][1] - e["leaves"][s]["ht"][1] for e in evs])
            th = np.array([e["theta_" + s] for e in evs])
            res[f"hinge_x_drift_{s}_px"] = round(float(hx.max() - hx.min()), 4)
            res[f"hinge_height_range_{s}_px"] = round(float(hh.max() - hh.min()), 4)
            res[f"theta_max_{s}_deg"] = round(float(th.max()), 2)
            res[f"distinct_leaf_drawings_{s}"] = int(len(set(np.round(th[th > 0], 3))))
        if shot == 4:
            TL = [e["theta_L"] for e in evs]; TR = [e["theta_R"] for e in evs]
            iL = next(i for i, v in enumerate(TL) if v > 0); iR = next(i for i, v in enumerate(TR) if v > 0)
            res["right_leaf_lag_frames"] = iR - iL
            cl = [evs[i]["t"] for i in range(1, len(evs)) if TL[i - 1] > 0 and TL[i] == 0 and evs[i]["t"] > S4_LOWER_L]
            cr = [evs[i]["t"] for i in range(1, len(evs)) if TR[i - 1] > 0 and TR[i] == 0 and evs[i]["t"] > S4_LOWER_R]
            res["contact_frames_s"] = dict(L=cl[:1], R=cr[:1], planned_thud=S4_CONTACT_R)
        else:
            c = [evs[i]["t"] for i in range(1, len(evs)) if evs[i - 1]["theta_L"] > 0 and evs[i]["theta_L"] == 0]
            res["contact_frames_s"] = dict(L=c[:1], planned_thud=S1_CONTACT)
        out[f"I9_shot{shot}"] = res
    # child (stud) never slides: FK-projected anchor vs where the texture's stud lands through the warp
    EVENTS_before = len(EVENTS)
    diffs = []
    for t in (32.0, 33.0, 38.5, 42.6):
        img, ev = p01_frame(4, t)
        for s in "LR":
            kf, kt = ev["leaves"][s]["knob_fk"], ev["leaves"][s]["knob_tex"]
            diffs.append(math.hypot(kf[0] - kt[0], kf[1] - kt[1]))
    out["I9_child_stud_slide_px_max"] = round(max(diffs), 4)
    out["I9_pass"] = bool(all(out[f"I9_shot{s}"][f"hinge_x_drift_{k}_px"] <= 0.5 and out[f"I9_shot{s}"][f"hinge_height_range_{k}_px"] < 1e-6
                              for s in (4, 1) for k in "LR") and out["I9_child_stud_slide_px_max"] <= 0.5)
    # I1: A vs B share the piece table and pose; stone-joint edge maps coincide
    fac = B()["fac"]
    pa = [r for r in B()["log"]["pieces"] if r["lamp"] == LAMP_A.name and not r["piece"].startswith(("p0", "card"))]
    pb = [r for r in B()["log"]["pieces"] if r["lamp"] == LAMP_B.name and not r["piece"].startswith(("p0", "card"))]
    same = [(x["piece"], x["stage_xy"], x["size"]) for x in pa] == [(x["piece"], x["stage_xy"], x["size"]) for x in pb]
    fa = render_shot(1, 2.0, log=False); fb = render_shot(4, 29.0, log=False)
    def edges(im):
        L = lum(np.asarray(im).astype(np.float32) / 255)
        hp = L - cv2.GaussianBlur(L, (0, 0), 3)
        e = cv2.Canny(to8(np.clip(0.5 + hp * 4, 0, 1)), 60, 140) > 0
        return e
    ea, eb = edges(fa), edges(fb)
    dtb = cv2.distanceTransform((~eb).astype(np.uint8), cv2.DIST_L2, 3)
    dta = cv2.distanceTransform((~ea).astype(np.uint8), cv2.DIST_L2, 3)
    roi = np.zeros_like(ea); roi[int(H * .2):int(H * .84), int(W * .6):] = True
    fa_ = float((dtb[ea & roi] <= 1.0).mean()); fb_ = float((dta[eb & roi] <= 1.0).mean())
    # geometric joint map (piece alpha, identical by construction) vs lamp-dependent shadow side
    out["I1"] = dict(piece_table_identical_A_B=same, n_pieces=len(pa), stone_edge_coincidence_within_1px_A_in_B=round(fa_, 3),
                     stone_edge_coincidence_within_1px_B_in_A=round(fb_, 3),
                     alpha_maps_identical=bool(np.array_equal(fac[LAMP_A.name]["a"], fac[LAMP_B.name]["a"])),
                     shadow_offset_example={r["piece"]: [r["lamp"], r["shadow_dx"], r["shadow_dy"]] for r in (pa[0], pb[0])},
                     p03_same_plate_shots_3_and_5=bool(np.array_equal(np.asarray(render_shot(3, 27.9, log=False)), np.asarray(render_shot(5, 48.0, log=False)))),
                     note="edge maps from a 3 px high-pass; the residue is the lamp-dependent shadow side of each 1-2 px gap")
    # I5
    f = np.asarray(render_shot(4, 38.5, log=False)).astype(float)
    mem = f[300:560, 290:400]; st = f[200:560, 640:940]
    out["I5"] = dict(memory_mean_rgb=mem.reshape(-1, 3).mean(0).round(1).tolist(), memory_B_ge_R=bool(mem[..., 2].mean() >= mem[..., 0].mean()),
                     stone_R_minus_B=round(float(st[..., 0].mean() - st[..., 2].mean()), 1),
                     memory_light=MEM_LIGHT["name"], stage_lamps=[LAMP_A.name, LAMP_B.name])
    out["I5"]["pass"] = out["I5"]["memory_B_ge_R"] and out["I5"]["stone_R_minus_B"] >= 35
    # I8
    src = open(__file__).read()
    out["I8"] = dict(imports_kit=("import kit" in src.replace('"import kit"', "")), kit_grain_or_vignette="not applied: no kit.Ink, no vignette, no noise generator used for texture",
                     random_noise_texture=False, textures_from=["DOOR-C", "DOOR-S", "BENCH", "STOCK", LOG.get("p02", {}).get("source", "JUNCTION-FB")],
                     shadows="lamp model only: offset = dz*(piece-lamp)/(lamp_z-z); blur = 0.6 + dz*lamp.size",
                     optics="plane focus sigma 0.55 px + veiling glare 3.5 % of a 45 px blur (lens scatter)")
    out["licence_recheck"] = json.load(open(SRC + "/paper-stage-fabricator/commons/commons_log.json")).get("verify") if os.path.exists(
        SRC + "/paper-stage-fabricator/commons/commons_log.json") else "pending"
    json.dump(out, open(OUT + "/stage_tests.json", "w"), indent=1, ensure_ascii=False)
    return out


def task_events():
    """full performance log at drawing rate (12/s) across the film, plus the planned cues"""
    global EVENTS
    EVENTS = []
    for k in range(int(57 * 12)):
        t = k / 12
        s = shot_at(t)
        if s in (1, 4):
            tl, tr, cam, settle = door_state(s, t)
            EVENTS.append(dict(t=round(t, 4), shot=s, theta_L=round(tl, 3), theta_R=round(tr, 3), truck_px=round(cam, 3),
                               bench_settle=round(settle, 3) if s == 4 else None))
        elif s == 2:
            tq = q(t); g = 10.0 * smooth((tq - 8.3) / 4.2)
            EVENTS.append(dict(t=round(t, 4), shot=2, glide_px=round(g, 3), route_drawing=0 if tq < 13 else min(6, 1 + int((tq - 13.0) / (2 / 6)))))
        elif s in (3, 5):
            tq = q(t)
            EVENTS.append(dict(t=round(t, 4), shot=s, truck_px=8.0 if s == 5 else round(8.0 * smooth((tq - 19.4) / 4.6), 3)))
        else:
            EVENTS.append(dict(t=round(t, 4), shot=6))
    cues = [dict(t=S1_OPEN, event="shot1 left leaf lifted (thread)"), dict(t=round(S1_REL, 3), event="shot1 left leaf released"),
            dict(t=S1_CONTACT, event="shot1 contact -> THUD"), dict(t=13.0, event="shot2 route strip laid, 6 drawings to 15.0"),
            dict(t=S4_OPEN, event="shot4 left leaf lifted"), dict(t=round(S4_OPEN + LAG, 4), event="shot4 right leaf lifted (4 frames late)"),
            dict(t=S4_LOWER_L, event="shot4 left leaf lowered by hand"), dict(t=round(S4_REL_L, 3), event="shot4 left leaf released"),
            dict(t=S4_CONTACT_L, event="shot4 left contact -> knock"), dict(t=round(S4_REL_R, 3), event="shot4 right leaf released"),
            dict(t=S4_CONTACT_R, event="shot4 right contact -> THUD"), dict(t=44.0, event="hard cut P03 return: digital silence to 57.0")]
    json.dump(dict(time_base="film seconds; paper drawings on twos (12/s); 24 fps", lamps=LOG["lamps"] if not _B else _B["log"]["lamps"],
                   cues=cues, drawings=EVENTS, pieces=B()["log"]["pieces"], prints=B()["log"]["prints"], p02=B()["log"]["p02"]),
              open(OUT + "/stage_events.json", "w"), indent=0, ensure_ascii=False)


if __name__ == "__main__":
    args = sys.argv[1:] or ["all"]
    if "bake" in args or "all" in args:
        bake(); _B = None
    if "test" in args or "all" in args:
        task_test()
    if "stills" in args or "all" in args:
        task_stills()
    if "compare" in args or "all" in args:
        print(json.dumps(task_compare()["shot1_t3"], indent=1))
    if "tests" in args or "all" in args:
        print(json.dumps(task_tests(), indent=1)[:3000])
    if "events" in args or "all" in args:
        task_events()
