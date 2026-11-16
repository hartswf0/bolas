"""SCION #29 GrabCut re-cut of Renzo (Arthur S. Siegel, Dodge truck plant lunch hour, 1942; LoC 2017835701, master TIFF
8d07886u fetched by HTTP range at K=4 -> re_8d07886_k4.png, 2x the r2 resolution). Pieces for #32 FK with 4 pins:
hip (body), neck (head), shoulder (upper arm), elbow (forearm+hands). Guides: the r2 masks upscaled x2 (figure) + hand-drawn
scissor polygons for the arm; seeded band GrabCut; one component; 1.2 px feather. The vacated sleeve area on the torso is
backed with knit copied from his own back in the same negative (declared). Jaw substitution drawings: the lower face below the
mouth line re-pinned 3 px / 6 px closed (two extra head drawings, chewing), cut from the same head."""
import os, json, numpy as np, cv2, sys
from PIL import Image
sys.path.insert(0, '/home/user/bolas/paeleo/scion/oulipo/films/swarm/renzo-e-luciana/cutout-build')
SRC = '/home/user/bolas/paeleo/scion/oulipo/films/sources/renzo-e-luciana'
O = SRC + '/editor/pieces'; os.makedirs(O, exist_ok=True)
C2 = '/home/user/bolas/paeleo/scion/oulipo/films/swarm/renzo-e-luciana/test-shot-build/cache2'
def poly(shape, p):
    m = np.zeros(shape, np.uint8); cv2.fillPoly(m, [np.array(p, np.int32)], 255); return m
def largest(m):
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    return np.where(lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]), 255, 0).astype(np.uint8) if n > 1 else m
def fill(m):
    ff = m.copy(); fm = np.zeros((m.shape[0] + 2, m.shape[1] + 2), np.uint8); cv2.floodFill(ff, fm, (0, 0), 255)
    return m | cv2.bitwise_not(ff)
def band_gc(g, guide, band=9, it=6):
    img = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
    lap = cv2.convertScaleAbs(cv2.Laplacian(cv2.GaussianBlur(g, (0, 0), 1.5), cv2.CV_16S, ksize=3))
    img[..., 2] = np.clip(cv2.GaussianBlur(lap, (0, 0), 3) * 3, 0, 255)
    k = np.ones((band, band), np.uint8)
    m = np.full(g.shape, cv2.GC_BGD, np.uint8)
    m[cv2.dilate(guide, k) > 0] = cv2.GC_PR_BGD; m[guide > 0] = cv2.GC_PR_FGD; m[cv2.erode(guide, k) > 0] = cv2.GC_FGD
    b = np.zeros((1, 65)); f = np.zeros((1, 65))
    cv2.grabCut(img, m, None, b, f, it, cv2.GC_INIT_WITH_MASK)
    out = np.where((m == 1) | (m == 3), 255, 0).astype(np.uint8)
    out = cv2.morphologyEx(out, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)); out = cv2.morphologyEx(out, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    return fill(largest(out))
g = np.asarray(Image.open(SRC + '/editor/re_8d07886_k4.png').convert('L')).astype(np.uint8); H, W = g.shape
# figure guide = r2 masks x2 (body crop [195,150], head crop [195,20] in the K=8 image) + the hands
guide = np.zeros((H, W), np.uint8)
for n, (cx, cy) in (('re_body', (195, 150)), ('re_head', (195, 20))):
    a = np.asarray(Image.open(f'{C2}/{n}.png'))[..., 3]
    a2 = cv2.resize(a, (a.shape[1] * 2, a.shape[0] * 2), interpolation=cv2.INTER_LINEAR)
    y0, x0 = cy * 2, cx * 2; h, w = a2.shape; h = min(h, H - y0); w = min(w, W - x0)
    guide[y0:y0 + h, x0:x0 + w] = np.maximum(guide[y0:y0 + h, x0:x0 + w], (a2[:h, :w] > 128) * 255)
FA = [(330, 920), (362, 990), (322, 1072), (232, 1102), (160, 1126), (68, 1116), (48, 1008), (108, 974), (208, 954), (268, 924)]
UA = [(430, 486), (566, 476), (596, 560), (566, 700), (506, 832), (424, 930), (334, 990), (268, 976), (250, 930), (300, 850), (360, 720), (398, 600)]
ARMG = [(400, 480), (440, 470), (560, 480), (600, 560), (580, 1000), (370, 1000), (330, 1078), (160, 1126), (62, 1118), (46, 1004), (110, 972), (240, 930), (300, 820), (360, 660)]
guide = np.maximum(guide, poly(g.shape, ARMG)); guide[1240:] = 0
fig = band_gc(g, guide, 11)
fig[1240:] = 0
ra = fig.sum() / max(guide.sum(), 1); comps = cv2.connectedComponents(fig)[0] - 1
mFA = cv2.bitwise_and(fig, poly(g.shape, FA)); mUA = cv2.bitwise_and(fig, poly(g.shape, UA))
mUA[mFA > 0] = 0
# body: torso + legs + head region minus the arm; the sleeve area is backed with his own back knit (dx = +250)
body = fig.copy(); body[mFA > 0] = 0
gb = g.astype(np.float32).copy()
ys, xs = np.nonzero(mUA)
src_x = np.clip(xs + 250, 0, W - 1)
gb[ys, xs] = g[ys, src_x]
# soft seam between backing and original torso
seam = cv2.GaussianBlur((mUA > 0).astype(np.float32), (0, 0), 3)
gb = g * (1 - seam) + gb * seam
SEAM_Y = 418                                                    # collar line: head piece above, body below (soft 6 px)
yy = np.arange(H)[:, None].astype(np.float32); cut = np.clip((yy - SEAM_Y) / 6.0, 0, 1)
P = {}
def piece(name, grey_img, mask, alpha_mul, pivots, bbox):
    x0, y0, x1, y1 = bbox
    a = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.2) * alpha_mul
    rgba = np.dstack([np.clip(grey_img, 0, 255)[y0:y1, x0:x1].astype(np.uint8)] * 3 + [np.clip(a[y0:y1, x0:x1], 0, 255).astype(np.uint8)])
    Image.fromarray(rgba, 'RGBA').save(f'{O}/{name}.png')
    P[name] = {'file': f'editor/pieces/{name}.png', 'source': '8d07886u (K=4)', 'crop_in_source_px': [x0, y0, x1, y1],
               'pivots': {k: [v[0] - x0, v[1] - y0] for k, v in pivots.items()}}
piece('re2_body', gb, body, cut, {'hip': (660, 1200), 'neck': (580, 410), 'shoulder': (500, 556)}, (300, 330, 897, 1240))
piece('re2_head', g, fig, 1 - cut, {'neck': (580, 410), 'mouth': (428, 332), 'eye': (441, 239)}, (380, 40, 897, 440))
# split the sleeve at the elbow (mid-sleeve, perpendicular to the shoulder->wrist axis) with an 8 px overlap each way
S0, E0, W0 = np.array([500., 556.]), np.array([402., 754.]), np.array([300., 950.])
ax = (W0 - S0) / np.linalg.norm(W0 - S0); YY, XX = np.mgrid[0:H, 0:W]
proj = (XX - E0[0]) * ax[0] + (YY - E0[1]) * ax[1]
mU1 = mUA * (proj < 10); mL1 = mUA * (proj > -10)
piece('re2_uarm', g, mU1, np.ones((H, W)), {'shoulder': (500, 556), 'elbow': (402, 754)}, (240, 470, 610, 1000))
piece('re2_larm', g, mL1, np.ones((H, W)), {'elbow': (402, 754), 'wrist': (300, 950)}, (240, 470, 610, 1000))
piece('re2_farm', g, mFA, np.ones((H, W)), {'elbow': (300, 950), 'wrist': (300, 950), 'grip': (122, 1046)}, (40, 910, 370, 1130))
# jaw substitutions (two chewing drawings): lower face below the mouth line, pinned at the jaw hinge below the ear, closed by 2.5 deg / 5 deg
hd = np.asarray(Image.open(f'{O}/re2_head.png')).astype(np.float32); hx0, hy0 = 380, 40
hinge = (560 - hx0, 330 - hy0)                                   # below the ear
yy2, xx2 = np.mgrid[0:hd.shape[0], 0:hd.shape[1]]
jaw = ((yy2 > (332 - hy0) + (xx2 - (428 - hx0)) * 0.10) & (xx2 < 545 - hx0) & (yy2 < 420 - hy0)).astype(np.float32)
jaw = cv2.GaussianBlur(jaw, (0, 0), 1.5)
for i, ang in ((1, -2.5), (2, -5.0)):
    M = cv2.getRotationMatrix2D(hinge, ang, 1.0)
    jw = cv2.warpAffine(np.dstack([hd[..., 0], hd[..., 3] * jaw]), M, (hd.shape[1], hd.shape[0]), flags=cv2.INTER_LINEAR)
    base_a = hd[..., 3] * (1 - jaw)
    a_out = jw[..., 1] + base_a * (1 - jw[..., 1] / 255.0)
    c_out = (jw[..., 0] * jw[..., 1] + hd[..., 0] * base_a * (1 - jw[..., 1] / 255.0)) / np.maximum(a_out, 1e-3)
    Image.fromarray(np.dstack([np.clip(c_out, 0, 255)] * 3 + [np.clip(a_out, 0, 255)]).astype(np.uint8), 'RGBA').save(f'{O}/re2_head_chew{i}.png')
    P[f're2_head_chew{i}'] = dict(P['re2_head'], file=f'editor/pieces/re2_head_chew{i}.png', note=f'jaw substitution drawing: lower face re-pinned {ang} deg at the jaw hinge')
P['_checks'] = {'figure_components': int(comps), 'figure_area_vs_guide': round(float(ra), 3), 'pass': bool(comps == 1 and .85 < ra < 1.15),
               'uarm_px': int((mUA > 0).sum()), 'farm_px': int((mFA > 0).sum())}
json.dump(P, open(f'{O}/renzo_pieces.json', 'w'), indent=1)
prev = np.where(fig > 0, g, (g * .25 + 190)).astype(np.uint8); prev[mUA > 0] = (prev[mUA > 0] * .6).astype(np.uint8); prev[mFA > 0] = 255 - prev[mFA > 0]
Image.fromarray(cv2.resize(prev, (W // 2, H // 2))).save('/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/re_prev.jpg')
Image.fromarray(cv2.resize(np.clip(gb, 0, 255).astype(np.uint8) * (body > 0), (W // 2, H // 2))).save('/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/re_body.jpg')
print(P['_checks'])
