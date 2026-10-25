"""proof/feet.json: how far each stance foot moves on screen per frame while it is planted (from the solved pose the render
draws; structurally verified, not tracked from pixels)."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import dogpose as D, render as R
S = R.FR; out = []; prev = {}
for i in range(len(S)):
    kind, a, hf, p = R.dog_plan(i)
    if kind != 'puppet' or a != 1 or p['lie'] > 0.05: prev = {}; continue
    p['s'] = R.s_acc[i]; sol, feet = D.solve(p)
    ox = R.XS + S[i]['dog']['x'] * R.S
    for leg, fp in feet.items():
        u = (p['s'] / D.STRIDE + D.GAIT[leg]) % 1.0
        sx = ox + D.K * (fp[0] - D.A[0])
        if u < D.DUTY:
            if leg in prev and prev[leg][1]: out.append(abs(sx - prev[leg][0]))
            prev[leg] = (sx, True)
        else: prev[leg] = (sx, False)
res = {'stance_frame_pairs': len(out), 'max_px_per_frame': round(max(out), 3), 'mean_px_per_frame': round(sum(out) / len(out), 4),
       'note': 'left-facing walking frames (retreat, approach, holds); the reversed refusal body does not walk'}
os.makedirs(os.path.join(R.ROOT, 'proof'), exist_ok=True)
json.dump(res, open(os.path.join(R.ROOT, 'proof', 'feet.json'), 'w'), indent=1); print(res)
