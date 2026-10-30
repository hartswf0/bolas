"""THE PAST UNDER ANOTHER LIGHT: three recuts of a Ludovico reel.

The earlier Pink Eye versions stared at the clamped eye and repeated the violence they meant to answer. Here the footage
is never shown as a full-screen spectacle. It is projected onto a pinned paper sheet in a dark room, over a worktable
where prints and typed slips lie under a desk lamp. Every light is a way of making a body visible: the projector (the
institution's record), the lamp (the person handling the record), the spill from one onto the other. The clamped eye and
the screaming are never shown.

  I    Rearrange    after Barbara Hammer, History Lessons: one gesture repeated across sources until its meaning turns
  II   Reinterpret  after Michelle Citron and Trinh T. Minh-ha: the reel slowed down on the only woman in the room,
                    with typed slips that do not agree with the picture
  III  Invent       after Cheryl Dunye and Zoe Leonard, and Saidiya Hartman: an invented record that keeps its blank, the
                    print of the eye left face down, and the reel running out onto the empty table

A composed scene: archive fragments re-performed, not a recorded event. The Ludovico footage is under copyright; this
script reads a local copy and writes a local film. The lantern hand is public domain (Anthracite: Pre-Shift Examinations
of Underground Mines, via hartswf0/secondhand-motion).

    python3 tools/pink_eye/under_another_light.py CLIP.mp4 SHOTS_DIR OUT_DIR
"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS, SR = 960, 540, 24, 48000
SWD, SHT = 1120, 630                                         # the room; the camera frames part of it
SHEET = [(420, 70), (880, 84), (872, 348), (428, 336)]       # the pinned paper sheet: tl, tr, br, bl
LENS = (40, -80)                                             # the projector, out of frame, upper left
TABLE_Y = 430
LAMP = (250, 600)

SEGS = {"dropper": (156.0, 163.9), "doctor": (164.0, 167.9), "desk": (146.0, 154.0), "wide": (198.0, 204.0)}
PARTS = [(0.0, 26.0), (26.0, 52.0), (52.0, 80.0)]
END = 84.0

SLATES = [
    ("I · REARRANGE", "after Barbara Hammer, History Lessons (2000)"),
    ("II · REINTERPRET", "after Michelle Citron, Daughter Rite (1978) · Trinh T. Minh-ha, Surname Viet Given Name Nam (1989)"),
    ("III · INVENT", "after Cheryl Dunye and Zoe Leonard, The Watermelon Woman (1996) · Saidiya Hartman, Venus in Two Acts (2008)"),
]
SLIPS = [  # part II: typed, they do not agree with the picture
    (30.0, "She is the only woman in this room.", (560, 462), -2.0),
    (37.0, "She watches him watch.", (700, 494), 1.5),
    (44.0, "The film gives her a close-up. It does not give her a question.", (600, 526), -0.8),
]
CARD_AT = 60.0                                               # part III: the invented record
CARD_LINES = ["INVENTED RECORD", "Medical officer, Ludovico ward, 1971", "Her account:", ""]
RUNOUT = 70.0                                                # the reel runs out


def smooth(u):
    u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)


def env(t, a, b, fade):
    return smooth((t - a) / fade) * smooth((b - t) / fade)


def font(size, mono=False, bold=False):
    name = "DejaVuSansMono" if mono else ("DejaVuSerif-Bold" if bold else "DejaVuSerif")
    f = f"/usr/share/fonts/truetype/dejavu/{name}.ttf"
    return ImageFont.truetype(f, size) if os.path.exists(f) else ImageFont.load_default()


# ---- sources -------------------------------------------------------------
def load(clip, seg):
    a, b = SEGS[seg]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a), "-i", clip, "-t", str(b - a), "-vf", "fps=12",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, 360, 640, 3)


def load_lantern(shots):
    d = os.path.join(shots, "lantern-sam", "frames")
    fr = [np.asarray(Image.open(os.path.join(d, f)).convert("RGB").resize((640, 480)), np.uint8) for f in sorted(os.listdir(d))]
    return np.stack([f[60:420] for f in fr])                 # 16:9 crop of the 4:3 frame


def sample(fr, t, speed):
    x = max(0.0, t) * 12 * speed; n = len(fr); p = 2 * n - 2
    k0 = int(x) % p; k1 = (k0 + 1) % p; f = x - int(x)
    idx = lambda k: k if k < n else p - k
    return fr[idx(k0)].astype(np.float32) * (1 - f) + fr[idx(k1)].astype(np.float32) * f


# ---- what is on the sheet ------------------------------------------------
def projection(src, t):
    """(image or None for an empty white gate, brightness) per moment of the score"""
    def mix(a, b, k):
        return a * (1 - k) + b * k
    if t < 26:                                               # I: the reach, repeated against the lantern hand
        reach = lambda sp, warm: sample(src["dropper"], t, sp) * np.array([1.0 + 0.10 * warm, 1.0, 1.0 - 0.12 * warm])
        lamp = sample(src["lantern"], t, 0.5)
        if t < 8:
            return reach(0.5, 0), 1.0
        if t < 13:
            return mix(reach(0.5, 0), lamp, smooth((t - 8) / 2.5)), 1.0
        if t < 21:
            return mix(lamp, reach(0.32, 0.6), smooth((t - 13) / 2.5)), 1.0
        return mix(reach(0.25, 1.0), lamp, 0.5 * smooth((t - 21) / 3)), 1.0   # superimposed: his reach carries the light
    if t < 52:                                               # II: the doctor, slowed almost to stillness
        doc = sample(src["doctor"], t - 26, 0.22)
        h, w = doc.shape[:2]; z = 1 + 0.35 * smooth((t - 28) / 20)
        cw, ch = int(w / z), int(h / z); x0 = int((w - cw) * 0.42); y0 = int((h - ch) * 0.3)
        doc = np.asarray(Image.fromarray(doc[y0:y0 + ch, x0:x0 + cw].astype(np.uint8)).resize((w, h), Image.BILINEAR), np.float32)
        if t < 31:
            return mix(sample(src["desk"], t - 26, 0.4), doc, smooth((t - 27) / 3)), 1.0
        return doc, 1.0
    if t < RUNOUT:                                           # III: the room seen from far off, then the reel runs out
        return sample(src["wide"], t - 52, 0.4), 1.0 - 0.15 * smooth((t - (RUNOUT - 3)) / 3)
    flick = 0.85 + 0.15 * math.sin(t * 47) * (1 - smooth((t - RUNOUT) / 3))
    return None, flick


# ---- the room ------------------------------------------------------------
def coeffs(dst, src):
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]; B += [u, v]
    return np.linalg.solve(np.array(A, float), np.array(B, float))


SHEET_MASK = Image.new("L", (SWD, SHT), 0); ImageDraw.Draw(SHEET_MASK).polygon(SHEET, fill=255)
SHEET_MASK = np.asarray(SHEET_MASK.filter(ImageFilter.GaussianBlur(1.2)), np.float32)[..., None] / 255
COEF = coeffs(SHEET, [(0, 0), (640, 0), (640, 360), (0, 360)])
YY, XX = np.mgrid[0:SHT, 0:SWD].astype(np.float32)
_r = np.random.default_rng(3)
FIBRE = np.asarray(Image.fromarray(_r.normal(128, 14, (SHT, SWD)).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)), np.float32)[..., None] / 128 - 1
GRAIN = [(_r.normal(0, 1, (SHT // 2, SWD // 2, 1)).repeat(2, 0).repeat(2, 1)).astype(np.float32) for _ in range(6)]

# the beam: a cone from the lens to the sheet, visible only where dust hangs in it
_b = Image.new("L", (SWD, SHT), 0); ImageDraw.Draw(_b).polygon([LENS, SHEET[1], SHEET[2], SHEET[3], SHEET[0]], fill=255)
BEAM = np.asarray(_b.filter(ImageFilter.GaussianBlur(18)), np.float32) / 255
BEAM *= np.clip(1 - np.hypot(XX - SHEET[0][0], YY - 200) / 1400, 0.2, 1)
DUST = _r.uniform([0, 0], [SWD, SHT], (420, 2)); DUSTV = _r.normal(0, 1, (420, 2)) * np.array([3, 2]) + np.array([2, -1])

LAMP_LIGHT = np.exp(-(((XX - LAMP[0]) / 430) ** 2 + ((YY - LAMP[1]) / 260) ** 2))[..., None] * np.array([1.0, 0.72, 0.42])
AMBIENT = 0.07


def base_albedo():
    a = np.zeros((SHT, SWD, 3), np.float32)
    wall = np.array([52, 50, 54], np.float32); table = np.array([118, 92, 70], np.float32)
    a[:TABLE_Y] = wall; a[TABLE_Y:] = table
    a[TABLE_Y - 3:TABLE_Y + 2] = np.array([30, 24, 20])      # the table's edge
    return a * (1 + 0.12 * FIBRE)


ALBEDO = base_albedo()


def make_print(img, w, seed, back=None):
    """a photographic print with its white border; back=text shows its reverse instead"""
    h = int(w * img.shape[0] / img.shape[1]) if img is not None else int(w * 0.5625)
    p = Image.new("RGB", (w + 20, h + 20), (232, 226, 212))
    if back is None:
        p.paste(Image.fromarray(img.astype(np.uint8)).resize((w, h), Image.BILINEAR), (10, 10))
    else:
        ImageDraw.Draw(p).text((24, h // 2), back, font=font(14), fill=(110, 100, 92))
    return p


def make_slip(text, typed):
    f = font(15, mono=True); w = int(f.getlength(text)) + 30
    s = Image.new("RGB", (w, 34), (238, 232, 218))
    ImageDraw.Draw(s).text((15, 9), text[:typed], font=f, fill=(48, 38, 36))
    return s


def make_card(lines, typed):
    f = font(15, mono=True); s = Image.new("RGB", (360, 150), (236, 228, 206)); d = ImageDraw.Draw(s)
    d.line([(16, 40), (344, 40)], fill=(196, 120, 120), width=1)
    left = typed; y = 14
    for i, ln in enumerate(lines):
        d.text((18, y), ln[:max(0, left)], font=f, fill=(48, 38, 36)); left -= len(ln) + 2; y += 30
    d.line([(150, 106), (330, 106)], fill=(120, 110, 104), width=1)   # the blank stays blank
    return s


def blend(arr, alpha, val, x0, y0):
    h, w = alpha.shape[:2]; xa, ya, xb, yb = max(0, x0), max(0, y0), min(SWD, x0 + w), min(SHT, y0 + h)
    if xa >= xb or ya >= yb:
        return
    al = alpha[ya - y0:yb - y0, xa - x0:xb - x0]
    if val is None:
        arr[ya:yb, xa:xb] *= 1 - al
    else:
        arr[ya:yb, xa:xb] = arr[ya:yb, xa:xb] * (1 - al) + val[ya - y0:yb - y0, xa - x0:xb - x0] * al


def lay(albedo, img, cx, cy, deg):
    """put a paper object on the table: rotated, with a soft contact shadow"""
    a = np.asarray(img.convert("RGBA").rotate(deg, expand=True, resample=Image.BICUBIC), np.float32)
    x0, y0 = int(cx - a.shape[1] / 2), int(cy - a.shape[0] / 2)
    shadow = np.asarray(Image.fromarray(a[..., 3].astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), np.float32)[..., None] / 255
    blend(albedo, shadow * 0.55, None, x0 + 6, y0 + 7)
    blend(albedo, a[..., 3:] / 255, a[..., :3], x0, y0)


def objects(t, stills):
    """what lies on the table at time t: (image, x, y, degrees)"""
    obs = []
    if t < 26:
        slide = smooth((t - 6) / 1.6)                        # the archivist puts the two reaches side by side
        obs.append((stills["reach"], 300, 520, -4))
        obs.append((stills["lantern"], 760 - 260 * slide, 610 - 40 * slide, 6 - 3 * slide))
    elif t < 52:
        obs.append((stills["doctor"], 190, 500, 3))
        for at, text, (x, y), deg in SLIPS:
            if t >= at:
                obs.append((make_slip(text, int((t - at) * 22)), x, y, deg))
    else:
        out = smooth((t - (RUNOUT + 3)) / 2.5)               # after the run-out the table is cleared
        if out < 1:
            obs.append((stills["eye_back"], 300 - 700 * out, 520, -5))
            if t >= CARD_AT:
                obs.append((make_card(CARD_LINES, int((t - CARD_AT) * 20)), 690 + 700 * out, 540, 2))
    return obs


def camera(t):
    """(centre x, centre y, zoom): the camera moves only when a relation between images changes"""
    if t < 26:
        k = smooth((t - 6) / 1.6); return 560 + 40 * k, 330, 1.0
    if t < 52:
        k = smooth((t - 28) / 22); return 600 - 20 * k, 330 - 30 * k, 1.0 + 0.08 * k
    k = smooth((t - (RUNOUT + 2)) / 6); return 560, 330 + 60 * k, 1.0 + 0.05 * k


def render(src, stills, t):
    img, gate = projection(src, t)
    if img is None:
        proj = np.full((360, 640, 3), 245, np.float32)
    else:
        proj = np.clip(img * 1.12 + 18, 0, 255)
    proj = np.clip(proj * np.array([0.93, 0.98, 1.06]), 0, 255)   # projector light, cooler than the lamp
    warped = np.asarray(Image.fromarray(proj.astype(np.uint8)).transform((SWD, SHT), Image.PERSPECTIVE, tuple(COEF), Image.BILINEAR), np.float32)
    emis = warped * SHEET_MASK * gate * (1 + 0.06 * FIBRE)
    albedo = ALBEDO.copy()
    for im, x, y, deg in objects(t, stills):
        lay(albedo, im, x, y, deg)
    spill = np.asarray(Image.fromarray((warped * SHEET_MASK).astype(np.uint8)).filter(ImageFilter.GaussianBlur(70)), np.float32) / 255
    light = AMBIENT + LAMP_LIGHT * 0.95 + spill * 0.9 * gate
    out = albedo * light * (1 - SHEET_MASK) + emis
    # dust that shows only inside the beam
    d = (DUST + DUSTV * t) % np.array([SWD, SHT]); field = np.zeros((SHT, SWD), np.float32)
    np.add.at(field, (d[:, 1].astype(int), d[:, 0].astype(int)), 1.0)
    field = np.asarray(Image.fromarray((field * 255).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.1)), np.float32) / 255
    out += (BEAM * (14 + 160 * field) * gate)[..., None] * np.array([0.85, 0.92, 1.0])
    out += np.asarray(Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(16)), np.float32) * 0.18
    out = np.clip((out - 8) * 1.06, 0, 255) + GRAIN[int(t * 12) % 6] * 5
    cx, cy, z = camera(t); cw, ch = W / z, H / z
    cx = min(max(cx, cw / 2), SWD - cw / 2); cy = min(max(cy, ch / 2), SHT - ch / 2)     # stay inside the room
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    frame = np.asarray(Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC, box=box), np.float32)
    # slates for each part, and the end
    for i, (a, b) in enumerate(PARTS):
        k = env(t, a + 0.3, a + 4.8, 1.0)
        if k > 0:
            frame = text_over(frame, SLATES[i][0], SLATES[i][1], k)
    fade_in = min(env(t, PARTS[0][0], END, 2.0), 1.0)
    end = smooth((t - (END - 6)) / 1.5)
    frame = frame * fade_in * (1 - end * 0.94)
    if t > END - 5.5:
        frame = title(frame, env(t, END - 5.0, END + 1, 1.2))
    return np.clip(frame, 0, 255).astype(np.uint8)


def text_over(frame, head, sub, k):
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    d.text((36, H - 66), head, font=font(20, mono=True), fill=255); d.text((36, H - 38), sub, font=font(13, mono=True), fill=170)
    m = np.asarray(im, np.float32)[..., None] / 255 * k
    return frame * (1 - m) + np.array([236, 226, 210]) * m


def title(frame, k):
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    d.text((W / 2, H / 2 - 24), "THE PAST UNDER ANOTHER LIGHT", font=font(34, bold=True), fill=255, anchor="mm")
    d.text((W / 2, H / 2 + 18), "three recuts of a Ludovico reel", font=font(17), fill=200, anchor="mm")
    d.text((W / 2, H / 2 + 60), "composed scene · archive fragments re-performed · not a recorded event", font=font(12, mono=True), fill=140, anchor="mm")
    m = np.asarray(im, np.float32)[..., None] / 255 * k
    return frame * (1 - m) + np.array([236, 150, 172]) * m


# ---- sound: the room, the projector, the hands ---------------------------
def soundscape():
    n = int(END * SR); t = np.arange(n) / SR; rng = np.random.default_rng(5); out = np.zeros(n)

    def lowpass(x, cut):
        X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); return np.fft.irfft(X / (1 + (f / cut) ** 4), len(x))

    def put(sig, at, g=1.0):
        a = int(at * SR); b = min(n, a + len(sig))
        if a < n:
            out[a:b] += g * sig[:b - a]

    running = (t < RUNOUT + 3).astype(float) * np.clip((RUNOUT + 3 - t) / 0.4, 0, 1)
    out += 0.25 * lowpass(rng.normal(0, 1, n), 180) / 3                  # the room
    out += running * (0.03 * np.sin(2 * np.pi * 50 * t) + 0.015 * np.sin(2 * np.pi * 100 * t))   # projector motor
    click = np.exp(-np.arange(int(0.006 * SR)) / 40) * rng.normal(0, 1, int(0.006 * SR))
    for i in range(int((RUNOUT + 3) * 24)):                            # the gate, soft
        tt = i / 24
        put(click, tt, 0.035)
    for i in range(int(3 * 24)):                                       # the tail of the film slapping the reel
        put(click * 2, RUNOUT + i / 24 + rng.normal(0, 0.004), 0.12 * (1 - i / 72))
    out += 0.004 * np.sin(2 * np.pi * 120 * t) * (np.abs(np.sin(2 * np.pi * 0.05 * t)))   # the lamp's faint buzz

    def bell(f, dur=3.5):
        k = int(dur * SR); x = np.arange(k) / SR
        return sum(g * np.sin(2 * np.pi * f * r * x) for r, g in ((1, 1), (2.0, 0.3), (3.01, 0.12))) * np.exp(-x * 1.6) * np.minimum(1, x / 0.01)
    for at in (0.8, 13.2, 21.5):                                        # I: the motif returns with each repetition
        put(bell(220.0), at, 0.09); put(bell(329.6), at + 0.7, 0.07)
    k = int(26 * SR); x = np.arange(k) / SR                             # II: one held, low tone under her face
    put(0.03 * np.sin(2 * np.pi * 110 * x) * np.minimum(1, x / 4) * np.minimum(1, (26 - x) / 4), 26.0)
    for a, b in ((6.0, 7.6), (RUNOUT + 3, RUNOUT + 5.5)):               # paper sliding
        m = int((b - a) * SR); s = lowpass(rng.normal(0, 1, m), 2200) * np.sin(np.linspace(0, np.pi, m)); put(s, a, 0.1)

    def typed(at, chars, rate):
        for i in range(chars):
            put(lowpass(np.exp(-np.arange(400) / 60) * rng.normal(0, 1, 400), 3000), at + i / rate + rng.normal(0, 0.006), 0.18)
    for at, text, *_ in SLIPS:
        typed(at, len(text), 22)
    typed(CARD_AT, sum(len(l) + 2 for l in CARD_LINES[:3]), 20)
    put(bell(196.0, 6.0), END - 5.0, 0.08)                              # the title
    L = int(1.8 * SR); ir = rng.normal(0, 1, L) * np.exp(-np.arange(L) / SR * 3.5); ir = lowpass(ir, 4000)
    m = 1 << int(np.ceil(np.log2(n + L))); wet = np.fft.irfft(np.fft.rfft(out, m) * np.fft.rfft(ir, m), m)[:n]
    mix = 0.75 * out + 0.25 * wet / max(1e-9, np.abs(wet).max()) * np.abs(out).max()
    mix *= np.minimum(1, t / 2.0) * np.clip((END - t) / 2.0, 0, 1)
    return mix / max(1e-9, np.abs(mix).max()) * 0.8


def main(clip, shots, od, parts=None):
    os.makedirs(od, exist_ok=True)
    src = {s: load(clip, s) for s in SEGS}; src["lantern"] = load_lantern(shots)
    stills = {"reach": make_print(src["dropper"][30], 230, 1), "lantern": make_print(src["lantern"][14], 210, 2),
              "doctor": make_print(src["doctor"][20], 220, 3), "eye_back": make_print(None, 230, 4, back="eye, clamped. not shown.")}
    wav = os.path.join(od, "light.wav"); raw = os.path.join(od, "picture.mp4"); vid = os.path.join(od, "the-past-under-another-light.mp4")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((soundscape() * 32767).astype(np.int16).tobytes())
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", raw], stdin=subprocess.PIPE)
    for f in range(int(END * FPS)):
        ff.stdin.write(render(src, stills, f / FPS).tobytes())
    ff.stdin.close(); ff.wait()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                    "-movflags", "+faststart", "-shortest", vid], check=True)
    print(vid)


if __name__ == "__main__":
    main(*sys.argv[1:4])
