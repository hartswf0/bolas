import sys; sys.path.insert(0, '.')
from common import *
TW, TH, LB = 960, 540, 40
labels = ['Reference · Renzo e Luciana (1962), Cineteca di Bologna still', '1 · Il paravento (silhouette theatre, handmade) · B 12:03, t = 42 s',
          '2 · Collage al marcatempo (LoC FSA/OWI cutouts) · A 12:02, t = 8 s', '3 · Cartellini (light-box score, handmade) · B slide, t = 33 s']
ims = [Image.open(ROOT + '/assets/references/calvino.webp').convert('RGB')] + [Image.open(f'{OUT}/kf-{i}.png').convert('RGB') for i in (1, 2, 3)]
B = Image.new('RGB', (TW * 2, (TH + LB) * 2), (24, 24, 24)); d = ImageDraw.Draw(B); fn = font(20, '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
for k, im in enumerate(ims):
    x, y = (k % 2) * TW, (k // 2) * (TH + LB)
    t = im.copy(); t.thumbnail((TW, TH), Image.LANCZOS)
    B.paste(t, (x + (TW - t.width) // 2, y + LB + (TH - t.height) // 2))
    d.text((x + 12, y + 9), labels[k], font=fn, fill=(235, 232, 222))
B.save(OUT + '/board.jpg', quality=88); print(B.size)
