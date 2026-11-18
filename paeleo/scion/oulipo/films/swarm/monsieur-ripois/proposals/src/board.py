import sys; sys.path.insert(0, __file__.rsplit('/', 1)[0])
from PIL import Image, ImageDraw
from common import *
REF = "/home/user/bolas/paeleo/scion/oulipo/assets/references/ripois1.webp"
cells = [(REF, "Référence · Monsieur Ripois (1954), still"),
         (OUT + "kf-1.png", "1 · Le canapé articulé — photo-cutout puppetry"),
         (OUT + "kf-2.png", "2 · Ombres du retour — shadow theatre (his flashback)"),
         (OUT + "kf-3.png", "3 · Le reçu sur la table — archive + handmade receipt")]
CW, CH, LB, M = 960, 540, 44, 16
B = Image.new("RGB", (2 * CW + 3 * M, 2 * (CH + LB) + 3 * M), (24, 24, 24)); d = ImageDraw.Draw(B); f = font(SERIF_I, 28)
for i, (p, lab) in enumerate(cells):
    im = Image.open(p).convert("RGB"); im.thumbnail((CW, CH), Image.LANCZOS)
    x = M + (i % 2) * (CW + M); y = M + (i // 2) * (CH + LB + M)
    cell = Image.new("RGB", (CW, CH), (6, 6, 6)); cell.paste(im, ((CW - im.width) // 2, (CH - im.height) // 2))
    B.paste(cell, (x, y)); d.text((x + 6, y + CH + 8), lab, font=f, fill=(236, 230, 218))
B.save(OUT + "board.jpg", quality=90); print(B.size)
