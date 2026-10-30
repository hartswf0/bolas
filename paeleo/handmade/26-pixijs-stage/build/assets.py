"""SCION-26 · assets.json: every asset in film.mp4, where it came from, rights, operation. Per-fragment provenance
(source file, frame, crop box) is in build/atlas/atlas.json; this file groups it by source shot."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); FOLDER = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(FOLDER, '../../..'))
A = json.load(open(os.path.join(HERE, 'atlas/atlas.json')))
FOUND = {s['category']: s for s in json.load(open(os.path.join(ROOT, 'paeleo/handmade/kit/found-frames.json')))}
dogsrc = json.load(open(os.path.join(ROOT, 'paeleo/handmade/kit/archive-dog/source.json')))['source']
USE = {
    'dog': 'dog coat (torso, neck, legs, head, tail): small patches cut inside the SAM dog mask',
    'lion': 'pale fur: chest, legs, muzzle, paws; the person neck',
    'cat': 'the person hair (head fragments)',
    'tiger': 'dark fragments: the dog ears, nose; leaves in the foreground; the person feet',
    'door': 'coat patches (the coats hanging beside the door) -> the person; the door leaf (whole cut-out, warped as a 2-triangle mesh)',
    'cloud': 'sky patches and three cloud-bank cut-outs at dusk',
    'star': 'star cut-outs in the sky',
    'horse': 'weathered fence-rail strips -> clapboards, porch boards, sill, trim, rail, crate',
    'ladder': 'ladder-pole strips -> boards',
    'hand': 'the offered hand (whole cut-out, mirrored)',
    'lantern': 'the lantern on the table inside',
    'windmill': 'the framed picture on the inside wall',
}
groups = {}
for name, f in A['frames'].items():
    sh = f.get('shot')
    if sh: groups.setdefault(sh, []).append((name, f))
assets = []
for sh, L in sorted(groups.items()):
    if sh == 'dog':
        src = dict(source_title=dogsrc['source_title'], collection=dogsrc['original_collection'], archive_url=dogsrc['original_source_url'],
                   shot_page=dogsrc['shot_page_url'], clip_id=dogsrc['clip_id'], rights=dogsrc['rights_statement'], kit='paeleo/handmade/kit/archive-dog/')
    else:
        s = FOUND[sh]; src = dict(source_title=s['source_title'], archive_url=s.get('source_url'), clip_id=s.get('clip_id'), rights=s['rights'], kit='/home/user/hartswf0/secondhand-motion/shots/%s-sam/' % sh)
    ops = sorted({f['op'] for _, f in L}); masks = sorted({f['mask'] for _, f in L})
    assets.append(dict(id='frag-' + sh, what=USE.get(sh, sh), n_atlas_frames=len(L), atlas_frames=[n for n, _ in L][:400],
                       source_frames=sorted({f['frame'] for _, f in L}), operation=ops, mask=masks, **src))
qd = [json.loads(l) for l in open(os.path.join(HERE, 'atlas/quickdraw_used.ndjson'))]
assets.append(dict(id='quickdraw-chalk', what='chalk lines: moon, trees, fence (backdrop), dog doodles pinned on the inside wall',
                   drawings=[dict(atlas_frame=d['name'], word=d['word'], key_id=d['key_id'], countrycode=d.get('countrycode')) for d in qd],
                   source='Quick, Draw! dataset (kit/quickdraw/quickdraw.ndjson and /home/user/hartswf0/quickdraw/<category>.part)',
                   rights='CC BY 4.0, Google Creative Lab and contributors', operation='stroke raster as chalk line, tinted', copy='build/atlas/quickdraw_used.ndjson'))
assets.append(dict(id='synth-sprites', what='soft disc, hard disc (eyes), white square', operation='synthesized in build/atlas.py', rights='own work'))
assets.append(dict(id='computed-geometry', what='sky gradient bands, yard gradient, room flat colours, table, window frame, door-opening mask, floor light polygon (lamp projected through the opening), porch edge', operation='PIXI.Graphics computed in build/engine.js', rights='own work'))
assets.append(dict(id='sound', what='formant-synthesized voice (Come here / Come on / It\'s all right / Come in), wind and crickets, warm room chord, door latch and creak, paws on boards timed to the rendered foot contacts, steps, crate, lying-down thump, sighs', operation='synthesized, build/sound.py (numpy)', rights='own work'))
assets.append(dict(id='engine', what='PixiJS 7.4.2', licence='MIT', source='npm pixi.js@7.4.2 (installed into build/node_modules, deleted after build)', operation='runtime'))
assets.append(dict(id='fonts', what='Big Shoulders Display, Literata, JetBrains Mono (title and end cards)', source='tools/paeleo/fonts/', rights='SIL Open Font License'))
json.dump(dict(about='SCION-26 assets, grouped by source shot. THE PER-FRAGMENT PROVENANCE RECORD IS build/atlas/atlas.json (kept in this folder): for every one of the atlas frames it gives the source file, shot, frame index, crop box in source pixels, mask rule and operation. Atlas frame names are <class>_<nnn> (fur_dog, fur_lion, fur_cat, dark, coat, sky, star, wood) or named cut-outs (hand, lantern, doorleaf, picture, cloudbank_k, qd_*); the prefix maps to the assets below.', provenance_record='build/atlas/atlas.json', atlas='build/atlas/atlas.png (2048x2048, %d frames)' % len(A['frames']), assets=assets),
          open(os.path.join(FOLDER, 'assets.json'), 'w'), indent=1)
print('assets', len(assets))
