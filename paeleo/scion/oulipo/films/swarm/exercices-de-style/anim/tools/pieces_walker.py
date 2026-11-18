"""Split the matted Rol 57642 walker into articulated RGBA pieces (#29 pieces, #32 FK rig), mirrored so he walks to frame left.
Writes rig_walker.json: pieces with origin (top-left in mirrored source px), pivot, parent, z, and drawing-substitution sets."""
import sys, json, numpy as np, cv2
from PIL import Image
d = sys.argv[1]
full = np.asarray(Image.open(f'{d}/walker_rgba_full.png').convert('RGBA')).copy()
h, w = full.shape[:2]; s = w / 1280.0
def P(poly): return (np.array(poly, np.float64) * s).astype(np.int32)
def polymask(poly):
    m = np.zeros((h, w), np.uint8); cv2.fillPoly(m, [P(poly)], 255); return m
A = full[..., 3]
HEADP = [(400,400),(600,400),(600,560),(560,600),(548,620),(462,620),(455,590),(400,560)]
ARMP = [(330,600),(372,628),(366,700),(352,800),(345,880),(352,960),(350,1010),(270,1010),(270,600)]
NEAR = [(533,1120),(620,1120),(620,1480),(515,1480),(522,1395),(532,1200)]
FARL = [(438,1120),(533,1120),(533,1240),(545,1300),(535,1395),(492,1395),(462,1300),(438,1240)]
HEMY = 1105
pieces = {}
def cut(name, m, pivot, extra=None):
    a = (A.astype(np.float32) * (m.astype(np.float32) / 255.0)).astype(np.uint8)
    ys, xs = np.nonzero(a > 8)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    rgba = full[y0:y1, x0:x1].copy(); rgba[..., 3] = a[y0:y1, x0:x1]
    rgba = rgba[:, ::-1]                       # mirror: he faces and walks to frame left
    mx0 = w - x1
    im = Image.fromarray(rgba, 'RGBA'); fn = f'wk_{name}.png'; im.save(f'{d}/{fn}')
    pv = (w - pivot[0] * s, pivot[1] * s)
    pieces[name] = dict(file=fn, origin=[int(mx0), int(y0)], pivot=[round(pv[0], 1), round(pv[1], 1)], size=list(im.size), **(extra or {}))
head = polymask(HEADP); arm = polymask(ARMP); near = polymask(NEAR); far = polymask(FARL)
yy = np.mgrid[0:h, 0:w][0]
cut('head', head, (505, 612), dict(parent='torso', z=5))
cut('arm', arm & ~head, (345, 640), dict(parent='torso', z=4, note='his right sleeve + hand: the hand that lowers the key'))
torso = np.where((yy < HEMY * s + 25 * s) & (head == 0) & (arm == 0), 255, 0).astype(np.uint8)
torso[:int(560 * s)] = 0
cane = polymask([(625,780),(700,780),(700,1330),(625,1330)])
torso = np.maximum(torso, cane & ~near & ~far)
cut('torso', torso, (500, 1060), dict(parent=None, z=3))
hem = np.where((yy >= HEMY * s) & (near == 0) & (far == 0) & (cane == 0), 255, 0).astype(np.uint8)
cut('hem', hem, (500, HEMY), dict(parent='torso', z=2, note='coat skirt: secondary-motion lag'))
cut('leg_straight', near, (576, 1130), dict(parent='torso', z=1, foot=[(1280 - 560) * s, 1460 * s], note='his left leg, planted: STANCE drawing'))
cut('leg_bent', far, (486, 1130), dict(parent='torso', z=1, foot=[(1280 - 512) * s, 1390 * s], note='his right leg, heel lifted: SWING drawing'))
rig = dict(source='Homme marchant dans la rue, Agence Rol 57642, Jan 1920 (BnF btv1b530359957), Commons, Public domain',
           source_px=[w, h], mirrored=True, units='mirrored source px', hip=[round((1280 - 531) * s, 1), round(1130 * s, 1)],
           leg_length=round((1460 - 1130) * s, 1), head_height=round((612 - 404) * s, 1), figure_height=round((1462 - 404) * s, 1),
           substitution=dict(stance='leg_straight', swing='leg_bent'),
           inventions=['arm/torso boundary along the sleeve is a cut line chosen by us (the print shows black wool on black wool)',
                       'leg tops above the hem are coat pixels hidden under the hem piece', 'cane kept with the torso (carried, rigid)'],
           pieces=pieces)
json.dump(rig, open(f'{d}/rig_walker.json', 'w'), indent=1)
print(json.dumps(rig, indent=1)[:1500])
