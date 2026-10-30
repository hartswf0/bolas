"""PINK EYE, version 0: the Ludovico footage chopped into torn-paper windows, the clip's own sound cut with it, and the
eye inflamed in cut paper.

Conjunctivitis: when the small blood vessels of the eye are irritated and swell, they become visible. Here every eye-drop
the attendant gives, the institution's care so that the watching can go on, pins another paper vessel onto the eye, until
the irritation has made the whole structure visible.

  A  Exposure   0-14 s   archive cuts pinned on twos and left to pile up; the sound follows the newest window
  B  Drops     14-28 s   the dropper and the woman doctor's voice; each drop is a vessel
  C  Pink eye  28-40 s   the eye pushed in, the vessels everywhere, the other windows torn away
  slot for archival voices: C is left to room tone and tearing until they are cleared (see README)

The source film is under copyright. This script reads a local copy and writes a local film; neither the footage nor the
render is committed or published.

    python3 tools/pink_eye/pink_eye.py CLIP.mp4 OUT_DIR
"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS, SR = 960, 540, 24, 48000
PAPER = (214, 205, 188)
VESSEL = (176, 28, 52)
PINK = np.array([236, 128, 156], np.float32)

# real seconds in the clip, checked against half-second strips at each cut
SEGS = {
    "ruins": (84.0, 89.0), "alex": (96.0, 104.0), "emblem": (121.0, 124.9), "eye": (125.0, 129.9),
    "scream": (130.0, 137.0), "dropper": (156.0, 163.9), "doctor": (164.0, 167.9), "brodsky": (206.0, 209.0),
    "dropper2": (214.0, 222.0),
}
A_END, B_END, C_END, END = 14.0, 28.0, 40.0, 44.0
DROPS = [15.5, 17.6, 19.4, 21.0, 22.4, 23.6, 24.7, 25.6, 26.4, 27.1]


def ragged(pts, seed, amp=1.6, step=7):
    out = []
    for i in range(len(pts)):
        a, b = np.array(pts[i], float), np.array(pts[(i + 1) % len(pts)], float)
        n = max(1, int(np.linalg.norm(b - a) / step))
        out += [a + (b - a) * j / n for j in range(n)]
    return np.array(out) + np.random.default_rng(seed).normal(0, amp, (len(out), 2))


def rect(w, h):
    return [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]


def almond(w, h, n=60):
    up = [(w / 2 * u, -h / 2 * (1 - u * u)) for u in np.linspace(-1, 1, n)]
    return up + [(x, -y) for x, y in up[::-1]]


def place(poly, cx, cy, deg, s=1.0):
    a = math.radians(deg); c, sn = math.cos(a), math.sin(a)
    q = np.asarray(poly) * s
    return [(cx + x * c - y * sn, cy + x * sn + y * c) for x, y in q]


# ---- the score: torn-paper windows -------------------------------------
def schedule():
    """(t_in, t_out, seg, cx, cy, w, h, deg, shape, seed)"""
    rng = np.random.default_rng(11)
    order = ["ruins", "alex", "eye", "emblem", "scream", "alex", "eye", "ruins", "scream", "eye", "emblem", "alex"]
    wins, t, d = [], 0.0, 1.5
    for i, seg in enumerate(order):
        if t >= A_END - 0.3:
            break
        cx, cy = rng.uniform(170, W - 170), rng.uniform(120, H - 120)
        w = rng.uniform(300, 420); h = w * 9 / 16
        shape = "almond" if seg == "eye" else "rect"
        out = C_END - 0.6 * (len(order) - i)                 # torn away in C, oldest last
        wins.append((t, out, seg, cx, cy, w, h, rng.uniform(-9, 9), shape, 100 + i))
        t, d = t + d, max(0.7, d * 0.9)
    wins.append((A_END, B_END, "dropper", 250, 170, 380, 214, -4, "rect", 300))
    wins.append((A_END + 0.5, B_END, "doctor", 720, 380, 330, 186, 5, "rect", 301))
    wins.append((19.0, B_END, "dropper2", 230, 400, 300, 169, 3, "rect", 302))
    wins.append((A_END + 1.0, END, "eye", W / 2, H / 2, 520, 300, 0, "almond", 400))   # the eye that will inflame
    return wins


WINS = schedule()


def vessels(n, seed=5):
    """paper vessels: tapering branches from the almond's rim toward the iris"""
    rng = np.random.default_rng(seed); out = []
    for k in range(n):
        side = rng.choice([-1, 1]); u = rng.uniform(0.35, 0.95) * side
        x, y = 260 * u, rng.choice([-1, 1]) * 150 * (1 - u * u) * rng.uniform(0.55, 0.9)
        ang = math.atan2(-y, -x) + rng.normal(0, 0.5); wdt = rng.uniform(3.5, 6.5)
        pts = [(x, y)]
        for s in range(rng.integers(5, 9)):
            ang += rng.normal(0, 0.45); L = rng.uniform(12, 24)
            x, y = x + L * math.cos(ang), y + L * math.sin(ang); pts.append((x, y))
        left, right = [], []
        for i, (px, py) in enumerate(pts):
            j = min(i + 1, len(pts) - 1); jj = max(i - 1, 0)
            dx, dy = pts[j][0] - pts[jj][0], pts[j][1] - pts[jj][1]; nrm = math.hypot(dx, dy) or 1
            ww = wdt * (1 - i / len(pts)) + 0.6
            left.append((px - dy / nrm * ww, py + dx / nrm * ww)); right.append((px + dy / nrm * ww, py - dx / nrm * ww))
        out.append(ragged(left + right[::-1], 900 + k, 0.5, 4))
    return out


VESSELS = vessels(46)


def vessel_count(t):
    if t < DROPS[0]:
        return 0
    if t < A_END + 0 or t < B_END:
        return 2 * sum(1 for d in DROPS if d <= t)
    return min(len(VESSELS), 20 + int((t - B_END) * 3.5))   # in C they come by themselves


def eye_scale(t):
    if t < B_END:
        return 1.0
    return [1.0, 1.08, 1.18, 1.3, 1.42, 1.55][min(5, int((t - B_END) / 2))]   # pushed in on stepped pins


# ---- footage ------------------------------------------------------------
def load(clip, seg):
    a, b = SEGS[seg]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a), "-i", clip, "-t", str(b - a), "-vf", "fps=12",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, 360, 640, 3)


def frame(fr, t, t_in):
    k = int((t - t_in) * 12); n = len(fr)
    k = k % (2 * n - 2); k = k if k < n else 2 * n - 2 - k
    return fr[k]


def font(size, bold=False):
    f = "/usr/share/fonts/truetype/dejavu/DejaVuSerif%s.ttf" % ("-Bold" if bold else "")
    return ImageFont.truetype(f, size) if os.path.exists(f) else ImageFont.load_default()


def draw(clips, f):
    t = f / FPS; tq = t - (t % (2 / FPS))                  # on twos
    if t >= C_END:
        img = Image.new("RGB", (W, H), (16, 8, 10)); d = ImageDraw.Draw(img)
        d.text((W / 2, H / 2 - 10), "PINK EYE", font=font(64, True), fill=(236, 120, 150), anchor="mm")
        d.text((W / 2, H / 2 + 46), "version 0 · archive voices to come", font=font(16), fill=(160, 150, 150), anchor="mm")
        return np.asarray(img)
    rng = np.random.default_rng(int(tq * 12))
    img = Image.new("RGB", (W, H), PAPER)
    live = [w for w in WINS if w[0] <= tq < w[1]]
    for (t_in, t_out, seg, cx, cy, w, h, deg, shape, seed) in live:
        s = eye_scale(tq) if seed == 400 else 1.0
        poly = place(ragged(almond(w, h) if shape == "almond" else rect(w, h), seed), cx, cy, deg, s)
        sh = Image.new("L", (W, H), 0); ImageDraw.Draw(sh).polygon([(x + 6, y + 8) for x, y in poly], fill=120)
        img.paste((40, 30, 30), mask=sh.filter(ImageFilter.GaussianBlur(5)))
        pic = Image.fromarray(frame(clips[seg], tq, t_in))
        bw, bh = int(w * s * 1.15), int(h * s * 1.15)
        pic = pic.resize((bw, bh), Image.BILINEAR).rotate(-deg, expand=True, resample=Image.BILINEAR)
        layer = Image.new("RGB", (W, H)); layer.paste(pic, (int(cx - pic.width / 2), int(cy - pic.height / 2)))
        m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(poly, fill=255)
        img.paste(layer, mask=m)
        ImageDraw.Draw(img).line(poly + [poly[0]], fill=(246, 240, 228), width=3)      # the torn white edge
        if seed == 400:
            d = ImageDraw.Draw(img)
            for v in VESSELS[:vessel_count(tq)]:
                d.polygon(place(v, cx, cy, deg, s), fill=VESSEL)
    if B_END <= tq < C_END:                                   # the medical fact, as a paper slip
        d = ImageDraw.Draw(img); x0, y0 = 60, 470
        d.polygon(place(ragged(rect(560, 44), 77), x0 + 280, y0, -1.5), fill=(244, 238, 226))
        d.text((x0 + 280, y0), "irritated, the small vessels of the eye become visible", font=font(17), fill=(60, 40, 40), anchor="mm")
    a = np.asarray(img, np.float32)
    pink = 0.0 if tq < A_END else 0.18 * (tq - A_END) / (B_END - A_END) if tq < B_END else 0.18 + 0.27 * (tq - B_END) / (C_END - B_END)
    a = a * (1 - pink) + PINK * pink
    a += rng.normal(0, 5, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1)
    if tq >= C_END - 0.8:
        a *= max(0.0, (C_END - tq) / 0.8)
    return np.clip(a, 0, 255).astype(np.uint8)


# ---- sound: the clip's own, cut on the same cuts ------------------------
def sound(clip):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", clip, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True).stdout
    src = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    n = int(END * SR); out = np.zeros(n); rng = np.random.default_rng(4)
    starts = sorted({w[0] for w in WINS})
    # the newest window speaks until the next one arrives; in B the doctor holds the floor
    voice = [(w[0], w[2]) for w in WINS if w[0] < A_END] + [(A_END + 0.5, "doctor")]
    for i, (t0, seg) in enumerate(voice):
        t1 = voice[i + 1][0] if i + 1 < len(voice) else B_END
        a = int(SEGS[seg][0] * SR); m = int((t1 - t0) * SR)
        piece = src[a:a + m].copy()
        if len(piece) < m:
            piece = np.pad(piece, (0, m - len(piece)))
        fade = min(len(piece) // 2, 240); piece[:fade] *= np.linspace(0, 1, fade); piece[-fade:] *= np.linspace(1, 0, fade)
        out[int(t0 * SR):int(t0 * SR) + m] += piece
    for t0 in starts:                                          # a pin goes in
        k = int(0.04 * SR); out[int(t0 * SR):int(t0 * SR) + k] += 0.25 * rng.normal(0, 1, k) * np.exp(-np.arange(k) / 300)
    for d in DROPS:                                            # a drop: a soft high plink
        k = int(0.25 * SR); x = np.arange(k) / SR
        out[int(d * SR):int(d * SR) + k] += 0.12 * np.sin(2 * np.pi * (1800 - 900 * x) * x) * np.exp(-x * 18)
    # C: room tone and tearing paper, leaving the floor open for the archive voices
    c0, c1 = int(B_END * SR), int(C_END * SR)
    out[c0:c1] += 0.006 * rng.normal(0, 1, c1 - c0)
    for w in WINS:
        if B_END <= w[1] < C_END:
            k = int(0.35 * SR); noise = np.convolve(rng.normal(0, 1, k), np.ones(6) / 6, "same")
            env = np.abs(np.sin(np.linspace(0, 40, k))) * np.exp(-np.linspace(0, 4, k))
            out[int(w[1] * SR):int(w[1] * SR) + k] += 0.3 * noise * env
    return out / max(1e-9, np.abs(out).max()) * 0.85


def main(clip, od):
    os.makedirs(od, exist_ok=True)
    clips = {s: load(clip, s) for s in SEGS}
    wav = os.path.join(od, "pink_eye.wav"); raw = os.path.join(od, "picture.mp4"); vid = os.path.join(od, "pink-eye-v0.mp4")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((sound(clip) * 32767).astype(np.int16).tobytes())
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", raw], stdin=subprocess.PIPE)
    for f in range(int(END * FPS)):
        ff.stdin.write(draw(clips, f).tobytes())
    ff.stdin.close(); ff.wait()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                    "-movflags", "+faststart", "-shortest", vid], check=True)
    print(vid)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
