"""SCION 51 · assets.json: every asset, its source and rights, and the operation that made it."""
import json, os
from lib import OUT

inv = json.load(open(os.path.join(OUT, 'inventory.json')))['records']
cuts = json.load(open(os.path.join(OUT, 'cutting-score.json')))['cuts']
words = json.load(open(os.path.join(OUT, 'words.json')))['words']
used = {}
for c in cuts:
    for k in ('coat', 'eye', 'paw', 'room', 'door', 'interior', 'hand'):
        used.setdefault(c[k], set()).add(k)
for w in words:
    for r in w['letters_from']:
        used.setdefault(r, set()).add('letters')
used.setdefault('soft.person.coat', set()).add('person coat')
ops = {'coat': 'whole crop, luminance-normalised, duotone-tinted by the cut\'s temperature, mapped onto the dog\'s body in its rest-pose coordinates (pinned, turns with the body), multiplied by the steady 3D shading',
       'eye': 'whole crop mapped onto the eye spheres (spherical coordinates)', 'paw': 'whole crop mapped onto the paw spheres',
       'room': 'whole crop stretched across the facade plane (mirrored repeat), low contrast, under drawn clapboard lines',
       'door': 'whole crop on the inner face of the door leaf', 'interior': 'whole crop on the back and side walls of the lit room',
       'hand': 'whole crop on the offered hand', 'letters': 'glyph-shaped cut (Big Shoulders Display / Literata) filled with the crop, on a cut-paper chip',
       'person coat': 'crop tinted dark on the person\'s coat'}
assets = []
for r in inv:
    if r['id'] not in used:
        continue
    assets.append({'id': r['id'], 'what': f"{r['class']} image ({r['temperature']})", 'imagery_class': r['class'], 'temperature': r['temperature'],
                   'path': r['file'], 'original_path': r['original_path'], 'crop_norm': r['crop_norm'], 'source_title': r['source_title'],
                   'archive_url': r['source_url'], 'clip_id': r['clip_id'], 'shot': r['shot'], 'frame': r['frame'], 'rights': r['rights'],
                   'rights_basis': 'kit/found-frames.json lists this shot as public_domain (Internet Archive / Moving Image Archive)',
                   'used_as': sorted(used[r['id']]), 'operation': '; '.join(ops[u] for u in sorted(used[r['id']]))})
assets += [
    {'id': 'dog.body', 'what': 'the dog: 165 spheres (torso, neck, skull, muzzle, nose, eyes, ears, tail, four two-bone legs, paws) built in build/lib.py',
     'source_title': 'made here', 'rights': 'own work', 'operation': 'constructed; posed per frame from the score (build/choreo.py); ray-cast with depth (build/render.py); dark contour and depth-break lines drawn from the depth buffer'},
    {'id': 'person.body', 'what': 'the person: spheres, built in build/lib.py', 'source_title': 'made here', 'rights': 'own work', 'operation': 'constructed and posed'},
    {'id': 'porch.house', 'what': 'porch floor planks, sill, facade planes, door frame, door leaf, lit room', 'source_title': 'made here', 'rights': 'own work',
     'operation': 'planes ray-cast per pixel; floor planks and clapboard lines synthesized; light pool computed through the door opening'},
    {'id': 'sound', 'what': 'voices (formant synthesis), cut grains, footfalls, door creak, breath, room tone', 'source_title': 'made here (build/sound.py)', 'rights': 'own work', 'operation': 'synthesized'},
    {'id': 'fonts', 'what': 'Big Shoulders Display, Literata, JetBrains Mono (tools/paeleo/fonts)', 'source_title': 'Google Fonts', 'rights': 'SIL Open Font License 1.1',
     'operation': 'glyph shapes used as cutting templates for the letters; card text'},
    {'id': 'score', 'what': 'paeleo/handmade/score/threshold-score.json', 'source_title': 'PAELEO machine', 'rights': 'project', 'operation': 'read: positions, act channels, timeline'},
]
not_used = ['kit/archive-dog (no frame used)', 'kit/archive-door (no frame used)', 'kit/quickdraw and /home/user/hartswf0/quickdraw (no drawing used)',
            'the Academy Film Archive Caroline and Frank Mouris Collection (not viewed, not accessible here; no footage, still or title from it used)']
json.dump({'about': 'SCION 51 assets. Every image is a whole crop from one public-domain frame, copied unchanged into sources/. '
           'Imagery classes and temperatures are in inventory.json; where and when each is used is in cutting-score.json and words.json.',
           'assets': assets, 'not_used': not_used}, open(os.path.join(OUT, 'assets.json'), 'w'), indent=1)
print(len(assets), 'assets')
