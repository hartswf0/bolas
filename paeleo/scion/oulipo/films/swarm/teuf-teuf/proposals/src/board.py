import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from common import *
from PIL import Image, ImageDraw
cw, ch, pad, lab = 960, 540, 20, 40
B = Image.new("RGB", (2 * cw + 3 * pad, 2 * (ch + lab) + 3 * pad), (24, 22, 20))
items = [(ROOT + "/assets/references/teuf.webp", "Reference: Teuf-Teuf (Jabely, 1956), still via Cité Films"),
         (OUT + "/kf-1.png", "1 · La paroi: charcoal cutout puppets on the rock (rollers, 27 s)"),
         (OUT + "/kf-2.png", "2 · Ombres des relevés: engravings cut to silhouettes (wheel, 40 s)"),
         (OUT + "/kf-3.png", "3 · Pochoirs du mouvement: simulation as stencils (comparison, 52 s)")]
d = ImageDraw.Draw(B); f = font(26, "serif")
for i, (p, t) in enumerate(items):
    im = Image.open(p).convert("RGB"); im.thumbnail((cw, ch), Image.LANCZOS)
    x = pad + (i % 2) * (cw + pad); y = pad + (i // 2) * (ch + lab + pad)
    B.paste(im, (x + (cw - im.width) // 2, y + lab + (ch - im.height) // 2))
    d.text((x, y + 4), t, font=f, fill=(236, 230, 210))
B.save(OUT + "/board.jpg", quality=90); print(B.size)
