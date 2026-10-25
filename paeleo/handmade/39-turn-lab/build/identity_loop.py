"""Identity-continuity loop and reviewer frame index (SCION 39 deliverables), from trace.json.
Numerical invariants (measured on the id-mask render):
  N1 body anchor stationary across substitutions: |Δ x_screen| at every frame where the body drawing changes, px
  N2 no scale pop: dog pixel area and bbox height ratio between consecutive frames at every swap
  N3 protected identity features visible every frame: collar ring and saddle pixels > 0
Writes proof/identity_loop.json and proof/reviewer_frame_index.json. The artistic test (does every frame read as this dog)
is not here: that is judged by viewing."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); FOLDER = os.path.dirname(HERE)
fr = json.load(open(os.path.join(FOLDER, 'trace.json')))['frames']
swaps = []
for a, b in zip(fr, fr[1:]):
    if a['body_view'] != b['body_view'] or a['head_view'] != b['head_view']:
        ha = a['bbox'][3] - a['bbox'][1]; hb = b['bbox'][3] - b['bbox'][1]
        swaps.append({'i': b['i'], 't': b['t'], 'film_t': round(b['t'] + 3, 3), 'body': [a['body_view'], b['body_view']], 'head': [a['head_view'], b['head_view']],
                      'dx_body_px': round(b['x_screen'] - a['x_screen'], 2), 'area_ratio': round(b['area_px'] / max(1, a['area_px']), 3),
                      'height_ratio': round(hb / max(1, ha), 3)})
body_swaps = [s for s in swaps if s['body'][0] != s['body'][1]]
res = {
    'N1_anchor_max_dx_px_at_body_swaps': max(abs(s['dx_body_px']) for s in body_swaps),
    'N2_area_ratio_range_at_swaps': [min(s['area_ratio'] for s in swaps), max(s['area_ratio'] for s in swaps)],
    'N2_height_ratio_range_at_swaps': [min(s['height_ratio'] for s in swaps), max(s['height_ratio'] for s in swaps)],
    'N3_frames_without_collar': [f['i'] for f in fr if f['collar_px'] <= 0],
    'N3_frames_without_saddle': [f['i'] for f in fr if f['saddle_px'] <= 0],
    'swaps': swaps,
}
json.dump(res, open(os.path.join(FOLDER, 'proof/identity_loop.json'), 'w'), indent=1)
idx = {'about': 'Frames the critic should look at first (scene frame i, scene t, film t = scene t + 3 s; film frame = i + 72).',
       'events': [
           {'what': 'call: backs away, still facing the person', 'scene_t': [1.0, 2.33]},
           {'what': 'refusal turn: head leads (H0→H45→H135→H180), body V0→V45→V90→V135; back shown from 3.66', 'scene_t': [3.42, 3.9]},
           {'what': 'lies down with its back turned', 'scene_t': [4.2, 5.0]},
           {'what': 'door opens: ear flick, does not turn', 'scene_t': [6.2, 6.7]},
           {'what': 'turns back to look: head first (H180→H135→H90→H45→H0 by 7.64), then rises, then body V135→V90→V45→V0', 'scene_t': [7.46, 8.4]},
           {'what': 'approach, head below the back line, feet planted', 'scene_t': [14.71, 23.0]},
           {'what': 'turns into the doorway (V0→V45) and lies down across the sill', 'scene_t': [22.9, 24.6]},
           {'what': 'come in: looks in through the door (head H0→H45→H90), then back down, stays', 'scene_t': [26.4, 29.2]}],
       'substitution_frames': [{'i': s['i'], 'film_frame': s['i'] + 72, 'body': s['body'], 'head': s['head']} for s in swaps]}
json.dump(idx, open(os.path.join(FOLDER, 'proof/reviewer_frame_index.json'), 'w'), indent=1)
print({k: v for k, v in res.items() if k != 'swaps'}, len(swaps), 'swaps')
