"""assets.json: every asset, where it came from, rights, and the operation that made it."""
import json, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = json.load(open(f'{HERE}/library/pose_library.json'))
SCHED = json.load(open(f'{HERE}/work/schedule.json'))
used = {}
for r in SCHED['frames']:
    used.setdefault(r['key_id'], set()).add(r['flip'])
QD_RIGHTS = 'CC BY 4.0, Quick, Draw! dataset, Google Creative Lab and contributors (https://quickdraw.withgoogle.com/data)'
QD_URL = 'https://github.com/googlecreativelab/quickdraw-dataset'
assets = []
for e in LIB['dogs']:
    assets.append(dict(
        id=f"dog-{e['key_id']}", what=f"dog doodle: {e['note']}", kind='pose-library drawing',
        source_file='/home/user/hartswf0/quickdraw/dog.part', line_index=e['idx'], key_id=e['key_id'],
        countrycode=e['countrycode'], copied_to='library/dogs.ndjson', source_title='Quick, Draw! (category: dog)',
        archive_url=QD_URL, rights=QD_RIGHTS,
        label=dict(native_facing=e['face'], posture=e['posture'], head=e['head'], leg_spread=e['spread'],
                   face_to_viewer=e['viewer'], rest=e['rest']),
        used_on_screen=e['key_id'] in used, mirrored_on_screen=bool(used.get(e['key_id']) and 1 in used[e['key_id']]),
        operation='selected by eye from contact sheets; strokes kept as drawn (simplified Quick, Draw! strokes); '
                  'placed by uniform scale + translation, mirrored when the decoder chose the mirror; swapped whole on twos'))
ops = {
    'house': 'uniform scale x2.8 + translation; its wall stroke also outlines the lit interior',
    'door': 'scaled (non-uniform) to the doorway rectangle; substituted ajar -> swinging -> open frame + panel',
    'moon': 'uniform scale + translation', 'face': "uniform scale + translation, the person's head",
    'hand': 'uniform scale + translation (reach: root at the shoulder; low: on the floor in the doorway)',
    'stairs': 'scaled (non-uniform) to the porch steps', 'fence': 'scaled (non-uniform) along the porch as rail and posts',
}
for s in LIB['set']:
    assets.append(dict(id=f"{s['category']}-{s['key_id']}", what=s['role'], kind='set doodle',
                       source_file=f"/home/user/hartswf0/quickdraw/{s['category']}.part", line_index=s['idx'],
                       key_id=s['key_id'], countrycode=s['countrycode'], copied_to='library/set.ndjson',
                       source_title=f"Quick, Draw! (category: {s['category']})", archive_url=QD_URL, rights=QD_RIGHTS,
                       operation=ops[s['category']] + '; drawn on in the maker\'s stroke order during the first 0.7 s'))
assets += [
    dict(id='person-body', what="the person's body lines (stand, going down, sit) and the arm to the low hand",
         kind='drawn', source='this swarm, build/04_render.py person_strokes()', rights='made here',
         operation='drawn as 4-5 straight strokes per posture with a fixed hand wobble (seeded, does not boil); substituted on twos'),
    dict(id='voice-marks', what='sound arcs at the mouth: 4 wide for a call, 2 small for soft speech', kind='drawn',
         source='build/04_render.py voice_marks()', rights='made here', operation='drawn arcs, pulse on twos'),
    dict(id='light-sky-floor', what='dusk gradient, fixed paper grain, porch fill, lit doorway/interior, warm glow',
         kind='computed', source='build/04_render.py', rights='made here', operation='numpy fields; lines inside the lit doorway turn dark'),
    dict(id='typed-prompts', what="the score's prompts, typed small at the bottom left", kind='text',
         source='paeleo/handmade/score/threshold-score.json', rights='PAELEO score', operation='JetBrains Mono (tools/paeleo/fonts, OFL)'),
    dict(id='fonts', what='Big Shoulders Display, JetBrains Mono, Literata (cards, prompts)', kind='font',
         source='/home/user/bolas/tools/paeleo/fonts/', rights='SIL Open Font License', operation='rendered with Pillow'),
    dict(id='sound', what='crickets, air, formant-synthesized voice syllables, paper flicks per drawing swap, pads, claws, '
         'flop, sighs, tail thumps, latch and creak, warm chords', kind='synthesized', source='build/05_sound.py (numpy)',
         rights='made here', operation='synthesized; placed on the score timeline and on the decoder\'s swap and footfall events'),
    dict(id='score', what='the PAELEO threshold score (dog state, x, acting, person, door, prompts)', kind='input',
         source='paeleo/handmade/score/threshold-score.json', rights='PAELEO', operation='read only'),
]
json.dump(dict(credit='Quick, Draw! drawings: Google Creative Lab and the people who drew them, CC BY 4.0. '
               'Each drawing keeps its key_id.', not_used=['paeleo/handmade/kit/archive-dog', 'paeleo/handmade/kit/archive-door',
               'paeleo/handmade/kit/quickdraw (the kit design doodle)', 'found-frames.json shots', 'stage.js / lenses.js'],
               assets=assets), open(f'{HERE}/assets.json', 'w'), indent=1)
print(len(assets), 'assets;', sum(a.get('used_on_screen', False) for a in assets), 'dog drawings on screen')
