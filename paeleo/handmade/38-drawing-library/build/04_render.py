"""Render the film picture: title card, the 32 s scene on the score's frames, end card.

Everything drawn is a real Quick, Draw! doodle placed by uniform scale + translation (+ a
mirror for some dog candidates), except: the person's body lines and the voice marks (drawn
by this swarm as a few strokes), the light, the sky and the floor fill.
The dog is never transformed except by the placement rule in 03_decode.placed(); the
drawing changes only by substitution, on twos, as the decoder chose.

Writes frames to ffmpeg (work/picture.mp4), stills/, work/trace_raw.json
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import qd
from importlib import util
spec = util.spec_from_file_location('dec', os.path.join(os.path.dirname(__file__), '03_decode.py'))
dec = util.module_from_spec(spec); spec.loader.exec_module(dec)

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = '/home/user/bolas/tools/paeleo/fonts'
SCORE = json.load(open(f'{HERE}/../score/threshold-score.json'))
SCHED = json.load(open(f'{HERE}/work/schedule.json'))
CANDS = json.load(open(f'{HERE}/work/candidates.json'))
SETD = [json.loads(l) for l in open(f'{HERE}/library/set.ndjson')]
SETROLE = json.load(open(f'{HERE}/library/pose_library.json'))['set']
SETBY = {r['role'].split(':')[0]: d for r, d in zip(SETROLE, SETD)}

Wd, Ht, SS = 1280, 720, 2
S = 150.0           # px per metre
X0 = 415.0          # screen x of the threshold (x = 0)
FLOOR = 585.0
def sx(x): return X0 + x * S

CREAM = np.array([239, 230, 210], float)
DOGC = np.array([250, 244, 230], float)
DARK = np.array([38, 28, 48], float)
WARM = np.array([246, 200, 112], float)
FPS = 24
ONLY = os.environ.get('ONLY')  # comma list of scene frames for quick looks


def by_role(prefix):
    for r, d in zip(SETROLE, SETD):
        if r['role'].startswith(prefix):
            return d
    raise KeyError(prefix)


def fit(d, box, uniform=True, anchor='bottom'):
    """Place a doodle's strokes in the box (x0,y0,x1,y1) world px."""
    Sx = qd.strokes_np(d)
    a, b, c, e = qd.bbox(Sx)
    w, h = max(c - a, 1), max(e - b, 1)
    bx0, by0, bx1, by1 = box
    if uniform:
        sc = min((bx1 - bx0) / w, (by1 - by0) / h)
        sxx = syy = sc
        ox = (bx0 + bx1) / 2 - (a + c) / 2 * sc
        oy = by1 - e * sc if anchor == 'bottom' else (by0 + by1) / 2 - (b + e) / 2 * sc
    else:
        sxx, syy = (bx1 - bx0) / w, (by1 - by0) / h
        ox, oy = bx0 - a * sxx, by0 - b * syy
    return [np.stack([s[:, 0] * sxx + ox, s[:, 1] * syy + oy], 1) for s in Sx]


def place_scale(d, sc, ox, oy):
    return [np.stack([s[:, 0] * sc + ox, s[:, 1] * sc + oy], 1) for s in qd.strokes_np(d)]


# ---------------------------------------------------------------- the set (world px)
house_d = by_role('house')
# house 'house' #3: right-wall foot at (255,245); scale so the walls stand ~320 px
HS = 2.8
HOUSE = place_scale(house_d, HS, sx(0.50) + 52 - 255 * HS, FLOOR - 245 * HS + 4)
HOUSE_POLY = HOUSE[1]  # the maker's own wall stroke, used as the lit interior's outline
DOOR_BOX = (sx(-0.46), FLOOR - 290, sx(0.46), FLOOR)
DOOR_AJAR = fit(by_role('door ajar'), DOOR_BOX, uniform=False)
DOOR_SWING = fit(by_role('door swinging'), DOOR_BOX, uniform=False)
DOOR_FRAME = fit(by_role('door frame'), DOOR_BOX, uniform=False)
DOOR_PANEL = fit(by_role('door panel'), (sx(-0.46) - 30, FLOOR - 300, sx(-0.46) + 34, FLOOR + 4), uniform=False)
MOON = fit(by_role('crescent'), (1010, 60, 1100, 150))
STAIRS = fit(by_role('porch steps'), (sx(4.9) - 4, FLOOR - 6, 1282, FLOOR + 120), uniform=False)
RAIL = fit(by_role('porch rail'), (sx(0.40), FLOOR - 10, sx(4.95), FLOOR + 22), uniform=False)
FACE = by_role("the person's face")
HAND_REACH = by_role('arm and hand')
HAND_LOW = by_role('flat hand')


def wob(points, seed, amp=1.6):
    """The swarm's own strokes get a fixed (not boiling) hand wobble."""
    P = qd.densify([np.array(points, float)], 6.0)[0]
    rng = np.random.default_rng(seed)
    n = len(P)
    k = np.linspace(0, 1, n)
    off = np.zeros_like(P)
    for f in (1, 2, 3):
        off[:, 0] += rng.normal(0, amp / f) * np.sin(math.pi * f * k + rng.uniform(0, 6))
        off[:, 1] += rng.normal(0, amp / f) * np.sin(math.pi * f * k + rng.uniform(0, 6))
    return P + off


def person_strokes(f, t):
    """The person: a real face doodle; the body is the swarm's few strokes; hands are doodles."""
    p = f['person']
    px = sx(p['x'])
    sit = p['sit']
    out = []
    m = S
    if sit < 0.3:  # standing
        head_c = (px, FLOOR - 1.55 * m)
        body = [[(px, FLOOR - 1.38 * m), (px + 2, FLOOR - 0.85 * m)],
                [(px + 2, FLOOR - 0.85 * m), (px - 0.16 * m, FLOOR)],
                [(px + 2, FLOOR - 0.85 * m), (px + 0.17 * m, FLOOR)],
                [(px, FLOOR - 1.30 * m), (px - 0.22 * m, FLOOR - 0.92 * m)]]
        if p['reach'] < 0.3:
            body.append([(px, FLOOR - 1.30 * m), (px + 0.22 * m, FLOOR - 0.92 * m)])
        posture = 'stand'
    elif sit < 0.75:  # going down
        head_c = (px, FLOOR - 1.2 * m)
        body = [[(px, FLOOR - 1.03 * m), (px - 0.05 * m, FLOOR - 0.55 * m)],
                [(px - 0.05 * m, FLOOR - 0.55 * m), (px + 0.3 * m, FLOOR - 0.45 * m), (px + 0.3 * m, FLOOR)],
                [(px - 0.05 * m, FLOOR - 0.55 * m), (px - 0.1 * m, FLOOR)],
                [(px, FLOOR - 0.95 * m), (px + 0.25 * m, FLOOR - 0.6 * m)]]
        posture = 'crouch'
    else:  # sitting on the floor beside the door
        head_c = (px, FLOOR - 0.98 * m)
        body = [[(px, FLOOR - 0.81 * m), (px - 0.03 * m, FLOOR - 0.28 * m)],
                [(px - 0.03 * m, FLOOR - 0.28 * m), (px + 0.36 * m, FLOOR - 0.46 * m), (px + 0.5 * m, FLOOR)],
                [(px - 0.03 * m, FLOOR - 0.24 * m), (px + 0.30 * m, FLOOR - 0.36 * m), (px + 0.42 * m, FLOOR)],
                [(px - 0.03 * m, FLOOR - 0.04 * m), (px + 0.40 * m, FLOOR - 0.02 * m)]]
        if p['low'] < 0.3:
            body.append([(px, FLOOR - 0.72 * m), (px + 0.3 * m, FLOOR - 0.47 * m)])
        posture = 'sit'
    for k, b in enumerate(body):
        out.append(wob(b, 100 + k + 10 * ['stand', 'crouch', 'sit'].index(posture)))
    fr = 0.17 * m
    out += fit(FACE, (head_c[0] - fr, head_c[1] - fr, head_c[0] + fr, head_c[1] + fr), anchor='centre')
    if p['reach'] >= 0.3 and posture == 'stand':
        # the reaching arm is the hand doodle (an arm and a hand), its root at the shoulder
        r = min(1.0, p['reach'])
        w = (0.35 + 0.45 * r) * m
        hs = fit(HAND_REACH, (0, 0, w, w))
        P = np.concatenate(hs); a = P.min(0); bb = P.max(0)
        # stroke starts at bottom-left of the doodle: put that at the shoulder
        out += [s - np.array([a[0], bb[1]]) + np.array([px + 4, FLOOR - 1.26 * m + 0.12 * w]) for s in hs]
    if posture == 'sit' and p['low'] >= 0.3:
        hx = px + (0.6 + 0.5 * min(1, p['low'])) * m  # into the doorway, at the floor
        hw = 0.30 * m
        hl = fit(HAND_LOW, (hx - hw / 2, FLOOR - hw * 0.6, hx + hw / 2, FLOOR - 2))
        out += hl
        out.append(wob([(px, FLOOR - 0.72 * m), (hx - hw * 0.45, FLOOR - 0.08 * m)], 150))
    mouth = (head_c[0] + fr * 0.95, head_c[1] + fr * 0.25)
    return out, posture, mouth


def voice_marks(f, mouth, t):
    v = f['person']['voice']
    if v == 'none':
        return []
    out = []
    if v == 'call':
        radii, span = (20, 38, 56, 74), 0.55
    else:
        radii, span = (12, 22), 0.4
    ph = (int(t * 12) % 2) * 3  # marks pulse on twos
    for k, r in enumerate(radii):
        r = r + ph
        ang = np.linspace(-span, span, 9)
        pts = [(mouth[0] + 6 + r * math.cos(a), mouth[1] + r * math.sin(a)) for a in ang]
        out.append(wob(pts, 300 + k, amp=0.6))
    return out


# ---------------------------------------------------------------- dog placement
PLACED = {}
def dog_strokes(ci, x):
    if ci not in PLACED:
        PLACED[ci] = dec.placed(CANDS[ci], S)
    return [s + np.array([sx(x), FLOOR + 1]) for s in PLACED[ci]]


# ---------------------------------------------------------------- camera
def smooth(u):
    u = min(1, max(0, u)); return u * u * (3 - 2 * u)

def camera(t):
    u = smooth((t - 19.0) / 6.0)
    x0 = 0 + u * 150; y0 = 0 + u * 160; w = 1280 + u * (980 - 1280)
    return x0, y0, Wd / w


def to_screen(P, cam):
    x0, y0, z = cam
    return (P - np.array([x0, y0])) * z


# ---------------------------------------------------------------- drawing helpers
def draw_strokes(dr, strokes, cam, width=3, reveal=1.0):
    total = sum(max(len(s) - 1, 1) for s in strokes)
    budget = reveal * total
    for s in strokes:
        n = max(len(s) - 1, 1)
        if budget <= 0:
            break
        P = to_screen(s, cam) * SS
        if budget < n and len(s) > 1:
            k = int(budget)
            frac = budget - k
            pts = list(P[:k + 1])
            if k + 1 < len(P):
                pts.append(P[k] + (P[k + 1] - P[k]) * frac)
            P = np.array(pts)
        budget -= n
        pts = [tuple(p) for p in P]
        if len(pts) == 1:
            pts = pts * 2
        dr.line(pts, fill=255, width=int(width * SS), joint='curve')
        r = width * SS / 2
        for q in (pts[0], pts[-1]):
            dr.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=255)


def layer():
    im = Image.new('L', (Wd * SS, Ht * SS), 0)
    return im, ImageDraw.Draw(im)


def down(im):
    return np.asarray(im.resize((Wd, Ht), Image.BOX), float) / 255


rng0 = np.random.default_rng(7)
GRAIN = rng0.normal(0, 1, (Ht, Wd)) * 3.0  # fixed paper grain, never boils
YY = np.arange(Ht)[:, None].astype(float)
XX = np.arange(Wd)[None, :].astype(float)


def background(t, cam):
    x0, y0, z = cam
    wy = YY / z + y0            # world y of each screen row
    wx = XX / z + x0
    dusk = 1 - 0.18 * t / 32
    top = np.array([30, 32, 68]) * dusk
    hor = np.array([78, 60, 98]) * (0.9 + 0.1 * dusk)
    u = np.clip(wy / FLOOR, 0, 1)[..., None]
    sky = top * (1 - u ** 1.6) + hor * (u ** 1.6)
    porch = np.array([34, 28, 46]) * np.ones((1, 1, 1))
    img = np.where((wy > FLOOR)[..., None], porch, sky) * np.ones((Ht, Wd, 1))
    img += GRAIN[..., None]
    return img, wx, wy


def poly_mask(P, cam):
    im = Image.new('L', (Wd, Ht), 0)
    ImageDraw.Draw(im).polygon([tuple(q) for q in to_screen(P, cam)], fill=255)
    return np.asarray(im) > 0


GAP = DOOR_AJAR[1]
GAP_POLY = np.concatenate([GAP, (GAP + np.array([-9.0, 0]))[::-1]])


def light_fields(t, f, wx, wy, cam):
    """inside: where the lit interior/doorway is (lines go dark there); glow: warm air."""
    door = f['door']
    open_u = smooth((t - 6.2) / 0.5) if door == 'open' else 0.0
    in_house = poly_mask(HOUSE_POLY, cam) & (wy < FLOOR + 2) & (wx < DOOR_BOX[2])  # wall thickness past the jamb stays dark
    in_door = (wx > DOOR_BOX[0]) & (wx < DOOR_BOX[2]) & (wy > DOOR_BOX[1]) & (wy < FLOOR)
    inside = np.zeros_like(wx + wy)
    fill = np.zeros_like(inside)
    # ajar: a strip of light in the gap (along the door doodle's own inner line)
    gap = poly_mask(GAP_POLY, cam)
    fill = np.where(gap, 0.75 * (1 - open_u), fill)
    fill = np.where(in_house, np.maximum(fill, 0.42 * open_u), fill)
    fill = np.where(in_door, np.maximum(fill, 0.92 * open_u), fill)
    inside = np.where(in_house | in_door, open_u, 0.0)
    d = np.hypot((wx - sx(0.3)) / 1.0, (wy - (FLOOR - 120)) / 0.8)
    glow = open_u * 0.30 * np.exp(-(d / 420) ** 2) * (wy < FLOOR + 40)
    return fill, inside, glow




FONT_T = ImageFont.truetype(f'{FONTS}/f8.woff2', 64)
FONT_S = ImageFont.truetype(f'{FONTS}/f34.woff2', 28)
FONT_M = ImageFont.truetype(f'{FONTS}/f14.woff2', 19)
FONT_MS = ImageFont.truetype(f'{FONTS}/f14.woff2', 14)


def scene_frame(i, trace):
    f = SCORE['frames'][i]
    t = f['t']
    sch = SCHED['frames'][i]
    cam = camera(t)
    bg, wx, wy = background(t, cam)
    fill, inside, glow = light_fields(t, f, wx, wy, cam)
    # set lines (draw on in the first 0.7 s, each doodle in its maker's stroke order)
    Ls, ds = layer()
    rev = smooth(t / 0.7) if t < 0.7 else 1.0
    door = f['door']
    if door == 'open':
        dd = DOOR_SWING + DOOR_PANEL if t < 6.2 + 0.17 else DOOR_FRAME + DOOR_PANEL
    else:
        dd = DOOR_AJAR
    set_list = [HOUSE, dd, RAIL, STAIRS, MOON]
    allset = [s for g in set_list for s in g]
    draw_strokes(ds, allset, cam, 3, rev)
    # person, positioned on twos
    f2 = SCORE['frames'][i - i % 2]
    pst, pposture, mouth = person_strokes(f2, t)
    Lp, dp = layer()
    draw_strokes(dp, pst, cam, 3, rev)
    vm = voice_marks(f2, mouth, t)
    Lv, dv = layer()
    draw_strokes(dv, vm, cam, 3.0 if f2['person']['voice'] == 'call' else 2.2)
    # dog: the decoder's drawing, at the score's x sampled on twos
    xd = f2['dog']['x']
    dst = dog_strokes(sch['cand'], xd)
    Ld, dd_ = layer()
    draw_strokes(dd_, dst, cam, 3.2)
    A_set, A_p, A_v, A_d = down(Ls), down(Lp), down(Lv), down(Ld)
    # composite
    img = bg
    img = img * (1 - fill[..., None]) + WARM * fill[..., None]
    img = img + glow[..., None] * (WARM - img) * 0.9
    ins = inside[..., None]
    lc_set = CREAM * 0.86 * (1 - ins) + DARK * ins
    lc_dog = DOGC * (1 - ins) + DARK * ins
    vcol = (CREAM if f2['person']['voice'] == 'call' else WARM) * (1 - ins) + DARK * ins
    for A, col, alpha in ((A_set, lc_set, 0.85), (A_p, lc_set, 0.95), (A_v, vcol, 0.9 if f2['person']['voice'] == 'call' else 0.6), (A_d, lc_dog, 1.0)):
        a = (A * alpha)[..., None]
        img = img * (1 - a) + col * a
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    # typed prompt, the PAELEO way: the operator's words, small, bottom left
    if f['prompt']:
        dr = ImageDraw.Draw(im)
        dr.text((40, Ht - 50), '> ' + f['prompt'], font=FONT_M, fill=(214, 204, 186))
    # measure the dog from its own layer, in screen pixels and back in metres
    ys, xs = np.nonzero(A_d > 0.25)
    x0c, y0c, z = cam
    if len(xs):
        cxp, cyp = float(xs.mean()), float(ys.mean())
        bx0, bx1 = xs.min() / z + x0c, xs.max() / z + x0c
        inside_frac = float((A_d * inside).sum() / max(A_d.sum(), 1e-6))
        left_m, right_m = (bx0 - X0) / S, (bx1 - X0) / S
    else:
        cxp = cyp = left_m = right_m = float('nan'); inside_frac = 0.0
    c = CANDS[sch['cand']]
    # x of the dog's centre of ink, back to metres in world space
    trace.append(dict(i=i, t=round(t, 4), state=f['dog']['state'], x_score=f['dog']['x'],
                      x_screen=round(cxp, 2), y_screen=round(cyp, 2),
                      x_ink_m=round((cxp / z + x0c - X0) / S, 4) if len(xs) else None,
                      facing={1: 'toward_door', -1: 'away', 0: 'front'}[c['face']], posture=c['posture'],
                      key_id=c['key_id'], flip=c['flip'], bbox_left_m=round(left_m, 4), bbox_right_m=round(right_m, 4),
                      ink_in_lit_doorway=round(inside_frac, 4), person=pposture,
                      voice=f2['person']['voice'], door=door, camera=[round(v, 3) for v in cam]))
    return im


def wrap(text, font, width, dr):
    words = text.split(); lines = []; cur = ''
    for w in words:
        tst = (cur + ' ' + w).strip()
        if dr.textlength(tst, font=font) > width and cur:
            lines.append(cur); cur = w
        else:
            cur = tst
    lines.append(cur)
    return lines


def card_bg():
    img = np.zeros((Ht, Wd, 3)) + np.array([24, 24, 50]) + GRAIN[..., None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def title_card(k):
    im = card_bg(); dr = ImageDraw.Draw(im)
    a = min(1, k / 12) * min(1, (72 - k) / 10)
    col = tuple(int(c * a + 24 * (1 - a)) for c in (239, 230, 210))
    dr.text((90, 250), 'PAE-02 · SCION 38 · Dynamic Pose Selection', font=FONT_T, fill=col)
    dr.text((92, 345), 'the drawing-library swarm: a dog at a threshold, made by choosing', font=FONT_S,
            fill=tuple(int(c * a + 24 * (1 - a)) for c in (200, 190, 175)))
    dr.text((92, 382), 'among real people’s dog doodles',
            font=FONT_S, fill=tuple(int(c * a + 24 * (1 - a)) for c in (200, 190, 175)))
    dr.text((92, 440), 'nothing is bent; everything is selected', font=FONT_M,
            fill=tuple(int(c * a + 24 * (1 - a)) for c in (246, 200, 112)))
    return im


def end_card(k, used):
    im = card_bg(); dr = ImageDraw.Draw(im)
    a = min(1, k / 10)
    def C(c): return tuple(int(v * a + 24 * (1 - a)) for v in c)
    dr.text((70, 50), 'Made of', font=FONT_T, fill=C((239, 230, 210)))
    txt = (f'{len(used)} dog drawings by {len(used)} different people, chosen frame by frame by a dynamic-programming decoder '
           f'from a library of 45 (picked by eye from 4,164 Quick, Draw! dog doodles), swapped whole on twos, never bent. '
           'House, door, moon, steps, rail, face and hands: Quick, Draw! doodles too. Body lines of the person, the voice marks '
           'and the light: drawn by the swarm. Sound synthesized. Quick, Draw! data © Google Creative Lab and contributors, CC BY 4.0.')
    y = 140
    for line in wrap(txt, FONT_M, 1140, dr):
        dr.text((72, y), line, font=FONT_M, fill=C((214, 204, 186))); y += 27
    # the drawings themselves, as used
    dogs = {json.loads(l)['key_id']: json.loads(l) for l in open(f'{HERE}/library/dogs.ndjson')}
    cw, ch = 140, 100
    for n, key in enumerate(used):
        cx, cy = 72 + (n % 8) * cw, y + 20 + (n // 8) * (ch + 12)
        Sx = qd.strokes_np(dogs[key]); x0, y0, x1, y1 = qd.bbox(Sx)
        sc = min((cw - 24) / max(x1 - x0, 1), (ch - 30) / max(y1 - y0, 1))
        for s in Sx:
            pts = [(cx + (p[0] - x0) * sc, cy + (p[1] - y0) * sc) for p in s]
            dr.line(pts if len(pts) > 1 else pts * 2, fill=C((239, 230, 210)), width=2)
        dr.text((cx, cy + ch - 22), key, font=FONT_MS, fill=C((150, 150, 190)))
    return im


def main():
    os.makedirs(f'{HERE}/stills', exist_ok=True)
    trace = []
    if ONLY:
        for i in [int(v) for v in ONLY.split(',')]:
            scene_frame(i, trace).save(f'{HERE}/work/look-{i:03d}.png')
        return
    used = []
    for s in SCHED['frames']:
        if s['key_id'] not in used:
            used.append(s['key_id'])
    out = f'{HERE}/work/picture.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{Wd}x{Ht}',
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17',
                          '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for k in range(72):
        p.stdin.write(title_card(k).tobytes())
    stills = {86: '03.6s-refusal', 216: '09.0s-watching', 456: '19.0s-approach', 672: '28.0s-lying-across-the-sill'}
    for i in range(len(SCORE['frames'])):
        im = scene_frame(i, trace)
        if i in stills:
            im.save(f'{HERE}/stills/{stills[i]}.png')
        p.stdin.write(im.tobytes())
        if i % 96 == 0:
            print('frame', i, flush=True)
    for k in range(72):
        p.stdin.write(end_card(k, used).tobytes())
    p.stdin.close(); p.wait()
    json.dump(trace, open(f'{HERE}/work/trace_raw.json', 'w'))


if __name__ == '__main__':
    main()
