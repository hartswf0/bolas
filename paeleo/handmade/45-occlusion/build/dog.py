"""SCION 45 · Scene continuity agent. What the archive dog is doing at each score frame, as RGBA sublayers.

dog_frame(i) -> dict:
  img      dog-local RGBA (source px space + OFFSET), straight alpha
  anchor   dog-local point that sits on the floor at the dog's world position
  mirror   True if this pose is shown mirrored (whole pose, never used to turn)
  Xc, D    world: body centre along the porch (m) and depth in front of the wall (m)
  shear    vertical shear (screen px per px) for a body angled into depth (lying across the sill)
  parts    names of the sublayers used, for the layer ledger
  head     dog-local head point (for the measured facing)
  kind     'cel' (one whole real frame) or 'rig' (real parts re-assembled)
Motion is substitution of real frames (walk, turn) and re-assembly of real parts (lie, head turns). Version: dog-v6
"""
import json, math, os
import numpy as np
from PIL import Image
import rig

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
SCORE = json.load(open(os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')))
FR = SCORE['frames']
META = json.load(open(os.path.join(HERE, 'cache/cels/cels.json')))
OX, OY = 60, 20                      # local canvas offset so rotated parts never clip
CANVAS = (384 + 2 * OX, 288 + OY + 20)
P_SRC = 152.0                        # archive-dog source px per metre (a big dog: shoulder ~0.70 m = ~105 px)
FLOOR = 205                          # source foot line used by the rig poses
CENTER_OFFSET = 0.14                 # world body centre = score x - 0.14 (so x = 0.59 lays the loin under the jamb)

# real-frame sequences
WALK_LOW = [42, 43, 44, 45, 46, 47]                              # head-low walk, shown mirrored (faces the door)
TURN_AWAY = [13, 14, 15, 17, 19, 20, 26, 28, 30, 33, 36, 38, 40]  # left -> frontal (head low) -> right
TURN_BACK = [30, 26, 19, 17, 15, 14, 13, 11, 10]   # never passes through a camera-facing frame: the head stays on the door side           # frontal (head up) -> left, for 8.0-9.0
WATCH = [9, 10, 11, 10]                                           # held alert cels (boil)
LIE_D, LIE_SHEAR = -0.05, 0.228   # lying across the sill: its depth pass crosses the casing plane at x = 0.54, under the right jamb
STRIDE = 0.30                                                     # metres per walk cycle (short, wary steps)


def sm(a, b, t):
    t = min(1, max(0, (t - a) / (b - a)))
    return t * t * (3 - 2 * t)


def lerp(a, b, u):
    return a + (b - a) * u


REAR = 61   # source px from the rump to the body centre (0.36 m): profile cels are registered by the rump, which
            # barely moves when the head does, so a head change never slides the body; camera-facing cels by their centre


def whole_cel(n):
    c = rig.cel(n)
    out = Image.new('RGBA', CANVAS, (0, 0, 0, 0))
    out.paste(c, (OX, OY), c)
    m = META[str(n)]
    bb = m['bbox']
    if n <= 19:
        ax = bb[2] - REAR           # faces left: rump on the right
    elif n <= 35:
        ax = (bb[0] + bb[2]) / 2    # faces the camera
    else:
        ax = bb[0] + REAR           # faces right: rump on the left
    return out, (ax + OX, m['foot_y'] + OY)


HEAD_ONLY = [None]


def lie_pose(u, head_th, head_kind='L', head_dy=0.0, head_dx=0.0):
    """Re-assembled lying dog from frame 10 parts. u: 0 standing ... 1 lying. head_kind L (profile, faces the pose's
    front), F (frontal head), B (frontal head shown as the back of the head: same outline, lit from behind).
    Returns local RGBA, anchor, head point."""
    h, hp = rig.part('head10'); t, tp = rig.part('torso10')
    fa, fap = rig.part('foreA10'); fb, fbp = rig.part('foreB10'); k, kp = rig.part('hind10')
    # hind end goes down first (sit), then the front (lie): staged, not one tween
    uh = sm(0.0, 0.6, u); uf = sm(0.35, 1.0, u)
    tor_th = lerp(0, -12, uf) + lerp(0, 9, uh) * (1 - uf)
    drop_r = lerp(0, 40, uh); drop_f = lerp(0, 46, uf)
    # torso: rotate, then translate by the mean drop
    T = rig.affine(t, tp, tor_th, (160, 150))
    a = np.array(T)[:, :, 3]
    bot = np.nonzero(a.max(1) > 128)[0].max() if a.max() > 128 else 176
    base_bot = 176
    dy = lerp(0, FLOOR - 2 - bot, uf) + lerp(0, 30, uh) * (1 - uf)
    tdst = (160 + OX, 150 + dy + OY)
    neck = rig.fwd(hp, tp, tor_th, tdst)
    chest = rig.fwd((108, 157), tp, tor_th, tdst)
    rump = rig.fwd((200, 172), tp, tor_th, tdst)
    F = FLOOR + OY
    # legs: from their standing place to folded
    fa_th = lerp(0, 80, uf); fb_th = lerp(0, 62, uf); k_th = lerp(0, 84, uh)
    fa_dst = (lerp(140 + OX, chest[0] + 2, uf), lerp(163 + OY, F - 9, uf))
    fb_dst = (lerp(114 + OX, chest[0] + 8, uf), lerp(160 + OY, F - 13, uf))
    k_dst = (lerp(195 + OX, rump[0] + 4, uh), lerp(175 + OY, F - 9, uh))
    L = [(fb, fbp, fb_th, fb_dst, (1, 1)), (t, tp, tor_th, tdst, (1, 1)), (k, kp, k_th, k_dst, (1, 1)),
         (fa, fap, fa_th, fa_dst, (1, 1))]
    HEAD_ONLY[0] = None
    if head_kind == 'L':
        L.append((h, hp, head_th, (neck[0] + head_dx, neck[1] + head_dy), (1, 1)))
        headpt = rig.fwd((80, 85), hp, head_th, (neck[0] + head_dx, neck[1] + head_dy))
    elif head_kind == 'T':
        # turning away into the room: the profile head foreshortened as it rotates away from the camera
        hl = (h, hp, head_th, (neck[0] + 4 + head_dx, neck[1] + head_dy), (0.70, 0.97))
        L.append(hl)
        HEAD_ONLY[0] = rig.compose([hl], CANVAS)
        headpt = rig.fwd((80, 85), hp, head_th, (neck[0] + 4 + head_dx, neck[1] + head_dy), (0.70, 0.97))
    else:
        hf, hfp = rig.part('headBack' if head_kind == 'B' else 'headF')
        hl = (hf, hfp, head_th, (neck[0] + 2 + head_dx, neck[1] + 10 + head_dy), (0.78, 0.78))
        L.append(hl)
        if head_kind == 'B':
            HEAD_ONLY[0] = rig.compose([hl], CANVAS)
        headpt = (neck[0] + 2 + head_dx, neck[1] - 14 + head_dy)
    img = rig.compose(L, CANVAS)
    anchor = (150 + OX, F)
    return img, anchor, headpt


def mirror_img(img, anchor, headpt):
    m = img.transpose(Image.FLIP_LEFT_RIGHT)
    W = img.size[0]
    return m, (W - 1 - anchor[0], anchor[1]), (W - 1 - headpt[0], headpt[1])


def dog_frame(i):
    f = FR[i]; t = f['t']; d = f['dog']; st = d['state']; a = d['act']
    x = d['x']
    Xc = x - CENTER_OFFSET
    D = 1.05
    shear = 0.0
    parts = []
    kind = 'cel'
    mirror = False
    tone = 'plain'   # 'back' = head rendered as backlit silhouette (looking in)
    # ---------------------------------------------------------------- 0 - 1.0 watch (alert, head up)
    if t < 1.0:
        n = WATCH[(i // 7) % len(WATCH)]
        img, anc = whole_cel(n); parts = ['cel%d' % n]; head = (77 + OX, 84 + OY); facing = 1; posture = 'stand'
    # ---------------------------------------------------------------- 1.0 - 2.33 retreat: head drops, backs away
    elif st == 'retreat' or (t < 2.6 and t >= 1.0):
        dist = x - 3.0
        if t < 2.333:
            k = int(dist / (STRIDE / 6))
            n = WALK_LOW[(-k) % 6]                  # cycle played backwards: it steps back
            img, anc = whole_cel(n); img, anc, head = mirror_img(img, anc, (258 + OX, 176 + OY)); mirror = True
            parts = ['cel%d(mirrored, reversed)' % n]; posture = 'crouch'
        else:                                        # 2.33-2.6: head comes up again, via the head-lowering frames
            seq = [15, 14, 13]
            n = seq[min(2, int((t - 2.333) / 0.09))]
            img, anc = whole_cel(n); parts = ['cel%d' % n]; head = (88 + OX, 110 + OY); posture = 'stand'
        facing = 1
    # ---------------------------------------------------------------- 2.6 - 3.42 watch
    elif t < 3.417:
        n = WATCH[(i // 7) % len(WATCH)]
        img, anc = whole_cel(n); parts = ['cel%d' % n]; head = (77 + OX, 84 + OY); facing = 1; posture = 'stand'
    # ---------------------------------------------------------------- 3.42 - 7.46 refuse: turns its back, lies down
    elif t < 7.458:
        tt = t - 3.417
        nT = len(TURN_AWAY)
        if tt < nT / 24.0 + 0.001:                  # the real turn, one frame each (0.58 s)
            n = TURN_AWAY[min(nT - 1, int(tt * 24))]
            img, anc = whole_cel(n); parts = ['cel%d' % n]
            m = META[str(n)]
            head = (m['bbox'][0] + OX, m['bbox'][1] + 20 + OY) if n < 20 else ((m['bbox'][2] + OX, m['bbox'][1] + 20 + OY) if n > 30 else (m['cx'] + OX, m['bbox'][1] + OY))
            facing = 1 if n < 19 else (-1)
            posture = 'stand'
        elif t < 4.15:                              # stands with its back turned (real cel held)
            img, anc = whole_cel(40); parts = ['cel40']; head = (META['40']['bbox'][2] + OX, 150 + OY); facing = -1; posture = 'stand'
        else:                                       # lies down, facing away, head low, then chin on the paws
            u = sm(4.15, 5.0, t)
            hth = lerp(-35, -55, sm(4.4, 5.0, t)) + lerp(0, -20, a['rest'])
            hdy = lerp(0, 6, a['rest'])
            img, anc, head = lie_pose(u, hth, 'L', hdy)
            img, anc, head = mirror_img(img, anc, head); mirror = True; kind = 'rig'
            parts = ['head10', 'torso10', 'foreA10', 'foreB10', 'hind10', '(pose mirrored)']
            facing = -1; posture = 'lie' if u > 0.6 else 'stand'
    # ---------------------------------------------------------------- 7.46 - 9.0 turns back to look, gets up, turns
    elif t < 9.0:
        if t < 7.95:
            # head first: profile-away -> frontal head -> profile toward the door, over the shoulder; body still lying
            ht = t - 7.458
            u = 1 - sm(7.62, 7.95, t)               # starts rising once the head is round
            if ht < 0.08:
                img, anc, head = lie_pose(u, lerp(-70, -20, ht / 0.08), 'L', 6)
                img, anc, head = mirror_img(img, anc, head); facing = -1
                parts = ['head10', 'torso10', 'legs', '(mirrored)']
            elif ht < 0.17:
                img, anc, head = lie_pose(u, 0, 'F', -4, 4)
                img, anc, head = mirror_img(img, anc, head); facing = 1
                parts = ['headF', 'torso10', 'legs', '(mirrored body)']
            else:
                # body mirrored (faces away), head NOT mirrored: it looks back over the shoulder to the door
                body, anc, _ = lie_pose(u, 0, 'F', 0)  # placeholder head replaced below
                img, anc, head = lie_back_look(u)
                facing = 1
                parts = ['head10 (unmirrored, over the shoulder)', 'torso10', 'legs', '(mirrored body)']
            mirror = True; kind = 'rig'; posture = 'lie' if u > 0.5 else 'stand'
        else:
            seq = TURN_BACK
            k = min(len(seq) - 1, int((t - 7.95) / (0.85 / len(seq))))
            n = seq[k]
            img, anc = whole_cel(n); parts = ['cel%d' % n]
            m = META[str(n)]
            head = (m['bbox'][0] + OX, m['bbox'][1] + 20 + OY)
            facing = 1; posture = 'stand'
    # ---------------------------------------------------------------- 9.0 - 14.71 watch, waiting
    elif t < 14.708:
        # waits, head level (cel 14); lifts at the soft voice (cel 13); glances down at the low hand (cel 15)
        n = 13 if 10.5 < t < 11.45 else (15 if 12.6 < t < 13.05 else 14)
        img, anc = whole_cel(n); parts = ['cel%d' % n]; head = (77 + OX, 84 + OY); facing = 1; posture = 'stand'
    # ---------------------------------------------------------------- 14.71 - 23.79 approach, head low
    elif t < 23.792:
        dist = 4.0 - x
        k = int(dist / (STRIDE / 6))
        n = WALK_LOW[k % 6]
        img, anc = whole_cel(n); img, anc, head = mirror_img(img, anc, (258 + OX, 176 + OY)); mirror = True
        parts = ['cel%d(mirrored)' % n]; facing = 1; posture = 'stand'
        # the last 1.3 m it angles in toward the doorway (depth decreases), body sheared into depth
        g = sm(1.9, 0.62, x)
        D = lerp(1.05, LIE_D, g); shear = lerp(0, LIE_SHEAR, g)
    # ---------------------------------------------------------------- 23.79 - 32 lies down across the sill; looks in; stays
    else:
        u = sm(23.792, 24.6, t)
        D = LIE_D; shear = LIE_SHEAR
        look = a['look']; rest = a['rest']
        if look > 0.62:
            # looking in: the head turned into the lit room; the frontal-head outline is what the back of a head looks
            # like, so it is shown from behind: dusk on the back of the skull, the room's light around its edge
            img, anc, head = lie_pose(u, 0, 'B', -12, -13)
            tone = 'back'; parts = ['headF (as back of head)', 'torso10', 'legs']
        elif look > 0.30:
            img, anc, head = lie_pose(u, 14, 'T', -8, -6)
            tone = 'turn'; parts = ['head10 (turning away, foreshortened)', 'torso10', 'legs']
        else:
            # head low as it came (matches the head-low walk), lifts to watch, chin to the paws when it settles
            hth = lerp(-78, -28, sm(23.95, 24.8, t)) + lerp(0, -42, rest) + 3 * math.sin(max(0, t - 24.8) * 1.3) * (1 - rest)
            img, anc, head = lie_pose(u, hth, 'L', lerp(0, 12, rest), lerp(0, -4, rest))
            parts = ['head10', 'torso10', 'foreA10', 'foreB10', 'hind10']
        kind = 'rig'; facing = 1; posture = 'lie' if u > 0.6 else 'stand'
    head_img = HEAD_ONLY[0] if tone in ('back', 'turn') else None
    return dict(img=img, head_img=head_img, anchor=anc, mirror=mirror, Xc=Xc, D=D, shear=shear, parts=parts, head=head, kind=kind,
                facing=facing, posture=posture, tone=tone, state=st)


def lie_back_look(u):
    """Mirrored lying body (facing away from the door) with the unmirrored profile head (facing the door) laid over
    its shoulders: the dog looks back over its shoulder. The head is composited in front of the torso."""
    h, hp = rig.part('head10')
    body, anc, _ = lie_pose(u, 0, 'F', 0)
    # remove the frontal head: rebuild the body without a head
    b2 = lie_body_only(u)
    m, anc2, _ = mirror_img(b2, anc, (0, 0))
    W = m.size[0]
    # the shoulders of the mirrored body: mirrored neck point
    neck_local = lie_neck(u)
    nx, ny = W - 1 - neck_local[0], neck_local[1]
    head_img = rig.affine(h, hp, 8, (nx - 18, ny - 4), out_size=CANVAS)
    out = Image.alpha_composite(m, head_img)
    headpt = rig.fwd((80, 85), hp, 8, (nx - 18, ny - 4))
    return out, anc2, headpt


_neck_cache = {}


def lie_neck(u):
    t, tp = rig.part('torso10'); h, hp = rig.part('head10')
    uh = sm(0.0, 0.6, u); uf = sm(0.35, 1.0, u)
    tor_th = lerp(0, -12, uf) + lerp(0, 9, uh) * (1 - uf)
    T = rig.affine(t, tp, tor_th, (160, 150)); a = np.array(T)[:, :, 3]
    bot = np.nonzero(a.max(1) > 128)[0].max()
    dy = lerp(0, FLOOR - 2 - bot, uf) + lerp(0, 30, uh) * (1 - uf)
    return rig.fwd(hp, tp, tor_th, (160 + OX, 150 + dy + OY))


def lie_body_only(u):
    t, tp = rig.part('torso10')
    fa, fap = rig.part('foreA10'); fb, fbp = rig.part('foreB10'); k, kp = rig.part('hind10')
    uh = sm(0.0, 0.6, u); uf = sm(0.35, 1.0, u)
    tor_th = lerp(0, -12, uf) + lerp(0, 9, uh) * (1 - uf)
    T = rig.affine(t, tp, tor_th, (160, 150)); a = np.array(T)[:, :, 3]
    bot = np.nonzero(a.max(1) > 128)[0].max()
    dy = lerp(0, FLOOR - 2 - bot, uf) + lerp(0, 30, uh) * (1 - uf)
    tdst = (160 + OX, 150 + dy + OY)
    chest = rig.fwd((108, 157), tp, tor_th, tdst); rump = rig.fwd((200, 172), tp, tor_th, tdst)
    F = FLOOR + OY
    L = [(fb, fbp, lerp(0, 62, uf), (lerp(114 + OX, chest[0] + 8, uf), lerp(160 + OY, F - 13, uf)), (1, 1)),
         (t, tp, tor_th, tdst, (1, 1)),
         (k, kp, lerp(0, 84, uh), (lerp(195 + OX, rump[0] + 4, uh), lerp(175 + OY, F - 9, uh)), (1, 1)),
         (fa, fap, lerp(0, 80, uf), (lerp(140 + OX, chest[0] + 2, uf), lerp(163 + OY, F - 9, uf)), (1, 1))]
    return rig.compose(L, CANVAS)
