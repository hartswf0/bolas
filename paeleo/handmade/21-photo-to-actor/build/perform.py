"""Retargeting operator + facial performer: the score's per-frame decision trace -> the actor's controls, frame by frame.

The score says what the dog intends (state, x, act.turn/lie/crouch/ear/tail/wag/head/rest/look). This file decides how the
photographic actor carries it out: which angle artwork is on screen (sprite replacement), where each paw is planted
(feet move with distance travelled, so nothing slides), and the expression controls (ears, brow, mouth).
Output: performance.json (one record per scene frame; render.py draws exactly this).
"""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); FOLDER = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(FOLDER, '..', '..', '..'))
sys.path.insert(0, HERE)
import spec

SCORE = json.load(open(os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')))
FR = SCORE['frames']
N = len(FR)
FPS = 24
TPL_PER_M = 150.0           # template px per metre (screen: 180 px per metre)
STRIDE = 82.0               # template px per gait cycle (~0.55 m, the score's walk_phase rate)
BETA = 0.65                 # stance fraction
GAIT = {'hind_near': 0.0, 'fore_near': 0.25, 'hind_far': 0.5, 'fore_far': 0.75}
G = spec.GROUND_Y - 1


def interp(table, v):
    xs = [a for a, b in table]; ys = [b for a, b in table]
    return float(np.interp(v, xs, ys))


NECK = [(0.15, -205), (0.45, -196), (0.6, -150), (0.9, -121), (1.25, -100)]
MUZ_LOW = [(0.15, 118), (0.45, 132), (0.6, 150)]
MUZ_PROF = [(0.6, -178), (0.9, -155), (1.25, -140)]

# ----- the sprite-replacement schedule for the two turns (frame -> view). Chosen by hand, in frames, from the score's times.
TURN1 = {82: ('rig', 1, 'tq'), 83: ('tq', 1, None), 84: ('front', 1, None), 85: ('front', 1, None)}   # no mirrored repeat (round 1: L/R flip)
                                                                           # away from the call: through the front, 3.42-3.58 s
HEADLEAD = {179: 'front'}                                       # 7.458 s: the head comes round first
TURN2 = {192: ('back', 1, None), 193: ('back', 1, None), 194: ('back', 1, None), 195: ('back', 1, None)}   # body follows, through the back
FACING_R = range(86, 192)                                                  # body faces away (screen right) 3.54 .. 7.96 s


def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)


def run():
    perf = []
    cum = 0.0
    prev_x = FR[0]['dog']['x']
    lie_reset = False
    last_m = -1
    for f in FR:
        i, t = f['i'], f['t']; d = f['dog']; a = d['act']
        x = d['x']; dx = x - prev_x; prev_x = x
        cum += abs(dx) * TPL_PER_M
        facing = -1 if i in FACING_R else 1
        lie, crouch, head, rest, look = a['lie'], a['crouch'], a['head'], a['rest'], a['look']
        if d['state'] == 'approach':
            # coming, head low: the head drops with the decision (over 4 frames) and stays below the back line
            head = min(head, 0.9 + (0.42 - 0.9) * min(1.0, (i - 353) / 4.0))
        if lie > 0.6: cum = 0.0; lie_reset = True
        # ---- paws: planted while in stance, so the photographed feet carry the travel
        if abs(dx) > 1e-5: last_m = (1 if dx > 0 else -1) * facing
        feet = {}
        for ln, Lg in spec.LEGS.items():
            p = (cum / STRIDE + GAIT[ln]) % 1.0
            if p < BETA:
                off = (0.5 - p / BETA) * BETA * STRIDE; lift = 0
            else:
                s = (p - BETA) / (1 - BETA); off = (-0.5 + s) * BETA * STRIDE; lift = 9 * math.sin(math.pi * s)
            # stance starts with the paw planted ahead in the direction of travel (template x), ends behind it
            off *= last_m
            lift *= min(1.0, a['moving'] * 1.5)
            rest_x = Lg['pts'][2][0]
            stand = (rest_x + off, G - lift)
            lx = Lg['pts'][0][0] + (-50 if ln.startswith('fore') else -16)
            lieT = (lx, G)
            e = ease(lie)
            feet[ln] = (stand[0] + (lieT[0] - stand[0]) * e, stand[1] + (lieT[1] - stand[1]) * e)
        # ---- head: sprite by pitch; rest = chin on the paws; look = back of the head into the doorway
        sprite_h = None
        view, head_view, head_flip = 'rig', ('profile' if head >= 0.6 else 'low'), False
        neck = interp(NECK, head)
        muz = interp(MUZ_PROF, head) if head >= 0.6 else interp(MUZ_LOW, head)
        if rest > 0.05:
            r = ease(rest)
            neck = neck + (-186 - neck) * r
            if rest > 0.5:
                head_view = 'profile'; muz = -178 + 0 * r
            else:
                muz = muz + ((178 if head_view == 'low' else -178) - muz) * r
        head_sx, head_off, head_scale = 1.0, (0, 0), 1.0
        head_tone = 1.0
        close = 634 <= i <= 677        # round 3: a closer shot on the sill for the look-in (26.42-28.21 s)
        if lie > 0.5 and head_view == 'low':
            # round 3: on the lying body the lowered (f046) head read as a pale hollow front face; use the profile, level
            head_view = 'profile'; muz = -178; neck = min(neck, -186) if rest < 0.5 else neck
        if look > 0.08:
            # round 3: the head turns INTO the lit hall. It stays profile until the cut (26.42), then turns on screen:
            # profile -> foreshortened profile -> the back of the head (both ears, skull outline, no muzzle) facing the viewer.
            neck = -186; muz = -178
            if look < 0.3 or i < 634:
                head_view = 'profile'
            elif look < 0.6:
                head_view = 'profile'; head_sx = 0.5; head_tone = 0.8
            else:
                head_view = 'back'; head_tone = 0.85; head_off = (-2, 6)
        # ---- the two turns and the head leading
        if i in TURN1:
            v, fc, hv = TURN1[i]
            view = v; facing = fc
            if hv: head_view = hv
        if i in TURN2:
            view = TURN2[i][0]; facing = TURN2[i][1]; sprite_h = 124   # matched to the neighbours' height (round 1)
        if i in HEADLEAD:
            head_view = HEADLEAD[i]; head_flip = True
        elif 180 <= i < 192:
            # round 3: the three-quarter photograph (f037: eye and muzzle legible) turned back toward the door
            head_flip = True; head_view = 'tq'
            neck = -112 if lie < 0.5 else -128; head_off = (6, 0)
        # ---- expression controls
        ear = a['ear']
        brow = min(1.0, crouch * 1.6) - 0.3 * max(0, a['wag'] - 0.3)
        relaxed = (d['state'] in ('watch', 'lie_down')) and crouch < 0.2 and f['door'] == 'open'
        mouth = 0.0
        if relaxed and look < 0.08:
            mouth = 0.28 + 0.18 * math.sin(2 * math.pi * 1.6 * t)          # soft pant
        if d['state'] == 'lie_down' and rest > 0.5: mouth = 0.0
        tail_ang = -38 + 88 * (a['tail'] / 1.35) + a['wag'] * 22 * math.sin(2 * math.pi * 2.2 * t)
        bob = 1.3 * math.sin(4 * math.pi * (cum / STRIDE)) * a['moving'] if lie < 0.1 else 0.0
        breath = 0.6 * math.sin(2 * math.pi * 0.45 * t)
        perf.append({'i': i, 't': t, 'x': x, 'state_score': d['state'], 'facing': facing, 'view': view,
                     'pose': {'view': view, 'lie': lie, 'crouch': crouch, 'feet': feet, 'tail_ang': tail_ang, 'neck_ang': neck,
                              'head_view': head_view, 'head_flip': head_flip, 'muzzle_ang': muz, 'ear': ear, 'brow': brow,
                              'mouth': mouth, 'bob': bob + breath * (1 if lie > 0.5 else 0.3), 'head_sx': head_sx,
                              'head_off': head_off, 'head_scale': head_scale, 'head_tone': head_tone, 'close': close, 'sprite_h': sprite_h or (112 - 14 * crouch)},
                     'person': f['person'], 'door': f['door']})
    return perf


if __name__ == '__main__':
    perf = run()
    json.dump(perf, open(os.path.join(FOLDER, 'build', 'cache', 'performance.json'), 'w'))
    print('frames', len(perf))
