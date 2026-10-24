"""SCION-04 · assemble film.mp4 (title 3 s + scene 32 s + made-of 3 s, with sound), extract the four stills,
and measure the invariants from trace.json (which is measured from the rendered dog mould, not copied from the score).
Writes ../film.mp4, ../stills/*.jpg, cache/invariants.json."""
import json, os, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE); C = os.path.join(HERE, 'cache')
def run(*a): subprocess.run(a, check=True)

# a lossless-ish master, then a two-pass web encode at ~2.1 Mb/s (film.mp4 must stay under 12 MB)
run('ffmpeg', '-y', '-loglevel', 'error', '-i', f'{C}/title.mp4', '-i', f'{C}/scene.mp4', '-i', f'{C}/end.mp4',
    '-filter_complex', '[0:v][1:v][2:v]concat=n=3:v=1:a=0,format=yuv420p[v]', '-map', '[v]', '-c:v', 'libx264', '-crf', '12', '-preset', 'fast', '-r', '24', f'{C}/master.mp4')
common = ['-c:v', 'libx264', '-preset', 'slow', '-b:v', '2100k', '-maxrate', '3000k', '-bufsize', '4200k', '-pix_fmt', 'yuv420p', '-r', '24', '-passlogfile', f'{C}/x264pass']
run('ffmpeg', '-y', '-loglevel', 'error', '-i', f'{C}/master.mp4', *common, '-pass', '1', '-an', '-f', 'mp4', '/dev/null')
run('ffmpeg', '-y', '-loglevel', 'error', '-i', f'{C}/master.mp4', '-i', f'{C}/sound.wav', '-map', '0:v', '-map', '1:a', *common, '-pass', '2',
    '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-movflags', '+faststart', '-t', '38', os.path.join(OUT, 'film.mp4'))
print('film.mp4', round(os.path.getsize(os.path.join(OUT, 'film.mp4')) / 1e6, 2), 'MB')
os.makedirs(os.path.join(OUT, 'stills'), exist_ok=True)
for name, t in (('refusal-3.6s', 3.6), ('watching-9s', 9.0), ('approach-19s', 19.0), ('sill-28s', 28.0)):
    # scene frame i = round(t*24) is film frame 72 + i
    run('ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(OUT, 'film.mp4'), '-vf', f'select=eq(n\\,{72 + round(t * 24)})', '-frames:v', '1', '-q:v', '2',
        os.path.join(OUT, 'stills', f'{name}.jpg'))
# proof that the dog's pictures are recognisable archive images, at full resolution, from the delivered (compressed) film
for t in (9.0, 19.0, 28.0):
    run('ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(OUT, 'film.mp4'), '-vf', f'select=eq(n\\,{72 + round(t * 24)})', '-frames:v', '1',
        os.path.join(OUT, 'stills', f'proof-tiles-{t:g}s.png'))

# ------------------------------------------------------------------ rhythm: frame-to-frame difference, whole frame and the dog
from PIL import Image, ImageDraw
w_, h_ = 320, 180
raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', f'{C}/scene.mp4', '-vf', f'scale={w_}:{h_}', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True, check=True).stdout
V = np.frombuffer(raw, np.uint8).reshape(-1, h_, w_).astype(np.float32)
TR_ = json.load(open(os.path.join(OUT, 'trace.json')))['frames']
full = [0.0] + [float(np.abs(V[k] - V[k - 1]).mean()) for k in range(1, len(V))]
dogd = [0.0]
for k in range(1, len(V)):
    cx, cy = TR_[k]['x_screen'] / 4, TR_[k]['y_screen'] / 4
    x0, x1 = int(max(0, cx - 45)), int(min(w_, cx + 45)); y0, y1 = int(max(0, cy - 30)), int(min(h_, cy + 25))
    dogd.append(float(np.abs(V[k, y0:y1, x0:x1] - V[k - 1, y0:y1, x0:x1]).mean()))
S_ = json.load(open(os.path.join(OUT, '../score/threshold-score.json')))
ch = [c['t'] for c in S_['choices']] + [26.4]
holds = [(11.9, 14.6), (29.0, 32.0)]
json.dump(dict(about='mean absolute frame difference (0-255, gray, 320x180) of the scene, whole frame and a box around the dog (from trace.json)',
               full=[round(v, 2) for v in full], dog=[round(v, 2) for v in dogd], choices=ch, holds=holds), open(os.path.join(OUT, 'rhythm.json'), 'w'))
PW, PH, ml, mt = 1280, 420, 60, 40; pl = Image.new('RGB', (PW, PH), (250, 247, 240)); d = ImageDraw.Draw(pl)
X = lambda t: ml + (PW - ml - 20) * t / 32; ymax = max(max(dogd), max(full), 1); Y = lambda v: PH - 50 - (PH - 50 - mt) * min(v, ymax) / ymax
for a_, b_ in holds: d.rectangle([X(a_), mt, X(b_), PH - 50], fill=(222, 222, 222)); d.text((X(a_) + 4, mt + 4), 'hold', fill=(80, 80, 80))
for c in ch: d.line([X(c), mt, X(c), PH - 50], fill=(200, 40, 30), width=1); d.text((X(c) + 2, PH - 46), f'{c:g}', fill=(200, 40, 30))
for series, col in ((full, (60, 90, 160)), (dogd, (190, 110, 30))):
    d.line([(X(k / 24), Y(v)) for k, v in enumerate(series)], fill=col, width=2)
d.text((ml, 10), 'SCION-04 rhythm: frame-to-frame difference (blue: whole frame, orange: the dog). Red: the choices; grey: the two holds. t in s.', fill=(20, 20, 20))
for v in range(0, int(ymax) + 1, max(1, int(ymax // 5))): d.text((10, Y(v) - 6), str(v), fill=(90, 90, 90))
pl.save(os.path.join(OUT, 'rhythm.png'))

# ------------------------------------------------------------------ invariants, measured
T = json.load(open(os.path.join(OUT, 'trace.json')))['frames']
S = json.load(open(os.path.join(OUT, '../score/threshold-score.json')))
t = np.array([f['t'] for f in T]); x = np.array([f['x_world_measured'] for f in T])
top = np.array([f['body_top_m'] for f in T]); head = np.array([f['head_up_m'] for f in T]); hdx = np.array([f['head_dx_m'] for f in T])
def first(cond, after, before=99):
    idx = np.nonzero(cond & (t >= after) & (t < before))[0]
    return float(t[idx[0]]) if len(idx) else None
dx = np.gradient(x)
hdx_s = np.abs(hdx)
meas = {}
meas['retreat (backs away)'] = (1.0, first(dx > 0.003, 0.5, 2.2))
meas['retreat -> watch (head comes up out of the crouch)'] = (2.333, first(head > head[int(2.2 * 24)] + 0.03, 2.2, 3.2))
meas['  (info) retreat steps end (x stops)'] = (None, first(np.abs(dx) < 0.0015, 2.0, 3.2))
meas['refuse (cowers: head drops, then turns its back)'] = (3.417, first(head < head[int(3.3 * 24)] - 0.03, 3.3, 5.0))
meas['  (info) turn of the back begins (head offset shrinks)'] = (None, first(hdx_s < hdx_s[int(3.0 * 24)] - 0.03, 3.0, 5.0))
meas['  (info) back fully turned (head on the far side)'] = (None, first(np.sign(hdx) != np.sign(hdx[int(3.0 * 24)]), 3.0, 6.0))
base = head[int(7.0 * 24)]
meas['refuse -> watch (lifts head, turns back to look)'] = (7.458, first(head > base + 0.03, 7.0, 9.0))
meas['watch -> approach (starts toward the door)'] = (14.708, first(dx < -0.003, 14.0, 16.0))
base = top[int(23.4 * 24)]
meas['approach -> lie down (body lowers at the sill)'] = (23.792, first(top < base - 0.03, 23.4, 25.0))
base = head[int(26.2 * 24)]
meas['hears come in: looks in (head rises)'] = (26.4, first(head > base + 0.03, 26.2, 27.6))
choices = {}
for k, (exp, got) in meas.items():
    choices[k] = dict(expected=exp, measured=got, delta=None if (exp is None or got is None) else round(got - exp, 3),
                      ok=None if exp is None else (got is not None and abs(got - exp) <= 0.25))
# never enters: the dog's measured centre stays outside; at rest its front is in the door frame and its back outside
rest = [f for f in T if f['t'] >= 25.0]
inv = dict(
    choices=choices,
    min_x_world_measured=float(x.min()), never_past_sill=bool(x.min() >= 0.56 - 0.02),
    final_extent_m=rest[-1]['extent_m'], doorway_m=[-0.46, 0.46], right_jamb_m=[0.46, 0.58],
    ends_across_threshold=bool(rest[-1]['extent_m'][0] < 0.46 and rest[-1]['extent_m'][1] > 0.58),
    final_posture=rest[-1]['posture'], final_facing=rest[-1]['facing'],
    approach_distance_m=round(float(x[int(14.7 * 24)] - x[int(23.79 * 24)]), 3),
    approach_distance_score_m=round(S['frames'][int(14.7 * 24)]['dog']['x'] - S['frames'][int(23.79 * 24)]['dog']['x'], 3),
    retreat_direction=('away from the door (+x)' if x[int(2.3 * 24)] > x[int(1.0 * 24)] else 'toward the door'),
    max_abs_x_error_m=round(float(np.max(np.abs(x - np.array([f['x_score'] for f in T])))), 3),
    facing_away_frames=[round(float(t[i]), 3) for i in (np.nonzero(np.array([f['facing'] for f in T]) == 'away')[0][[0, -1]])],
)
json.dump(inv, open(os.path.join(C, 'invariants.json'), 'w'), indent=1)
print(json.dumps(inv, indent=1))
