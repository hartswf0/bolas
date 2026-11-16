"""Reference beside 3 frames of the test shot, labelled, with the tonal/grain measures."""
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
D = '/home/user/bolas/paeleo/scion/oulipo/films/swarm/renzo-e-luciana'
ref = Image.open('/home/user/bolas/paeleo/scion/oulipo/assets/references/calvino.webp').convert('RGB')
def meas(im):
    a = np.asarray(im.convert('RGB')).astype(np.float32); g = a.mean(2)
    if g.shape[1] != 960: g = cv2.resize(g, (960, int(g.shape[0] * 960 / g.shape[1])), interpolation=cv2.INTER_AREA)
    hp = g - cv2.GaussianBlur(g, (0, 0), 2)
    return 'med %d p5 %d p95 %d std %d hp %.1f chroma %.1f' % (np.median(g), np.percentile(g, 5), np.percentile(g, 95), g.std(), hp.std(), (a.max(2) - a.min(2)).mean())
fr = [(f'{D}/test-shot-build/cache/f_{t}.png', l) for t, l in [
      ('1.0', 'A 12:01:42 (film t 8.5) bite 1: her forearm on its elbow pin feeds him'),
      ('2.5', 'A 12:02:00 (film t 10) DEFINING: offer held, his head up to the clock'),
      ('6.75', 'B 12:01:54 (film t 46.5) late bell: he is alone, head to her empty place')]]
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 17)
W = 960; out = Image.new('RGB', (W * 2 + 30, 540 * 2 + 90), (250, 250, 250)); d = ImageDraw.Draw(out)
r = ref.copy(); r.thumbnail((W, 540)); out.paste(r, (10 + (W - r.width) // 2, 40))
d.text((14, 12), 'REFERENCE calvino.webp (look target only)  ' + meas(ref), fill=(0, 0, 0), font=F)
for i, (f, l) in enumerate(fr):
    im = Image.open(f); x = 10 + ((i + 1) % 2) * (W + 10); y = 40 + ((i + 1) // 2) * (540 + 40)
    out.paste(im, (x, y)); d.text((x + 4, y - 26), l, fill=(0, 0, 0), font=F)
    d.text((x + 4, y + 520), meas(im), fill=(255, 255, 255), font=F); print(l, meas(im))
print('ref', meas(ref)); out.save(f'{D}/test-shot-compare.jpg', quality=88)
