"""Write assets.json: every asset in the film, where it came from, its rights and the operation that made it.
python3 build/assets.py"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
FOLD = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(FOLD, '..', '..', '..'))
BANK = json.load(open(os.path.join(FOLD, 'bank', 'bank.json')))['drawings']
PATH = json.load(open(os.path.join(HERE, 'cache', 'path.json')))
used = set(PATH['summary']['drawings_used']) | {f['person'] for f in PATH['frames']}
src = json.load(open(os.path.join(ROOT, 'paeleo/handmade/kit/archive-dog/source.json')))['source']
REF = {'what': 'reference footage (looked at, not shown)', 'file': 'paeleo/handmade/kit/archive-dog/frames/f000.jpg .. f049.jpg',
       'source_title': src['source_title'], 'archive_url': src['original_source_url'], 'collection': src['original_collection'],
       'rights': src['rights_statement'],
       'operation': 'looked at in contact sheets (frames 0-48) to set the dog\'s build and markings (dark saddle, pale ring of ruff, pale legs, '
                    'pricked ears) and to see how this dog turns round (through a front view, head leading). No pixels, masks or rig keys '
                    'from the footage are used in any drawing.'}
items = [REF]
for k, d in BANK.items():
    m = d['meta']
    if m.get('flopped_from'):
        op = 'drawn: left-right flop of %s (a separate drawing for the other facing; turns never use flops as in-betweens)' % m['flopped_from']
    elif m.get('gait'):
        op = 'drawn on a gait chart: drawing %d of %d, paw targets set so a planted paw keeps its board; legs set by two-bone construction' % (m['gait']['k'], m['gait']['n'])
    else:
        op = 'drawn: hand-set construction (torso, neck, head, legs, tail, markings placed by hand in build/bank.py), ink and flat wash'
    items.append({'what': ('person drawing: ' if m.get('group') == 'person' else 'dog drawing: ') + k + (' - ' + m['note'] if m.get('note') else ''),
                  'file': 'bank/bank.json#' + k, 'group': m.get('group'), 'chosen_by_the_path': k in used,
                  'source_title': 'this film (SCION 14)', 'rights': 'made here', 'operation': op})
items += [
    {'what': 'porch, house wall, door and its swing, room seen through the door, window, bench, sky, moon, far trees, light and shadows',
     'file': 'build/scene.js', 'source_title': 'this film', 'rights': 'made here', 'operation': 'drawn with canvas paths each frame; the door angle and the light follow the score timeline'},
    {'what': 'sound: voice (formant synthesis), paws, body and tail on the boards, whine, sniff, sigh, door creak, latch, clock, room hum, crickets, room tone',
     'file': 'build/sound.py', 'source_title': 'this film', 'rights': 'made here', 'operation': 'synthesized; dog and step events taken from the decoded path'},
    {'what': 'the score: the dog\'s decision trace', 'file': 'paeleo/handmade/score/threshold-score.json', 'source_title': 'PAELEO machine (paeleo/threshold/machine.js)',
     'rights': 'Bolas project', 'operation': 'read: pose vectors (build/poses.py) with four recorded action edits'},
    {'what': 'fonts: Big Shoulders Display, Literata, JetBrains Mono', 'file': 'tools/paeleo/fonts/', 'source_title': 'Google Fonts',
     'rights': 'SIL Open Font License', 'operation': 'title card, spoken-line captions, end card'},
]
not_used = ['paeleo/handmade/kit/archive-door (looked at, not used)', 'paeleo/handmade/kit/quickdraw and /home/user/hartswf0/quickdraw (not used)',
            'paeleo/handmade/kit/found-frames.json shots (not used)', 'paeleo/threshold/stage.js, paeleo/scion/lenses.js (not imported)']
json.dump({'about': 'Assets of PAE-02 SCION 14 (Pose2Pose casting). Nothing fetched from the web; no generated images.',
           'assets': items, 'not_used': not_used}, open(os.path.join(FOLD, 'assets.json'), 'w'), indent=1)
print(len(items), 'assets')
