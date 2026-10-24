"""SCION-04 · assets.json: every archive shot the torrent drew from, with its source, rights and how often it was placed."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
L = json.load(open(os.path.join(HERE, 'cache/library.json')))
usage = json.load(open(os.path.join(OUT, 'trace.json')))['usage']
pools = L['pools']
def pools_of(cat, kit):
    key = 'dog-archive' if (kit and cat == 'dog') else 'door-archive' if (kit and cat == 'door') else cat
    return [p for p, cs in pools.items() if key in cs] + (['eye (dog\'s eye)'] if cat == 'eye' else []) + (['face (head)'] if cat in ('face', 'eye', 'hat') else []) + (['hand (hand)'] if cat == 'hand' else []) + (['moon'] if cat == 'light-bulb' else [])
assets = []
for s in L['shots']:
    kit = 'kit/' in s['dir']; name = s['category'] + ('(kit)' if kit else '')
    assets.append(dict(
        id=name, what=f'{s["n"]} archive frames ({s["category"]}) with SAM masks, cut into tiles',
        file=s['dir'] + ('/frames' if kit else ''), masks=(s['dir'] + '/masks.json') if kit else s['dir'].replace('/frames', '/masks.json'),
        source_title=s['source_title'], archive_url=s['source_url'], clip_id=s.get('clip_id'), rights=s['rights'],
        pools=pools_of(s['category'], kit), placements=usage.get(name, 0),
        operation='each frame cropped twice (whole frame; and the SAM-mask bounding box widened to 4:3), resized to 64x48/32x24/16x12/8x6 tiles; '
                  'placed by a quadtree into computed moulds; tile mean shifted to the mould\'s guide colour (contrast kept); held tiles play their own shot forward at 12 fps'))
assets += [
    dict(id='moulds', what='the shapes of the dog, person, door, porch, moon and the words', file='build/scene.py, build/02_render.py', rights='made here',
         operation='computed (drawn as polygons from the PAELEO score: dog act values, person posture/reach/low hand, door state); never shown directly, only filled with archive tiles'),
    dict(id='score', what='the dog decision trace', file='paeleo/handmade/score/threshold-score.json', rights='PAELEO, made in this program', operation='read only: drives every mould and every rate'),
    dict(id='fonts', what='Big Shoulders Display (COME HERE, title), Literata italic (it\'s all right, come in), JetBrains Mono (made-of card)', file='tools/paeleo/fonts/', rights='SIL Open Font License',
         operation='text rendered into moulds, then filled with archive tiles (spoken words); plain text on the cards'),
    dict(id='sound', what='all sound', file='build/04_sound.py', rights='made here', operation='synthesized with numpy: one click per replaced tile (from cache/stats.json), formant voice, stick-slip door creak, paw thumps from the score walk phase, breath noise, a sine chord, 24 Hz projector purr, crickets'),
    dict(id='glow', what='the warm glow of the doorway into the dusk', file='build/02_render.py', rights='made here', operation='computed screen-blend radial grade (not a picture); the light itself is lantern, bulb and star tiles'),
    dict(id='quickdraw', what='not used', file='paeleo/handmade/kit/quickdraw', rights='CC BY 4.0', operation='none'),
]
json.dump(dict(about='SCION-04 · Frank Mouris image torrent: every asset, its source and rights, and the operation that made it.', assets=assets), open(os.path.join(OUT, 'assets.json'), 'w'), indent=1)
print(len(assets), 'assets;', sum(a.get('placements', 0) for a in assets), 'placements')
