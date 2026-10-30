"""Export the depth scene graph (planes, depths, parallax ratios, camera path, focus curve) and assets.json."""
import os, json
import numpy as np
from common import *
import world

FOUND = json.load(open(os.path.join(KIT, 'found-frames.json')))
META = {}
for s in FOUND:
    META[s['category']] = {'title': s['source_title'], 'url': s.get('source_url'), 'clip_id': s.get('clip_id'), 'rights': s['rights']}
DOGSRC = json.load(open(os.path.join(KIT, 'archive-dog/source.json')))['source']
DOORSRC = json.load(open(os.path.join(KIT, 'archive-door/source.json')))['source']


def meta_for(path):
    if '/archive-dog/' in path:
        return {'title': DOGSRC['source_title'], 'url': DOGSRC['original_source_url'], 'clip_id': DOGSRC['clip_id'], 'rights': DOGSRC['rights_statement']}
    if '/archive-door/' in path:
        return {'title': DOORSRC['source_title'], 'url': DOORSRC['original_source_url'], 'clip_id': DOORSRC['clip_id'], 'rights': DOORSRC['rights_statement']}
    for cat in META:
        if f'/shots/{cat}-sam/' in path:
            return META[cat]
    return None


def main():
    planes = world.build()
    graph = []
    cam0, _ = camera(0)
    for p in planes:
        e = {'name': p['name'], 'kind': p['kind'], 'fog': p.get('fog', 0), 'interior': bool(p.get('interior'))}
        if p['kind'] == 'card':
            e['Z_m'] = p['Z']; e['rect_m'] = p['rect']
            e['parallax_ratio_vs_wall_at_t0'] = round((0 - cam0[2]) / (p['Z'] - cam0[2]), 4)
        elif p['kind'] == 'quad':
            e['corners_m'] = p['corners']
        else:
            e['hinge'] = 'x=-0.46, swings into the room: 46 deg (ajar) -> 102 deg (open) from 6.2 s'
        e['image_px'] = list(p['img'].shape[:2][::-1])
        graph.append(e)
    track = []
    for i in range(0, N, 6):
        c, fz = camera(i / FPS)
        track.append({'t': round(i / FPS, 3), 'cam': [round(float(v), 4) for v in c], 'focus_z': round(fz, 3)})
    json.dump({'about': 'SCION 44 depth scene graph. World metres: X along the porch (= score x), Y up, Z depth (wall at 0, room > 0, '
                        'railing at -2.1). The camera only translates, looking +Z; f = %g px at 1280x720. Cards are parallel to the '
                        'film (parallax = f/(Z-cz)); quads are mapped by their own homography. The dog and the person are stacks of '
                        'pieces at their own depths (build/dog.py, build/person.py).' % F_PX,
               'planes': graph, 'camera_keys': CAM_KEYS, 'camera_track': track},
              open(os.path.join(FOLDER, 'proof', 'scene_graph.json'), 'w'), indent=1)
    import render
    assets = []
    for key, u in world.USED.items():
        src = u['src']
        m = meta_for(src)
        if key == 'quickdraw-moon':
            assets.append({'id': 'moon', 'what': 'the moon in the sky plane', 'source': {'path': src, 'key_id': u['key_id'],
                           'title': 'Quick, Draw! dataset (moon)', 'credit': 'Google Creative Lab and contributors'},
                           'rights': 'CC BY 4.0', 'operation': 'strokes filled as a polygon, cut as pale paper, glow'})
            continue
        assets.append({'id': key, 'what': 'plane fragment', 'source': {'path': src, 'box_xyxy': u['box'], **(m or {})},
                       'rights': (m or {}).get('rights', 'unknown'), 'operation': ', '.join(sorted(u['ops'])),
                       'used_in': 'world.py planes'})
    for name, (f, box, col, con) in render.TEX_SRC.items():
        m = meta_for(f)
        assets.append({'id': f'piece-texture-{name}', 'what': f'collage texture for the {"dog" if name in ("flank","saddle","chest","leg","face","muzzle","black","eye") else "person"} pieces: {name}',
                       'source': {'path': f, 'box_xyxy': list(box), **(m or {})}, 'rights': (m or {}).get('rights', 'unknown'),
                       'operation': 'crop, ' + ('luminance re-graded into a colour, contrast ' + str(con) if col else 'colour kept') + ', paper grain, mirror-tile; cut by the piece outline (seeded scissor jitter), pale cut rim, drop shadow'})
    assets += [
        {'id': 'dog-skeleton', 'what': 'the 3D skeleton the dog pieces are laid on (shoulder, hip, neck, head, legs, tail)', 'source': {'path': 'build/dog.py'},
         'rights': 'own work', 'operation': 'computed (acting curves from the score; foot planner; two-bone IK)'},
        {'id': 'person-profile', 'what': "the person's head: a cut-paper profile silhouette", 'source': {'path': 'build/render.py PROFILE'}, 'rights': 'own work', 'operation': 'drawn polygon, filled with the hair fragment'},
        {'id': 'casing-table-window', 'what': 'door casing, window frame and mullions, table', 'source': {'path': 'build/world.py'}, 'rights': 'own work', 'operation': 'drawn rectangles'},
        {'id': 'sound', 'what': 'all sound: formant-synthesized voice, wind, crickets, room hum and clock, door creak, cloth, dog nails, thumps, tail, sigh', 'source': {'path': 'build/sound.py'}, 'rights': 'own work', 'operation': 'synthesized; spatialized by camera'},
        {'id': 'fonts', 'what': 'card text', 'source': {'path': '/usr/share/fonts/truetype/dejavu'}, 'rights': 'DejaVu fonts licence (free)', 'operation': 'typeset'},
    ]
    json.dump({'about': 'Every asset of SCION 44 Multiplane Parallax: where it came from, its rights, and the operation that made it. All archive frames are public domain per kit/found-frames.json and kit/*/source.json.',
               'assets': assets}, open(os.path.join(FOLDER, 'assets.json'), 'w'), indent=1)
    bad = [a['id'] for a in assets if a['rights'] in ('unknown', None)]
    print('assets', len(assets), 'unknown rights:', bad)


if __name__ == '__main__':
    main()
