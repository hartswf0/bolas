"""SCION 46 registration pass (sequential): for every frame, project the solver's landmark vectors through the camera,
choose each plate by view-matching (with hysteresis so substitution never flickers), and fit it.
Writes build/cache/registration.json: per frame, per plate, the view chosen, the mirror flag, the 2x3 fit, the
fit residual (px) and the anisotropy of the fit. This is the face fitting manifest for the dog and the person."""
import json, math, os
import numpy as np
from geom import Camera, CACHE, mirror_key, fit_affine, fit_similarity, residual, apply, W, H, HEAD
from plates import TORSO, HEADS

PERSON_HEAD_SCALE = 0.00082     # metres per source pixel of the face portrait
FACE_PIVOT_SRC = np.array([40.0, 95.0])  # skull pivot in the source face's pixel frame (annotated)


def cam_of(f):
    c = f['camera']; return Camera(c['pos'], c['target'], c['fov'])


def view_of(center, fwd, rt, campos):
    v = np.array(campos) - np.array(center); v[1] = 0
    a = math.degrees(math.atan2(abs(v @ rt), v @ fwd))
    side = 1 if (v @ rt) >= 0 else -1
    return a, side


def pick(table, a, prev, hyst=7.0, allowed=None):
    keys = sorted(allowed or table)
    best = min(keys, key=lambda k: abs(k - a))
    if prev is not None and prev in table and best != prev:
        if abs(a - prev) < abs(a - best) + hyst: return prev
    return best


def anisotropy(M):
    s = np.linalg.svd(M[:, :2], compute_uv=False); return float(s[0] / max(1e-9, s[1]))


def fwd_of(th):
    r = math.radians(th); return np.array([math.cos(r), 0.0, math.sin(r)])


def right_of(th):
    r = math.radians(th); return np.array([-math.sin(r), 0.0, math.cos(r)])


def main():
    rig = json.load(open(os.path.join(CACHE, 'rig.json')))
    pose = json.load(open(os.path.join(CACHE, 'pose.json')))
    reg = []; prev_t = None; prev_h = None
    for f, p in zip(rig, pose):
        cam = cam_of(f)
        P = lambda X: cam.project(np.array(X))[0][0]
        body = {k: np.array(v) for k, v in p['body'].items()}
        head = {k: np.array(v) for k, v in p['head'].items()}
        fw = fwd_of(f['heading']); rt = right_of(f['heading'])
        center = (body['W'] + body['R']) / 2
        a_t, side_t = view_of(center, fw, rt, cam.pos)
        vt = pick(TORSO, a_t, prev_t); prev_t = vt
        pl = TORSO[vt]
        keys = pl['keys']
        src = np.array([pl['lm'][k] for k in keys]) * np.array([1, -1])   # canonical y-up -> screen y-down
        dst = np.array([P(body[k if side_t > 0 else mirror_key(k)]) for k in keys])
        Mt = fit_affine(src, dst)
        hf = fwd_of(f['hyaw']); hr = right_of(f['hyaw'])
        a_h, side_h = view_of(head['S'], hf, hr, cam.pos)
        turning = 3.40 <= f['t'] < 4.10 or 7.40 <= f['t'] < 7.62
        back_to_door = 7.62 <= f['t'] < 8.65 and prev_h in (45, 90)   # once the face is back it stays back
        vh = pick(HEADS, a_h, prev_h, allowed=(45, 90) if back_to_door else ((45, 90, 135) if turning else None)); prev_h = vh
        ph = HEADS[vh]
        src = np.array([ph['lm'][k] for k in ph['keys']]) * np.array([1, -1])
        dst = np.array([P(head[k if side_h > 0 else mirror_key(k)]) for k in ph['keys']])
        Mh = fit_affine(src, dst); fb = False
        if anisotropy(Mh) > 1.5:
            fb = True   # a view far from its plate would squeeze the head: keep its size (similarity fit)
            from geom import fit_similarity_reflect
            Mh = fit_similarity_reflect(src, dst)
            # keep the head's true size (metres x cast scale x px per metre at its depth) and pin its skull pivot to the neck
            from pose import HS
            want = HS * cam.focal / float(cam.project(head['S'])[1][0])
            lin = Mh[:, :2] / np.sqrt(abs(np.linalg.det(Mh[:, :2]))) * want
            s_src = np.array(ph['lm']['S']) * np.array([1, -1])
            Mh = np.hstack([lin, (P(head['S']) - lin @ s_src)[:, None]])
        # person head: similarity only (the source portrait is never sheared)
        pr = f['person']
        reg.append(dict(i=f['i'], t=f['t'],
                        torso=dict(view=vt, alpha=round(a_t, 2), side=side_t, M=Mt.tolist(), res=round(residual(Mt, np.array([pl['lm'][k] for k in keys]) * np.array([1, -1]), np.array([P(body[k if side_t > 0 else mirror_key(k)]) for k in keys])), 3), aniso=round(anisotropy(Mt), 3)),
                        head=dict(view=vh, alpha=round(a_h, 2), side=side_h, M=Mh.tolist(), res=round(residual(Mh, src, dst), 3), aniso=round(anisotropy(Mh), 3), size_kept=fb,
                                  depth=float(cam.project(head['S'])[1][0]))))
    json.dump(reg, open(os.path.join(CACHE, 'registration.json'), 'w'))
    from collections import Counter
    print('torso views', Counter(r['torso']['view'] for r in reg), 'head views', Counter(r['head']['view'] for r in reg))
    print('max torso residual px', max(r['torso']['res'] for r in reg), 'max head residual px', max(r['head']['res'] for r in reg))


if __name__ == '__main__':
    main()
