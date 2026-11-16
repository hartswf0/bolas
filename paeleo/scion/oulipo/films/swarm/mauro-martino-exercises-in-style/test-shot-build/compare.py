"""Reference beside 3 frames from the rendered test shot, labelled, with measured tonal stats."""
import subprocess, tempfile, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path("/home/user/bolas/paeleo/scion/oulipo")
WS = ROOT / "films/swarm/mauro-martino-exercises-in-style"
REF = ROOT / "assets/references/martinoCharcoal.webp"
MP4 = WS / "test-shot.mp4"
FR = [(0.50, "0.50 s  bus slides to its stop"), (1.21, "1.21 s  A3 shove (film 0:05.2)"), (1.42, "1.42 s  stanchion, cord swings out")]
mono = ImageFont.truetype(str(ROOT / "assets/fonts/ibm-plex-mono.woff2"), 15)
INK, PAPER = (34, 33, 31), (238, 230, 214)


def stats(im):
    a = np.asarray(im.convert("RGB"), np.float32); l = a @ [0.299, 0.587, 0.114]
    p = np.percentile(l, [2, 25, 50, 75, 98]).round().astype(int)
    return "L p2/25/50/75/98 " + "/".join(map(str, p)) + f"  chroma {(a.max(2) - a.min(2)).mean():.1f}"


def frame(t):
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "f.png"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t:.3f}", "-i", str(MP4), "-frames:v", "1", str(out)], check=True)
        return Image.open(out).convert("RGB")


cw, ch, pad, lab = 640, 360, 14, 46
sheet = Image.new("RGB", (2 * cw + 3 * pad, 2 * (ch + lab) + 3 * pad), PAPER)
d = ImageDraw.Draw(sheet)
ref = Image.open(REF).convert("RGB")
cells = [(ref, "REFERENCE  martinoCharcoal.webp (Martino, 2023), shown for comparison only")]
cells += [(frame(t), "TEST SHOT  " + s) for t, s in FR]
for i, (im, title) in enumerate(cells):
    x = pad + (i % 2) * (cw + pad); y = pad + (i // 2) * (ch + lab + pad)
    st = stats(im)
    fit = im.copy(); fit.thumbnail((cw, ch), Image.LANCZOS)
    sheet.paste(fit, (x + (cw - fit.width) // 2, y + (ch - fit.height) // 2))
    d.rectangle([x, y + ch + 4, x + cw, y + ch + lab - 2], fill=INK)
    d.text((x + 8, y + ch + 7), title, font=mono, fill=PAPER)
    d.text((x + 8, y + ch + 25), st, font=mono, fill=(211, 203, 188))
out = WS / "test-shot-compare.jpg"
sheet.save(out, quality=90)
print(out)
