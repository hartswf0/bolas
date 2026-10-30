"""SCION 19 trace: what the dog did, per scene frame, measured from the render (build/cache/frames/measures.json).
x_screen/y_screen: centroid of the dog's pixels in a mask render of the same frame; x_world_measured: that centroid taken
back through the frame's camera (U = x/s + L) and my mapping (x = U + 0.42). facing, layer, heights: from the rig geometry
that was drawn. state: the performed state (the controller follows the score); measured onsets are found separately from
render evidence and written to the summary."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..'))
score = json.load(open(os.path.join(ROOT, '..', 'score', 'threshold-score.json')))
M = json.load(open(os.path.join(HERE, 'cache', 'frames', 'measures.json')))
M.sort(key=lambda m: m['i'])
OFF = 0.42
fr = []
for m in M:
    i = m['i']; sf = score['frames'][i]; c = m['cam']; px = m['px']; r = m['rig']
    U = px['cx'] / c['s'] + c['L'] if px['cx'] is not None else None
    lie = r['lie']
    posture = 'lying' if lie > 0.6 else ('rising' if lie > 0.1 else ('crouched' if sf['dog']['act']['crouch'] > 0.5 else 'standing'))
    fr.append({'i': i, 't': round(i / 24, 3), 'state': sf['dog']['state'], 'x_score': sf['dog']['x'],
               'x_screen': round(px['cx'], 2), 'y_screen': round(px['cy'], 2), 'x_world_measured': round(U + OFF, 4),
               'facing': r['facing'], 'head_facing': r['headFacing'], 'head_layer': r['layer'], 'posture': posture,
               'back_y_m': round(r['backY'], 3), 'skull_top_y_m': round(r['skullTopY'], 3), 'head_below_back': r['skullTopY'] < r['backY'],
               'inside_door_share': round(px['insideShare'], 3), 'dog_px': px['n'], 'bbox': px['bbox'],
               'nose_U_m': round(r['noseW'][0], 3), 'nose_W_m': round(r['noseW'][2], 3), 'tail_tip_U_m': round(r['tailTipW'][0], 3),
               'corrections': {k: round(v, 3) for k, v in r['corrections'].items()}})
def first(cond, t0):
    for k, f in enumerate(fr):
        if f['t'] >= t0 and cond(k, f): return f['t']
    return None
base_back = fr[20]['back_y_m']
on = {
  'retreat (1.00)': first(lambda k, f: k > 0 and (f['x_world_measured'] - fr[k - 1]['x_world_measured'] > 0.0015 or f['back_y_m'] < base_back - 0.01), 0.6),
  'watch (2.33): stops crouching, rises': first(lambda k, f: k > 2 and f['back_y_m'] > fr[k - 3]['back_y_m'] + 0.004, 2.1),
  'refuse (3.42): head view leaves profile': first(lambda k, f: f['head_layer'] != 'profile', 3.0),
  'refuse: body facing flips (back turned)': first(lambda k, f: f['facing'] == -1, 3.0),
  'watch (7.46): head view leaves profile (head leads)': first(lambda k, f: f['head_layer'] != 'profile', 7.0),
  'watch: muzzle toward the door (head facing +1)': first(lambda k, f: f['head_facing'] == 1, 7.0),
  'watch: body facing flips back': first(lambda k, f: f['facing'] == 1, 7.0),
  'approach (14.71): measured x decreases': first(lambda k, f: k > 0 and fr[k - 1]['x_world_measured'] - f['x_world_measured'] > 0.002, 14.3),
  'approach: head below the back': first(lambda k, f: f['head_below_back'], 14.3),
  'lie_down (23.79): back height drops': first(lambda k, f: f['back_y_m'] < 0.56, 23.3),
  'look in (26.4): head view to three-quarter back': first(lambda k, f: f['head_layer'] == 'three_quarter_back', 26.0),
}
appr = [f for f in fr if f['state'] == 'approach']
summary = {
  'measured_onsets_s': on,
  'body_down_when_muzzle_reached_door': next((f['posture'] for f in fr if f['t'] >= 7.0 and f['head_facing'] == 1), None),
  'approach_frames_head_below_back': f"{sum(f['head_below_back'] for f in appr)}/{len(appr)}",
  'refuse_frames_back_turned': f"{sum(f['facing'] == -1 for f in fr if f['state'] == 'refuse')}/{sum(f['state'] == 'refuse' for f in fr)}",
  'frames_with_dog_pixels': f"{sum(f['dog_px'] > 2000 for f in fr)}/{len(fr)}", 'min_dog_px': min(f['dog_px'] for f in fr),
  'end': {k: fr[-1][k] for k in ('posture', 'inside_door_share', 'nose_U_m', 'tail_tip_U_m', 'x_world_measured')},
  'look_in_frames_three_quarter_back': sum(f['head_layer'] == 'three_quarter_back' for f in fr if f['t'] > 26),
  'look_in_nose_in_room': all(f['nose_U_m'] < -0.25 for f in fr if f['head_layer'] == 'three_quarter_back' and f['t'] > 26),
}
json.dump({'about': 'SCION 19 dog trace, measured from the render (pixel centroid of a mask pass; rig geometry for facing/heights)', 'mapping': 'U = x_score - 0.42 (U: metres along my porch, outer wall face at 0); x_world_measured = centroid U + 0.42', 'summary': summary, 'frames': fr}, open(os.path.join(ROOT, 'trace.json'), 'w'))
print(json.dumps(summary, indent=1))
