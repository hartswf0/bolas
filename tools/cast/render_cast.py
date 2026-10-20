"""Model sheets for the CRASH LAB site: the crash-test family from the lab's own renderer (front, three-quarter, side, back),
and The Found Odyssey's cast from ody/toon.py on one body."""
import sys, os, math, json, numpy as np, cv2
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path[:0] = [S + '/hybrid', S + '/ody', S + '/hybrid/hand']
from hyb import Page, ortho
OUT = S + '/cast/out'; os.makedirs(OUT, exist_ok=True)
pg = Page()
FAM = [('cast_bola', 'A', 'bola'), ('cast_shim', 'B', 'shim'), ('cast_dot', 'C', 'dot'), ('cast_critic', 'Cb', 'critic'), ('cast_extra', 'D', 'extra')]
W, H = 520, 640
def blindfold(img, J, yaw, elev, c, zoom):
    sc = H * .86 / 230 * zoom; P = ortho(yaw, elev, np.array(c, float), sc, W, H)
    h = np.array(J['head']); eL, eR = np.array(J['eyeL']), np.array(J['eyeR']); mid = (eL + eR) / 2
    ax = eL - eR; ax /= np.linalg.norm(ax); fw = mid - h; fw -= ax * fw.dot(ax); r = np.linalg.norm(fw) * 1.12 + 1.5; fw /= np.linalg.norm(fw)
    up = np.cross(fw, ax); up /= np.linalg.norm(up); c0 = h + up * (mid - h).dot(up)
    arc = [c0 + (ax * math.cos(a) + fw * math.sin(a)) * r for a in np.linspace(-.05, math.pi + .05, 25)]
    th = max(5, int(np.linalg.norm(P(h) - P(h + up * r)) * .42))
    cam = np.array([math.sin(math.radians(yaw)) * -1, 0, math.cos(math.radians(yaw))])
    vis = [i for i, p in enumerate(arc) if (p - c0).dot(fw) > -r * .1]
    q = np.int32([P(arc[i]) for i in vis])
    if len(q) > 1: cv2.polylines(img, [q], False, (30, 26, 34, 255), th, cv2.LINE_AA)
    return img
sheets = {}
for cid, aid, name in FAM:
    J = pg.joints(cid)[0][aid]; c = [0, 92, 0]; row = []
    for yaw in (0, -40, -90, 180):
        o = dict(W=W, H=H, yaw=yaw, elev=4, zoom=1.0, c=c, show=[aid], noFx=True)
        im = pg.render(cid, [dict(o, f=0)])[0]
        if aid == 'Cb' and yaw != 180: im = blindfold(im, J, yaw, 4, c, 1.0)
        row.append(im)
    cv2.imwrite(f'{OUT}/{name}-front.png', row[0])
    sheets[name] = row
# family lineup: front views side by side, sized as the cast is sized (Shim taller, Dot little), on the bay's paper
order = ['bola', 'shim', 'dot']
line = np.hstack([sheets[n][0] for n in order]); cv2.imwrite(f'{OUT}/family-lineup.png', line)
for n, row in sheets.items(): cv2.imwrite(f'{OUT}/{n}-turnaround.png', np.hstack(row))
pg.close()
# The Found Odyssey: one body, many costumes
import toon
from common import pcam
pg = Page(); J = pg.joints('e2t'); pg.close()
cam = pcam(W=960, H=720, floor_v=640, horizon_v=330, fig_px=170); P = lambda X: cam.proj(X)[0]
ODY = [('odysseus', 'Odysseus', dict(smile=.3)), ('odysseus-vase', 'Odysseus, black-figure', dict(style='vase')), ('crew', 'The crew', dict(costume='crew')),
       ('polyphemus', 'Polyphemus', dict(costume='cyclops', mouth=.4)), ('zeus', 'Zeus', dict(costume='zeus', mouth=.3)), ('hermes', 'Hermes', dict(costume='hermes', smile=.8)),
       ('calypso', 'Calypso', dict(costume='calypso', smile=.4, lids=.3)), ('poseidon', 'Poseidon', dict(costume='poseidon', brows=-.8, mouth=.6)), ('circe', 'Circe', dict(costume='circe', smile=.5)),
       ('athena', 'Athena', dict(costume='athena', smile=.2)), ('tiresias', 'Tiresias', dict(costume='tiresias')), ('anticleia', 'Anticleia', dict(costume='anticleia', brows=.6)),
       ('agamemnon', 'Agamemnon', dict(costume='agamemnon', brows=-.5)), ('achilles', 'Achilles', dict(costume='achilles')), ('ajax', 'Ajax', dict(costume='ajax', brows=-.9)),
       ('sisyphus', 'Sisyphus', dict(costume='sisyphus')), ('oldbeggar', 'Odysseus, the old beggar', dict(costume='oldbeggar', lids=.4))]
meta = []
for key, label, L in ODY:
    try:
        rgb, al = toon.render_layer(960, 720, 2, lambda ctx: toon.draw_figure(ctx, P, J[2]['Od'], 2, dict(L)))
    except Exception as e:
        print('skip', key, e); continue
    a = np.uint8(np.clip(al, 0, 1) * 255); im = np.dstack([np.uint8(np.clip(rgb, 0, 1) * 255), a])[120:705, 430:900]
    cv2.imwrite(f'{OUT}/ody-{key}.png', im); meta.append(dict(key=key, label=label))
json.dump(meta, open(f'{OUT}/ody.json', 'w'))
print('cast done', len(meta))
