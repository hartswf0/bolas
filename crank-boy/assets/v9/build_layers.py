#!/usr/bin/env python3
"""Build version 9's layers from Watson's aligned plates of the school card and the cast sprites.
python3 assets/v9/build_layers.py <folder with the cast sprites (crankboy_motion_proof/assets)>
The four plates in assets/v9/src are the same room at the same size, each with less in it: helmets and machine,
helmets and lectern, machine only, lectern only. Subtracting one from another gives a layer that is already in place:
  machine.png  = where the machine plate differs from the lectern plate, in the machine plate's pixels
  lectern.png  = the same place, in the lectern plate's pixels
  tables_front.png, tables_back.png = the tables' tops, aprons and near legs, cut from the plate by hand-placed outlines,
                 drawn over the pupils of each row
  lectern_front.png = the lectern's front, by a hand-placed outline, so the teacher can stand behind it
Sprites are scaled to the size they are drawn at, times 1.5 for sharpness."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
H = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(H, 'src'); spr = sys.argv[1]
ld = lambda n: Image.open(os.path.join(S, n)).convert('RGB').resize((1309, 816))
mach, lect = ld('plate-machine.jpg'), ld('plate-lectern.jpg')
a, b = np.asarray(mach, np.float32), np.asarray(lect, np.float32)
d = np.abs(a - b).mean(-1)
m = Image.fromarray(((d > 22) * 255).astype(np.uint8))
box = Image.new('L', m.size, 0); ImageDraw.Draw(box).rectangle((930, 260, 1290, 760), fill=255)
m = Image.fromarray(np.minimum(np.asarray(m), np.asarray(box)))
m = m.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MedianFilter(9))
# fill holes: anything enclosed by the machine's outline belongs to it
pad = Image.new('L', (m.width + 2, m.height + 2), 0); pad.paste(m, (1, 1)); ImageDraw.floodfill(pad, (0, 0), 128)
inside = np.asarray(pad.crop((1, 1, m.width + 1, m.height + 1))) != 128
m = Image.fromarray((inside * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))
for img, name in ((mach, 'machine'), (lect, 'lectern')):
    o = img.copy(); o.putalpha(m); bb = m.getbbox(); o.crop(bb).save(os.path.join(H, name + '.png'), optimize=True)
json.dump({'box': m.getbbox()}, open(os.path.join(H, 'machine.json'), 'w'))
# the tables in front of the pupils: tops, aprons and the legs nearest the viewer
T = [[(38, 503), (636, 489), (642, 500), (545, 530), (545, 550), (38, 552)], [(50, 525), (76, 525), (76, 748), (50, 748)], [(538, 525), (568, 525), (568, 745), (538, 745)],
     [(295, 457), (700, 442), (702, 455), (648, 478), (648, 492), (295, 494)], [(298, 470), (314, 470), (314, 585), (298, 585)], [(640, 470), (656, 470), (656, 575), (640, 575)],
     [(105, 438), (344, 426), (344, 440), (300, 452), (105, 455)], [(388, 424), (718, 416), (718, 430), (388, 436)]]
for name, polys in (('tables_front', T[:3]), ('tables_back', T[3:])):
    tm = Image.new('L', mach.size, 0); dr = ImageDraw.Draw(tm)
    for p in polys: dr.polygon(p, fill=255)
    tm = tm.filter(ImageFilter.GaussianBlur(.8)); o = mach.copy(); o.putalpha(tm); o.save(os.path.join(H, name + '.png'), optimize=True)
# the lectern's front, for the teacher to stand behind
lm = Image.new('L', lect.size, 0); ImageDraw.Draw(lm).polygon([(958, 322), (1152, 316), (1182, 374), (1170, 622), (1022, 624), (960, 562)], fill=255)
lm = lm.filter(ImageFilter.GaussianBlur(.8)); o = lect.copy(); o.putalpha(lm); o.crop(lm.getbbox()).save(os.path.join(H, 'lectern_front.png'), optimize=True)
bx = json.load(open(os.path.join(H, 'machine.json'))); bx['lecternFront'] = lm.getbbox(); json.dump(bx, open(os.path.join(H, 'machine.json'), 'w'))
# the cast, scaled
size = {'boy_01_blue': .62, 'boy_02_red': .62, 'boy_03_blue': .62, 'boy_04_teal': .5, 'boy_05_red': .5, 'boy_06_blue': .5,
        'teacher_reading': .56, 'teacher_gesture': .56, 'crankboy_working': .6, 'crank_handle': .6}
os.makedirs(os.path.join(H, 'cast'), exist_ok=True); man = {}
for k, sc in size.items():
    for suf in ('', '_head_rig', '_body_rig'):
        f = os.path.join(spr, k + suf + '.png')
        if not os.path.exists(f): continue
        im = Image.open(f).convert('RGBA'); w, h = int(im.width * sc * 1.5), int(im.height * sc * 1.5)
        im.resize((w, h), Image.LANCZOS).save(os.path.join(H, 'cast', k + suf + '.png'), optimize=True)
        if suf == '_head_rig':   # the neck: the lowest row where the head layer still has pixels
            al = np.asarray(im.split()[3]); rows = np.nonzero(al.max(1) > 40)[0]; cols = np.nonzero(al[rows[-1]] > 40)[0]
            man[k] = {'neck': [float(cols.mean() * sc * 1.5), float(rows[-1] * sc * 1.5)]}
    man.setdefault(k, {}).update({'scale': sc * 1.5})
json.dump(man, open(os.path.join(H, 'cast', 'cast.json'), 'w'), indent=1)
print('layers and', len(size), 'cast members')
