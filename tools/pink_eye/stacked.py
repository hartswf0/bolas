"""PINK EYE, stacked: The One-Caring above The Averted Glance, playing at once as two halves of one film.

Noddings on top (care as relation, against care as procedure) and Sontag underneath (looking, and the right to look
away). The top cut is stretched slightly so both halves reach white together. Their separate title cards are dropped
for one card across the whole frame, and the two scores are mixed into one. The frame is 960x1080, two 16:9 halves
with a thin seam.

    python3 tools/pink_eye/stacked.py CLIP.mp4 SHOTS_DIR OUT_DIR
"""
import os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import her_eyes as E
import her_eyes_sound as A
import two_cuts as C

W, H, FPS, SR = E.W, E.H, E.FPS, A.SR
SEAM = 4
TAIL = 6.5                                                  # the shared title after both halves have gone white


def without_title(cut, end=None):
    """rebuild a cut without its title beat; with `end`, stretch its beats so it finishes exactly then"""
    beats = [(d, fn, text, it) for s, d, fn, text, it in cut.beats[:-1]]
    if end is not None:
        k = (end + C.XF * (len(beats) - 1)) / sum(d for d, *_ in beats)
        beats = [(d * k, fn, text, it) for d, fn, text, it in beats]
    return C.Cut(beats)


def shared_title(k):
    a = np.full((2 * H + SEAM, W, 3), 246.0)
    m = Image.new("L", (W, 2 * H + SEAM), 0); d = ImageDraw.Draw(m); y = H - 40
    for txt, size, fill in (("PINK EYE", 58, 255), ("I · THE ONE-CARING · after Nel Noddings", 20, 200),
                            ("II · THE AVERTED GLANCE · after Susan Sontag", 20, 200)):
        d.text((W / 2, y), txt, font=ImageFont.truetype(C.SERIF, size), fill=fill, anchor="mm"); y += size + 22
    mm = np.asarray(m, np.float32)[..., None] / 255 * k
    return a * (1 - mm) + np.array([170, 62, 100]) * mm


def score(top, bottom, end):
    n = int(end * SR); t = np.arange(n) / SR; out = np.zeros(n)
    a, b = C.score_noddings(top), C.score_sontag(bottom)
    out[:len(a)] += 0.9 * a[:n]; out[:len(b)] += 0.9 * b[:n]
    joint = bottom.end                                       # both halves white: one chord, harp and bell together
    for j, m in enumerate((50, 57, 62, 66, 69, 74)):
        p = A.pluck(A.hz(m + 12), 5.0, 200 + j); k = int((joint + 0.3 + 0.35 * j) * SR); out[k:k + len(p)] += 0.22 * p[:max(0, n - k)]
    bell = A.tone(A.hz(74), 6.0, ((1, 1), (2.76, 0.3), (5.4, 0.1)), 0.7); k = int((joint + 0.3) * SR); out[k:k + len(bell)] += 0.2 * bell[:max(0, n - k)]
    out = A.reverb(out, 3.0, 1.7, 0.45)
    out *= np.minimum(1, t / 2.0) * np.clip((end - t) / 2.5, 0, 1)
    return out / np.abs(out).max() * 0.8


def main(clip, shots, od):
    os.makedirs(od, exist_ok=True)
    S = {k: C.load_real(clip, k) for k in C.REAL}; S.update({k: E.load_pd(shots, k) for k in C.PD})
    bottom = without_title(C.sontag(S)); top = without_title(C.noddings(S), bottom.end)
    end = bottom.end + TAIL
    wav = os.path.join(od, "stacked.wav"); vid = os.path.join(od, "pink-eye-stacked.mp4")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((score(top, bottom, end) * 32767).astype(np.int16).tobytes())
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{2 * H + SEAM}", "-r", str(FPS),
                           "-i", "-", "-i", wav, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-c:a", "aac", "-b:a", "192k",
                           "-movflags", "+faststart", "-shortest", vid], stdin=subprocess.PIPE)
    for f in range(int(end * FPS)):
        t = f / FPS
        if t < bottom.end - 0.05:
            up = E.grade(top.frame(min(t, top.end - 0.05)), f); lo = E.grade(bottom.frame(t), f + 7)
            a = np.concatenate([up, np.full((SEAM, W, 3), 238.0), lo], 0)
            a = a * min(1, t / 1.5)
            k = E.smooth((t - (bottom.end - 1.2)) / 1.2)      # the seam and the halves dissolve into the shared white
            if k > 0:
                a = a * (1 - k) + shared_title(0.0) * k
        else:
            a = shared_title(E.smooth((t - bottom.end) / 1.5))
        ff.stdin.write(np.clip(a, 0, 255).astype(np.uint8).tobytes())
    ff.stdin.close(); ff.wait(); print(vid, round(end, 1), "s")


if __name__ == "__main__":
    main(*sys.argv[1:4])
