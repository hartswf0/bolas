"""Measure the final film's own frames (critic round 2): key parabola + rotation (V.3), bell damping (II.4),
parallax per plane (V.3, phase correlation of the encoded frames), pivot error (rig matrices at the film's frame
times).  python3 -I films/swarm/la-belle-hortense/editor/measure_final.py  -> editor/measures/final_film.json
"""
import json, math, os, subprocess, sys
import numpy as np, cv2
sys.path.insert(0, '/home/user/bolas/paeleo/scion/oulipo/films/swarm/la-belle-hortense/animator')
import scene as S
S.key_screen(43.3)

ROOT = '/home/user/bolas/paeleo/scion/oulipo'
MP4 = os.path.join(ROOT, 'assets/films/la-belle-hortense.mp4')
OUT = os.path.join(ROOT, 'films/sources/la-belle-hortense/editor/measures/final_film.json')
W, H, FPS = 960, 540, 24

def frames(t0, t1):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', '%.4f' % t0, '-i', MP4, '-t', '%.4f' % (t1 - t0),
                          '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)

res = {'film': os.path.relpath(MP4, ROOT), 'size_bytes': os.path.getsize(MP4)}

# ---- key in V.3: brass pixels (hue 35-55 deg, high sat and value) below the hem, from the drop at 43.2 s
fr = frames(43.0, 43.5)
t0f = round(43.0 * FPS)
pts = []
for i, f in enumerate(fr):
    t = (t0f + i + 0.5) / FPS
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
    m = ((hsv[..., 0] >= 17) & (hsv[..., 0] <= 28) & (hsv[..., 1] > 120) & (hsv[..., 2] > 140)).astype(np.uint8)
    ks = S.key_screen(t) if t >= 43.2 else None
    win = np.zeros_like(m)
    if ks is not None:                                         # search window only: 70 px round the authored path
        x0, y0 = int(ks[0]), int(ks[1]); win[max(y0 - 70, 0):y0 + 70, max(x0 - 70, 0):x0 + 70] = 1
    m *= win
    n, lab, st, cen = cv2.connectedComponentsWithStats(m)
    if n < 2: continue
    j = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    if st[j, cv2.CC_STAT_AREA] < 25: continue
    mm = (lab == j).astype(np.uint8)
    mo = cv2.moments(mm)
    ang = 0.5 * math.degrees(math.atan2(2 * mo['mu11'], mo['mu20'] - mo['mu02']))
    pts.append(dict(t=round(t, 4), x=float(cen[j][0]), y=float(cen[j][1]), area=int(st[j, cv2.CC_STAT_AREA]), axis_deg=round(ang, 1)))
fall = [p for p in pts if p['t'] >= 43.2]
key = dict(frames=pts)
if len(fall) >= 4:
    ts = np.array([p['t'] - 43.2 for p in fall]); ys = np.array([p['y'] for p in fall])
    c = np.polyfit(ts, ys, 2); r = ys - np.polyval(c, ts)
    ax = np.unwrap(np.radians([p['axis_deg'] for p in fall]) * 2) / 2
    w = np.polyfit(ts, np.degrees(ax), 1)[0]
    key.update(n=len(fall), g_px_s2=round(float(2 * c[0]), 1), rms_residual_px=round(float(np.sqrt((r ** 2).mean())), 2),
               rotation_deg_s=round(float(w), 1), authored=dict(g=2600, rotation_deg_s=690),
               note='centroid of the largest brass component in each encoded frame; the near shin occludes part of the key and the 180-degree shutter smears it, so the centroid is biased; principal-axis angle is mod 180')
res['V3_key'] = key

# ---- bell in II.4 (16.5-18.0): principal axis of the bronze bell body per frame
fr = frames(16.5, 18.0)
ang = []
sh = S.plate('shed')
bgp = cv2.cvtColor((np.clip(cv2.resize(sh, (960, 720), interpolation=cv2.INTER_AREA)[110:650], 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2BGR).astype(np.float32)
for i, f in enumerate(fr):
    t = (i + 0.5) / FPS
    d = np.abs(f.astype(np.float32) - bgp).sum(-1)
    m = (d > 60).astype(np.uint8)
    m[380:] = 0; m[:, :360] = 0; m[:, 760:] = 0               # clear of the type block
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    ys, xs = np.nonzero(m)
    if len(xs) < 200: continue
    a = math.degrees(math.atan2(xs.mean() - 560.0, ys.mean() + 40.0 * 0.78))   # about the headstock pin (560, -40)
    ang.append((t, a))
bell = dict(samples=len(ang))
if len(ang) > 10:
    t = np.array([a[0] for a in ang]); th = np.array([a[1] for a in ang]); th -= np.median(th)
    best = None
    for tau in np.linspace(0.3, 6.0, 115):
        for f in np.linspace(0.6, 1.6, 51):
            for ph in np.linspace(0, 2 * np.pi, 37)[:-1]:
                b = np.exp(-(t - 0.1) / tau) * np.sin(2 * np.pi * f * (t - 0.1) + ph)
                A = (b @ th) / max(b @ b, 1e-9); e = ((th - A * b) ** 2).mean()
                if best is None or e < best[0]: best = (e, tau, f, ph, A)
    e, tau, f, ph, A = best
    bell.update(tau_s=round(float(tau), 2), freq_hz=round(float(f), 2), amp_deg=round(float(abs(A)), 1),
                rms_residual_deg=round(float(math.sqrt(e)), 2), authored=dict(tau=1.5, f=1.05, theta0=26.0),
                note='swing angle of the bronze-mask centroid about the headstock column x=560, fitted A exp(-t/tau) sin(2 pi f t + phi)')
res['II4_bell'] = bell

# ---- parallax in V.3: phase correlation between consecutive encoded frames, per plane band, runner columns masked
fr = frames(42.0, 43.5)
bands = dict(far=(0, 56), mid=(70, 165), ground=(180, 425), near=(445, 540))
expect = dict(far=0.35 * 4200 / FPS, mid=0.60 * 4200 / FPS, ground=1.0 * 4200 / FPS, near=1.6 * 4200 / FPS)
par = {k: [] for k in bands}
for a, b in zip(fr[:-1], fr[1:]):
    for k, (y0, y1) in bands.items():
        A = cv2.cvtColor(a[y0:y1], cv2.COLOR_BGR2GRAY).astype(np.float32)
        B = cv2.cvtColor(b[y0:y1], cv2.COLOR_BGR2GRAY).astype(np.float32)
        A[:, 330:640] = A[:, 330:640].mean(); B[:, 330:640] = B[:, 330:640].mean()
        win = cv2.createHanningWindow((A.shape[1], A.shape[0]), cv2.CV_32F)
        (dx, dy), r = cv2.phaseCorrelate(A, B, win)
        par[k].append(abs(dx))
def shift_search(a, b, y0, y1, x0=560, x1=960, smax=400):
    A = cv2.cvtColor(a[y0:y1], cv2.COLOR_BGR2GRAY).astype(np.float32); B = cv2.cvtColor(b[y0:y1], cv2.COLOR_BGR2GRAY).astype(np.float32)
    best = None
    for sft in range(0, smax):
        if x0 + sft + 120 > W: break
        xa1 = min(x1, W - sft)
        ra = A[:, x0 + sft:xa1 + sft] if xa1 + sft <= W else None
        rb = B[:, x0:xa1]
        if ra is None or ra.shape != rb.shape: continue
        ra = ra - ra.mean(); rb = rb - rb.mean()
        c = (ra * rb).sum() / (np.sqrt((ra ** 2).sum() * (rb ** 2).sum()) + 1e-6)
        if best is None or c > best[0]: best = (c, sft)
    return best[1]
for k, (y0, y1) in (('ground', (180, 380)), ('near', (445, 540))):
    par[k] = [shift_search(a, b, y0, y1, x0=650 if k == 'ground' else 540) for a, b in zip(fr[:-1:3], fr[1::3])]
pm = {k: round(float(np.median(v)), 1) for k, v in par.items()}
res['V3_parallax'] = dict(measured_px_per_frame_median=pm, authored_px_per_frame={k: round(v, 1) for k, v in expect.items()},
                          order_near_gt_ground_gt_mid_gt_far=bool(pm['near'] > pm['ground'] > pm['mid'] > pm['far']),
                          note='phase correlation of each band between consecutive encoded frames (runner columns 330-640 flattened); shifts above half a band width alias')

# ---- pivots: the rig matrices used for every V.3 frame of the film (same functions the clip was integrated with)
mx = 0.0
for k in range(round(42.0 * FPS), round(43.5 * FPS)):
    for i in range(36):
        t = (k + 0.5) / FPS + ((i + 0.5) / 36 - 0.5) * 0.5 / FPS
        pose, _ = S.run_pose(t)
        M = S.RUN.mats(S.runner_x(t), S.HIP_Y + S.bob(t), S.SCALE, S.LEAN, pose)
        mx = max(mx, max(S.RUN.pivot_errors(M).values()))
res['V3_pivot_max_px'] = mx
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(res, open(OUT, 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'V3_key'}, indent=1))
print(json.dumps({k: v for k, v in key.items() if k != 'frames'}, indent=1))
