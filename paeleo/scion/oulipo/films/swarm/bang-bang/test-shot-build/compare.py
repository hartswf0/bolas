# Reference beside three frames of the shot, labelled.  python3 -I compare.py <ref> <mp4> <out.jpg>
import sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
ref, mp4, out = sys.argv[1:4]
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17)
picks = [(528, "f528 (22.0 s): nose 15 deg above the horizon, x stops; the strike lands on 'monter'"),
         (546, "f546: the hang (still); legs still swinging on the pin; the bird flies level past"),
         (590, "f590: tail-first slide back; the bird has flared and landed on the post")]
def grab(f):
    t = (f - 480 + 0.5) / 24
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.4f}", "-i", mp4, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.fromarray(np.frombuffer(raw, np.uint8).reshape(540, 960, 3))
W = 960 * 2 + 30; H = 2 * 540 + 2 * 34 + 30
c = Image.new("RGB", (W, H), (30, 28, 26)); d = ImageDraw.Draw(c)
r = Image.open(ref).convert("RGB"); r = r.resize((int(r.width * 540 / r.height), 540), Image.LANCZOS)
cells = [(r, "REFERENCE: assets/references/bang.webp (Jabely/Queneau, page 2)")] + [(grab(f), s) for f, s in picks]
for i, (im, s) in enumerate(cells):
    x = 10 + (i % 2) * 970; y = 10 + (i // 2) * (540 + 44)
    c.paste(im, (x + (960 - im.width) // 2, y)); d.text((x, y + 544), s, fill=(235, 225, 210), font=F)
c.save(out, quality=90)
