"""SCION-26 · trace.json from what the stage actually rendered (build/cache/measure.json).
x_screen, y_screen: centroid of the dog's body render texture alpha (> 100/255), read back from the GPU each frame (px, 1280x720).
facing: 1 = body toward the door (projected body axis points to screen-left), -1 = away; from the scene graph that placed the sprites.
state: labelled from measured events, not copied from the score:
  retreat   from the first frame the measured centroid moves away from the door (> 0.4 px/frame), until it stops
  refuse    from the first frame the head has swung more than 12 deg off the door (the turn away begins), until
  watch     (after retreat) the first frame the head lifts > 2 px above its low backing-away carriage (it stops to watch);
            (after refuse) the first frame the projected muzzle points back toward the door (head-led look back)
  approach  from the first frame the measured centroid moves toward the door (> 0.4 px/frame) after 14 s
  lie_down  from the first frame the body starts down at the sill (lie > 0.05)
  look_in   (event, not a state) first frame the muzzle turns > 0.02 m deeper (relative to the skull) than when the head lies along the body (turned into the room)"""
import json, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); FOLDER = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(FOLDER, '../../..'))
SC = json.load(open(os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')))
M = json.load(open(os.path.join(HERE, 'cache/measure.json')))
fr = M['scene']; n = len(fr)
xs = [f['m']['x'] for f in fr]
vel = [0.0] * n
for i in range(n):
    a, b = max(0, i - 2), min(n - 1, i + 2)
    vel[i] = (xs[b] - xs[a]) / (b - a)
def first(cond, start=0):
    return next((i for i in range(start, n) if cond(i)), None)
on = {}
on['retreat'] = first(lambda i: vel[i] > 0.4, 12)
h0 = fr[on['retreat'] + 12]['headY']
on['watch1'] = first(lambda i: fr[i]['headY'] < h0 - 2, on['retreat'] + 12)
on['refuse'] = first(lambda i: abs(fr[i]['q']['psiH'] - 168) > 12, 72)
on['watch2'] = first(lambda i: fr[i]['muzzleDx'] < 0, 168)
on['approach'] = first(lambda i: vel[i] < -0.4, 336)
on['lie_down'] = first(lambda i: fr[i]['q']['lie'] > 0.05, 552)
base = fr[620]['muzzleDepth']   # lying, head along the body (which already lies into depth across the sill)
on['look_in'] = first(lambda i: fr[i]['muzzleDepth'] > base + 0.02, 600)
seq = [(0, 'watch'), (on['retreat'], 'retreat'), (on['watch1'], 'watch'), (on['refuse'], 'refuse'), (on['watch2'], 'watch'), (on['approach'], 'approach'), (on['lie_down'], 'lie_down')]
def state(i):
    s = 'watch'
    for k, v in seq:
        if i >= k: s = v
    return s
frames = []
for i, f in enumerate(fr):
    sf = SC['frames'][i]; q = f['q']; st = state(i)
    facing = 1 if math.cos(math.radians(q['psi'])) < 0 else -1
    if st == 'lie_down' or q['lie'] > 0.6: posture = 'lying'
    elif abs(vel[i]) > 0.4: posture = 'backing away' if (vel[i] > 0 and facing == 1) else 'walking'
    else: posture = 'standing'
    frames.append(dict(i=i, t=round(i / 24, 3), state=st, x_score=sf['dog']['x'], x_screen=round(f['m']['x'], 2), y_screen=round(f['m']['y'], 2),
                       facing=facing, posture=posture, head_toward_door=f['muzzleDx'] < 0, muzzle_into_room=f['muzzleDepth'] > 0,
                       head_y=round(f['headY'], 1), back_y=round(f['backY'], 1), bbox=f['m']['bbox'], body_yaw_deg=round(q['psi'], 1),
                       head_yaw_deg=round(q['psiH'], 1), draws=f['draws']))
score_t = {'retreat': 1.0, 'watch1': 2.333, 'refuse': 3.417, 'watch2': 7.458, 'approach': 14.708, 'lie_down': 23.792, 'look_in': 26.4}
onsets = {k: dict(frame=v, t=round(v / 24, 3), score_t=score_t[k], dt=round(v / 24 - score_t[k], 3)) for k, v in on.items()}
head_low = [fr[i]['headY'] > fr[i]['backY'] for i in range(on['approach'], on['lie_down'])]
out = dict(about=__doc__, mapping=dict(formula='x_screen ~ 330 + 200 * x (body centre; in the last 2 s the body creeps 0.24 m onto the sill as it lies)', OX=330, S=200),
           onsets=onsets, approach_head_below_back_share=round(sum(head_low) / len(head_low), 3), frames=frames)
json.dump(out, open(os.path.join(FOLDER, 'trace.json'), 'w'), indent=0)
print(json.dumps(onsets, indent=0)); print('head below back during approach:', out['approach_head_below_back_share'])
