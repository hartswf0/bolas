"""SCION 06 · Whitney — the phase visualizer and the numerical invariant.
psi = 2 theta_dog - 3 theta_house (the 3:2 relation). Locked when d psi/dt ~ 0. The A/B: the same bank with coupling
removed (K = 0, a rational lock replaced by deliberate detuned drift). Writes ../proof/phase.json and ../proof/phase.png."""
import json, math, os
import numpy as np
from PIL import Image, ImageDraw
import harmonic as H

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'proof')
S = H.load_score()
A = H.bank(S, coupled=True); Bd = H.bank(S, coupled=False)
t = H.T
win = {'commands 1.0-7.4': (1.0, 7.4), 'entrain 7.46-14.7': (7.46, 14.7), 'approach 14.7-23.8': (14.7, 23.8), 'sill 23.8-32': (23.8, 31.95)}
res = {'definition': 'psi = 2*theta_dog - 3*theta_house (radians); |dpsi/dt| in rad/s, mean over each window',
       'invariant': 'locked (|dpsi/dt| < 0.05 rad/s, max) through the approach and the sill; drifting (> 1 rad/s mean) under the commands',
       'coupled': {}, 'uncoupled_drift_AB': {}}
for k, (a, b) in win.items():
    m = (t >= a) & (t < b)
    res['coupled'][k] = dict(mean=round(float(np.abs(A['dpsi'][m]).mean()), 4), max=round(float(np.abs(A['dpsi'][m]).max()), 4))
    res['uncoupled_drift_AB'][k] = dict(mean=round(float(np.abs(Bd['dpsi'][m]).mean()), 4), max=round(float(np.abs(Bd['dpsi'][m]).max()), 4))
m = (t >= 14.7)
res['pass'] = bool(np.abs(A['dpsi'][m]).max() < 0.05 and np.abs(A['dpsi'][(t >= 1) & (t < 7.4)]).mean() > 1.0)
json.dump(res, open(os.path.join(OUT, 'phase.json'), 'w'), indent=1)
print(json.dumps(res, indent=1))
# plot: wrapped psi over the scene, coupled (gold) vs uncoupled (grey); plus two Lissajous figures
im = Image.new('RGB', (1280, 520), (8, 9, 22)); d = ImageDraw.Draw(im)
X = lambda tt: 60 + tt / 32 * 800
for arr, col in ((Bd['psi'], (120, 120, 140)), (A['psi'], (255, 205, 120))):
    w = (arr + math.pi) % (2 * math.pi) - math.pi
    pts = [(X(tt), 260 - v / math.pi * 200) for tt, v in zip(t, w)]
    for p in pts:
        d.point(p, fill=col)
for tt, lab in ((1.0, 'call'), (3.42, 'refuse'), (7.46, 'turns to look'), (14.71, 'approach'), (23.79, 'lies down'), (26.4, 'come in')):
    d.line([(X(tt), 50), (X(tt), 470)], fill=(60, 60, 90)); d.text((X(tt) + 3, 475 if lab != 'refuse' else 490), lab, fill=(170, 170, 200))
d.text((60, 20), 'psi = 2 theta_dog - 3 theta_house (wrapped). gold: coupled (the film). grey: K = 0, detuned drift (the A/B)', fill=(220, 220, 240))
for k, (B_, cx, lab) in enumerate(((A, 1000, 'coupled, last 6 s'), (Bd, 1160, 'drift, last 6 s'))):
    jj = np.arange(768 - 144, 768)
    for j in jj:
        d.point((cx + 60 * math.sin(B_['th_dog'][j]), 260 - 60 * math.sin(B_['th_house'][j] + 0.6)), fill=(255, 230, 190))
    d.text((cx - 55, 340), lab, fill=(200, 200, 220))
im.save(os.path.join(OUT, 'phase.png'))
