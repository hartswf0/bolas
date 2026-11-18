"""Board: the Points cover beside three frames of the test shot, with measurements.
python3 -I compare.py   (after shot.py has written test-shot.mp4)
"""
import os, subprocess, json, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = '/home/user/bolas/paeleo/scion/oulipo'
SW = os.path.join(ROOT, 'films/swarm/la-belle-hortense')
TMP = os.path.join(ROOT, 'films/sources/la-belle-hortense/test-shot/compare')
os.makedirs(TMP, exist_ok=True)
F = ImageFont.truetype('/usr/share/fonts/X11/Type1/c0583bt_.pfb', 20)
f2 = ImageFont.truetype('/usr/share/fonts/X11/Type1/c0419bt_.pfb', 15)

def grab(t):
    p = os.path.join(TMP, f'f_{t:.2f}.png')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.3f}', '-i', os.path.join(SW, 'test-shot.mp4'),
                    '-frames:v', '1', p], check=True)
    return Image.open(p).convert('RGB')

def measure(im):
    a = np.asarray(im)
    hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV).astype(float)
    l = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY).astype(float)
    low = l[l.shape[0] // 2:]
    gy = np.abs(np.diff(low, axis=0)).mean(); gx = np.abs(np.diff(low, axis=1)).mean()
    red = ((hsv[..., 0] < 8) | (hsv[..., 0] > 170)) & (hsv[..., 1] > 150) & (hsv[..., 2] > 60)
    green = (hsv[..., 0] > 25) & (hsv[..., 0] < 90) & (hsv[..., 1] > 60)
    hue = hsv[..., 0][red] * 2; hue = np.where(hue > 180, hue - 360, hue)
    rows = np.where(red.sum(1) > 0.02 * a.shape[1])[0]
    return dict(luma=[int(v) for v in np.percentile(l, [5, 25, 50, 75, 95])], med_sat=int(np.median(hsv[..., 1])),
                gy_gx=round(float(gy / gx), 2), green_pct=round(float(green.mean() * 100), 1),
                red_hue=round(float(np.median(hue)), 1) if red.any() else None,
                red_sat=round(float(np.median(hsv[..., 1][red]) / 255), 2) if red.any() else None,
                red_height=round(float((rows.max() - rows.min()) / a.shape[0]), 2) if len(rows) else 0)

ref = Image.open(os.path.join(ROOT, 'assets/references/hortense.webp')).convert('RGB')
frames = [(2.60, 'film 42.6 s  V.3 MANTEAU, locked on the coat'),
          (3.30, 'film 43.3 s  V.3 the key slips from the fold'),
          (4.70, 'film 44.7 s  V.4 at rest: brass on green')]
ims = [(grab(t), lab) for t, lab in frames]
HH = 380
refr = ref.resize((int(ref.width * HH / ref.height), HH), Image.LANCZOS)
fw = int(960 * HH / 540)
B = Image.new('RGB', (refr.width + 3 * fw + 40, HH + 150), (24, 24, 22)); d = ImageDraw.Draw(B)
B.paste(refr, (0, 40)); d.text((6, 10), 'REFERENCE', font=F, fill=(235, 235, 225))
m = measure(ref)
d.text((6, HH + 48), f"luma p50 {m['luma'][2]}  sat {m['med_sat']}", font=f2, fill=(220, 220, 210))
d.text((6, HH + 68), f"gy/gx {m['gy_gx']}  green {m['green_pct']}%", font=f2, fill=(220, 220, 210))
d.text((6, HH + 88), f"red hue {m['red_hue']}  sat {m['red_sat']}", font=f2, fill=(220, 220, 210))
x = refr.width + 10
out = {'reference': m}
for (im, lab), (t, _) in zip(ims, frames):
    B.paste(im.resize((fw, HH), Image.LANCZOS), (x, 40))
    d.text((x + 4, 10), f'TEST SHOT t={t:.2f}', font=F, fill=(235, 235, 225))
    m = measure(im); out[f'{t:.2f}'] = m
    d.text((x + 4, HH + 48), lab, font=f2, fill=(235, 235, 225))
    d.text((x + 4, HH + 68), f"luma p5/25/50/75/95 {m['luma']}  sat {m['med_sat']}", font=f2, fill=(220, 220, 210))
    d.text((x + 4, HH + 88), f"lower-half gy/gx {m['gy_gx']}  green {m['green_pct']}%", font=f2, fill=(220, 220, 210))
    d.text((x + 4, HH + 108), f"coat hue {m['red_hue']} deg  sat {m['red_sat']}  red height {m['red_height']}", font=f2, fill=(220, 220, 210))
    x += fw + 10
d.text((refr.width + 14, HH + 128), 'targets (plan 10.4): coat hue within 8 deg of #e2011b (-6), sat >= 0.75; green >= 25%; gy/gx >= 1.3 (ref 1.55)', font=f2, fill=(200, 160, 150))
B.save(os.path.join(SW, 'test-shot-compare.jpg'), quality=90)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'measures.json'), 'w'), indent=1)
print(json.dumps(out, indent=1))
