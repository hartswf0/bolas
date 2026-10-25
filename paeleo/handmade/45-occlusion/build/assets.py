"""SCION 45 · Provenance: assets.json (every asset, its source, rights and the operation that made it) and the list of the
archive-dog frames actually composited (cache/cels_used.json), read back from the render records."""
import glob, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.abspath(os.path.join(HERE, '..'))
KIT = 'paeleo/handmade/kit'
SH = '/home/user/hartswf0/secondhand-motion/shots'


def used_cels():
    used = {}
    PART_SRC = {'head10': 10, 'torso10': 10, 'foreA10': 10, 'foreB10': 10, 'hind10': 10, 'headF': 28}
    for p in sorted(glob.glob(os.path.join(HERE, 'cache/records/r*.json'))):
        r = json.load(open(p))
        for part in r['dog']['parts']:
            m = re.match(r'cel(\d+)', part)
            n = int(m.group(1)) if m else next((v for k, v in PART_SRC.items() if part.startswith(k)), None)
            if n is not None:
                used.setdefault(n, set()).add('whole cel' if m else part.split(' ')[0])
    out = {str(k): sorted(v) for k, v in sorted(used.items())}
    json.dump(out, open(os.path.join(HERE, 'cache/cels_used.json'), 'w'), indent=0)
    return out


def main():
    used = used_cels()
    dog_src = json.load(open(os.path.join(HERE, '../../kit/archive-dog/source.json')))['source']
    A = []
    for n, how in used.items():
        A.append(dict(asset='dog cel %s' % n, kind='RGBA cel (the dog)', file='%s/archive-dog/frames/f%03d.jpg' % (KIT, int(n)),
                      matte='%s/archive-dog/masks.json["%s"] (SAM) x garbage matte in build/cels.py' % (KIT, n),
                      source_title=dog_src['source_title'], archive_url=dog_src['original_source_url'], collection=dog_src['original_collection'],
                      rights=dog_src['rights_statement'], used_as=how,
                      operation='mask (SAM polygon AND hand garbage matte), 0.7 px feather; ' +
                                ('composited whole; walk cels shown mirrored as a whole pose' if how == ['whole cel'] else
                                 'split into semantic sublayers by hand-authored holdout polygons (build/rig.py PARTS) and re-assembled by rotation about pivots') +
                                '; re-lit by the scene light pass (colour from luminance; no pixel painted)'))
    A += [
        dict(asset='hallway plate', kind='background plate (inside the door)', file='%s/archive-door/frames/f029.jpg' % KIT,
             source_title='Straight Talk', archive_url='https://archive.org/details/gov.ntis.ava19144vnb1', rights='public_domain',
             operation='crop x<372, luminance to a warm ramp, perspective-mapped to the back wall at D=-1.5 m'),
        dict(asset='door leaf', kind='RGBA card', file='%s/archive-door/frames/f016.jpg' % KIT, matte='%s/archive-door/masks.json["16"] (SAM quad)' % KIT,
             source_title='Straight Talk', archive_url='https://archive.org/details/gov.ntis.ava19144vnb1', rights='public_domain',
             operation='SAM quad rectified to a rectangle (PIL QUAD), then perspective-mapped to the swinging leaf; shaded by angle'),
        dict(asset='light bulb', kind='RGBA card', file='%s/light-bulb-sam/frames/f012.jpg' % SH, matte='masks.json["12"] (SAM)',
             source_title='Light Of Your Life B', archive_url='https://archive.org/details/LightOfYourL_2', rights='public_domain',
             clip_id='ccf9d371-1f80-5aa3-bb2a-2e720f1786f2', operation='mask, crop, scaled onto a drawn shelf inside'),
        dict(asset='hand', kind='RGBA card (the offered hand)', file='%s/hand-sam/frames/f010.jpg' % SH,
             matte='masks.json["10"] (SAM fingers) + hand-authored forearm polygon', source_title='Door to Heaven, The',
             archive_url='https://archive.org/details/DoortoHe1941', rights='public_domain', clip_id='0870ef3a-b328-5284-890b-3e1ac18057c1',
             operation='mask, crop, mirrored (fingers toward the dog), luminance re-lit warm by the doorway light pass'),
        dict(asset='sky', kind='background plate', file='%s/cloud-sam/frames/f030.jpg' % SH, source_title='Top Of The Cloud - Time Lapse (Wide Screen 16:9)',
             archive_url='https://archive.org/details/CEP391', rights='public_domain', clip_id='3a3663e4-7a6e-5277-8cf5-12e94237350c',
             operation='luminance remapped to a dusk ramp, slight parallax'),
        dict(asset='house, porch, sill, door casing, bench, porch post, tree line, interior floor and shelf', kind='drawn layers',
             file='build/scene.py', source_title='drawn by this swarm (procedural numpy/PIL)', rights='own work',
             operation='computed per frame from world geometry under the stage camera'),
        dict(asset='the person', kind='drawn holdout matte', file='build/person.py', source_title='drawn by this swarm', rights='own work',
             operation='capsule/polygon matte from a small joint set, rim-lit; only the hand is a found image'),
        dict(asset='light, shadow and depth passes', kind='computed passes', file='build/scene.py',
             source_title='computed', rights='own work', operation='doorway light through the leaf holdout, cast shadows of the actors, contact shadows, per-pixel depth for the dog, person and leaf'),
        dict(asset='voice', kind='synthesized speech', file='build/sound.py', source_title="flite (CMU) voice 'slt', run locally via ffmpeg's flite filter",
             rights='synthesized here; flite is free software (BSD-style licence)', operation='synthesized, re-timed, filtered, placed'),
        dict(asset='foley, dusk, room tone', kind='synthesized sound', file='build/sound.py', source_title='synthesized (numpy)', rights='own work',
             operation='noise/oscillator synthesis; the room is held out (low-passed, -14 dB) until the door opens'),
        dict(asset='fonts', kind='type', file='tools/paeleo/fonts/ (Big Shoulders Display, Literata, JetBrains Mono)', source_title='house fonts',
             rights='SIL Open Font License (as supplied in tools/paeleo/fonts)', operation='title and end cards'),
    ]
    json.dump({'assets': A, 'not_used': 'no Quick, Draw! drawings, no web images, no model-generated images, nothing of unknown rights'},
              open(os.path.join(F, 'assets.json'), 'w'), indent=1)
    print('assets', len(A), 'dog cels used', len(used))


if __name__ == '__main__':
    main()
