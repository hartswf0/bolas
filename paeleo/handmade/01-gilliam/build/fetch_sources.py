"""Archivist: copy every found frame this film uses into ../sources/, with its SAM masks and provenance.
Everything downstream reads only from ../sources/ (and the score)."""
import json, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                     # 01-gilliam
KIT = os.path.abspath(os.path.join(ROOT, '..', 'kit'))
SHOTS = '/home/user/hartswf0/secondhand-motion/shots'
OUT = os.path.join(ROOT, 'sources')

found = {s['category']: s for s in json.load(open(os.path.join(KIT, 'found-frames.json')))}

USE = {
    # name: (frames dir, masks.json, frames used, provenance dict)
    'dog':       (os.path.join(KIT, 'archive-dog'), [0, 8, 20], None),
    'door':      (os.path.join(KIT, 'archive-door'), [0, 12, 16, 31], None),
    'face':      (os.path.join(SHOTS, 'face-sam'), [6, 12, 18], found['face']),
    'hand':      (os.path.join(SHOTS, 'hand-sam'), [10], found['hand']),
    'butterfly': (os.path.join(SHOTS, 'butterfly-sam'), [0, 15, 60], found['butterfly']),
    'lantern':   (os.path.join(SHOTS, 'lantern-sam'), [30], found['lantern']),
    'cloud':     (os.path.join(SHOTS, 'cloud-sam'), list(range(0, 62, 6)), found['cloud']),
}

manifest = {}
for name, (d, frames, prov) in USE.items():
    od = os.path.join(OUT, name)
    os.makedirs(od, exist_ok=True)
    masks = json.load(open(os.path.join(d, 'masks.json')))
    sub = {}
    for f in frames:
        src = os.path.join(d, 'frames', 'f%03d.jpg' % f)
        shutil.copyfile(src, os.path.join(od, 'f%03d.jpg' % f))
        sub[str(f)] = masks.get(str(f), [])
    json.dump(sub, open(os.path.join(od, 'masks.json'), 'w'))
    if prov is None:
        sj = json.load(open(os.path.join(d, 'source.json')))
        s = sj.get('source', sj)
        prov = {'source_title': s['source_title'], 'clip_id': s['clip_id'],
                'rights': s['rights_statement'], 'source_url': s['original_source_url'],
                'shot_page_url': s.get('shot_page_url')}
    if name == 'dog':
        shutil.copyfile(os.path.join(d, 'pose_agent_v8.json'), os.path.join(od, 'pose_agent_v8.json'))
    manifest[name] = {**prov, 'from': d, 'frames': frames}
json.dump(manifest, open(os.path.join(OUT, 'sources.json'), 'w'), indent=1)
print('copied', {k: len(v['frames']) for k, v in manifest.items()})
