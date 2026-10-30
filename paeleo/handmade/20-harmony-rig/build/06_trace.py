"""SCION 20 · 06: trace.json from the render's own measurements (build/cache/measure.json: the dog's composite matte
and the head element's matte, read back from the canvas every frame) and the drawings the exposure sheet exposed.
Choice onsets are MEASURED with the rules below; the trace's `state` switches at the measured onsets.
  retreat   first frame after 0.5 s whose matte centroid (in metres, camera undone) is > 0.02 m further out than at rest
  watch     (2.33) first frame after the retreat onset where the head matte's top rises >= 0.04 m above its lowest point in the retreat
  refuse    first frame where the matte narrows by >= 20 % (the body goes end-on) AND the exposed body drawing faces away
  watch     (7.46) first frame after 7 s where the head matte's centroid rises >= 0.05 m above the resting head (the head comes round)
  approach  first frame after 14 s where the matte centroid is >= 0.03 m nearer the door than its 13-14.5 s mean
  lie_down  first frame after 23 s where the matte's height falls >= 12 % below its 23.0-23.6 s mean
  looks in  (26.4, not a checked choice) first frame after 26 s where >= 50 % of the head matte is inside the inner face of the wall"""
import json, os
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.dirname(os.path.dirname(D))
SC = json.load(open(os.path.join(R, 'handmade/score/threshold-score.json')))
XS = json.load(open(os.path.join(D, 'scene/xsheet.json')))
LIB = json.load(open(os.path.join(D, 'scene/library.json')))['elements']
M = json.load(open(os.path.join(D, 'build/cache/measure.json')))
mp = XS['mapping']; X0, K, FL = mp['X0'], mp['K'], mp['FLOOR']
F = XS['frames']; N = len(F)
def world(px, py, view):
    a, b, c, d, e, f = view   # screen = view * base ; invert (no rotation, uniform zoom)
    bx = (px - e) / a; by = (py - f) / d
    return (bx - X0) / K, (FL - by) / K
rows = []
for i in range(N):
    m = M[str(i)]; fr = F[i]; v = m['cam']['view']; dg, hd = m['dog'], m['head']
    xw, yw = world(dg['cx'], dg['cy'], v)
    x0w, y_top = world(dg['x0'], dg['y0'], v); x1w, y_bot = world(dg['x1'], dg['y1'], v)
    hx, hy = world(hd['cx'], hd['cy'], v) if hd.get('n') else (None, None)
    _, htop = world(hd['x0'], hd['y0'], v) if hd.get('n') else (None, None)
    rows.append(dict(i=i, xw=xw, yw=yw, w=x1w - x0w, h=y_top - y_bot, hx=hx, hy=hy, htop=htop, in_room=hd.get('in_room', 0), in_door=dg.get('in_door_frame', 0),
                     sx=dg['cx'], sy=dg['cy']))
def first(cond, start):
    return next(r['i'] for r in rows[start:] if cond(r))
rest_x = sum(r['xw'] for r in rows[0:20]) / 20
on = {}
on['retreat'] = first(lambda r: r['xw'] > rest_x + 0.02, 12)
low = min(rows[on['retreat']:on['retreat'] + 40], key=lambda r: r['htop'])
on['watch1'] = first(lambda r: r['htop'] >= low['htop'] + 0.04, low['i'])
w_rest = sum(r['w'] for r in rows[60:78]) / 18
def facing_away(i):
    fr = F[i]; body = LIB['dog_body'][fr['body']]
    return fr['mirror'] == -1 or body['view'] in ('back', 'q3back')
on['refuse'] = first(lambda r: r['w'] <= 0.8 * w_rest and facing_away(r['i']), 70)
head_rest = sum(rows[k]['hy'] for k in range(160, 168)) / 8
on['watch2'] = first(lambda r: r['hy'] >= head_rest + 0.05, 168)
a_mean = sum(r['xw'] for r in rows[312:348]) / 36
on['approach'] = first(lambda r: r['xw'] <= a_mean - 0.03, 336)
h_mean = sum(r['h'] for r in rows[552:567]) / 15
on['lie_down'] = first(lambda r: r['h'] <= 0.88 * h_mean, 552)
on['looks_in'] = first(lambda r: r['in_room'] >= 0.5 and F[r['i']]['head'] == 'deep', 624)
seq = [(0, 'watch'), (on['retreat'], 'retreat'), (on['watch1'], 'watch'), (on['refuse'], 'refuse'), (on['watch2'], 'watch'), (on['approach'], 'approach'), (on['lie_down'], 'lie_down')]
def state_at(i):
    s = 'watch'
    for k, st in seq:
        if i >= k: s = st
    return s
def facing(fr):
    hv = LIB['dog_head'][fr['head']]['view']; bv = LIB['dog_body'][fr['body']]['view']
    if bv in ('back', 'q3back'): return 'away_turning' if bv == 'q3back' else 'back_to_door'
    if fr['mirror'] == -1 and bv == 'profile': return 'back_to_door' if fr['head_rel'] == 1 else 'back_to_door_head_looking'
    if bv in ('front', 'q3front'): return 'turning_to_door'
    return 'toward_door'
frames = []
for r in rows:
    fr = F[r['i']]; sc = SC['frames'][r['i']]
    frames.append(dict(i=r['i'], t=round(r['i'] / 24, 3), state=state_at(r['i']), x_score=sc['dog']['x'], x_screen=round(r['sx'], 2), y_screen=round(r['sy'], 2),
                       x_world_measured=round(r['xw'], 4), facing=facing(fr), posture=LIB['dog_body'][fr['body']]['posture'],
                       body=fr['body'] + ('.R' if fr['mirror'] == -1 else ''), head=fr['head'], ear=fr['ear'], tail=fr['tail'],
                       head_y_m=None if r['hy'] is None else round(r['hy'], 4), head_in_room=round(r['in_room'], 3), dog_in_door_frame=round(r['in_door'], 3),
                       width_m=round(r['w'], 3), height_m=round(r['h'], 3), cam_zoom=fr['cam_z'], voice=SC['frames'][r['i']]['person']['voice'], door=fr['door']))
score_t = {'retreat': 1.0, 'watch1': 2.333, 'refuse': 3.417, 'watch2': 7.458, 'approach': 14.708, 'lie_down': 23.792, 'looks_in': 26.4}
onsets = {k: dict(frame=v, t=round(v / 24, 3), score_t=score_t[k], dt=round(v / 24 - score_t[k], 3)) for k, v in on.items()}
lev = json.load(open(os.path.join(D, 'build/cache/sound_levels.json')))
json.dump(dict(about='Measured from the render: x_world_measured / x_screen / y_screen are the centroid of the dog\'s composite matte read back from the canvas '
                     '(camera undone for x_world_measured); head_* from the head element\'s matte. facing/posture/body/head are the drawings exposed. '
                     'state switches at the measured onsets (rules in build/06_trace.py).',
               mapping=mp, measured_onsets=onsets, sound_levels_db=lev, frames=frames), open(os.path.join(D, 'trace.json'), 'w'))
for k, v in onsets.items(): print('%-9s measured %6.3f s  score %6.3f  dt %+.3f' % (k, v['t'], v['score_t'], v['dt']))
print('in door frame at end %.2f, head in room max %.2f' % (rows[-1]['in_door'], max(r['in_room'] for r in rows[640:676])))
