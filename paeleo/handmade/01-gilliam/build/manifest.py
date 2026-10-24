"""Archivist: write ../assets.json (cutout and substitution manifest + source ledger) from the cards and the sources."""
import json
from common import *

src = json.load(open(os.path.join(SRC, 'sources.json')))
cards = json.load(open(os.path.join(CACHE, 'cards.json')))
sounds = json.load(open(os.path.join(CACHE, 'sound_events.json')))
out = {'about': 'Every asset in SCION-01 (Gilliam) PAE-02. Each card is cut from a public-domain archive frame copied into '
                'sources/<name>/fNNN.jpg (with its SAM masks), engraved by luminance hatching (build/common.py:engrave), '
                'and placed on pivots by build/render.py. Drawn parts are marked as drawn.',
       'sources': {}, 'cards': [], 'drawn': [], 'sound': [], 'type': [], 'substitutions': []}
for k, v in src.items():
    out['sources'][k] = {'title': v['source_title'], 'clip_id': v.get('clip_id'), 'rights': v['rights'],
                         'archive_url': v['source_url'], 'shot_page_url': v.get('shot_page_url'),
                         'kit_or_shot_dir': v['from'], 'frames_used': v['frames'],
                         'local_copy': 'sources/%s/' % k}
for name, c in cards.items():
    s = c.get('source')
    out['cards'].append({'card': name, 'file': 'build/cache/%s.png' % name, 'size_px': c['size'],
                         'from': 'sources/%s/f%03d.jpg' % (s, c['frame']) if s and 'frame' in c else None,
                         'source_title': src[s]['source_title'] if s in src else None,
                         'archive_url': src[s]['source_url'] if s in src else None,
                         'rights': src[s]['rights'] if s in src else None,
                         'operation': c.get('op'), 'pivots_px': c['pivots']})
out['drawn'] = [
    {'what': 'sky gradient, field below the horizon, eave, porch boards and fascia, steps, door casing, sill slab',
     'operation': 'drawn: flat tones + noise engraved by the same hatching routine (render.py:hatched)', 'rights': 'made here'},
    {'what': 'dog eye highlight and nose dot; eye on the shouting mouth', 'operation': 'drawn on the cards (assets.py)', 'rights': 'made here'},
    {'what': 'tail scissor line, trouser scissor line, rounded head cut of the mouth card', 'operation': 'drawn cut lines over found pixels', 'rights': 'made here'},
    {'what': 'the rubber stamp NO on the back of the dog card', 'operation': 'drawn with Big Shoulders Display 900', 'rights': 'made here; font OFL'},
    {'what': 'light spill and doorway glow', 'operation': 'computed (blurred polygons, additive warm light)', 'rights': 'made here'},
]
out['type'] = [{'font': 'Big Shoulders Display (variable, 900), Literata Italic/Regular', 'from': 'tools/paeleo/fonts/*.woff2 (decompressed by build/fonts.py)',
                'rights': 'SIL Open Font License'}]
out['sound'] = [{'t_film': e['t_film'], 'sound': e['sound'], 'operation': 'synthesized with numpy (build/sound.py)', 'rights': 'made here'} for e in sounds]
out['substitutions'] = [
    {'when': 'scene 1.000-2.333 s (frames 24-55), the first command', 'what': "the dog's head is replaced by the Straight Talk door (card door_head)",
     'why': 'commanded, the dog shuts: the door it is called through becomes its face'},
    {'when': 'scene 1.0-2.3 s and 3.417-4.6 s, the calls', 'what': "the woman's head is replaced by the shouting cartoon mouth (We Learn About the Telephone I), enlarged 2x",
     'why': 'the command is all mouth'},
    {'when': 'scene 3.417 s (frames 82-87)', 'what': 'the dog card turns over: its blank back with a rubber stamp NO',
     'why': 'the refusal is the cut-out showing its paper back'},
    {'when': 'scene 3.417-4.6 s', 'what': 'the arm becomes a telescope of repeated sleeve cards ending in The Door to Heaven hand', 'why': 'reaching = grabbing across the whole porch'},
    {'when': 'scene 6.8 s onward', 'what': 'the same found hand, laid low and still on the boards', 'why': 'the same fragment, different circumstance'},
    {'when': 'scene 7.4-11.6 s and 26.4-27.6 s', 'what': 'the soft voice is carried by the Insect Zoo butterfly (two mirrored wing cards)',
     'why': 'it goes to the dog, comes back, and finally flies in through the door: the dog looks after it'},
    {'when': 'background', 'what': "the cloud's own SAM outline reused as the hills at dusk", 'why': 'collage economy'},
]
json.dump(out, open(os.path.join(ROOT, 'assets.json'), 'w'), indent=1)
print('assets.json:', len(out['cards']), 'cards,', len(out['sound']), 'sounds')
