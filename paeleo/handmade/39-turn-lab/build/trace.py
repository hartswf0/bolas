"""Build trace.json from the render's own id-mask measurements (build/cache/measure.json) and the plan.
python3 build/trace.py
  x_screen, y_screen  centroid of the dog's torso+saddle pixels (1280×720 px), measured in the mask pass
  x_score             x_screen mapped back to porch metres: (x_screen − 290) / 225 + 0.39 (the film's fixed mapping, static camera)
  facing              measured: +1 when the head pixels sit on the door side of the torso (left), −1 on the far side, 0 within ±8 px
  posture             measured: torso top above the dog's ground line, metres: ≥0.545 stand, 0.47–0.545 low, <0.47 lying
  state               the orientation controller's state (the choice it is performing; it follows the score's decisions)
  body_view, head_view the drawings on screen in that frame; collar_px, saddle_px, tail_px identity-feature pixel counts"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); FOLDER = os.path.dirname(HERE)
S, OX, X0 = 225, 290, 0.39
m = json.load(open(os.path.join(HERE, 'cache/measure.json')))
plan = json.load(open(os.path.join(HERE, 'cache/plan.json')))
fr = []
for q, p in zip(m, plan):
    assert q['i'] == p['i']
    dx = (q['head_cx'] - q['body_cx']) if q['head_cx'] is not None else 0
    facing = 1 if dx < -8 else (-1 if dx > 8 else 0)
    h = (q['ground_y'] - q['torso_top']) / S
    posture = 'stand' if h >= 0.545 else ('low' if h >= 0.47 else 'lying')
    fr.append({'i': p['i'], 't': round(p['t'], 4), 'state': p['dog']['state'],
               'x_score': round((q['body_cx'] - OX) / S + X0, 4), 'x_screen': round(q['body_cx'], 2), 'y_screen': round(q['body_cy'], 2),
               'facing': facing, 'posture': posture, 'torso_top_m': round(h, 3), 'head_dx_px': round(dx, 1),
               'body_view': q['body_view'], 'head_view': q['head_view'],
               'collar_px': q['counts']['collar'], 'saddle_px': q['counts']['saddle'], 'tail_px': q['counts']['tail'], 'area_px': q['area'],
               'bbox': [round(v) for v in q['bbox']]})
doc = {'about': 'SCION 39 Turn Lab: what the dog did, per scene frame, measured from an id-mask pass of its own render (see build/trace.py).',
       'mapping': {'x_score': '(x_screen - 290) / 225 + 0.39', 'camera': 'static'}, 'frames': fr}
json.dump(doc, open(os.path.join(FOLDER, 'trace.json'), 'w'))
print('trace', len(fr), 'frames; end x', fr[-1]['x_score'], 'min x', min(f['x_score'] for f in fr))
