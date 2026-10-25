"""Merge the render's per-frame measurements into trace.json, measure the choice onsets from the render, write stills,
then mux title + scene + end with the synthesized sound into film.mp4."""
import glob, json, os, subprocess, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); C = os.path.join(HERE, 'cache'); OUT = os.path.join(HERE, '..')
SCORE = json.load(open(os.path.join(HERE, '../../score/threshold-score.json')))
FR = SCORE['frames']


def merge():
    tr = {}
    for p in sorted(glob.glob(os.path.join(C, 'trace_part_*.json'))):
        tr.update(json.load(open(p)))
    assert len(tr) == 768, len(tr)
    json.dump(tr, open(os.path.join(C, 'render_trace.json'), 'w'))
    return tr


def state_of(i, p):
    """the dog's state, read from what the render shows (pose chosen for that frame), not copied from the score"""
    post = p['posture']
    if post == 'back away':
        return 'retreat'
    if post in ('turn away', 'back turned', 'back turned, lying'):
        return 'refuse'
    if post in ('head lowers', 'walk head low'):
        return 'approach'
    if post in ('lying down', 'lie'):
        return 'lie_down'
    return 'watch'


def onsets(frames):
    """measured from the render: first frame of each visible change"""
    xs = np.array([f['x_screen'] for f in frames])
    m = {}
    # retreat: the dog's screen x starts increasing (moves away from the door, to the right)
    i = next(k for k in range(1, 768) if xs[k] - xs[0] > 1.0); m['retreat_motion_starts'] = frames[i]['t']
    i = next(k for k in range(i, 768) if all(abs(xs[j] - xs[j - 1]) < .3 for j in range(k, k + 6))); m['retreat_motion_stops'] = frames[i]['t']
    i = next(k for k in range(60, 768) if frames[k]['source_frame'] not in (None, 13) and frames[k - 1]['source_frame'] == 13); m['turn_away_first_new_frame'] = frames[i]['t']
    i = next(k for k in range(60, 768) if frames[k]['facing'] == -1); m['back_turned_first_frame'] = frames[i]['t']
    i = next(k for k in range(150, 768) if frames[k]['facing'] == 1 and frames[k - 1]['facing'] == -1); m['head_toward_door_again'] = frames[i]['t']
    i = next(k for k in range(300, 768) if xs[300] - xs[k] > 1.0); m['approach_motion_starts'] = frames[i]['t']
    i = next(k for k in range(300, 768) if frames[k]['source_frame'] in (14, 16) and frames[k - 1]['source_frame'] not in (14, 16) and k > 340)
    m['approach_head_lowers_first_frame'] = frames[i]['t']
    hts = np.array([f['dog_bottom'] - f['dog_top'] for f in frames])
    h0 = np.median(hts[500:560])
    i = next(k for k in range(560, 768) if frames[k]['source_frame'] is None); m['lie_sequence_first_frame'] = frames[i]['t']
    hl = np.median(hts[620:640])
    i = next(k for k in range(560, 768) if hts[k] <= hl + .5 * (hts[i] - hl)); m['lying_half_down'] = frames[i]['t']
    i = next(k for k in range(90, 180) if frames[k]['posture'] == 'back turned, lying'); m['refusal_lies_down_full'] = frames[i]['t']
    i = next(k for k in range(600, 768) if frames[k].get('looking_in')); m['looks_in_first_frame'] = frames[i]['t']
    i = next(k for k in range(i, 768) if not frames[k].get('looking_in')); m['looks_in_last_frame'] = frames[i - 1]['t']
    return m


def main():
    tr = merge()
    frames = []
    for i in range(768):
        r = tr[str(i)]; p = r['pose']
        frames.append(dict(i=i, t=round(i / 24., 4), state=state_of(i, p), x_score=FR[i]['dog']['x'],
                           x_screen=r['x_screen'], y_screen=r['y_screen'], facing=p['facing'], posture=p['posture'],
                           source_frame=p.get('f'), mirrored=p.get('m'), lie=p.get('L'), looking_in=bool(p.get('looking_in', False)),
                           dog_left=r['dog_left'], dog_right=r['dog_right'], dog_top=r['dog_top'], dog_bottom=r['dog_bottom'],
                           door_open=r['door_open']))
    door = SCORE['frames'][0]
    x0, x1 = 330 - 87, 330 + 87
    last = frames[-1]
    onset = onsets(frames)
    info = dict(about='SCION 31 Alpha Matting: what the dog did, measured from its own render. x_screen/y_screen = alpha-weighted '
                      'centroid of the dog matte as composited; dog_left..dog_bottom = its solid (alpha>0.5) extent on screen; '
                      'facing +1 = toward the door (screen left), -1 = back turned; state is read from the pose the render chose.',
                mapping='x_screen = 330 + 190 * x_score (camera static); while lying facing the door the matte is set 48 px further in',
                door_opening_screen_x=[x0, x1],
                end=dict(dog_left=last['dog_left'], dog_right=last['dog_right'], px_inside_frame=round(x1 - last['dog_left'], 1),
                         px_outside=round(last['dog_right'] - x1, 1)),
                onsets_measured=onset, frames=frames)
    json.dump(info, open(os.path.join(OUT, 'trace.json'), 'w'), indent=0)
    print(json.dumps(onset), json.dumps(info['end']))
    # stills
    os.makedirs(os.path.join(OUT, 'stills'), exist_ok=True)
    for t in (3.6, 9.0, 19.0, 28.0):
        Image.open(os.path.join(C, 'frames/s%04d.jpg' % round(t * 24))).save(os.path.join(OUT, 'stills/still_%04.1fs.jpg' % t), quality=90)
    if '--nofilm' in sys.argv:
        return
    subprocess.run([sys.executable, os.path.join(HERE, 'sound.py')], check=True)
    lst = os.path.join(C, 'seq.txt')
    with open(lst, 'w') as f:
        for k in range(72): f.write("file 'cards/t%03d.jpg'\nduration 0.0416667\n" % k)
        for k in range(768): f.write("file 'frames/s%04d.jpg'\nduration 0.0416667\n" % k)
        for k in range(72): f.write("file 'cards/e%03d.jpg'\nduration 0.0416667\n" % k)
        f.write("file 'cards/e071.jpg'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
                    '-f', 'lavfi', '-t', '3', '-i', 'anullsrc=r=48000:cl=stereo', '-i', os.path.join(C, 'scene.wav'),
                    '-f', 'lavfi', '-t', '3', '-i', 'anullsrc=r=48000:cl=stereo',
                    '-filter_complex', '[1:a][2:a][3:a]concat=n=3:v=0:a=1[a]', '-map', '0:v', '-map', '[a]',
                    '-r', '24', '-frames:v', '912', '-c:v', 'libx264', '-preset', 'slow', '-crf', '25', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', '-t', '38', os.path.join(OUT, 'film.mp4')], check=True)
    print('film ok')


if __name__ == '__main__':
    main()
