"""SCION 20 · 08: assets.json — every asset, where it came from, its rights, and the operation that made it."""
import json, os
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = json.load(open(os.path.join(D, 'scene/library.json')))
A = []
for el, drs in LIB['elements'].items():
    for k, v in drs.items():
        A.append(dict(id=f'{el}/{k}', what=f'{el} drawing "{k}"' + (f" (view {v.get('view')})" if v.get('view') else ''), kind='drawing (vector, in the library)',
                      source_file='build/01_library.js', copied_to='scene/library.json', source_title='drawn in code by SCION 20', archive_url=None, key_id=None,
                      rights='original work made for this film (no third-party material)', operation='drawn: constructed from coordinates and curves written in code (catmull-rom outlines, tapered tubes, two-bone IK for legs)'))
A += [
    dict(id='palette', what='named colour styles, dusk and lamp palettes', kind='palette', source_file='build/01_library.js', copied_to='scene/palette.json', rights='original', operation='authored + graded in code'),
    dict(id='background', what='painted background: dusk sky, moon, hills, trees, porch, the room in cutaway, the wall in section, the sill', kind='background painting',
         source_file='build/background.js', rights='original', operation='painted in code: washes and gradients, then 90,000 gouache dabs sampling the wash'),
    dict(id='light', what='lamp glow, door spill, fireflies', kind='light node', source_file='build/background.js (drawLight)', rights='original', operation='synthesized per frame'),
    dict(id='sound', what='voice (formant synthesis), crickets, wind, pads on boards, steps, stool, door latch and creak, tail thumps, whine, sniff, sigh, music cue', kind='soundtrack',
         source_file='build/05_sound.py', rights='original', operation='synthesized in numpy/scipy from the track breakdown (scene/track.json); no recordings or samples'),
    dict(id='fonts', what='Big Shoulders Display, Literata, JetBrains Mono (title, subtitles, end card)', kind='font', source_file='tools/paeleo/fonts/ (read in place, not copied)',
         rights='SIL Open Font License (as shipped in the repo for PAELEO)', operation='typeset'),
]
json.dump(dict(credit='Everything you see and hear was made in code by SCION 20 for this film. No photographs, no archive footage, no Quick, Draw! drawings, no web images, no generative model.',
               not_used=['paeleo/handmade/kit/archive-dog', 'paeleo/handmade/kit/archive-door', 'paeleo/handmade/kit/quickdraw', '/home/user/hartswf0/quickdraw', 'found-frames.json shots',
                         'paeleo/threshold/stage.js', 'paeleo/scion/lenses.js'],
               counts=LIB['counts'], assets=A), open(os.path.join(D, 'assets.json'), 'w'), indent=1)
print('assets', len(A))
