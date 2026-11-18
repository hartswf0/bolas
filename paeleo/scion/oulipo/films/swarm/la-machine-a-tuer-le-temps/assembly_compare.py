"""Assembler's side-by-side check (plan section 13, acceptance 4 and 5).

Stills from the rendered film (decoded from the delivered mp4) and the lossless
pre-encode frames, at S1, end of S5, S3 and S7, beside oucipo.webp.  Writes
sources/.../assembly/compare.jpg and assembly/measures.json.
Usage: python3 assembly_compare.py [MP4]
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import notebook_rig as R

ROOT = R.ROOT
SLUG = 'la-machine-a-tuer-le-temps'
OUTD = R.SRC / 'assembly'
MP4 = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'assets/films' / f'{SLUG}.mp4'
REF = ROOT / 'assets/references/oucipo.webp'
LED = {e['frame']: e for e in json.load(open(HERE / 'render-ledger.json'))['ledger']}
RIG = json.load(open(OUTD / 'nb' / 'rig-ledger.json'))
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 17)
TL = R.TL
STILLS = {'S0': 30, 'S1': 110, 'S5-end': TL['S5'][1] - 6,
          'S3 02': TL['S3'][0] + 60 + 36, 'S3 07': TL['S3'][0] + 360 + 30,
          'S3 01': TL['S3'][0] + 3, 'S3 01b': TL['S3'][0] + 53, 'S3 04': TL['S3'][0] + 198, 'S3 04b': TL['S3'][0] + 248,
          'S7 05 hold': TL['S7'][0] + 60, 'S7 04': TL['S7'][0] + 126, 'S7 01': TL['S7'][0] + 400, 'S10 label': TL['S10'][0] + 100, 'S7 02': TL['S7'][0] + 168 + 60, 'S7 08': TL['S7'][0] + 492 + 30}


def decode(f):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(MP4), '-vf', f'select=eq(n\\,{f})', '-vsync', '0',
                          '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(720, 1280, 3)


def lossless(f):
    e = LED[f]
    if e['asset_id'] == 'notebook':
        return np.asarray(Image.open(OUTD / 'nb' / f'{f:04d}.png').convert('RGB'))
    return np.asarray(Image.open(R.REG / 'assets' / e['asset_id'] / f"{e['src_frame']:04d}.png").convert('RGB'))


def med(a, box):
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    r = a[y0:y1, x0:x1].reshape(-1, 3).astype(int)
    return [int(v) for v in np.median(r, 0)]


def ob(V, b):
    return R.to_out(V, b)[0]


def notebook_meas(a, f):
    V = RIG[str(f)]['view']; m = {}
    if f < TL['S0'][1]:
        ox, oy = R.face_origin('R')
        m['cover'] = med(a, ob(V, (ox + 60, oy + 700, ox + 980, oy + 960)))
        return m
    if 'slips' not in RIG[str(f)]:
        return {'coda': 'sheet with typed label (legibility checked by eye)'}
    for sd in ('L', 'R'):
        ox, oy = R.face_origin(sd)
        m['page_' + sd] = med(a, ob(V, (ox + 120, oy + 1220, ox + 900, oy + 1330)))
    sl = RIG[str(f)]['slips']
    k = [kk for kk, v in sl.items() if v[0] == 'page' and v[1] == RIG[str(f)]['spread'][1]][0]
    s = R.slips()[k]; x, y = s.rest_xy('R')
    tb = ob(V, (x + s.tape_xy[0] + 20, y + s.tape_xy[1] + s.tape.height * .3,
                x + s.tape_xy[0] + s.tape.width - 20, y + s.tape_xy[1] + s.tape.height * .7))
    reg = a[int(tb[1]):int(tb[3]), int(tb[0]):int(tb[2])].reshape(-1, 3).astype(int)
    band = reg[reg.mean(1) > np.percentile(reg.mean(1), 40)]
    m['tape_band'] = [int(v) for v in np.median(band, 0)]
    ai = a.astype(int)
    red = ai[(ai[..., 0] - ai[..., 1] >= 50) & (ai[..., 0] > 120)]
    m['red_pixels'] = int(len(red))
    if len(red):
        m['red_R_minus_G_median'] = int(np.median(red[:, 0] - red[:, 1]))
    return m


def print_meas(a):
    a = a.astype(int); l = a.mean(2)
    return dict(p1=round(float(np.percentile(l, 1)), 1), p99=round(float(np.percentile(l, 99)), 1),
                median=round(float(np.median(l)), 1), median_R_minus_B=int(np.median(a[..., 0] - a[..., 2])))


def dist(c, t):
    return max(abs(x - y) for x, y in zip(c, t))


meas = {'mp4': str(MP4)}
imgs = {}
for name, f in STILLS.items():
    d, l = decode(f), lossless(f)
    imgs[name] = d
    nb = LED[f]['asset_id'] == 'notebook'
    meas[name] = dict(frame=f, tc='%05.2f s' % (f / 24), source=LED[f]['asset_id'] + ('' if nb else ' src %d' % LED[f]['src_frame']),
                      mp4=notebook_meas(d, f) if nb else print_meas(d),
                      lossless=notebook_meas(l, f) if nb else print_meas(l))
ref = np.asarray(Image.open(REF).convert('RGB'))
meas['reference'] = dict(page_left=med(ref, (620, 470, 900, 560)), page_right=med(ref, (1060, 470, 1380, 560)),
                         cover=med(ref, (60, 340, 460, 440)), print15=print_meas(ref[133:338, 583:928]),
                         print16=print_meas(ref[125:328, 1048:1388]))
# acceptance 4/5 verdicts on the delivered mp4
T = dict(page=(240, 232, 215), tape=(223, 190, 135), cover=(97, 14, 24))
v = {}
for n in ('S1', 'S5-end'):
    m = meas[n]['mp4']
    v[n] = dict(page_L=dist(m['page_L'], T['page']) <= 12, page_R=dist(m['page_R'], T['page']) <= 12,
                tape=dist(m['tape_band'], T['tape']) <= 25, red=m.get('red_R_minus_G_median', 0) >= 50)
v['S0 cover'] = dist(meas['S0']['mp4']['cover'], T['cover']) <= 15
for n in STILLS:
    if n.startswith('S3') or n.startswith('S7'):
        m = meas[n]['mp4']
        v[n] = dict(p1=14 <= m['p1'] <= 36, p99=210 <= m['p99'] <= 238, RB=3 <= m['median_R_minus_B'] <= 16)
# speed-0.5 hold: identical pairs in the ledger (pre-encode) for B 05
g7 = TL['S7'][0]
pairs = [LED[g7 + 2 * i]['md5'] == LED[g7 + 2 * i + 1]['md5'] for i in range(60)]
v['B 05 hold identical pairs (pre-encode)'] = all(pairs)
meas['verdicts'] = v
json.dump(meas, open(OUTD / 'measures.json', 'w'), indent=1)

W = 960; rh = int(ref.shape[0] * W * 2 / ref.shape[1])
cols = 3; tw, th = 640, 360
rows = (len(STILLS) + cols - 1) // cols
sheet = Image.new('RGB', (W * 2, 30 + rh + rows * (th + 30) + 10), (250, 249, 246)); d = ImageDraw.Draw(sheet)
d.text((10, 6), 'REFERENCE oucipo.webp (not copied, not traced) | below: frames decoded from the delivered mp4', font=F, fill=(20, 20, 20))
sheet.paste(Image.fromarray(ref).resize((W * 2, rh)), (0, 30))
for i, (n, f) in enumerate(STILLS.items()):
    x, y = (i % cols) * tw, 30 + rh + (i // cols) * (th + 30)
    d.text((x + 8, y + 5), '%s  f%d  %s' % (n, f, json.dumps(meas[n]['mp4'])[:70]), font=F, fill=(20, 20, 20))
    sheet.paste(Image.fromarray(imgs[n]).resize((tw, th)), (x, y + 26))
sheet.save(OUTD / 'compare.jpg', quality=86)
print(json.dumps(meas, indent=1))
