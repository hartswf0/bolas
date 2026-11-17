"""le-maki-mococo · U2 paper-mouth puppet, pose library, decoder and kinetic type (rev U2-r2).

HANDMADE: an articulated cut-paper mouth in profile, facing right, on pure white.  Built in code from
original geometry (anatomical landmarks placed by eye; never traced from, nor pasted from, maki.webp).
Pure PIL + numpy.  Deterministic: every piece is generated from a fixed seed, so a library drawing has the
same bytes on every use (#38 "source artwork stays stable").

Paper (what each piece is "made of"):
  skin        layered tissue over a washi base sheet: domed by the glue (soft relief), under-sheets (cheek pad,
              philtrum column, nose ala, chin pad) show as soft ridges and a faint denser tint; long visible
              kozo fibres + cloudy formation; scissor-wobble edge with a lit cut edge.
  lips        glazed crepe paper: fine crepe striations across the lip, a soft specular sheen from the glaze
              where the domed lip faces the light (no sticker strip); two colourways A warm rose, B cool mauve.
  teeth       smooth cream card, scalloped tooth by tooth.
  cavity      deep red-brown card, lighter toward the front.
Rig (Reiniger pinned joints, #2 folded into #38):
  static   : cavity < upper teeth < neck < [JAW FRONT] < head (with ala + nostril) < upper lip (substitution)
  JAW BACK : tongue + lower teeth          } both rotate as forward kinematics about one off-screen
  JAW FRONT: jaw/chin skin + lower lip     } hinge HINGE, 0..10 deg (clamped)
Library (#38): <= 10 drawings per lip set: rest MBP A O EI UW FV LNT hm surprise.
Decoder (#38): Viterbi over 24 fps frames, pose changes only on even frames (12 fps on twos), minimum hold
  2 frames, transition costs penalising open<->closed jumps, protected key poses (O, surprise, MBP).
Speech/gesture (#47): visemes from measured phone spans; jaw scaled by the measured RMS envelope; silences are
  holds; breaths are explicit single events; silent gestures carry the readers' captions.

Public API (all images RGBA, 960x540):
  mouth_layer(t, viseme_track, lip_set)          -> PIL RGBA (transparent field)
  decode(targets, min_hold=2)                    -> pose id per 24 fps frame
  make_track(events, breaths, seconds)           -> Track (decoded once; pass it to mouth_layer)
  glyph_table()                                  -> fixed glyph boxes (exported for the invariant test)
  type_layer(t, syllable_onsets, glyph_table)    -> PIL RGBA
  underline_layer(t)                             -> PIL RGBA (red pencil under 'hangs', 52-54 s)
  film_events(timeline)                          -> speech + gesture events for the whole film (S0..S8)
  lip_set_at(t)                                  -> 'A' | 'B' (S4 swaps to B)
"""
import json
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OULIPO = HERE.parents[2]
SRC = OULIPO / "films" / "sources" / "le-maki-mococo" / "mouth"
W, H = 960, 540
S = 2                                    # work at 2x film resolution
CW, CH = W * S, H * S
FPS = 24
HINGE = (-250.0, 40.0)                   # temporo-mandibular pin, off-screen left (film px)
JAW_MAX = 10.0
LIGHT = np.array([-0.40, -0.58, 0.71])   # soft, frontal-left, from above (x right, y down, z to viewer)
LIGHT = LIGHT / np.linalg.norm(LIGHT)
HALF = LIGHT + np.array([0, 0, 1.0]); HALF = HALF / np.linalg.norm(HALF)

# ------------------------------------------------------------------ palette (targets from maki.webp) --
SKIN = (203, 155, 139)       # ~#CA9A8A
SKIN_SH = (168, 124, 110)    # ~#AC8071
SKIN_HI = (234, 199, 187)    # ~#E8C4B9
NECK = (196, 148, 132)
TEETH = (240, 233, 220)
TEETH_SH = (196, 184, 168)
CAVITY = (66, 26, 23)        # #421A17 (deepest, at the back only)
CAVITY_FRONT = (128, 58, 60)
TONGUE = (156, 76, 78)
NOSTRIL_C = (118, 66, 60)
SHADOW = (70, 38, 32)        # warm cast-shadow colour (paper on paper)

LIP_SETS = {
    # lower lip base, upper lip base (lighter, thinner), shade, highlight
    "A": dict(name="A warm rose", lower=(176, 96, 104), upper=(186, 122, 120), shade=(132, 78, 76), hi=(214, 152, 152)),
    "B": dict(name="B cool mauve", lower=(164, 92, 112), upper=(178, 120, 130), shade=(124, 76, 90), hi=(206, 150, 164)),
}

# ------------------------------------------------------------------ pose library (#38) ---------------
# jaw: FK hinge angle (deg).  ulift: upper-lip underside raised (shows teeth).  upro/lpro: protrusion.
# ldrop: lower-lip top border dropped (+, shows lower teeth) or pressed up (-).  corner: corner moves forward
# (+, rounding) or back (-, spreading).  thick: fullness.  tuck: F/V lower lip under the upper teeth.
POSES = {
    "rest":     dict(jaw=0.8, ulift=0,  upro=0,  lpro=0,   ldrop=-12, corner=0,   thick=1.00, tuck=0, tongue=0),
    "MBP":      dict(jaw=0.0, ulift=-4, upro=2,  lpro=3,   ldrop=-25, corner=4,   thick=0.94, tuck=0, tongue=0),
    "A":        dict(jaw=4.6, ulift=6,  upro=-2, lpro=-4,  ldrop=2,   corner=-4,  thick=0.94, tuck=0, tongue=0),
    "O":        dict(jaw=3.0, ulift=3,  upro=8,  lpro=9,   ldrop=-2,  corner=14,  thick=1.08, tuck=0, tongue=0),
    "EI":       dict(jaw=1.8, ulift=7,  upro=-3, lpro=-5,  ldrop=-4,  corner=-14, thick=0.90, tuck=0, tongue=0),
    "UW":       dict(jaw=1.4, ulift=1,  upro=12, lpro=12,  ldrop=-10, corner=20,  thick=1.06, tuck=0, tongue=0),
    "FV":       dict(jaw=0.9, ulift=5,  upro=0,  lpro=-14, ldrop=-20, corner=0,   thick=0.96, tuck=1, tongue=0),
    "LNT":      dict(jaw=2.0, ulift=5,  upro=0,  lpro=-2,  ldrop=-2,  corner=-6,  thick=0.96, tuck=0, tongue=1),
    "hm":       dict(jaw=0.0, ulift=-4, upro=6,  lpro=8,   ldrop=-25, corner=10,  thick=1.04, tuck=0, tongue=0),
    "surprise": dict(jaw=6.4, ulift=9,  upro=2,  lpro=-2,  ldrop=6,   corner=6,   thick=1.02, tuck=0, tongue=0),
}
POSE_IDS = list(POSES)
KEY_POSES = {"O", "surprise", "MBP"}     # protected from smoothing (MBP = the closures on b / p)
CLOSED = {"MBP", "hm"}
OPEN = {"A", "surprise"}
OPENNESS = {k: v["jaw"] + 0.15 * v["ulift"] + 0.1 * v["ldrop"] for k, v in POSES.items()}
SIM = {("EI", "LNT"): .5, ("LNT", "EI"): .5, ("A", "surprise"): .5, ("surprise", "A"): .5, ("O", "UW"): .45,
       ("UW", "O"): .45, ("rest", "MBP"): .45, ("MBP", "rest"): .3, ("hm", "rest"): .6, ("rest", "hm"): .6,
       ("MBP", "hm"): .6, ("hm", "MBP"): .7, ("A", "LNT"): .35, ("LNT", "A"): .35, ("EI", "A"): .3, ("A", "EI"): .3}


# ================================================================== numpy paper helpers ==============
def _box(a, r, axis):
    if r < 1:
        return a
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r + 1, r)
    p = np.pad(a, pad, mode="edge")
    c = np.cumsum(p, axis=axis, dtype=np.float64)
    n = a.shape[axis]
    hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
    lo = np.take(c, np.arange(0, n), axis=axis)
    return ((hi - lo) / (2 * r + 1)).astype(np.float32)


def blur(a, sigma):
    """Gaussian approximated by three box passes (pure numpy, deterministic)."""
    if sigma <= 0.3:
        return a.astype(np.float32)
    r = max(1, int(round((math.sqrt(12 * sigma * sigma / 3 + 1) - 1) / 2)))
    out = a.astype(np.float32)
    for _ in range(3):
        out = _box(_box(out, r, 0), r, 1)
    return out


def shift(a, dx, dy):
    out = np.zeros_like(a)
    dx, dy = int(round(dx)), int(round(dy))
    h, w = a.shape[:2]
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = a[ys, xs]
    return out


def catmull(pts, step=2.0):
    P = [np.array(p, float) for p in pts]
    n = len(P)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = P[(i - 1) % n], P[i], P[(i + 1) % n], P[(i + 2) % n]
        k = max(2, int(np.linalg.norm(p2 - p1) / step))
        for j in range(k):
            t = j / k
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return np.array(out)


def scissor(path, seed, amp=0.7, snip=6.0):
    """Scissor-wobble: low-frequency normal drift + straight facets every ~snip px (real snips)."""
    rs = np.random.RandomState(seed)
    d = np.diff(np.vstack([path, path[:1]]), axis=0)
    L = np.r_[0, np.cumsum(np.linalg.norm(d, axis=1))][:-1]
    tang = np.roll(path, -1, 0) - np.roll(path, 1, 0)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True) + 1e-9
    nrm = np.stack([tang[:, 1], -tang[:, 0]], 1)
    off = np.zeros(len(path))
    for lam, a in ((40, 1.0), (16, 0.5), (6.5, 0.22)):
        off += a * np.sin(L / lam + rs.uniform(0, 2 * np.pi))
    p = path + nrm * (off * amp)[:, None]
    keep, nxt = [], 0.0
    for i in range(len(p)):
        if i == 0 or L[i] >= nxt:
            keep.append(p[i])
            nxt = L[i] + snip * rs.uniform(0.6, 1.4)
    return np.array(keep)


def cut(pts, seed, amp=0.7):
    return scissor(catmull(pts), seed, amp)


def mask_of(poly):
    """Anti-aliased mask on the 2x canvas (polygon drawn at 4x of film, box-downsampled)."""
    k = 2
    m = Image.new("L", (CW * k, CH * k), 0)
    ImageDraw.Draw(m).polygon([(float(x) * S * k, float(y) * S * k) for x, y in poly], fill=255)
    m = m.resize((CW, CH), Image.BOX)
    return np.asarray(m, np.float32) / 255.0


@lru_cache(maxsize=None)
def fibre_field(seed):
    """Visible paper fibres: long, curling kozo strands (light and a few dark) over a cloudy formation.
    No per-pixel speckle.  ~N(0,1) field on the 2x canvas."""
    rs = np.random.RandomState(1000 + seed)
    img = Image.new("L", (CW, CH), 128)
    d = ImageDraw.Draw(img)
    for _ in range(int(CW * CH / 1400)):
        x, y = rs.uniform(-20, CW + 20), rs.uniform(-20, CH + 20)
        a = rs.uniform(0, np.pi)
        ln = rs.uniform(8, 34)
        bend = rs.uniform(-0.9, 0.9)
        dark = rs.rand() < 0.12
        c = int(128 + (-rs.uniform(6, 12) if dark else rs.uniform(8, 22)))
        pts = []
        for k in range(9):
            t = k / 8 - 0.5
            aa = a + bend * t
            pts.append((x + math.cos(aa) * ln * t, y + math.sin(aa) * ln * t))
        d.line(pts, fill=c, width=1)
    f = blur(np.asarray(img, np.float32) - 128, 0.9)
    f = f / (np.abs(f).max() + 1e-6)          # peak-normalised: a fibre is at most +1
    cloud = blur(rs.normal(0, 1, (CH // 4, CW // 4)).astype(np.float32), 5)
    cloud = np.asarray(Image.fromarray(cloud).resize((CW, CH), Image.BICUBIC), np.float32)
    cloud = cloud / (cloud.std() + 1e-6)
    return f.astype(np.float32), cloud.astype(np.float32)


def crepe_field(seed, angle_deg=95):
    """Glazed crepe paper: fine near-parallel striations (lip paper)."""
    rs = np.random.RandomState(2000 + seed)
    yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float32)
    a = math.radians(angle_deg)
    u = xx * math.cos(a) + yy * math.sin(a)
    wob = blur(rs.normal(0, 1, (CH // 8, CW // 8)).astype(np.float32), 2)
    wob = np.asarray(Image.fromarray(wob).resize((CW, CH), Image.BICUBIC), np.float32)
    s = np.sin(u / 1.7 + wob * 4.0) * (0.5 + 0.5 * np.sin(u / 23.0 + wob * 2.0)) + 0.4 * np.sin(u / 0.9 + wob * 6.0)
    return blur((s / 1.4).astype(np.float32), 0.7)


def normals(h, k):
    gy, gx = np.gradient(h)
    nx, ny, nz = -gx * k, -gy * k, np.ones_like(h)
    n = np.sqrt(nx * nx + ny * ny + nz * nz)
    return nx / n, ny / n, nz / n


def shade(height, k, base, sh, hi, strength=1.0):
    """Soft relief: lambert of the domed sheet relative to a flat sheet, mapped base->hi / base->shade."""
    nx, ny, nz = normals(height, k)
    lam = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]
    s = np.clip((lam - LIGHT[2]) / (1 - LIGHT[2]) * 1.6 * strength, -1, 1)
    base, sh, hi = (np.array(c, np.float32) for c in (base, sh, hi))
    rgb = np.where(s[..., None] > 0, base + (hi - base) * s[..., None], base + (base - sh) * s[..., None])
    return rgb, (nx, ny, nz)


def rim(rgb, a, strength=0.18):
    """Lit cut edge: thin bright band on edges facing the light, darker on the others."""
    sm = blur(a, 1.4 * S)
    ey, ex = np.gradient(sm)
    en = np.sqrt(ex * ex + ey * ey) + 1e-6
    band = np.clip(en * 2.6 * S, 0, 1) * (a > 0.02)
    lit = -(ex * LIGHT[0] + ey * LIGHT[1]) / en
    lit = lit / (np.hypot(LIGHT[0], LIGHT[1]))
    amt = band * lit * strength * 255
    return rgb + (amt * np.where(lit > 0, 0.6, 0.8))[..., None]


def to_rgba(rgb, a):
    out = np.dstack([np.clip(rgb, 0, 255), np.clip(a, 0, 1) * 255]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def shadow_img(a, dx=2.5, dy=3.5, sig=3.0, strength=0.25):
    sh = blur(shift(a, dx * S, dy * S), sig * S) * strength
    out = np.zeros((CH, CW, 4), np.uint8)
    out[..., :3] = SHADOW
    out[..., 3] = np.clip(sh * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


# ================================================================== geometry (film px, original) =====
# Built by eye from landmarks (subnasale, philtrum, vermilion, stomion, commissure, mentolabial sulcus,
# pogonion, menton).  Skin is kept left of x=432 (45%) and bleeds off the top, left and bottom edges.
HEAD = [(-60, -40), (412, -40), (415, -14), (406, 0), (392, 9), (374, 16), (382, 26), (396, 38), (404, 52),
        (360, 82), (290, 112), (210, 136), (150, 152), (160, 172), (146, 204), (122, 252), (84, 318), (44, 392), (-6, 456),
        (-60, 520)]
ALA = [(300, -40), (370, -40), (388, -22), (384, -6), (364, 6), (336, 8), (314, -4), (302, -22)]
NOSTRIL = [(378, -2), (398, -6), (408, 2), (400, 8), (386, 9), (376, 5)]
CHEEK_PAD = [(-60, -40), (250, -40), (300, 20), (250, 90), (160, 140), (100, 220), (40, 320), (-60, 380)]
PHILTRUM = [(352, 20), (386, 18), (398, 40), (396, 62), (356, 76), (338, 50)]
JAW = [(-460, 40), (60, 120), (150, 148), (270, 156), (380, 196), (404, 236), (392, 262), (388, 284),
       (396, 318), (406, 360), (404, 400), (390, 438), (360, 466), (318, 486), (268, 498), (240, 540),
       (232, 620), (-460, 620)]
CHIN_PAD = [(250, 290), (330, 276), (394, 300), (404, 360), (396, 420), (362, 456), (300, 470), (240, 440),
            (220, 370)]
LABIOMENTAL = [(300, 262), (360, 256), (392, 266), (386, 276), (354, 272), (304, 274)]
NECKP = [(-60, 360), (120, 420), (250, 452), (300, 470), (286, 520), (278, 620), (-60, 620)]
TEETH_UP = [(236, 112), (300, 94), (406, 90), (414, 104), (413, 130), (408, 150), (398, 154), (390, 148), (384, 153),
            (374, 152), (366, 145), (360, 149), (350, 147), (342, 140), (334, 142), (322, 139), (310, 133),
            (298, 132), (286, 128), (272, 134), (258, 130), (244, 134), (236, 128)]
TEETH_LO = [(300, 140), (318, 132), (330, 134), (342, 128), (356, 130), (368, 124), (380, 126), (392, 120),
            (400, 124), (404, 140), (398, 160), (300, 166)]
CAVITY_PTS = [(100, 150), (140, 150), (230, 130), (320, 104), (400, 96), (406, 122), (406, 160), (402, 200), (396, 236),
              (300, 232), (180, 214), (100, 200)]
TONGUE_PTS = [(150, 166), (250, 140), (320, 132), (360, 138), (372, 156), (330, 186), (240, 200), (150, 204)]
TONGUE_UP = [(170, 186), (280, 160), (350, 140), (394, 128), (402, 142), (370, 172), (300, 196), (180, 210)]


def upper_lip_poly(p):
    """Thin, light upper lip: vermilion border (top) to stomion (underside)."""
    c = 142 + p["corner"]; f = p["upro"]; lift = p["ulift"]; th = p["thick"]
    def full(x, y):           # fuller lips push the top border up toward the front
        return (x, y - (th - 1) * 26 * max(0.0, (x - c) / 280))
    top = [full(c, 152), full(c + 60, 134), full(250, 116), full(320, 90), full(372, 64), full(398, 50), (408, 44)]
    front = [(418 + f * 0.6, 48), (428 + f, 62), (431 + f, 78), (424 + f, 94 - lift * 0.5)]
    under = [(404 + f * 0.7, 102 - lift), (360, 108 - lift * 0.8), (290, 122 - lift * 0.5),
             (220, 138 - lift * 0.25), (c + 14, 154)]
    return top + front + under


def lower_lip_poly(p):
    """Full lower lip, in jaw space (unrotated).  Top border = stomion line."""
    c = 142 + p["corner"]; f = p["lpro"]; d = p["ldrop"]; th = p["thick"]
    if p["tuck"]:               # F/V: lower lip rolled in under the upper incisors
        return [(c + 10, 156), (250, 146), (330, 132 + d * 0.6), (386 + f, 120 + d), (402 + f, 132 + d),
                (404 + f, 170), (392 + f, 210), (356, 236), (296, 240), (226, 214), (c + 4, 172)]
    bot = 254 + (th - 1) * 50
    return [(c + 10, 156), (240, 146 + d * 0.3), (320, 136 + d * 0.6), (384 + f * 0.8, 128 + d),
            (408 + f, 140 + d * 0.9), (420 + f, 168 + d * 0.5), (418 + f, 202), (404 + f * 0.6, 232),
            (360, bot), (296, bot - 4), (232, 230), (186, 196), (c + 2, 168)]


# ================================================================== piece factory ====================
class Rig:
    """All pieces, rendered once, as 2x RGBA PIL images (+ their cast shadows)."""

    def __init__(self):
        fib, cloud = fibre_field(1)
        self.fib, self.cloud = fib, cloud
        # ---- head: base washi sheet + tissue under-sheets (cheek pad, philtrum column, nose ala)
        a_head = mask_of(cut(HEAD, 1))
        a_cheek = mask_of(cut(CHEEK_PAD, 2, 1.6)) * a_head
        a_phil = mask_of(cut(PHILTRUM, 3, 0.8)) * a_head
        a_ala = mask_of(cut(ALA, 4))
        a_nos = mask_of(cut(NOSTRIL, 5, 0.4))
        h = blur(a_head, 36 * S) + 0.14 * blur(a_cheek, 18 * S) + 0.08 * blur(a_phil, 10 * S) \
            + 0.16 * blur(a_ala, 10 * S)
        rgb, _ = shade(h, 300, SKIN, SKIN_SH, SKIN_HI, 0.62)
        rgb = self._skin_paper(rgb, a_head, [a_cheek, a_phil, a_ala])
        ala_edge = blur(a_ala, 1.5 * S) - blur(a_ala, 4 * S)          # crease where the ala sheet sits
        rgb *= (1 - 0.10 * np.clip(-ala_edge * 3, 0, 1))[..., None]
        rgb = rim(rgb, a_ala, 0.10)
        rgb = rgb * (1 - a_nos[..., None]) + np.array(NOSTRIL_C, np.float32) * a_nos[..., None]
        rgb = rim(rgb, a_head, 0.16)
        self.a_head = a_head
        self.head = to_rgba(rgb, a_head)
        self.head_sh = shadow_img(a_head, 2.0, 3.0, 2.6, 0.22)
        # ---- jaw/chin skin (FK group, front plane) with chin pad + labiomental crease tissue
        a_jaw = mask_of(cut(JAW, 6))
        a_chin = mask_of(cut(CHIN_PAD, 7, 1.4)) * a_jaw
        a_lm = mask_of(cut(LABIOMENTAL, 8, 0.6)) * a_jaw
        h = blur(a_jaw, 38 * S) + 0.18 * blur(a_chin, 22 * S) - 0.16 * blur(a_lm, 6 * S)
        rgb, _ = shade(h, 300, SKIN, SKIN_SH, SKIN_HI, 0.62)
        yy = np.linspace(0, 1, CH, dtype=np.float32)[:, None]
        rgb *= (1 - 0.08 * np.clip((yy - 0.80) * 5, 0, 1))[..., None]          # under-chin turning away
        rgb = self._skin_paper(rgb, a_jaw, [a_chin])
        rgb = rim(rgb, a_jaw, 0.16)
        self.a_jaw = a_jaw
        self.jaw_rgb = rgb
        # ---- neck (static, behind the jaw)
        a_neck = mask_of(cut(NECKP, 9))
        rgb, _ = shade(blur(a_neck, 30 * S), 300, NECK, SKIN_SH, SKIN_HI, 0.8)
        rgb = self._skin_paper(rgb, a_neck, []) * 0.97
        self.a_neck = a_neck
        self.neck = to_rgba(rim(rgb, a_neck, 0.12), a_neck)
        # ---- teeth (smooth card, scalloped)
        a_tu = mask_of(cut(TEETH_UP, 10, 0.3))
        rgb, _ = shade(blur(a_tu, 6 * S), 160, TEETH, TEETH_SH, (252, 249, 242))
        xg = np.arange(CW, dtype=np.float32)[None, :] / S
        rgb *= (1 - 0.30 * np.clip((320 - xg) / 90, 0, 1))[..., None]          # back teeth recede into shade
        for x0 in (284, 310, 334, 360, 384):                    # tooth divisions: little gaps where the snips met
            xs = int(x0 * S)
            rgb[:, xs - 1:xs + 2] *= np.where(a_tu[:, xs - 1:xs + 2, None] > 0, 0.84, 1.0)
        yy = np.arange(CH, dtype=np.float32)[:, None] / S
        rgb *= (1 - 0.10 * np.clip((yy - 136) / 14, 0, 1))[..., None]           # incisal edge in shade
        self.teeth_up = to_rgba(rim(rgb, a_tu, 0.22), a_tu)
        self.teeth_up_sh = shadow_img(a_tu, 1.2, 2.0, 1.5, 0.35)
        a_tl = mask_of(cut(TEETH_LO, 11, 0.3))
        rgb, _ = shade(blur(a_tl, 6 * S), 160, (226, 216, 200), TEETH_SH, (246, 240, 230))
        self.teeth_lo = to_rgba(rim(rgb, a_tl, 0.18), a_tl)
        # ---- cavity (deep at the back, lighter at the front)
        a_cav = mask_of(cut(CAVITY_PTS, 12, 0.3))
        xx = np.arange(CW, dtype=np.float32)[None, :] / S
        g = np.clip((xx - 170) / 230, 0, 1)[..., None] ** 0.8
        rgb = np.array(CAVITY, np.float32) * (1 - g) + np.array(CAVITY_FRONT, np.float32) * g
        rgb = np.broadcast_to(rgb, (CH, CW, 3)).copy()
        self.cavity = to_rgba(rgb, a_cav)
        # ---- tongue hint (two drawings: down, tip up for L/N/T)
        self.tongue = {}
        for k, pts in ((0, TONGUE_PTS), (1, TONGUE_UP)):
            a = mask_of(cut(pts, 13 + k, 0.5))
            rgb, _ = shade(blur(a, 10 * S), 240, TONGUE, (110, 50, 52), (186, 104, 104))
            self.tongue[k] = to_rgba(rim(rgb, a, 0.10), a)
        self.lips = {}

    def _skin_paper(self, rgb, a, unders):
        """Visible fibres + cloudy formation; under-sheets add a faint denser, rosier tint."""
        over = sum(unders) if unders else 0
        tint = np.array([0.990, 0.972, 0.975], np.float32)
        if unders:
            rgb = rgb * (1 - (1 - tint) * np.clip(over, 0, 2)[..., None])
        rgb = rgb * (1 + 0.10 * self.fib[..., None] + 0.016 * self.cloud[..., None])
        return rgb

    def lip(self, pose, lip_set):
        key = (pose, lip_set)
        if key in self.lips:
            return self.lips[key]
        p = POSES[pose]
        ls = LIP_SETS[lip_set]
        seed = 100 + 10 * POSE_IDS.index(pose) + (0 if lip_set == "A" else 5)
        crepe = crepe_field(seed % 7)
        out = {}
        for part, poly, base in (("up", upper_lip_poly(p), ls["upper"]), ("lo", lower_lip_poly(p), ls["lower"])):
            a = mask_of(cut(poly, seed + (0 if part == "up" else 1), 0.55))
            dome = blur(a, (13 if part == "up" else 22) * S)
            rgb, (nx, ny, nz) = shade(dome, 420 if part == "up" else 520, base, ls["shade"], ls["hi"],
                                      0.9 if part == "up" else 0.45)
            if part == "up":       # light vermilion border roll along the top edge
                border = np.clip(blur(a, 1.5 * S) - blur(a, 5 * S), 0, 1)
                yy = np.arange(CH, dtype=np.float32)[:, None] / S
                rgb = rgb + (border * 70 * (yy < 100))[..., None] * np.array([0.9, 0.75, 0.7], np.float32)
            rgb = rgb * (1 + 0.018 * crepe[..., None])
            # glaze: soft specular sheen where the domed lip faces the half-vector (no sticker strip)
            spec = np.clip(nx * HALF[0] + ny * HALF[1] + nz * HALF[2], 0, 1) ** (14 if part == "lo" else 30)
            spec = spec * (0.75 if part == "lo" else 0.30) * np.clip(0.75 + 0.35 * crepe, 0, 1.2)
            spec = blur(spec, 1.2 * S)
            if part == "lo":      # glazed-paper glints: a few soft reflections along the lit upper-front roll
                rs = np.random.RandomState(seed)
                gl = np.zeros((CH, CW), np.float32)
                for k in range(5):
                    gx = (300 + 22 * k + rs.uniform(-6, 6) + p["lpro"] * 0.6) * S
                    gy = (172 + 3 * k + p["ldrop"] * 0.5 + rs.uniform(-4, 4)) * S
                    rr = rs.uniform(5, 9) * S
                    yy0, xx0 = int(max(0, gy - 3 * rr)), int(max(0, gx - 3 * rr))
                    sub = np.mgrid[yy0:int(gy + 3 * rr), xx0:int(gx + 3 * rr)].astype(np.float32)
                    v = np.exp(-(((sub[1] - gx) / (rr * 1.8)) ** 2 + ((sub[0] - gy) / rr) ** 2))
                    gl[yy0:yy0 + v.shape[0], xx0:xx0 + v.shape[1]] += v * rs.uniform(0.45, 0.75)
                spec = np.clip(spec + gl * a, 0, 1)
            rgb = rgb + spec[..., None] * (np.array([250, 228, 228], np.float32) - rgb) * 0.85
            rgb = rim(rgb, a, 0.18)
            out[part] = to_rgba(rgb, a)
            out[part + "_a"] = a
        out["up_sh"] = shadow_img(out["up_a"], 1.5, 3.0, 2.4, 0.30)
        out["lo_sh"] = shadow_img(out["lo_a"], 1.5, 3.0, 2.4, 0.22)
        self.lips[key] = out
        return out

    # ---------------------------------------------------------------- one frame (2x canvas) ----------
    def render2x(self, pose, lip_set, jaw_deg):
        p = POSES[pose]
        jaw_deg = float(np.clip(jaw_deg, 0.0, JAW_MAX))
        L = self.lip(pose, lip_set)
        img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        img.alpha_composite(self.cavity)
        back = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        back.alpha_composite(self.tongue[p["tongue"]])
        back.alpha_composite(self.teeth_lo)
        img.alpha_composite(self._rot(back, jaw_deg))
        img.alpha_composite(self.teeth_up_sh)
        img.alpha_composite(self.teeth_up)
        img.alpha_composite(self.neck)
        front = self._jaw_front(pose, lip_set)
        frot = self._rot(front, jaw_deg)
        img.alpha_composite(self._rot(self._jaw_front_sh(pose, lip_set), jaw_deg))
        img.alpha_composite(frot)
        img.alpha_composite(self.head_sh)
        img.alpha_composite(self.head)
        img.alpha_composite(L["up_sh"])
        img.alpha_composite(L["up"])
        return img

    @staticmethod
    def _rot(im, deg):
        if abs(deg) < 1e-3:
            return im
        # PIL rotates counter-clockwise for positive angles; jaw opening = clockwise on screen
        return im.rotate(-deg, resample=Image.BICUBIC, center=(HINGE[0] * S, HINGE[1] * S))

    @lru_cache(maxsize=None)
    def _jaw_front(self, pose, lip_set):
        L = self.lip(pose, lip_set)
        a_lo = L["lo_a"]
        grp = self.jaw_rgb.copy()
        sh = blur(shift(a_lo, 1.5 * S, 3.0 * S), 2.4 * S) * 0.22 * self.a_jaw          # lip on chin skin
        grp *= (1 - sh[..., None])
        lo = np.asarray(L["lo"], np.float32)
        al = lo[..., 3:4] / 255
        grp = lo[..., :3] * al + grp * (1 - al)
        return to_rgba(grp, np.maximum(self.a_jaw, a_lo))

    @lru_cache(maxsize=None)
    def _jaw_front_sh(self, pose, lip_set):
        a = np.maximum(self.a_jaw, self.lip(pose, lip_set)["lo_a"])
        return shadow_img(a, 2.0, 3.0, 2.6, 0.20)


_RIG = None


def rig():
    global _RIG
    if _RIG is None:
        _RIG = Rig()
    return _RIG


@lru_cache(maxsize=512)
def mouth_image(pose, lip_set, jaw_q):
    """Film-resolution RGBA of one (pose, lip set, jaw angle in 0.25 deg steps)."""
    return rig().render2x(pose, lip_set, jaw_q * 0.25).resize((W, H), Image.LANCZOS)


# ================================================================== decoder (#38) ====================
def transition_cost(a, b):
    if a == b:
        return 0.0
    c = 0.15 + 0.10 * abs(OPENNESS[a] - OPENNESS[b])
    if (a in OPEN and b in CLOSED) or (a in CLOSED and b in OPEN):
        c += 0.6                                   # A <-> closed in a single step looks like a flap
    return c


def match_cost(want, pid, weight=1.0):
    if want is None:
        want = "rest"
    c = 0.0 if pid == want else 1.0 - SIM.get((want, pid), 0.0)
    if want in KEY_POSES and pid != want:
        c *= 3.0                                   # protected key poses are never averaged away
    return c * weight


def decode(targets, min_hold=2, on_twos=True):
    """#38 Viterbi decoder over 24 fps frames.
    targets: list (one per 24 fps frame) of either a pose id, None (rest), or a dict pose->match cost.
    Constraints: a pose may change only on even frames (12 fps on twos) and only after it has been held
    >= min_hold frames.  Returns list of pose ids (len == len(targets))."""
    ids = POSE_IDS
    n = len(ids)
    TC = np.array([[transition_cost(a, b) for b in ids] for a in ids])

    def costs(tg):
        if isinstance(tg, dict):
            return np.array([tg.get(k, 3.0) for k in ids])
        return np.array([match_cost(tg, k) for k in ids])

    D = min_hold                                    # duration state d in 1..D (D = held >= min_hold)
    INF = 1e12
    cost = np.full((n, D), INF)
    cost[:, 0] = costs(targets[0])
    back = []
    for t in range(1, len(targets)):
        c = costs(targets[t])
        new = np.full((n, D), INF)
        bp = np.zeros((n, D, 2), int)
        # stay: d -> min(d+1, D)
        for d in range(D):
            nd = min(d + 1, D - 1)
            better = cost[:, d] < new[:, nd]
            new[better, nd] = cost[better, d]
            bp[better, nd] = np.stack([np.arange(n)[better], np.full(better.sum(), d)], 1)
        # switch (only from a held state, only on an even frame)
        if (not on_twos) or t % 2 == 0:
            src = cost[:, D - 1][:, None] + TC          # (from, to)
            np.fill_diagonal(src, INF)
            fi = src.argmin(0)
            fv = src[fi, np.arange(n)]
            better = fv < new[:, 0]
            new[better, 0] = fv[better]
            bp[better, 0] = np.stack([fi[better], np.full(better.sum(), D - 1)], 1)
        cost = new + c[:, None]
        back.append(bp)
    i, d = np.unravel_index(np.argmin(cost), cost.shape)
    path = [(i, d)]
    for bp in reversed(back):
        i, d = bp[i, d]
        path.append((i, d))
    return [ids[i] for i, _ in reversed(path)]


def flicker_count(path):
    """Runs shorter than 2 frames (should be 0)."""
    runs, k = [], 0
    for i in range(1, len(path) + 1):
        if i == len(path) or path[i] != path[k]:
            runs.append(i - k); k = i
    return sum(1 for r in runs[1:-1] if r < 2)


# ================================================================== tracks (#47) =====================
class Track:
    """Viseme events -> decoded per-frame poses + jaw angles.
    events: list of dict(t0, t1, pose, kind='speech'|'gesture', jaw=None|float, env=None|(list@100Hz, t_env0),
            ease=None|seconds).  breaths: list of (t_center, seconds, deg)."""

    def __init__(self, events, breaths=(), seconds=None, lead=1 / 24):
        self.events = sorted(events, key=lambda e: e["t0"])
        self.breaths = list(breaths)
        self.lead = lead
        end = max([e["t1"] for e in self.events] + [b[0] + b[1] for b in self.breaths] + [0.5])
        self.seconds = seconds or end + 0.5
        self.n = int(math.ceil(self.seconds * FPS)) + 1
        self.targets = [self.event_at(k / FPS + lead) for k in range(self.n)]
        self.path = decode([e["pose"] if e else None for e in self.targets])

    def event_at(self, t):
        hit = None
        for e in self.events:
            if e["t0"] <= t < e["t1"]:
                hit = e
        return hit

    def frame(self, t):
        """Quantised to twos: returns (pose, jaw_deg) for film time t."""
        k = int(round(t * FPS))
        k -= k % 2
        k = max(0, min(self.n - 1, k))
        pose = self.path[k]
        tt = k / FPS + self.lead
        e = self.targets[k]
        base = POSES[pose]["jaw"]
        jaw = base
        if e is not None and e.get("kind") == "speech" and e.get("env") is not None:
            envl, t_env0 = e["env"]
            i = int((tt - t_env0) * 100)
            v = envl[i] if 0 <= i < len(envl) else 0.0
            jaw = base * (0.72 + 0.45 * v)
        elif e is not None and e.get("jaw") is not None:
            jaw = e["jaw"]
        if e is not None and e.get("ease"):
            x = min(1.0, max(0.0, (tt - e["t0"]) / e["ease"]))
            x = x * x * (3 - 2 * x)
            j0 = e.get("jaw_from", POSES["rest"]["jaw"])
            jaw = j0 + (jaw - j0) * x
        for tc, dur, deg in self.breaths:
            if abs(tt - tc) < dur / 2:
                jaw += deg * 0.5 * (1 + math.cos(2 * math.pi * (tt - tc) / dur))
        return pose, jaw

    def ledger(self, t0=None, t1=None):
        out = []
        for k in range(self.n):
            t = k / FPS
            if (t0 is not None and t < t0) or (t1 is not None and t > t1):
                continue
            if k % 2:
                continue
            pose, jaw = self.frame(t)
            e = self.targets[k]
            out.append(dict(frame=k, t=round(t, 4), target=(e["pose"] if e else "rest"), pose=pose,
                            jaw_deg=round(jaw, 2)))
        return out


def make_track(events, breaths=(), seconds=None):
    return Track(events, breaths, seconds)


def mouth_layer(t, viseme_track, lip_set="A"):
    """RGBA 960x540 of the paper mouth at film time t (12 fps on twos; transparent field)."""
    pose, jaw = viseme_track.frame(t)
    return mouth_image(pose, lip_set if isinstance(lip_set, str) else lip_set(t), int(round(jaw / 0.25)))


def lip_set_at(t):
    """S4 (23.5-31.0): replacement swap to set B (Reader B's guess); otherwise set A."""
    return "B" if 23.5 <= t < 31.0 else "A"


# ================================================================== poem, syllables, glyph table =====
POEM = ["In the dark it hangs and swings,", "binturong, binturong,", "smells of popcorn, never rings —",
        "binturong, binturong."]
# Typeset rows inside the column x 455-735, y 120-330 (Caladea 30 px; poem lines broken as verse).
ROWS = [(0, 0, 20, 0), (0, 20, 32, 1), (1, 0, 21, 0), (2, 0, 18, 0), (2, 18, 32, 1), (3, 0, 21, 0)]
#        (poem line, char start, char end, indent level)
COL_X, COL_Y, LEAD, BASE0, INDENT = 455, 120, 36, 146, 26
INK = (42, 36, 34)            # #2a2422
ROSE = (196, 112, 120)
PENCIL = (182, 38, 42)
CAL = "/usr/share/fonts/truetype/crosextra/Caladea-Regular.ttf"
F_POEM = ImageFont.truetype(CAL, 30 * S)
SYLLABLES = {   # word -> syllables (letters); seg ids L{line}.w{word}.s{syl}
    "binturong": ["bin", "tu", "rong"], "popcorn": ["pop", "corn"], "never": ["ne", "ver"]}
VISEME_OF = {   # syllable -> (onset, nucleus, coda) viseme classes (for provisional/estimated tracks)
    "in": ("EI", "EI", "LNT"), "the": ("LNT", "A", "A"), "dark": ("LNT", "A", "LNT"), "it": ("EI", "EI", "LNT"),
    "hangs": ("A", "A", "EI"), "and": ("A", "A", "LNT"), "swings": ("UW", "EI", "EI"),
    "bin": ("MBP", "EI", "LNT"), "tu": ("LNT", "UW", "UW"), "rong": ("UW", "A", "O"),
    "smells": ("EI", "EI", "LNT"), "of": ("O", "A", "FV"), "pop": ("MBP", "O", "MBP"), "corn": ("O", "O", "LNT"),
    "ne": ("LNT", "EI", "EI"), "ver": ("FV", "A", "A"), "rings": ("UW", "EI", "EI")}


def syllable_index():
    """seg_id -> dict(line, chars=[char indices], text).  Punctuation attaches to the preceding syllable."""
    out = {}
    for li, line in enumerate(POEM):
        wi = 0
        i = 0
        last = None
        while i < len(line):
            if line[i].isalpha():
                j = i
                while j < len(line) and line[j].isalpha():
                    j += 1
                word = line[i:j]
                wi += 1
                syls = SYLLABLES.get(word.lower(), [word])
                k = i
                for si, s in enumerate(syls):
                    sid = f"L{li + 1}.w{wi}.s{si + 1}"
                    out[sid] = dict(line=li, chars=list(range(k, k + len(s))), text=s.lower(), word=word.lower())
                    k += len(s)
                    last = sid
                i = j
            else:
                if line[i] not in " " and last is not None:
                    out[last]["chars"].append(i)
                i += 1
    return out


SYL = syllable_index()


def glyph_table():
    """Fixed glyph boxes (film px).  A pure function of the frozen poem string, font and rows: it cannot reflow."""
    tab = []
    for r, (li, a, b, ind) in enumerate(ROWS):
        line = POEM[li]
        seg = line[a:b].lstrip(" ")
        off = len(line[a:b]) - len(seg)
        base = BASE0 + r * LEAD
        x0 = COL_X + ind * INDENT
        for ci, ch in enumerate(seg):
            idx = a + off + ci
            if ch == " ":
                continue
            x = x0 + F_POEM.getlength(seg[:ci]) / S
            w = F_POEM.getlength(ch) / S
            sid = next((k for k, v in SYL.items() if v["line"] == li and idx in v["chars"]), None)
            bb = F_POEM.getbbox(ch, anchor="ls")
            tab.append(dict(line=li, i=idx, ch=ch, seg_id=sid, row=r, x=round(x, 3), base=base, w=round(w, 3),
                            box=[round(x + bb[0] / S, 2), round(base + bb[1] / S, 2), round(x + bb[2] / S, 2),
                                 round(base + bb[3] / S, 2)]))
    xs = [g["box"][2] for g in tab]
    assert max(xs) <= 735 and min(g["x"] for g in tab) >= 455, "type left the column"
    assert min(g["box"][1] for g in tab) >= 120 and max(g["box"][3] for g in tab) <= 336
    return tab


GLYPHS = glyph_table()


def word_box(line, word):
    i = POEM[line].index(word)
    g = [g for g in GLYPHS if g["line"] == line and i <= g["i"] < i + len(word)]
    return (min(x["box"][0] for x in g), min(x["box"][1] for x in g), max(x["box"][2] for x in g),
            max(x["box"][3] for x in g))


HANGS_BOX = word_box(0, "hangs")
LAND = 3 / FPS          # a letter lands in 3 frames (drop 3 px, ink up); its box is fixed from then on


def type_layer(t, syllable_onsets, glyph_table=GLYPHS, ink=1.0, darken=None, cursor=True):
    """Kinetic typesetting.  syllable_onsets: seg_id -> onset (film s) or (onset, offset).
    Letters of a syllable start landing at its measured onset, spread over the syllable (<= 0.18 s);
    a rose cursor follows the newest letter and fades 0.6 s after the last.  darken: seg_id/word -> 0..1 extra."""
    lay = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    newest, newest_t = None, -1
    for g in glyph_table:
        on = syllable_onsets.get(g["seg_id"]) if g["seg_id"] else None
        if on is None:
            continue
        t0, t1 = (on if isinstance(on, (tuple, list)) else (on, on + 0.18))
        idx = SYL[g["seg_id"]]["chars"]
        k = idx.index(g["i"])
        tk = t0 + min(0.18, max(0.06, t1 - t0)) * k / max(1, len(idx))
        if t < tk:
            continue
        x = min(1.0, (t - tk) / LAND)
        x = x * x * (3 - 2 * x)
        dy = -3.0 * (1 - x)
        a = (0.30 + 0.70 * x) * ink
        col = INK
        if darken:
            dv = darken.get(g["seg_id"], darken.get(SYL[g["seg_id"]]["word"], 0.0))
            if dv:
                col = tuple(int(c * (1 - 0.55 * dv)) for c in INK)
        d.text((g["x"] * S, (g["base"] + dy) * S), g["ch"], font=F_POEM, fill=col + (int(255 * a),), anchor="ls")
        if tk > newest_t:
            newest, newest_t = g, tk
    if cursor and newest is not None and t - newest_t < 0.6 + LAND:
        fade = 1.0 if t - newest_t < 0.35 else max(0.0, 1 - (t - newest_t - 0.35) / 0.25 / (1 + LAND))
        x = (newest["box"][2] + 2.5) * S
        d.rectangle([x, (newest["base"] - 24) * S, x + 2.5 * S, (newest["base"] + 6) * S],
                    fill=ROSE + (int(235 * fade),))
    return lay.resize((W, H), Image.LANCZOS)


@lru_cache(maxsize=1)
def _pencil_stroke():
    x0, _, x1, yb = HANGS_BOX
    rs = np.random.RandomState(52)
    strokes = []
    for k, (n, lift, press0) in enumerate(((240, 0.0, 1.0), (180, 1.6, 0.7))):
        u = np.linspace(0, 1, n)
        if k == 0:
            xs = x0 - 4 + (x1 - x0 + 9) * u
        else:      # the return stroke, shorter, from right to left (stroke by stroke)
            xs = x1 + 2 - (x1 - x0 - 2) * u
        ys = yb + 4.0 + lift - 1.4 * np.sin(u * np.pi) + 0.6 * u + np.cumsum(rs.normal(0, 0.05, n))
        press = press0 * (0.5 + 0.5 * np.sin(np.clip(u * 1.1, 0, 1) * np.pi) ** 0.5)
        strokes.append((xs, ys, press))
    return strokes


def underline_layer(t, t0=52.0, t1=54.0):
    """Red pencil drawn straight-ahead under 'hangs': stroke 1 (52.0-52.9 s), return stroke (53.1-53.8 s).
    Wax skips on the paper tooth (fibre field)."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t < t0:
        return lay
    sc = (t1 - t0) / 2.0
    spans = ((t0, t0 + 0.9 * sc), (t0 + 1.1 * sc, t0 + 1.8 * sc))
    L = Image.new("L", (CW, CH), 0)
    d = ImageDraw.Draw(L)
    for (xs, ys, press), (a, b) in zip(_pencil_stroke(), spans):
        x = min(1.0, max(0.0, (t - a) / (b - a)))
        x = x * x * (3 - 2 * x)
        k = int(len(xs) * x)
        for i in range(k):
            r = (1.3 + 0.7 * press[i]) * S
            d.ellipse([xs[i] * S - r, ys[i] * S - r * 0.75, xs[i] * S + r, ys[i] * S + r * 0.75],
                      fill=int(225 * press[i] + 20))
    a = np.asarray(L, np.float32) / 255.0
    fib, _ = fibre_field(1)
    a = a * np.clip(0.80 + 0.30 * fib, 0, 1)
    out = np.zeros((CH, CW, 4), np.uint8)
    out[..., :3] = PENCIL
    out[..., 3] = np.clip(a * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA").resize((W, H), Image.LANCZOS)


# ================================================================== whole-film events (#47) ==========
def speech_events(syllables, env=None):
    """syllables: list of dict(seg_id, t0, t1, phones=[(t0,t1,viseme)] optional).  Returns speech events."""
    ev = []
    for s in syllables:
        if s.get("phones"):
            for a, b, v in s["phones"]:
                ev.append(dict(t0=a, t1=b, pose=v, kind="speech", env=env))
        else:
            vis = VISEME_OF.get(SYL[s["seg_id"]]["text"], ("EI", "A", "LNT"))
            a, b = s["t0"], s["t1"]
            dur = b - a
            cuts = [a, a + 0.25 * dur, a + 0.72 * dur, b]
            for k, v in enumerate(vis):
                ev.append(dict(t0=cuts[k], t1=cuts[k + 1], pose=v, kind="speech", env=env))
    return ev


def gesture_events():
    """Silent acting for the captions (plan §6).  Holds carry thought; nothing flaps."""
    return [
        dict(t0=10.0, t1=10.9, pose="hm", kind="gesture"),                     # S2 Reader A thinks: pursed 'hm'
        dict(t0=10.9, t1=12.4, pose="LNT", kind="gesture", jaw=1.6),           # ... opens slightly ('a gong?')
        dict(t0=23.5, t1=31.0, pose="rest", kind="gesture", jaw=2.8, ease=0.8, jaw_from=0.8),  # S4 thinking drop
        dict(t0=38.3, t1=44.0, pose="surprise", kind="gesture", ease=1.1, jaw_from=0.8),        # S6 slow surprise
        dict(t0=44.0, t1=45.2, pose="O", kind="gesture"),                      # S7 'Oh -'
        dict(t0=45.2, t1=45.8, pose="hm", kind="gesture"),                     # ... closes
    ]


BREATHS = [(0.9, 1.4, 1.0), (34.5, 3.2, 1.2)]          # S0 one breath, S5 one slow breath (declared)


def load_timeline(path=HERE / "cue_timeline.json"):
    """U1's cue_timeline.json if present (status 'measured'), else provisional onsets (status 'provisional')."""
    if path.exists():
        try:
            return json.load(open(path)), "cue_timeline.json"
        except Exception:
            pass
    p = SRC / "provisional_onsets.json"
    return json.load(open(p)), "provisional"


def _u1_syllables(tl, section):
    """Tolerant reader for U1's schema: audio.syllables (or audio.sections[section]) with seg_id/onset/offset."""
    a = tl.get("audio", {})
    cand = None
    for key in ("syllables_" + section, section):
        if isinstance(a.get(key), list):
            cand = a[key]
    if cand is None and isinstance(a.get("sections"), dict):
        cand = a["sections"].get(section)
    if cand is None and isinstance(a.get("syllables"), list):
        cand = [s for s in a["syllables"] if s.get("section", section) == section]
    if not cand:
        return None
    out = []
    for s in cand:
        t0 = s.get("onset", s.get("t0", s.get("film_t0")))
        t1 = s.get("offset", s.get("t1", s.get("film_t1")))
        if s.get("seg_id") in SYL and t0 is not None and t1 is not None:
            out.append(dict(seg_id=s["seg_id"], t0=float(t0), t1=float(t1)))
    return out or None


def film_events(timeline=None):
    """Speech for S1 (2.0), S3 (15.5), S8 (52.x) + gestures.  Returns (events, onsets_by_section, status)."""
    if timeline is None:
        timeline, status = load_timeline()
    else:
        status = timeline.get("status", "given")
    ev, onsets = [], {}
    if "sections" in timeline and status == "provisional" or timeline.get("status") == "provisional":
        for name, sec in timeline["sections"].items():
            env = (sec["env"], sec["t_env0"]) if sec.get("env") else None
            ev += speech_events(sec["syllables"], env)
            onsets[name] = {s["seg_id"]: (s["t0"], s["t1"]) for s in sec["syllables"]}
    else:
        for name in ("S1", "S3", "S8"):
            syl = _u1_syllables(timeline, name)
            if syl:
                ev += speech_events(syl)
                onsets[name] = {s["seg_id"]: (s["t0"], s["t1"]) for s in syl}
    ev += gesture_events()
    return ev, onsets, status
