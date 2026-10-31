"""THE PAST UNDER ANOTHER LIGHT, luminous cut: one continuous, full-frame, bright minute.

The worktable version was dark (61% of every frame near black) and its picture filled a quarter of the screen. Its sound
was clicks. This cut keeps the ideas and makes them watchable. It is full frame, lifted out of the dark, joined only by long
dissolves, and set to a slow chord progression.

  0-10 s   the attendant's reach with the dropper, slowed, dissolves into a public-domain hand lifting a lantern
  10-26 s  the two reaches side by side, then merged into one image: his reach carries the light (after Barbara Hammer)
  26-46 s  the woman doctor held almost still, with words that do not agree with her picture (after Trinh, Citron)
  46-60 s  her face gives way to the lantern's light, then to white, then the title

The clamped eye and the screaming never appear. The Ludovico footage is under copyright; this reads a local copy and
writes a local film.

    python3 tools/pink_eye/luminous.py CLIP.mp4 SHOTS_DIR OUT_DIR
"""
import os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import under_another_light as U                              # shared loaders and easing

W, H, FPS, SR, END = 960, 540, 24, 48000, 60.0
WORDS = [(28.5, 34.5, "She is the only woman in this room."),
         (35.5, 40.5, "She watches him watch."),
         (41.0, 46.5, "The film gives her a close-up. Not a question.")]
sm, env = U.smooth, U.env
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
_rng = np.random.default_rng(2)
GRAIN = [_rng.normal(0, 3.5, (H, W, 1)).astype(np.float32) for _ in range(8)]


def full(img, z=1.0, fx=0.5, fy=0.45):
    """fill the frame; crop for zoom and upscale softly so 360p reads as film rather than as blur"""
    h, w = img.shape[:2]; cw, ch = w / z, h / z; x0, y0 = (w - cw) * fx, (h - ch) * fy
    return np.asarray(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch)), np.float32)


def grade(a, t):
    """open the shadows into plum and warm the highlights, with a little bloom and fine grain"""
    x = np.clip(a / 255, 0, 1) ** 0.78
    x = x * np.array([1.02, 0.95, 0.93]) + (1 - x) * np.array([0.10, 0.04, 0.08])
    x = x + np.asarray(Image.fromarray((x * 255).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(18)), np.float32) / 255 * 0.22
    return np.clip(x / 1.12 * 255 + GRAIN[int(t * 12) % 8], 0, 255)


def words(a, t):
    for t0, t1, text in WORDS:
        k = env(t, t0, t1, 0.8)
        if k <= 0:
            continue
        m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).text((W / 2, H - 64), text, font=ImageFont.truetype(SERIF, 30), fill=255, anchor="mm")
        sh = np.asarray(m.filter(ImageFilter.GaussianBlur(4)), np.float32)[..., None] / 255; mm = np.asarray(m, np.float32)[..., None] / 255
        a = a * (1 - sh * 0.6 * k); a = a * (1 - mm * k) + np.array([250, 244, 236]) * mm * k
    return a


def picture(src, t):
    reach = lambda z=1.0, fx=0.5, fy=0.45, sp=0.45: full(U.sample(src["dropper"], t, sp), z + 0.004 * t, fx, fy)
    lamp = lambda z=1.08: full(U.sample(src["lantern"], t, 0.45), z + 0.003 * t)
    face = lambda: full(U.sample(src["doctor"], t - 26, 0.2), 1.22 + 0.006 * (t - 26), 0.42, 0.3)
    if t < 10:
        return reach() * (1 - sm((t - 4) / 4)) + lamp() * sm((t - 4) / 4)
    if t < 26:
        r, l = reach(1.6, 0.62, 0.3), lamp(1.15)
        side = np.concatenate([r[:, W // 4: W // 4 + W // 2], l[:, W // 4: W // 4 + W // 2]], 1)
        a = lamp() * (1 - sm((t - 10) / 2.5)) + side * sm((t - 10) / 2.5)
        return a * (1 - sm((t - 19) / 4)) + (r * 0.5 + l * 0.5) * sm((t - 19) / 4)
    if t < 46:
        r, l = reach(1.6, 0.62, 0.3), lamp(1.15)
        return (r * 0.5 + l * 0.5) * (1 - sm((t - 25.5) / 3)) + face() * sm((t - 25.5) / 3)
    a = face() * (1 - sm((t - 46) / 4)) + lamp(1.3) * sm((t - 46) / 4)
    return a * (1 - sm((t - 52) / 3)) + np.full((H, W, 3), 250.0) * sm((t - 52) / 3)


def title(a, t):
    k = env(t, 54.5, END + 2, 1.5)
    if k <= 0:
        return a
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    d.text((W / 2, H / 2 - 16), "THE PAST UNDER ANOTHER LIGHT", font=ImageFont.truetype(SERIF, 34), fill=255, anchor="mm")
    d.text((W / 2, H / 2 + 26), "a Ludovico reel, recut", font=ImageFont.truetype(SERIF, 18), fill=190, anchor="mm")
    mm = np.asarray(m, np.float32)[..., None] / 255 * k
    return a * (1 - mm) + np.array([150, 70, 96]) * mm


def music():
    """a slow progression, Am9 - Fmaj7 - C/E - G6 - Am9, voiced as soft breathing pads; no clicks anywhere"""
    n = int(END * SR); t = np.arange(n) / SR; out = np.zeros(n)
    chords = [[110, 164.8, 220, 261.6, 329.6, 493.9], [87.3, 174.6, 220, 261.6, 329.6, 440],
              [82.4, 130.8, 196, 261.6, 329.6, 392], [98, 146.8, 196, 246.9, 329.6, 392], [110, 164.8, 220, 261.6, 329.6, 493.9]]
    step = END / len(chords)
    for i, ch in enumerate(chords):
        w = np.clip(1 - np.abs(t - (i + 0.5) * step) / (step * 0.85), 0, 1) ** 1.5      # each chord breathes in and out
        for j, f in enumerate(ch):
            out += w * (0.9 - 0.1 * j) * np.sin(2 * np.pi * f * t + i + j) * (0.8 + 0.2 * np.sin(2 * np.pi * (0.11 + 0.03 * j) * t))
    rng = np.random.default_rng(4)
    out += np.convolve(rng.normal(0, 1, n), np.ones(30) / 30, "same") * 0.25        # tape air
    for at in (4.0, 19.0, 46.0):                                                       # a bell where images join
        k = int(4 * SR); x = np.arange(k) / SR
        bell = sum(g * np.sin(2 * np.pi * 659.3 * r * x) for r, g in ((1, 1), (2.0, 0.3), (3.01, 0.1))) * np.exp(-x * 1.2) * np.minimum(1, x / 0.02)
        out[int(at * SR):int(at * SR) + k] += 1.2 * bell[: max(0, n - int(at * SR))]
    out *= np.minimum(1, t / 2.5) * np.clip((END - t) / 3, 0, 1)
    return out / np.abs(out).max() * 0.7


def main(clip, shots, od):
    os.makedirs(od, exist_ok=True)
    src = {s: U.load(clip, s) for s in ("dropper", "doctor")}; src["lantern"] = U.load_lantern(shots)
    wav = os.path.join(od, "luminous.wav"); vid = os.path.join(od, "the-past-under-another-light-luminous.mp4")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((music() * 32767).astype(np.int16).tobytes())
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", wav, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac", "-b:a", "160k",
                           "-movflags", "+faststart", "-shortest", vid], stdin=subprocess.PIPE)
    for f in range(int(END * FPS)):
        t = f / FPS
        a = title(words(grade(picture(src, t), t), t), t) * min(1, t / 1.5)
        ff.stdin.write(np.clip(a, 0, 255).astype(np.uint8).tobytes())
    ff.stdin.close(); ff.wait(); print(vid)


if __name__ == "__main__":
    main(*sys.argv[1:4])
