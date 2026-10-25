"""SCION 03 Ernst · assemble: trace.json from the render's own measurements, the frame sequence, the stills."""
import glob, json, os
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(HERE, 'cache')

if __name__ == '__main__':
    parts = []
    for p in sorted(glob.glob(os.path.join(CACHE, 'trace_parts', '*.json'))):
        parts += json.load(open(p))
    byi = {}
    for f in parts:
        byi[f['i']] = f
    frames = [byi[i] for i in sorted(byi)]
    assert len(frames) == 768, len(frames)
    # measured onsets: when the rendered dog visibly does each choice (from its own render, not from the state field)
    def first(cond, t0):
        return next((f['t'] for f in frames if f['t'] >= t0 and cond(f)), None)
    x0 = frames[12]['x_screen']
    def at(tq, key):
        return min(frames, key=lambda f: abs(f['t'] - tq))[key]
    def vel(f, k=2):
        i = f['i']; a = frames[max(0, i - k)]; b = frames[min(767, i + k)]
        return (b['x_screen'] - a['x_screen']) / (b['t'] - a['t'])
    on = {
        'retreat (backs away: x_screen rises 2 px)': first(lambda f: f['x_screen'] > x0 + 2, 0.5),
        'watch (stops backing: |v| < 25 px/s)': first(lambda f: abs(vel(f)) < 25, 2.0),
        'refuse (rendered head passes to the far side of the tail)': first(lambda f: f['facing'] == -1, 3.0),
        'watch (head starts coming round: head_x moves 3 px toward the door)': first(lambda f: f['head_x'] < at(7.4, 'head_x') - 3, 7.4),
        'approach (comes: x_screen falls 2 px)': first(lambda f: f['x_screen'] < at(14.0, 'x_screen') - 2, 14.0),
        'lie_down (rendered torso drops 3 cm)': first(lambda f: f['torso_h'] < at(23.5, 'torso_h') - 0.03, 23.5),
    }
    score_t = [1.0, 2.333, 3.417, 7.458, 14.708, 23.792]
    measured = [{'choice': k, 'score_t': st, 'measured_onset_t': v, 'dt': None if v is None else round(v - st, 3)}
                for (k, v), st in zip(on.items(), score_t)]
    about = {
        'measured_onsets': measured,
        'about': 'What the Ernst dog did, per scene frame, measured from its own render (fixed camera: x_screen is '
                 'the screen centre of the torso pixels of the engraved maquette; facing is +1 when the rendered head '
                 'is on the door side of the rendered tail; posture from the rendered torso height). state is the '
                 'score decision that drove the frame (copied, not measured). x_score is the score position.',
        'camera': 'fixed orthographic plate camera, 168 px/m, threshold x=0 at screen x=400, pitch 18 deg',
        'fields': {'x_screen': 'px', 'y_screen': 'px', 'torso_h': 'm above the boards (rendered)',
                   'head_h': 'm (rendered head centre)', 'back_h': 'm (rendered top of torso)',
                   'head_below_back': 'rendered head centre at least 8 cm below the top of the back',
                   'frac_in_frame': 'share of the dog pixels whose screen x lies inside the door opening',
                   'z_min': 'm, the deepest rendered point of the dog (negative = past the facade plane, in the reveal)'},
        'frames': frames}
    json.dump(about, open(os.path.join(ROOT, 'trace.json'), 'w'), indent=0)
    # the film's frame sequence: 3 s title, 32 s scene, 3 s colophon
    seq = os.path.join(CACHE, 'seq'); os.makedirs(seq, exist_ok=True)
    for f in glob.glob(os.path.join(seq, '*')):
        os.remove(f)
    k = 0
    def link(src):
        global k
        os.symlink(src, os.path.join(seq, 'f%05d.png' % k)); k += 1
    for _ in range(72):
        link(os.path.join(CACHE, 'card_title.png'))
    for i in range(768):
        link(os.path.join(CACHE, 'frames', 's%04d.png' % i))
    for _ in range(72):
        link(os.path.join(CACHE, 'card_end.png'))
    os.makedirs(os.path.join(ROOT, 'stills'), exist_ok=True)
    for t in ('03.6', '09.0', '19.0', '28.0'):
        i = int(round(float(t) * 24))
        Image.open(os.path.join(CACHE, 'frames', 's%04d.png' % i)).convert('RGB').save(
            os.path.join(ROOT, 'stills', 'still_%ss.jpg' % t), quality=92)
    print('trace', len(frames), 'seq', k)
