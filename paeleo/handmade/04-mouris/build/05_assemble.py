"""SCION-04 · assemble film.mp4 (title 3 s + scene 32 s + made-of 3 s, with sound), extract the four stills,
and measure the invariants from trace.json (which is measured from the rendered dog mould, not copied from the score).
Writes ../film.mp4, ../stills/*.jpg, cache/invariants.json."""
import json, os, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE); C = os.path.join(HERE, 'cache')
def run(*a): subprocess.run(a, check=True)

run('ffmpeg', '-y', '-loglevel', 'error', '-i', f'{C}/title.mp4', '-i', f'{C}/scene.mp4', '-i', f'{C}/end.mp4', '-i', f'{C}/sound.wav',
    '-filter_complex', '[0:v][1:v][2:v]concat=n=3:v=1:a=0,format=yuv420p[v]', '-map', '[v]', '-map', '3:a',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-r', '24', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart',
    '-t', '38', os.path.join(OUT, 'film.mp4'))
os.makedirs(os.path.join(OUT, 'stills'), exist_ok=True)
for name, t in (('refusal-3.6s', 3.6), ('watching-9s', 9.0), ('approach-19s', 19.0), ('sill-28s', 28.0)):
    # scene frame i = round(t*24) is film frame 72 + i
    run('ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(OUT, 'film.mp4'), '-vf', f'select=eq(n\\,{72 + round(t * 24)})', '-frames:v', '1', '-q:v', '2',
        os.path.join(OUT, 'stills', f'{name}.jpg'))

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
