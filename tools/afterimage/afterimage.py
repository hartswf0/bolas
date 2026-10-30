"""AFTERIMAGE: the eye keeps the glow.

A study after Afterlight's Retina (AFL-20) and A Clockwork Pink. The screen is treated as a retina: it adapts to the
archive's light, and where the light has gone it keeps a complementary afterimage. The projector light is a cold
clinical green-white, so the afterimage the eye makes is pink. Nobody paints it on.

  I   Held     no blink is allowed and the cuts accelerate, so the afterimage builds into a burn
  II  Release  a hand lifts a lantern; the first blink, red through the lid, lets the retina rest
  III Carry    in the dark the afterimage is the only light; the glow is also the sound

Footage: public-domain shots from the Prelinger and other Internet Archive collections, as cut into frames by
hartswf0/secondhand-motion (see SOURCES below). Frames are retimed, cropped, tinted and composited, never drawn on.

    python3 tools/afterimage/afterimage.py SHOTS_DIR OUT_DIR
SHOTS_DIR is secondhand-motion/shots (eye-sam, camera-sam, light-bulb-sam, lighthouse-sam, lantern-sam, star-sam).
"""
import json, math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter, zoom

W, H, FPS, SR = 960, 720, 24, 48000          # 4:3, the archive's own frame
PW, PH = 480, 360                             # the retina works at half size
CLINIC = np.array([0.78, 1.0, 0.84], np.float32)   # projector light: cold green-white
PINK = np.array([1.0, 0.42, 0.70], np.float32)     # its complement: what the eye keeps
LID = np.array([0.55, 0.09, 0.03], np.float32)     # light through an eyelid

SOURCES = [
    ("eye", "Mental Hospital", "https://archive.org/details/mental_hospital"),
    ("camera", "Gateways to the Mind", "https://archive.org/details/gateways_to_the_mind"),
    ("light-bulb", "Light Of Your Life", "https://archive.org/details/LightOfYourL_2"),
    ("lighthouse", "Celebrating Chincoteague National Wildlife Refuge", "https://archive.org/details/gov.fws.aws.3.4"),
    ("lantern", "Anthracite: Pre-Shift Examinations of Underground Mines", "https://archive.org/details/anthracite_pre_shift"),
    ("star", "Gift of Green", "https://archive.org/details/GiftofGr1946"),
]

# ---- the score -----------------------------------------------------------
HELD_END, RELEASE_END, CARRY_END, CARD_END = 18.0, 30.0, 45.5, 51.0


def held_cuts():
    """Ludovico acceleration: each shot shorter than the last, down to a floor; the eye between every image."""
    others = ["camera", "light-bulb", "lighthouse", "light-bulb", "camera", "light-bulb"]
    shots, t, d, i = [], 0.0, 1.6, 0
    while t < HELD_END - 1e-6:
        clip = "eye" if i % 2 == 0 else others[(i // 2) % len(others)]
        e = min(HELD_END, t + d)
        shots.append((t, e, clip, 1.0, 1.0))
        t, d, i = e, max(0.17, d * 0.88), i + 1      # keeps tightening to about four frames
    return shots


# (start, end, clip, speed, gain)
SHOTS = held_cuts() + [
    (18.0, 21.0, "eye", 0.5, 1.0),          # the clatter stops; still held, nothing new to see
    (21.0, 25.3, "lantern", 0.62, 1.0),     # a hand lifts a light
    (25.3, 30.0, "eye", 0.5, 1.0),
    (33.0, 41.0, "star", 0.5, 0.55),        # a flower opens inside the afterglow
    (41.0, 44.5, "eye", 0.5, 0.6),
]
BLINKS = [25.0, 28.4, 43.0]                 # none before the release
BLINK_LEN = 0.5
DARK = (30.0, 41.0)                         # nothing is shown here but what the retina holds
GLOW_PEAK = 0.62                            # the kept glow is never brighter than this


def blink(t):
    for b in BLINKS:
        u = (t - b) / BLINK_LEN
        if 0 <= u <= 1:
            return 1 - abs(2 * u - 1)
    return 0.0


def phase(t):
    return "held" if t < HELD_END else "release" if t < RELEASE_END else "carry" if t < CARRY_END else "card"


# ---- footage ------------------------------------------------------------
def load(shots_dir, clip):
    d = os.path.join(shots_dir, f"{clip}-sam", "frames")
    fr = []
    for f in sorted(os.listdir(d)):
        a = np.asarray(Image.open(os.path.join(d, f)).convert("RGB").resize((PW, PH), Image.BICUBIC), np.float32) / 255
        fr.append(a)
    a = np.stack(fr)
    lo, hi = np.percentile(a, 1), np.percentile(a, 99.5)    # level the print, as the Afterlight cache does
    return np.clip((a - lo) / max(hi - lo, 1e-3), 0, 1)


def frame_at(clips, t):
    for s, e, clip, speed, gain in SHOTS:
        if s <= t < e:
            fr = clips[clip]
            k = int((t - s) * 12 * speed)
            n = len(fr)
            k = k % (2 * n - 2)
            k = k if k < n else 2 * n - 2 - k              # ping-pong: a held loop has no seam
            return fr[k] * gain, (clip, s)
    return np.zeros((PH, PW, 3), np.float32), (None, None)


# ---- the retina ---------------------------------------------------------
class Retina:
    def __init__(s):
        s.A = np.zeros((PH, PW, 3), np.float32)   # what the eye has adapted to
        s.log = []

    def step(s, I, t, dt):
        ph = phase(t)
        rate = {"held": 0.9, "release": 0.9, "carry": 0.16, "card": 0.16}[ph]
        s.A += (I - s.A) * min(1.0, dt * rate)
        b = blink(t)
        if b > 0:
            s.A *= 1 - 0.09 * b                       # behind the lid the retina rests
        after = np.clip(s.A - I, 0, 1)                # light the eye still holds after it has gone
        if DARK[0] <= t < DARK[1]:
            # in the dark the screen shows only the brightest of what the retina is holding, in pink;
            # anything new (the flower) reaches the viewer only through that holding
            L = gaussian_filter(s.A.mean(2), 3)
            q = np.percentile(L, 85)
            g = np.clip((L - q) / max(L.max() - q, 1e-4), 0, 1) ** 1.2
            D = g[..., None] * PINK * GLOW_PEAK
        else:
            comp = after.mean(2, keepdims=True) * PINK
            D = np.clip(I - s.A * 0.35, 0, None) * 1.3 + comp * 1.25
        s.log.append(dict(t=round(t, 4), phase=ph, A=float(s.A.mean()), after=float(after.mean()), blink=round(b, 3)))
        return D, b


YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


def finish(D, b, t):
    img = zoom(D, (H / PH, W / PW, 1), order=1)
    img = img + gaussian_filter(img, (10, 10, 0)) * (0.15 if DARK[0] <= t < DARK[1] else 0.35)   # halation
    if b > 0.02:                                                             # the lid closes from both edges
        u = np.clip(1 - ((XX - W / 2) / (W * 0.62)) ** 2, 0, 1) ** 0.5   # the lid's edge is an arc
        half = (H / 2) * (1 - b) * u + 1
        open_ = (np.abs(YY - H / 2) < half).astype(np.float32)
        open_ = gaussian_filter(open_, 14)[..., None]                       # soft, as flesh is
        glow = (0.25 + img.mean()) * LID
        img = img * open_ + glow * (1 - open_)
    rng = np.random.default_rng(int(t * FPS))
    img = img + rng.normal(0, 0.025, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1)   # grain
    v = np.exp(-(((XX - W / 2) / (W * 0.62)) ** 2 + ((YY - H / 2) / (H * 0.62)) ** 2))
    img = img * (0.55 + 0.45 * v)[..., None]
    if CARRY_END - 1.2 < t < CARD_END:                                       # fade before the card
        img = img * max(0.0, (CARRY_END - t) / 1.2)
    return np.clip(img, 0, 1)


def font(size, bold=False):
    for f in ["/usr/share/fonts/truetype/dejavu/DejaVuSerif%s.ttf" % ("-Bold" if bold else ""),
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def card():
    img = Image.new("RGB", (W, H), (8, 6, 7))
    d = ImageDraw.Draw(img)
    d.text((W / 2, 210), "AFTERIMAGE", font=font(58, True), fill=(236, 130, 172), anchor="mm")
    d.text((W / 2, 262), "the eye keeps the glow", font=font(20), fill=(170, 160, 160), anchor="mm")
    y = 340
    d.text((W / 2, y), "Archive footage, public domain, via the Internet Archive", font=font(15), fill=(150, 142, 142), anchor="mm")
    for clip, title, url in SOURCES:
        y += 30
        d.text((W / 2, y), f"{clip}: {title}", font=font(15), fill=(205, 196, 196), anchor="mm")
    return np.asarray(img, np.float32) / 255


# ---- sound --------------------------------------------------------------
def sound(log, cut_times):
    n = int(CARD_END * SR)
    out = np.zeros(n)
    t = np.arange(n) / SR
    rng = np.random.default_rng(3)

    def put(sig, at, gain=1.0):
        a = int(at * SR); b = min(n, a + len(sig))
        if a < n:
            out[a:b] += gain * sig[: b - a]

    def burst(ms, decay, tone=None):
        m = int(ms / 1000 * SR); tt = np.arange(m) / SR
        s = rng.normal(0, 1, m) if tone is None else sum(np.sin(2 * np.pi * f * tt) for f in tone)
        return s * np.exp(-tt * decay)

    # I: the projector gate, 24 a second, and a clinical tone that tightens as the cuts accelerate
    h = int(HELD_END * SR)
    for i in range(int(HELD_END * 24)):
        put(burst(5, 1000), i / 24, 0.05)
    press = (t[:h] / HELD_END) ** 2
    out[:h] += 0.05 * press * (np.sin(2 * np.pi * 880 * t[:h]) + np.sin(2 * np.pi * 886 * t[:h]))
    for c in cut_times:
        if c < HELD_END:
            put(burst(25, 160, (1900, 2700)), c, 0.12)
    # II: the clatter stops dead; room tone; the lantern brings a low warm chord; blinks are muffled thumps
    out[h:int(RELEASE_END * SR)] += 0.004 * rng.normal(0, 1, int(RELEASE_END * SR) - h)
    a, b = int(21.0 * SR), int(30.0 * SR)
    tt = np.arange(b - a) / SR
    env = np.minimum(1, tt / 2.5) * np.minimum(1, (tt[-1] - tt) / 1.5)
    chord = sum(np.sin(2 * np.pi * f * tt) / (k + 1) for k, f in enumerate([110, 164.8, 220, 246.9]))
    out[a:b] += 0.06 * env * chord
    for bt in BLINKS:
        m = int(0.35 * SR); x = np.arange(m) / SR
        put(np.sin(2 * np.pi * 55 * x) * np.exp(-x * 14), bt + BLINK_LEN / 2, 0.35)
    # III: the glow is heard: a pink-noise-free tone cluster whose loudness is the afterimage energy
    ts = np.array([r["t"] for r in log]); E = np.array([r["after"] for r in log])
    c0, c1 = int(RELEASE_END * SR), int(CARRY_END * SR)
    e = np.interp(t[c0:c1], ts, E); e = e / max(1e-6, E[(ts >= RELEASE_END) & (ts < CARRY_END)].max())
    tone = sum(np.sin(2 * np.pi * f * t[c0:c1] + k) for k, f in enumerate([523.3, 659.3, 784.0, 1046.5]))
    out[c0:c1] += 0.05 * e * tone
    out = out / max(1e-9, np.abs(out).max()) * 0.85
    return out


def main(shots_dir, od):
    os.makedirs(od, exist_ok=True)
    clips = {c: load(shots_dir, c) for c, _, _ in SOURCES}
    ret = Retina()
    vid = os.path.join(od, "afterimage.mp4"); wav = os.path.join(od, "afterimage.wav")
    raw = os.path.join(od, "picture.mp4")
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", raw],
                          stdin=subprocess.PIPE)
    C = card()
    dt = 1 / FPS
    for f in range(int(CARD_END * FPS)):
        t = f / FPS
        if t >= CARRY_END:
            img = C
        else:
            I, _ = frame_at(clips, t)
            if phase(t) == "held":
                I = I * CLINIC                         # the projector's light
            D, b = ret.step(I, t, dt)
            img = finish(D, b, t)
        ff.stdin.write((img * 255).astype(np.uint8).tobytes())
    ff.stdin.close(); ff.wait()
    cut_times = [s for s, *_ in SHOTS]
    s = (sound(ret.log, cut_times) * 32767).astype(np.int16)
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(s.tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                    "-movflags", "+faststart", "-shortest", vid], check=True)
    json.dump(dict(shots=SHOTS, blinks=BLINKS, log=ret.log), open(os.path.join(od, "retina.json"), "w"))
    print(vid)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
