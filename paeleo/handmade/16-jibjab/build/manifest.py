"""SCION 16 JibJab: the matte manifest. Timecoded spans of what the face slot showed and how it was occluded, measured
from the render (build/cache/measure-paper.json), plus the paw contacts the stepping solver planted."""
import json, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = json.load(open(os.path.join(HERE, 'build/cache/measure-paper.json')))
P = json.load(open(os.path.join(HERE, 'performance.json')))
spans = []
for m in M:
    key = (m['view'], m['headBehind'])
    if spans and spans[-1]['key'] == key: spans[-1]['i1'] = m['i']
    else: spans.append({'key': key, 'i0': m['i'], 'i1': m['i']})
out = {'about': 'Face slot view and occlusion order per span of scene frames (24 fps), measured from the paper-cast render; '
                'views: L profile, BL three-quarter from behind, B back of head; ~ = mirrored. head_behind_torso: the head layer '
                'was composited under the body plate (the head faces away). The collar (neck matte) is always over the seam.',
       'layers_in_order': ['sky/world', 'house, interior, door plate (clipped to the opening)', 'porch, light spill', 'person plate',
                           'dog contact shadow', 'head layer OR body layer (by occlusion)', 'body layer OR head layer', 'caption', 'grain'],
       'spans': [{'t0': round(s['i0'] / 24, 3), 't1': round((s['i1'] + 1) / 24, 3), 'frames': [s['i0'], s['i1']],
                  'view': s['key'][0], 'head_behind_torso': s['key'][1]} for s in spans],
       'contacts': [e for e in P['events'] if e['e'] == 'paw']}
json.dump(out, open(os.path.join(HERE, 'matte-manifest.json'), 'w'), indent=1)
print(len(out['spans']), 'spans', len(out['contacts']), 'contacts')
