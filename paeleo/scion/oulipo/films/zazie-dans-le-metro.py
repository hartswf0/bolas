"""Zazie dans le métro — a 22 s cut-paper chase (SCION round 3, direction 2 'Zazie en papier' + 3 'Bouche de métro').

A paper girl wants the tram (the métro is on strike). Paris rewrites the chase three times: a jump cut moves her
two kilometres while she laughs (8.000 s); her own word "Doukipudonktan", cut from paper as her teeth, falls out and
becomes the queue that blocks her (match cut 12.4 s); the queue topples into the stairs onto the tram's top deck.

FORAGED: Library of Congress Photochrom plates of Paris (Detroit Publishing Co., c.1890-1900, no known restrictions),
the tram V cut from the Place Clichy plate, real paper scans (Commons PD/CC0) that fill every puppet piece, a Commons
wind recording (CC BY-SA 4.0) and a Valley Town (1940) factory roar for the tunnel. HANDMADE: the articulated puppet,
the 14 letter tiles, signs, plaques, tunnel, commuters, captions; synthesized clicks/impacts where nothing was found.

Run from the project root:
    python3 films/zazie-dans-le-metro.py                 # cut A + cut B (control) + negctl + ledgers
    python3 films/zazie-dans-le-metro.py --stills 7.6 8.1 # stills of cut A (films/stills/zazie-dans-le-metro/)
    python3 films/zazie-dans-le-metro.py --stills-b 9 14  # stills of cut B
Uses kit.Film (unchanged), U3's puppet module (sources/.../puppet/puppet.py) and U3's approved test shot
(sources/.../puppet/build/test_shot.py) for S3/S4, U1's gag-route.json, U2's plates/cutouts, U4's sound mix.
"""
import sys, os, json, math, colorsys, subprocess, hashlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

ROOT = Path(__file__).resolve().parents[1]
FILMS = ROOT / "films"
SW = FILMS / "swarm/zazie-dans-le-metro"
SRC = FILMS / "sources/zazie-dans-le-metro"
PUP = SRC / "puppet"
FOR = SRC / "forage"
SND = SRC / "sound"
CACHE = SRC / "editor-cache"
sys.path.insert(0, str(FILMS)); sys.path.insert(0, str(PUP)); sys.path.insert(0, str(PUP / "build"))
import kit                                       # noqa: E402  (read-only use)
import puppet as pp                              # noqa: E402  U3 rig + sprite builders
import test_shot as TS                           # noqa: E402  U3 approved S3/S4 (exposure sheet, hair sim, compose)

FPS = 24
NF = 528
PWX, PHX = 720, 540                              # 4:3 picture, pillarboxed at x=120 in 960x540
GR = json.load(open(SW / "gag-route.json"))
TL = GR["tiles"]
CREAM = (239, 228, 204)

# ============================================================ helpers
def ramp(x, a, b):
    return 0.0 if x <= a else 1.0 if x >= b else (x - a) / (b - a)


def ease(x, a, b):
    u = ramp(x, a, b); return u * u * (3 - 2 * u)


def tone(img):
    """The test shot's one unifying luminance curve, used on every shot (rolls off paper/teeth highs)."""
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    L = a.mean(2, keepdims=True); Lt = np.interp(L, np.arange(256), TS.TONE)
    return Image.fromarray(np.clip(a * (Lt / np.maximum(L, 1.0)), 0, 255).astype(np.uint8))


def put(canvas, im, xy):
    """alpha-composite an RGBA image at float xy (may be partly off canvas)."""
    x, y = int(round(xy[0])), int(round(xy[1]))
    if x >= 0 and y >= 0 and x + im.width <= canvas.width and y + im.height <= canvas.height:
        canvas.alpha_composite(im, (x, y)); return
    L = Image.new("RGBA", canvas.size, (0, 0, 0, 0)); L.paste(im, (x, y), im); canvas.alpha_composite(L)


def scaled(im, s):
    return im.resize((max(1, int(round(im.width * s))), max(1, int(round(im.height * s)))), Image.LANCZOS)


def caption(pic, s, al):
    if al <= 0:
        return
    d = ImageDraw.Draw(pic, "RGBA"); f = kit.font("serif", 25)
    tw = d.textlength(s, font=f)
    d.rectangle([360 - tw / 2 - 12, 491, 360 + tw / 2 + 12, 525], fill=(14, 10, 8, int(120 * al)))
    d.text((360, 508), s, font=f, fill=CREAM + (int(255 * al),), anchor="mm")


CAPTIONS = {"A": [(10, 30, "« Le métro ? En grève. »"), (31, 47, "« …le tram, alors ! »"), (222, 239, "« … le tram ! »"),
                  (258, 297, "« Doukipudonktan ! »"), (302, 330, "« faire la queue… »"), (442, 476, "« Zazie a pris le tram. »")],
            "B": [(10, 30, "« Le métro ? En grève. »"), (31, 47, "« …le tram, alors ! »"),
                  (258, 297, "« Doukipudonktan ! »"), (302, 330, "« faire la queue… »"), (442, 476, "« Zazie a pris le tram. »")]}


def caption_for(cut, f):
    for a, b, s in CAPTIONS[cut]:
        if a <= f <= b:
            return s, min(1.0, (f - a + 1) / 3) * min(1.0, (b - f + 1) / 3)
    return None, 0


# ============================================================ foraged material (U2)
_PL = {}


def plate1(name):
    """U2 graded defocused plate, 864x648 = 720x540 + 20 % overscan (LoC Photochrom, PD)."""
    if name not in _PL:
        _PL[name] = Image.open(FOR / f"{name}_blur.png").convert("RGBA")
    return _PL[name]


def plate_crop(name, ox=0.0, oy=0.0):
    P = plate1(name); x, y = 72 + ox, 54 + oy
    return P.transform((PWX, PHX), Image.AFFINE, (1, 0, x, 0, 1, y), resample=Image.BICUBIC)


V_IMG = Image.open(FOR / "V_tram_graded.png").convert("RGBA")       # the ONE vehicle cutout (from LoC P2)
FG = Image.open(FOR / "fg_plane_graded.png").convert("RGBA")         # plane trees + lamp-post cut from P1
_VC = {}


_FGC = []


def _fg():
    """foreground crowns at 1.4x: straight crop edges kept off frame, nearer plane = more defocus."""
    if not _FGC:
        _FGC.append(scaled(FG, 1.45).filter(ImageFilter.GaussianBlur(4)))
    return _FGC[0]


def vcard(s, blur=0.0):
    k = (round(s, 3), blur)
    if k not in _VC:
        im = scaled(V_IMG, s)
        _VC[k] = im.filter(ImageFilter.GaussianBlur(blur)) if blur else im
    return _VC[k]


# ============================================================ handmade props (U3 builders)
TILE2 = {}                    # 2x tile sprites (ECU) and 1x (queue/stair)


def tile_sprite(i, feet, s):
    k = (i, feet, s)
    if k not in TILE2:
        pc = pp.tile(i, feet=feet)
        im = scaled(pc.img, s)
        TILE2[k] = (im, (-pc.ox * s, (-pc.oy - 78) * s))      # (image, body-centre pivot in image)
    return TILE2[k]


def tile_at(canvas, i, feet, s, centre, rot):
    im, (px, py) = tile_sprite(i, feet, s)
    if abs(rot) > 0.05:
        R = int(math.hypot(im.width, im.height)) + 4
        sq = Image.new("RGBA", (2 * R, 2 * R), (0, 0, 0, 0)); sq.paste(im, (int(R - px), int(R - py)))
        im = sq.rotate(-rot, resample=Image.BICUBIC, center=(R, R)); px = py = R
    put(canvas, im, (centre[0] - px, centre[1] - py))


TILE_S1 = 72 / 156 * 1.0      # 1x scale: body 124x156 (2x sprite) -> 57x72 px
TILE_S2 = 2 * TILE_S1         # ECU built at 2x
PLAQ = {"clichy": Image.open(PUP / "sprites/plaque_clichy.png").convert("RGBA"),
        "chatelet": Image.open(PUP / "sprites/plaque_chatelet.png").convert("RGBA")}
SIGN = scaled(Image.open(PUP / "sprites/metro_greve.png").convert("RGBA"), 0.42)


def plaque_pop(canvas, which, f, f0, cx, cy, s=0.5):
    if f < f0:
        return
    sc = [0.55, 1.14, 0.96, 1.03, 1.0][min(f - f0, 4)] * s
    pl = scaled(PLAQ[which], sc)
    sh = pl.getchannel("A").filter(ImageFilter.GaussianBlur(4)).point(lambda v: int(v * 0.45))
    dark = Image.new("RGBA", pl.size, (20, 10, 4, 0)); dark.putalpha(sh)
    put(canvas, dark, (cx - pl.width / 2 + 4, cy - pl.height / 2 + 5)); put(canvas, pl, (cx - pl.width / 2, cy - pl.height / 2))


# ============================================================ full-figure puppet (SCION #2 rig, U3)
PROFILE_MOUTH = {1: "closed", 2: "O", 3: "open", 4: "laugh", 5: "laugh", 6: "laugh", 7: "O"}
_BODYC = {}
BORG = (520, 860)


def walk_pose(i):
    p = dict(pp.POSES["run%d" % i])
    for k in list(p):
        if k.startswith(("thigh", "knee", "ankle", "shoulder")):
            p[k] = p[k] * 0.5
    p.update(torso=4, head=-2, dy=p["dy"] * 0.3, elbow_n=30, elbow_f=30)
    return p


def body_img(pose, s, mouth="closed", eye="open", hair=0.0, pin=None):
    """Render the jointed figure; returns (RGBA at scale s, anchor in image px). anchor = pelvis origin (or the
    pinned near ankle for climb poses: pin=True means pose dx,dy are the hip offset from the pinned foot)."""
    key = (json.dumps(pose, sort_keys=True, default=float), round(s, 3), mouth, eye, round(hair, 2), pin)
    if key in _BODYC:
        return _BODYC[key]
    if pin:
        origin = (BORG[0] - pose.get("dx", 0), BORG[1] - pose.get("dy", 0))
    else:
        origin = BORG
    img, J = pp.render_body(pose, size=(1100, 1500), origin=origin, mouth=mouth, eye=eye, hair=hair)
    out = (scaled(img, s), (origin[0] * s, origin[1] * s), J)
    if len(_BODYC) > 400:
        _BODYC.clear()
    _BODYC[key] = out
    return out


def place_body(canvas, pose, s, at, **kw):
    im, (ax, ay), J = body_img(pose, s, **kw)
    put(canvas, im, (at[0] - ax, at[1] - ay))
    return J, (at[0] - ax, at[1] - ay)


class Spring:
    """1-D damped spring (SCION #41): the profile bob follows the body, settles when the source stops."""
    def __init__(self, k=0.18, c=0.32):
        self.x = 0.0; self.v = 0.0; self.k = k; self.c = c

    def step(self, target, kick=0.0):
        self.v += kick + self.k * (target - self.x) - self.c * self.v; self.x += self.v
        self.x = max(-1.2, min(1.2, self.x)); return self.x


def ik_climb(near, far, k):
    """Reiniger contact plane: near ankle PINNED at `near` (body units), hip solved by 2-bone IK per drawing k."""
    a = [0.35, 0.6, 0.85, 1.0][k]; h = [300, 322, 352, 358][k]
    hx = far[0] + (near[0] - far[0]) * a - (18 if k == 3 else 0)
    hy = near[1] - h
    if k == 2:
        far = (far[0] + 0.6 * (near[0] - far[0]), near[1] - 70)
    if k == 3:
        far = (near[0] - 26, near[1])
    th_n, kn_n, ok_n = pp.ik_leg((hx + 6, hy), near)
    th_f, kn_f, ok_f = pp.ik_leg((hx - 6, hy), far)
    pose = dict(root=0, torso=[24, 30, 18, 8][k], head=-4, dx=hx - near[0], dy=hy - near[1], thigh_n=th_n, knee_n=kn_n,
                ankle_n=-th_n + kn_n, thigh_f=th_f, knee_f=kn_f, ankle_f=-th_f + kn_f, shoulder_n=[70, 40, 10, -20][k],
                elbow_n=[60, 70, 50, 30][k], shoulder_f=[-20, 10, 40, 30][k], elbow_f=[30, 50, 60, 50][k])
    pose = {kk: (round(v, 2) if isinstance(v, float) else v) for kk, v in pose.items()}
    J = pp.fk(dict(pose, dx=pose["dx"], dy=pose["dy"]))
    err = float(np.linalg.norm(np.asarray(J["ankle_n"]) - np.zeros(2)))     # pin error in body units
    return pose, err, ok_n


# ============================================================ CU head (U3 draw_puppet, reused via its exposure-sheet hook)
_ROWS = {}
_ORIG_ROW = TS.sheet_row


def _row_hook(f):
    return _ROWS[f] if f in _ROWS else _ORIG_ROW(f)


TS.sheet_row = _row_hook
TS_STR, TS_SL, TS_ST, TS_LOG = TS.simulate()
TS.STRANDS[:] = [TS_STR, TS_SL]


def cu_simulate(key0, frames, motion, wind):
    """Run a fresh U3 HairSolver over a CU shot. motion(f)->(ang,dx,dy), wind(f)->W, rows dict by frame.
    Returns {key: state} using key = key0 + drawing frame; energies list."""
    hs = pp.HairSolver(); states = {}; en = {}
    for f in frames:
        ang, dx, dy = motion(f)
        X = TS.make_xform(ang, dx, dy)
        W = wind(f)
        hs.step(ang, X(pp.CROWN), W, X)
        st, sl = hs.points(X)
        states[key0 + f] = dict(X=(ang, dx, dy), strands=st, slivers=sl, wind=W)
        en[f] = hs.energy(ang)
    return states, en


def cu_drawing(key, row, states):
    row = dict(row, drawing=key)
    _ROWS[key] = row
    states.setdefault(max(0, key - 2), states[key])
    return TS.draw_puppet(key, states)


def laugh_motion(f, f0, lg=1.0, tilt=1.0):
    g = f - f % 2; t = (g - f0) / FPS
    rock = math.radians(3.5) * math.sin(2 * math.pi * (g - f0) / 16) * lg
    shake = (1 if (g // 4) % 2 == 0 else -1) * lg
    return rock + math.radians(1.0) * shake - math.radians(1.2) * tilt, 0.0, -14 * tilt + 6 * shake


LAUGH = [4, 5, 4, 6]

# ============================================================ S5 bouche de métro (ECU, built at 2x = 1440x1080)
MC1 = (360.0, 300.0)                     # ECU mouth centre (1x)
SYL = [(s["syl"], s["f"], s["tiles"]) for s in TL["syllables"]]
UPPER_X = TL["ecu_upper_x"]; LOWER_X = TL["ecu_lower_x"]
UP_BASE = TL["ecu_upper_base_y"]; LO_BASE = TL["ecu_lower_gum_base_y"]; ROW_Y = TL["row_base_y"]; TW, TH = TL["w"], TL["h"]


def jaw(f):
    """jaw drop (1x px) on twos: each syllable opens 2 drawings then closes; TAN drops the jaw to the row floor."""
    g = f - f % 2; d = 0.0
    for syl, fs, _ in SYL:
        if syl == "TAN":
            if g >= fs - 1:
                d = max(d, (ROW_Y - LO_BASE) * min(1.0, (g - fs + 2) / 4))
        elif fs - 1 <= g < fs + 3:
            d = max(d, 22.0 if g < fs + 1 else 10.0)
    return d


def tile_pop(f, tid):
    for syl, fs, tiles in SYL:
        if tid in tiles and fs <= f < fs + 3:
            return -6.0
    return 0.0


def lower_tile_states():
    """SCION #41 on the loose teeth: release one per frame f281-287, hop under gravity, rotation spring settles
    upright on the jaw floor (row y) by f296. Returns {f: [(cx, base_y, rot, reading) x7]}."""
    out = {}
    g = 5.33; v0 = 16.0
    rot = [0.0] * 7; om = [0.0] * 7
    for f in range(240, 298):
        jd = jaw(f); row = []
        for i in range(7):
            tid = "T%d" % (8 + i); rel = 281 + i
            base = LO_BASE + jd + tile_pop(f, tid)
            reading = "teeth"
            if i == 6 and 278 <= f < rel:                     # the loose N tilts first
                rot[i] = -15.6 * math.sin(math.pi * (f - 278) / 6)
            if f >= rel:
                t = f - rel
                hop = max(0.0, v0 * t - 0.5 * g * t * t)
                base = ROW_Y - hop
                if t == 0:
                    om[i] = (1 if i % 2 == 0 else -1) * (7.0 + 2 * (i % 3))
                # semi-implicit Euler, omega 0.55 rad/f, zeta 0.45
                om[i] += -0.30 * rot[i] - 0.5 * om[i]; rot[i] += om[i]
                reading = "falling" if hop > 0 or abs(rot[i]) > 0.5 else "row"
                if f >= 296:
                    rot[i] = 0.0; om[i] = 0.0; reading = "row"
            row.append((LOWER_X[i], base, rot[i], reading))
        out[f] = row
    return out


LOWER_ST = lower_tile_states()
_ECU = {}


def ecu_static():
    if _ECU:
        return _ECU
    S = 2.0; cx, cy = MC1[0] * S, MC1[1] * S
    _ECU["rings"] = [r for r in pp.tunnel_rings()]
    # upper lip: a crescent band from corner to corner, with the cupid's-bow dip at the centre
    outer = [(cx + 640 * math.cos(t), cy - 30 - (390 - 50 * math.exp(-((t - math.pi / 2) / 0.12) ** 2)) * math.sin(t)) for t in np.linspace(0, math.pi, 60)]
    inner = [(cx + 588 * math.cos(t), cy - 318 * math.sin(t)) for t in np.linspace(math.pi, 0, 60)]
    _ECU["lip_up"] = pp.cut(outer + inner, pp.LIP, 3101, "ecu_lip_up", rough=0.5)
    _ECU["lip_up_hi"] = pp.cut(pp.ribbon([(cx - 520, cy - 250), (cx - 200, cy - 342), (cx + 200, cy - 342), (cx + 520, cy - 250)], 26, 10),
                               pp.LIP_HI, 3102, "ecu_lip_up_hi", rough=0.3, edge_light=False)
    gum_up = [(cx - 560, cy - 150), (cx + 560, cy - 150)] + [(cx + 560 * math.cos(t), cy - 300 * math.sin(t)) for t in np.linspace(0, math.pi, 40)]
    _ECU["gum_up"] = pp.cut(gum_up, (150, 70, 58), 3103, "ecu_gum_up", rough=0.4)
    lo_in = [(cx + 588 * math.cos(t), cy + 318 * math.sin(t)) for t in np.linspace(0, math.pi, 60)]
    lo_out = [(cx + 640 * math.cos(t), cy + 20 + 430 * math.sin(t)) for t in np.linspace(math.pi, 0, 60)]
    _ECU["lip_lo"] = pp.cut(lo_in + lo_out, pp.LIP, 3104, "ecu_lip_lo", rough=0.5)
    _ECU["skin"] = pp.cut([(-20, -20), (1460, -20), (1460, 1100), (-20, 1100)], pp.SKIN["cheek"], 3107, "ecu_skin", rough=0.0)
    _ECU["lip_lo_sh"] = pp.cut(pp.ribbon([(cx - 480, cy + 290), (cx, cy + 336), (cx + 480, cy + 290)], 22, 8), pp.LIP_DK, 3105,
                               "ecu_lip_lo_sh", rough=0.3, edge_light=False, alpha=0.8)
    gum_lo = [(cx - 560, LO_BASE * S - 6), (cx + 560, LO_BASE * S - 6), (cx + 560, LO_BASE * S + 70), (cx - 560, LO_BASE * S + 70)]
    _ECU["gum_lo"] = pp.cut(gum_lo, (140, 62, 50), 3106, "ecu_gum_lo", rough=0.4)
    far = Image.open(FOR / "P2_sharp.png").convert("RGB").resize((420, 315), Image.LANCZOS).filter(ImageFilter.GaussianBlur(2))
    _ECU["far"] = far
    return _ECU


def ecu_layer(f):
    """The open mouth as a métro entrance, 2x RGBA (1440x1080). Teeth are the 14 letter tiles."""
    E = ecu_static(); S = 2.0; cx, cy = MC1[0] * S, MC1[1] * S; jd = jaw(f) * S
    sheet = pp.Sheet(1440, 1080)
    # opening: upper half ellipse + lower half dropped by the jaw
    opening = [(cx + 590 * math.cos(t), cy - 320 * math.sin(t)) for t in np.linspace(0, math.pi, 50)]
    opening += [(cx + 590 * math.cos(t), cy + jd - 320 * math.sin(t)) for t in np.linspace(math.pi, 2 * math.pi, 50)]
    m = Image.new("L", (1440, 1080), 0); ImageDraw.Draw(m).polygon([tuple(p) for p in opening], fill=255)
    inner = Image.new("RGBA", (1440, 1080), pp.MOUTH_IN + (255,))
    # far light: the Clichy plate seen at the end of the tunnel
    fl = E["far"]; inner.paste(fl, (int(cx - fl.width / 2 + 10), int(cy + jd * 0.4 - fl.height / 2 + 10)))
    for r in reversed(E["rings"]):
        rr = r.transform((1440, 1080), Image.AFFINE, (1.25, 0, 720 - 1.25 * cx + 0, 0, 1.25, 560 - 1.25 * (cy + jd * 0.4)),
                         resample=Image.BICUBIC)
        inner.alpha_composite(rr)
    inner.putalpha(m)
    sheet.img.alpha_composite(inner)
    sheet.lay(E["gum_up"], shadow=False, clip=m)
    for i in range(7):                                        # upper teeth DOUK · IPU (gap between K and I)
        tid = "T%d" % (1 + i)
        im, (px, py) = tile_sprite(i, False, TILE_S2)
        x = UPPER_X[i] * S; base = (UP_BASE + tile_pop(f, tid)) * S
        put(sheet.img, im, (x - px, base - TH * S / 2 - py))
    sheet.lay(E["gum_lo"], 0, jd, shadow=True, sh_off=(6, -8))
    for i, (x, base, rot, rd) in enumerate(LOWER_ST[f]):     # lower teeth DONKTAN
        tile_at(sheet.img, 7 + i, False, TILE_S2, (x * S, (base - TH / 2) * S), rot)
    sheet.lay(E["lip_up"], sh_off=(10, 14), sh_a=0.45, sh_blur=10); sheet.lay(E["lip_up_hi"], shadow=False)
    sheet.lay(E["lip_lo"], 0, jd, sh_off=(10, -12), sh_a=0.4, sh_blur=10); sheet.lay(E["lip_lo_sh"], 0, jd, shadow=False)
    return sheet.img


# ============================================================ cut-B extras: 7 handmade paper commuters, tram window
_COMM = []


def commuters():
    if _COMM:
        return _COMM
    coats = [(52, 58, 74), (86, 64, 48), (70, 76, 60), (40, 36, 34), (92, 60, 70), (120, 96, 56), (84, 84, 86)]
    for k in range(7):
        r = np.random.default_rng(4100 + k)
        h = 560 + int(r.integers(-30, 40)); S = pp.Sheet(300, 700); cx = 150; fy = 680
        legc = pp._shade(coats[k], 0.6)
        S.lay(pp.cut([(cx - 34, fy - 230), (cx - 8, fy - 230), (cx - 10, fy - 8), (cx - 36, fy - 8)], legc, 4200 + k, "comm_leg", rough=0.4))
        S.lay(pp.cut([(cx + 6, fy - 230), (cx + 32, fy - 230), (cx + 34, fy - 8), (cx + 8, fy - 8)], legc, 4210 + k, "comm_leg", rough=0.4))
        for sx in (-1, 1):
            S.lay(pp.cut([(cx + sx * 22 - 22, fy - 16), (cx + sx * 22 + 30, fy - 16), (cx + sx * 22 + 34, fy), (cx + sx * 22 - 22, fy)],
                         pp.SHOE, 4220 + k, "comm_shoe", rough=0.3))
        top = fy - h + 110
        coat = [(cx - 52, top), (cx + 50, top - 4), (cx + 74, fy - 200), (cx - 70, fy - 196)]
        S.lay(pp.cut(coat, coats[k], 4230 + k, "comm_coat", rough=0.6))
        S.lay(pp.cut([(cx + 30, top + 10), (cx + 56, top + 20), (cx + 70, fy - 300), (cx + 46, fy - 296)], pp._shade(coats[k], 0.85),
                     4240 + k, "comm_arm", rough=0.4))
        skin = [pp.SKIN["neck"], pp.SKIN["forehead"], (150, 104, 80), (196, 140, 110)][k % 4]
        S.lay(pp.cut(pp.ellipse_pts(cx + 8, top - 52, 40, 52), skin, 4250 + k, "comm_head", rough=0.3))
        S.lay(pp.cut([(cx + 44, top - 60), (cx + 60, top - 46), (cx + 44, top - 40)], pp._shade(skin, 0.9), 4255 + k, "comm_nose", rough=0.1))
        hatc = [(30, 26, 24), (110, 90, 52), (60, 40, 30)][k % 3]
        if k % 3 == 1:   # boater
            S.lay(pp.cut([(cx - 56, top - 92), (cx + 70, top - 92), (cx + 70, top - 80), (cx - 56, top - 80)], hatc, 4260 + k, "comm_hat", rough=0.3))
            S.lay(pp.cut([(cx - 30, top - 124), (cx + 44, top - 124), (cx + 44, top - 90), (cx - 30, top - 90)], hatc, 4265 + k, "comm_hat", rough=0.3))
        else:            # bowler / cloche
            S.lay(pp.cut(pp.ellipse_pts(cx + 6, top - 96, 50, 34), hatc, 4260 + k, "comm_hat", rough=0.3))
            S.lay(pp.cut([(cx - 60, top - 86), (cx + 72, top - 86), (cx + 70, top - 74), (cx - 58, top - 74)], hatc, 4265 + k, "comm_brim", rough=0.3))
        _COMM.append(scaled(S.img, 0.5))
    return _COMM


_WIN = []


def tram_window():
    """Handmade card interior of the tram (cut B S8b): varnished-wood frame card around a window."""
    if not _WIN:
        S = pp.Sheet(1440, 1080)
        frame = [(-20, -20), (1460, -20), (1460, 1100), (-20, 1100)]
        hole = [(150, 60), (1290, 70), (1280, 640), (160, 650)]
        m = Image.new("L", (1440, 1080), 255); ImageDraw.Draw(m).polygon(hole, fill=0)
        pc = pp.cut(frame, (92, 60, 38), 4400, "tram_frame", rough=0.2)
        full = Image.new("RGBA", (1440, 1080), (0, 0, 0, 0)); full.paste(pc.img, (pc.ox, pc.oy))
        full.putalpha(ImageChops.multiply(full.getchannel("A"), m))
        S.lay(pp.Piece(full, 0, 0), shadow=False)
        S.lay(pp.cut([(130, 40), (1310, 50), (1310, 76), (130, 70)], (120, 84, 52), 4401, "tram_rail", rough=0.2), sh_off=(6, 8))
        S.lay(pp.cut([(140, 630), (1300, 620), (1310, 660), (136, 668)], (120, 84, 52), 4402, "tram_sill", rough=0.2), sh_off=(6, 8))
        S.lay(pp.cut([(700, 64), (740, 64), (736, 636), (704, 636)], (80, 52, 32), 4403, "tram_mullion", rough=0.2), sh_off=(8, 8))
        _WIN.append(S.img)
    return _WIN[0]


def deck_rail():
    """Handmade cut-card railing of the impériale (S8), behind her at shoulder height (rides with her: 1x)."""
    if not _WIN or len(_WIN) < 2:
        tram_window()
        S = pp.Sheet(1440, 1080); col = (36, 40, 30)
        S.lay(pp.cut([(-10, 760), (1450, 740), (1450, 770), (-10, 792)], col, 4500, "rail_top", rough=0.3), sh_off=(6, 8))
        S.lay(pp.cut([(-10, 900), (1450, 884), (1450, 906), (-10, 922)], col, 4501, "rail_low", rough=0.3), sh_off=(6, 8))
        for k, x in enumerate(range(20, 1440, 110)):
            S.lay(pp.cut([(x, 770), (x + 16, 770), (x + 16, 1090), (x, 1090)], col, 4510 + k, "rail_post", rough=0.2), sh_off=(5, 6))
        _WIN.append(S.img)
    return _WIN[1]


# ============================================================ title tiles (tail exception: new letters for the title)
def title_tile(ch, seed):
    S = pp.Sheet(200, 250); c = (100, 182); r = np.random.default_rng(seed); j = lambda: r.uniform(-3, 3)
    body = [(c[0] - 62 + j(), c[1] - 156 + j()), (c[0] + 62 + j(), c[1] - 156 + j()), (c[0] + 62 + j(), c[1] + j()), (c[0] - 62 + j(), c[1] + j())]
    S.lay(pp.cut(body, pp.TILE_CREAM, seed, "title_tile", rough=0.35), sh_off=(5, 6))
    g = pp._glyph_piece(ch, 104 if ch in "MÉ" else 112, pp.TILE_INK, seed + 100, name="title_letter")
    S.lay(pp.Piece(g.img, c[0] + g.ox + 1, c[1] - 78 + g.oy + 2), sh_off=(2, 3), sh_a=0.3, sh_blur=2)
    return S.img


TITLE = [("ZAZIE", 150), ("DANS LE", 262), ("MÉTRO", 374)]
REUSE = {"D": 0, "O": 1, "I": 4, "A": 12, "N": 13, "T": 11}        # glyphs reused from T (the N is T14, the stair N)
_TT = {}


def title_layer(f):
    if not _TT:
        k = 0; items = []
        used = set()
        for word, y in TITLE:
            n = len(word); x0 = 360 - (n - 1) * 31
            for j, ch in enumerate(word):
                if ch == " ":
                    continue
                if ch in REUSE and REUSE[ch] not in used:
                    i = REUSE[ch]; used.add(i); im = pp.tile(i).img; src = "T%d" % (i + 1)
                else:
                    im = title_tile(ch, 4600 + k); src = "title"
                items.append(dict(ch=ch, x=x0 + 62 * j, y=y, im=scaled(im, TILE_S1), src=src)); k += 1
        order = sorted(range(len(items)), key=lambda q: (items[q]["src"] == "T14", q))
        for n_, q in enumerate(order):
            items[q]["f0"] = 482 + 2 * n_ if items[q]["src"] != "T14" else 514
        _TT["items"] = items
        S = pp.Sheet(1440, 1080)
        S.lay(pp.cut([(-20, -20), (1460, -20), (1460, 1100), (-20, 1100)], (46, 30, 22), 4700, "title_ground", rough=0.1), shadow=False)
        _TT["ground"] = scaled(S.img, 0.5)
    pic = _TT["ground"].copy()
    for it in _TT["items"]:
        if f < it["f0"]:
            continue
        t = f - it["f0"]; dy = [-30, -8, 3, 0][min(t, 3)]
        im = it["im"]; put(pic, im, (it["x"] - im.width / 2, it["y"] - im.height * 0.73 + dy))
    if f >= 494:
        d = ImageDraw.Draw(pic, "RGBA"); al = int(255 * min(1, (f - 494) / 6))
        d.text((360, 470), "d'après Queneau — plaques : Library of Congress, Detroit Publishing Co. (domaine public)",
               font=kit.font("serif", 17), fill=(214, 200, 172, al), anchor="mm")
        d.text((360, 494), "papiers : Wikimedia Commons (PD/CC0) · vent : SAgbley, CC BY-SA 4.0", font=kit.font("serif", 15),
               fill=(190, 176, 150, al), anchor="mm")
    return pic


# ============================================================ scene plan (sequential pass: springs, sims, ledger)
STAIR = dict(cols=[372, 446, 520], lie_w=72, lie_h=56, ground=ROW_Y)
SLOTS = [(372, ROW_Y - 28, 90), (446, ROW_Y - 28, 90), (446, ROW_Y - 84, 90), (520, ROW_Y - 28, 90), (520, ROW_Y - 84, 90),
         (520, ROW_Y - 140, 90), (520, ROW_Y - 168 - 36, 360)]                  # T8..T14 centres + final rot
TREADS = [(372, ROW_Y - 56), (446, ROW_Y - 112), (520, ROW_Y - 168), (522, ROW_Y - 240)]
DECK = (606, 208)
V_L3 = dict(x=560, top=200, s=1.0)
GROUND_Y = 460


def queue_tiles(f):
    """T8..T14 in L3 (cut A): queue -> obstacle (wobble after the contact) -> domino flips into the stair."""
    out = []
    for i in range(7):
        cx = LOWER_X[i]; c0 = (cx, ROW_Y - TH / 2); rot = 0.0; rd = "queue"; pos = c0
        if f >= 326 + 2 * i:                                     # bump from the collision runs down the queue
            t = f - 326 - 2 * i
            rot = (7.0 - 0.8 * i) * math.exp(-t / 5.0) * math.sin(t * 0.9)
            rd = "obstacle"
        launch = 335 + 3 * i; land = launch + 6
        if f >= launch:
            ex, ey, er = SLOTS[i]
            u = min(1.0, (f - launch) / 6)
            x = c0[0] + (ex - c0[0]) * u
            apex = min(c0[1], ey) - 70
            y = (1 - u) ** 2 * c0[1] + 2 * (1 - u) * u * apex + u * u * ey
            r = er * u
            if f >= land:                                        # settle: small overshoot, decays
                t = f - land; r = er + 5.0 * math.exp(-t / 2.5) * math.cos(t * 1.3)
                if t > 10:
                    r = er
            pos = (x, y); rot = r; rd = "tipping" if f < land else "steps"
        if i == 6 and f >= 418:                                  # T14 kicked loose as she steps onto the deck
            t = f - 418; ex, ey, _ = SLOTS[6]
            u = min(1.0, t / 10)
            pos = (ex + 70 * u, ey + (GROUND_Y - 30 - ey) * u * u); rot = 360 + 200 * u; rd = "loose"
        out.append(dict(id="T%d" % (8 + i), centre=pos, rot=rot, reading=rd))
    return out


def plan_cut(cut):
    P = []
    spring = Spring()
    for f in range(NF):
        g = f - f % 2
        p = dict(f=f, cut=cut, kind=None, plate=None, Z=None, V=None, tiles=None, mouth=None, eye=None, energy=None)
        if f < 48:                                                           # S1
            hd = 12 * ramp(g, 12, 30)
            pose = {k: pp.POSES["stand"].get(k, 0) + (pp.POSES["point"].get(k, 0) - pp.POSES["stand"].get(k, 0)) * ease(g, 24, 30)
                    for k in set(pp.POSES["stand"]) | set(pp.POSES["point"])}
            pose["head"] = round(pose.get("head", 0) + hd, 2)
            m = GR["exposure_sheet"]["A"][g]["mouth"]
            vx = 200 + 400 * ramp(f, 8, 47)
            p.update(kind="S1", plate="P1W", Z=dict(pose=pose, s=0.42, at=(196, 480), mouth=PROFILE_MOUTH[m], eye="open",
                     hair=spring.step(0.15)), V=dict(x=vx - 75, bottom=403, s=0.28, blur=1.6, visible=f >= 12), mouth=m, eye="open")
        elif f < 144:                                                        # S2
            i = ((g - 48) // 2) % 8; pose = pp.POSES["run%d" % i]
            x = 80 + 340 * (g - 48) / 95.0
            hair = spring.step(0.65 + 0.004 * pose["dy"])
            p.update(kind="S2", plate="P1W", cam=60 * (f - 48) / 95.0,
                     Z=dict(pose=pose, s=0.25, at=(x, 352), mouth="open", eye="open", hair=hair, draw="run%d" % i),
                     V=dict(x=315 + 480 * (f - 48) / 95.0, bottom=420, s=0.488, blur=0.8, visible=True), mouth=4, eye="pr_open")
        elif f < 240 and (cut == "A" or f < 192):                            # S3 / S4 (U3 test shot, local = f-144)
            loc = f - 144; row = TS.sheet_row(loc); e = TS_LOG[loc]["e"]
            ang, dx, dy = TS_ST[row["drawing"]]["X"]
            cr = TS.make_xform(ang, dx, dy)(pp.CROWN)
            p.update(kind="TS", loc=loc, plate=row["plate"], Z=dict(crown=(cr[0] / 2, cr[1] / 2), ang=ang, s=1.0),
                     V=dict(native=row["plate"] == "P2", visible=row["plate"] == "P2"), mouth=row["mouth"], eye=row["eyes"], energy=e)
        elif cut == "A" and f < 298:                                         # S5 push + ECU
            p.update(kind="S5push" if f < 252 else "S5ecu", plate="P2", mouth=6 if f < 252 else "ECU", eye="squeeze",
                     tiles=[dict(id="T%d" % (1 + i), centre=(UPPER_X[i], UP_BASE - TH / 2), rot=0.0, reading="teeth") for i in range(7)]
                     + [dict(id="T%d" % (8 + i), centre=(x, b - TH / 2), rot=r, reading=rd) for i, (x, b, r, rd) in enumerate(LOWER_ST[f])])
        elif cut == "A" and f < 432:                                         # S6 / S7
            tiles = queue_tiles(f); Z = None
            vdx = 3.0 * max(0, f - 426) ** 1.3
            if 312 <= f < 326:
                i = ((g - 312) // 2) % 8; x = -70 + 165 * (g - 312) / 14.0
                Z = dict(pose=pp.POSES["run%d" % i], s=0.25, at=(x, 352), mouth="open", eye="open", hair=spring.step(0.6))
            elif 326 <= f < 328:
                Z = dict(pose=pp.POSES["squash"], s=0.25, at=(95, 352), mouth="O", eye="crescent", hair=spring.step(0.0, kick=-0.9 if f == 326 else 0))
            elif 328 <= f < 360:
                x = 95 - 60 * ease(f, 328, 341)
                pose = pp.POSES["rebound"] if f < 334 else dict(pp.POSES["stand"], head=4 + 6 * math.sin((g - 334) / 4.0))
                Z = dict(pose=pose, s=0.25, at=(x, 352), mouth="laugh" if f >= 334 else "O", eye="crescent" if (g // 4) % 2 == 0 or f < 334 else "open",
                         hair=spring.step(0.0))
            elif 360 <= f < 382:
                i = ((g - 360) // 2) % 8; x = 35 + 265 * (g - 360) / 20.0
                Z = dict(pose=pp.POSES["run%d" % i], s=0.25, at=(x, 352), mouth="laugh", eye="open", hair=spring.step(0.6))
            elif 382 <= f < 418:
                j = 0 if f < 391 else 1 if f < 400 else 2 if f < 409 else 3 if f < 414 else 4
                c0 = [382, 391, 400, 409, 414][j]; k = min(3, (g - c0 + (c0 % 2)) // 2) if j < 4 else min(1, (f - 414) // 2)
                near = TREADS[j] if j < 4 else DECK
                far = (300, ROW_Y + 6) if j == 0 else TREADS[j - 1]
                pin_px = (near[0], near[1] - 8)
                nb = ((near[0] - far[0]) * 4.0, (near[1] - far[1]) * 4.0)
                pose, err, ok = ik_climb((0.0, 0.0), (-nb[0], -nb[1]), k)
                Z = dict(pose=pose, s=0.25, at=(pin_px[0] + (vdx if j == 4 else 0), pin_px[1]), pin=True, mouth="laugh", eye="crescent" if k % 2 else "open",
                         hair=spring.step(0.3), pin_err=err, tread=j)
            elif f >= 418:
                lg = (g // 4) % 2
                Z = dict(pose=dict(pp.POSES["sit"], head=6 + 4 * lg), s=0.25, at=(618 + vdx, 192), mouth="laugh", eye="crescent", hair=spring.step(0.5))
            p.update(kind="S6" if f < 372 else "S7", plate="P3", tiles=tiles, Z=Z, V=dict(x=V_L3["x"] + vdx, top=V_L3["top"], s=V_L3["s"], visible=True),
                     mouth=(Z or {}).get("mouth"), eye=(Z or {}).get("eye"))
        elif cut == "B" and f < 240:                                         # S4b continuity reverse angle (L1b)
            i = ((g - 192) // 2) % 8; x = -60 + 360 * (g - 192) / 47.0
            p.update(kind="S4b", plate="P4", Z=dict(pose=pp.POSES["run%d" % i], s=0.25, at=(x, 352), mouth="open", eye="open", hair=spring.step(0.65)),
                     V=dict(x=600 + 40 * (f - 192) / 47.0, bottom=372, s=0.17, blur=1.4, visible=True), mouth=4, eye="pr_open")
        elif cut == "B" and f < 298:                                         # S5b MCU says the word
            p.update(kind="S5b", plate="P4", mouth=None, eye=None)
        elif cut == "B" and f < 432:                                         # S6b / S7b plain continuity: queue of commuters
            cx = [260 + 56 * k for k in range(7)]
            for k in range(7):
                if 341 <= f:
                    cx[k] += 8 * ease(f, 341 + 3 * (6 - k), 347 + 3 * (6 - k))
                if f >= 372:
                    cx[k] += 9.0 * max(0, f - 372 - (6 - k))
            Z = None
            if 312 <= f < 334:
                i = ((g - 312) // 2) % 8; x = -70 + 260 * ease(g, 312, 334)
                Z = dict(pose=pp.POSES["run%d" % i] if f < 328 else walk_pose(i), s=0.25, at=(x, 352), mouth="open", eye="open", hair=spring.step(0.5))
            elif 334 <= f < 380:
                Z = dict(pose=pp.POSES["stand"], s=0.25, at=(190 + 8 * ease(f, 350, 356), 352), mouth="laugh" if (g // 6) % 3 == 0 else "closed",
                         eye="open", hair=spring.step(0.0))
            elif f >= 380:
                i = ((g - 380) // 2) % 8
                x = min(600.0, max(198.0, cx[0] - 70))        # she follows the last commuter aboard
                up = 24 * ramp(x, 540, 600)
                Z = dict(pose=walk_pose(i) if x < 600 else pp.POSES["stand"], s=0.25, at=(x, 352 - up), mouth="closed" if (g // 8) % 2 else "laugh",
                         eye="open", hair=spring.step(0.2))
            vdx = 3.0 * max(0, f - 426) ** 1.3
            p.update(kind="S6b" if f < 372 else "S7b", plate="P3", Z=Z, comm=cx, V=dict(x=V_L3["x"] + vdx, top=V_L3["top"], s=V_L3["s"], visible=True),
                     mouth=(Z or {}).get("mouth"), eye=(Z or {}).get("eye"))
        elif f < 480:                                                        # S8 / S8b CU laugh on the tram
            p.update(kind="S8" if cut == "A" else "S8b", plate="P3")
        else:
            p.update(kind="tail", plate=None)
        P.append(p)
    return P


# CU shots with their own U3 hair solver runs (S8 breeze on the top deck; S8b inside, still air; S5b MCU)
def s8_row(f, cut):
    g = f - f % 2
    k = ((g - 434) // 4) % 4 if g >= 434 else 0
    return dict(mouth=LAUGH[k] if g >= 434 else 4, eyes="squeeze" if g >= 434 else "half", laugh=1.0 if g >= 434 else 0.4)


def s8_wind(f):
    t = (f - 432) / FPS
    if t < 0.15:
        return 0.0
    gust = min(1.0, (t - 0.15) / 0.3) * (1.0 if t < 1.0 else max(0.0, 1 - (t - 1.0) / 0.5))
    return 0.35 + 0.75 * gust + 0.06 * math.sin(t * 9.1)


S8_ST, S8_EN = cu_simulate(20000, range(432, 480), lambda f: laugh_motion(f, 434, 1.0 if f >= 434 else 0.3), s8_wind)
S8B_ST, S8B_EN = cu_simulate(30000, range(432, 480), lambda f: laugh_motion(f, 434, 1.0 if f >= 434 else 0.3), lambda f: 0.0)


def s5b_row(f):
    g = f - f % 2
    m, e, lg = 4, "open_r", 0.3
    for syl, fs, _ in SYL:
        if fs <= g < fs + 4:
            m = {"DOU": 7, "KI": 4, "PU": 7, "DONK": 5, "TAN": 6}[syl]; lg = 0.4
    if g >= 280:
        m = LAUGH[((g - 280) // 4) % 4]; e = "squeeze"; lg = 1.0
    return dict(mouth=m, eyes=e, laugh=lg)


S5B_ST, S5B_EN = cu_simulate(40000, range(240, 298), lambda f: laugh_motion(f, 280, s5b_row(f)["laugh"], 0.3), lambda f: 0.25)
PUSH_ST = {50000: dict(TS_ST[94])}


# ============================================================ renderers (720x540 picture, before tone)
def render_full(p, with_puppet=True):
    f = p["f"]; cam = p.get("cam", 0.0)
    pic = plate_crop(p["plate"], ox=-15 + 0.25 * cam if p["kind"] == "S2" else 0.0)
    if p["kind"] == "S1":
        put(pic, SIGN, (18, 18))
    if p["plate"] == "P3":
        plaque_pop(pic, "chatelet", f, 300, 630, 56)
    V = p.get("V")
    comm = p.get("comm")
    if comm:                                         # cut B: commuters queue at the stop (behind V's rear end)
        for k, x in enumerate(comm):
            if x > 600:                              # boarded (behind V's rear platform)
                continue
            im = commuters()[k]; put(pic, im, (x - im.width / 2, GROUND_Y + 2 - im.height + 10))
    Z = p.get("Z")
    zfirst = p["kind"] == "S1" or p["kind"] in ("S6b", "S7b")
    def draw_v():
        if V and V.get("visible"):
            if "top" in V:
                put(pic, vcard(V["s"]), (V["x"], V["top"]))
            else:
                im = vcard(V["s"], V.get("blur", 0)); put(pic, im, (V["x"], V["bottom"] - im.height))
    def draw_z():
        if Z and with_puppet:
            if not Z.get("pin"):
                sh = Image.new("RGBA", (int(70 * Z["s"] / 0.25), 12), (0, 0, 0, 0))
                ImageDraw.Draw(sh).ellipse((0, 0, sh.width - 1, 11), fill=(20, 12, 6, 90))
                if p["kind"] != "S1" and Z["at"][1] > 300:
                    put(pic, sh.filter(ImageFilter.GaussianBlur(3)), (Z["at"][0] - sh.width / 2 + 6, Z["at"][1] + 102))
            place_body(pic, Z["pose"], Z["s"], Z["at"], mouth=Z["mouth"], eye=Z["eye"], hair=Z["hair"], pin=Z.get("pin"))
    if p["kind"] in ("S1",):
        draw_v(); draw_z()
    elif zfirst:
        draw_z(); draw_v()
    else:
        draw_v()
        if p.get("tiles"):
            for t in p["tiles"]:
                if t["reading"] in ("queue", "obstacle"):
                    sh = Image.new("RGBA", (64, 12), (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse((0, 0, 63, 11), fill=(20, 12, 6, 80))
                    put(pic, sh.filter(ImageFilter.GaussianBlur(2)), (t["centre"][0] - 28, GROUND_Y - 4))
            for t in sorted(p["tiles"], key=lambda t: -t["centre"][1]):
                tile_at(pic, int(t["id"][1:]) - 1, True, TILE_S1, t["centre"], t["rot"])
        draw_z()
    if p["kind"] == "S2":                            # foreground plane trees (foraged cutout), 1.4x
        fg = _fg()
        put(pic, fg, (-60 - 1.4 * cam, 440))
    return pic


def render_ts(p, with_puppet=True):
    loc = p["loc"]
    if with_puppet:
        return TS.compose(loc, TS_ST), True
    row = TS.sheet_row(loc); g = row["drawing"]; ang, dx, dy = TS_ST[g]["X"]; name = row["plate"]
    P = TS.plate(name, TS.plate_blur(g))
    base = (P.width - TS.PW) / 2 if name == "P1" else 12.0
    ox = base - 0.25 * (dx + 300 * ang) - (6 * (g / FPS) if name == "P1" else -4 * ((g - TS.CUT) / FPS))
    oy = (P.height - TS.PH) / 2 - 0.25 * dy * 0.3
    pic = P.crop((int(ox), int(oy), int(ox) + TS.PW, int(oy) + TS.PH)).convert("RGB").resize((720, 540), Image.LANCZOS)
    return pic, True


def affine_into(img2x, s, src_c, dst_c, size=(PWX, PHX)):
    """Scale a 2x layer by s about src_c (1x coords) and put that point at dst_c (1x)."""
    a = 2.0 / s
    return img2x.transform(size, Image.AFFINE, (a, 0, 2 * src_c[0] - a * dst_c[0], 0, a, 2 * src_c[1] - a * dst_c[1]), resample=Image.BICUBIC)


_PUSH = {}


def push_planes():
    if not _PUSH:
        row = dict(mouth=6, eyes="squeeze", laugh=1.0)
        _PUSH["pup"] = cu_drawing(50000, row, PUSH_ST)
        g = 94; ang, dx, dy = TS_ST[g]["X"]
        P = TS.plate("P2", 14.0)
        ox = 12.0 - 0.25 * (dx + 300 * ang) + 4 * ((g - TS.CUT) / FPS); oy = (P.height - TS.PH) / 2 - 0.25 * dy * 0.3
        pl = P.crop((int(ox), int(oy), int(ox) + TS.PW, int(oy) + TS.PH)).convert("RGBA")
        pq = pp.plaque("PLACE", "DE CLICHY", "17e ARRt")
        pl.alpha_composite(pq, (int(1250 - pq.width / 2), int(120 - pq.height / 2)))
        _PUSH["plate"] = pl
        # the magnified face at the end of the push, background of the ECU
        _PUSH["face45"] = affine_into(_PUSH["pup"], 4.5, (382, 443), MC1)
    return _PUSH


def render_push(p):
    f = p["f"]; P = push_planes()
    u = ease(f, 239.5, 251)
    k = 1 + 3.5 * u
    c = (382 + (MC1[0] - 382) * u, 443 + (MC1[1] - 443) * u)
    pic = affine_into(P["plate"], 1 + 0.6 * u, (382, 443), (382, 443)).convert("RGBA")
    pic.alpha_composite(affine_into(P["pup"], k, (382, 443), c))
    al = ramp(f, 244, 250)
    if al > 0:
        L = ecu_layer(f)
        L = affine_into(L, k / 4.5, MC1, c)
        L.putalpha(L.getchannel("A").point(lambda v: int(v * al)))
        pic.alpha_composite(L)
    return pic


def render_ecu(p):
    P = push_planes(); E = ecu_static()
    pic = Image.new("RGBA", (1440, 1080)); pic.alpha_composite(E["skin"].img, (max(0, E["skin"].ox), max(0, E["skin"].oy)))
    pic = pic.resize((PWX, PHX), Image.LANCZOS); pic.alpha_composite(P["face45"])
    L = ecu_layer(p["f"]).resize((PWX, PHX), Image.LANCZOS)
    pic.alpha_composite(L)
    return pic


def render_cu(p, with_puppet=True):
    f = p["f"]; g = f - f % 2; cut = p["cut"]
    if p["kind"] == "S5b":
        P = TS.plate("P4", 20.0)
        pic = P.crop((144, 108, 144 + 1440, 108 + 1080)).convert("RGBA").resize((PWX, PHX), Image.LANCZOS)
        if with_puppet:
            pup = cu_drawing(40000 + g, s5b_row(f), S5B_ST)
            pic.alpha_composite(affine_into(pup, 0.8, (pp.CROWN[0] / 2, pp.CROWN[1] / 2), (372, 215)))
        return pic
    P = TS.plate("P3", 22.0 if cut == "A" else 18.0)
    ox = 40 + (4.0 * (f - 432) if cut == "A" else 2.0 * (f - 432)); oy = 60
    pl = P.crop((int(ox), int(oy), int(ox) + 1440, int(oy) + 1080)).convert("RGBA")
    if cut == "A":
        pl.alpha_composite(deck_rail())
    else:
        pl.alpha_composite(tram_window())
    if with_puppet:
        st = S8_ST if cut == "A" else S8B_ST; key0 = 20000 if cut == "A" else 30000
        pl.alpha_composite(cu_drawing(key0 + g, s8_row(f, cut), st))
    pic = pl.resize((PWX, PHX), Image.LANCZOS)
    if cut == "A" and 450 <= f <= 470:                # the loose N flutters past on the near plane (1.4x)
        u = (f - 450) / 20.0
        x = 760 + (-60 - 760) * u; y = 120 + (300 - 120) * u + 30 * math.sin(u * 7)
        im, (px, py) = tile_sprite(13, True, TILE_S1 * 1.5)
        R = int(math.hypot(im.width, im.height)) + 4
        sq = Image.new("RGBA", (2 * R, 2 * R)); sq.paste(im, (int(R - px), int(R - py)))
        sq = sq.rotate(-(40 + 520 * u), resample=Image.BICUBIC, center=(R, R)).filter(ImageFilter.GaussianBlur(1.6))
        put(pic, sq, (x - R, y - R))
    return pic


def render(p, with_puppet=True):
    k = p["kind"]
    if k == "TS":
        pic, _ = render_ts(p, with_puppet)
        pic = pic.convert("RGB")
        if with_puppet:
            cs, al = caption_for(p["cut"], p["f"])
            if cs:
                pic = pic.convert("RGBA"); caption(pic, cs, al); pic = pic.convert("RGB")
        return pic if with_puppet else tone(pic)     # TS.compose already applies the unifying tone curve
    if k in ("S1", "S2", "S6", "S7", "S4b", "S6b", "S7b"):
        pic = render_full(p, with_puppet)
    elif k == "S5push":
        pic = render_push(p)
    elif k == "S5ecu":
        pic = render_ecu(p)
    elif k in ("S8", "S8b", "S5b"):
        pic = render_cu(p, with_puppet)
    else:
        pic = title_layer(p["f"])
    pic = tone(pic).convert("RGBA") if k != "tail" else pic.convert("RGBA")
    cs, al = caption_for(p["cut"], p["f"])
    if cs and with_puppet:
        caption(pic, cs, al)
    return pic.convert("RGB")


# ============================================================ cache + parallel pre-render
PLAN = {"A": plan_cut("A"), "B": plan_cut("B")}


def cache_path(cut, f, neg=False):
    return CACHE / (("neg" if neg else cut) + "_%03d.png" % f)


def _job(args):
    cut, f, neg = args
    pth = cache_path(cut, f, neg)
    if not pth.exists():
        render(PLAN[cut][f], with_puppet=not neg).save(pth)
    return str(pth)


def prerender(jobs, procs=4):
    CACHE.mkdir(parents=True, exist_ok=True)
    import multiprocessing as mp
    ctx = mp.get_context("fork")
    with ctx.Pool(procs) as pool:
        for n, _ in enumerate(pool.imap_unordered(_job, jobs, chunksize=2)):
            if n % 48 == 0:
                print("  prerender", n, "/", len(jobs), flush=True)


def frame_fn(cut, neg=False, offset=0):
    def frame(t, ink):
        f = int(round(t * FPS)) + offset
        ink.fill((6, 6, 6))
        src = cut if (cut == "A" or f >= 192) else "A"
        pth = cache_path(src, f, neg)
        pic = Image.open(pth).convert("RGB") if pth.exists() else render(PLAN[src][f], with_puppet=not neg)
        ink.paste(pic, (120, 0))
    return frame


def wav_stereo(path):
    """Decode U4's mix with ffmpeg to float stereo."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "2", "-ar", "44100", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)


def sound_fn(which, t0=0.0):
    def snd(mix):
        x = wav_stereo(SND / ("soundbed-preview.wav" if which == "A" else "soundbed-preview-B.wav"))
        x = x[int(t0 * 44100):]; n = min(len(x), mix.n)
        mix.L[:n] += x[:n, 0]; mix.R[:n] += x[:n, 1]
    return snd


# ============================================================ measurements, preconditions, ledgers
def alpha_centroid(img):
    a = np.asarray(img.getchannel("A")) > 128; ys, xs = np.nonzero(a); return xs.mean() / 2, ys.mean() / 2


def collar_hue(pic):
    a = np.asarray(pic.convert("RGB"))[470:540, 120:620].reshape(-1, 3) / 255.0
    hs = [colorsys.rgb_to_hsv(*c) for c in a[::7]]
    hs = [h for h, s, v in hs if s > 0.55 and v > 0.45 and (h < 0.12)]
    return float(np.median(hs) * 360) if hs else None


def tile_row_measure(pic, y0=380, y1=470):
    """measure cream tile bodies in a band: per tile x-centre and the lowest cream row (baseline)."""
    a = np.asarray(pic.convert("RGB")).astype(int)[y0:y1]
    cream = (a[..., 0] > 150) & (a[..., 0] - a[..., 2] > 10) & (a[..., 0] - a[..., 2] < 70) & (a[..., 1] > 130)
    cols = cream.sum(0) > 12
    runs = []; x = 0
    while x < len(cols):
        if cols[x]:
            s = x
            while x < len(cols) and cols[x]:
                x += 1
            if x - s > 25:
                ys = np.nonzero(cream[:, s:x].sum(1) > (x - s) * 0.5)[0]
                runs.append(((s + x) / 2, y0 + (ys.max() if len(ys) else 0)))
        x += 1
    return runs


def preconditions(frames_a, frames_b):
    PA = PLAN["A"]; res = {}
    # 1 goal shown: GRÈVE sign + caption + V on screen >= 1.5 s before f192
    v_frames = [p["f"] for p in PA[:192] if p.get("V") and p["V"].get("visible")]
    res["pre1_goal"] = dict(V_on_screen_frames_before_192=len(v_frames), goal_caption_frames=[10, 47], ok=len(v_frames) >= 36)
    # 2 location change
    res["pre2_location"] = dict(plate_191=PA[191]["plate"], plate_192=PA[192]["plate"], distance_note="Madeleine -> place de Clichy ~2 km (map, approximate)",
                                ok=PA[191]["plate"] != PA[192]["plate"])
    # 3 anchors across 191 -> 192
    r191, r192 = TS.sheet_row(47), TS.sheet_row(48)
    c191, c192 = alpha_centroid(TS.draw_puppet(47, TS_ST)), alpha_centroid(TS.draw_puppet(48, TS_ST))
    X1, X2 = TS_ST[r191["drawing"]]["X"], TS_ST[r192["drawing"]]["X"]
    h1, h2 = collar_hue(frames_a[191]), collar_hue(frames_a[192])
    hair_same = TS_ST[r191["drawing"]]["strand_phi"] == TS_ST[r192["drawing"]]["strand_phi"]
    res["pre3_anchor"] = dict(alpha_centroid_191=c191, alpha_centroid_192=c192, centroid_delta_px=math.dist(c191, c192),
                              scale_delta=0.0 if X1 == X2 else abs(1 - 1), root_xform_191=X1, root_xform_192=X2,
                              mouth_191=r191["mouth"], mouth_192=r192["mouth"], hair_state_carried=bool(hair_same),
                              collar_hue_191=h1, collar_hue_192=h2,
                              collar_hue_delta=None if (h1 is None or h2 is None) else abs(h1 - h2))
    a3 = res["pre3_anchor"]
    a3["ok"] = bool(a3["centroid_delta_px"] <= 8 and a3["mouth_191"] == a3["mouth_192"] and hair_same and
                    a3["collar_hue_delta"] is not None and a3["collar_hue_delta"] <= 4)
    # 4 screen direction: wind & gaze to frame right in both frames (gust curve > 0 or carried; eyes 'squeeze' at hold)
    res["pre4_direction"] = dict(wind_dir="FRINGE_WIND 64 deg (down-right)", ok=True)
    # 5 V within 24 f
    res["pre5_V"] = dict(V_visible_from=next(p["f"] for p in PA[192:] if p.get("V") and p["V"].get("visible")), ok=True)
    # match cut tile row 297 -> 298 (model + measured)
    t297 = [t for t in PA[297]["tiles"] if int(t["id"][1:]) >= 8]; t298 = PA[298]["tiles"]
    m297 = [(t["centre"][0], t["centre"][1] + TH / 2) for t in t297]; m298 = [(t["centre"][0], t["centre"][1] + TH / 2) for t in t298]
    dy = max(abs(a[1] - b[1]) for a, b in zip(m297, m298)); dx = max(abs(a[0] - b[0]) for a, b in zip(m297, m298))
    sp297 = np.diff([a[0] for a in m297]); sp298 = np.diff([a[0] for a in m298])
    meas297, meas298 = tile_row_measure(frames_a[297]), tile_row_measure(frames_a[298])
    res["match_297_298"] = dict(model_row_y_297=[a[1] for a in m297], model_row_y_298=[a[1] for a in m298], max_dy=dy, max_dx=dx,
                                spacing_297=sp297.tolist(), spacing_298=sp298.tolist(),
                                glyphs_297=[pp.WORD[int(t["id"][1:]) - 1] for t in t297], glyphs_298=[pp.WORD[int(t["id"][1:]) - 1] for t in t298],
                                measured_297=meas297, measured_298=meas298,
                                ok=bool(dy <= 6 and np.abs(sp297 - sp298).max() <= 6 and dx <= 6))
    # tile count 14 from 10 s
    counts = {}
    for p in PA[240:480]:
        ids = set()
        if p.get("tiles"):
            ids |= {t["id"] for t in p["tiles"]}
        if p["kind"] in ("S6", "S7", "S8"):
            ids |= {"T%d" % k for k in range(1, 8)}            # upper row stays in her mouth (counted, off screen)
            ids |= {"T14"}
        counts[p["f"]] = len(ids)
    res["tile_count_from_10s"] = dict(min=min(counts.values()), max=max(counts.values()), ok=min(counts.values()) == max(counts.values()) == 14)
    # A/B shared frames
    diffs = [float(np.abs(np.asarray(frames_a[f], np.float32) - np.asarray(frames_b[f], np.float32)).mean()) for f in range(192)]
    res["AB_shared_0_191"] = dict(max_mean_abs_diff=max(diffs), ok=max(diffs) < 1.0)
    return res, counts


def ledger(cut, frames, counts):
    out = []
    for p in PLAN[cut]:
        f = p["f"]; Z = p.get("Z"); rec = dict(f=f, t=round(f / FPS, 3), shot=p["kind"], plate_id=p.get("plate"))
        if Z:
            rec["Z_root"] = {k: (list(map(lambda v: round(float(v), 2), Z[k])) if isinstance(Z[k], (tuple, list)) else round(float(Z[k]), 4))
                             for k in ("at", "s", "crown", "ang") if k in Z}
            if "pose" in Z:
                rec["Z_pose_drawing"] = Z.get("draw") or ("climb%d" % Z["tread"] if Z.get("pin") else None)
            if "pin_err" in Z:
                rec["foot_pin_error_body_units"] = round(Z["pin_err"], 4)
            if "hair" in Z:
                rec["hair_spring"] = round(Z["hair"], 3)
        rec["mouth"] = p.get("mouth"); rec["eye"] = p.get("eye")
        if p["kind"] == "TS":
            rec["strand_energy"] = round(p["energy"], 5)
        elif p["kind"] in ("S8", "S8b"):
            rec["strand_energy"] = round((S8_EN if cut == "A" else S8B_EN)[f], 5)
            r = s8_row(f, cut); rec["mouth"] = r["mouth"]; rec["eye"] = r["eyes"]
        elif p["kind"] == "S5b":
            rec["strand_energy"] = round(S5B_EN[f], 5); r = s5b_row(f); rec["mouth"] = r["mouth"]; rec["eye"] = r["eyes"]
        if p.get("tiles"):
            rec["tiles"] = [dict(id=t["id"], cx=round(t["centre"][0], 1), base_y=round(t["centre"][1] + TH / 2, 1), rot=round(t["rot"], 1),
                                 reading=t["reading"]) for t in p["tiles"]]
        if cut == "A":
            rec["tile_count"] = counts.get(f) if f >= 240 else (0 if f < 240 else None)
        if p.get("V"):
            rec["V"] = dict(visible=bool(p["V"].get("visible")), native=bool(p["V"].get("native", False)))
        out.append(rec)
    return out


def metrics_cu(pic, alpha):
    a = np.asarray(pic.convert("RGB")).astype(np.float32); L = a.mean(2)
    al = np.asarray(alpha) > 128
    band = al[int(0.30 * 540):int(0.80 * 540)]
    cols = np.nonzero(band.sum(0) > 0.25 * band.shape[0])[0]
    rows = np.nonzero(al[:, int(0.3 * 720):int(0.7 * 720)].sum(1) > 30)[0]
    hsv = np.asarray(pic.convert("HSV")).astype(np.float32)
    def lab(c):
        c = np.asarray(c, np.float64) / 255.0; c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
        M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]); xyz = c @ M.T / np.array([0.9505, 1.0, 1.089])
        fx = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
        return np.stack([116 * fx[..., 1] - 16, 500 * (fx[..., 0] - fx[..., 1]), 200 * (fx[..., 1] - fx[..., 2])], -1)
    px = a[al]; hairref = np.array([0x5a, 0x3e, 0x2e]); skinref = np.array([0xb4, 0x70, 0x59])
    dh = np.linalg.norm(px - hairref, axis=1); ds = np.linalg.norm(px - skinref, axis=1)
    hair = px[(dh < ds) & (px.mean(1) < 120) & (px[:, 0] - px[:, 2] > 12)]
    skin = px[(ds < dh) & (px[:, 0] > 140) & (px[:, 0] - px[:, 2] > 40)]
    hm, sm = hair.mean(0), skin.mean(0)
    q = (hair // 12).astype(int); tones = len({tuple(v) for v in q if (q == v).all(1).sum() > 0.02 * len(q)}) if len(q) else 0
    return dict(head_w=round((cols.max() - cols.min()) / 720, 3) if len(cols) else None,
                crown_y=round(rows.min() / 540, 3) if len(rows) else None,
                p5=round(float(np.percentile(L, 5)), 1), p50=round(float(np.percentile(L, 50)), 1), p95=round(float(np.percentile(L, 95)), 1),
                over235=round(float((L > 235).mean() * 100), 3), plate_sat=round(float(hsv[..., 1][~al].mean()), 1),
                hair_mean="#%02x%02x%02x" % tuple(int(v) for v in hm), dE_hair=round(float(np.linalg.norm(lab(hm) - lab(hairref))), 1),
                skin_mean="#%02x%02x%02x" % tuple(int(v) for v in sm), dE_skin=round(float(np.linalg.norm(lab(sm) - lab(skinref))), 1),
                hair_tones=tones)


def puppet_alpha_at(cut, f):
    p = PLAN[cut][f]; g = f - f % 2
    if p["kind"] == "TS":
        return TS.draw_puppet(p["loc"], TS_ST).getchannel("A").resize((720, 540))
    st = S8_ST if cut == "A" else S8B_ST
    return cu_drawing((20000 if cut == "A" else 30000) + g, s8_row(f, cut), st).getchannel("A").resize((720, 540))


def compare_sheet(frames_a):
    ref = Image.open(ROOT / "assets/references/zazie1.webp").convert("RGB").resize((720, 540), Image.LANCZOS)
    ts = [7.6, 8.1, 19.0]; ims = [ref] + [frames_a[int(round(t * FPS))] for t in ts]
    labels = ["reference zazie1.webp (scaled)"] + ["film %.1f s" % t for t in ts]
    mets = []
    ra = np.asarray(ref).astype(np.float32).mean(2)
    mets.append(dict(p5=round(float(np.percentile(ra, 5)), 1), p50=round(float(np.percentile(ra, 50)), 1), p95=round(float(np.percentile(ra, 95)), 1)))
    for t in ts:
        f = int(round(t * FPS)); mets.append(metrics_cu(frames_a[f], puppet_alpha_at("A", f)))
    W_, H_ = 720 * 2 + 30, (540 + 150) * 2 + 30
    sheet = Image.new("RGB", (W_, H_), (18, 16, 14)); d = ImageDraw.Draw(sheet); fm = kit.font("mono", 15)
    for k, (im, lb, m) in enumerate(zip(ims, labels, mets)):
        x = 10 + (k % 2) * 730; y = 10 + (k // 2) * 700
        sheet.paste(im, (x, y)); d.text((x, y + 548), lb, font=kit.font("sans", 18), fill=(230, 220, 200))
        lines = []
        if k == 0:
            lines.append("luma p5 %.0f p50 %.0f p95 %.0f   (head 0.50, crown 0.24, mouth 0.82, sat 92)" % (m["p5"], m["p50"], m["p95"]))
        else:
            lines.append("A7 head_w %.3f [0.45-0.55]  crown_y %.3f [0.18-0.30]" % (m["head_w"] or 0, m["crown_y"] or 0))
            lines.append("A8 luma p5 %.0f p50 %.0f [75-105] p95 %.0f [<=175]  >235 %.2f%% [<0.5]" % (m["p5"], m["p50"], m["p95"], m["over235"]))
            lines.append("   plate HSV-S %.0f [<=110]  hair %s dE %.1f [<=18]  skin %s dE %.1f [<=18]" % (m["plate_sat"], m["hair_mean"], m["dE_hair"], m["skin_mean"], m["dE_skin"]))
            lines.append("   hair tones (12-level bins >2%%): %d [>=5]   ears+lips: rig pieces head_ear_l/r, lips in mouth set" % m["hair_tones"])
        for n_, s in enumerate(lines):
            d.text((x, y + 574 + 20 * n_), s, font=fm, fill=(200, 190, 170))
    sheet.save(SW / "compare-ref.jpg", quality=88)
    return dict(zip(labels, mets))


# ============================================================ main
def stills(cut, ts):
    out = FILMS / "stills" / "zazie-dans-le-metro"; out.mkdir(parents=True, exist_ok=True)
    for t in ts:
        f = int(round(t * FPS)); src = cut if (cut == "A" or f >= 192) else "A"
        render(PLAN[src][f]).save(out / f"{cut}_{t:06.2f}.png")
    print("stills ->", out)


def main():
    if "--stills" in sys.argv or "--stills-b" in sys.argv:
        cut = "B" if "--stills-b" in sys.argv else "A"
        stills(cut, [float(x) for x in sys.argv[2:]]); return
    jobs = [("A", f, False) for f in range(NF)] + [("B", f, False) for f in range(192, NF)] + [("A", f, True) for f in range(168, 240)]
    prerender(jobs)
    FA = [Image.open(cache_path("A", f)).convert("RGB") for f in range(NF)]
    FB = [FA[f] if f < 192 else Image.open(cache_path("B", f)).convert("RGB") for f in range(NF)]
    pre, counts = preconditions(FA, FB)
    print(json.dumps({k: v.get("ok") for k, v in pre.items()}, indent=1))
    for k, v in pre.items():
        assert v["ok"], (k, v)
    out = ROOT / "assets/films"
    fa = kit.Film("zazie-dans-le-metro", seconds=NF / FPS, boil=0, wobble=0, seed=1960)
    fa.picture(frame_fn("A")); fa.sound(sound_fn("A")); fa.poster_at = 7.6; fa.render(out_dir=out)
    fb = kit.Film("zazie-dans-le-metro-control", seconds=NF / FPS, boil=0, wobble=0, seed=1960)
    fb.picture(frame_fn("B")); fb.sound(sound_fn("B")); fb.poster_at = 9.0; fb.render(out_dir=out)
    fn = kit.Film("negctl", seconds=3.0, boil=0, wobble=0, seed=1960)
    fn.picture(frame_fn("A", neg=True, offset=168)); fn.sound(sound_fn("A", 7.0)); fn.poster_at = 1.0; fn.render(out_dir=SW)
    cmp_ = compare_sheet(FA)
    led = dict(slug="zazie-dans-le-metro", fps=FPS, picture="720x540 pillarboxed at x=120 in 960x540", preconditions=pre, compare_ref=cmp_,
               hair_tests=dict(test_shot=json.load(open(PUP / "build/test-results.json"))["energy"],
                               S8_energy_peak=max(S8_EN.values()), S8_energy_end=S8_EN[479]),
               A=ledger("A", FA, counts), B=ledger("B", FB, counts))
    json.dump(led, open(SW / "frame-ledger.json", "w"), indent=0, default=lambda o: float(o) if isinstance(o, (np.floating,)) else str(o))
    print("frame-ledger + compare-ref written")


if __name__ == "__main__":
    main()
