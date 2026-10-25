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
    about = {
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
