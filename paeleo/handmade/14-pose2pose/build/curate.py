"""REPRESENTATIVE-POSE CURATOR: cluster the performance's pose vectors, and check that every cluster, and every rare
critical gesture, has a drawing in the bank that represents it. A cluster whose nearest drawing is far away is
unexplained error: it asks for new artwork instead of a forced substitution.
python3 build/curate.py -> proof/clusters.json"""
import json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from solve import dist_dog, BANK, POSES

HERE = os.path.dirname(os.path.abspath(__file__))
FOLD = os.path.abspath(os.path.join(HERE, '..'))
F = POSES['frames']


def vec(p):
    mv = p['moving']
    return np.array([p['yaw'] / 90.0, p['lie'] * 1.5, p['crouch'], p['head'], p['look'] * 1.5, p['rest'], mv * 1.5, p['back'] * mv,
                     p['over'] * 1.5, p['listen'], math.cos(p['phase']) * mv, math.sin(p['phase']) * mv])


Xv = np.array([vec(f['dog']) for f in F])
K = 14
r = np.random.default_rng(14)
best = None
for trial in range(12):
    C = Xv[r.choice(len(Xv), K, replace=False)]
    for it in range(60):
        lab = np.argmin(((Xv[:, None] - C[None]) ** 2).sum(-1), 1)
        C2 = np.array([Xv[lab == k].mean(0) if (lab == k).any() else C[k] for k in range(K)])
        if np.allclose(C2, C): break
        C = C2
    inertia = ((Xv - C[lab]) ** 2).sum()
    if best is None or inertia < best[0]: best = (inertia, C, lab)
_, C, lab = best
dog_ids = [k for k, v in BANK['drawings'].items() if v['meta'].get('group') != 'person']
clusters = []
for k in range(K):
    idx = np.where(lab == k)[0]
    if not len(idx): continue
    # medoid frame of the cluster, and the drawing nearest to it
    med = idx[np.argmin(((Xv[idx] - C[k]) ** 2).sum(1))]
    d = sorted((dist_dog(F[med]['dog'], BANK['drawings'][j]['pose']), j) for j in dog_ids)
    spans = []
    for i in idx:
        if spans and i == spans[-1][1] + 1: spans[-1][1] = i
        else: spans.append([i, i])
    clusters.append({'cluster': int(k), 'frames': int(len(idx)), 'medoid_t': F[med]['t'], 'state': F[med]['state'],
                     'spans_s': [[round(a / 24, 2), round(b / 24, 2)] for a, b in spans][:6],
                     'nearest_drawing': d[0][1], 'distance': round(d[0][0], 3), 'second': d[1][1],
                     'explained': d[0][0] < 1.0})
clusters.sort(key=lambda c: c['medoid_t'])
# rare gestures: frames the median clusters would never show, each must have its own drawing
rare = []
for name, key in (('head comes round to the door (7.46 s)', 'over'), ('listens to the soft voice', 'listen'), ('looks in through the door (26.4 s)', 'look')):
    fr = [f for f in F if f['dog'][key] > .5]
    if not fr: continue
    f = fr[len(fr) // 2]
    d = min((dist_dog(f['dog'], BANK['drawings'][j]['pose']), j) for j in dog_ids)
    rare.append({'gesture': name, 'frames': len(fr), 'share_of_film': round(len(fr) / len(F), 3), 'drawing': d[1], 'distance': round(d[0], 3)})
out = {'about': 'k-means (k=%d) over the per-frame pose vectors of the score performance; each cluster checked against the bank.' % K,
       'clusters': clusters, 'rare_gestures': rare,
       'unexplained': [c for c in clusters if not c['explained']]}
json.dump(out, open(os.path.join(FOLD, 'proof', 'clusters.json'), 'w'), indent=1)
for c in clusters: print(c['medoid_t'], c['state'], c['frames'], c['nearest_drawing'], c['distance'])
print(rare)
