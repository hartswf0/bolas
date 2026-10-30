"""A CLOCKWORK PINK, proof 0: the lid clamp, undone by a hand.

Original paper-cutout passage rendered from code. No film frames are used; the
Ludovico sequence is consulted as reference only (see README.md).

Every piece is a rigid card polygon with a fixed ragged edge and a lifted
shadow. Poses are keyed by hand below and sampled on twos (12 drawings a
second on a 24 fps timeline), the way a tabletop cutout is moved and exposed.

    python3 tools/clockwork_pink/proof0.py OUT_DIR
"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS, SR = 960, 540, 24, 48000
CX, CY = 480, 235            # eye centre, high enough to leave room for the hand
RX, HMAX = 230, 105          # almond half-width, full lid opening
N_FRAMES = 276               # 11.5 s

# ---- timeline (frames) --------------------------------------------------
SLIDE_IN = (12, 30)          # clamps slide to the lids
SPREAD = (30, 42)            # clamps prise the lids wide; lock at 42
GLARE = (42, 108)            # the projector's flicker
HAND_IN = (108, 144)         # a hand slides in and lands on the lower clamp
HOLD = (144, 180)            # nothing moves but the light
SWIVEL = (180, 204)          # the hand swivels the clamp off; upper clamp withdrawn
BLINK = (204, 228)           # first blink; a tear
POP = 228                    # bulb pops
CARD = 252                   # title card


def ramp(f, a, b):
    return min(1.0, max(0.0, (f - a) / (b - a)))


def ease(t):
    return t * t * (3 - 2 * t)


def pose(f):
    """Hand-keyed pose for frame f, held on twos."""
    k = f - f % 2
    p = {}
    # clamps: slide in from off-frame, then spread
    s = ease(ramp(k, *SLIDE_IN))
    spread = ease(ramp(k, *SPREAD))
    p["gap_up"] = 52 + 53 * spread
    p["gap_lo"] = 40 + 65 * spread
    p["clamp_up_y"] = (-140) * (1 - s) + (CY - p["gap_up"]) * s
    p["clamp_lo_y"] = (H + 140) * (1 - s) + (CY + p["gap_lo"]) * s
    # pupil contracts under the flicker, in stepped substitutions
    g = ramp(k, *GLARE)
    p["pupil"] = [34, 30, 26, 22, 19, 17][min(5, int(g * 6))]
    if k >= HAND_IN[0]:
        p["pupil"] = [17, 20, 24, 27, 30][min(4, int(ramp(k, HAND_IN[0], HOLD[1]) * 5))]
    # the hand
    h = ease(ramp(k, *HAND_IN))
    # the hand slides in along its own fingers and lands with the fingertips on the lower clamp bar
    p["hand_x"] = WRIST[0] - 420 * HAND_DIR[0] * (1 - h)
    p["hand_y"] = WRIST[1] - 420 * HAND_DIR[1] * (1 - h)
    sw = ease(ramp(k, *SWIVEL))
    p["swivel"] = 24 * sw                            # degrees, clockwise on screen
    p["gap_lo"] -= 65 * sw if k >= SWIVEL[0] else 0
    p["clamp_up_y"] -= 420 * sw
    p["gap_up"] -= 53 * sw
    # blink: substitution drawings open -> half -> shut -> half -> open
    if BLINK[0] <= k < BLINK[1]:
        seq = [1, .5, 0, 0, .5, 1]
        o = seq[min(5, (k - BLINK[0]) // 2)]
        p["gap_up"] *= o
        p["gap_lo"] *= o
    p["tear"] = ramp(k, BLINK[0] + 10, POP - 4) if k >= BLINK[0] + 10 else None
    # light: a hard projector beam, on or off per drawing, never a wash
    rng = np.random.default_rng(k)
    p["beam"] = bool(GLARE[0] <= k < HAND_IN[0] + 12 and rng.random() < 0.55)
    p["dark"] = 0.78 if GLARE[0] <= k < HAND_IN[0] + 12 else 1.0
    p["pink"] = 0.38 * ease(ramp(k, HAND_IN[0], SWIVEL[1]))
    p["level"] = 0.32 if k >= POP else 1.0
    p["card"] = k >= CARD
    return p


# ---- paper pieces -------------------------------------------------------
def densify(pts, step=6):
    out = []
    for i in range(len(pts)):
        a, b = np.array(pts[i], float), np.array(pts[(i + 1) % len(pts)], float)
        n = max(1, int(np.linalg.norm(b - a) / step))
        out += [a + (b - a) * j / n for j in range(n)]
    return np.array(out)


def ragged(pts, seed, amp=1.4):
    """A fixed cut edge: paper does not re-cut itself between frames."""
    d = densify(pts)
    rng = np.random.default_rng(seed)
    return d + rng.normal(0, amp, d.shape)


def ellipse(cx, cy, rx, ry, n=90):
    return [(cx + rx * math.cos(t), cy + ry * math.sin(t)) for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]


def rrect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


FACE = ragged(ellipse(CX, CY + 10, 340, 200), 1, 1.8)
ALMOND = [(CX + RX * u, CY - HMAX * (1 - u * u)) for u in np.linspace(-1, 1, 60)] + \
         [(CX + RX * u, CY + HMAX * (1 - u * u)) for u in np.linspace(1, -1, 60)]
ALMOND_R = ragged(ALMOND, 2, 1.0)
# speculum bar, local origin at the bar's lid edge centre; short arms to a screw knob are drawn
def speculum(sign, seed):
    """Bar, two short arms splayed outward, two screw knobs. sign -1 = upper, +1 = lower."""
    out = [ragged(rrect(-85, 0, 85, 16 * sign), seed)]
    for sx in (-1, 1):
        out.append(ragged([(sx * 66, 2 * sign), (sx * 78, 2 * sign), (sx * 108, 70 * sign), (sx * 96, 70 * sign)], seed + 2 + sx))
        out.append(ragged(ellipse(sx * 104, 80 * sign, 13, 13, 24), seed + 5 + sx, 0.8))
    return out


CLAMP_UP = speculum(-1, 3)
CLAMP_LO = speculum(1, 40)
CLAMP_COL = [(150, 150, 156)] + [(110, 110, 118), (82, 82, 90)] * 2   # bar, then arm and knob per side
# open flat hand, local origin at the wrist, fingers pointing along +x, spread so the gaps show
FINGERS = [(-39, 82), (-13, 112), (13, 104), (39, 90)]                # (centre y, length)
HAND = [ragged(rrect(-520, -50, 0, 50), 5, 1.8)]                     # sleeve
HAND += [ragged([(0, -44), (96, -52), (108, -36), (108, 50), (88, 56), (0, 46)], 6)]  # palm
def finger(dy, ln, r=9):
    tip = [(96 + ln - r + r * math.cos(a), dy + r * math.sin(a)) for a in np.linspace(-math.pi / 2, math.pi / 2, 9)]
    return [(96, dy - r)] + tip + [(96, dy + r)]


for i, (dy, ln) in enumerate(FINGERS):
    HAND += [ragged(finger(dy, ln), 10 + i)]
HAND += [ragged([(26, -42), (62, -100), (82, -92), (58, -36)], 20)]  # thumb
HAND_COL = [(58, 52, 60)] + [(238, 158, 168)] * 6
# charcoal on the finger pads: thin, low-contrast streaks along each finger, never dots
SMUDGES = [(96 + ln - 22, dy, 12, 3) for dy, ln in FINGERS[:3]]
NAILS = [(96 + ln - 10, dy, 6, 5) for dy, ln in FINGERS]
TEAR = ragged([(0, -12), (7, 2), (5, 9), (0, 11), (-5, 9), (-7, 2)], 30, 0.4)
HAND_SCALE = 1.4
REST_DEG = -32               # the hand's angle at rest: reaching up and to the right
LIFT = (7, 9)                # shadow offset: the card sits off the table


def rot(v, deg):
    a = math.radians(deg)
    return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a))


# key the rest pose backwards from the contact: middle fingertip on the lower clamp bar
CONTACT = (CX - 30, CY + HMAX + 9)
_t = rot((HAND_SCALE * (96 + FINGERS[1][1]), HAND_SCALE * FINGERS[1][0]), REST_DEG)
WRIST = (CONTACT[0] - _t[0], CONTACT[1] - _t[1])
HAND_DIR = rot((1, 0), REST_DEG)


def tips(p):
    """Screen positions of the four fingertips."""
    deg = REST_DEG + p["swivel"]
    out = []
    for dy, ln in FINGERS:
        v = rot((HAND_SCALE * (96 + ln), HAND_SCALE * dy), deg)
        out.append((p["hand_x"] + v[0], p["hand_y"] + v[1]))
    return out


def xf(pts, dx, dy, deg=0.0, piv=(0, 0), scale=1.0):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    q = np.asarray(pts, float) * scale - piv
    q = np.stack([q[:, 0] * c - q[:, 1] * s, q[:, 0] * s + q[:, 1] * c], 1) + piv
    return [tuple(v) for v in q + (dx, dy)]


def placed(p):
    """All pieces in screen space, back to front: (name, polygon, colour)."""
    hand_deg = REST_DEG + p["swivel"]
    wx, wy = p["hand_x"], p["hand_y"]
    out = []
    for i, poly in enumerate(CLAMP_UP):
        out.append(("clamp_up" if i == 0 else "clamp_part", xf(poly, CX, p["clamp_up_y"]), CLAMP_COL[i]))
    # the lower clamp rides the fingers once the hand has it, pivoting about the wrist
    for i, poly in enumerate(CLAMP_LO):
        if p["swivel"] > 0:
            q = xf(poly, CX, CY + HMAX, p["swivel"], (wx - CX, wy - CY - HMAX))
        else:
            q = xf(poly, CX, p["clamp_lo_y"])
        out.append(("clamp_lo" if i == 0 else "clamp_part", q, CLAMP_COL[i]))
    for poly, col in zip(HAND, HAND_COL):
        out.append(("hand", xf(poly, wx, wy, hand_deg, scale=HAND_SCALE), col))
    return out, (wx, wy, hand_deg)


# ---- drawing ------------------------------------------------------------
def font(size):
    for f in ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def paper_ground(seed):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 7, (H // 3, W // 3))
    n = np.array(Image.fromarray(n.astype(np.float32), "F").resize((W, H), Image.BILINEAR))
    return n


GRAIN = [paper_ground(s) for s in range(4)]
_yy, _xx = np.mgrid[0:H, 0:W]
SPOT = ((_xx - CX) / 300) ** 2 + ((_yy - CY) / 175) ** 2 < 1          # hard edge, no falloff
TEAR_AT = (CX + RX * 0.62, CY + 44)                                     # outer corner, clear of the hand
TEAR_RUN = 130
TABLE = paper_ground(99) * 0.8


def draw_frame(f):
    p = pose(f)
    if p["card"]:
        return title_card(f)
    bg = np.array([200, 188, 166], float)                 # clinical card
    img = Image.new("RGB", (W, H), tuple(int(v) for v in bg))
    pieces, (wx, wy, hdeg) = placed(p)
    # shadows: one layer, one blur per frame
    sh = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(sh)
    sd.polygon([tuple(v + LIFT) for v in FACE], fill=110)
    for _, poly, _ in pieces:
        sd.polygon([(x + LIFT[0], y + LIFT[1]) for x, y in poly], fill=130)
    sh = sh.filter(ImageFilter.GaussianBlur(6))
    img.paste((40, 30, 30), mask=sh)
    d = ImageDraw.Draw(img)
    d.polygon([tuple(v) for v in FACE], fill=(226, 186, 152))
    # eye: white, iris, pupil, lids, all masked to the almond
    eye = Image.new("RGB", (W, H), (244, 240, 230))
    e = ImageDraw.Draw(eye)
    for cx, cy, r, col in [(CX, CY, 80, (60, 98, 128)), (CX, CY, p["pupil"], (16, 14, 18))]:
        e.polygon([tuple(v) for v in ragged(ellipse(cx, cy, r, r, 60), int(r), 0.6)], fill=col)
    e.ellipse((CX + 22, CY - 34, CX + 38, CY - 18), fill=(250, 250, 250))
    lid = (214, 168, 136)
    up = [(CX + RX * u, CY - p["gap_up"] * (1 - u * u)) for u in np.linspace(-1.1, 1.1, 50)]
    lo = [(CX + RX * u, CY + p["gap_lo"] * (1 - u * u)) for u in np.linspace(-1.1, 1.1, 50)]
    e.polygon(up + [(CX + 260, CY - 140), (CX - 260, CY - 140)], fill=lid)
    e.polygon(lo + [(CX + 260, CY + 140), (CX - 260, CY + 140)], fill=lid)
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon([tuple(v) for v in ALMOND_R], fill=255)
    img.paste(eye, mask=m)
    d.line(up[5:-5], fill=(70, 40, 36), width=5)
    d.line(lo[5:-5], fill=(110, 70, 60), width=3)
    if p["tear"] is not None:
        tx, ty0 = TEAR_AT
        ty = ty0 + TEAR_RUN * p["tear"]
        d.line([(tx, ty0), (tx + 2, ty - 14)], fill=(244, 214, 214), width=5)       # the wet track
        d.polygon([(x * 2.4 + tx, y * 2.4 + ty) for x, y in TEAR], fill=(252, 236, 240), outline=(150, 96, 112))
    for name, poly, col in pieces:
        d.polygon(poly, fill=col)
    # nails and charcoal ride the hand
    for (sx, sy, rx, ry), col in [(n, (250, 214, 216)) for n in NAILS] + [(s_, (196, 116, 132)) for s_ in SMUDGES]:
        q = xf(np.array(ellipse(sx, sy, rx, ry, 20)), wx, wy, hdeg, scale=HAND_SCALE)
        d.polygon(q, fill=col)
    a = np.asarray(img, float)
    # light: a hard-edged projector spot, on or off per drawing; then the pink; then the dark after the pop
    if p["beam"]:
        a = np.where(SPOT[..., None], a + (255 - a) * 0.62, a * 0.5)
    else:
        a = a * p["dark"]
    a = a * (1 - p["pink"]) + np.array([236, 128, 156]) * p["pink"]
    a = a + TABLE[..., None] + GRAIN[(f // 2) % 4][..., None]
    if p["level"] < 1:
        yy, xx = np.mgrid[0:H, 0:W]
        v = np.exp(-(((xx - CX) / 420) ** 2 + ((yy - CY - 60) / 300) ** 2))
        a = a * (p["level"] * (0.35 + 0.65 * v))[..., None]
    return np.clip(a, 0, 255).astype(np.uint8)


def title_card(f):
    img = Image.new("RGB", (W, H), (14, 10, 12))
    d = ImageDraw.Draw(img)
    for txt, size, y, col in [("A CLOCKWORK PINK", 54, 220, (236, 140, 166)),
                              ("proof 0", 20, 300, (190, 180, 176))]:
        fnt = font(size)
        w = d.textlength(txt, font=fnt)
        d.text(((W - w) / 2, y), txt, font=fnt, fill=col)
    return np.asarray(img)


# ---- sound --------------------------------------------------------------
def sound():
    n = int(N_FRAMES / FPS * SR)
    out = np.zeros(n)
    rng = np.random.default_rng(7)
    t = np.arange(n) / SR
    sec = lambda fr: int(fr / FPS * SR)

    def put(sig, at):
        a = sec(at) if isinstance(at, int) else int(at * SR)
        b = min(n, a + len(sig))
        out[a:b] += sig[: b - a]

    def burst(ms, amp, decay, tone=None):
        m = int(ms / 1000 * SR)
        tt = np.arange(m) / SR
        s = rng.normal(0, 1, m) if tone is None else sum(np.sin(2 * np.pi * fq * tt) for fq in tone)
        return amp * s * np.exp(-tt * decay)

    # projector gate: 24 clicks a second, plus mains hum, until the pop
    end = sec(POP)
    hum = 0.03 * np.sin(2 * np.pi * 50 * t) + 0.015 * np.sin(2 * np.pi * 100 * t)
    out[:end] += hum[:end]
    for i in range(int(POP / FPS * 24)):
        put(burst(6, 0.09 * (0.7 + 0.3 * rng.random()), 900), i / 24)
    # clamp lock: two small metal clicks
    put(burst(120, 0.25, 40, (2200, 3130)), SPREAD[1])
    put(burst(90, 0.18, 50, (2410, 3370)), SPREAD[1] + 2)
    # flicker ticks
    for k in range(GLARE[0], HAND_IN[0] + 24, 2):
        put(burst(15, 0.05, 300), k)
    # paper on paper as the hand slides and swivels
    for a, b in (HAND_IN, SWIVEL):
        m = sec(b) - sec(a)
        s = np.convolve(rng.normal(0, 1, m), np.ones(40) / 40, "same") * 0.35
        put(s * np.sin(np.linspace(0, np.pi, m)), a)
    # hummed: first phrase of the Ode to Joy (public domain), a voice not a machine
    notes = [64, 64, 65, 67, 67, 65, 64, 62, 60, 60, 62, 64, 64, 62, 62]
    beat = 0.3
    t0 = 120 / FPS
    for i, m in enumerate(notes):
        dur = beat * (1.5 if i == 12 else 0.5 if i == 13 else 2 if i == 14 else 1)
        fq = 440 * 2 ** ((m - 69) / 12)
        k = int(dur * SR)
        tt = np.arange(k) / SR
        vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * tt)
        ph = 2 * np.pi * fq * np.cumsum(vib) / SR
        env = np.minimum(1, tt / 0.06) * np.minimum(1, (dur - tt) / 0.08)
        put(0.12 * env * (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)), t0)
        t0 += dur
        if t0 > POP / FPS - 0.05:
            break
    # cut the hum dead at the pop, then the bulb
    out[sec(POP):] *= 0.0
    put(burst(250, 0.6, 25) + burst(250, 0.4, 12, (70,)), POP)
    out[sec(POP):sec(CARD)] += 0.004 * rng.normal(0, 1, sec(CARD) - sec(POP))
    out = out / max(1e-9, np.abs(out).max()) * 0.85
    return out


def main(od):
    os.makedirs(od, exist_ok=True)
    wav = os.path.join(od, "proof0.wav")
    s = (sound() * 32767).astype(np.int16)
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(s.tobytes())
    mp4 = os.path.join(od, "clockwork-pink-proof0.mp4")
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                           "-c:a", "aac", "-b:a", "160k", "-shortest", mp4], stdin=subprocess.PIPE)
    for f in range(N_FRAMES):
        ff.stdin.write(draw_frame(f).tobytes())
    ff.stdin.close()
    ff.wait()
    print(mp4)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "out")
