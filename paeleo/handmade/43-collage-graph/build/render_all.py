"""render the 768 scene frames (parallel) + per-frame measurements of what was actually drawn"""
import json, os, sys
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'cache/frames'); MEAS = os.path.join(HERE, 'cache/meas')
os.makedirs(OUT, exist_ok=True); os.makedirs(MEAS, exist_ok=True)


def job(i):
    import scene
    im, meta = scene.render(i)
    im.save(os.path.join(OUT, 's%04d.jpg' % i), quality=92)
    d = meta['dog']; g = d['g']
    m = dict(i=i, t=g['t'], state=g['state'], x_score=g['x'], mode=g['mode'], head=g['head'][0] if g['mode'] == 'graph' else g['whole'][0],
             head_mirror=g['head_mirror'], lie=g['lie'], crouch=g['crouch'], rules=g['rules'], facing_measured=d.get('facing_measured'),
             nose=d.get('nose'), neck=d.get('neck'), withers=d.get('withers'), materials=d.get('materials'), split=d.get('split', False),
             planted=d.get('planted'), meas=d.get('meas'), gy=d['gy'], muzzle_angle_deg=d.get('muzzle_angle_deg'), person_bbox=meta['person'].get('bbox'),
             nodes=[(e['node'], e['frag']) for e in meta['log']], door=meta['door'], voice=scene.voice_at(scene.FRAMES[i]['t'])[0])
    json.dump(m, open(os.path.join(MEAS, '%04d.json' % i), 'w'))
    return i


if __name__ == '__main__':
    frames = list(range(768)) if len(sys.argv) < 2 else [int(a) for a in sys.argv[1:]]
    with Pool(int(os.environ.get('NPROC', 3))) as p:
        for k, i in enumerate(p.imap_unordered(job, frames, chunksize=8)):
            if k % 100 == 0: print('frame', k, flush=True)
    print('rendered', len(frames))
