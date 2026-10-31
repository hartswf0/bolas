"""Assemble film.mp4 (title 3 s + scene 32 s + end card 3 s, H.264 + AAC, faststart), trace.json (measured from the
drawn dog's mask pass), measured choice onsets, and the four stills taken from the encoded film."""
import json, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); TOP = os.path.dirname(HERE); C = os.path.join(HERE, 'cache')
ROOT = os.path.abspath(os.path.join(TOP, '../../..'))
SCORE = json.load(open(os.path.join(TOP, '../score/threshold-score.json')))
M = json.load(open(os.path.join(C, 'measure.json')))
assert len(M) == 768, len(M)

# ---------- end card (claims only what the picture and the build show) ----------
nstr = json.load(open(os.path.join(C, 'rig_counts.json'))) if os.path.exists(os.path.join(C, 'rig_counts.json')) else None
lines = [
    "The dog: crepe- and tissue-paper strips with torn ends, drawn in code, hung in overlapping rows on a",
    "torso of paper discs, with a skull, a muzzle, four legs, long fringed ears, a feathered tail and a loose dewlap.",
    "Every strip, ear, tail link, reed, curtain strip, and her hair, scarf and coat tails is a secondary link:",
    "an inertial spring-damper pulled toward a rest shape, under gravity and wind, with collision masks",
    "(the floor, the dog's body, her arm). Its coat flattens on the refusal; its ears flick at the soft voice.",
    "The primary motion follows the PAELEO score frame by frame. It lies across the sill: head and forepaws in, tail out.",
    "Voices and sound are synthesized here. No footage, photograph or recording is used.",
    "Fonts: Big Shoulders Display, Literata (SIL OFL), from tools/paeleo/fonts.",
]
json.dump(lines, open(os.path.join(C, 'endlines.json'), 'w'))
env = dict(os.environ, NODE_PATH=os.environ.get('NODE_PATH', '/opt/node-tools/node_modules'))
subprocess.run(['node', os.path.join(HERE, 'render.js'), 'cards', os.path.join(C, 'endlines.json')], check=True, env=env)

# ---------- film ----------
film = os.path.join(TOP, 'film.mp4')
cmd = ['ffmpeg', '-y', '-loglevel', 'error',
       '-loop', '1', '-framerate', '24', '-t', '3', '-i', os.path.join(C, 'title.jpg'),
       '-i', os.path.join(C, 'scene.mp4'),
       '-loop', '1', '-framerate', '24', '-t', '3', '-i', os.path.join(C, 'end.jpg'),
       '-i', os.path.join(C, 'sound.wav'),
       '-filter_complex', '[0:v]format=yuv420p,setsar=1,fade=t=in:st=0:d=0.5,fade=t=out:st=2.6:d=0.4[a];[1:v]format=yuv420p,setsar=1[b];[2:v]format=yuv420p,setsar=1,fade=t=in:st=0:d=0.4[c];[a][b][c]concat=n=3:v=1:a=0[v]',
       '-map', '[v]', '-map', '3:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-maxrate', '5M', '-bufsize', '10M', '-pix_fmt', 'yuv420p', '-r', '24',
       '-c:a', 'aac', '-b:a', '128k', '-t', '38', '-movflags', '+faststart', film]
subprocess.run(cmd, check=True)
probe = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames,codec_name,width,height', '-show_entries', 'format=duration,size', '-of', 'json', film], capture_output=True, text=True).stdout
pj = json.loads(probe); vs = pj['streams'][0]
info = {'frames': int(vs['nb_read_frames']), 'codec': vs['codec_name'], 'size_mb': round(int(pj['format']['size']) / 1e6, 2), 'duration': float(pj['format']['duration'])}
print('film', info)
assert info['frames'] == 912 and info['size_mb'] <= 12, info

# ---------- trace (measured) ----------
frames = []; prev = 1
for k, m in enumerate(M):
    sf = SCORE['frames'][k]
    hx, tx = (m['snout_px'] or [None])[0], (m['skull_px'] or [None])[0]
    if hx is not None and tx is not None:
        d = hx - tx; facing = 1 if d < -3 else -1 if d > 3 else prev
    else: facing = prev
    prev = facing
    ty = m['torso_y_world']; posture = 'lying' if ty is not None and ty < 0.25 else 'standing' if ty is not None and ty > 0.3 else 'between'
    frames.append({'i': k, 't': sf['t'], 'state': sf['dog']['state'], 'x_score': sf['dog']['x'], 'x_screen': m['x_screen'], 'y_screen': m['y_screen'],
                   'x_world_measured': m['x_world_measured'], 'facing': facing, 'facing_measure': 'snout centroid vs skull centroid', 'posture': posture,
                   'head_below_back': (m['head_y_world'] is not None and m['back_top_y_world'] is not None and m['head_y_world'] < m['back_top_y_world'] - 0.02),
                   'head_x_world': m['head_x_world'], 'head_y_world': m['head_y_world'], 'back_top_y_world': m['back_top_y_world'], 'torso_y_world': ty, 'bbox': m['bbox']})

def first(pred, after):
    for f in frames:
        if f['t'] >= after and pred(f): return f['t']
    return None
def mean(key, a, b):
    v = [f[key] for f in frames if a <= f['t'] <= b and f[key] is not None]; return sum(v) / len(v)
x0 = mean('x_world_measured', 0.0, 0.9)
on = {}
on['retreat'] = first(lambda f: f['x_world_measured'] - x0 > 0.02, 0.5)
for k, f in enumerate(frames): f['_hy'] = sum(g['head_y_world'] for g in frames[max(0, k - 2):k + 3]) / len(frames[max(0, k - 2):k + 3])
hmin = min(f['_hy'] for f in frames if 1.5 <= f['t'] <= 2.6)
on['watch_after_retreat'] = first(lambda f: f['_hy'] > hmin + 0.04, 2.0)
for f in frames: del f['_hy']
h0 = mean('head_x_world', 3.0, 3.3); on['refuse'] = first(lambda f: f['head_x_world'] - h0 > 0.03, 3.0)
on['refuse_back_shown'] = first(lambda f: f['facing'] == -1, 3.3)
h1 = mean('head_x_world', 7.0, 7.3); on['watch_turns_back'] = first(lambda f: h1 - f['head_x_world'] > 0.03, 7.0)
on['watch_head_toward_door'] = first(lambda f: f['facing'] == 1, 7.3)
xa = mean('x_world_measured', 14.0, 14.6); on['approach'] = first(lambda f: xa - f['x_world_measured'] > 0.02, 14.0)
ty0 = mean('torso_y_world', 23.3, 23.7); on['lie_down'] = first(lambda f: ty0 - f['torso_y_world'] > 0.02, 23.5)
hl = mean('head_x_world', 26.0, 26.35); on['looks_in'] = first(lambda f: hl - f['head_x_world'] > 0.02, 26.2)
score_t = {'retreat': 1.0, 'watch_after_retreat': 2.333, 'refuse': 3.417, 'refuse_back_shown': 3.417, 'watch_turns_back': 7.458, 'watch_head_toward_door': 7.458, 'approach': 14.708, 'lie_down': 23.792, 'looks_in': 26.4}
onsets = {k: {'measured_t': v, 'score_t': score_t[k], 'dt': None if v is None else round(v - score_t[k], 3)} for k, v in on.items()}
appr = [f for f in frames if 15.2 <= f['t'] <= 23.6]
hb = sum(f['head_below_back'] for f in appr) / len(appr)
lie_end = frames[-1]
summary = {'onsets': onsets, 'head_below_back_share_approach_15.2_23.6': round(hb, 3),
           'end_head_x_world': lie_end['head_x_world'], 'end_posture': lie_end['posture'],
           'min_head_x_world_looking_in': min(f['head_x_world'] for f in frames if 26.4 <= f['t'] <= 28.5),
           'film': info, 'voices': json.load(open(os.path.join(C, 'voice_levels.json')))}
trace = {'about': 'SCION 13 · Secondary Motion. Per scene frame, measured from a mask pass of the drawn dog (the same geometry drawn into the film, rasterised at 320x180 in three groups: torso, head, limbs). x_screen/y_screen: dog pixel centroid; x_world_measured: that centroid unprojected through the (moving) camera onto the dog path plane Z=0, metres along the porch; facing: +1 when the head centroid is left of the torso centroid (toward the door), -1 when right (its back to the door); posture from the torso centroid height; head_below_back: head centroid below the top of the torso mask. state and x_score are copied from the score.',
         'facing_convention': '+1 toward the door (left on screen), -1 away', 'measured': summary, 'frames': frames}
json.dump(trace, open(os.path.join(TOP, 'trace.json'), 'w'))
json.dump(summary, open(os.path.join(C, 'summary.json'), 'w'), indent=1)
print(json.dumps(summary, indent=1))

# ---------- stills from the encoded film ----------
os.makedirs(os.path.join(TOP, 'stills'), exist_ok=True)
for t in (3.6, 9.0, 19.0, 28.0):
    n = round((t + 3) * 24)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', film, '-vf', f'select=eq(n\\,{n})', '-vframes', '1', '-q:v', '3', os.path.join(TOP, 'stills', f'still_{t:04.1f}s.jpg')], check=True)
subprocess.run(['python3', os.path.join(ROOT, 'tools/paeleo/check_handmade.py'), TOP], check=True)
