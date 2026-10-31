"""SCION 32 · trace.json from the render's own measurements (build/cache/measure.json, one record per scene frame).
Pixel measures come from an id pass of the same frame (same camera, same depth test): the dog's visible silhouette centroid,
its head's visible pixels. Geometry measures (nose, skull) are the rig's points projected with that frame's camera."""
import json, math, os
H = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(H, '../../score/threshold-score.json')))
M = json.load(open(os.path.join(H, 'cache/measure.json')))
X_OFF, MID = 0.12, 0.175 * 1.4
assert len(M) == 768, len(M)

def ray_x0(cam, px, py):  # back-project a pixel onto the vertical plane X = 0 (the dog's line); returns Z
    p, t = cam['pos'], cam['tgt']
    f = [t[k] - p[k] for k in range(3)]; n = math.sqrt(sum(v * v for v in f)); f = [v / n for v in f]
    r = [f[1] * 0 - f[2] * 1, f[2] * 0 - f[0] * 0, f[0] * 1 - f[1] * 0]; n = math.sqrt(sum(v * v for v in r)); r = [v / n for v in r]
    u = [r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0]]
    th = math.tan(math.radians(cam['fov']) / 2); nx = (px / 1280) * 2 - 1; ny = 1 - (py / 720) * 2
    d = [f[k] + nx * th * 1280 / 720 * r[k] + ny * th * u[k] for k in range(3)]
    s = -p[0] / d[0]
    return p[2] + s * d[2]

rows = []
for m in M:
    i = m['i']; t = i / 24
    dog = m['dog']; ok = dog is not None
    zc = ray_x0(m['cam'], dog[0], dog[1]) if ok else None
    mz = [m['nose'][0] - m['skull'][0], m['nose'][1] - m['skull'][1]]
    dz = [m['door'][0] - m['skull'][0], m['door'][1] - m['skull'][1]]
    ang = math.degrees(math.atan2(mz[1], mz[0]))
    cosd = (mz[0] * dz[0] + mz[1] * dz[1]) / (math.hypot(*mz) * math.hypot(*dz) + 1e-9)
    ppm = m['g0'][1] - m['g1'][1]   # pixels per metre at the dog's depth
    top_m = (m['g0'][1] - m['bbox'][1]) / ppm if ok else None
    head_m = (m['g0'][1] - m['head_top_px']) / ppm if m.get('head_top_px') else None
    rows.append(dict(i=i, t=round(t, 4), ok=ok, xs=dog[0] if ok else None, ys=dog[1] if ok else None, area=dog[2] if ok else 0,
                     xw=None if zc is None else zc + X_OFF + MID, mang=ang, door_deg=math.degrees(math.acos(max(-1, min(1, cosd)))),
                     facing=1 if cosd > 0 else -1, top_m=top_m, head_m=head_m, hx=m['head'][0] if m['head'] else None, hy=m['head'][1] if m['head'] else None, zmid=m['zmid'], lie=m['lie']))
def mean(a): a = [v for v in a if v is not None]; return sum(a) / len(a)
def win(k, a, b): return [r[k] for r in rows if a <= r['t'] <= b]
def first(cond, t0):
    for r in rows:
        if r['t'] >= t0 and cond(r): return r['t']
    return None
def sm(k, i): return mean([rows[j][k] for j in range(max(0, i - 1), min(767, i + 1) + 1)])
on = []
b = mean(win('xw', 0.5, 0.9));       on.append(('watch -> retreat', 1.0, 'dog silhouette centroid, back-projected to the path, moves > 2 cm away from the door (from its 0.5-0.9 s mean)', first(lambda r: sm('xw', r['i']) > b + 0.02, 0.8)))
lo = min(win('head_m', 1.5, 2.2));   on.append(('retreat -> watch', 2.333, 'top of the visible head rises > 2 cm above its lowest point of the retreat (1.5-2.2 s)', first(lambda r: r['head_m'] is not None and r['head_m'] > lo + 0.02, 2.0)))
a0 = rows[round(3.3 * 24)]['mang']; on.append(('watch -> refuse', 3.417, 'muzzle direction on screen turns > 10 deg from its 3.3 s heading (the head leads the turn away)', first(lambda r: abs((r['mang'] - a0 + 180) % 360 - 180) > 10, 3.3)))
d0 = rows[round(7.3 * 24)]['door_deg']; on.append(('refuse -> watch', 7.458, 'angle between the muzzle and the door on screen falls > 10 deg from its 7.3 s value (the head comes round)', first(lambda r: r['door_deg'] < d0 - 10, 7.3)))
b = mean(win('xw', 14.0, 14.5));     on.append(('watch -> approach', 14.708, 'silhouette centroid, back-projected, moves > 2 cm toward the door (from its 14.0-14.5 s mean)', first(lambda r: sm('xw', r['i']) < b - 0.02, 14.4)))
b = mean(win('top_m', 23.3, 23.6));  on.append(('approach -> lie_down', 23.792, 'top of the visible silhouette, in metres over the floor at the dog, drops > 2 cm (from its 23.3-23.6 s mean)', first(lambda r: r['top_m'] < b - 0.02, 23.5)))
bx, by = mean(win('hx', 25.9, 26.3)), mean(win('hy', 25.9, 26.3)); on.append(('hears come in: looks in', 26.4, 'centroid of the visible head moves > 4 px (from its 25.9-26.3 s mean) as it lifts level and turns into the doorway', first(lambda r: r['hx'] is not None and ((r['hx'] - bx) ** 2 + (r['hy'] - by) ** 2) ** 0.5 > 4, 26.2)))
backshown = first(lambda r: r['facing'] == -1, 3.42)
cuts = [o[3] for o in on]
def state(t):
    s = 'watch'
    for (name, _, _, tt) in on[:6]:
        if tt is not None and t >= tt: s = name.split(' -> ')[1]
    return s
frames = []
for r, f in zip(rows, S['frames']):
    a = f['dog']['act']
    post = 'lying' if r['lie'] > 0.5 else 'walking' if a['moving'] > 0.3 else 'crouched' if a['crouch'] > 0.4 else 'standing'
    frames.append({'i': r['i'], 't': r['t'], 'state': state(r['t']), 'x_score': round(r['zmid'] + MID + X_OFF, 4), 'x_screen': None if r['xs'] is None else round(r['xs'], 1), 'y_screen': None if r['ys'] is None else round(r['ys'], 1),
                   'x_world_measured': None if r['xw'] is None else round(r['xw'], 4), 'facing': r['facing'], 'posture': post, 'muzzle_to_door_deg': round(r['door_deg'], 1), 'dog_px': r['area'],
                   'silhouette_top_m': None if r['top_m'] is None else round(r['top_m'], 3), 'head_top_m': None if r['head_m'] is None else round(r['head_m'], 3)})
summ = {'onsets_measured': [{'choice': n, 'score_t': st, 'measure': ms, 't': tt, 'dt': None if tt is None else round(tt - st, 3), 'within_0.25s': None if tt is None else abs(tt - st) <= 0.25} for (n, st, ms, tt) in on],
        'back_shown_from_t': backshown, 'frames_without_dog_pixels': [r['i'] for r in rows if not r['ok']], 'min_dog_px': min(r['area'] for r in rows)}
out = {'about': 'SCION 32 trace, measured from the render. x_screen/y_screen: centroid of the dog\'s visible pixels in an id pass of the same frame (same camera and depth test). x_world_measured: that centroid back-projected through the frame\'s camera onto the vertical plane of the dog\'s line, plus the mapping offset (metres, score units). facing: +1 when the muzzle (rig nose and skull points projected with the frame camera) points toward the door on screen, -1 away. state: from the measured onsets below, not from the score\'s labels. x_score: the rig\'s body-middle position mapped back to score metres. posture: reported by the rig (lie, crouch, moving).',
       'camera': 'one wide set-up 0-14.6 s, then a moving camera (tracking the approach, settling behind the dog\'s right shoulder at the sill); x_world_measured is therefore given every frame',
       'summary': summ, 'frames': frames}
json.dump(out, open(os.path.join(H, '..', 'trace.json'), 'w'))
print(json.dumps(summ['onsets_measured'], indent=0)); print('back shown from', backshown, 'missing', summ['frames_without_dog_pixels'][:10], 'min px', summ['min_dog_px'])
