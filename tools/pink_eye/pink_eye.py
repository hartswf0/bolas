"""PINK EYE, version 1: the Ludovico footage dissolved into soft paper, with a new soundscape.

Conjunctivitis: when the small blood vessels of the eye are irritated and swell, they become visible. In the Ludovico
sequence an attendant keeps dropping saline into Alex's clamped eyes, the institution's care so that the watching can go
on. Here every drop lets a vessel grow across the eye, until the irritation has made the whole structure visible.

Version 0 cut, pinned and chopped. This version blends: footage layers drift slowly and dissolve through feathered paper
edges, nothing cuts, the vessels grow like ink, and the sound is new (synthesized), with no cut-up clip audio.

  A  Exposure   0-16 s   archive layers surface and sink into one another; the eye rises out of them
  B  Drops     16-32 s   the dropper and the doctor drift over the eye; each drop starts a vessel
  C  Pink eye  32-44 s   the vessels spread, the paper flushes pink, the other layers dissolve away
  room is left in C for archival voices (see README)

The source film is under copyright. This script reads a local copy and writes a local film; neither is committed or
published.

    python3 tools/pink_eye/pink_eye.py CLIP.mp4 OUT_DIR
"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS, SR = 960, 540, 24, 48000
SW, SH = 560, 315                                          # footage is held at this size
PAPER = np.array([216, 207, 190], np.float32)
VESSEL = np.array([168, 26, 50], np.float32)
PINK = np.array([234, 140, 164], np.float32)

# real seconds in the clip, checked against half-second strips at each cut
SEGS = {
    "ruins": (84.0, 89.0), "alex": (96.0, 104.0), "emblem": (121.0, 124.9), "eye": (125.0, 129.9),
    "scream": (130.0, 137.0), "dropper": (156.0, 163.9), "doctor": (164.0, 167.9), "dropper2": (214.0, 222.0),
}
A_END, B_END, C_END, END = 16.0, 32.0, 44.0, 49.0
DROPS = [17.5, 19.5, 21.3, 23.0, 24.6, 26.0, 27.3, 28.5, 29.6, 30.6]

# layers: (seg, t_in, t_out, x, y, w, drift_x, drift_y, peak opacity); fades are long, nothing cuts
LAYERS = [
    ("ruins", 0.0, 9.0, 300, 190, 520, 6, 2, 0.85),
    ("alex", 2.5, 13.0, 640, 300, 500, -5, -3, 0.85),
    ("emblem", 5.5, 11.5, 360, 360, 430, 4, -4, 0.55),
    ("scream", 8.0, 17.0, 620, 200, 470, -4, 3, 0.75),
    ("dropper", 15.0, 31.0, 300, 200, 470, 5, 2, 0.75),
    ("doctor", 18.0, 30.0, 700, 360, 420, -4, -2, 0.7),
    ("dropper2", 23.0, 34.0, 270, 390, 400, 3, -3, 0.6),
]
EYE = ("eye", 4.0, END, W / 2, H / 2, 640)                 # the eye rises and stays
FADE = 3.0


def smooth(u):
    u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)


def env(t, a, b, fade=FADE):
    return smooth((t - a) / fade) * smooth((b - t) / fade)


def ragged(pts, seed, amp=2.0, step=7):
    out = []
    for i in range(len(pts)):
        a, b = np.array(pts[i], float), np.array(pts[(i + 1) % len(pts)], float)
        n = max(1, int(np.linalg.norm(b - a) / step))
        out += [a + (b - a) * j / n for j in range(n)]
    return np.array(out) + np.random.default_rng(seed).normal(0, amp, (len(out), 2))


def feather(w, h, seed, shape):
    """a torn-paper mask whose edge dissolves: the window has no hard line"""
    if shape == "almond":
        up = [(w / 2 + w / 2 * u, h / 2 - h / 2 * (1 - u * u)) for u in np.linspace(-1, 1, 60)]
        poly = up + [(x, h - y) for x, y in up[::-1]]
    else:                                                   # a rounded scrap, no corners left to read as a box
        poly = [(w / 2 + (w / 2 - 18) * math.copysign(abs(math.cos(a)) ** 0.5, math.cos(a)),
                 h / 2 + (h / 2 - 18) * math.copysign(abs(math.sin(a)) ** 0.5, math.sin(a))) for a in np.linspace(0, 2 * math.pi, 90, endpoint=False)]
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon([tuple(p) for p in ragged(poly, seed, 3.0)], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(min(w, h) * (0.07 if shape == "almond" else 0.13)))
    return np.asarray(m, np.float32)[..., None] / 255


# ---- footage ------------------------------------------------------------
def load(clip, seg):
    a, b = SEGS[seg]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a), "-i", clip, "-t", str(b - a), "-vf", f"fps=12,scale={SW}:{SH}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, SH, SW, 3)


def sample(fr, t, speed=0.5):
    """slow motion with the in-between frames blended, ping-pong so a held loop has no seam"""
    x = t * 12 * speed; n = len(fr); p = 2 * n - 2
    k0 = int(x) % p; k1 = (k0 + 1) % p; f = x - int(x)
    idx = lambda k: k if k < n else p - k
    return fr[idx(k0)].astype(np.float32) * (1 - f) + fr[idx(k1)].astype(np.float32) * f


def resized(img, w):
    h = int(w * SH / SW)
    return np.asarray(Image.fromarray(img.astype(np.uint8)).resize((w, h), Image.BILINEAR), np.float32)


# ---- vessels that grow like ink -----------------------------------------
def vessel_paths(n=40, seed=5):
    rng = np.random.default_rng(seed); out = []
    for _ in range(n):
        u = rng.uniform(0.35, 0.95) * rng.choice([-1, 1])
        x, y = 300 * u, rng.choice([-1, 1]) * 170 * (1 - u * u) * rng.uniform(0.55, 0.9)
        ang = math.atan2(-y, -x) + rng.normal(0, 0.5); pts = [(x, y)]
        for _ in range(rng.integers(6, 11)):
            ang += rng.normal(0, 0.4); L = rng.uniform(10, 20)
            x, y = x + L * math.cos(ang), y + L * math.sin(ang); pts.append((x, y))
        out.append((pts, rng.uniform(2.5, 5.0)))
    return out


PATHS = vessel_paths()


def vessel_starts():
    """each drop starts two vessels; in C the rest start on their own, closer and closer together"""
    s = []
    for d in DROPS:
        s += [d + 0.4, d + 0.9]
    t, gap = B_END, 0.9
    while len(s) < len(PATHS):
        s.append(t); t += gap; gap = max(0.25, gap * 0.85)
    return s


STARTS = vessel_starts()
GROW = 2.2                                                  # seconds for a vessel to reach its full length


def vessels_layer(t, cx, cy, scale):
    img = Image.new("L", (W, H), 0); d = ImageDraw.Draw(img)
    for (pts, wdt), s in zip(PATHS, STARTS):
        p = smooth((t - s) / GROW)
        if p <= 0:
            continue
        k = max(2, int(len(pts) * p) + 1); seg = pts[:k]
        q = [(cx + x * scale, cy + y * scale) for x, y in seg]
        for i in range(len(q) - 1):
            ww = max(1, int(wdt * scale * (1 - i / len(pts)) + 1))
            d.line([q[i], q[i + 1]], fill=230, width=ww)
    a = np.asarray(img.filter(ImageFilter.GaussianBlur(1.6)), np.float32) / 255
    return a[..., None]


def font(size, bold=False):
    f = "/usr/share/fonts/truetype/dejavu/DejaVuSerif%s.ttf" % ("-Bold" if bold else "")
    return ImageFont.truetype(f, size) if os.path.exists(f) else ImageFont.load_default()


def text_layer(txt, size, y, bold=False):
    img = Image.new("L", (W, H), 0)
    ImageDraw.Draw(img).text((W / 2, y), txt, font=font(size, bold), fill=255, anchor="mm")
    return np.asarray(img.filter(ImageFilter.GaussianBlur(0.6)), np.float32)[..., None] / 255


SLIP = None; TITLE = None; SUB = None
_r = np.random.default_rng(9)
GRAIN = [np.asarray(Image.fromarray((_r.normal(128, 9, (H // 3, W // 3))).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32)[..., None] - 128 for _ in range(6)]
FIBRE = np.asarray(Image.fromarray(_r.normal(128, 16, (H, W)).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur((0.4))).resize((W, H)), np.float32)[..., None] - 128


def draw(clips, masks, t):
    global SLIP, TITLE, SUB
    if SLIP is None:
        SLIP = text_layer("irritated, the small vessels of the eye become visible", 18, H - 46)
        TITLE = text_layer("PINK EYE", 66, H / 2 - 10, True)
        SUB = text_layer("archive voices to come", 16, H / 2 + 46)
    flush = smooth((t - A_END) / (C_END - A_END)) * 0.55                 # the paper slowly flushes pink
    a = PAPER * (1 - flush) + PINK * flush
    a = np.broadcast_to(a, (H, W, 3)).copy() + FIBRE * 0.35
    clear = 1 - smooth((t - B_END - 3) / 6)                              # in C the other layers dissolve away
    for (seg, t0, t1, x, y, w, dx, dy, op) in LAYERS:
        e = env(t, t0, t1) * op * clear
        if e <= 0.003:
            continue
        pic = resized(sample(clips[seg], t - t0), w); m = masks[seg]
        cx, cy = x + dx * (t - t0), y + dy * (t - t0)
        a = paste(a, pic, m, cx, cy, e)
    seg, t0, t1, x, y, w = EYE
    grow = 1 + 0.18 * smooth((t - B_END) / (C_END - B_END))              # one slow push-in, no steps
    e = env(t, t0, t1 + FADE, 5.0) * (0.55 + 0.4 * smooth((t - 10) / 8))
    pic = resized(sample(clips[seg], t - t0, 0.35), int(w * grow))
    a = paste(a, pic, mask_for(masks, int(w * grow)), x, y, e)
    v = vessels_layer(t, x, y, grow) * min(1.0, e * 1.4)
    a = a * (1 - v * 0.85) + VESSEL * v * 0.85
    s = env(t, B_END + 1, C_END - 1, 2.0) * 0.8
    if s > 0:
        a = a * (1 - SLIP * s) + np.array([70, 40, 44], np.float32) * SLIP * s
    a = a + GRAIN[int(t * 12) % len(GRAIN)]
    a = a + np.asarray(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(14)), np.float32) * 0.12
    out = np.clip(a / 1.12, 0, 255)
    dark = smooth((t - C_END) / 2.0)                                     # sink into the title
    out = out * (1 - dark) + np.array([18, 9, 12], np.float32) * dark
    if t > C_END + 1:
        k = smooth((t - C_END - 1) / 1.5) * smooth((END - t) / 1.0)
        out = out * (1 - TITLE * k) + np.array([236, 128, 156], np.float32) * TITLE * k
        out = out * (1 - SUB * k * 0.8) + np.array([170, 158, 160], np.float32) * SUB * k * 0.8
    return np.clip(out, 0, 255).astype(np.uint8)


def mask_for(masks, w):
    key = "eye@%d" % w
    if key not in masks:
        masks[key] = feather(w, int(w * SH / SW), 400, "almond")
    return masks[key]


def paste(a, pic, m, cx, cy, e):
    h, w = pic.shape[:2]; x0, y0 = int(cx - w / 2), int(cy - h / 2)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb:
        return a
    p = pic[ya - y0:yb - y0, xa - x0:xb - x0]; mm = m[ya - y0:yb - y0, xa - x0:xb - x0] * e
    region = a[ya:yb, xa:xb]
    # footage is laid on paper like a print: multiplied into the fibre, then lifted toward its own light
    printed = region * (p / 255) * 0.55 + p * 0.45
    a[ya:yb, xa:xb] = region * (1 - mm) + printed * mm
    return a


# ---- a new soundscape ----------------------------------------------------
def soundscape():
    n = int(END * SR); t = np.arange(n) / SR; rng = np.random.default_rng(12)

    def lowpass(x, cut):
        X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
        return np.fft.irfft(X / (1 + (f / cut) ** 4), len(x))

    def sm(a, b):
        return np.clip((t - a) / (b - a), 0, 1) ** 2 * (3 - 2 * np.clip((t - a) / (b - a), 0, 1))

    inflame = sm(A_END, C_END)                                            # rises through B and C
    # the room: a low breathing hush
    bed = lowpass(rng.normal(0, 1, n), 260) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * t) ** 2)
    out = 0.35 * bed / np.abs(bed).max()
    # the body: a soft drone that thickens and slowly detunes as the eye inflames
    for f0, g in ((55.0, 1.0), (82.4, 0.6), (110.0, 0.35)):
        out += 0.05 * g * np.sin(2 * np.pi * f0 * t + 2 * np.pi * 0.6 * inflame * t * (f0 / 110)) * (0.6 + 0.4 * inflame)
    # a pulse, slow and soft, that fades out as the pink arrives
    beat = 1.05; k = int(0.18 * SR); x = np.arange(k) / SR
    thump = np.sin(2 * np.pi * 48 * x) * np.exp(-x * 22)
    tb = 1.0
    while tb < C_END + 2:
        gain = 0.22 * (1 - 0.8 * smooth((tb - B_END) / 12))
        for off, gg in ((0, 1.0), (0.22, 0.55)):
            a = int((tb + off) * SR); out[a:a + k] += gain * gg * thump[: max(0, min(k, n - a))]
        tb += beat; beat *= 1.006
    # glass: an inharmonic tone, wine-glass partials, that swells with the irritation
    glass = sum(g * np.sin(2 * np.pi * 660 * r * t + r) for r, g in ((1, 1), (2.32, 0.5), (4.25, 0.25), (6.63, 0.12)))
    out += 0.05 * glass * (0.15 + 0.85 * inflame) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.23 * t))
    # drops: a bright plink that falls in pitch
    for d in DROPS:
        k = int(0.6 * SR); x = np.arange(k) / SR
        plink = np.sin(2 * np.pi * (2100 * np.exp(-x * 6) + 700) * x) * np.exp(-x * 9)
        a = int(d * SR); out[a:a + k] += 0.22 * plink
    # the end: everything but one pure note falls away
    tail = sm(C_END, C_END + 2.5)
    out = out * (1 - tail) + 0.08 * np.sin(2 * np.pi * 660 * t) * tail * (1 - sm(END - 2.5, END))
    # one shared space: a long, dark reverb
    L = int(3.2 * SR); ir = rng.normal(0, 1, L) * np.exp(-np.arange(L) / SR * 2.2); ir = lowpass(ir, 3500); ir /= np.abs(ir).sum() / 6
    m = 1 << int(np.ceil(np.log2(n + L)))
    wet = np.fft.irfft(np.fft.rfft(out, m) * np.fft.rfft(ir, m), m)[:n]
    mix = 0.65 * out + 0.35 * wet / max(1e-9, np.abs(wet).max()) * np.abs(out).max()
    fade = np.minimum(1, t / 2.0)
    return mix * fade / max(1e-9, np.abs(mix).max()) * 0.8


def main(clip, od):
    os.makedirs(od, exist_ok=True)
    clips = {s: load(clip, s) for s in SEGS}
    masks = {seg: feather(w, int(w * SH / SW), 100 + i, "rect") for i, (seg, _, _, _, _, w, _, _, _) in enumerate(LAYERS)}
    wav = os.path.join(od, "pink_eye.wav"); raw = os.path.join(od, "picture.mp4"); vid = os.path.join(od, "pink-eye-v1.mp4")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((soundscape() * 32767).astype(np.int16).tobytes())
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "21", raw], stdin=subprocess.PIPE)
    for f in range(int(END * FPS)):
        ff.stdin.write(draw(clips, masks, f / FPS).tobytes())
    ff.stdin.close(); ff.wait()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                    "-movflags", "+faststart", "-shortest", vid], check=True)
    print(vid)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
