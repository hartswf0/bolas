"""PINK EYE, stacked: The One-Caring above The Averted Glance, playing at once as two halves of one film.

Noddings on top (care as relation, against care as procedure) and Sontag underneath (looking, and the right to look
away). The top cut is stretched slightly so both halves reach white together. Their separate title cards are dropped
for one card across the whole frame, and the two scores are mixed into one. The frame is 960x1080, two 16:9 halves
with a thin seam.

    python3 tools/pink_eye/stacked.py CLIP.mp4 SHOTS_DIR OUT_DIR
"""
import os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import her_eyes as E
import her_eyes_sound as A
import two_cuts as C

W, H, FPS, SR = E.W, E.H, E.FPS, A.SR
SEAM = 4
TAIL = 7.0                                                  # the shared title after both halves have gone white
OPEN = 4.3                                                  # the opening: hairline, the lids open as type, the type becomes the frame
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
FIBRE = np.asarray(Image.fromarray(np.random.default_rng(5).normal(128, 30, (HT, W)).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), np.float32)[..., None] / 128 - 1


# ---- the title: LIDS, a cut-paper letterface drawn here, not a font --------------------------------------------------
# Container: the seam between the two films is the lid line. PINK is the upper lid, EYE the lower.
# Axes: open (0 = a closed hairline, 1 = full cap height: PINK grows up from the seam, EYE grows down from it);
#       width (each word is set flush to the full measure, then breathes with the swell).
# Seed: ragged scissor edges (fixed per letter, paper does not re-cut itself), a hand-wobbled ink hairline, paper fibre.
# Spec: two 16:9 cells, a 30 px margin, three colours only (rose, ink, paper), one word per cell, nothing else on screen.
INK = np.array([18, 10, 13], np.float32); PAPER = np.array([246, 238, 236], np.float32)
MARGIN, STROKE, GAP = 30, 0.2, 0.08
GLYPH = {"P": 0.62, "I": 0.2, "N": 0.72, "K": 0.66, "E": 0.56, "Y": 0.72}


def glyph(ch, w, s=STROKE):
    """(filled polygons, counter polygons) in unit space: x 0..w, y 0 (baseline)..1 (cap)"""
    box = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    if ch == "P":
        return [box(0, 0, s, 1), box(0, 0.42, w, 1)], [box(s, 0.42 + s * 0.9, w - s, 1 - s * 0.9)]
    if ch == "I":
        return [box(0, 0, w, 1)], []
    if ch == "N":
        return [box(0, 0, s, 1), box(w - s, 0, w, 1), [(0, 1), (s * 1.3, 1), (w, 0), (w - s * 1.3, 0)]], []
    if ch == "K":
        return [box(0, 0, s, 1), [(s, 0.4), (s, 0.66), (w - s * 1.2, 1), (w, 1)], [(s, 0.6), (s * 1.6, 0.6), (w, 0), (w - s * 1.25, 0)]], []
    if ch == "E":
        return [box(0, 0, s, 1), box(0, 1 - s, w, 1), box(0, 0.5 - s / 2, w * 0.86, 0.5 + s / 2), box(0, 0, w, s)], []
    if ch == "Y":
        c = w / 2
        return [[(0, 1), (s * 1.2, 1), (c + s / 2, 0.46), (c - s / 2, 0.46)], [(w, 1), (w - s * 1.2, 1), (c - s / 2, 0.46), (c + s / 2, 0.46)],
                box(c - s / 2, 0, c + s / 2, 0.5)], []
    return [], []


def ragged(pts, seed, amp=1.8, step=7):
    out = []
    for i in range(len(pts)):
        a, b = np.array(pts[i], float), np.array(pts[(i + 1) % len(pts)], float)
        n = max(1, int(np.linalg.norm(b - a) / step))
        out += [tuple(a + (b - a) * j / n) for j in range(n)]
    r = np.random.default_rng(seed)
    return [(x + r.normal(0, amp), y + r.normal(0, amp)) for x, y in out]


def word_mask(word, open_, up, breathe=0.0):
    """the word as a cut-paper mask, flush to the measure, growing away from the seam"""
    m = Image.new("L", (W, HT), 0); d = ImageDraw.Draw(m)
    units = sum(GLYPH[c] for c in word) + GAP * (len(word) - 1)
    measure = (W - 2 * MARGIN) * (1 + breathe); sx = measure / units; x0 = (W - measure) / 2
    cap = (H - 2 * MARGIN) * open_; cy = H + SEAM / 2
    to = lambda x, y, ox: (ox + x * sx, cy - y * cap if up else cy + (1 - y) * cap)
    ox = x0
    for k, c in enumerate(word):
        fills, holes = glyph(c, GLYPH[c])
        for n, poly in enumerate(fills):
            d.polygon(ragged([to(x, y, ox) for x, y in poly], 31 * k + n + (0 if up else 500)), fill=255)
        for n, poly in enumerate(holes):
            d.polygon(ragged([to(x, y, ox) for x, y in poly], 77 * k + n + (0 if up else 500)), fill=0)
        ox += (GLYPH[c] + GAP) * sx
    return m


def opening(t, films):
    """an ink hairline; PINK and EYE open from it like lids; then the letters become windows onto the films and grow
    until the type is the frame"""
    cy = H + SEAM / 2
    a = np.broadcast_to(INK, (HT, W, 3)).copy() + FIBRE * 6
    w = W * E.smooth(t / 1.0) / 2                             # the hairline, drawn by hand: it wobbles
    wob = cy + 1.6 * np.sin(XX[0] / 37.0) + 1.1 * np.sin(XX[0] / 11.0 + 2)
    line = (np.abs(YY - wob[None, :]) < 1.6) & (np.abs(XX - W / 2) < w)
    a = np.where(line[..., None], ROSE, a)
    o = E.smooth((t - 0.9) / 1.8)                             # the lids open
    if o <= 0:
        return a
    breathe = 0.015 * np.sin(2 * np.pi * 0.5 * (t - 0.9)) * E.smooth((t - 2.7) / 0.6)
    mask = np.maximum(np.asarray(word_mask("PINK", o, True, breathe), np.float32), np.asarray(word_mask("EYE", o, False, breathe), np.float32))
    z = 1 + 16 * E.smooth((t - OPEN) / 2.2) ** 2               # the type becomes the frame
    if z > 1.001:
        cw, ch = W / z, HT / z
        mask = np.asarray(Image.fromarray(mask.astype(np.uint8)).resize((W, HT), Image.BILINEAR,
                          box=(W / 2 - cw / 2, cy - ch / 2, W / 2 + cw / 2, cy + ch / 2)), np.float32)
    m = mask[..., None] / 255
    win = E.smooth((t - OPEN + 0.4) / 1.5)                     # rose paper slowly turns into a window onto the films
    letters = (ROSE * (0.9 + 0.1 * FIBRE / 3)) * (1 - win) + films * win
    sh = np.asarray(Image.fromarray(mask.astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), np.float32)[..., None] / 255
    a = a * (1 - 0.5 * np.roll(np.roll(sh, 5, 0), 4, 1))      # a lifted shadow, as cut paper casts
    a = a * (1 - m) + letters * m
    k = E.smooth((t - (OPEN + 1.6)) / 0.7)                   # whatever black is left melts into the films
    return a * (1 - k) + films * k


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
            if tt < OPEN + 2.3:
                a = opening(tt, a)
        else:
            a = shared_title(E.smooth((t - bottom.end) / 1.5))
        ff.stdin.write(np.clip(a, 0, 255).astype(np.uint8).tobytes())
    ff.stdin.close(); ff.wait(); print(vid, round(end, 1), "s")


if __name__ == "__main__":
    main(*sys.argv[1:4])
