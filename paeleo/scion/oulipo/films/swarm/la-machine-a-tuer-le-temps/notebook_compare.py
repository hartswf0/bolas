"""Stills at S1, mid-S5, end of S5, S10 (and S0) beside the reference, with
measured colour samples (plan section 13, acceptance 3-4).  Writes
sources/.../notebook/stills/*.png, compare.jpg and measures.json."""
import sys, json, math
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import notebook_rig as R

OUT = R.SRC / 'notebook'; ST = OUT / 'stills'; ST.mkdir(parents=True, exist_ok=True)
REF = R.ROOT / 'assets/references/oucipo.webp'
STILLS = {'S0': 30, 'S1': 110, 'S5-mid': R.TL['S5'][0] + 108, 'S5-end': R.TL['S5'][1], 'S10': R.TL['S10'][1]}
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)


def med(a, box):
    x0, y0, x1, y1 = box
    r = a[y0:y1, x0:x1].reshape(-1, 3)
    return [int(v) for v in np.median(r, 0)], [round(float(v), 1) for v in r.std(0)]


def out_box(V, R_):
    o, _ = R.to_out(V, R_); return tuple(int(round(v)) for v in o)


meas = {}
imgs = {}
for name, f in STILLS.items():
    im, led = R.notebook_frame(f); im.save(ST / f'{name}.png'); imgs[name] = im
    a = np.asarray(im).astype(int); V = led.get('view')
    m = dict(frame=f)
    if name == 'S0':
        ox, oy = R.face_origin('R')
        m['cover'] = med(a, out_box(V, (ox + 60, oy + 700, ox + 980, oy + 960)))
    if name in ('S1', 'S5-end'):
        for sd in ('L', 'R'):
            ox, oy = R.face_origin(sd)
            m['page_' + sd] = med(a, out_box(V, (ox + 120, oy + 1220, ox + 900, oy + 1330)))
        # tape band: the yellowed middle of the tape on the right page
        k = led['slips'] and [kk for kk, v in led['slips'].items() if v == ['page', 2]][0]
        s = R.slips()[k]; x, y = s.rest_xy('R')
        tb = (x + s.tape_xy[0] + 20, y + s.tape_xy[1] + s.tape.height * .3, x + s.tape_xy[0] + s.tape.width - 20, y + s.tape_xy[1] + s.tape.height * .7)
        reg = a[out_box(V, tb)[1]:out_box(V, tb)[3], out_box(V, tb)[0]:out_box(V, tb)[2]].reshape(-1, 3)
        lum = reg.mean(1); band = reg[lum > np.percentile(lum, 40)]
        m['tape_band'] = [int(v) for v in np.median(band, 0)]
        # red marks: pixels clearly red
        red = a[(a[..., 0] - a[..., 1] >= 50) & (a[..., 0] > 120)]
        m['red_pixels'] = int(len(red))
        if len(red):
            m['red_median'] = [int(v) for v in np.median(red, 0)]
            m['red_R_minus_G_median'] = int(np.median(red[:, 0] - red[:, 1]))
        # ink numbers
    meas[name] = m

# a projection frame vs the reference prints
pa = np.asarray(R.asset_frame('05', 0)).astype(int); pl = pa.mean(2)
meas['projection_05_f0'] = dict(p1=round(float(np.percentile(pl, 1)), 1), p99=round(float(np.percentile(pl, 99)), 1),
                                median_R_minus_B=int(np.median(pa[..., 0] - pa[..., 2])))
pa = np.asarray(R.asset_frame('02', 24)).astype(int); pl = pa.mean(2)
meas['projection_02_f24'] = dict(p1=round(float(np.percentile(pl, 1)), 1), p99=round(float(np.percentile(pl, 99)), 1),
                                 median_R_minus_B=int(np.median(pa[..., 0] - pa[..., 2])))
ref = Image.open(REF).convert('RGB')
ra = np.asarray(ref).astype(int)
meas['reference'] = dict(page_left=med(ra, (520, 470, 800, 560)), page_right=med(ra, (900, 470, 1200, 560)), cover=med(ra, (20, 340, 420, 440)))
meas['targets'] = dict(page='within 12 of (240,232,215) [#f0e8d7]', tape_band='within 25 of (223,190,135) [#dfbe87]',
                       red='R-G >= 50', cover='within 15 of (97,14,24) [#610e18]')

# translation-only check on a lifted slip (acceptance 3): NCC of the projected
# print against the rest print re-sampled at the same scale and shift
f = R.TL['S5'][0] + 80; im, led = R.notebook_frame(f)
nccs = {}
for p in led['prints']:
    k = p['asset']; o = p['rect_out']
    x0, y0, x1, y1 = math.ceil(o[0]) + 1, math.ceil(o[1]) + 1, math.floor(o[2]) - 1, math.floor(o[3]) - 1
    if x0 < 0 or y0 < 0 or x1 > R.OW or y1 > R.OH:
        continue
    got = np.asarray(im.crop((x0, y0, x1, y1))).astype(float).mean(2)
    fw, fh = o[2] - o[0], o[3] - o[1]
    exp = np.asarray(R.sample_print(k, ((x0 - o[0]) / fw, (y0 - o[1]) / fh, (x1 - o[0]) / fw, (y1 - o[1]) / fh), (x1 - x0, y1 - y0))).astype(float).mean(2)
    g, e = got - got.mean(), exp - exp.mean()
    nccs[k] = round(float((g * e).sum() / math.sqrt((g * g).sum() * (e * e).sum())), 5)
meas['translation_only_ncc_frame_%d' % f] = nccs
json.dump(meas, open(OUT / 'measures.json', 'w'), indent=1)

# side-by-side sheet
W = 1280; th = int(ref.height * W / ref.width)
sheet = Image.new('RGB', (W * 2, th + 30 + 2 * (360 + 30)), (250, 249, 246)); d = ImageDraw.Draw(sheet)
d.text((10, 5), 'REFERENCE oucipo.webp (Drouot lot 175) - not copied, not traced', font=F, fill=(20, 20, 20))
sheet.paste(ref.resize((W, th)), (0, 30))
y = 30
d.text((W + 10, 5), 'S1 (f %d) notebook-animator rig' % STILLS['S1'], font=F, fill=(20, 20, 20))
sheet.paste(imgs['S1'].resize((W, 720 * W // 1280)), (W, 30))
y = 30 + max(th, 720) + 0
row = [('S0', 'S0 cover'), ('S5-mid', 'mid-S5'), ('S5-end', 'end of S5'), ('S10', 'S10 coda')]
y = 30 + max(th, 720) + 10
for i, (n, lab) in enumerate(row):
    x = (i % 4) * 640
    d.text((x + 10, y), '%s (f %d)' % (lab, STILLS[n]), font=F, fill=(20, 20, 20))
    sheet.paste(imgs[n].resize((640, 360)), (x, y + 25))
yy = y + 25 + 370
lines = [f"{k}: {json.dumps(v)}" for k, v in meas.items() if k not in ('targets',)]
for j, l in enumerate(lines[:12]):
    d.text((10, yy + j * 22), l[:230], font=F, fill=(40, 40, 40))
sheet = sheet.crop((0, 0, W * 2, yy + 12 * 22 + 10))
sheet.save(OUT / 'compare.jpg', quality=88)
print(json.dumps(meas, indent=1))
