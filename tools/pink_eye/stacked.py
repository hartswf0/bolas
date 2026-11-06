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
TAIL = 7.0                                                  # the shared title after both halves have gone white
OPEN = 3.4                                                  # the opening: a pink hairline, the title, then the eye opens on the films
HT = 2 * H + SEAM
ROSE = np.array([236, 128, 156], np.float32)


def without_title(cut, end=None):
    """rebuild a cut without its title beat; with `end`, stretch its beats so it finishes exactly then"""
    beats = [(d, fn, text, it) for s, d, fn, text, it in cut.beats[:-1]]
    if end is not None:
        k = (end + C.XF * (len(beats) - 1)) / sum(d for d, *_ in beats)
        beats = [(d * k, fn, text, it) for d, fn, text, it in beats]
    return C.Cut(beats)


def shared_title(k):
    a = np.full((HT, W, 3), 246.0)
    m = Image.new("L", (W, HT), 0); d = ImageDraw.Draw(m); y = H - 60
    for txt, size, fill in (("PINK EYE", 58, 255), ("I · THE ONE-CARING · after Nel Noddings", 20, 200),
                            ("II · THE AVERTED GLANCE · after Susan Sontag", 20, 200),
                            ("III · COUNTER ARCHIVE · after Cecile Zhang", 20, 200)):
        d.text((W / 2, y), txt, font=ImageFont.truetype(C.SERIF, size), fill=fill, anchor="mm"); y += size + 22
    mm = np.asarray(m, np.float32)[..., None] / 255 * k
    return a * (1 - mm) + np.array([170, 62, 100]) * mm


YY, XX = np.mgrid[0:HT, 0:W].astype(np.float32)


def opening(t, films):
    """black; a pink hairline draws out from the centre; PINK EYE tracks in letter by letter; then the line opens
    like an eyelid, an almond widening past the frame, onto the two films as they begin"""
    a = np.zeros((HT, W, 3), np.float32)
    cy = H + SEAM / 2
    w = W * E.smooth(t / 1.4) / 2
    line = (np.abs(YY - cy) < 1.5) & (np.abs(XX - W / 2) < w)
    glow = np.exp(-((YY - cy) / 6) ** 2) * (np.abs(XX - W / 2) < w) * 0.35
    a += (line * 0.9 + glow)[..., None] * ROSE
    fade = E.smooth((3.2 - t) / 0.5)                        # the words leave before the eye opens
    m = Image.new("L", (W, HT), 0); d = ImageDraw.Draw(m); f = ImageFont.truetype(C.SERIF, 64)
    word = "PINK EYE"; track = 34 - 20 * E.smooth((t - 0.6) / 2.0)
    widths = [f.getlength(ch) for ch in word]; x = W / 2 - (sum(widths) + track * (len(word) - 1)) / 2
    for i, ch in enumerate(word):
        k = E.smooth((t - 0.6 - 0.12 * i) / 0.5) * fade
        if k > 0:
            d.text((x, cy - 70), ch, font=f, fill=int(255 * k), anchor="lm")
        x += widths[i] + track
    k = E.smooth((t - 1.8) / 0.8) * fade
    if k > 0:
        d.text((W / 2, cy + 46), "a counter-archive of the Ludovico sequence", font=ImageFont.truetype(C.SERIF, 18), fill=int(190 * k), anchor="mm")
    mm = np.asarray(m, np.float32)[..., None] / 255
    a = a * (1 - mm) + np.array([250, 236, 236]) * mm
    o = E.smooth((t - OPEN) / 3.0)                          # the eye opens
    if o > 0:
        rx = W * (0.55 + 0.9 * o); ah = HT * 1.05 * o
        u = np.clip((XX - W / 2) / rx, -1, 1)
        mask = np.clip((ah * (1 - u ** 2) - np.abs(YY - cy)) / 14, 0, 1)[..., None]
        a = a * (1 - mask) + films * mask
    return a


def score(top, bottom, end):
    n = int(end * SR); t = np.arange(n) / SR; out = np.zeros(n)
    a, b = C.score_noddings(top), C.score_sontag(bottom)
    k0 = int(OPEN * SR)                                      # the films' scores start as the eye opens
    out[k0:k0 + len(a)] += 0.9 * a[:n - k0]; out[k0:k0 + len(b)] += 0.9 * b[:n - k0]
    swell = np.clip(t / OPEN, 0, 1) ** 2 * np.clip((OPEN + 2.5 - t) / 2.5, 0, 1)    # under the opening: a low swell
    out += 0.06 * swell * (np.sin(2 * np.pi * 73.4 * t) + 0.6 * np.sin(2 * np.pi * 110 * t) + 0.3 * np.sin(2 * np.pi * 146.8 * t))
    bell = A.tone(A.hz(81), 5.0, ((1, 1), (2.76, 0.3), (5.4, 0.1)), 0.8); out[k0:k0 + len(bell)] += 0.22 * bell[:max(0, n - k0)]
    joint = OPEN + bottom.end                                # both halves white: one chord, harp and bell together
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
    end = OPEN + bottom.end + TAIL
    wav = os.path.join(od, "stacked.wav"); vid = os.path.join(od, "pink-eye-stacked.mp4")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((score(top, bottom, end) * 32767).astype(np.int16).tobytes())
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{2 * H + SEAM}", "-r", str(FPS),
                           "-i", "-", "-i", wav, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-c:a", "aac", "-b:a", "192k",
                           "-movflags", "+faststart", "-shortest", vid], stdin=subprocess.PIPE)
    for f in range(int(end * FPS)):
        tt = f / FPS; t = max(0.0, tt - OPEN)                # t is film time; the films begin as the eye opens
        if t < bottom.end - 0.05:
            up = E.grade(top.frame(min(t, top.end - 0.05)), f); lo = E.grade(bottom.frame(t), f + 7)
            a = np.concatenate([up, np.full((SEAM, W, 3), 238.0), lo], 0)
            k = E.smooth((t - (bottom.end - 1.2)) / 1.2)      # the seam and the halves dissolve into the shared white
            if k > 0:
                a = a * (1 - k) + shared_title(0.0) * k
            if tt < OPEN + 3.2:
                a = opening(tt, a)
        else:
            a = shared_title(E.smooth((t - bottom.end) / 1.5))
        ff.stdin.write(np.clip(a, 0, 255).astype(np.uint8).tobytes())
    ff.stdin.close(); ff.wait(); print(vid, round(end, 1), "s")


if __name__ == "__main__":
    main(*sys.argv[1:4])
