import os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../.."))
import kit
SW = os.path.join(HERE, "..")
ROOT = os.path.join(SW, "../../..")
def grab(t):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", "%.3f" % t, "-i", os.path.join(SW, "test-shot.mp4"), "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.frombytes("RGB", (960, 540), raw)
tiles = [(Image.open(os.path.join(ROOT, "assets/references/extract-001.webp")).convert("RGB"), "REFERENCE: Lecroart, extract-001 (not used in the work)"),
         (Image.open(os.path.join(SW, "proposals/kf-2.png")).convert("RGB"), "CHOSEN KEYFRAME kf-2 (to meet or beat)"),
         (grab(1.40), "SHOT 1.4 s (film 27.4): note edge-on (substitution), white ground"),
         (grab(3.0), "SHOT 3.0 s (film 29.0): face-out, spot-black hinge, balloon"),
         (grab(8.0), "SHOT 8.0 s (film 48.0): B' held, identical to B"),
         (Image.open(os.path.join(SW, "test-page.png")).convert("RGB"), "TEST PAGE (3200x1800), same art")]
cw, ch, lab = 800, 450, 34
sheet = Image.new("RGB", (2 * cw + 30, 3 * (ch + lab) + 40), (30, 30, 30))
d = ImageDraw.Draw(sheet)
f = kit.font("sans", 22)
for i, (im, name) in enumerate(tiles):
    x, y = 10 + (i % 2) * (cw + 10), 10 + (i // 2) * (ch + lab + 10)
    t = im.copy(); t.thumbnail((cw, ch), Image.LANCZOS)
    sheet.paste(t, (x + (cw - t.width) // 2, y + lab + (ch - t.height) // 2))
    d.text((x + 4, y + 5), name, fill=(240, 240, 240), font=f)
sheet.save(os.path.join(SW, "test-shot-compare.jpg"), quality=90)
print("ok")
