"""Assemble the test shot: picture frames (identical in both passes) + caption band + A then B sound.

python3 -I assemble.py <frames_dir> <sound_dir>
Writes test-shot.mp4 and test-shot-compare.jpg next to this folder; prints loudness and picture identity checks.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SW = os.path.dirname(HERE)
FONTS = "/home/user/bolas/paeleo/scion/oulipo/assets/fonts"
REF = "/home/user/bolas/paeleo/scion/oulipo/assets/references/citefilm.webp"
K0, K1, FPS = 456, 624, 24
W16_BOX = (468, 70, 538, 150)
PAPER, INKC, MUTED = (243, 239, 228), (36, 32, 29), (101, 92, 82)
serif = ImageFont.truetype(os.path.join(FONTS, "instrument-serif.woff2"), 24)
sans = ImageFont.truetype(os.path.join(FONTS, "instrument-sans.woff2"), 14)
tag = ImageFont.truetype(os.path.join(FONTS, "instrument-sans.woff2"), 12)

CAP = {
    "A": [(19.0, 20.3, "« Six heures : on rentre, une fenêtre après l'autre. »", "Six o'clock: people come home, one window after another."),
          (20.6, 25.5, "« — C'est toi ? Le thé est prêt. »", "Is that you? The tea is ready.")],
    "B": [(19.0, 20.3, "« Six heures : chaque fenêtre allumée est notée. »", "Six o'clock: every lit window is logged."),
          (20.6, 25.5, "« 18 h 04 · fenêtre 16 : quelqu'un regarde la rue. »", "6:04 pm · window 16: someone is watching the street.")],
}

def band(ed, t):
    im = Image.new("RGB", (960, 76), PAPER)
    d = ImageDraw.Draw(im)
    d.text((16, 8), f"édition {ed}", font=tag, fill=MUTED)
    for a, b, fr, en in CAP[ed]:
        if a <= t < b:
            w = d.textlength(fr, font=serif)
            d.text(((960 - w) / 2, 10), fr, font=serif, fill=INKC)
            w2 = d.textlength(en, font=sans)
            d.text(((960 - w2) / 2, 46), en, font=sans, fill=MUTED)
    return im

def loud(path):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1]); tp = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1])
    return I, tp

def norm(src, dst, target=-23.0):
    I, tp = loud(src)
    g = target - I
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", f"loudnorm=I={target}:TP=-2.0:LRA=20", "-ar", "44100", dst], check=True)
    I2, tp2 = loud(dst)
    return dict(raw_I=I, gain_db=round(g, 3), I=I2, true_peak=tp2)

def main():
    fdir, sdir = sys.argv[1], sys.argv[2]
    frames = [os.path.join(fdir, f"f{k:04d}.png") for k in range(K0, K1)]
    sha = [hashlib.sha1(Image.open(f).convert("RGB").tobytes()).hexdigest() for f in frames]
    report = {"picture_frames": len(frames), "picture_sha1_first": sha[0], "picture_sha1_492": sha[492 - K0]}
    for ed in "AB":
        report[ed] = norm(os.path.join(sdir, f"{ed}_raw.wav"), os.path.join(sdir, f"{ed}.wav"))
    tmp = os.path.join(sdir, "passes")
    os.makedirs(tmp, exist_ok=True)
    outs = []
    for ed in "AB":
        mp4 = os.path.join(tmp, f"pass-{ed}.mp4")
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "960x540", "-r", "24", "-i", "-",
                              "-i", os.path.join(sdir, f"{ed}.wav"), "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-tune", "animation",
                              "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", mp4], stdin=subprocess.PIPE)
        pass_sha = []
        for k, f in zip(range(K0, K1), frames):
            pic = Image.open(f).convert("RGB")
            pass_sha.append(hashlib.sha1(pic.tobytes()).hexdigest())
            full = Image.new("RGB", (960, 540), PAPER)
            full.paste(pic, (0, 0)); full.paste(band(ed, k / FPS), (0, 464))
            p.stdin.write(full.tobytes())
        p.stdin.close(); p.wait()
        report[ed]["picture_region_sha1_equal_to_master"] = pass_sha == sha
        outs.append(mp4)
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{o}'\n" for o in outs))
    final = os.path.join(SW, "test-shot.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", final], check=True)
    report["size_mb"] = round(os.path.getsize(final) / 1e6, 2)
    # compare sheet: reference beside 3 frames of the shot (decoded from the final mp4, A pass)
    ref = Image.open(REF).convert("RGB")
    H = 270
    tiles = [("reference · citefilm.webp (1990s SD video, overcast)", ref.resize((int(ref.width * H / ref.height), H), Image.LANCZOS))]
    for k, lab in ((480, "f480 · 20.0 s · before the beat"), (520, "f520 · 21.7 s · silhouette risen"), (560, "f560 · 23.3 s · after the head turn")):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{(k - K0) / FPS + 0.001:.3f}", "-i", final, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True, check=True).stdout
        im = Image.frombytes("RGB", (960, 540), raw).crop((0, 0, 960, 464))
        tiles.append((lab, im.resize((int(960 * H / 464), H), Image.LANCZOS)))
    W = sum(t.width for _, t in tiles[:2]) + 30
    sheet = Image.new("RGB", (W, 2 * (H + 34) + 10), PAPER)
    d = ImageDraw.Draw(sheet)
    pos = [(10, 10), (20 + tiles[0][1].width, 10), (10, H + 54), (20 + tiles[0][1].width, H + 54)]
    for (lab, im), (x, y) in zip(tiles, pos):
        sheet.paste(im, (x, y)); d.text((x, y + H + 4), lab, font=sans, fill=INKC)
    # window-16 inset strip: the beat at 2x (nearest-neighbour from the decoded A pass), so the reviewer can see the turn
    ks = [488, 496, 510, 518, 538, 545, 552, 566]
    strip = Image.new("RGB", (W, 200), PAPER)
    ds = ImageDraw.Draw(strip)
    ds.text((10, 4), "window 16 at 2x, from the shot (lights f492 · rises f502-518 · head turn f538-552 · curtain f552-566)", font=sans, fill=INKC)
    cw = (W - 20) // len(ks)
    for n, k in enumerate(ks):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{(k - K0) / FPS + 0.001:.3f}", "-i", final, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True, check=True).stdout
        im = Image.frombytes("RGB", (960, 540), raw).crop(W16_BOX)
        im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        strip.paste(im, (10 + n * cw, 24)); ds.text((10 + n * cw, 24 + im.height + 2), f"f{k}", font=tag, fill=MUTED)
    full = Image.new("RGB", (W, sheet.height + strip.height), PAPER)
    full.paste(sheet, (0, 0)); full.paste(strip, (0, sheet.height))
    sheet = full
    sheet.save(os.path.join(SW, "test-shot-compare.jpg"), quality=90)
    json.dump(report, open(os.path.join(sdir, "report.json"), "w"), indent=1)
    print(json.dumps(report, indent=1))

if __name__ == "__main__":
    main()
