"""POSE EXTRACTOR + ACTION EDITOR.
The recorded performance here is the PAELEO machine's decision trace (score/threshold-score.json): per frame the dog's
state, position and acting intentions. This turns each frame into a typed pose vector in the same coordinates as the
illustration bank, and records every action edit (a re-timing of the performance inside the score's choice windows).
python3 build/poses.py -> build/cache/poses.json"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
SCORE = json.load(open(os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')))
OUT = os.path.join(HERE, 'cache', 'poses.json')
RATE = 11.42           # gait radians per metre (the score's walk phase follows distance at this rate)

EDITS = [
    {'id': 'E1', 'what': 'refusal turn leads', 't': [3.417, 3.9],
     'why': 'the score turns the body 3.9-4.6 s; the brief needs the back clearly shown by about 3.9 s. The turn starts at the choice (3.417) and is complete by 3.88; the lie-down keeps its score timing.'},
    {'id': 'E2', 'what': 'head comes round first', 't': [7.458, 8.5],
     'why': 'at 7.458 the score turns the dog back to look but its body turn only starts at 7.9; the head comes round over the shoulder at the choice frame and the body follows on the score.'},
    {'id': 'E3', 'what': 'listening', 't': 'soft voice onsets',
     'why': 'attention: for 1.1 s after the soft voice starts, while the dog stands watching, it lifts its nose to listen (heard < 1.1 s in the score).'},
    {'id': 'E4', 'what': 'the person walks, then sits', 't': [5.4, 6.3],
     'why': 'the score starts sitting while the person is still moving to the place beside the door; the person steps aside first and sits once there.'},
]


def smooth(a):
    a = max(0.0, min(1.0, a))
    return a * a * (3 - 2 * a)


def main():
    F = SCORE['frames']
    out = []
    s = 0.0
    prev_x = F[0]['dog']['x']
    soft_on = [t for t, ev in SCORE['timeline'] if ev.get('voice') == 'soft']
    for f in F:
        t, dg, a, pr = f['t'], f['dog'], f['dog']['act'], f['person']
        x = dg['x']
        s += abs(x - prev_x); prev_x = x
        yaw = 90.0 * (1 - a['turn'])
        over = 0.0
        if 3.417 <= t < 7.458:                       # E1
            yaw = 180.0 * smooth((t - 3.417) / (3.88 - 3.417))
        if 7.458 <= t < 8.6:                          # E2: the head leads, the body keeps the score
            over = 1.0 if yaw > 60 else 0.0
        listen = 0.0
        if dg['state'] == 'watch' and a['lie'] < .2 and yaw < 30:
            for ts in soft_on:
                if 0 <= t - ts < 1.1:
                    listen = 1.0
        v = dg['v']
        moving = a['moving'] if abs(v) > .02 or a['moving'] > .5 else 0.0
        back = 1.0 if (v > .02 and dg['state'] in ('retreat', 'watch') and moving > .3) else 0.0
        wag = a['wag'] * math.sin(2 * math.pi * 2.1 * t)
        p = dict(yaw=round(yaw, 2), lie=a['lie'], crouch=a['crouch'], head=a['head'], look=a['look'], rest=a['rest'],
                 ear=max(0, min(1, a['ear'])), tail=a['tail'], moving=round(moving, 3), back=back, phase=round((s * RATE) % (2 * math.pi), 4),
                 wag=round(wag, 3), over=over, listen=listen)
        pp = dict(sit=pr['sit'], reach=pr['reach'], low=pr['low'], mouth=pr['mouth'], x=pr['x'])
        out.append({'i': f['i'], 't': t, 'state': dg['state'], 'x': x, 's': round(s, 5), 'dog': p, 'person': pp, 'door': f['door'],
                    'voice': pr['voice'], 'hand': pr['hand']})
    # person walking (steps aside): from the change of the person's x
    for k in range(len(out)):
        x0 = out[max(k - 1, 0)]['person']['x']; x1 = out[min(k + 1, len(out) - 1)]['person']['x']
        out[k]['person']['walk'] = 1.0 if abs(x1 - x0) > 1e-3 else 0.0
        if out[k]['person']['walk']:
            out[k]['person']['sit'] = 0.0       # E4: the person walks aside first, then sits (the score does both at once)
    json.dump({'about': 'Pose vectors per score frame (dog and person), after the action edits listed.', 'rate_rad_per_m': RATE,
               'edits': EDITS, 'frames': out}, open(OUT, 'w'))
    print('poses', len(out), '->', OUT)


if __name__ == '__main__':
    main()
