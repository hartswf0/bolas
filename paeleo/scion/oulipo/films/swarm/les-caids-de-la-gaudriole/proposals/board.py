"""Board: the reference beside the three keyframes, each labelled."""
import os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
font = lambda s: ImageFont.truetype(os.path.join(ROOT, "assets/fonts/instrument-sans.woff2"), s)
TW = 960
tiles = [("REFERENCE - Lecroart, Les caids de la gaudriole (Oubapo fold)", Image.open(os.path.join(ROOT, "assets/references/fold_extract-000.webp")).convert("RGB")),
         ("1 - LE PLI SUR LA TABLE (stop-motion paper fold)", Image.open(os.path.join(HERE, "kf-1.png")).convert("RGB")),
         ("2 - LA TABLE LUMINEUSE (light-box onion-skin fold)", Image.open(os.path.join(HERE, "kf-2.png")).convert("RGB")),
         ("3 - PHOTO-ROMAN PLIE (archive hands, folded)", Image.open(os.path.join(HERE, "kf-3.png")).convert("RGB"))]
LH = 46
cell_h = 540 + LH
board = Image.new("RGB", (2 * TW + 30, 2 * cell_h + 30), (24, 24, 24))
d = ImageDraw.Draw(board)
for i, (lab, im) in enumerate(tiles):
    x, y = 10 + (i % 2) * (TW + 10), 10 + (i // 2) * (cell_h + 10)
    im = im.copy(); im.thumbnail((TW, 540))
    bg = Image.new("RGB", (TW, 540), (255, 255, 255) if i == 0 else (24, 24, 24))
    bg.paste(im, ((TW - im.width) // 2, (540 - im.height) // 2))
    board.paste(bg, (x, y + LH))
    d.text((x + 4, y + 8), lab, font=font(26), fill=(240, 236, 226))
board.save(os.path.join(HERE, "board.jpg"), quality=90)
print(board.size)
