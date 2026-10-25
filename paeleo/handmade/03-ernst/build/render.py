"""SCION 03 Ernst · render the 768 scene frames: plate + person + pasted fragments + dog, engraved, with the caption.

python3 render.py [start end] [--step k]   -> build/cache/frames/s%04d.png and build/cache/trace_parts/*.json
"""
import json, os, sys, pickle, copy
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import sdf, plate, compose, burin, dogplate
import dog as D
import person as PR
import timeline as TL

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache')
OUT = os.path.join(CACHE, 'frames')
H, W = plate.H, plate.W
TLD = pickle.load(open(os.path.join(CACHE, 'timeline.pkl'), 'rb'))
FRAG = {n: dict(np.load(os.path.join(CACHE, 'frag_%s.npz' % n))) for n in ('lion_head', 'lion_head_b', 'lion_mask', 'hand', 'lantern')}
FONT = ImageFont.truetype(os.path.join(CACHE, 'literata_it.ttf'), 23)
_static = None
_door_cache = {}
DOORTOP = plate.DOOR_H + 0.4


def static():
    global _static
    if _static is None:
        p = os.path.join(CACHE, 'plate_static.pkl')
        if os.path.exists(p):
            _static = pickle.load(open(p, 'rb'))
        else:
            _static = plate.build_static()
            pickle.dump(_static, open(p, 'wb'))
    return _static


def warp(arr, center, scale, rot_deg, out_shape=(H, W)):
    """place a fragment array (h,w) centred at `center` (px), scaled and rotated (bilinear).
    Returns (box, values) with box = (x0, y0, x1, y1) in the frame."""
    h, w = arr.shape
    a = np.radians(rot_deg)
    ca, sa = np.cos(a), np.sin(a)
    hw, hh = w * scale / 2, h * scale / 2
    cs = np.array([[-hw, -hh], [hw, -hh], [hw, hh], [-hw, hh]])
    R = np.array([[ca, -sa], [sa, ca]])
    cc = cs @ R.T + np.array(center)
    x0 = int(max(0, np.floor(cc[:, 0].min()))); x1 = int(min(out_shape[1], np.ceil(cc[:, 0].max())))
    y0 = int(max(0, np.floor(cc[:, 1].min()))); y1 = int(min(out_shape[0], np.ceil(cc[:, 1].max())))
    if x1 <= x0 or y1 <= y0:
        return None, None
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(float) + 0.5
    dx = xx - center[0]; dy = yy - center[1]
    fx = (ca * dx + sa * dy) / scale + w / 2
    fy = (-sa * dx + ca * dy) / scale + h / 2
    ix = np.floor(fx - 0.5).astype(int); iy = np.floor(fy - 0.5).astype(int)
    tx = fx - 0.5 - ix; ty = fy - 0.5 - iy
    valid = (ix >= 0) & (iy >= 0) & (ix < w - 1) & (iy < h - 1)
    ix = np.clip(ix, 0, w - 2); iy = np.clip(iy, 0, h - 2)
    v = (arr[iy, ix] * (1 - tx) * (1 - ty) + arr[iy, ix + 1] * tx * (1 - ty) + arr[iy + 1, ix] * (1 - tx) * ty +
         arr[iy + 1, ix + 1] * tx * ty)
    return (x0, y0, x1, y1), np.where(valid, v, 0)


def paste(rgb, name, center, scale, rot, margin_a, tint=None, clip=None):
    f = FRAG[name]
    box, cov = warp(f['cov'], center, scale, rot)
    if box is None:
        return rgb, None
    _, m = warp(f['mask'], center, scale, rot)
    _, mg = warp(f['margin'], center, scale, rot)
    x0, y0, x1, y1 = box
    if clip is not None:
        m = m * clip[y0:y1, x0:x1]; mg = mg * clip[y0:y1, x0:x1]
    mg = mg * margin_a
    paper = burin.PAPER if tint is None else tint
    sub = rgb[y0:y1, x0:x1]
    sub = sub * (1 - mg[..., None]) + np.array([248, 244, 232]) / 255 * mg[..., None]
    frag = paper * (1 - cov[..., None]) + burin.INK * cov[..., None]
    a = np.clip(m, 0, 1)[..., None]
    rgb[y0:y1, x0:x1] = sub * (1 - a) + frag * a
    return rgb, box


_spill_cache = {}


def spill(light, ang):
    key = (round(light, 3), round(ang, 3))
    if key not in _spill_cache:
        _spill_cache.clear()
        _spill_cache[key] = plate.light_spill(light, ang)
    return _spill_cache[key]


def door_plate(ang, light, dk):
    key = (round(ang, 3), round(light, 3), round(dk, 2))
    if key in _door_cache:
        return _door_cache[key]
    L = copy.deepcopy(static())
    plate.door_layer(L, ang, light)
    _door_cache.clear()
    _door_cache[key] = L
    return L


def soft_ellipse(cx, cy, rx, ry):
    yy, xx = plate.gy, plate.gx
    return np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2) * 1.6)


def render_frame(i):
    d = TLD['dog'][i]; q = TLD['person'][i]
    t = d['t']
    ang, light = TL.door_state(t)
    dk = TL.dusk(t)
    L = door_plate(ang, light, dk)
    fl, air = spill(light, ang)
    # contact shadows (dog, person) darken the boards before the burin cuts them
    Lr = copy.copy(L)
    Lr.dark = L.dark.copy()
    prims_d, Jd = D.build(d)
    mid = (Jd['chest'] + Jd['rump']) / 2
    sx, sy, _ = sdf.project(np.array([mid[0], 0.0, mid[2]]))
    Fd, _ = D.frame(d['phi'])
    ext = abs(Fd[0]) * 0.42 + 0.18
    sh = soft_ellipse(sx, sy, ext * sdf.SCALE, 0.16 * sdf.SCALE * np.sin(sdf.PITCH) + 6) * (0.32 + 0.1 * d['lie'])
    psx, psy, _ = sdf.project(np.array([q['x'] + 0.05, 0.0, q['z']]))
    sh += soft_ellipse(psx, psy, 0.38 * sdf.SCALE, 14) * 0.3
    Lr.dark = np.clip(Lr.dark + sh * (1 - 0.5 * fl), 0, 1)
    # the keystone lion is part of the facade once it has landed (painted before the figures)
    cov, warm = compose.cut_plate(Lr, fl, air, dk)
    tint = compose.paper_tint(warm, dk)
    rgb = burin.compose(cov, tint)
    # the lantern hanging in the hall (seen through the door, behind the door panel), glowing as the light comes
    lc = sdf.project(np.array([0.16, 1.18, -1.4]))
    top = sdf.project(np.array([0.16, DOORTOP, -1.4]))
    clipm = np.clip(L.opening - L.panel_mask, 0, 1)
    ch = (np.abs(plate.gx - lc[0]) < 0.7) & (plate.gy > top[1]) & (plate.gy < lc[1] - 26)
    rgb = np.where((ch * clipm > 0.5)[..., None], burin.INK, rgb)
    rgb, _ = paste(rgb, 'lantern', (lc[0], lc[1]), 0.36, 0, 0.0, tint=np.array([250, 236, 200]) / 255, clip=clipm)
    # -- the person (maquette), its own head hidden while the lion sits on it
    lion_on_head = t < 5.45
    q2 = dict(q)
    q2['head_on'] = not lion_on_head
    hand_frag = q['reach'] > 0.04 or q['low'] * q['sit'] > 0.04
    q2['hands_on'] = {'R': not hand_frag, 'L': True}
    q2['nod'] = 0.12 * q['soft']
    prims_p, Jp = PR.build(q2)
    bp = sdf.render(prims_p)
    head_px = sdf.project(Jp['head'])
    if bp is not None and bp['hit'].any():
        lightP = light * 0.5
        cp, ap, wp = dogplate.engrave(bp, prims_p, doorlight=lightP, dusk=dk * 0.4)
        x0, y0, x1, y1 = bp['box']
        sub = rgb[y0:y1, x0:x1]
        prgb = burin.compose(cp, compose.paper_tint(np.clip(wp * 0.5, 0, 0.6), dk)[:1, :1] * np.ones(cp.shape + (1,)))
        a = ap[..., None]
        rgb[y0:y1, x0:x1] = sub * (1 - a) + prgb * a
    # -- the lion: on the head, in flight, or in the keystone
    nm, c, sc, rot, mg = TL.lion_state(t, head_px, q['mouth'])
    if nm == 'lion_mask' and t >= 6.05:
        rgb, _ = paste(rgb, nm, c, sc, rot, mg, tint=np.array([232, 224, 206]) / 255)
    else:
        rgb, _ = paste(rgb, nm, c, sc, rot, mg)
    # -- the hand: pasted large to reach (cut margin shown), small and low to offer (margin concealed)
    if hand_frag:
        el = sdf.project(Jp['elR']); hd = sdf.project(Jp['handR'])
        dx, dy = hd[0] - el[0], hd[1] - el[1]
        rot = np.degrees(np.arctan2(dy, dx))
        if q['reach'] > 0.04:
            s = 0.17 * (1 + 2.4 * q['reach'] ** 1.5)
            mgA = 1.0
        else:
            s = 0.21; mgA = 0.0
        fw = FRAG['hand']['cov'].shape[1] * s
        ln = np.hypot(dx, dy) + 1e-6
        cen = (hd[0] + dx / ln * fw * 0.42, hd[1] + dy / ln * fw * 0.42)
        rgb, _ = paste(rgb, 'hand', cen, s, rot, mgA)
    # -- the dog
    bd = sdf.render(prims_d)
    tr = dict(i=d['i'], t=round(t, 4), state=d['state'], x_score=TL.FR[i]['dog']['x'])
    if bd is not None and bd['hit'].any():
        # door light reaches the dog when it is near the open door
        cd, ad, wd = dogplate.engrave(bd, prims_d, doorlight=light * 1.0, dusk=dk * 0.35)
        x0, y0, x1, y1 = bd['box']
        sub = rgb[y0:y1, x0:x1]
        wt = np.clip(wd * 0.8, 0, 0.75)[..., None]
        paperD = burin.PAPER[None, None] * (1 - 0.2 * dk) * (1 - wt) + compose.WARM[None, None] * wt
        drgb = paperD * (1 - cd[..., None]) + burin.INK * cd[..., None]
        a = ad[..., None]
        rgb[y0:y1, x0:x1] = sub * (1 - a) + drgb * a
        # measurement from the render: torso pixels (chest, loin, haunch) give the body's screen centre
        ids = bd['id']
        torso = np.isin(ids, [k for k, pr in enumerate(prims_d) if pr.name in ('chest', 'loin', 'haunch')])
        head = np.isin(ids, [k for k, pr in enumerate(prims_d) if pr.name in ('skull', 'muzzle', 'nose')])
        tail = np.isin(ids, [k for k, pr in enumerate(prims_d) if pr.name.startswith('tail') or pr.name == 'haunch'])
        yy, xx = np.nonzero(torso)
        tr['x_screen'] = round(float(xx.mean() + x0), 2)
        tr['y_screen'] = round(float(yy.mean() + y0), 2)
        hy, hx = np.nonzero(head)
        ty_, tx_ = np.nonzero(tail)
        hxm = hx.mean() + x0 if hx.size else tr['x_screen']
        txm = tx_.mean() + x0 if tx_.size else tr['x_screen']
        tr['head_x'] = round(float(hxm), 2)
        tr['facing'] = 1 if hxm < txm else -1          # +1: the head is on the door's side (screen left) of the tail
        P = bd['P']
        tyw = float(P[torso][:, 1].mean())
        hyw = float(P[head][:, 1].mean()) if head.any() else tyw
        top = float(P[torso][:, 1].max())
        tr['torso_h'] = round(tyw, 3); tr['head_h'] = round(hyw, 3); tr['back_h'] = round(top, 3)
        tr['posture'] = 'lying' if tyw < 0.29 else ('crouch' if tyw < 0.47 else 'stand')
        tr['head_below_back'] = bool(hyw + 0.08 < top)
        # how much of the dog is inside the door frame (screen x within the opening) vs outside
        ox0 = sdf.X0 + sdf.SCALE * plate.DOOR_X[0]; ox1 = sdf.X0 + sdf.SCALE * plate.DOOR_X[1]
        hy_all, hx_all = np.nonzero(bd['hit'])
        hx_all = hx_all + x0
        tr['frac_in_frame'] = round(float(((hx_all >= ox0) & (hx_all <= ox1)).mean()), 3)
        zmin = float(P[bd['hit']][:, 2].min())
        tr['z_min'] = round(zmin, 3)
        tr['head_yaw_rel_deg'] = round(float(np.degrees(d['yaw_rel'])), 1)
        tr['contacts'] = d['contact']
    # caption under the plate (the typed circumstance, set as a book's caption)
    rgb = compose.finish(np.clip(rgb, 0, 1))
    img = Image.fromarray((rgb * 255).astype(np.uint8))
    cap = TL.FR[i]['prompt']
    if cap:
        # fade in over the first 8 frames of each caption
        k = i
        while k > 0 and TL.FR[k - 1]['prompt'] == cap:
            k -= 1
        fa = min(1.0, (i - k + 1) / 8.0)
        dr = ImageDraw.Draw(img)
        txt = cap[0].upper() + cap[1:]
        tw = dr.textlength(txt, font=FONT)
        col = tuple(int(c) for c in (np.array(burin.PAPER) * (1 - fa) + np.array(burin.INK) * fa) * 255)
        dr.text(((W - tw) / 2, 650), txt, font=FONT, fill=col)
    return img, tr


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(CACHE, 'trace_parts'), exist_ok=True)
    a = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    b = int(sys.argv[2]) if len(sys.argv) > 2 else TL.N
    step = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    trs = []
    for i in range(a, b, step):
        img, tr = render_frame(i)
        img.save(os.path.join(OUT, 's%04d.png' % i))
        trs.append(tr)
    json.dump(trs, open(os.path.join(CACHE, 'trace_parts', 'p%04d_%04d_%d.json' % (a, b, step)), 'w'))
