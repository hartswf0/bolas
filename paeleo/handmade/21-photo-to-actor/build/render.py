"""Stage + render: the porch at dusk, the door, the person, and the photographic dog actor; one JPEG per scene frame.

Every surface the viewer sees is either an archive photograph (dog, person, door leaf, lit hallway, sky) or a computed
surface (house boards, porch planks, light) developed with the same grain, tone curve and dusk grade as the photographs.
Also measures, from each rendered dog layer, its alpha bbox, centroid and head point -> build/cache/measure.json.
usage: python3 render.py [first last]
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__)); FOLDER = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(FOLDER, '..', '..', '..'))
sys.path.insert(0, HERE)
import spec, actor

W, H = 1280, 720
GROUND = 612
X0, KM = 330, 180.0                       # screen x of the threshold, px per metre
DOOR_L, DOOR_R = X0 - 0.46 * KM, X0 + 0.46 * KM
DOOR_TOP = GROUND - 2.05 * KM
HOUSE_R = X0 + 0.98 * KM
DOG_OFF = 0.3 * KM                      # the score's x is the dog's loins, 0.3 m behind its body centre
CACHE = os.path.join(FOLDER, 'build', 'cache')
OUTF = os.path.join(CACHE, 'frames')
os.makedirs(OUTF, exist_ok=True)
P = actor.P
rng = np.random.default_rng(21)


def sx(xm): return X0 + KM * xm


def grain_tex(w, h, base, amp, seed, blur=1.2, streak=None):
    r = np.random.default_rng(seed)
    n = r.normal(0, 1, (h, w))
    img = Image.fromarray(np.clip(128 + 40 * n, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
    a = (np.array(img).astype(float) - 128) / 40 * amp
    return np.clip(base + a, 0, 255)


def tone(arr):
    """shared photographic tone curve (soft toe and shoulder)"""
    x = arr / 255.0
    return 255 * (x ** 1.08) * (1.0 - 0.12 * x)


DUSK = np.array([0.62, 0.70, 0.92])     # ambient dusk tint (multiplier on grey)
WARM = np.array([1.05, 0.80, 0.52])     # lamp light from the doorway


# ------------------------------------------------------------------------------------------- the plate (static)
def build_plate():
    pl = np.zeros((H, W, 3))
    # sky: a cloud photograph (Top of the Cloud, public domain) graded to dusk, upper band only
    sky = Image.open(os.path.join(FOLDER, 'sources', 'cloud', 'f020.jpg')).convert('L')
    sky = ImageOps.autocontrast(sky).resize((W, int(W * 216 / 384)), Image.LANCZOS)
    s = np.array(sky).astype(float)[:H, :]
    sk = np.zeros((H, W))
    sk[:s.shape[0]] = s
    grad = np.linspace(0, 1, H)[:, None]
    skyv = 18 + 0.22 * sk[:H] * (1 - grad * 0.8) + 34 * grad
    pl[:] = skyv[:, :, None] * np.array([0.55, 0.62, 0.95])[None, None, :]
    pl[:, :, 0] += 22 * grad[:, :]; pl[:, :, 1] += 8 * grad          # low warm band of the last light
    # distant ground beyond the porch (dark field, grain)
    yard_top = GROUND - 150
    yard = grain_tex(W, H - yard_top, 26, 6, 3, blur=2.5)
    pl[yard_top:, :, :] = yard[:, :, None] * np.array([0.7, 0.78, 0.9])
    # a distant tree line: low dark band with an irregular top, computed
    xs = np.arange(W)
    top = yard_top - 30 - 22 * np.abs(np.sin(xs / 37.0)) - 14 * np.abs(np.sin(xs / 11.3 + 1)) - 8 * rng.random(W)
    for x in range(W):
        y0 = int(top[x]); pl[y0:yard_top + 2, x, :] = np.array([14, 16, 24]) + rng.normal(0, 2, (yard_top + 2 - y0, 1))
    # porch railing posts and rail (computed, silhouette), right of the house
    for xm in np.arange(1.3, 4.95, 0.9):
        x = int(sx(xm)) + 40
        pl[GROUND - 150:GROUND, x - 5:x + 5] = grain_tex(10, 150, 30, 5, int(xm * 10))[:, :, None] * np.array([0.8, 0.85, 1.0])
    pl[GROUND - 150:GROUND - 140, int(HOUSE_R):int(sx(4.9))] = grain_tex(int(sx(4.9)) - int(HOUSE_R), 10, 34, 5, 7)[:, :, None] * np.array([0.8, 0.85, 1])
    # house facade: clapboard boards (computed), dusk grey-blue
    fac = grain_tex(int(HOUSE_R), GROUND, 64, 8, 11, blur=1.0)
    for y in range(0, GROUND, 22):
        fac[y:y + 3, :] *= 0.55; fac[y + 3:y + 7, :] *= 1.08
    pl[:GROUND, :int(HOUSE_R)] = fac[:, :, None] * np.array([0.58, 0.64, 0.82])
    pl[:GROUND, int(HOUSE_R) - 8:int(HOUSE_R)] *= 0.6       # corner board
    # eave shadow
    pl[:70, :int(HOUSE_R) + 30] *= 0.45
    # porch floor: planks running along the porch (computed), perspective-free side stage
    fl = grain_tex(W, H - GROUND, 70, 9, 13, blur=0.9)
    for y in range(0, H - GROUND, 13):
        fl[y:y + 2, :] *= 0.5
    for y in range(H - GROUND):
        fl[y] *= 0.85 + 0.25 * (y / (H - GROUND))
    pl[GROUND:, :int(sx(4.9))] = fl[:, :int(sx(4.9)), None] * np.array([0.62, 0.62, 0.72])
    # steps at the porch end (x = 4.9 m)
    for k in range(3):
        y = GROUND + 18 + k * 30; x = int(sx(4.9)) + k * 18
        pl[y:, x:] = (grain_tex(W - x, H - y, 50 - 8 * k, 6, 20 + k)[:, :, None]) * np.array([0.6, 0.62, 0.75])
        pl[y:y + 3, x:] *= 0.5
    # door frame (casing) and sill
    pl[int(DOOR_TOP) - 18:GROUND, int(DOOR_L) - 16:int(DOOR_R) + 16] = grain_tex(int(DOOR_R) - int(DOOR_L) + 32, GROUND - int(DOOR_TOP) + 18, 82, 7, 17)[:, :, None] * np.array([0.6, 0.64, 0.8])
    return np.clip(pl, 0, 255)


PLATE = build_plate()
SILL_Y = GROUND


def interior(light):
    """the lit hallway photograph (Straight Talk f021) seen through the doorway; light 0..1"""
    room = actor.IMG['room'].convert('RGB')
    w, h = int(DOOR_R - DOOR_L), int(GROUND - DOOR_TOP)
    r = np.array(room.resize((w, h), Image.BICUBIC)).astype(float)
    g = r.mean(axis=2, keepdims=True)
    r = 0.6 * r + 0.4 * g
    lamp = 0.18 + 0.95 * light
    r = r * lamp * np.array([1.12, 0.92, 0.66])
    # floor of the hall
    r[-30:] *= 0.7
    return r


def door_leaf(frac_open):
    """the photographed door leaf (f030), foreshortened as it swings in; returns RGBA and its width"""
    leaf = actor.IMG['door_leaf']
    w_full = int(DOOR_R - DOOR_L); h = int(GROUND - DOOR_TOP)
    ang = math.radians(8 + 80 * frac_open)
    w = max(6, int(w_full * math.cos(ang)))
    im = leaf.resize((w, h), Image.BICUBIC)
    a = np.array(im).astype(float)
    a[:, :, :3] = a[:, :, :3].mean(axis=2, keepdims=True) * 0.45 * np.array([0.9, 0.92, 1.0])
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA'), w


# ------------------------------------------------------------------------------------------- the person
PS = {}
for k in ('torso', 'legs', 'arm'):
    im = actor.IMG['person_' + k]
    bb = im.getbbox()
    PS[k] = im.crop(bb)
pa = np.array(PS['torso']).astype(float); pa[:, :, :3] = pa[:, :, :3].mean(axis=2, keepdims=True)
PS['torso'] = Image.fromarray(pa.astype(np.uint8), 'RGBA')
PS['arm'] = ImageOps.mirror(PS['arm'])           # she reaches toward screen right


def silhouette(im, k, rim=0.0):
    a = np.array(im).astype(float)
    g = a[:, :, :3].mean(axis=2, keepdims=True)
    a[:, :, :3] = g * k * DUSK * 0.9 + 6
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')


def draw_person(frame, pr, light):
    x = sx(pr['x']); sit = pr['sit']; reach = pr['reach']; low = pr['low']
    k = 0.2 + 0.04 * (1 - light)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    torso_h = 186.0; leg_h = 128.0
    tor = PS['torso']; s_t = torso_h / tor.height
    legs = PS['legs']; lw, lh = legs.size
    thigh = legs.crop((0, 0, lw, lh // 2 + 6)); shin = legs.crop((0, lh // 2 - 6, lw, lh))
    hip_y = GROUND - leg_h + (leg_h - 30) * sit
    hip = np.array([x, hip_y])
    # legs: straight when standing; seated on the porch boards with the knees up, toward the dog
    ta = math.radians(90 - 115 * sit)                 # thigh: down -> forward and a little up
    sa_ = math.radians(90 + 8 * sit)                  # shin: down to the boards
    knee = hip + leg_h / 2 * np.array([math.cos(ta), math.sin(ta)])
    foot = knee + leg_h / 2 * np.array([math.cos(sa_), math.sin(sa_)])
    if sit > 0.5: foot[1] = min(foot[1], GROUND - 2)
    actor_place(lay, silhouette(shin, k * 0.8), (lw / 2, 0), (lw / 2, shin.height), knee, foot)
    actor_place(lay, silhouette(thigh, k * 0.8), (lw / 2, 0), (lw / 2, thigh.height), hip, knee)
    # torso, leaning toward the dog when seated and further when the hand is offered low
    tl = math.radians(-90 + 10 * sit + 24 * low)
    tw, th = tor.size
    top = hip + torso_h * np.array([math.cos(tl), math.sin(tl)])
    actor_place(lay, silhouette(tor, k), (tw * 0.47, th * 0.97), (tw * 0.47, 0), hip + [0, 8], top)
    # arm from the near shoulder: hangs, reaches out (the call), or is offered low (seated)
    sh = hip + (torso_h * 0.74) * np.array([math.cos(tl), math.sin(tl)]) + np.array([tw * s_t * 0.30, 0])
    aa = 95 - 85 * reach
    if low > 0: aa = aa + (74 - aa) * low
    ar = PS['arm']; aw, ah = ar.size
    arm_len = 100.0
    a_r = math.radians(aa)
    actor_place(lay, silhouette(ar, k * 1.2), (aw * 0.14, ah * 0.05), (aw * 0.88, ah * 0.93), sh, sh + arm_len * np.array([math.cos(a_r), math.sin(a_r)]))
    frame.alpha_composite(lay)
    return {'x': x, 'hand': (sh + arm_len * np.array([math.cos(a_r), math.sin(a_r)])).tolist()}


def actor_place(canvas, img, sa, sb, da, db):
    sa, sb, da, db = (np.asarray(v, float) for v in (sa, sb, da, db))
    u = sb - sa; Ls = np.hypot(*u); u /= Ls; v = np.array([-u[1], u[0]])
    U = db - da; Ld = np.hypot(*U); U /= Ld; V = np.array([-U[1], U[0]])
    s = Ld / Ls
    A = s * np.outer(U, u) + s * np.outer(V, v); t = da - A @ sa
    Ai = np.linalg.inv(A); c = -Ai @ t
    out = img.transform(canvas.size, Image.AFFINE, (Ai[0, 0], Ai[0, 1], c[0], Ai[1, 0], Ai[1, 1], c[1]), resample=Image.BILINEAR)
    canvas.alpha_composite(out)


# ------------------------------------------------------------------------------------------- one frame
def door_state(t):
    """0 = ajar (half open, lamp low) .. 1 = open and lit; the score opens it at 6.2 s"""
    return float(np.clip((t - 6.2) / 0.8, 0, 1)) ** 0.8


def render(rec, scene_t):
    t = scene_t
    op = door_state(t)
    light = 0.12 + 0.88 * op
    fr = PLATE.copy()
    # interior + door leaf
    it = interior(light)
    x0, y0 = int(DOOR_L), int(DOOR_TOP)
    fr[y0:y0 + it.shape[0], x0:x0 + it.shape[1]] = it
    # light spill on the porch floor and the facade around the door
    yy, xx = np.mgrid[GROUND:H, 0:W]
    spill = np.exp(-((xx - X0) / (150 + 260 * op)) ** 2) * np.exp(-((yy - GROUND) / 140.0)) * light
    fr[GROUND:H] += spill[:, :, None] * 95 * (WARM - 0.25)
    yy2, xx2 = np.mgrid[0:GROUND, 0:int(HOUSE_R)]
    glow = np.exp(-(((xx2 - X0) / 260.0) ** 2 + ((yy2 - (GROUND - 180)) / 260.0) ** 2)) * light * 0.35
    fr[0:GROUND, 0:int(HOUSE_R)] *= (1 + glow[:, :, None] * (WARM - 0.2))
    img = Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8)).convert('RGBA')
    leaf, lw = door_leaf(0.42 + 0.58 * op)
    img.alpha_composite(leaf, (x0, y0))
    # person
    pinfo = draw_person(img, rec['person'], light)
    # dog
    cv, info = actor.draw(rec['pose'])
    if rec['facing'] < 0:
        cv = ImageOps.mirror(cv)
        cc = np.array([actor.CW - actor.CC[0], actor.CC[1]])
    else:
        cc = actor.CC
    xd = sx(rec['x']) - DOG_OFF
    ox, oy = int(round(xd - cc[0])), int(round(GROUND + 2 - actor.GROUND_C))
    # grade the dog: develop grey, dusk ambient + lamp light by distance to the door
    cv.putalpha(cv.split()[3].filter(ImageFilter.MinFilter(3)))   # trim the 1 px bright fringe the SAM masks carry
    a = np.array(cv).astype(float)
    g = a[:, :, :3].mean(axis=2, keepdims=True)
    g = tone(g * 0.9)
    lamp = light * math.exp(-max(0.0, rec['x'] - 0.3) / 1.6)
    col = g * (DUSK * (0.86 - 0.1 * light) + WARM * 0.55 * lamp)
    # warm rim where the lamp light from the doorway catches the fur edge (contre-jour near the door)
    if lamp > 0.02:
        al0 = cv.split()[3]
        edge = (np.array(al0).astype(float) - np.array(al0.filter(ImageFilter.MinFilter(5))).astype(float)) / 255
        col = col + edge[:, :, None] * lamp * 55 * WARM
    a[:, :, :3] = col
    cvg = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    # contact shadow under the dog (computed from its own alpha, squashed to the floor)
    al = cv.split()[3]
    sh = al.resize((al.width, max(1, al.height // 7))).filter(ImageFilter.GaussianBlur(5))
    shadow = Image.new('RGBA', sh.size, (8, 8, 14, 0)); shadow.putalpha(sh.point(lambda q: int(q * 0.55)))
    img.alpha_composite(shadow, (ox, oy + int(actor.GROUND_C) - sh.height // 2 - 2))
    img.alpha_composite(cvg, (ox, oy))
    # measure the dog from its own rendered layer
    aa = np.array(al).astype(float) / 255
    ys, xs = np.nonzero(aa > 0.5)
    meas = {}
    if len(xs):
        meas = {'bbox': [int(xs.min() + ox), int(ys.min() + oy), int(xs.max() + ox), int(ys.max() + oy)],
                'centroid': [float((xs * 1).mean() + ox), float(ys.mean() + oy)], 'area': int(len(xs))}
    hc = np.array(info.get('head_c', actor.CC))
    if rec['facing'] < 0: hc = np.array([actor.CW - hc[0], hc[1]])
    meas['head'] = [float(hc[0] + ox), float(hc[1] + oy)]
    meas['_alpha'] = (np.array(al.resize((actor.CW // 2, actor.CH // 2), Image.BILINEAR)) > 127, ox, oy)
    meas['body_centre_screen'] = [float(xd), float(GROUND)]
    # final film grade: tone, vignette, grain, faint flicker (one grain for every material)
    out = np.array(img.convert('RGB')).astype(float)
    out = tone(np.clip(out * 1.32, 0, 255))
    vy, vx = np.mgrid[0:H, 0:W]
    vig = 1 - 0.32 * (((vx - W / 2) / (W / 2)) ** 2 + ((vy - H / 2) / (H / 1.6)) ** 2)
    out *= vig[:, :, None]
    n = rng.normal(0, 1, (H // 2, W // 2))
    n = np.array(Image.fromarray(np.clip(128 + 40 * n, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(float) - 128
    out += n[:, :, None] * 0.085
    out *= 1 + 0.012 * math.sin(t * 23.0) + 0.008 * rng.normal()
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)), meas, pinfo


if __name__ == '__main__':
    perf = json.load(open(os.path.join(CACHE, 'performance.json')))
    a0, a1 = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, len(perf) - 1)
    M = {}; ALPHA = {}
    for rec in perf[a0:a1 + 1]:
        im, meas, pinfo = render(rec, rec['t'])
        im.save(os.path.join(OUTF, '%04d.jpg' % rec['i']), quality=90)
        al, aox, aoy = meas.pop('_alpha')
        ALPHA[rec['i']] = al; meas['alpha_origin'] = [aox, aoy]
        M[rec['i']] = {'dog': meas, 'person': pinfo}
    json.dump(M, open(os.path.join(CACHE, 'measure_%04d_%04d.json' % (a0, a1)), 'w'))
    np.savez_compressed(os.path.join(CACHE, 'alpha_%04d_%04d.npz' % (a0, a1)), **{'f%04d' % k: v for k, v in ALPHA.items()})
    print('rendered', a0, a1)
