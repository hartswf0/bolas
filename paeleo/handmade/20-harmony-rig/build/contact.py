"""contact sheet of frames (from a directory of JPEGs or from film.mp4 via ffmpeg-extracted files) for looking.
usage: python3 contact.py out.jpg 'pattern%04d.jpg' first last step [crop x0 y0 x1 y1] [cols]"""
import sys
from PIL import Image, ImageDraw
out, pat, a, b, st = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
crop = tuple(map(int, sys.argv[6:10])) if len(sys.argv) > 9 else (0, 0, 1280, 720)
cols = int(sys.argv[10]) if len(sys.argv) > 10 else 6
fs = list(range(a, b + 1, st)); cw = (crop[2] - crop[0]); ch = (crop[3] - crop[1])
sc = min(1.0, 1800 / (cols * cw)); tw, th = int(cw * sc), int(ch * sc)
rows = (len(fs) + cols - 1) // cols
W = Image.new('RGB', (cols * tw, rows * (th + 14)), (20, 20, 20)); d = ImageDraw.Draw(W)
for k, f in enumerate(fs):
    im = Image.open(pat % f).crop(crop).resize((tw, th))
    x, y = (k % cols) * tw, (k // cols) * (th + 14)
    W.paste(im, (x, y + 14)); d.text((x + 3, y + 1), '%d  %.3fs' % (f, f / 24), fill=(255, 220, 150))
W.save(out, quality=88)
