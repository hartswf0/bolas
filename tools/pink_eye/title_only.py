"""The LIDS title sequence on its own, safe to publish: the letter-windows open onto public-domain archive (hands holding
an apple above, cloud below) instead of the Ludovico footage. Also writes the stills for the Pink Eye page.

    python3 tools/pink_eye/title_only.py SHOTS_DIR OUT_DIR
"""
import os, subprocess, sys, wave
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import her_eyes as E
import her_eyes_sound as A
import stacked as T

END = T.OPEN + 4.6


def films(src, t):
    up = E.grade(E.push(E.at(src["apple"], t, 0.4), 1.04), 3); lo = E.grade(E.push(E.at(src["cloud"], t, 0.35), 1.04, 0.5, 0.2), 9)
    a = np.concatenate([up, np.full((T.SEAM, T.W, 3), 238.0), lo], 0)
    return a * (1 - E.smooth((t - 1.6) / 1.4)) + T.shared_title(0) * E.smooth((t - 1.6) / 1.4)    # settles to paper, then the card


def frame(src, tt):
    t = max(0.0, tt - T.OPEN)
    a = films(src, t)
    if t > 1.6:
        a = T.shared_title(E.smooth((t - 2.4) / 1.4)) * E.smooth((t - 1.6) / 1.4) + a * (1 - E.smooth((t - 1.6) / 1.4))
    return T.opening(tt, a) if tt < T.OPEN + 2.3 else a


def sound():
    n = int(END * A.SR); t = np.arange(n) / A.SR; out = np.zeros(n)
    swell = np.clip(t / T.OPEN, 0, 1) ** 2 * np.clip((T.OPEN + 3 - t) / 3, 0, 1)
    out += 0.06 * swell * (np.sin(2 * np.pi * 73.4 * t) + 0.6 * np.sin(2 * np.pi * 110 * t) + 0.3 * np.sin(2 * np.pi * 146.8 * t))
    k0 = int(T.OPEN * A.SR); bell = A.tone(A.hz(81), 5.0, ((1, 1), (2.76, 0.3), (5.4, 0.1)), 0.8); out[k0:k0 + len(bell)] += 0.22 * bell[:n - k0]
    for j, m in enumerate((50, 57, 62, 66, 69, 74)):
        p = A.pluck(A.hz(m + 12), 4.0, 300 + j); k = int((T.OPEN + 2.0 + 0.3 * j) * A.SR); out[k:k + len(p)] += 0.2 * p[:max(0, n - k)]
    out = A.reverb(out, 3.0, 1.7, 0.45) * np.clip((END - t) / 1.5, 0, 1)
    return out / np.abs(out).max() * 0.8


def main(shots, od):
    os.makedirs(od, exist_ok=True)
    src = {k: E.load_pd(shots, k) for k in ("apple", "cloud")}
    wav = os.path.join(od, "title.wav"); vid = os.path.join(od, "pink-eye-title.mp4")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(A.SR); w.writeframes((sound() * 32767).astype(np.int16).tobytes())
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{T.W}x{T.HT}", "-r", str(T.FPS),
                           "-i", "-", "-i", wav, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-c:a", "aac", "-b:a", "128k",
                           "-movflags", "+faststart", "-shortest", vid], stdin=subprocess.PIPE)
    stills = {0.9: "hairline", 1.9: "lids", 3.4: "open", 4.9: "windows", 5.9: "frame", END - 0.6: "card"}
    for f in range(int(END * T.FPS)):
        tt = f / T.FPS; a = np.clip(frame(src, tt), 0, 255).astype(np.uint8)
        ff.stdin.write(a.tobytes())
        for ts, name in stills.items():
            if abs(tt - ts) < 0.5 / T.FPS:
                Image.fromarray(a).resize((480, 542)).save(os.path.join(od, f"lids-{name}.jpg"), quality=86)
    ff.stdin.close(); ff.wait(); print(vid)


if __name__ == "__main__":
    main(*sys.argv[1:3])
