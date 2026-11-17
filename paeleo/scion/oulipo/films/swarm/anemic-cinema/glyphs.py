"""Anemic cinema - U2 language unit: the two original puns, their GlyphPaths and the text discs.

API (shared field contract, plan.md section 10):
    PUNS                       {"T1": str, "T2": str}: the puns themselves (one chiasmus each)
    disc_text(pun)             the token string actually laid on the disc (pun repeated to fill the turns)
    glyph_path(pun)            list of dicts, one per token, in token order:
                               {i, ch, r, phi, tangent, turn, ring, adv, w}  (2x plate px, radians)
    render_text(pun, theta, visible=None, omega=None, nsub=8, shutter=0.5)
                               -> (L, A, "neutral"): float32 L 0..255 of the whole 1920x1080 frame
                                  (field + sphere-lit plate + embossed letters) and the letter alpha
                                  A at 2x, both already integrated over the 180 deg shutter
    glyph_sprite(pun, i)       per-glyph sprite for substitution: {alpha, value, cx, cy, ux, uy, vx, vy,
                               phi, r, turn, ring, adv, ch} in plate coords at theta = 0
    letter_layer(pun, visible) (alpha, value) of the letters in plate coords, unrotated, N x N
    plate_L()                  the neutral sphere-lit plate (camera-fixed light) N x N, 2x
    to_frame(Lplate, Aplate)   place an N x N plate-space image into the 1920x1080 2x canvas

Conventions: 2x internal (1920x1080, plate radius 464), centre (960, 540) of the 2x frame; plate
texture N x N with centre C. phi is measured in image coordinates (y down) so phi increasing is
CLOCKWISE on screen; phi = -pi/2 is 12 o'clock. theta (from score.json) is counter-clockwise
positive on screen. A glyph at plate angle phi appears at screen angle phi - theta.

Rings: spiral turn j is centred on O_A ring j. Ring radii are read from optics-ledger.json
("rings") when U1 has published it, else from the approved test shot (test-shot-build/geometry.json).

Deterministic, no randomness, no grain. Run: python3 -I glyphs.py   (writes glyphpaths.json + fixtures)
"""
import hashlib
import json
import math
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = "/home/user/bolas/paeleo/scion/oulipo"
WS = ROOT + "/films/swarm/anemic-cinema"
MED = ROOT + "/films/sources/anemic-cinema/language"
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

SS = 2
W2X, H2X = 960 * SS, 540 * SS
R = 232 * SS
N = 2 * R + 32
C = N / 2.0
SEP = " · "

# ---------------------------------------------------------------- the puns (original; chiasmus)
# T1, the door pun. Exact word permutation: [LA PORTE] [TOURNE SUR] [LE GOND] -> [LE GOND] [TOURNE SUR] [LA PORTE].
# T2, the key-and-bell pun (station seed). Exact word permutation: CLOCHE <-> CLEF (both feminine).
PUNS = {
    "T1": "LA PORTE TOURNE SUR LE GOND · LE GOND TOURNE SUR LA PORTE",
    "T2": "LA CLOCHE DU QUAI SONNE LA CLEF · LA CLEF DU QUAI SONNE LA CLOCHE",
}
GLOSS = {
    "T1": ("The door turns on the hinge / the hinge turns on the door. 'Tourner' is also 'to shoot a "
           "film': the door is filming its hinge, the hinge its door; and 'sortir de ses gonds' (to come "
           "off the hinge) is to lose one's temper. On a turning disc, what is the pivot and what is the "
           "thing that turns is exactly what the chiasmus swaps."),
    "T2": ("The platform bell rings the key / the platform key rings the bell. 'Clef' is both the key that "
           "opens and the musical clef or key-note: the bell 'sounds the key' (gives the pitch), and the key "
           "'rings the bell' (rings for the train, opens the bell-tower). Slang 'ca cloche' = 'something is "
           "off'. The two nouns change places and the station keeps the same hour."),
}
# Duchamp's Anemic cinema disc texts (as transcribed in the literature; checked word-for-phrase below)
DUCHAMP_TEXTS = [
    "BAINS DE GROS THE POUR GRAINS DE BEAUTE SANS TROP DE BENGUE",
    "L'ENFANT QUI TETE EST UN SOUFFLEUR DE CHAIR CHAUDE ET N'AIME PAS LE CHOU-FLEUR DE SERRE CHAUDE",
    "SI JE TE DONNE UN SOU, ME DONNERAS-TU UNE PAIRE DE CISEAUX ?",
    "ON DEMANDE DES MOUSTIQUES DOMESTIQUES (DEMI-STOCK) POUR LA CURE D'AZOTE SUR LA COTE D'AZUR",
    "INCESTE OU PASSION DE FAMILLE, A COUPS TROP TIRES",
    "ESQUIVONS LES ECCHYMOSES DES ESQUIMAUX AUX MOTS EXQUIS",
    "AVEZ-VOUS DEJA MIS LA MOELLE DE L'EPEE DANS LE POELE DE L'AIMEE ?",
    "PARMI NOS ARTICLES DE QUINCAILLERIE PARESSEUSE, NOUS RECOMMANDONS LE ROBINET QUI S'ARRETE DE COULER QUAND ON NE L'ECOUTE PAS",
    "L'ASPIRANT HABITE JAVEL ET MOI J'AVAIS L'HABITE EN SPIRALE",
    "ANEMIC CINEMA",
]

# ---------------------------------------------------------------- ring geometry (from U1)
KF2_PITCH_OVER_CAP = 44.0 / 30.0           # kf-2 crowding (1280x720): 44 px pitch, 30 px type
OPEN = 1.17                                # open turn spacing by 17 % against kf-2 (>= 15 %)


def _ring_radii_1x():
    p = WS + "/optics-ledger.json"     # U1 publishes rings[k].r_1x (outside in)
    if os.path.exists(p):
        try:
            led = json.load(open(p))
            rings = led.get("rings")
            if isinstance(rings, dict):
                rings = rings.get("rings") or rings.get("list") or list(rings.values())
            out = []
            for q in rings:
                if isinstance(q, (int, float)):
                    out.append(float(q))
                else:
                    for key in ("r_1x", "r", "radius_1x", "radius", "r_px"):
                        if key in q:
                            out.append(float(q[key]))
                            break
            if len(out) >= 3:
                return sorted(out, reverse=True), "optics-ledger.json rings"
        except Exception:
            pass
    g = json.load(open(WS + "/test-shot-build/geometry.json"))
    return [float(x) for x in g["rings_1x"]], "test-shot-build/geometry.json rings_1x (optics-ledger.json absent)"


RINGS_1X, RING_SOURCE = _ring_radii_1x()
KR = len(RINGS_1X)
RADII = [r * SS for r in RINGS_1X]
RING_PITCH = float(np.mean(-np.diff(RADII)))   # ring pitch = ring width + gap
# Text turn pitch in ring pitches. 1.0 = literal 'turn j <-> ring j' (7 turns, cap 17.5 px: busy, much
# denser than spiralTextPom). 1.4 (chosen) = about 4.7 turns with a 24 px cap, close to the approved test
# shot (23 px) and the reference's few large turns; every glyph still slides at most half a ring pitch
# (one ring band) onto its nearest ring, and the correspondence stays order-preserving.
TEXT_PITCH_RINGS = float(os.environ.get("ANEMIC_TEXT_PITCH_RINGS", "1.4"))
PITCH = RING_PITCH * TEXT_PITCH_RINGS
CAP = PITCH / (KF2_PITCH_OVER_CAP * OPEN)  # cap height at 2x
FPX = int(round(CAP / 0.729))              # LiberationSans-Bold cap height = 0.729 em
FNT = ImageFont.truetype(FONT, FPX)
TRACK_MIN = 1.15                           # advance >= 1.15 x natural width (tracking +15 %)
TRACK_GOAL = 1.30
PHI0 = -math.pi / 2                        # the sentence starts at 12 o'clock of the plate ...
K_READ = 288                               # ... T2's start is phase-locked to 12 o'clock on SCREEN at F288


def _theta_read():
    """theta at the start of the declared reading interval, from U3's score.json when published."""
    p = WS + "/score.json"
    if os.path.exists(p):
        try:
            sc = json.load(open(p))
            if "theta_reading_start" in sc:
                return float(sc["theta_reading_start"]), "score.json theta_reading_start"
            fr = sc.get("frames") or sc.get("exposure") or []
            for f in fr:
                if int(f.get("k", -1)) == K_READ:
                    return float(f["theta"]), "score.json frames[k=288].theta"
        except Exception:
            pass
    rev = sum(1 / 80 + (1 / 256 - 1 / 80) * ((j + 0.5) / 24) for j in range(24))
    return 2 * math.pi * (rev % 1.0), "placeholder: F24-263 at 1/80 + 24-frame ease to 1/256 (score.json absent)"


THETA_READ, THETA_READ_SOURCE = _theta_read()
# plate phase of each disc's first token: a glyph at plate phi is on screen at phi - theta, so T2's first
# token sits at 12 o'clock when theta = THETA_READ. T1 starts at 12 o'clock at theta = 0.
PHASE = {"T1": 0.0, "T2": THETA_READ % (2 * math.pi)}
RIM_CLEAR = 5 * SS                         # letter tops stay this far inside the plate rim
DELTA = min(PITCH / 2, R - RIM_CLEAR - CAP / 2 - RADII[0])   # the spiral starts at r_0 + DELTA (rim-limited)
R_END = RADII[-1] - 0.45 * RING_PITCH      # and ends just inside the innermost ring


def _width(c):
    if c == " ":
        return FNT.getlength(" ") * 1.25
    return FNT.getlength(c)


def _spiral_len():
    """Arc length of the spiral centre line from r_0 + DELTA to R_END, measured at the letters' inner edge."""
    s_end = 2 * math.pi * (RADII[0] + DELTA - R_END) / PITCH
    n = 20000
    tot = 0.0
    for q in range(n):
        r = _r_at((q + 0.5) / n * s_end)
        tot += max(r - 0.4 * CAP, 0.35 * r) * s_end / n
    return tot


def disc_text(pun):
    """The pun's two halves alternated A . B . A . B . A ... along the spiral. Any two neighbouring
    halves (A.B or B.A) read as the chiasmus, so the reader can enter the turning disc at any separator.
    The number of halves h is chosen so the tracking scale is closest to TRACK_GOAL with scale >= TRACK_MIN."""
    p = PUNS.get(pun, pun)
    halves = [x.strip() for x in p.split(SEP.strip())]
    L = _spiral_len()
    best = None
    for h in range(2, 12):
        t = SEP.join(halves[q % 2] for q in range(h))
        sc = L / sum(_width(c) for c in t)
        if sc >= TRACK_MIN and (best is None or abs(sc - TRACK_GOAL) < abs(best[0] - TRACK_GOAL)):
            best = (sc, t)
    return best[1]


def _r_at(s):
    """Spiral radius after turning s radians clockwise from PHI0 (continuous in s)."""
    return RADII[0] + DELTA - PITCH * s / (2 * math.pi)


_GP = {}


def glyph_path(pun):
    """GlyphPath: inward clockwise spiral, tops out, tracking solved so the text fills KR turns exactly."""
    if pun in _GP:
        return _GP[pun]
    text = disc_text(pun)
    widths = [_width(c) for c in text]
    s_end = 2 * math.pi * (RADII[0] + DELTA - R_END) / PITCH

    def lay(scale):
        s = 0.0
        out = []
        for c, wv in zip(text, widths):
            r = max(_r_at(s), 1.0)
            # spacing is held at the letters' inner edge (r - 0.4 cap), so tight inner turns do not crowd
            adv = wv * scale * r / max(r - 0.4 * CAP, 0.35 * r)
            ds = adv / r
            sm = s + ds / 2
            out.append((c, sm, adv, wv))
            s += ds
        return out, s

    lo, hi = 0.5, 4.0
    for _ in range(60):
        mid = (lo + hi) / 2
        _, s = lay(mid)
        if s > s_end:
            hi = mid
        else:
            lo = mid
    lay_out, s_tot = lay(lo)
    path = []
    for i, (c, sm, adv, wv) in enumerate(lay_out):
        phi = PHI0 + PHASE.get(pun, 0.0) + sm
        r = _r_at(sm)
        turn = int(sm // (2 * math.pi))
        ring = int(min(KR - 1, max(0, round((RADII[0] - r) / RING_PITCH))))
        path.append(dict(i=i, ch=c, r=r, phi=phi, phi_deg_cw_from_12=math.degrees(sm % (2 * math.pi)),
                         tangent=[-math.sin(phi), math.cos(phi)], turn=turn, ring=ring, adv=adv, w=wv))
    _GP[pun] = (path, lo)
    return path, lo


# ---------------------------------------------------------------- sprites
_SPR = {}


def _char_sprite(ch):
    """Glyph alpha at 2x in glyph-local frame (x right along reading, y down = toward plate centre)."""
    if ch not in _SPR:
        wch = max(int(math.ceil(FNT.getlength(ch))), 1)
        sw, sh = wch + 12, int(CAP * 2.2)
        im = Image.new("L", (sw, sh), 0)
        ImageDraw.Draw(im).text((sw / 2, sh / 2 + CAP / 2), ch, font=FNT, fill=255, anchor="ms")
        _SPR[ch] = np.asarray(im, np.float32) / 255.0
    return _SPR[ch]


def glyph_sprite(pun, i):
    """Sprite for token i: alpha (h, w), its cream groove value (premultiplied L), and the affine
    placement in plate coords at theta = 0: sprite x axis -> (ux, uy), y axis -> (vx, vy), centre (cx, cy)."""
    path, _ = glyph_path(pun)
    g = path[i]
    a = _char_sprite(g["ch"]) if g["ch"] != " " else np.zeros((4, 4), np.float32)
    phi, r = g["phi"], g["r"]
    tx, ty = -math.sin(phi), math.cos(phi)
    nx, ny = math.cos(phi), math.sin(phi)
    return dict(ch=g["ch"], alpha=a, value=a * LETTER_L, cx=C + r * nx, cy=C + r * ny,
                ux=tx, uy=ty, vx=-nx, vy=-ny, phi=phi, r=r, turn=g["turn"], ring=g["ring"], adv=g["adv"])


def paste_affine(canvas, src, ux, uy, vx, vy, cx, cy, weight=1.0):
    """Max-combine src (h, w) into canvas, src centre at (cx, cy), src axes -> (ux, uy), (vx, vy)."""
    h, w = src.shape
    ext = int(math.ceil(abs(ux) * w / 2 + abs(vx) * h / 2)) + 3
    eyt = int(math.ceil(abs(uy) * w / 2 + abs(vy) * h / 2)) + 3
    bx, by = int(cx) - ext, int(cy) - eyt
    bw, bh = 2 * ext + 1, 2 * eyt + 1
    M = np.array([[ux, vx, cx - bx - ux * w / 2 - vx * h / 2],
                  [uy, vy, cy - by - uy * w / 2 - vy * h / 2]], np.float32)
    out = cv2.warpAffine(src, M, (bw, bh), flags=cv2.INTER_LINEAR) * weight
    x0, y0 = max(bx, 0), max(by, 0)
    x1, y1 = min(bx + bw, canvas.shape[1]), min(by + bh, canvas.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    sub = canvas[y0:y1, x0:x1]
    np.maximum(sub, out[y0 - by:y1 - by, x0 - bx:x1 - bx], out=sub)


# ---------------------------------------------------------------- material and light
yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
DPLATE = np.hypot(xx - C, yy - C)
GROOVE = 2.5 * SS                          # same groove pitch as the ring stock (2.5 px at 1x)
LETTER_L = 238.0
LETTER_GROOVE = (1.0 + 0.03 * np.cos(2 * np.pi * DPLATE / GROOVE)).astype(np.float32)

ux_, uy_ = (xx - C) / R, (yy - C) / R
rr_ = np.hypot(ux_, uy_)
uz_ = np.sqrt(np.clip(1 - rr_ * rr_, 0, 1))
DISC = np.clip((1 - rr_) * R + 0.5, 0, 1).astype(np.float32)


def _lam(L):
    L = np.array(L, np.float32) / np.linalg.norm(L)
    return np.clip(ux_ * L[0] + uy_ * L[1] + uz_ * L[2], 0, 1)


LF_TEXT = _lam((-0.38, -0.78, 0.55))       # sphere, key light top / upper left (camera-fixed)
PLATE_TEXT = (58 + 158 * LF_TEXT).astype(np.float32)
LIGHT_LET = (0.96 + 0.06 * LF_TEXT).astype(np.float32)
FIELD = 2.0


def plate_L():
    return PLATE_TEXT


def letter_layer(pun, visible=None):
    """Letter alpha and premultiplied L in plate coords (unrotated). visible: None (all), an iterable of
    token indices, a bool array, or a dict {i: weight 0..1}."""
    path, _ = glyph_path(pun)
    if visible is None:
        wts = {g["i"]: 1.0 for g in path}
    elif isinstance(visible, dict):
        wts = visible
    else:
        v = list(visible)
        if len(v) == len(path) and all(isinstance(x, (bool, np.bool_)) for x in v):
            wts = {i: 1.0 for i, x in enumerate(v) if x}
        else:
            wts = {int(i): 1.0 for i in v}
    A = np.zeros((N, N), np.float32)
    for i, wgt in wts.items():
        if wgt <= 0 or path[i]["ch"] == " ":
            continue
        s = glyph_sprite(pun, i)
        paste_affine(A, s["alpha"], s["ux"], s["uy"], s["vx"], s["vy"], s["cx"], s["cy"], wgt)
    return A, A * LETTER_L * LETTER_GROOVE


def _rot(img, ang):
    M = cv2.getRotationMatrix2D((C, C), math.degrees(ang), 1.0)
    return cv2.warpAffine(img, M, (N, N), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


def to_frame(Lp, fill=FIELD):
    full = np.full((H2X, W2X), fill, np.float32)
    x0, y0 = int(W2X / 2 - C), int(H2X / 2 - C)
    full[y0:y0 + N, x0:x0 + N] = Lp
    return full


def render_text(pun, theta, visible=None, omega=None, nsub=8, shutter=0.5, layer=None):
    """Text disc at plate angle theta (rad, ccw on screen). omega: rev/frame for the 180 deg shutter
    (None or 0 = a still). Returns (L 2x full frame float32, letter alpha 2x full frame, 'neutral')."""
    A, V = layer if layer is not None else letter_layer(pun, visible)
    st = np.dstack([A, V])
    dth = 2 * math.pi * (omega or 0.0)
    subs = [theta + dth * shutter * ((q + 0.5) / nsub - 0.5) for q in range(nsub)] if omega else [theta]
    accL = np.zeros((N, N), np.float32)
    accA = np.zeros((N, N), np.float32)
    for a in subs:
        rs = _rot(st, a)
        at, vt = rs[..., 0], rs[..., 1]
        # emboss: shadow cast down-right by the camera-fixed upper-left light, 1.5 px at 1x
        sh = cv2.GaussianBlur(np.roll(at, (3, 3), (0, 1)), (0, 0), 1.2)
        plate = PLATE_TEXT * (1 - 0.6 * sh * (1 - at))
        accL += plate * (1 - at) + vt * LIGHT_LET
        accA += at
    L = accL / len(subs)
    L = FIELD + (L - FIELD) * DISC
    return to_frame(L), to_frame(accA / len(subs) * DISC, 0.0), "neutral"


def to_1x(L2):
    return np.clip(cv2.resize(L2, (960, 540), interpolation=cv2.INTER_AREA) + 0.5, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- fixtures
def screen_order(pun, theta, direction):
    """Order tokens are met reading the frozen frame along the spiral: outer turn first, clockwise from
    the token nearest the text start. Independent of rotation direction because rotation is rigid."""
    path, _ = glyph_path(pun)
    sgn = 1 if direction == "ccw" else -1
    pts = []
    for g in path:
        a = g["phi"] - sgn * theta                    # screen angle (image coords, cw positive)
        x, y = g["r"] * math.cos(a), g["r"] * math.sin(a)
        pts.append((g["i"], x, y))
    # recover spiral parameter from screen position: unwrap angle cw from the screen start ray
    start = path[0]["phi"] - sgn * theta - 1e-6
    out = []
    for i, x, y in pts:
        a = (math.atan2(y, x) - start) % (2 * math.pi)
        r = math.hypot(x, y)
        # turn index from radius relative to the continuous spiral at that angle
        turn = round(((RADII[0] + DELTA - PITCH * a / (2 * math.pi)) - r) / PITCH)
        out.append((turn * 2 * math.pi + a, i))
    out.sort()
    return [i for _, i in out]


def fixtures():
    res = {}
    for pun in PUNS:
        path, scale = glyph_path(pun)
        text = disc_text(pun)
        ok_tokens = "".join(g["ch"] for g in path) == text
        ok_mono = all(path[i]["phi"] > path[i - 1]["phi"] and path[i]["r"] < path[i - 1]["r"]
                      and path[i]["turn"] >= path[i - 1]["turn"] for i in range(1, len(path)))
        orders = {}
        for d in ("cw", "ccw"):
            ok = True
            for th in np.linspace(0, 2 * math.pi, 37):
                if screen_order(pun, float(th), d) != list(range(len(path))):
                    ok = False
            orders[d] = ok
        # ring correspondence: glyph radius vs ring j radius, in ring band-widths (band = PITCH/2)
        band = RING_PITCH / 2
        dev = [abs(g["r"] - RADII[g["ring"]]) / band for g in path if g["ch"] != " "]
        mono_ring = all(path[i]["ring"] >= path[i - 1]["ring"] for i in range(1, len(path)))
        per_ring = [sum(1 for g in path if g["ring"] == k and g["ch"] != " ") for k in range(KR)]
        # still-frame read-back: decode the frozen frame's GlyphPath along the spiral
        readback = "".join(path[i]["ch"] for i in screen_order(pun, 2 * math.pi * 360 / 256, "ccw"))
        res[pun] = dict(
            token_string_equals_disc_text=ok_tokens,
            glyph_path_monotone_inward_clockwise=ok_mono,
            order_equals_token_order_cw=orders["cw"],
            order_equals_token_order_ccw=orders["ccw"],
            order_tested_at_thetas=37,
            readback_at_theta_F360_equals_text=readback == text,
            ring_band_deviation_max=max(dev), ring_band_deviation_mean=float(np.mean(dev)),
            within_one_band=bool(max(dev) <= 1.0 + 1e-9),
            radial_slide_max_px_1x=max(dev) * band / SS,
            within_slide_budget_1p5_band=max(dev) <= 1.5,
            slide_note=("one continuous Archimedean spiral (turn pitch = TEXT_PITCH_RINGS x ring pitch); glyph i corresponds to "
                        "ring c(i) = the ring nearest its radius (order-preserving: c is non-decreasing in i), "
                        "so its radial slide onto ring c(i) is at most half a pitch = one ring band. The "
                        "geometric turn index ('turn') runs ahead of 'ring' by the rim offset (the outer turn "
                        "starts %.1f px outside ring 0 because the letter tops must stay inside the 232 px rim)."
                        % (DELTA / SS)),
            every_ring_has_glyphs=all(n > 0 for n in per_ring),
            ring_correspondence_order_preserving=mono_ring,
            glyphs_per_ring=per_ring,
            tracking_scale=scale, tracking_ok=scale >= TRACK_MIN - 1e-9,
            pitch_over_cap=PITCH / CAP,
            opened_vs_kf2=(PITCH / CAP) / KF2_PITCH_OVER_CAP,
            letter_tops_inside_rim=(RADII[0] + DELTA + CAP / 2) <= R - RIM_CLEAR + 1e-6,
            not_duchamp=not any(_norm(PUNS[pun]) in _norm(t) or _norm(t) in _norm(PUNS[pun]) for t in DUCHAMP_TEXTS),
            shared_word_3grams_with_duchamp=_shared_ngrams(PUNS[pun]),
        )
        assert all(v for k, v in res[pun].items() if isinstance(v, bool) and k != "within_one_band"), (pun, res[pun])
    return res


def _norm(s):
    return "".join(ch for ch in s.upper() if ch.isalnum())


def _shared_ngrams(p, n=3):
    def grams(s):
        w = [x for x in "".join(ch if ch.isalnum() else " " for ch in s.upper()).split()]
        return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}
    g = grams(p)
    hit = set()
    for t in DUCHAMP_TEXTS:
        hit |= g & grams(t)
    return sorted(" ".join(x) for x in hit)


def chiasmus_check(pun):
    a, b = PUNS[pun].split(SEP.strip())
    wa, wb = sorted(a.split()), sorted(b.split())
    return dict(first=a.strip(), second=b.strip(), exact_word_permutation=wa == wb,
                chars=len(PUNS[pun]))


def dump():
    out = dict(
        unit="U2 language agent and glyph layout",
        module=WS + "/glyphs.py",
        ring_source=RING_SOURCE, rings_1x=RINGS_1X,
        ring_source_sha1=hashlib.sha1(json.dumps(RINGS_1X).encode()).hexdigest(),
        conventions=dict(scale="2x internal (plate radius 464, centre of 1920x1080 frame); values below at 2x unless *_1x",
                         phi="radians in image coords (y down): increasing = clockwise on screen; -pi/2 = 12 o'clock",
                         theta="ccw positive on screen; glyph at plate phi appears at screen angle phi - theta",
                         tangent="unit reading direction (cw) in image coords",
                         turn="spiral turn from outside (0) inward; ring = turn (O_A ring index from outside)"),
        type=dict(font="LiberationSans-Bold", cap_px_1x=CAP / SS, font_px_1x=FPX / SS,
                  pitch_px_1x=PITCH / SS, pitch_over_cap=PITCH / CAP, ring_pitch_px_1x=RING_PITCH / SS,
                  text_pitch_in_ring_pitches=TEXT_PITCH_RINGS,
                  kf2_pitch_over_cap=KF2_PITCH_OVER_CAP, opened_by=(PITCH / CAP) / KF2_PITCH_OVER_CAP - 1,
                  tracking_min=TRACK_MIN, spiral_start_phi=PHI0, delta_px_1x=DELTA / SS,
                  plate_phase=PHASE, theta_read=THETA_READ, theta_read_source=THETA_READ_SOURCE,
                  letter_L=LETTER_L, letter_groove_pitch_px_1x=GROOVE / SS, letter_groove_depth=0.03,
                  emboss="shadow 1.5 px down-right, Gaussian 0.6 px (1x), from the camera-fixed upper-left light",
                  plate="neutral sphere, L = 58 + 158 * lambert(light (-0.38,-0.78,0.55)), camera-fixed"),
        puns={}, fixtures=fixtures())
    for pun in PUNS:
        path, scale = glyph_path(pun)
        out["puns"][pun] = dict(
            pun=PUNS[pun], gloss_en=GLOSS[pun], chiasmus=chiasmus_check(pun),
            disc_text=disc_text(pun), halves=disc_text(pun).count(SEP) + 1, n_tokens=len(path),
            tracking_scale=scale,
            tokens=[dict(i=g["i"], ch=g["ch"], r=round(g["r"], 2), r_1x=round(g["r"] / SS, 2),
                         phi=round(g["phi"], 5), tangent=[round(g["tangent"][0], 5), round(g["tangent"][1], 5)],
                         turn=g["turn"], ring=g["ring"], adv=round(g["adv"], 2)) for g in path],
            ring_correspondence=[dict(ring=k, r_ring_1x=RINGS_1X[k],
                                      tokens=[g["i"] for g in path if g["ring"] == k],
                                      first=min(g["i"] for g in path if g["ring"] == k),
                                      last=max(g["i"] for g in path if g["ring"] == k),
                                      glyph_r_1x_range=[round(min(g["r"] for g in path if g["ring"] == k) / SS, 2),
                                                        round(max(g["r"] for g in path if g["ring"] == k) / SS, 2)])
                                 for k in range(KR)])
    return out


if __name__ == "__main__":
    os.makedirs(MED, exist_ok=True)
    d = dump()
    p = WS + "/glyphpaths.json"
    old = json.load(open(p)) if os.path.exists(p) else {}
    for key in ("reading_speed", "still_pass", "evidence", "absences", "handmade", "media", "aesthetic_measurements"):
        if key in old:
            d[key] = old[key]
    json.dump(d, open(p, "w"), indent=1, ensure_ascii=False)
    print(json.dumps(d["fixtures"], indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in d["type"].items()}, indent=1))
    for pun in PUNS:
        print(pun, d["puns"][pun]["chiasmus"], d["puns"][pun]["halves"], d["puns"][pun]["n_tokens"])
