"""SCION 11 · the recorded performance graph.

Barnes's puppeteer moves paper under a camera and the system records the tracked transforms.
Here no hand moves anything: the performance is *derived from the score* (the dog's decision
trace), frame by frame, and written out as an editable performance clip (data/performance.json).
Editing one channel of that clip and re-rendering changes only that channel; nothing needs to be
"re-recorded".  Channels per frame:

  dog.x       metres along the porch (= the score's x, unchanged)
  dog.k       position on the turn axis 0 L (faces the door) .. 1 F' .. 2 F .. 3 R (back turned)
  dog.pose    crouch, head, tail, wag, lie, rest, look, bob, feet{f1,f2,h1,h2: [dx, lift]} (canon px)
  person      cx (screen px), sit, reach, low, lean, step
  door        theta (deg, inward swing), light (0..1)
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
SCORE = json.load(open(os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')))
FR = SCORE['frames']
N = len(FR)
FPS = 24
STRIDE = 0.46           # metres per full gait cycle
STANCE = 0.65
OFFS = {'h2': 0.0, 'f2': 0.25, 'h1': 0.5, 'f1': 0.75}   # four-beat walk (near hind, near fore, far hind, far fore)


def lerp(a, b, t):
    return a + (b - a) * t


def sm(u):
    u = np.clip(u, 0, 1)
    return u * u * (3 - 2 * u)


def ease_out(u):
    u = np.clip(u, 0, 1)
    return 1 - (1 - u) ** 2


def turn_axis(t):
    """turn to the back at 3.42 (L -> F' -> F -> R), turn back to the door at 7.46 (R -> F -> F' -> L)"""
    if t < 3.417:
        return 0.0
    if t < 7.458:
        return 3.0 * ease_out((t - 3.417) / 0.44)
    # repair rounds 1-2: the head comes round first (from 7.46, the face to the camera by 7.59) while it is
    # still getting up (7.46-7.75, 7 frames); standing, it finishes the turn by 7.98
    return 3.0 - 3.0 * sm((t - 7.80) / 0.45)


def feet(x, moving, pxm_over_scale):
    """planted feet: during stance a foot's offset from the body is exactly minus the body's travel"""
    s = -x  # forward travel (the dog faces the door, i.e. -x)
    out = {}
    for n, o in OFFS.items():
        u = (s / STRIDE + o) % 1.0
        if u < STANCE:
            off = STRIDE * (u - STANCE / 2)
            lift = 0.0
        else:
            v = (u - STANCE) / (1 - STANCE)
            off = STRIDE * (STANCE / 2 - STANCE * sm(v))
            lift = np.sin(np.pi * v) * 0.075
        out[n] = [off * pxm_over_scale, lift * pxm_over_scale * min(1, moving * 1.5)]
    return out


def build():
    from stage import PXM, feet_y, dog_scale, sx
    perf = []
    for f in FR:
        i, t = f['i'], f['t']
        d, a, p = f['dog'], f['dog']['act'], f['person']
        x = d['x']
        k = turn_axis(t)
        y = feet_y(x)
        sc = dog_scale(y)
        head = a['head']
        crouch, tail, lie, rest, look = a['crouch'], a['tail'], a['lie'], a['rest'], a['look']
        # approach: the head is carried below the line of the back the whole way (the brief's lesson)
        if d['state'] == 'approach' or (14.5 < t < 23.9):
            head = lerp(head, min(head, 0.24), sm((t - 14.58) / 0.21)) if t > 14.58 else head  # 5 frames, no snap
        # refusal: lying with its back turned, the chin goes down (score rest), head low
        if 3.417 <= t < 7.458:
            head = min(head, 0.3)
        # turning back to look (7.46): the head comes up with the turn, not after it
        if 7.458 <= t < 8.2:
            # still lying, it swings its head up and back over its shoulder toward the door (7.46-7.60),
            # then the head comes forward again as the body turns
            # round 3: lying, the head is cut round to face the door (low, level) from 7.46 to 7.80
            head = 0.5 + 0.4 * sm((t - 7.80) / 0.3)
        # lying at the sill: looks in (score look), then settles chin down (score rest)
        if 7.458 <= t < 8.0:
            lie = min(1.0 if t < 7.78 else lie, 1 - sm((t - 7.78) / 0.30)); rest = min(rest, lie); crouch = min(crouch, .3)
        mov = a['moving']
        ft = feet(x, mov, PXM / sc) if lie < 0.5 else {}
        bob = -2.2 * abs(np.sin(2 * np.pi * (-x) / STRIDE * 2)) * mov if lie < .2 else 0.0
        lookback = 1 if 7.458 <= t < 7.92 else 0
        if lookback:
            rest = 0.0
        pose = dict(lookback=lookback, crouch=round(crouch, 4), head=round(float(head), 4), tail=round(tail, 4), wag=round(a['wag'], 4),
                    lie=round(lie, 4), rest=round(rest, 4), look=round(a['look'], 4), bob=round(float(bob), 3),
                    feet={kk: [round(v[0], 2), round(v[1], 2)] for kk, v in ft.items()})
        # person: stands in the doorway, steps aside along the wall (4.7-5.5), sits (score sit)
        u = sm((t - 4.7) / 0.8)
        cx = 300 + (118 - 300) * u
        step = (t - 4.7) / 0.8 if 4.7 <= t <= 5.5 else 0
        per = dict(cx=round(cx, 2), sit=round(p['sit'], 4), reach=round(p['reach'], 4), low=round(p['low'], 4),
                   lean=round(p['mouth'] * (1.0 if p['voice'] == 'call' else 0.4), 4), step=round(step, 4))
        # door: ajar until 6.2, then swings in over 0.9 s and the room's light comes up
        uo = sm((t - 6.2) / 0.9)
        door = dict(theta=round(24 + (78 - 24) * uo, 3), light=round(0.28 + 0.72 * uo, 4))
        perf.append(dict(i=i, t=t, dog=dict(x=x, sx=round(sx(x), 2), y=round(float(y), 2), scale=round(float(sc), 4),
                                            k=round(k, 4), pose=pose), person=per, door=door,
                         voice=p['voice'], prompt=f['prompt']))
    return perf


if __name__ == '__main__':
    perf = build()
    os.makedirs(os.path.join(HERE, '..', 'data'), exist_ok=True)
    json.dump({'about': __doc__.strip().splitlines()[0], 'fps': FPS, 'frames': perf},
              open(os.path.join(HERE, '..', 'data', 'performance.json'), 'w'), separators=(',', ':'))
    print('performance frames', len(perf))
