"""Cameo sprites for the CRASH LAB site. Each cameo world (crash/m_zcameo.js) is rendered frame by frame at one shared
scale, so Shim stays taller than Bola and Dot stays little, cropped to the union of its frames, and written as a
horizontal sprite strip (WebP). The manifest records the frame size and the anchor the site positions by: the soles for
standing poses, the seat for sitting, the hands for peeking. Odysseus is drawn with the Found Odyssey ink renderer from
Bola's joints in the same poses. Usage: python3 cameos.py [name ...]"""
import sys, os, math, json, numpy as np, cv2
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path[:0] = [S + '/hybrid', S + '/ody', S + '/hybrid/hand', S + '/cast']
from hyb import Page, ortho
R = '/home/claude/bolas'; OUT = R + '/media/cameo'; os.makedirs(OUT, exist_ok=True)
W, H, ZOOM, C = 520, 720, 1.0, [0, 100, 0]
SC = H * .86 / 230 * ZOOM                     # px per cm, same for every cast member
POSES = ['wave', 'point', 'shrug', 'peek', 'jump', 'sit']
CAST = [('bola', 'A'), ('shim', 'B'), ('dot', 'C'), ('critic', 'Cb')]
ANCHOR = {'sit': 'pelvis', 'peek': 'wrist'}
only = set(sys.argv[1:])

def blindfold(img, J, yaw):
    P = ortho(yaw, 4, np.array(C, float), SC, W, H)
    h = np.array(J['head']); eL, eR = np.array(J['eyeL']), np.array(J['eyeR']); mid = (eL + eR) / 2
    ax = eL - eR; ax /= np.linalg.norm(ax); fw = mid - h; fw -= ax * fw.dot(ax); r = np.linalg.norm(fw) * 1.12 + 1.5; fw /= np.linalg.norm(fw)
    up = np.cross(fw, ax); up /= np.linalg.norm(up); c0 = h + up * (mid - h).dot(up)
    arc = [c0 + (ax * math.cos(a) + fw * math.sin(a)) * r for a in np.linspace(-.05, math.pi + .05, 25)]
    th = max(5, int(np.linalg.norm(P(h) - P(h + up * r)) * .42))
    q = np.int32([P(p) for p in arc if (p - c0).dot(fw) > -r * .1])
    if len(q) > 1: cv2.polylines(img, [q], False, (30, 26, 34, 255), th, cv2.LINE_AA)
    return img

def anchor_y(J, pose, yaw):
    P = ortho(yaw, 12 if pose == 'sit' else 4, np.array(C, float), SC, W, H)
    if pose == 'sit': return P(np.array(J['pelvis']))[1] + 10
    if pose == 'peek': return (P(np.array(J['wristL']))[1] + P(np.array(J['wristR']))[1]) / 2
    return max(P(np.array(J[k]))[1] for k in ('heelL', 'heelR', 'ballL', 'ballR'))

def strip(frames, ay):
    a = np.max([f[..., 3] for f in frames], axis=0); ys, xs = np.where(a > 8)
    x0, x1, y0, y1 = max(0, xs.min() - 6), min(W, xs.max() + 7), max(0, ys.min() - 6), min(H, ys.max() + 7)
    crop = [cv2.resize(f[y0:y1, x0:x1], ((x1 - x0) // 2, (y1 - y0) // 2), interpolation=cv2.INTER_AREA) for f in frames]
    return np.hstack(crop), dict(w=int(x1 - x0) // 2, h=int(y1 - y0) // 2, n=len(frames), ay=round(float(ay - y0) / (y1 - y0), 3), ppc=round(SC / 2, 3))

man = json.load(open(OUT + '/cameos.json')) if os.path.exists(OUT + '/cameos.json') else {}
pg = Page()
for name, aid in CAST:
    for pose in POSES:
        key = f'{name}-{pose}'
        if only and key not in only and name not in only: continue
        cid = f'cam_{name}_{pose}'; JJ = pg.joints(cid); n = len(JJ) - 1
        for view, yaw in (('', -32), ('-back', 180)) if pose == 'sit' else (('', 0),):
            ims = pg.render(cid, [dict(W=W, H=H, yaw=yaw, elev=12 if pose == 'sit' else 4, zoom=ZOOM, c=C, show=[aid], noFx=True, f=f) for f in range(n)])
            if aid == 'Cb' and yaw != 180: ims = [blindfold(im, JJ[f][aid], yaw) for f, im in enumerate(ims)]
            sp, m = strip(ims, np.mean([anchor_y(JJ[f][aid], pose, yaw) for f in range(n)]))
            cv2.imwrite(f'{OUT}/{key}{view}.webp', sp, [cv2.IMWRITE_WEBP_QUALITY, 88]); man[key + view] = m
            print(key + view, m, flush=True); json.dump(man, open(OUT + '/cameos.json', 'w'), indent=0)
pg.close()

# Odysseus: the ink renderer on the same keyed bodies
if not only or 'odysseus' in only:
    import toon
    from common import pcam
    cam = pcam(W=960, H=720, floor_v=690, horizon_v=300, fig_px=300); P = lambda X: cam.proj(X)[0]
    pg = Page()
    for pose in ['wave', 'point', 'shrug', 'jump', 'sit', 'peek']:
        JJ = pg.joints(f'cam_bola_{pose}'); n = len(JJ) - 1; ims = []; ays = []
        for f in range(n):
            J = {k: [v[0], v[1], v[2] - 900] for k, v in JJ[f]['A'].items()}
            rgb, al = toon.render_layer(960, 720, 2, lambda ctx: toon.draw_figure(ctx, P, J, 2, dict(smile=.5)))
            im = np.dstack([np.uint8(np.clip(rgb, 0, 1) * 255), np.uint8(np.clip(al, 0, 1) * 255)])[:, 220:740]; ims.append(im)
            ays.append(P(J['pelvis'])[1] + 10 if pose == 'sit' else (P(J['wristL'])[1] + P(J['wristR'])[1]) / 2 if pose == 'peek' else max(P(J[k])[1] for k in ('heelL', 'heelR', 'ballL', 'ballR')))
        sp, m = strip(ims, np.mean(ays)); cv2.imwrite(f'{OUT}/odysseus-{pose}.webp', sp, [cv2.IMWRITE_WEBP_QUALITY, 88]); man[f'odysseus-{pose}'] = m
        print('odysseus', pose, m, flush=True)
    pg.close()
json.dump(man, open(OUT + '/cameos.json', 'w'), indent=0)
