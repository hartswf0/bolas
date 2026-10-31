"""Two cuts of the Ludovico sequence, each built on one thinker, from the real footage and more of the public-domain archive.

THE ONE-CARING, after Nel Noddings, Caring (1984)
  Each procedure from the Ludovico room is paired with the same gesture performed as relation. The doctors behind the
  console ("monitored") are answered by a woman opening a door and coming in ("met"). The attendant's dropper ("treated")
  is answered by two hands holding an apple ("held"). The doctor's soothing face ("observed") is answered by a girl's
  rabbit ("answered"). Machine hum and harp sit under the procedures, and human voices come in under the relations.

THE AVERTED GLANCE, after Susan Sontag, On Photography (1977) and Regarding the Pain of Others (2003)
  The projector, the watchers and a man with binoculars. Then "load / aim / shoot" over a camera, a cannon, and the WWII
  newsreel that Kubrick projected. Then the film does what Alex was not allowed to do: it looks away, up into cloud and
  out to sea.

Neither cut shows the clamped eye or the screaming. Every real segment is cut down to one unbroken shot (her_eyes.single_shot),
and beats overlap in long dissolves, so nothing flashes or pops. The Ludovico footage is under copyright; this reads a
local copy and writes local films. The archive shots are public domain, via hartswf0/secondhand-motion.

    python3 tools/pink_eye/two_cuts.py CLIP.mp4 SHOTS_DIR OUT_DIR
"""
import os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import her_eyes as E
import her_eyes_sound as A

W, H, FPS, SR = E.W, E.H, E.FPS, A.SR
XF = 3.0                                                    # every beat dissolves into the next over three seconds
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
ITALIC = SERIF                                             # no italic serif is installed; quotes keep their quotation marks

REAL = {   # real seconds and a 16:9 crop (x, y, w) in the 640x360 clip
    "console": (178.0, 198.0, (0, 0, 640)),   # both doctors behind the console, watching
    "dropper": (156.0, 163.9, (0, 0, 640)),   # the attendant's drops, seen wide and softened
    "face": (164.0, 167.9, (110, 0, 420)),    # her soothing close-up
    "glow": (199.0, 205.0, (120, 0, 300)),    # the projector's glow above the empty seats
    "planes": (64.0, 78.0, (0, 0, 640)),      # the newsreel Kubrick projected: aircraft
    "ruins": (84.0, 89.5, (0, 0, 640)),       # the newsreel: a ruined city
}
PD = ["door", "apple", "rabbit", "cat", "binoculars", "camera", "cannon", "cloud", "ocean"]


def load_real(clip, key):
    a, b, (x, y, w) = REAL[key]; h = int(w * 9 / 16)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a), "-i", clip, "-t", str(b - a), "-vf",
                          f"fps=12,crop={w}:{h}:{x}:{y},scale={W}:{H}:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    return E.single_shot(np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3))


def soft(img, r=2.5, fade=0.0):
    a = np.asarray(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32)
    return a * (1 - fade) + 235 * fade


def mono(img, warm=(1.0, 0.93, 0.86)):
    y = (img @ np.array([0.299, 0.587, 0.114]))[..., None]; return y * np.array(warm)


def caption(a, text, k, italic=False, size=34, y=None):
    if k <= 0 or not text:
        return a
    f = ImageFont.truetype(ITALIC if italic else SERIF, size)
    lines, cur = [], ""
    for w_ in text.split():
        if f.getlength(cur + " " + w_) > W - 160 and cur:
            lines.append(cur); cur = w_
        else:
            cur = (cur + " " + w_).strip()
    lines.append(cur)
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m); yy = (y or H - 58) - (len(lines) - 1) * (size + 8)
    for ln in lines:
        d.text((W / 2, yy), ln, font=f, fill=255, anchor="mm"); yy += size + 8
    sh = np.asarray(m.filter(ImageFilter.GaussianBlur(4)), np.float32)[..., None] / 255; mm = np.asarray(m, np.float32)[..., None] / 255
    a = a * (1 - sh * 0.75 * k)
    return a * (1 - mm * k) + np.array([250, 244, 236]) * mm * k


def title_card(lines, k):
    a = np.full((H, W, 3), 246.0)
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m); y = H / 2 - 30
    for i, (txt, size) in enumerate(lines):
        d.text((W / 2, y), txt, font=ImageFont.truetype(SERIF, size), fill=255 if i == 0 else 190, anchor="mm"); y += size + 18
    mm = np.asarray(m, np.float32)[..., None] / 255 * k
    return a * (1 - mm) + np.array([170, 62, 100]) * mm


class Cut:
    """beats overlap by XF seconds; each frame is the weighted blend of the beats alive at that moment"""
    def __init__(self, beats):
        self.beats, t = [], 0.0
        for dur, fn, text, italic in beats:
            self.beats.append((t, dur, fn, text, italic)); t += dur - XF
        self.end = t + XF

    def frame(self, t):
        acc, wsum = None, 0.0
        for s, d, fn, text, italic in self.beats:
            if s <= t < s + d:
                w = E.smooth((t - s) / XF) if s > 0 else 1.0
                w = w * (E.smooth((s + d - t) / XF) if s + d < self.end - 0.01 else 1.0)
                img = caption(fn(t - s), text, E.env(t - s, 1.6, d - 1.2, 0.9), italic)
                acc = img * w if acc is None else acc + img * w; wsum += w
        return acc / max(wsum, 1e-6)

    def cues(self):
        return [s for s, *_ in self.beats]


def noddings(S):
    sp = lambda k, t, v=0.4: E.at(S[k], t, v)
    return Cut([
        (8.0, lambda t: E.push(sp("console", t, 0.5), 1.02 + 0.004 * t), "monitored", False),
        (8.0, lambda t: E.push(sp("door", t, 0.5), 1.03 + 0.004 * t), "met", False),
        (8.5, lambda t: E.double(soft(sp("dropper", t, 0.35), 3.0, 0.08), sp("apple", t, 0.4), 0.35), "treated", False),
        (8.5, lambda t: E.push(sp("apple", t, 0.4), 1.04 + 0.005 * t), "held", False),
        (9.0, lambda t: E.double(E.push(sp("face", t, 0.3), 1.05 + 0.005 * t, 0.5, 0.35), sp("rabbit", t, 0.4), 0.55), "observed", False),
        (9.0, lambda t: E.push(sp("rabbit", t, 0.4), 1.03 + 0.004 * t), "answered", False),
        (8.0, lambda t: E.push(sp("cat", t, 0.4), 1.03 + 0.004 * t) * (1 - E.smooth((t - 4.5) / 3.5)) + 246 * E.smooth((t - 4.5) / 3.5), "", False),
        (7.0, lambda t: title_card([("THE ONE-CARING", 44), ("after Nel Noddings, Caring (1984)", 19)], E.smooth(t / 1.5)), "", False),
    ])


def sontag(S):
    sp = lambda k, t, v=0.4: E.at(S[k], t, v)
    news = lambda k, t: soft(mono(sp(k, t, 0.35), (0.98, 0.95, 0.92)), 1.6, 0.06)
    def look_away(t):                                     # the newsreel slides down out of view, and the sky takes its place
        k = E.smooth((t - 2.5) / 4.5)
        r = np.roll(news("ruins", t), int(H * 0.85 * k), axis=0); r[: int(H * 0.85 * k)] = 0
        return r * (1 - k) + E.push(sp("cloud", t, 0.35), 1.08 - 0.008 * t, 0.5, 0.2) * k
    return Cut([
        (8.0, lambda t: E.push(sp("glow", t, 0.35), 1.0 + 0.01 * t), "", False),
        (9.0, lambda t: E.double(E.push(sp("console", t, 0.5), 1.02), sp("binoculars", t, 0.4), 0.45),
         "“To photograph people is to violate them.”", True),
        (6.5, lambda t: E.push(sp("camera", t, 0.4), 1.02 + 0.006 * t), "load", False),
        (6.5, lambda t: E.push(sp("cannon", t, 0.4), 1.02 + 0.006 * t), "aim", False),
        (7.0, lambda t: news("planes", t), "shoot", False),
        (9.5, look_away, "", False),
        (10.0, lambda t: E.push(sp("cloud", t, 0.35), 1.0 + 0.004 * t, 0.5, 0.2),
         "“Our sympathy proclaims our innocence as well as our impotence.”", True),
        (8.0, lambda t: E.push(sp("ocean", t, 0.3), 1.03 + 0.004 * t) * (1 - E.smooth((t - 4.5) / 3.5)) + 246 * E.smooth((t - 4.5) / 3.5), "", False),
        (7.5, lambda t: title_card([("THE AVERTED GLANCE", 44), ("after Susan Sontag, On Photography (1977)", 18),
                                    ("and Regarding the Pain of Others (2003)", 18)], E.smooth(t / 1.5)), "", False),
    ])


# ---- sound -----------------------------------------------------------------
def score_noddings(cut):
    n = int(cut.end * SR); t = np.arange(n) / SR; out = np.zeros(n)
    c = cut.cues()
    hum = 0.02 * np.sin(2 * np.pi * 50 * t) + 0.012 * np.sin(2 * np.pi * 100 * t)
    for i in (0, 2, 4):                                     # the procedures: the machine's hum and a cool harp
        a, b = c[i], c[i] + cut.beats[i][1]
        w = np.clip(np.minimum((t - a) / XF, (b - t) / XF), 0, 1); out += hum * w
        at, k = a + 0.5, 0
        while at < b - 1:
            put = A.pluck(A.hz([62, 69, 74, 69][k % 4] + 12), 2.0, k + i); s = int(at * SR); out[s:s + len(put)] += 0.16 * put[:max(0, n - s)]
            at += 0.9; k += 1
    for i, root in ((1, 50), (3, 45), (5, 47)):           # the relations: voices come in, warm and close
        a = c[i]; dur = cut.beats[i][1] + 1.5
        for m, g in ((root + 12, 0.38), (root + 16, 0.22), (root + 19, 0.22), (root, 0.2)):
            s = A.sing(A.hz(m), dur, g); k = int(a * SR); out[k:k + len(s)] += s[:max(0, n - k)]
    a = c[6]                                                # the cat, the white, the title: harp alone, resolving
    for j, m in enumerate((62, 66, 69, 74, 78)):
        p = A.pluck(A.hz(m + 12), 4.0, 90 + j); k = int((a + 1 + j * 0.6) * SR); out[k:k + len(p)] += 0.2 * p[:max(0, n - k)]
    return out


def score_sontag(cut):
    n = int(cut.end * SR); t = np.arange(n) / SR; out = np.zeros(n); c = cut.cues(); rng = np.random.default_rng(8)
    away = c[5] + 3.0                                       # the moment the film looks away
    held = np.clip((away + 3 - t) / 3, 0, 1)
    out += held * (0.025 * np.sin(2 * np.pi * 50 * t) + 0.015 * np.sin(2 * np.pi * 100 * t))      # the projector, while we watch
    out += held * 0.04 * np.sin(2 * np.pi * 73.4 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t))  # a low held note under it
    for i, m in ((2, 81), (3, 78), (4, 74)):               # load, aim, shoot: three bells, falling
        b = A.tone(A.hz(m), 4.0, ((1, 1), (2.76, 0.35), (5.4, 0.12)), 1.0); k = int((c[i] + 1.6) * SR); out[k:k + len(b)] += 0.3 * b[:max(0, n - k)]
    air = A.lowpass(rng.normal(0, 1, n), 900) * np.clip((t - away) / 4, 0, 1)                         # after: open air
    out += 0.12 * air / np.abs(air).max() * (0.7 + 0.3 * np.sin(2 * np.pi * 0.09 * t))
    for j, (m, at) in enumerate(((62, away), (69, away + 2), (66, away + 4), (74, away + 7), (71, away + 11))):
        k = int(at * SR); s = A.tone(A.hz(m), 7.0, ((1, 1), (2.0, 0.25)), 0.45, 1.2); out[k:k + len(s)] += 0.12 * s[:max(0, n - k)]
    sea = A.lowpass(rng.normal(0, 1, n), 500) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.12 * t)) ** 2 * np.clip((t - c[7]) / 3, 0, 1)
    out += 0.15 * sea / np.abs(sea).max()
    return out


def render(cut, score, path):
    n = int(cut.end * SR); t = np.arange(n) / SR
    snd = A.reverb(score(cut), 3.0, 1.7, 0.45)
    snd = snd * np.minimum(1, t / 2.0) * np.clip((cut.end - t) / 2.5, 0, 1); snd = snd / np.abs(snd).max() * 0.8
    wav = path[:-4] + ".wav"
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((snd * 32767).astype(np.int16).tobytes())
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", wav, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-c:a", "aac", "-b:a", "192k",
                           "-movflags", "+faststart", "-shortest", path], stdin=subprocess.PIPE)
    for f in range(int(cut.end * FPS)):
        a = E.grade(cut.frame(f / FPS), f) * min(1, f / FPS / 1.5)
        ff.stdin.write(np.clip(a, 0, 255).astype(np.uint8).tobytes())
    ff.stdin.close(); ff.wait(); print(path)


def main(clip, shots, od):
    os.makedirs(od, exist_ok=True)
    S = {k: load_real(clip, k) for k in REAL}; S.update({k: E.load_pd(shots, k) for k in PD})
    render(noddings(S), score_noddings, os.path.join(od, "the-one-caring.mp4"))
    render(sontag(S), score_sontag, os.path.join(od, "the-averted-glance.mp4"))


if __name__ == "__main__":
    main(*sys.argv[1:4])
