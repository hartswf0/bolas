"""testshot-contact.jpg: calvino.webp (look target only) beside 5 frames of testshot.mp4, with tonal/grain measures -> measures.json."""
import json, subprocess, numpy as np, cv2, sys
from PIL import Image, ImageDraw, ImageFont
D = '/home/user/bolas/paeleo/scion/oulipo/films/swarm/renzo-e-luciana'; MP4 = D + '/testshot.mp4'
ref = Image.open('/home/user/bolas/paeleo/scion/oulipo/assets/references/calvino.webp').convert('RGB')
def meas(im):
    a = np.asarray(im.convert('RGB')).astype(np.float32); g = a.mean(2)
    if g.shape[1] != 960: g = cv2.resize(g, (960, int(g.shape[0] * 960 / g.shape[1])), interpolation=cv2.INTER_AREA)
    hp = g - cv2.GaussianBlur(g, (0, 0), 2)
    return {'median': float(np.median(g)), 'p5': float(np.percentile(g, 5)), 'p95': float(np.percentile(g, 95)), 'std': round(float(g.std()), 1),
            'highpass_std': round(float(hp.std()), 2), 'chroma': round(float((a.max(2) - a.min(2)).mean()), 2)}
def fmt(m): return 'med %d p5 %d p95 %d std %d hp %.1f chroma %.1f' % (m['median'], m['p5'], m['p95'], m['std'], m['highpass_std'], m['chroma'])
def grab(t):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t), '-i', MP4, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    return Image.fromarray(np.frombuffer(raw, np.uint8).reshape(540, 960, 3))
FR = [(0.30, 'A film 4.8 (12:00:58) WIDE: foreman FRONT faces the floor; Renzo alone, head to the clock'),
      (3.90, 'A film 8.4 (12:01:41) bite 1: her forearm (elbow pin) puts the apple to his mouth'),
      (5.50, 'A film 10.0 (12:02:00) DEFINING: she holds the bitten apple up, he watches the clock, foreman back turned'),
      (6.50, 'A film 11.0 (12:02:12) bite 2: hers (the photograph\'s own pose)'),
      (14.5, 'B film 45.5 (12:01:42) alone: head down to her empty place, the apple on her lid')]
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 17)
W = 960; out = Image.new('RGB', (W * 2 + 30, 3 * 580 + 40), (250, 250, 250)); d = ImageDraw.Draw(out)
r = ref.copy(); r.thumbnail((W, 540)); out.paste(r, (10 + (W - r.width) // 2, 40)); rm = meas(ref)
d.text((14, 12), 'REFERENCE calvino.webp (look target only)  ' + fmt(rm), fill=(0, 0, 0), font=F)
res = {'reference': rm, 'frames': []}
for i, (t, l) in enumerate(FR):
    im = grab(t); x = 10 + ((i + 1) % 2) * (W + 10); y = 40 + ((i + 1) // 2) * 580
    out.paste(im, (x, y)); d.text((x + 4, y - 26), l, fill=(0, 0, 0), font=F); m = meas(im)
    d.rectangle([x, y + 514, x + 560, y + 540], fill=(0, 0, 0)); d.text((x + 6, y + 518), fmt(m), fill=(255, 255, 255), font=F)
    res['frames'].append({'testshot_t': t, 'label': l, **m})
out.save(D + '/testshot-contact.jpg', quality=88)
json.dump(res, open(D + '/cutout-build/measures.json', 'w'), indent=1); print(json.dumps(res, indent=0))
