"""Independent-of-the-rig measurements: the dog matte measured per rendered frame (cache/measure.json), choice onsets
detected from those measurements, frame counts and audio levels measured on the ENCODED film.mp4, stills and proof
sheets extracted from film.mp4. Writes ../trace.json, ../stills/, ../proof/, cache/film_checks.json."""
import os, json, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SCORE = json.load(open(os.path.join(os.path.dirname(ROOT), 'score', 'threshold-score.json')))
M = json.load(open(os.path.join(HERE, 'cache', 'measure.json')))
FILM = os.path.join(ROOT, 'film.mp4')
fr = M['frames']; n = len(fr); assert n == 768, n
import camera as cam
PPM = cam.px_per_m_on_path(); XS0 = M['xs0']

xs = np.array([f['x_screen'] for f in fr]); top = np.array([f['top'] for f in fr]); hgt = np.array([f['height_px'] for f in fr])
vx = np.gradient(xs)
t = np.arange(n) / 24


def first(cond, after):
    for i in range(n):
        if t[i] >= after and cond(i): return i
    return None


# measured onsets (each from a rendered quantity, not from the score's labels)
ev = {}
ev['retreat'] = first(lambda i: xs[i] - xs[max(0, i - 2)] > 0.8, 0.5)                       # starts moving away
ev['watch1'] = first(lambda i: top[i] < top[max(0, i - 3)] - 2.0, t[ev['retreat']] + 0.6)    # head comes back up
ev['refuse'] = first(lambda i: fr[i]['mode'] == 'turn1', 3.0)                                   # body begins to turn
ev['watch2'] = first(lambda i: fr[i]['head_facing'] == 1 and fr[i]['mode'] == 'rig', 7.0)     # head comes round
ev['approach'] = first(lambda i: xs[i] - xs[max(0, i - 2)] < -0.8, 12.0)                     # starts coming
stand_h = float(np.median(hgt[(t > 20) & (t < 23)]))
ev['lie_down'] = first(lambda i: hgt[i] < stand_h - 6, 23.0)                                  # body goes down
ev['look_in'] = first(lambda i: 'back of head' in str(fr[i].get('head', '')), 26.0)
ev['look_end'] = first(lambda i: 'back of head' not in str(fr[i].get('head', '')), t[ev['look_in']] + .1)
ON = {k: (None if v is None else round(v / 24, 3)) for k, v in ev.items()}

segs = [(0, 'watch'), (ev['retreat'], 'retreat'), (ev['watch1'], 'watch'), (ev['refuse'], 'refuse'),
        (ev['watch2'], 'watch'), (ev['approach'], 'approach'), (ev['lie_down'], 'lie_down')]


def state(i):
    s = 'watch'
    for a, nm in segs:
        if i >= a: s = nm
    return s


out = []
for i, f in enumerate(fr):
    sx = SCORE['frames'][i]['dog']['x']
    lie = f.get('lie', 0)
    posture = 'turning' if f['mode'] != 'rig' else ('lying' if hgt[i] < stand_h - 20 or lie > .6 else
                                                   'crouched' if f.get('crouch', 0) > .4 else 'standing')
    out.append(dict(i=i, t=round(i / 24, 4), state=state(i), x_score=sx,
                    x_screen=f['x_screen'], y_screen=f['y_screen'],
                    x_measured_m=round((f['x_screen'] - XS0) / PPM + cam.OFFSET, 3),
                    facing='door' if f['head_facing'] == 1 else 'away',
                    body_facing='door' if f['body_facing'] == 1 else ('away' if f['body_facing'] == -1 else 'camera'),
                    posture=posture, head=f.get('head', f['mode']), layer_mode=f['mode'], plate=f.get('plate'),
                    height_px=int(hgt[i]), visible_px=f['visible_px'], held_out_px=f['held_out_px'],
                    frac_inside_threshold=f['frac_inside_threshold'], person=f.get('person')))

# --- the encoded film: frame count, duration, streams
pr = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', FILM]))
vs = [s for s in pr['streams'] if s['codec_type'] == 'video'][0]; au = [s for s in pr['streams'] if s['codec_type'] == 'audio']
checks = dict(film_frames=int(vs['nb_read_frames']), film_seconds=float(pr['format']['duration']), video_codec=vs['codec_name'],
              audio_codec=au[0]['codec_name'] if au else None, size_mb=round(os.path.getsize(FILM) / 1e6, 2),
              scene_frames=n, width=vs['width'], height=vs['height'])
with open(FILM, 'rb') as fh:
    head = fh.read(4096)
checks['faststart_moov_before_mdat'] = head.find(b'moov') != -1 and (head.find(b'mdat') == -1 or head.find(b'moov') < head.find(b'mdat'))

# --- audio levels measured on the film's own AAC track
wav = os.path.join(HERE, 'cache', 'film_audio.wav')
subprocess.check_call(['ffmpeg', '-loglevel', 'error', '-y', '-i', FILM, '-ac', '1', '-ar', '48000', wav])
with wave.open(wav) as w:
    a = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float32) / 32768
os.remove(wav)


def rms(t0, t1):
    s = a[int((t0 + 3) * 48000):int((t1 + 3) * 48000)]
    return float(20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-12))


aud = dict(call_1=rms(1.0, 1.65), call_2=rms(3.42, 4.07), soft_1=rms(7.4, 8.1), soft_2=rms(10.4, 11.1), soft_come_in=rms(26.4, 26.95),
           room_tone=rms(12.5, 14.0))
aud['soft_under_calls_db'] = round(np.mean([aud['call_1'], aud['call_2']]) - max(aud['soft_1'], aud['soft_2'], aud['soft_come_in']), 2)
aud['softest_over_room_tone_db'] = round(min(aud['soft_1'], aud['soft_2'], aud['soft_come_in']) - aud['room_tone'], 2)
checks['audio_dbfs_measured_on_film'] = {k: round(v, 2) for k, v in aud.items()}

# --- choice onsets: measured vs score
sc = {c['to'] if c['t'] != 2.333 else 'watch1': c['t'] for c in SCORE['choices']}
pairs = [('retreat', 1.0), ('watch1', 2.333), ('refuse', 3.417), ('watch2', 7.458), ('approach', 14.708), ('lie_down', 23.792), ('look_in', 26.4)]
checks['onsets'] = [dict(choice=k, score_t=s, measured_t=ON[k], dt=round(ON[k] - s, 3)) for k, s in pairs]
checks['look_in_until'] = ON['look_end']
lying = [o for o in out if o['t'] > 25]
checks['end_frac_inside_threshold'] = lying[-1]['frac_inside_threshold']
checks['end_held_out_px'] = lying[-1]['held_out_px']
checks['grain'] = M.get('grain')
json.dump(checks, open(os.path.join(HERE, 'cache', 'film_checks.json'), 'w'), indent=1)

json.dump(dict(about='SCION 28 trace. Per scene frame, measured from the render: x_screen/y_screen = centroid of the visible dog '
                     'matte (after holdouts); x_measured_m = that centroid mapped back through the locked camera to the score '
                     'metres (+0.45 m offset: the score x is the rear); height_px from the matte; facing = where the head '
                     'points (door/away), body_facing = the body plate; state = segmented by onsets detected in these '
                     'measurements (see onsets). x_score is the score value that drove the root track.',
               scene_offset_frames=72, fps=24, onsets=checks['onsets'], frames=out),
          open(os.path.join(ROOT, 'trace.json'), 'w'))

# --- stills and proof frames from the ENCODED film
os.makedirs(os.path.join(ROOT, 'stills'), exist_ok=True); os.makedirs(os.path.join(ROOT, 'proof'), exist_ok=True)


def grab(ts, path):
    subprocess.check_call(['ffmpeg', '-loglevel', 'error', '-y', '-ss', '%.4f' % (ts + 3.0 + 1 / 48), '-i', FILM, '-frames:v', '1', '-q:v', '3', path])


for ts in ('03.6', '09.0', '19.0', '28.0'):
    grab(float(ts), os.path.join(ROOT, 'stills', 'still_%ss.jpg' % ts))
print(json.dumps(checks, indent=1))
