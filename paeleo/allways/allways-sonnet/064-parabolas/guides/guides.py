"""Burn fitted-model guides onto copies of frames of 064-parabolas-noguides.mp4 -> 064-parabolas.mp4.

All guides are MODEL OVERLAYS: drawn on top of the rendered film, never replacing source pixels outside
their thin lines. Fits, samples and residuals are written to guides/fits.json.
Source coordinates are in the 320x240 clip frame; the film shows these clips at scale 2.0, offset 0
(see 064-parabolas-noguides.ledger.json), so film px = 2 * source px.

usage: python3 guides/guides.py   (run from the film folder)
"""
import json, subprocess, os, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); FILM = os.path.dirname(HERE)
IDX = {e['id'][:8]: e for e in json.load(open('/home/user/bolas/tools/allways-forage/index.json'))}
LED = json.load(open(os.path.join(FILM, '064-parabolas-noguides.ledger.json')))
W, H, FPS, S = 640, 480, 24, 2.0

def decode(k, t0, t1, w=320, h=240):
    p = IDX[k]['media']['clip']
    o = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t0}', '-i', p, '-t', f'{t1 - t0}', '-vf', f'fps={FPS},scale={w}:{h}',
                        '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True).stdout
    n = len(o) // (w * h)
    return np.frombuffer(o[:n * w * h], np.uint8).reshape(n, h, w).astype(np.float32)

def camera_path(k, t0, t1, band):
    """cumulative content translation (source px) per frame at FPS, by phase correlation on a horizontal band"""
    F = decode(k, t0, t1); y0, y1 = int(band[0] * 240), int(band[1] * 240)
    win = cv2.createHanningWindow((320, y1 - y0), cv2.CV_32F); cam = [(0.0, 0.0)]
    for i in range(1, len(F)):
        (dx, dy), _ = cv2.phaseCorrelate(F[i - 1][y0:y1], F[i][y0:y1], win)
        cam.append((cam[-1][0] + dx, cam[-1][1] + dy))
    ts = [t0 + i / FPS for i in range(len(F))]
    return np.array(ts), np.array(cam)

def fit_ballistic(t, x, y):
    """screen/world model: x = a0 + a1 t ; y = b0 + b1 t + b2 t^2 (least squares)"""
    A1 = np.vstack([np.ones_like(t), t]).T; A2 = np.vstack([np.ones_like(t), t, t * t]).T
    a = np.linalg.lstsq(A1, x, rcond=None)[0]; b = np.linalg.lstsq(A2, y, rcond=None)[0]
    rx = x - A1 @ a; ry = y - A2 @ b
    return a, b, float(np.sqrt(np.mean(rx ** 2 + ry ** 2)))

fits = {'note': 'All curves are fitted 2-D screen-space models. No physical constant is derived; time base of 1930s footage may be altered (slow motion).'}

# ---------- Guide A: diver, hips marked by eye on 3x zoomed grids (uncertainty ~ +/-8 source px), camera pan compensated
evA = LED['events'][8]; inA = evA['layers'][0]['clip_in']
tsA, camA = camera_path('652e9a2d', inA, inA + 2.0, (0.15, 0.45))
man = [(3.10, 82, 112), (3.20, 100, 120), (3.30, 97, 117), (3.40, 115, 118), (3.50, 130, 130), (3.60, 140, 155)]
def cam_at(ts, cam, t): return np.array([np.interp(t, ts, cam[:, 0]), np.interp(t, ts, cam[:, 1])])
tA = np.array([m[0] for m in man]); wA = np.array([np.array(m[1:]) - cam_at(tsA, camA, m[0]) for m in man])
aA, bA, rmsA = fit_ballistic(tA - tA[0], wA[:, 0], wA[:, 1])
fits['A_dive'] = {'src': IDX['652e9a2d']['id'], 'film_event': 8, 'method': 'hip position marked by eye on zoomed frames; camera translation by phase correlation on tree band y=15-45% ; world = screen - cam; x linear, y quadratic in t',
                  'samples_screen': man, 'samples_world': wA.round(1).tolist(), 'x_coef': aA.round(3).tolist(), 'y_coef': bA.round(3).tolist(),
                  'rms_px_source': round(rmsA, 2), 'uncertainty': 'marking +/-8 px; pan estimate drift unknown; diver is an extended body, not a point'}

# ---------- Guide B: high diver, automatic dark-blob track in raw screen space (no compensation possible: sky/clouds)
evB = LED['events'][9]; inB = evB['layers'][0]['clip_in']
FB = decode('55c605ed', inB, inB + 6.4)
trB = []; prev = np.array([232.0, 120.0])  # seed: diver position read from the first frames (source px)
for i, f in enumerate(FB):
    bg = cv2.GaussianBlur(f, (0, 0), 12); m = ((bg - f) > 40).astype(np.uint8); m[:4] = 0; m[-4:] = 0; m[:, :4] = 0; m[:, -4:] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    nl, lab, st, cen = cv2.connectedComponentsWithStats(m); best = None
    for l in range(1, nl):
        x, y, w, h, a = st[l]
        if a < 40 or h > 0.3 * 240 or w > 0.35 * 320 or h > 3 * w: continue   # compact blobs only (excludes the lattice tower)
        d = np.hypot(*(cen[l] - prev))
        if d < 30 and (best is None or d < best[0]): best = (d, cen[l])
    if best is not None:
        prev = best[1].copy(); trB.append((inB + i / FPS, float(best[1][0]), float(best[1][1])))
trB = np.array(trB)
aB, bB, rmsB = fit_ballistic(trB[:, 0] - trB[0, 0], trB[:, 1], trB[:, 2])
fits['B_highdive'] = {'src': IDX['55c605ed']['id'], 'film_event': 9, 'method': 'dark-blob tracking (local contrast > 40 vs 12px gaussian background, compact component), raw screen coordinates; same x-linear / y-quadratic model',
                      'n_samples': int(len(trB)), 'samples_screen_every10': trB[::10].round(2).tolist(), 'x_coef': aB.round(3).tolist(), 'y_coef': bB.round(3).tolist(),
                      'rms_px_source': round(rmsB, 2), 'why_it_departs': 'the camera tilts and pans to follow the diver; screen path records camera operation as much as flight. Cloud-based compensation was tried (phase correlation) and judged unreliable (low-contrast clouds, vignette).'}

# ---------- Guide C: round-headed doorway (static camera), rim marked by eye on a 6x zoomed grid (+/-1.5 source px)
evC = LED['events'][10]; LC = evC['layers'][0]
assert LC['transform']['fit'] == 'register'
KC = LC['transform']['scale']; OFF = np.array(LC['transform']['offset_px'])   # film px = OFF + KC * source px
crown = np.array([(129.5, 140), (130, 130), (131.7, 122.5), (135.8, 117.5), (142, 114), (150, 112.5), (158, 114),
                  (164.2, 117.5), (169.2, 122.5), (171.7, 130), (172.5, 140)], float)
jambs = np.array([(129.3, 150), (129.3, 160), (173, 150), (173, 160)], float)
fitpts = crown
P = np.polyfit(fitpts[:, 0], fitpts[:, 1], 2); rpC = fitpts[:, 1] - np.polyval(P, fitpts[:, 0])
A_ = np.c_[2 * fitpts[:, 0], 2 * fitpts[:, 1], np.ones(len(fitpts))]; bb = (fitpts ** 2).sum(1)
cx, cy, c = np.linalg.lstsq(A_, bb, rcond=None)[0]; RC = np.sqrt(c + cx * cx + cy * cy)
rcC = np.hypot(fitpts[:, 0] - cx, fitpts[:, 1] - cy) - RC
# how far each model is from the jamb samples (not used in the fit)
jp = jambs[:, 1] - np.polyval(P, jambs[:, 0]); jc = np.hypot(jambs[:, 0] - cx, jambs[:, 1] - cy) - RC
fits['C_doorway'] = {'src': IDX['ec168197']['id'], 'film_event': 10, 'method': 'outer rim of the arch marked by eye at one frame (t=1.0 s, static camera, checked stable at 0.5 and 2.5 s); parabola y(x) and algebraic circle fitted to the 11 crown samples; 4 jamb samples held out',
                     'samples_crown': crown.tolist(), 'samples_jambs_held_out': jambs.tolist(), 'parabola': P.round(5).tolist(), 'circle_cx_cy_r': [round(cx, 2), round(cy, 2), round(RC, 2)],
                     'rms_parabola_px': round(float(np.sqrt(np.mean(rpC ** 2))), 2), 'rms_circle_px': round(float(np.sqrt(np.mean(rcC ** 2))), 2),
                     'heldout_jamb_error_parabola_px': np.abs(jp).round(1).tolist(), 'heldout_jamb_error_circle_px': np.abs(jc).round(1).tolist(),
                     'uncertainty': 'arch only ~44 px wide in the 320x240 source; perspective slightly oblique; rim is a painted/moulded band, not a structural line'}
json.dump(fits, open(os.path.join(HERE, 'fits.json'), 'w'), indent=1)

# ---------- draw
COL = {'A': (255, 200, 60), 'B': (40, 140, 255), 'Cp': (230, 230, 60), 'Cc': (230, 80, 230)}  # BGR
def poly(img, pts, col, th=1):
    pts = np.round(np.array(pts) * S).astype(np.int32)
    cv2.polylines(img, [pts.reshape(-1, 1, 2)], False, col, th, cv2.LINE_AA)
def tag(img, text, col):
    cv2.rectangle(img, (6, H - 30), (min(W - 6, 14 + int(7.6 * len(text))), H - 8), (0, 0, 0), -1)
    cv2.putText(img, text, (12, H - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, col, 1, cv2.LINE_AA)

src = os.path.join(FILM, '064-parabolas-noguides.mp4'); out = os.path.join(FILM, '064-parabolas.mp4')
dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-i', src, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '23', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                        '-c:a', 'copy', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
k = 0
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    img = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy(); ft = k / FPS
    if evA['t_in'] <= ft < evA['t_out']:
        st = inA + (ft - evA['t_in']); c = cam_at(tsA, camA, st)
        if st >= 3.30:
            tt = np.linspace(0, 0.62, 40); curve = np.c_[aA[0] + aA[1] * tt, bA[0] + bA[1] * tt + bA[2] * tt * tt] + c
            poly(img, curve, COL['A'], 1)
        for (tm, x, y), wp in zip(man, wA):
            if tm <= st: p = (wp + c) * S; cv2.circle(img, tuple(np.round(p).astype(int)), 3, COL['A'], 1, cv2.LINE_AA)
        tag(img, f'fitted model A: hand-marked hips, pan removed, rms {rmsA:.1f}px', COL['A'])
    if evB['t_in'] <= ft < evB['t_out']:
        st = inB + (ft - evB['t_in']); shown = trB[trB[:, 0] <= st]
        for p in shown[::3]: cv2.circle(img, tuple(np.round(p[1:] * S).astype(int)), 2, COL['B'], -1, cv2.LINE_AA)
        if len(shown) > 20:
            tt = np.linspace(0, trB[-1, 0] - trB[0, 0], 80); poly(img, np.c_[aB[0] + aB[1] * tt, bB[0] + bB[1] * tt + bB[2] * tt * tt], COL['B'], 1)
        tag(img, f'fitted model B: screen track, camera moving, rms {rmsB:.1f}px', COL['B'])
    if evC['t_in'] <= ft < evC['t_out']:
        st = ft - evC['t_in']
        def fp(q): return np.round(OFF + KC * np.asarray(q)).astype(np.int32)
        for q in crown: cv2.circle(img, tuple(fp(q)), 3, (255, 255, 255), 1, cv2.LINE_AA)
        for q in jambs: cv2.drawMarker(img, tuple(fp(q)), (255, 255, 255), cv2.MARKER_TILTED_CROSS, 7, 1)
        if st >= 0.6:
            xs = np.linspace(124, 178, 120); inside = np.abs(xs - cx) < RC
            cv2.polylines(img, [fp(np.c_[xs[inside], cy - np.sqrt(RC * RC - (xs[inside] - cx) ** 2)]).reshape(-1, 1, 2)], False, COL['Cc'], 2, cv2.LINE_AA)
            cv2.polylines(img, [fp(np.c_[xs, np.polyval(P, xs)]).reshape(-1, 1, 2)], False, COL['Cp'], 2, cv2.LINE_AA)
        tag(img, f'fitted C: parabola rms {fits["C_doorway"]["rms_parabola_px"]}px / circle rms {fits["C_doorway"]["rms_circle_px"]}px (source px)', COL['Cp'])
    enc.stdin.write(img.tobytes()); k += 1
enc.stdin.close(); enc.wait()
print('frames', k, json.dumps({x: {kk: v for kk, v in fits[x].items() if 'rms' in kk or 'heldout' in kk} for x in fits if x != 'note'}))
