"""trace.json from the render's own measurements (cache/meas), plus choice onsets measured from them."""
import json, os, glob
import numpy as np
import perform

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.dirname(HERE)
M = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(HERE, 'cache', 'meas', '*.json')))]
assert len(M) == 768, len(M)
P = perform.dog_poses()
T = np.array([m['t'] for m in M])
xw = np.array([m['x_world_measured'] for m in M])
mz = np.array([m['muzzle_world_x'] for m in M])
top = np.array([m['bbox'][1] for m in M], float)
vel = np.gradient(xw) * 24
# skull top and back line from the deformed mesh (head-bone region without the ears; back = withers and mid-back)
import rig, bbw
V, F, W, HS = rig.load(); nm = [h['name'] for h in HS]
SK = (W[:, nm.index('head')] > 0.5) & (W[:, nm.index('ear_near')] + W[:, nm.index('ear_far')] < 0.05)
BK = (np.abs(V[:, 0] + 0.10) < 0.12) & (V[:, 1] > 0.45)
skull, backy = [], []
for p in P:
    X = bbw.skin(V, W, rig.pose_affines(p, HS))
    skull.append(X[SK, 1].max()); backy.append(X[BK, 1].max())
skull, backy = np.array(skull), np.array(backy)


def first(cond, after, before=None):
    for i, m in enumerate(M):
        if T[i] >= after and (before is None or T[i] < before) and cond(i):
            return float(T[i])
    return None


def dev(arr, t_ref, thr, after, before=None):
    ref = arr[int(round(t_ref * 24))]
    return first(lambda i: abs(arr[i] - ref) > thr, after, before)


on = {
    'retreat (backs away), score 1.000': first(lambda i: vel[i] > 0.05, 0.6, 2.0),
    'watch (head comes up, ears prick), score 2.333': first(lambda i: skull[i] > skull[int(2.0 * 24)] + 0.015, 2.0, 3.0),
    'refuse (head starts to turn away), score 3.417': dev(mz, 3.2, 0.01, 3.2, 4.5),
    'watch (head comes round to the door), score 7.458': dev(mz, 7.1, 0.01, 7.1, 8.0),
    'approach (comes closer), score 14.708': first(lambda i: vel[i] < -0.05, 14.0, 16.0),
    'lie_down (back lowers at the sill), score 23.792': first(lambda i: backy[i] < backy[int(23.3 * 24)] - 0.02, 23.3, 25.0),
    'looks in (muzzle moves into the room), score 26.4': first(lambda i: mz[i] < mz[int(26.3 * 24)] - 0.01, 26.3, 28.0),
}
frames = []
for m, p in zip(M, P):
    y = p['yaw']
    posture = ('turning' if max(y.values()) - min(y.values()) > 0.5 or 0 < y['front'] < 180 else
               'lying' if p['lie'] > 0.5 else 'walking' if perform.FR[m['i']]['dog']['act']['moving'] > 0.5 else
               'crouching' if p['crouch'] > 0.5 else 'standing')
    frames.append({'i': m['i'], 't': m['t'], 'state': p['state'], 'x_score': perform.XS[m['i']], 'x_screen': m['x_screen'],
                   'y_screen': m['y_screen'], 'x_world_measured': m['x_world_measured'], 'facing': m['facing'],
                   'posture': posture, 'muzzle_world_x': m['muzzle_world_x'], 'skull_top_y': round(float(skull[m['i']]), 4),
                   'back_y': round(float(backy[m['i']]), 4),
                   'flipped_triangles': m['flipped_triangles'], 'yaw': m['yaw']})
appr = [f for f in frames if f['state'] == 'approach']
head_low = float(np.mean([skull[f['i']] < backy[f['i']] - 0.05 for f in appr]))
out = {'about': 'SCION 12 lace dog, measured from its own render: x_screen/y_screen = centroid of the rendered dog mask (px); '
                'x_world_measured = that centroid mapped back through the camera into score metres (the camera moves); facing = '
                'direction the rendered muzzle points (1 toward the door, -1 away); state = the score label; onsets measured from '
                'the render below.',
       'onsets_measured': on,
       'approach_skull_more_than_5cm_below_back_share': round(head_low, 3),
       'frames': frames}
json.dump(out, open(os.path.join(FOLDER, 'trace.json'), 'w'), indent=0)
print(json.dumps(on, indent=1), 'head low share', head_low)
