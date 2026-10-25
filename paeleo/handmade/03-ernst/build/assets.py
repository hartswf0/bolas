"""SCION 03 Ernst · the rights ledger: every asset in the film, where it came from, its rights, and the operation."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KIT = json.load(open(os.path.join(ROOT, '..', 'kit', 'found-frames.json')))
SHOT = {s['category']: s for s in KIT}
FR = json.load(open(os.path.join(HERE, 'cache', 'fragments.json')))

ROLE = {
    'lion_head': 'the magistrate’s head (hybrid noun: person + lion) while the person commands, 0-5.45 s; its cut margin is shown (a pasted authority)',
    'lion_head_b': 'substitution partner of lion_head, alternated at 4 Hz while the person calls (the head “speaks” by substitution)',
    'lion_mask': 'the keystone over the door from 6.05 s (the same lion, now architecture); its cut margin fades: the seam concealed',
    'hand': 'the person’s right hand: pasted large and swelling while it reaches (3.4-4.6 s, margin shown), small and low when offered (6.8 s on, margin concealed)',
    'lantern': 'the lamp hanging in the hall, seen through the open door: where the light comes from',
    'mane': 'round 2: the dog\u2019s hybrid part. The lion\u2019s mane (the same frame as the magistrate\u2019s head, its face cut away with a disc) pasted round the dog\u2019s neck from the first call (1.0 s): hackles raised, white cut margin shown while it is commanded and refuses; it shrinks as trust grows and its margin fades as the dog lies across the sill (23.9-24.9 s): absorbed as the ruff of a couchant guardian under the keystone lion',
    'mane_r': 'the same mane, unmirrored, used when the dog faces away (the refusal)',
}

if __name__ == '__main__':
    assets = []
    for f in FR:
        s = SHOT[f['shot']]
        assets.append({
            'id': f['name'], 'what': ROLE[f['name']],
            'source_file': f['src'], 'kit_path': s['frames'] + '/f%03d.jpg' % f['frame'],
            'mask': s['frames'].replace('/frames', '/masks.json') + ' [frame %d]' % f['frame'],
            'source_title': s['source_title'], 'archive_url': s['source_url'], 'clip_id': s['clip_id'],
            'rights': s['rights'],
            'operation': 'cut by its SAM mask (crop %s), %sscaled x%.1f, tone-stretched, engraved with this swarm’s burin '
                         '(%s line system), outlined at the cut, white cut margin kept as a separate layer'
                         % (list(f['crop']), 'mirrored, ' if f['mirror'] else '', f['scale'],
                            'radial mane' if f['name'].startswith(('lion', 'mane')) else 'parallel, luminance-displaced'),
            'used_as': 'build/cache/frag_%s.npz' % f['name']})
    assets += [
        {'id': 'dog', 'what': 'the dog: a maquette of 27 typed primitives (round cones, ellipsoids): chest, loin, haunch, neck, skull, muzzle, nose, two eyes, two ears, four legs of three segments (upper, lower, paw), a four-segment tail',
         'source_file': 'build/dog.py', 'rights': 'made here (this swarm)', 'operation': 'drawn as geometry, posed from the score, paws by the step solver (build/gait.py), two-bone IK, ray-marched (build/sdf.py), engraved along the form (build/dogplate.py, build/burin.py)'},
        {'id': 'person', 'what': 'the person: a frock-coated mannequin of round cones and ellipsoids, own plain head shown once the lion has left',
         'source_file': 'build/person.py', 'rights': 'made here', 'operation': 'geometry posed from the score’s person circumstances; feet by the same step solver; ray-marched and engraved'},
        {'id': 'plate', 'what': 'porch boards, clapboard facade, door case, door and its four panels, sill, hall with papered wall, chair, window, fence, hedge, moon, steps, newel post',
         'source_file': 'build/plate.py', 'rights': 'made here', 'operation': 'projected world quads, each given its own engraved line system; the door swings and lets out light (build/plate.py door_layer, light_spill)'},
        {'id': 'sound', 'what': 'all sound: crickets, wind, formant voices (come here / here / it’s all right / come in), lion growl, paper rustles, stone knock, hinge and chair creaks, footfalls, sighs, tail knocks, the warm chord of the light',
         'source_file': 'build/sound.py', 'rights': 'made here (synthesized; no recordings)', 'operation': 'synthesized in numpy, cued from the score and from the step solver’s touchdown events'},
        {'id': 'fonts', 'what': 'Literata (captions, cards)', 'source_file': 'tools/paeleo/fonts/f27.woff2, f34.woff2, f41.woff2',
         'rights': 'Literata is published under the SIL Open Font License (Google Fonts); used as shipped in the repo', 'operation': 'converted to TrueType into build/cache (fonts.py)'},
        {'id': 'score', 'what': 'the dog’s decisions and the circumstances', 'source_file': 'paeleo/handmade/score/threshold-score.json',
         'rights': 'PAELEO (this repo)', 'operation': 'read only; drives the timeline (build/timeline.py)'},
    ]
    not_used = ['kit/archive-dog (looked at, not used: no lying or turned-back dog in it; the dog is built as a maquette instead)',
                'kit/archive-door (looked at, not used)', 'kit/quickdraw and Quick, Draw! categories (not used)']
    json.dump({'assets': assets, 'not_used': not_used,
               'rule': 'only rights-recorded material: public-domain archive frames from the kit’s found-frames list, and what this swarm made'},
              open(os.path.join(ROOT, 'assets.json'), 'w'), indent=1, ensure_ascii=False)
    print(len(assets), 'assets')
