"""assets.json: every asset, where it came from, its rights, and the operation that made it."""
import os, json
HERE = os.path.dirname(os.path.abspath(__file__)); F = os.path.dirname(HERE)
DOG = {'source_title': 'Amateur Film New Jersey C', 'collection': 'Home Movies (Internet Archive)', 'archive_url': 'https://archive.org/details/NewJerseyC',
       'shot_url': 'https://www.movingimagearchive.com/sources/amateur-film-new-jersey-c-c65a8960?clip=2fdacde1-8a23-58e1-b905-5407385bd039', 'rights': 'public_domain'}
DOOR = {'source_title': 'Straight Talk (1992)', 'collection': 'NTIS', 'archive_url': 'https://archive.org/details/gov.ntis.ava19144vnb1',
        'shot_url': 'https://www.movingimagearchive.com/sources/straight-talk-583ba802?clip=271d80c7-4f56-51b8-90fe-012dfb984b4f', 'rights': 'public_domain'}
HAND = {'source_title': 'The Door to Heaven (1941)', 'archive_url': 'https://archive.org/details/DoortoHe1941', 'clip_id': '0870ef3a-b328-5284-890b-3e1ac18057c1',
        'rights': 'public_domain', 'kit_index': 'paeleo/handmade/kit/found-frames.json (category hand)'}
used = [0, 9, 10, 11, 13, 30, 34, 42, 43, 44, 45]
A = []
for i in used:
    role = {0: 'back-of-head piece (look in)', 13: 'puppet source: head, torso, two forelegs, hind legs, tail; also turn drawings',
            9: 'watch', 10: 'watch', 11: 'watch'}.get(i, 'walk (mirrored; reversed for the retreat)' if 42 <= i <= 45 else 'turn drawing')
    A.append(dict(DOG, asset='dog cut f%03d' % i, file='paeleo/handmade/kit/archive-dog/frames/f%03d.jpg' % i, piece='pieces/dog_f%03d.png' % i,
                  role=role, operation='graph cut (BK max-flow; seeds from kit SAM mask eroded/dilated, rig-key scribbles, belly-gap and tail scribbles; '
                  'unaries: intensity x texture x |frame - clean plate| histograms re-estimated 4x; contrast pairwise; 2x supersampled) -> alpha cleanup '
                  '(largest component, hole fill, border matte); mirrored / re-timed / re-posed in the film'))
A.append(dict(DOG, asset='clean plate of the dog shot', file='paeleo/handmade/kit/archive-dog/frames/f000..f049.jpg + camera.json + masks.json',
              piece='build/cache/plate/plate.png (regenerable)', operation='camera-registered median of all 50 frames with the dog (SAM dilated 10 px) excluded; '
              'used as a unary cue, as the porch boards (stretched, darkened) and as the far garden (blurred, darkened)'))
for n, fi, role, op in (('pillar', 6, 'stone of the façade (tiled, mirrored), jambs, lintel', 'box + scribble graph cut'),
                        ('shrub', 6, 'cut but not used in the final film', 'box + scribble graph cut'),
                        ('bowl', 6, 'cut but not used in the final film', 'box + scribble graph cut')):
    A.append(dict(DOG, asset=n, file='paeleo/handmade/kit/archive-dog/frames/f%03d.jpg' % fi, piece='pieces/%s.png' % n, role=role, operation=op))
A.append(dict(DOOR, asset='woman', file='paeleo/handmade/kit/archive-door/frames/f000.jpg', piece='pieces/woman_stand.png',
              role='the person: body, sleeve (shoulder pivot), lower cut (hips/thighs); a dusk silhouette, re-posed to reach, step aside and sit',
              operation='box + scribble graph cut (colour unaries); split by straight joint lines; repair: the last 24 rows (trousers) stretched as shins '
              'because the archive frame cuts her off below the knee'))
A.append(dict(DOOR, asset='door panel', file='paeleo/handmade/kit/archive-door/frames/f028.jpg', piece='pieces/door_panel.png',
              role='the door, hinged on the left jamb; ajar, then swung inward by a homography of the cut', operation='SAM-seeded graph cut; projective warp'))
A.append(dict(HAND, asset='offered hand', file='sources/door-to-heaven_hand_f010.jpg (copied from /home/user/hartswf0/secondhand-motion/shots/hand-sam/frames/f010.jpg)',
              piece='pieces/hand.png', role='the hand on the reaching arm and the hand offered low',
              operation='graph cut separating hand + forearm from the card its fingers overlap (SAM hand mask + forearm scribble fg, card scribble bg); mirrored, scaled 0.4'))
A.append({'asset': 'light, sky, porch-edge lines, shadows, grain', 'source': 'synthesized in build/render.py', 'rights': 'made here',
          'operation': 'computed: doorway light field and floor spill; cast shadow = the dog\'s own rendered alpha flattened onto the boards'})
A.append({'asset': 'sound', 'source': 'synthesized in build/sound.py', 'rights': 'made here',
          'operation': 'formant voice synthesis (calls, soft voice), footfalls at the frames where the walk drawing changes, sighs, tail taps, latch, creak, room hum, wind floor, crickets'})
A.append({'asset': 'fonts', 'source': 'tools/paeleo/fonts (Big Shoulders Display, JetBrains Mono)', 'rights': 'SIL Open Font License', 'operation': 'title/end cards, prompt slips'})
A.append({'asset': 'score', 'source': 'paeleo/handmade/score/threshold-score.json', 'operation': 'read only: x, state times and act values drive the choreography'})
json.dump({'assets': A, 'not_used': ['Quick, Draw! drawings (none used)', 'SAM masks are used only as seeds/soft prior, never as final mattes']},
          open(os.path.join(F, 'assets.json'), 'w'), indent=1)
print(len(A), 'assets')
