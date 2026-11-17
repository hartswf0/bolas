"""Repair 2 (montage editor): Gilliam-style collage graft.  The walker (Rol 57642, 1920, PD) wears a wide-brim felt
hat; the bar asks for a man in a bowler.  We cut the real bowler out of the PD Rol 49112 portrait (1917, « Portrait
d'homme en pardessus et chapeau melon », already cut by the forager: forage/man_rgba.png) along its brim, grade it
to the walker print's tonal range (levels only), cut the felt hat off the walker's head piece, and paste the bowler
on.  Output: animator-pagemaker/cut/wk_head_bowler.png (+ rig_walker.json head entry updated, felt head kept)."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SRC = Path('/home/user/bolas/paeleo/scion/oulipo/films/sources/exercices-de-style')
CUT = SRC / 'animator-pagemaker' / 'cut'
man = Image.open(SRC / 'forage' / 'man_rgba.png').convert('RGBA')
head = Image.open(CUT / 'wk_head.png').convert('RGBA')

# --- 1. the bowler, cut below its brim (scissor path traced by eye on the 2x crop, src px)
brim = [(318, 400), (327, 406), (360, 428), (390, 435), (450, 429), (500, 419), (560, 406), (620, 390), (690, 377),
        (712, 372), (740, 330), (760, 330), (760, 130), (300, 130), (300, 400)]
keep = Image.new('L', man.size, 0); ImageDraw.Draw(keep).polygon(brim, fill=255)
box = (300, 130, 760, 440)
bw = man.crop(box); km = keep.crop(box)
a = np.minimum(np.asarray(bw.getchannel('A')), np.asarray(km))
g = np.asarray(bw.convert('L'), np.float32)
# levels: bowler p5/p95 -> felt hat p5/p95 of the walker print (grade only to unify real material)
hg = np.asarray(head.convert('L'), np.float32); ha = np.asarray(head.getchannel('A'))
hat_px = hg[20:100, 70:210][ha[20:100, 70:210] > 200]
bp = g[a > 200]
b5, b95 = np.percentile(bp, [5, 95]); h5, h95 = np.percentile(hat_px, [5, 95])
h95 = max(h95, h5 + 70)                                  # keep the bowler's real highlight on the crown readable
g2 = ((g - b5) / (b95 - b5) * (h95 - h5) + h5).clip(0, 255)
bowl = Image.merge('RGBA', [Image.fromarray(g2.astype(np.uint8))] * 3 + [Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))])

# --- 2. the felt hat off the walker's head piece
TOP = 22                                                # canvas grows upward so the bowler crown fits
H2 = Image.new('RGBA', (head.size[0], head.size[1] + TOP), (0, 0, 0, 0))
hd = np.asarray(head).copy()
L = hg
yy, xx = np.mgrid[0:head.size[1], 0:head.size[0]]
kill = (yy < 118) | ((yy < 156) & (L < 80) & ((xx < 82) | (xx > 188))) | ((yy < 160) & (xx > 205))
hd[..., 3] = np.where(kill, 0, hd[..., 3])
H2.alpha_composite(Image.fromarray(hd), (0, TOP))

# --- 3. paste, MIRRORED (the walker print is mirrored too): the brim's low side then falls over his right temple,
# where the felt brim hid the head and no real pixels exist.  Brim width 250 px; lowest brim point -> (214, 150).
sc = 250.0 / 440.0
bowl = bowl.transpose(Image.FLIP_LEFT_RIGHT).resize((int(bowl.size[0] * sc), int(bowl.size[1] * sc)), Image.LANCZOS)
lo = ((460 - (390 - 300)) * sc, (435 - 130) * sc)       # mirrored local coords of the brim's lowest point
bx = int(round(214 - lo[0])); by = int(round(150 + TOP - lo[1]))
H2.alpha_composite(bowl, (bx, by))
H2.save(CUT / 'wk_head_bowler.png')

rig = json.load(open(CUT / 'rig_walker.json'))
hp = rig['pieces']['head']
if 'felt_hat_original' not in hp:
    hp['felt_hat_original'] = dict(file=hp['file'], origin=list(hp['origin']), size=list(hp['size']))
o = hp['felt_hat_original']
hp.update(file='wk_head_bowler.png', origin=[o['origin'][0], o['origin'][1] - TOP], size=[H2.size[0], H2.size[1]],
          graft='repair 2: felt hat cut off; bowler cut from Rol 49112 (1917, PD, forage/man_rgba.png) along its brim, '
                'levels-graded to the walker print, pasted (Gilliam collage; declared)')
rig.setdefault('inventions', [])
note = 'head: the bowler is grafted from a second PD Agence Rol print (Rol 49112, 1917); the felt hat of Rol 57642 is cut away'
if note not in rig['inventions']:
    rig['inventions'].append(note)
json.dump(rig, open(CUT / 'rig_walker.json', 'w'), indent=1, ensure_ascii=False)
print('bowler graft', H2.size, 'levels', (round(b5), round(b95)), '->', (round(h5), round(h95)), 'paste', (bx, by))
