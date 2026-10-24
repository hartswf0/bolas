"""Comedy director + mechanics builder: stage the score with engraved cards on pivots and hard substitutions.
Pipes 912 frames (3 s title, 32 s scene, 3 s end card) to ffmpeg, writes trace.json and events.json.
usage: python3 render.py [out.mp4] [--frames a:b] [--stills]"""
import sys, json, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from common import *

score = load_score()
SF = score['frames']
N = len(SF)
cards = json.load(open(os.path.join(CACHE, 'cards.json')))
C = {n: Image.open(os.path.join(CACHE, n + '.png')).convert('RGBA') for n in cards}
PV = {n: cards[n]['pivots'] for n in cards}
def FONT(n, s):
    f = ImageFont.truetype(os.path.join(HERE, 'fonts', n + '.ttf'), s)
    if n.startswith('BigShoulders'):
        f.set_variation_by_axes([int(n.split('-')[1])])
    return f


def darker(im, k):
    a = np.asarray(im, np.float32).copy()
    a[..., :3] *= k
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


C['dog_fore_far'] = darker(C['dog_fore'], 0.72)
C['dog_fore_far_back'] = darker(C['dog_fore_back'], 0.86)
C['dog_hind_f'] = darker(C['dog_hind_f'], 0.78)
C['dog_hind_f_back'] = darker(C['dog_hind_f_back'], 0.88)
PV['dog_fore_far'] = PV['dog_fore']

# ------------------------------------------------------------------ events (the score's choices, on exact frames)
def first(pred, start=0):
    for f in SF[start:]:
        if pred(f):
            return f['i']
    return None

st = [f['dog']['state'] for f in SF]
EV = {}
EV['retreat'] = first(lambda f: f['dog']['state'] == 'retreat')
EV['watch1'] = first(lambda f: f['dog']['state'] == 'watch', EV['retreat'])
EV['refuse'] = first(lambda f: f['dog']['state'] == 'refuse')
EV['watch2'] = first(lambda f: f['dog']['state'] == 'watch', EV['refuse'])
EV['approach'] = first(lambda f: f['dog']['state'] == 'approach')
EV['lie'] = first(lambda f: f['dog']['state'] == 'lie_down')
EV['comein'] = first(lambda f: f['person']['voice'] == 'soft', EV['lie'])
EV['door_open'] = first(lambda f: f['door'] == 'open')
EV['sit'] = first(lambda f: f['person']['sit'] > 0)
EV['hand_low'] = first(lambda f: f['person']['hand'] == 'low')
voice_on = [(f['i'], f['person']['voice']) for k, f in enumerate(SF) if k == 0 or SF[k - 1]['person']['voice'] != f['person']['voice']]
EVENT_FRAMES = sorted(set(v for v in EV.values() if v is not None) | {i for i, _ in voice_on})
FLIP_N = 6


def held(i):
    """cut-out animation on twos; every event frame lands exactly."""
    j = i - (i % 2)
    for e in EVENT_FRAMES:
        if j < e <= i:
            j = e
    return j


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def facing(i):
    """the card turning over: +1 engraved front (facing the door), -1 the blank back (back turned)."""
    a, b = EV['refuse'], EV['watch2']
    if i < a:
        return 1.0
    if i < a + FLIP_N:
        return FLIP[i - a]
    if i < b:
        return -1.0
    if i < b + FLIP_N:
        return -FLIP[i - b]
    return 1.0


# the turn: narrowing, then the bare card edge held for two frames, then the other side
FLIP = [0.88, 0.45, 0.0, 0.0, -0.45, -0.88]


# walking phase from distance actually travelled (feet move with distance)
xs = np.array([f['dog']['x'] for f in SF])
dist = np.concatenate([[0], np.cumsum(np.abs(np.diff(xs)))])
STRIDE = 0.55


# ------------------------------------------------------------------ static stage
def hatched(w, h, color, tone=0.5, angle=30, spacing=4.0, seed=0, grad=None):
    rng = np.random.default_rng(seed)
    base = np.full((h, w), tone, np.float32)
    if grad is not None:
        base = base + np.linspace(grad[0], grad[1], h, dtype=np.float32)[:, None]
    base = base + (box_blur(rng.random((h, w)).astype(np.float32), 6) - 0.5) * 0.5
    g = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).convert('RGB')
    e, pad = engrave(g, Image.new('L', (w, h), 255), 1.0, wash=color, wash_mix=0.0, outline=0, margin=0,
                     spacing=spacing, angle=angle, cross=0.62, contrast=(0, 1))
    return e.crop((int(pad), int(pad), int(pad) + w, int(pad) + h))


OPEN_L, OPEN_R = int(round(sx(-0.46))), int(round(sx(0.46)))
DOOR_H = C['door'].size[1] - 2 * int(PV['door']['hinge_top'][1])
OPEN_T = FLOOR - DOOR_H
WALL_R = int(sx(1.05))
PAW = 622                     # the line the dog's paws stand on (on the boards, in front of the wall)
STEP_X = int(sx(4.9))


def build_stage():
    bgs = []
    yy = np.linspace(0, 1, 470, dtype=np.float32)[:, None]
    top, mid, hor = np.array([46, 36, 86.]) / 255, np.array([132, 76, 122.]) / 255, np.array([238, 150, 98.]) / 255
    grad = np.where(yy[..., None] < 0.6, top + (mid - top) * (yy[..., None] / 0.6),
                    mid + (hor - mid) * ((yy[..., None] - 0.6) / 0.4))
    grad = np.repeat(grad, W, 1)
    common_ = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    # far field below the horizon
    field = hatched(W, FLOOR - 470 + 10, (70, 52, 92), tone=0.45, angle=4, spacing=3.6, seed=3, grad=(0.15, -0.15))
    common_.alpha_composite(field, (0, 470))
    hg = C['hedge']
    for hx in [WALL_R - 200, WALL_R - 200 + hg.size[0] - 40]:
        common_.alpha_composite(hg, (hx, 478 - int(hg.size[1] * 0.55)))
    # the wall, the eave
    wall = C['wall'].crop((0, 0, WALL_R, FLOOR - 120))
    common_.alpha_composite(wall, (0, 120))
    eave = hatched(WALL_R + 34, 34, (60, 44, 60), tone=0.25, angle=0, spacing=3.0, seed=4)
    common_.alpha_composite(eave, (0, 100))
    d = ImageDraw.Draw(common_)
    d.line([(WALL_R, 120), (WALL_R, FLOOR)], fill=(24, 16, 24, 255), width=3)
    # lantern beside the door
    lp = PV['lantern']['hook']
    d.line([(int(sx(0.78)), 300), (int(sx(0.78)), 318)], fill=(20, 14, 18, 255), width=2)
    place(common_, C['lantern'], lp, (sx(0.78), 318))
    # porch boards and fascia
    boards = hatched(STEP_X, 42, (176, 140, 110), tone=0.62, angle=0, spacing=3.2, seed=5)
    bd = ImageDraw.Draw(boards)
    for y in range(0, 42, 10):
        bd.line([(0, y), (STEP_X, y)], fill=(40, 26, 26, 255), width=2)
    for k in range(0, STEP_X, 157):
        y0 = (k * 7) % 4 * 10
        bd.line([(k, y0), (k, y0 + 10)], fill=(40, 26, 26, 255), width=2)
    common_.alpha_composite(boards, (0, FLOOR))
    fascia = hatched(STEP_X, H - FLOOR - 42, (120, 82, 76), tone=0.4, angle=88, spacing=3.4, seed=6)
    common_.alpha_composite(fascia, (0, FLOOR + 42))
    d.line([(0, FLOOR + 42), (STEP_X, FLOOR + 42)], fill=(24, 14, 18, 255), width=3)
    # steps down at the porch end
    for k in range(3):
        stp = hatched(W - STEP_X, 34, (150, 116, 98), tone=0.55 - 0.08 * k, angle=0, spacing=3.0, seed=7 + k)
        common_.alpha_composite(stp, (STEP_X + k * 26, FLOOR + 16 + k * 34))
        d.line([(STEP_X + k * 26, FLOOR + 16 + k * 34), (W, FLOOR + 16 + k * 34)], fill=(24, 14, 18, 255), width=2)
    d.line([(STEP_X, FLOOR), (STEP_X, H)], fill=(24, 14, 18, 255), width=3)
    # door casing
    cas = (214, 200, 172)
    for (x0, y0, w_, h_) in [(OPEN_L - 14, OPEN_T - 16, 14, DOOR_H + 16), (OPEN_R, OPEN_T - 16, 14, DOOR_H + 16),
                             (OPEN_L - 22, OPEN_T - 26, OPEN_R - OPEN_L + 44, 14)]:
        c = hatched(w_, h_, cas, tone=0.7, angle=90 if h_ > w_ else 0, spacing=3.0, seed=x0)
        common_.alpha_composite(c, (x0, y0))
        d.rectangle([x0, y0, x0 + w_, y0 + h_], outline=(26, 18, 22, 255), width=2)
    return grad, common_


def sill_card():
    w_, h_ = int(sx(0.62) - sx(-0.56)), 16
    c = hatched(w_, h_, (170, 166, 176), tone=0.62, angle=0, spacing=2.6, seed=21)
    d = ImageDraw.Draw(c)
    d.rectangle([0, 0, w_ - 1, h_ - 1], outline=(26, 18, 22, 255), width=2)
    d.line([(2, 3), (w_ - 3, 3)], fill=(236, 230, 214, 255), width=2)
    return c, (int(sx(-0.56)), FLOOR - 4)


GRAD, STAGE = build_stage()
SILL, SILL_AT = sill_card()
CLOUDS = [np.asarray(C['cloud_%02d' % f].convert('RGB'), np.float32) / 255 for f in range(0, 62, 6)]
SKY = []
for cl in CLOUDS:
    sky = GRAD.copy()
    fade = np.clip((405 - np.arange(410)) / 60.0, 0, 1)[:, None, None]
    sky[:410] = sky[:410] * (1 - fade + fade * (0.30 + 0.70 * cl))
    SKY.append(sky)

# paper grain + vignette, multiplied over everything
_rng = np.random.default_rng(99)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = 1 - 0.30 * (((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.70)) ** 2)
GRAIN = 1 + (box_blur(_rng.random((H, W)).astype(np.float32), 0.8) - 0.5) * 0.06
FINISH = (np.clip(VIG, 0.55, 1) * GRAIN)[..., None]
# light spilling from the open door: across the sill, onto the boards, toward us
spill = Image.new('L', (W, H), 0)
sd = ImageDraw.Draw(spill)
sd.polygon([(OPEN_L, FLOOR - 2), (OPEN_R, FLOOR - 2), (OPEN_R + 330, H), (OPEN_L - 60, H)], fill=210)
sd.rectangle([OPEN_L, OPEN_T, OPEN_R, FLOOR], fill=120)
spill = spill.filter(ImageFilter.GaussianBlur(26))
SPILL = (np.asarray(spill, np.float32) / 255)[..., None] * np.array([1.0, 0.70, 0.30])[None, None]
glow = Image.new('L', (W, H), 0)
ImageDraw.Draw(glow).ellipse([OPEN_L - 140, OPEN_T - 60, OPEN_R + 140, FLOOR + 90], fill=120)
GLOW = (np.asarray(glow.filter(ImageFilter.GaussianBlur(60)), np.float32) / 255)[..., None] * np.array([1.0, 0.62, 0.28])[None, None]


# ------------------------------------------------------------------ the dog
DOG_S = 1.0
CENTRE = PV['dog_body']['centre']
LEG = PV['dog_fore']['paw'][1] - PV['dog_fore']['top'][1]
SH_OFF = PV['dog_body']['shoulder'][1] - CENTRE[1]


def body_pt(name, card='dog_body'):
    p = PV[card][name]
    return (p[0] - CENTRE[0], p[1] - CENTRE[1])


def dog_pose(i, i_real=None):
    f = SF[i]
    d = f['dog']; a = d['act']
    t = f['t']
    crouch = a['crouch']
    # the retreat lands as a snap: the crouch arrives on the choice frame, not over half a second
    if EV['retreat'] <= i < EV['watch1']:
        crouch = max(crouch, 0.85)          # hard pose substitution on the choice frame
    head = a['head']
    if EV['retreat'] <= i < EV['watch1']:
        head = min(head, 0.35)
    tail = a['tail']
    if EV['retreat'] <= i < EV['watch1']:
        tail = max(tail, 1.3)
    if EV['approach'] <= i < EV['approach'] + 12:
        head = min(head, 0.9 - 0.45 * ease((i - EV['approach'] + 1) / 6))
    lie = a['lie']
    if i >= EV['lie']:
        lie = max(lie, ease((i - EV['lie'] + 1) / 10))
    moving = abs(xs[min(i + 1, N - 1)] - xs[max(i - 1, 0)]) > 0.002
    return dict(x=d['x'], face=facing(i_real if i_real is not None else i), crouch=crouch, lie=lie, head=head, tail=tail, wag=a['wag'], rest=a['rest'],
                look=a['look'], phase=2 * math.pi * dist[i] / STRIDE, moving=moving, t=t,
                doorhead=EV['retreat'] <= i < EV['watch1'])


NOSE_ANG = None


def draw_dog(layer, probe, P, look_at=None):
    X = sx(P['x'])
    f = P['face']
    back = f < 0
    sfx = '_back' if back else ''
    lie, cr = P['lie'], P['crouch']
    # body height: paws on the boards; crouch and lying lower the card
    shoulder_y = PAW - LEG + cr * 24 * (1 - lie) + lie * (LEG - 10)
    Yc = shoulder_y - SH_OFF
    tilt = -cr * 7 * (1 - lie) + lie * 1.5      # crouching dips the rump a little (rotation, local deg)
    bob = 0.0
    swing = 0.0
    if P['moving'] and lie < 0.2:
        bob = -2.5 * abs(math.sin(P['phase']))
        swing = 24.0
    Yc += bob

    def L2S(p):
        """local dog coords (centre-relative, source facing left) -> screen, applying tilt and the card turn"""
        a = math.radians(tilt)
        x, y = p
        xr, yr = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
        return (X + f * xr, Yc + yr)

    def put(dst, card, pivot_name, at_local, ang):
        nm = card + sfx if (card + sfx) in C else card
        place(dst, C[nm], PV[card][pivot_name], L2S(at_local), angle=(ang + tilt) * (1 if f >= 0 else -1), sx_=f)

    if abs(f) < 0.05:
        # edge-on: the dog is only the thin edge of a card for a held moment
        top = Yc - 60 - 40 * (1 - lie)
        edge = Image.new('RGBA', (16, int(PAW - top) + 8), (0, 0, 0, 0))
        ed = ImageDraw.Draw(edge)
        hgt = edge.size[1] - 4
        ed.polygon([(5, 2), (10, 0), (11, hgt), (6, hgt + 2)], fill=(236, 230, 214, 255), outline=(26, 18, 22, 255))
        ed.line([(7, 6), (8, hgt - 4)], fill=(150, 140, 120, 255), width=1)
        layer.alpha_composite(edge, (int(X - 8), int(top)))
        probe.alpha_composite(edge, (int(X - 8), int(top)))
        return
    ph = P['phase']
    # legs: walk swing, crouch splay, lying fold (fore legs forward, hind legs tucked)
    fore_lie, hind_lie = 82 * lie, 76 * lie
    cl = cr * (1 - lie)
    a_ff = swing * math.sin(ph + math.pi) + 26 * cl + fore_lie
    a_fn = swing * math.sin(ph) + 26 * cl + fore_lie
    a_hf = swing * math.sin(ph + math.pi / 2) - 30 * cl + hind_lie
    a_hn = swing * math.sin(ph + 3 * math.pi / 2) - 30 * cl + hind_lie
    sh = body_pt('shoulder'); hn = body_pt('hip_n'); hf = body_pt('hip_f')
    put(layer, 'dog_fore_far', 'top', (sh[0] - 13, sh[1]), a_ff)
    put(layer, 'dog_hind_f', 'top', hf, a_hf)
    put(layer, 'dog_fore', 'top', sh, a_fn)
    put(layer, 'dog_hind_n', 'top', hn, a_hn)
    # tail
    ta = -55 + P['tail'] * 105 + P['wag'] * 28 * math.sin(2 * math.pi * 3.2 * P['t'])
    put(layer, 'dog_tail', 'base', body_pt('rump'), ta)
    put(layer, 'dog_body', 'centre', (0, 0), 0)
    put(probe, 'dog_body', 'centre', (0, 0), 0)
    # head: pivot at the neck; down for low, chin to the paws at rest, forward and level to look in
    nk = body_pt('neck')
    ha = -(0.9 - min(P['head'], 0.9)) * 70
    ha = ha * (1 - P['rest']) + (-62) * P['rest']
    nkx, nky = nk
    if P['rest'] > 0:
        nky += 10 * P['rest']
    lk = P['look']
    if lk > 0:
        ha = ha * (1 - lk) + 14 * lk      # nose up and in, toward the lit opening
        nkx -= 6 * lk
        nky -= 8 * lk
    if look_at is not None and f > 0.95 and lie < 0.3:
        # attention: the head turns to follow the butterfly (the soft voice made visible)
        ns, nn = PV['dog_head']['neck'], PV['dog_head']['nose']
        th_n = math.degrees(math.atan2(nn[1] - ns[1], nn[0] - ns[0]))
        q = L2S((nkx, nky))
        th_t = math.degrees(math.atan2(look_at[1] - q[1], look_at[0] - q[0]))
        want = (th_t - th_n + 180) % 360 - 180
        ha = max(-70, min(45, want))
    if P['doorhead']:
        # substitution: commanded, the dog's head is a shut door
        # hung low: the knob edge on the neck, the door hanging down toward the boards like a lowered head
        place(layer, C['door_head'], PV['door_head']['knob'], L2S((nkx + 4, nky + 6)), angle=-38 * f, sx_=f)
    else:
        if False:
            # (retired in round 2: read as a rectangle) a stretched neck of fur card fills the gap when the head leans in (drawn behind the head)
            a0, a1 = nk, (nkx, nky)
            mid = ((a0[0] + a1[0]) / 2 + 6, (a0[1] + a1[1]) / 2 + 4)
            span = math.hypot(a1[0] - a0[0], a1[1] - a0[1]) + 40
            put(layer, 'dog_neck', 'c', mid, 0) if False else place(layer, C['dog_neck' + sfx] if ('dog_neck' + sfx) in C else C['dog_neck'],
                PV['dog_neck']['c'], L2S(mid), angle=(-8 + tilt) * (1 if f >= 0 else -1), sx_=f * span / C['dog_neck'].size[0], sy_=1.0)
        put(layer, 'dog_head', 'neck', (nkx, nky), ha)


def dog_shadow(frame_rgba, P):
    X = sx(P['x'])
    w = 150 + 30 * P['lie']
    sh = Image.new('RGBA', (int(w) + 40, 40), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([20, 12, 20 + w, 28], fill=(20, 10, 30, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(5))
    frame_rgba.alpha_composite(sh, (int(X - w / 2 - 20), PAW - 22))


# ------------------------------------------------------------------ the person
TORSO = PV['p_torso']
P_LEG = PV['p_leg']
LEG_H = P_LEG['foot'][1] - P_LEG['hip'][1]


def draw_person(fr, i, overlays):
    f = SF[i]; p = f['person']
    X = sx(p['x'])
    sit = ease(p['sit'])
    hip_y = PAW - 14 - LEG_H * (1 - 0.82 * sit)
    # stepping aside: little hops while she moves
    if 0 < abs(p['x'] + 0.28) and abs(p['x'] + 1.25) > 0.01 and sit < 0.8:
        hip_y -= 6 * abs(math.sin(i * math.pi / 4))
    hip = (X, hip_y)
    # legs: standing straight, sitting folded forward (toward the door / the dog)
    la = -88 * sit
    place(fr, darker(C['p_leg'], 0.8), P_LEG['hip'], (X - 8, hip_y), angle=la)
    place(fr, C['p_leg'], P_LEG['hip'], (X + 8, hip_y + 2), angle=la)
    # torso: its hip point on the hip
    tq = (TORSO['hip'][0], TORSO['hip'][1] - 6)
    place(fr, C['p_torso'], tq, hip, angle=-4 * sit)
    neck = (X + (TORSO['neck'][0] - tq[0]), hip_y + (TORSO['neck'][1] - tq[1]))
    sh_r = (X + (TORSO['shoulder_r'][0] - tq[0]) - 6, hip_y + (TORSO['shoulder_r'][1] - tq[1]) + 4)
    return neck, sh_r


def draw_head(fr, i, neck):
    f = SF[i]; p = f['person']; voice = p['voice']
    t = f['t']
    if voice == 'call':
        on = max(v for v, vv in voice_on if v <= i)
        k = i - on
        # the command: her head is replaced by a shouting mouth, enlarged; mouth on two syllables, then held open
        nm = 'face_loud' if (k < 6 or 9 <= k < 16 or k >= 16) else 'face_half'
        s = 2.0 + 0.4 * max(0, 1 - k / 4)
        card = C[nm].resize((int(C[nm].size[0] * s), int(C[nm].size[1] * s)), Image.BICUBIC)
        pv = (PV[nm]['neck'][0] * s, PV[nm]['neck'][1] * s)
        place(fr, card, pv, (neck[0] - 18, neck[1] + 10), angle=10)   # leaning out at the dog
        return 'loud', k
    if voice == 'soft':
        # the soft voice keeps her own head; it is spoken by the slip and carried by the butterfly
        on = max(v for v, vv in voice_on if v <= i)
        place(fr, C['p_head'], PV['p_head']['neck'], neck, angle=8)
        return 'soft', i - on
    place(fr, C['p_head'], PV['p_head']['neck'], neck)
    return None, 0


def draw_reach(fr, i, sh_r, dogX):
    p = SF[i]['person']
    r = p['reach']
    if r <= 0.01:
        return
    # the telescoping arm: sleeve segment after sleeve segment, out across the porch toward the dog
    target = dogX - 70
    L = max(0.0, (target - sh_r[0]) * r)
    seg = C['p_sleeve']
    sw = seg.size[0] - 8
    ang = math.degrees(math.atan2(70, target - sh_r[0])) * 0.6
    n = int(L // sw) + 1
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    for k in range(n):
        d_ = min(k * sw, L)
        place(fr, seg, PV['p_sleeve']['l'], (sh_r[0] + ca * d_, sh_r[1] + sa * d_), angle=ang)
    end = (sh_r[0] + ca * (L - 24), sh_r[1] + sa * (L - 24))
    place(fr, C['hand_reach'], PV['hand_reach']['wrist'], end, angle=ang + 6)


def draw_low_hand(fr, i, sh_r):
    p = SF[i]['person']
    lo = ease(p['low'])
    if lo <= 0.01:
        return None
    # the low hand: her arm runs along the boards; the hand (Insect Zoo) rests open by the sill
    target = (sx(-0.95), FLOOR - 10)
    start = sh_r
    end = (start[0] + (target[0] - start[0]) * lo, start[1] + (target[1] - start[1]) * lo)
    seg = C['p_sleeve']
    dx, dy = end[0] - start[0], end[1] - start[1]
    L = math.hypot(dx, dy)
    ang = math.degrees(math.atan2(dy, dx))
    sw = seg.size[0] - 8
    for k in range(int(L // sw) + 1):
        d_ = min(k * sw, max(0, L - sw * 0.6))
        place(fr, seg, PV['p_sleeve']['l'], (start[0] + dx / max(L, 1) * d_, start[1] + dy / max(L, 1) * d_), angle=ang)
    place(fr, C['hand_reach'], PV['hand_reach']['wrist'], end, angle=4)
    return end


def butterfly_pos(i, hand_at, dog_head):
    """the soft voice made visible: the butterfly leaves the low hand and goes to the dog, and finally into the house."""
    t = SF[i]['t']
    rest = (hand_at[0] + 112, hand_at[1] - 26) if hand_at else None
    if rest is None:
        return None, False
    def path(a, b, u, lift):
        u = ease(u)
        return (a[0] + (b[0] - a[0]) * u + 14 * math.sin(u * 9), a[1] + (b[1] - a[1]) * u - lift * math.sin(u * math.pi) + 8 * math.sin(u * 17))
    near_dog = (dog_head[0] - 20, dog_head[1] - 125)
    if 7.4 <= t < 8.4:
        return path(rest, near_dog, (t - 7.4) / 1.0, 90), True
    if 8.4 <= t < 9.4:
        u = (t - 8.4)
        return (near_dog[0] + 26 * math.sin(u * 7), near_dog[1] + 14 * math.cos(u * 9)), True
    if 9.4 <= t < 10.2:
        return path(near_dog, rest, (t - 9.4) / 0.8, 60), True
    if 10.4 <= t < 11.6:
        u = (t - 10.4) / 1.2
        return (rest[0] + 120 * math.sin(u * math.pi), rest[1] - 70 * math.sin(u * math.pi) + 6 * math.sin(u * 30)), True
    if 26.4 <= t < 27.6:
        inside = (sx(-0.15), OPEN_T + 170)
        return path(rest, inside, (t - 26.4) / 1.2, 50), True
    if t >= 27.6:
        return None, False
    return rest, False


def speech(fr, i, kind, k, neck):
    if kind is None:
        return
    t = SF[i]['t']
    if kind == 'loud':
        txt, font, col, paper = 'COME HERE!', FONT('BigShoulders-900', 64), (24, 14, 18), (240, 232, 210)
        s = 1.0 + 0.35 * max(0, 1 - k / 3)
        rot = 4 if (k // 3) % 2 else -3
    else:
        txt = 'come in.' if t > 25 else "it's all right."
        font, col, paper = FONT('Literata-Italic', 26), (40, 30, 40), (240, 232, 210)
        s, rot = 1.0, -2
    bb = font.getbbox(txt)
    w_, h_ = bb[2] - bb[0] + 28, bb[3] - bb[1] + 22
    slip = Image.new('RGBA', (w_, h_), (0, 0, 0, 0))
    d = ImageDraw.Draw(slip)
    rng = np.random.default_rng(len(txt))
    pts = [(0 + rng.integers(0, 5), 0 + rng.integers(0, 4)), (w_ - rng.integers(0, 6), rng.integers(0, 4)),
           (w_ - rng.integers(0, 4), h_ - rng.integers(0, 6)), (rng.integers(0, 6), h_ - rng.integers(0, 4))]
    d.polygon(pts, fill=paper + (255,), outline=(30, 20, 24, 255))
    d.text((14 - bb[0], 10 - bb[1]), txt, font=font, fill=col + (255,))
    if s != 1.0:
        slip = slip.resize((int(w_ * s), int(h_ * s)), Image.BICUBIC)
    slip = slip.rotate(rot, expand=True, resample=Image.BICUBIC)
    sh = shadowed(slip)
    if kind == 'loud':
        at = (int(neck[0] + 60), int(neck[1] - 150))
    else:
        at = (int(neck[0] + 30), int(neck[1] - 92))
    fr.alpha_composite(sh, (at[0] + 4, at[1] + 5))
    fr.alpha_composite(slip, at)


# ------------------------------------------------------------------ door
def draw_door(fr, i):
    f = SF[i]
    o = EV['door_open']
    if i < o:
        op = 0.52
    else:
        u = (i - o + 1) / 5
        op = 0.52 + (0.86 - 0.52) * ease(u) + (0.05 * math.sin((i - o) * 1.3) * math.exp(-(i - o) / 5) if u >= 1 else 0)
    sxd = math.cos(op * math.pi / 2)
    door = C['door']
    # swinging inward on the left hinge: narrower, darker
    if sxd < 0.999:
        a = np.asarray(door, np.float32).copy()
        a[..., :3] *= 0.75 + 0.25 * sxd
        door = Image.fromarray(a.astype(np.uint8), 'RGBA')
    pv = PV['door']['hinge_top']
    place(fr, door, pv, (OPEN_L, OPEN_T), sx_=sxd)
    return op


def lit_level(i):
    o = EV['door_open']
    if i < o + 2:
        return 0.0
    return min(1.0, (i - o - 1) / 3.0)


# ------------------------------------------------------------------ frames
TITLE = 'PAE-02 · SCION 01 · TERRY GILLIAM'
SUB = 'comic cutout metamorphosis — the threshold, cut from found film'


def card_frame(k, end=False):
    sky = SKY[(k // 12) % len(SKY)]
    img = np.zeros((H, W, 3), np.float32)
    img[:470] = sky
    img[470:] = sky[-1]
    fr = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(fr)
    if not end:
        f1, f2 = FONT('BigShoulders-900', 76), FONT('Literata-Italic', 30)
        slip_lines = [(TITLE, f1, (24, 14, 18)), (SUB, f2, (50, 36, 46))]
        y = 230
        for j, (txt, fnt, col) in enumerate(slip_lines):
            bb = fnt.getbbox(txt)
            w_, h_ = bb[2] - bb[0] + 50, bb[3] - bb[1] + 34
            slip = Image.new('RGBA', (w_, h_), (240, 232, 210, 255))
            ImageDraw.Draw(slip).text((25 - bb[0], 17 - bb[1]), txt, font=fnt, fill=col)
            ImageDraw.Draw(slip).rectangle([0, 0, w_ - 1, h_ - 1], outline=(30, 20, 24), width=2)
            drop = 0 if k > 8 + 6 * j else -400 + 400 * ease(k / (8 + 6 * j))
            slip = slip.rotate([-2, 1.5][j], expand=True, resample=Image.BICUBIC)
            fr.alpha_composite(shadowed(slip), ((W - slip.size[0]) // 2 + 5, int(y + drop) + 6))
            fr.alpha_composite(slip, ((W - slip.size[0]) // 2, int(y + drop)))
            y += h_ + 40
        # the dog card, peeking in from the bottom
        dg = C['dog_head']
        place(fr, dg, PV['dog_head']['neck'], (W - 180, H - 40 + max(0, 30 - k) * 4), angle=-10, sx_=1.6, sy_=1.6)
    else:
        f1, f2 = FONT('BigShoulders-900', 46), FONT('Literata-Regular', 21)
        lines = ['MADE OF', ]
        body = [
            'the dog: Amateur Film New Jersey C (Home Movies) — cut out, engraved, split on pivots',
            'the door, the woman, her jeans, the coat wall: Straight Talk (NTIS, 1992)',
            'the shouting mouth: We Learn About the Telephone I  ·  the hand: The Door to Heaven',
            'the butterfly: Insect Zoo  ·  the lantern: Anthracite: Pre-Shift Examinations',
            'the stone wall: the dog film again  ·  the dusk and the hills: Top Of The Cloud',
            'all public domain; engraved by luminance hatching; every sound synthesized here',
            "the dog's choices: the PAELEO threshold score, frame for frame",
        ]
        w_, h_ = 1120, 470
        slip = Image.new('RGBA', (w_, h_), (240, 232, 210, 255))
        sd_ = ImageDraw.Draw(slip)
        sd_.rectangle([0, 0, w_ - 1, h_ - 1], outline=(30, 20, 24), width=2)
        sd_.text((40, 30), 'MADE OF', font=f1, fill=(24, 14, 18))
        for j, ln in enumerate(body):
            sd_.text((40, 110 + j * 46), ln, font=f2, fill=(40, 28, 36))
        slip = slip.rotate(-1, expand=True, resample=Image.BICUBIC)
        fr.alpha_composite(shadowed(slip), ((W - slip.size[0]) // 2 + 5, 125 + 6))
        fr.alpha_composite(slip, ((W - slip.size[0]) // 2, 125))
        st = C['dog_body_back']
        place(fr, st, PV['dog_body']['centre'], (W - 150, H - 70), angle=8, sx_=-0.9, sy_=0.9)
    out = np.asarray(fr.convert('RGB'), np.float32) / 255 * FINISH
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)


def front_light(la, xs_, ys_):
    """how much of the leftmost 28% of the dog (its door-side end) is pale: high when the head is a door"""
    x0, x1 = xs_.min(), xs_.max()
    sel = xs_ < x0 + 0.28 * (x1 - x0)
    px = la[ys_[sel], xs_[sel], :3] @ np.array([0.299, 0.587, 0.114]) / 255
    return (px > 0.72).mean() if len(px) else 0.0


def front_warm(la, xs_, ys_):
    """mean (R - B) of the door-side 28% of the dog: the engraved dog is ochre, the door-head is grey-white"""
    x0, x1 = xs_.min(), xs_.max()
    sel = xs_ < x0 + 0.28 * (x1 - x0)
    px = la[ys_[sel], xs_[sel], :3]
    return float((px[:, 0] - px[:, 2]).mean() / 255) if len(px) else 0.0


CUT_IN = 610   # 25.42 s: the rostrum camera cuts in on the sill and holds there to the end


def camera(i):
    if i < CUT_IN:
        return None
    return (0, 236, 1.6)


def scene_frame(i):
    j = held(i)
    f = SF[i]
    t = f['t']
    sky = SKY[(i // 12) % len(SKY) if (i // (12 * len(SKY))) % 2 == 0 else len(SKY) - 1 - (i // 12) % len(SKY)]
    img = np.zeros((H, W, 3), np.float32)
    img[:470] = sky
    fr = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    fr.alpha_composite(STAGE)
    # interior through the opening
    L = lit_level(i)
    it = C['interior_dark'] if L < 0.5 else C['interior_lit']
    tl = PV['interior_dark']['tl']
    fr.alpha_composite(it.crop((int(tl[0]), int(tl[1]), int(tl[0]) + OPEN_R - OPEN_L, int(tl[1]) + DOOR_H)), (OPEN_L, OPEN_T))
    draw_door(fr, i)
    fr.alpha_composite(SILL, SILL_AT)
    # person
    neck, sh_r = draw_person(fr, j, None)
    kind, k = draw_head(fr, i, neck)
    hand_at = draw_low_hand(fr, j, sh_r)
    # dog
    P = dog_pose(j, i)
    head_at = (sx(P['x']) - 90 * P['face'], PAW - 120)
    bp, flying = butterfly_pos(i, hand_at, head_at)
    look_at = None
    if bp is not None and flying and 7.7 <= t < 11.8:
        bj, _ = butterfly_pos(j, hand_at, head_at)   # attention also on twos
        look_at = bj or bp
        P['wag'] = max(P['wag'], 0.45)
    dog_shadow(fr, P)
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    probe = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_dog(layer, probe, P, look_at)
    fr.alpha_composite(layer)
    draw_reach(fr, i, sh_r, sx(P['x']))
    # butterfly
    if bp is not None:
        flap = abs(math.cos(2 * math.pi * 5 * t)) * 0.85 + 0.15 if flying else 1.0
        sc = 1.0
        if t >= 27.0:
            sc = max(0.2, 1 - (t - 27.0) / 0.6 * 0.8)
        place(fr, C['butterfly'], PV['butterfly']['body'], bp, angle=-20, sx_=flap * sc, sy_=sc)
        place(fr, C['butterfly'], PV['butterfly']['body'], bp, angle=20, sx_=-flap * sc * 0.9, sy_=sc)
    speech(fr, i, kind, k, neck)
    out = np.asarray(fr.convert('RGB'), np.float32) / 255
    dim = 1 - 0.16 * t / 32
    out = out * dim
    if L > 0:
        out = out + (SPILL * 0.55 + GLOW * 0.45) * L * out * 1.4 + SPILL * 0.10 * L
    out = out * FINISH
    frame = (np.clip(out, 0, 1) * 255).astype(np.uint8)
    cam = camera(i)
    if cam is not None:
        x0c, y0c, z = cam
        frame = np.asarray(Image.fromarray(frame).crop((x0c, y0c, x0c + int(W / z), y0c + int(H / z))).resize((W, H), Image.LANCZOS))
    # measurement from the render itself
    la = np.asarray(layer, np.float32)
    alpha = la[..., 3] / 255
    m = alpha > 0.5
    pa = np.asarray(probe, np.float32)[..., 3] / 255 > 0.5
    rec = {'i': i, 't': round(t, 4), 'state': f['dog']['state'], 'x_score': f['dog']['x']}
    if m.any():
        ys_, xs_ = np.nonzero(m)
        pys, pxs = np.nonzero(pa)
        lum = (la[..., :3] @ np.array([0.299, 0.587, 0.114]))[m] / 255
        x0c, y0c, z = cam if cam is not None else (0, 0, 1.0)
        xst = float(pxs.mean())
        rec.update({'x_stage': round(xst, 2), 'x_screen': round((xst - x0c) * z, 2),
                    'y_screen': round((float(ys_.max()) - y0c) * z, 2), 'camera': [x0c, y0c, z],
                    'bbox_stage': [int(xs_.min()), int(ys_.min()), int(xs_.max()), int(ys_.max())],
                    'head_x_stage': int(xs_.min()),
                    'mean_lum': round(float(lum.mean()), 3),
                    'body_y_stage': round(float(pys.mean()), 2),
                    'front_light': round(float(front_light(la, xs_, ys_)), 3),
                    'front_warm': round(float(front_warm(la, xs_, ys_)), 3),
                    'white_frac': round(float((lum > 0.80).mean()), 3)})
    return frame, rec


def main():
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else os.path.join(ROOT, 'build', 'video.mp4')
    rng_ = None
    if '--frames' in sys.argv:
        a, b = sys.argv[sys.argv.index('--frames') + 1].split(':')
        rng_ = (int(a), int(b))
    if '--stills' in sys.argv:
        for t in [3.6, 9.0, 19.0, 28.0]:
            i = int(round(t * FPS))
            fr, _ = scene_frame(i)
            Image.fromarray(fr).save(os.path.join(ROOT, 'stills', 'still_%04.1fs.jpg' % t), quality=92)
        return
    if '--sheet' in sys.argv:
        ids = [int(v) for v in sys.argv[sys.argv.index('--sheet') + 1].split(',')]
        tw, th = 426, 240
        cols = 3
        sheet = Image.new('RGB', (tw * cols, th * ((len(ids) + cols - 1) // cols)))
        for n_, i in enumerate(ids):
            fr, _ = scene_frame(i)
            im = Image.fromarray(fr).resize((tw, th), Image.LANCZOS)
            ImageDraw.Draw(im).text((6, 4), '%d  %.2fs %s' % (i, i / FPS, SF[i]['dog']['state']), fill=(255, 255, 0))
            sheet.paste(im, ((n_ % cols) * tw, (n_ // cols) * th))
        sheet.save(sys.argv[sys.argv.index('--sheet') + 2])
        return
    if rng_:
        for i in range(*rng_):
            fr, rec = scene_frame(i)
            Image.fromarray(fr).save(os.path.join(CACHE, 'probe_%03d.jpg' % i), quality=90)
        return
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H),
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out],
                          stdin=subprocess.PIPE)
    for k in range(72):
        ff.stdin.write(card_frame(k).tobytes())
    trace = []
    for i in range(N):
        fr, rec = scene_frame(i)
        ff.stdin.write(fr.tobytes())
        trace.append(rec)
        if i % 96 == 0:
            print('frame', i, flush=True)
    for k in range(72):
        ff.stdin.write(card_frame(k, end=True).tobytes())
    ff.stdin.close(); ff.wait()
    json.dump({'events': EV, 'raw': trace}, open(os.path.join(CACHE, 'raw_trace.json'), 'w'))
    print('done', out)


if __name__ == '__main__':
    main()
