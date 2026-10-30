"""SCION 37 renderer: skin the meshes (DQS in the film; LBS for the comparison), rasterize everything with raster.py,
shade per pixel (procedural materials, dusk sky light, the room's light through the doorway with splatted shadows),
grade like old film, write JPEG frames to cache/frames and per-frame measurements (from the render's own G-buffer)
to cache/measure/NNNN.json.
usage: python3 render.py A B          render frames A..B-1
       python3 render.py still i path [lbs|dqs] [weights]"""
import json, os, sys, time
import numpy as np
from PIL import Image
from scipy import ndimage
import rig, raster, world
from world import MAT

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
W, H, SS = 1280, 720, int(os.environ.get("SS", "2"))
CACHE = os.path.join(HERE, 'cache'); FRAMES = os.path.join(CACHE, 'frames'); MEAS = os.path.join(CACHE, 'measure')
for d in (FRAMES, MEAS): os.makedirs(d, exist_ok=True)

PF = dict(np.load(os.path.join(CACHE, 'perform.npz')))
DOG = np.load(os.path.join(ROOT, 'assets', 'mesh', 'dog.npz')); PER = np.load(os.path.join(ROOT, 'assets', 'mesh', 'person.npz'))
SK, PSK = rig.dog_skeleton(), rig.person_skeleton()
COAT = np.asarray(Image.open(os.path.join(ROOT, 'assets', 'texture', 'coat.png')), float) / 255
SV, SF, SM = world.static()
HEADBONES = [list(DOG['bones']).index(b) for b in ('head', 'neck2', 'earL', 'earR')]
DOG_HEADW = DOG['W'][:, HEADBONES].sum(1)
MUZZLE_V = int(np.argmax(DOG['V'][:, 0]))
GRID = (-3.6, 5.6, -3.0, 3.2, .02)            # top-down splat grid: x0 x1 z0 z1 cell


def hsh(k):
    return (np.sin(k * 12.9898 + 78.233) * 43758.5453) % 1.


def skin(i, mode='dqs'):
    pose = {n: PF['dog_rot'][i, j] for j, n in enumerate(SK.names)}
    G = SK.fk(pose, PF['dog_root'][i]); S = SK.skin_mats(G)
    f = rig.dqs if mode == 'dqs' else rig.lbs
    Pd = f(DOG['V'], DOG['idx'], DOG['w'], S)
    pp = {n: PF['person_rot'][i, j] for j, n in enumerate(PSK.names)}
    Gp = PSK.fk(pp, PF['person_root'][i]); Sp = PSK.skin_mats(Gp)
    Pp = rig.dqs(PER['V'], PER['idx'], PER['w'], Sp)
    return Pd, Pp, G, S


def splat(P, wts, sigma):
    x0, x1, z0, z1, c = GRID
    nx, nz = int((x1 - x0) / c), int((z1 - z0) / c)
    g = np.zeros((nx, nz))
    ix = ((P[:, 0] - x0) / c).astype(int); iz = ((P[:, 2] - z0) / c).astype(int)
    ok = (ix >= 0) & (ix < nx) & (iz >= 0) & (iz < nz)
    np.add.at(g, (ix[ok], iz[ok]), wts[ok])
    return ndimage.gaussian_filter(g, sigma)

def grid_at(g, P):
    x0, x1, z0, z1, c = GRID
    ix = np.clip(((P[:, 0] - x0) / c).astype(int), 0, g.shape[0] - 1); iz = np.clip(((P[:, 2] - z0) / c).astype(int), 0, g.shape[1] - 1)
    return g[ix, iz]


def sky(cam, pix):
    yy, xx = pix // cam.W, pix % cam.W
    d = cam.ray(xx + .5, yy + .5)
    el = d[:, 1]; az = np.arctan2(d[:, 2], d[:, 0])
    top = np.array([.10, .13, .26]); mid = np.array([.36, .30, .42]); hor = np.array([.88, .55, .36])
    a = np.clip(el / .35, 0, 1)[:, None]
    c = hor * (1 - a) ** 2 + mid * 2 * a * (1 - a) + top * a * a
    # tree line and far hills against the afterglow
    tl = .012 + .010 * np.sin(az * 7 + 1) + .008 * np.sin(az * 19 + 2) + .006 * np.sin(az * 53) + .02 * np.clip(np.sin(az * 3 - .5), 0, 1)
    tree = (el < tl) & (el > -.2)
    c[tree] = np.array([.06, .07, .09]) + .02 * np.sin(az[tree] * 90)[:, None]
    # the yard: the ground plane y = -0.45 seen below the horizon, fading into dusk haze
    g = el < -1e-3
    tg = (cam.eye[1] + .45) / -el[g]; Pg = cam.eye + d[g] * tg[:, None]
    fog = np.clip((tg - 4) / 40, 0, 1)[:, None]
    gc = np.array([.10, .12, .09]) * (1 + .25 * np.sin(Pg[:, 0] * 3 + np.sin(Pg[:, 2] * 2) * 3))[:, None] * .75
    c[g] = gc * (1 - fog) + fog * np.array([.12, .11, .14])
    return c


def surface(P, n, mat, A, i):
    base = np.zeros((len(P), 3)); emis = np.zeros((len(P), 3))
    light = PF['light'][i]
    def M(name): return mat == MAT[name]
    k = M('floor') | M('step')
    if k.any():
        z = P[k, 2] + 5; pl = np.floor(z / .14); fr = (z / .14) % 1
        tone = .40 + .10 * hsh(pl) + .03 * np.sin(P[k, 0] * (25 + 20 * hsh(pl + 3)) + hsh(pl) * 9) + .02 * np.sin(P[k, 0] * 110 + pl)
        tone = tone * np.where(fr < .07, .45, 1.)
        base[k] = tone[:, None] * np.array([.66, .58, .48])
    k = M('siding')
    if k.any():
        y = P[k, 1]; fr = (y / .16) % 1
        tone = .58 * np.where(fr < .14, .62, 1.) * (1 + .03 * np.sin(P[k, 2] * 31 + np.floor(y / .16) * 7))
        base[k] = tone[:, None] * np.array([.70, .76, .80])
    for nm, col in (('trim', (.80, .78, .72)), ('beam', (.30, .27, .24)), ('sill', (.64, .53, .40))):
        k = M(nm)
        if k.any(): base[k] = np.array(col) * (1 + .04 * np.sin(P[k, 0] * 60 + P[k, 2] * 60))[:, None]
    k = M('door')
    if k.any():
        a = A[k]; zz, yy = a[:, 2], a[:, 1]
        panel = (((zz > .12) & (zz < .76)) & (((yy > .25) & (yy < .95)) | ((yy > 1.10) & (yy < 1.85))))
        edge = panel & ((np.abs(zz - .12) < .025) | (np.abs(zz - .76) < .025) | (np.abs(yy - .25) < .025) | (np.abs(yy - .95) < .025)
                        | (np.abs(yy - 1.10) < .025) | (np.abs(yy - 1.85) < .025))
        base[k] = np.array([.17, .30, .25]) * np.where(edge, .55, 1.)[:, None]
    k = M('ifloor')
    if k.any():
        z = P[k, 2] + 5; pl = np.floor(z / .11)
        base[k] = ((.52 + .08 * hsh(pl + 1)) * np.where((z / .11) % 1 < .06, .5, 1))[:, None] * np.array([.62, .42, .27])
    k = M('iwall')
    if k.any():
        base[k] = np.array([.76, .66, .50]) * np.where(P[k, 1] < .9, .78, 1.)[:, None] * np.where(np.abs(P[k, 1] - .9) < .02, .6, 1.)[:, None]
    k = M('rug')
    if k.any():
        bx = np.minimum(np.abs(P[k, 0] + 2.3), np.abs(P[k, 0] + .3)); bz = np.minimum(np.abs(P[k, 2] + .75), np.abs(P[k, 2] - .75))
        border = np.minimum(bx, bz) < .12
        diamond = (np.abs((P[k, 0] + 1.3) * 2) + np.abs(P[k, 2] * 3)) % .6 < .1
        base[k] = np.where(border[:, None], [.62, .46, .20], np.where(diamond[:, None], [.70, .55, .30], [.50, .13, .10]))
    k = M('picture')
    if k.any():
        inner = (np.abs(P[k, 2] + .125) < .34) & (np.abs(P[k, 1] - 1.46) < .24)
        base[k] = np.where(inner[:, None], np.where((P[k, 1] < 1.40 + .05 * np.sin(P[k, 2] * 9))[:, None], [.32, .40, .28], [.62, .62, .52]), [.18, .12, .08])
    k = M('crate')
    if k.any():
        base[k] = ((.42 + .06 * hsh(np.floor(P[k, 1] / .1))) * np.where((P[k, 1] / .1) % 1 < .1, .5, 1))[:, None] * np.array([.80, .62, .45])
    k = M('ground')
    if k.any():
        fog = np.clip((np.hypot(P[k, 0] - 3, P[k, 2]) - 6) / 30, 0, 1)[:, None]
        base[k] = (np.array([.10, .13, .10]) * (1 + .25 * np.sin(P[k, 0] * 13 + np.sin(P[k, 2] * 7) * 3))[:, None]) * (1 - fog) + fog * np.array([.09, .09, .12])
    k = M('lamp')
    if k.any():
        base[k] = [.9, .8, .6]; emis[k] = np.array([1.0, .78, .50]) * (.25 + .9 * light)
    k = M('window')
    if k.any():
        zz, yy = P[k, 2], P[k, 1]
        bar = (np.abs(zz - (world.WIN[0] + world.WIN[1]) / 2) < .025) | (np.abs(yy - (world.WIN[2] + world.WIN[3]) / 2) < .025)
        emis[k] = np.where(bar[:, None], [.05, .04, .03], np.array([.95, .66, .36]) * (.30 + .55 * light))
    k = M('dog')
    if k.any():
        u = np.clip(A[k, 0], 0, 1) * (COAT.shape[1] - 1); v = (1 - np.clip(A[k, 1], 0, 1)) * (COAT.shape[0] - 1)
        base[k] = np.stack([ndimage.map_coordinates(COAT[..., c], [v, u], order=1) for c in range(3)], 1) * 1.05
    k = M('person')
    if k.any():
        r = A[k]
        col = np.tile([.36, .30, .25], (k.sum(), 1))                                 # wool coat
        col[r[:, 1] < .86] = [.16, .16, .19]                                          # trousers
        col[r[:, 1] < .11] = [.10, .08, .07]                                          # shoes
        hand = (r[:, 1] < .86) & (np.abs(r[:, 2]) > .25) & (r[:, 1] > .65)
        col[hand] = [.60, .45, .37]
        headk = r[:, 1] > 1.53; col[headk] = [.58, .44, .36]
        hair = headk & ((r[:, 1] > 1.74) | (r[:, 0] < -.035)); col[hair] = [.12, .10, .09]
        col[(r[:, 1] > .86) & (r[:, 1] < .95)] *= .7                                  # belt
        base[k] = col * (1 + .05 * np.sin(r[:, 0] * 90 + r[:, 1] * 140))[:, None]
    return base, emis


def lighting(P, n, mat, base, emis, i, extra):
    light = PF['light'][i]; door = PF['door'][i]
    def M(name): return mat == MAT[name]
    # ---------------------------------------------------------------- light
    inside = P[:, 0] < world.WALL_IN_X - .005
    # how much of the dusk outside reaches a point: a soft ramp across the doorway, none deeper in the room
    wout = np.where(np.abs(P[:, 2]) < world.DOOR_Z + .05, np.clip((P[:, 0] + .45) / .75, 0, 1), (~inside) * 1.)[:, None]
    amb = wout * np.array([.30, .34, .48]) * (.62 + .38 * n[:, 1:2]) + (1 - wout) * np.array([.42, .30, .20]) * (.12 + .55 * light)
    glow_dir = np.array([.80, .22, .55]); glow_dir /= np.linalg.norm(glow_dir)
    glow = wout * np.clip(n @ glow_dir, 0, 1)[:, None] * np.array([.55, .34, .26]) * .55
    Lv = world.LIGHT_POS - P; d = np.linalg.norm(Lv, axis=1); lam = np.clip((n * Lv).sum(1) / d, 0, 1)
    thr, win = world.through_door(P)
    vis = np.where(inside, 1., (thr & ~world.door_blocks(P, door)) * 1. + win * .25)
    if extra is not None:
        sh = extra['shadow']; ao = extra['ao']
        flo = M('floor') | M('ifloor') | M('rug') | M('sill') | M('step')
        vis[flo] *= 1 - np.clip(grid_at(sh, P[flo]), 0, .85)
        amb[flo] *= (1 - np.clip(grid_at(ao, P[flo]), 0, .75))[:, None]
    dl = (vis * lam * light * 6.5 / (d * d + .5))[:, None] * np.array([1.0, .72, .42])
    return base * (amb + glow + dl) + emis




_STATIC = {}

def static_layer(cam, i):
    """the porch, house and room never move: rasterize and surface them once per camera set-up"""
    key = (tuple(np.round(cam.eye, 6)), tuple(np.round(cam.target, 6)), round(cam.f, 4), cam.W)
    if _STATIC.get('key') != key:
        tri, bary, zb = raster.rasterize(*cam.project(SV), SF, cam.W, cam.H)
        m = tri >= 0; t = tri[m]; b = bary[m]
        P = np.einsum('pi,pik->pk', b, SV[SF[t]])
        fn = np.cross(SV[SF[:, 1]] - SV[SF[:, 0]], SV[SF[:, 2]] - SV[SF[:, 0]]); fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
        n = fn[t]; mat = SM[t]
        base, emis = surface(P, n, mat, P, i)
        skyc = sky(cam, np.nonzero(~m)[0])
        _STATIC.clear(); _STATIC.update(key=key, m=m, zb=zb, P=P, n=n, mat=mat, base=base, emis=emis, sky=skyc,
                                        emis_light=(mat == MAT['lamp']) | (mat == MAT['window']))
    return _STATIC


def shade(cam, V, F, Mt, aux, i, extra=None):
    """V/F hold only the moving things (door, person, dog); the static layer comes from the cache"""
    S = static_layer(cam, i)
    tri, bary, zd = raster.rasterize(*cam.project(V), F, cam.W, cam.H)
    dyn = (tri >= 0) & (zd < S['zb'])
    m = S['m'] | dyn
    # per covered pixel: static values, overwritten where a moving surface is nearer
    sidx = np.full(cam.H * cam.W, -1); sidx[S['m']] = np.arange(S['m'].sum())
    pix = np.nonzero(m)[0]; isd = dyn[pix]
    P = np.zeros((len(pix), 3)); n = np.zeros((len(pix), 3)); mat = np.zeros(len(pix), int)
    base = np.zeros((len(pix), 3)); emis = np.zeros((len(pix), 3))
    st = sidx[pix[~isd]]
    P[~isd] = S['P'][st]; n[~isd] = S['n'][st]; mat[~isd] = S['mat'][st]; base[~isd] = S['base'][st]; emis[~isd] = S['emis'][st]
    # emissive lamp and window follow the room light
    if S['emis_light'].any():
        e2 = surface(S['P'][st][S['emis_light'][st]], S['n'][st][S['emis_light'][st]], S['mat'][st][S['emis_light'][st]],
                     S['P'][st][S['emis_light'][st]], i)[1]
        tmp = emis[~isd]; tmp[S['emis_light'][st]] = e2; emis[~isd] = tmp
    t = tri[pix[isd]]; b = bary[pix[isd]]
    Pd = np.einsum('pi,pik->pk', b, V[F[t]]); Ad = np.einsum('pi,pik->pk', b, aux[F[t]])
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]); fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
    P[isd] = Pd; n[isd] = fn[t]; mat[isd] = Mt[t]
    bd, ed = surface(Pd, fn[t], Mt[t], Ad, i); base[isd] = bd; emis[isd] = ed
    c = lighting(P, n, mat, base, emis, i, extra)
    img = np.zeros((cam.H * cam.W, 3))
    img[~m] = S['sky'][np.searchsorted(np.nonzero(~S['m'])[0], np.nonzero(~m)[0])]
    img[m] = c
    # for the measurements: the dog's pixels with their triangle and barycentrics (in the moving set)
    tri_full = np.full(cam.H * cam.W, -1); tri_full[pix[isd]] = t
    out = {'img': img.reshape(cam.H, cam.W, 3), 'tri': tri_full, 'm': dyn, 'P': Pd, 'mat': Mt[t], 't': t, 'b': b}
    return out


def assemble(i, mode='dqs', weights_view=None):
    Pd, Pp, G, S = skin(i, mode)
    Vd, Fd, Md = world.door_geo(PF['door'][i])
    aux_d = Vd.copy()
    # door local coords for its panels: undo the hinge rotation
    c, s = np.cos(PF['door'][i]), np.sin(PF['door'][i])
    Rm = np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]])
    aux_d = (Vd - [world.WALL_IN_X, 0, -world.DOOR_Z + .01]) @ Rm
    parts = [(Vd, Fd, Md, aux_d),
             (Pp, PER['F'], np.full(len(PER['F']), MAT['person']), PER['V']),
             (Pd, DOG['F'], np.full(len(DOG['F']), MAT['dog']), np.c_[DOG['UV'], np.zeros(len(DOG['V']))])]
    V, F, Mt, AX = [], [], [], []; off = 0; ranges = {}
    for k, (v, f, mm, ax) in enumerate(parts):
        V.append(v); F.append(f + off); Mt.append(mm); AX.append(ax); ranges[k] = (off, off + len(v)); off += len(v)
    V = np.concatenate(V); F = np.concatenate(F); Mt = np.concatenate(Mt); AX = np.concatenate(AX)
    # shadows of dog and person in the door light, and contact occlusion, splatted onto a top-down grid
    L = world.LIGHT_POS; Q = np.concatenate([Pd, Pp])
    th, _ = world.through_door(Q); ok = th & (Q[:, 1] < L[1] - .05) & (Q[:, 0] > world.WALL_IN_X - .3)
    tt = L[1] / (L[1] - Q[ok, 1]); proj = L + (Q[ok] - L) * tt[:, None]
    sh = splat(proj, np.full(ok.sum(), 1.), 1.6) * .9
    ao = splat(Q, np.exp(-np.clip(Q[:, 1], 0, None) / .10) * .5, 3.0)
    return V, F, Mt, AX, {'shadow': sh, 'ao': ao}, Pd, G, ranges


FONTS = os.path.join(ROOT, '..', '..', '..', 'tools', 'paeleo', 'fonts')
# the person's spoken words (the synthesized voice is not a recording, so the words are given); never the dog's state
SUBS = [(1.02, 2.25, 'Come here.'), (3.42, 4.60, 'Come here.'), (7.45, 9.30, "It's all right."),
        (10.45, 11.70, "It's all right."), (26.42, 27.70, 'Come in.')]

def subtitle(im, i):
    t = i / 24
    for a, b, txt in SUBS:
        if a <= t < b:
            from PIL import ImageDraw, ImageFont
            f = ImageFont.truetype(os.path.join(FONTS, 'f27.woff2'), 30)
            d = ImageDraw.Draw(im); w_ = d.textlength(txt, font=f)
            al = int(255 * min(1, (t - a) / .2, (b - t) / .25))
            ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            od.text(((W - w_) / 2 + 1, H - 74 + 1), txt, font=f, fill=(0, 0, 0, int(al * .8)))
            od.text(((W - w_) / 2, H - 74), txt, font=f, fill=(244, 232, 205, al))
            im = Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB')
    return im


def grade(img, i):
    rng = np.random.default_rng(1000 + i)
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    vig = 1 - .28 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    img = img * vig[..., None]
    img = np.clip(img, 0, None); img = img / (1 + .35 * img) * 1.18
    img = img ** (1 / 1.15)
    img = img + rng.normal(0, .007, (h, w, 1))
    return np.clip(img, 0, 1)


def cam_for(i, s=SS):
    return raster.Camera(PF['cam_eye'][i], PF['cam_target'][i], PF['cam_f'][i] * s, W * s, H * s)


def render(i, mode='dqs', cam=None, path=None, measure=True):
    V, F, Mt, AX, extra, Pd, G, ranges = assemble(i, mode)
    cam = cam or cam_for(i)
    o = shade(cam, V, F, Mt, AX, i, extra)
    img = raster.downsample(o['img'], SS)
    img = grade(img, i)
    if path:
        subtitle(Image.fromarray((img * 255).astype(np.uint8)), i).save(path, quality=93)
    if measure:
        m = o['m']; t = o['t']; isdog = o['mat'] == MAT['dog']
        idx = np.nonzero(m)[0][isdog]
        py, px = idx // cam.W / SS, idx % cam.W / SS
        Pw = o['P'][isdog]
        # head-ness of each dog pixel, interpolated from the vertex weights of the head/neck bones
        a, b_ = ranges[2]
        hw = np.einsum('pi,pi->p', o['b'][isdog], DOG_HEADW[F[t[isdog]] - a])
        hd = hw > .5; bd = hw < .1
        res = {'i': i, 'dog_px': int(isdog.sum() / SS / SS)}
        if isdog.any():
            res.update({'cx': float(px.mean()), 'cy': float(py.mean()), 'top_px': float(py.min()), 'bot_px': float(py.max()),
                        'x_world': float(Pw[:, 0].mean()), 'top_y_world': float(np.percentile(Pw[:, 1], 99)),
                        'inside_door_share': float((Pw[:, 0] < world.FACADE_X).mean()),
                        'inside_room_share': float((Pw[:, 0] < world.WALL_IN_X).mean())})
            if hd.any() and bd.any():
                res.update({'head_x_world': float(Pw[hd, 0].mean()), 'head_y_world': float(Pw[hd, 1].mean()),
                            'head_z_world': float(Pw[hd, 2].mean()),
                            'body_x_world': float(Pw[bd, 0].mean()), 'back_y_world': float(np.percentile(Pw[bd, 1], 97)),
                            'head_cx': float(px[hd].mean()), 'head_cy': float(py[hd].mean()), 'head_px': int(hd.sum() / SS / SS),
                            'head_top_y_world': float(np.percentile(Pw[hd, 1], 97))})
            # what the camera sees of the head: back of the skull (muzzle pointing away from the camera)?
            mz = Pd[MUZZLE_V]; hj = G[SK.ix['head'], :3, 3]
            v = cam.eye - hj; res['muzzle_away_from_camera'] = float(np.dot((mz - hj) / np.linalg.norm(mz - hj), v / np.linalg.norm(v)))
            res['muzzle_world'] = [float(c) for c in mz]
        json.dump(res, open(os.path.join(MEAS, '%04d.json' % i), 'w'))
    return img


if __name__ == '__main__':
    if sys.argv[1] == 'still':
        i = int(sys.argv[2]); mode = sys.argv[4] if len(sys.argv) > 4 else 'dqs'
        t0 = time.time(); render(i, mode, path=sys.argv[3], measure=False); print('frame', i, round(time.time() - t0, 2), 's')
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        for i in range(a, b):
            render(i, path=os.path.join(FRAMES, '%04d.jpg' % i))
            if i % 48 == 0: print('rendered', i, flush=True)
