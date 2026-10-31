"""PINK EYE, through her eyes: the Ludovico scene told from the woman in the room.

The real footage, recombined. We stay with the woman doctor's own shots (her close-ups, her half of the control desk) and
with the projector's violet glow from the wide shots. Alex's suffering never comes on screen. What the machine shows is
replaced by public-domain archive images of tenderness, laid into her face and into the beam as double exposures: a water
lily opening, a butterfly on a woman's fingertips, a swan. Long dissolves only, a warm full-frame grade, and Ode to Joy
(Alex's own Beethoven) as strings and a music box.

The Ludovico footage is under copyright; this reads a local copy and writes a local film. The archive shots are public
domain (via hartswf0/secondhand-motion: Wathen collection 1939-40, Insect Zoo, Muscatatuck National Wildlife Refuge).

    python3 tools/pink_eye/her_eyes.py CLIP.mp4 SHOTS_DIR OUT_DIR
"""
import os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS, SR, END = 960, 540, 24, 48000, 56.0
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"

# real seconds and a crop (x, y, w) in the 640x360 clip; every crop is 16:9
REAL = {
    "glow": (199.0, 205.0, (120, 0, 300)),        # the projector's violet glow above the seats, nobody in frame
    "desk": (178.0, 198.0, (20, 40, 300)),        # her half of the control desk: she watches
    "face": (164.0, 167.9, (110, 0, 420)),        # her close-up
    "face2": (209.0, 211.9, (110, 0, 420)),       # her second close-up, looking aside
}
PD = {"lily": "flower", "fly": "butterfly", "swan": "swan"}


def smooth(u):
    u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)


def env(t, a, b, f):
    return smooth((t - a) / f) * smooth((b - t) / f)


def load_real(clip, key):
    a, b, (x, y, w) = REAL[key]; h = int(w * 9 / 16)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a), "-i", clip, "-t", str(b - a), "-vf",
                          f"fps=12,crop={w}:{h}:{x}:{y},scale={W}:{H}:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    return single_shot(fr)


def single_shot(fr):
    """keep only the longest unbroken run of one shot, so a stray frame of another (Alex's clamped eyes at the end of
    her close-up, his strapped head at the start of the desk shot) can never flash up, even when the loop turns"""
    small = fr[:, ::8, ::8].astype(np.float32)
    d = np.abs(np.diff(small, axis=0)).mean((1, 2, 3))
    cuts = [0] + [i + 1 for i in range(len(d)) if d[i] > 4 * np.median(d) + 8] + [len(fr)]
    a, b = max(zip(cuts, cuts[1:]), key=lambda r: r[1] - r[0])
    return fr[a:b]


def load_pd(shots, name):
    d = os.path.join(shots, f"{name}-sam", "frames")
    return np.stack([np.asarray(Image.open(os.path.join(d, f)).convert("RGB").resize((W, H), Image.LANCZOS), np.uint8)
                     for f in sorted(os.listdir(d))])


def at(fr, t, speed):
    """slow motion with blended in-betweens, ping-pong so nothing jumps"""
    x = max(0.0, t) * 12 * speed; n = len(fr); p = 2 * n - 2
    k0 = int(x) % p; k1 = (k0 + 1) % p; f = x - int(x); i = lambda k: k if k < n else p - k
    return fr[i(k0)].astype(np.float32) * (1 - f) + fr[i(k1)].astype(np.float32) * f


def push(img, z, fx=0.5, fy=0.45):
    if z <= 1.001:
        return img
    cw, ch = W / z, H / z; x0, y0 = (W - cw) * fx, (H - ch) * fy
    return np.asarray(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch)), np.float32)


def pinkish(a):
    """archive images take a rose cast so they sit inside her light"""
    return np.clip(a * np.array([1.05, 0.86, 0.92]) + np.array([18, 0, 10]), 0, 255)


def double(base, over, k):
    """a double exposure: the second image shows mostly where the first is dark, so her face stays readable"""
    y = (base @ np.array([0.299, 0.587, 0.114]))[..., None] / 255
    kk = k * (1 - y) ** 1.1
    b, o = base / 255, pinkish(over) / 255
    return (1 - (1 - b) * (1 - o * kk)) * 255


def grade(a, seed):
    x = np.clip(a / 255, 0, 1) ** 0.82
    x = x * np.array([1.03, 0.95, 0.95]) + (1 - x) * np.array([0.09, 0.03, 0.07])
    x = x + np.asarray(Image.fromarray((x * 255).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(20)), np.float32) / 255 * 0.2
    return np.clip(x / 1.1 * 255 + np.random.default_rng(seed).normal(0, 3.0, (H, W, 1)), 0, 255)


def picture(S, t):
    glow = lambda: push(at(S["glow"], t, 0.35), 1.0 + 0.01 * t)
    desk = lambda: push(at(S["desk"], t - 5, 0.5), 1.04 + 0.006 * t)
    face = lambda: push(at(S["face"], t - 13, 0.35), 1.05 + 0.006 * (t - 13), 0.5, 0.35)
    face2 = lambda: push(at(S["face2"], t - 31, 0.3), 1.05 + 0.006 * (t - 31), 0.5, 0.35)
    lily = lambda: at(S["lily"], t, 0.4); fly = lambda: at(S["fly"], t - 14, 0.5); swan = lambda: at(S["swan"], t - 22, 0.5)
    if t < 7:
        a = double(glow(), lily(), 0.25 * smooth((t - 2) / 4))
    elif t < 14:
        a = glow() * (1 - smooth((t - 7) / 3)) + double(desk(), lily(), 0.75) * smooth((t - 7) / 3)
    elif t < 24:
        a = double(desk(), lily(), 0.75) * (1 - smooth((t - 13) / 3)) + double(face(), fly(), 0.85) * smooth((t - 13) / 3)
    elif t < 32:
        a = double(face(), fly(), 0.85) * (1 - smooth((t - 23) / 3.5)) + fly() * smooth((t - 23) / 3.5)
        a = a * (1 - smooth((t - 27.5) / 3.5)) + swan() * smooth((t - 27.5) / 3.5)
    elif t < 43:
        a = swan() * (1 - smooth((t - 31) / 3.5)) + double(face2(), swan(), 0.9) * smooth((t - 31) / 3.5)
    elif t < 51:
        a = double(face2(), swan(), 0.9) * (1 - smooth((t - 42) / 3.5)) + double(glow(), lily(), 0.8) * smooth((t - 42) / 3.5)
        a = a * (1 - smooth((t - 47) / 3.5)) + np.full((H, W, 3), 244.0) * smooth((t - 47) / 3.5)
    else:
        a = np.full((H, W, 3), 244.0)
    return a


def title(a, t):
    k = env(t, 50.5, END + 2, 1.5)
    if k <= 0:
        return a
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    d.text((W / 2, H / 2 - 18), "PINK EYE", font=ImageFont.truetype(SERIF, 54), fill=255, anchor="mm")
    d.text((W / 2, H / 2 + 34), "the Ludovico scene, through her eyes", font=ImageFont.truetype(SERIF, 19), fill=200, anchor="mm")
    mm = np.asarray(m, np.float32)[..., None] / 255 * k
    return a * (1 - mm) + np.array([196, 70, 112]) * mm


def music():
    """Ode to Joy, slow: a music-box melody over a soft string pad, with the projector's hum at the start"""
    n = int(END * SR); t = np.arange(n) / SR; out = np.zeros(n); rng = np.random.default_rng(3)
    beat = 0.78; start = 4.0
    tune = [66, 66, 67, 69, 69, 67, 66, 64, 62, 62, 64, 66, 66, 64, 64, 66, 66, 67, 69, 69, 67, 66, 64, 62, 62, 64, 66, 64, 62, 62]
    lens = [1] * 12 + [1.5, 0.5, 2] + [1] * 12 + [1.5, 0.5, 2]
    def note(f, a0, g, dur=2.6):
        k = int(dur * SR); x = np.arange(k) / SR
        s = sum(c * np.sin(2 * np.pi * f * r * x) for r, c in ((1, 1), (2.0, 0.3), (3.0, 0.1), (4.16, 0.06))) * np.exp(-x * 2.2) * np.minimum(1, x / 0.004)
        a = int(a0 * SR); b = min(n, a + k)
        if a < n:
            out[a:b] += g * s[:b - a]
    a0 = start
    for m, l in zip(tune, lens):
        note(440 * 2 ** ((m + 12 - 69) / 12), a0, 0.45); a0 += l * beat
    # strings: detuned, vibrato, breathing chords D - A - D - G - D - A - D under the tune
    chords = [[146.8, 220, 293.7, 370], [110, 220, 277.2, 329.6], [146.8, 220, 293.7, 370], [98, 196, 246.9, 293.7],
              [146.8, 220, 293.7, 370], [110, 220, 277.2, 329.6], [146.8, 220, 293.7, 370]]
    span = (END - 2) / len(chords)
    for i, ch in enumerate(chords):
        w = np.clip(1 - np.abs(t - (1 + (i + 0.5) * span)) / (span * 0.9), 0, 1) ** 1.3
        for f in ch:
            for det in (-0.6, 0.6):
                out += 0.035 * w * np.sin(2 * np.pi * (f + det) * t + 0.004 * f * np.sin(2 * np.pi * 5.1 * t))
    out += (0.02 * np.sin(2 * np.pi * 50 * t) + 0.01 * np.sin(2 * np.pi * 100 * t)) * np.clip(1 - t / 8, 0, 1)   # the projector, fading
    L = int(2.5 * SR); ir = rng.normal(0, 1, L) * np.exp(-np.arange(L) / SR * 2.6)
    m = 1 << int(np.ceil(np.log2(n + L))); wet = np.fft.irfft(np.fft.rfft(out, m) * np.fft.rfft(ir, m), m)[:n]
    out = 0.7 * out + 0.3 * wet / np.abs(wet).max() * np.abs(out).max()
    out *= np.minimum(1, t / 2.0) * np.clip((END - t) / 3, 0, 1)
    return out / np.abs(out).max() * 0.75


def main(clip, shots, od):
    os.makedirs(od, exist_ok=True)
    S = {k: load_real(clip, k) for k in REAL}; S.update({k: load_pd(shots, v) for k, v in PD.items()})
    wav = os.path.join(od, "her.wav"); vid = os.path.join(od, "pink-eye-through-her-eyes.mp4")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((music() * 32767).astype(np.int16).tobytes())
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", wav, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-c:a", "aac", "-b:a", "160k",
                           "-movflags", "+faststart", "-shortest", vid], stdin=subprocess.PIPE)
    for f in range(int(END * FPS)):
        t = f / FPS
        a = title(grade(picture(S, t), f), t) * min(1, t / 2.0)
        ff.stdin.write(np.clip(a, 0, 255).astype(np.uint8).tobytes())
    ff.stdin.close(); ff.wait(); print(vid)


if __name__ == "__main__":
    main(*sys.argv[1:4])
