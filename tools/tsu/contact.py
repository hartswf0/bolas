"""contact.py out.jpg path...  labelled thumbnails (index, name, mtime) for choosing and captioning sheets"""
import sys, os, cv2, numpy as np, time
from PIL import Image, ImageDraw, ImageFont
out, P = sys.argv[1], sys.argv[2:]; TW, TH = 360, 250; cols = 5
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13) if os.path.exists('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf') else ImageFont.load_default()
rows = (len(P) + cols - 1) // cols; S = Image.new('RGB', (cols * TW, rows * (TH + 20)), (30, 30, 30)); d = ImageDraw.Draw(S)
for i, p in enumerate(P):
    im = cv2.imread(p)
    if im is None: continue
    h, w = im.shape[:2]; s = min(TW / w, TH / h); im = cv2.resize(im, (max(1, int(w * s)), max(1, int(h * s))), interpolation=cv2.INTER_AREA)
    x, y = (i % cols) * TW, (i // cols) * (TH + 20)
    S.paste(Image.fromarray(im[..., ::-1]), (x, y))
    d.text((x + 2, y + TH + 2), f"{i} {os.path.basename(os.path.dirname(p))}/{os.path.basename(p)} {time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(p)))} {w}x{h}", fill=(255, 230, 120), font=F)
S.save(out, quality=80); print(out, len(P))
