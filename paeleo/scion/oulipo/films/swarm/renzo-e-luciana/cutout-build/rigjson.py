import json, os
D = '/home/user/bolas/paeleo/scion/oulipo/films/swarm/renzo-e-luciana'; S = 'films/sources/renzo-e-luciana'
CP = S + '/cutout-performance'
r3 = json.load(open('/home/user/bolas/paeleo/scion/oulipo/' + CP + '/pieces/pieces.json')); r2 = json.load(open('/home/user/bolas/paeleo/scion/oulipo/' + CP + '/pieces/r2/rig.json'))
perf = json.load(open(D + '/performance.json')); meas = json.load(open(D + '/cutout-build/measures.json'))
LOC = 'https://www.loc.gov/rr/print/res/071_fsab.html'; NKR = 'No known restrictions (LoC FSA/OWI; US government work, public domain); re-verified from item JSON 2026-11-16'
ev = [
 {'id': 'loc-2017789670', 'title': 'Time clock and tool boxes at the vocational school for aircraft construction workers. San Diego, California (1941), LC-USF34-039424-D', 'author': 'Russell Lee (FSA)', 'license': NKR, 'license_url': LOC,
  'source_url': 'https://www.loc.gov/item/2017789670/', 'file_url': 'https://tile.loc.gov/storage-services/master/pnp/fsa/8c01000/8c01400/8c01492u.tif',
  'local_path': S + '/test-shot/r2/hi/plate_8c01492.png; pails_8c01492.png (r2 master-TIFF range crops, reused)', 'what_it_shows': 'a wall of time-card racks around a pendulum time clock, a pile of workers\' tool boxes in front',
  'verified_date_or_place': '1941, San Diego, California (LoC item)', 'used_as': 'wall plate at native sampling (photographed clock hands lifted off, paper hands drawn per frame); the near pail/tool-box pile occluder (#45 holdout) and the lids where the apple is set'},
 {'id': 'loc-2017851428', 'title': 'Buffalo, New York. Women employees eating lunches brought from home at Ross Heater... (1943), OWI-23899-D', 'author': 'Marjory Collins (OWI)', 'license': NKR, 'license_url': LOC,
  'source_url': 'https://www.loc.gov/item/2017851428/', 'file_url': 'https://tile.loc.gov/storage-services/master/pnp/fsa/8d16000/8d16900/8d16982u.tif',
  'local_path': CP + '/hi/lu_8d16982.png (HTTP-range crop x4572-9144, y300-6036 of the 13070x10068 master, 6x box-averaged; 29.4 MB fetched)',
  'what_it_shows': 'a young woman in a hairnet, three-quarter view, laughing as she bites an apple held in her left hand, at a lunch table',
  'verified_date_or_place': '1943, Buffalo, New York (LoC item)', 'used_as': 'NEW LUCIANA (recast): head, body, forearm+hand pieces on an FK rig, and the apple (with bite states cut from it)'},
 {'id': 'loc-2017835701', 'title': 'Dodge truck plant, Detroit, Michigan. Lunch hour (1942), LC-USW3-007191-C', 'author': 'Arthur S. Siegel (OWI)', 'license': NKR, 'license_url': LOC,
  'source_url': 'https://www.loc.gov/item/2017835701/', 'file_url': 'https://tile.loc.gov/storage-services/master/pnp/fsa/8d07000/8d07800/8d07886u.tif',
  'local_path': S + '/test-shot/r2/hi/re_8d07886.png (r2 crop, reused)', 'what_it_shows': 'a man in a cap in profile at lunch', 'verified_date_or_place': '1942, Detroit, Michigan (LoC item)',
  'used_as': 'Renzo (kept from the approved r2): head and torso pieces, neck and hip pins'},
 {'id': 'loc-2017829778', 'title': 'Madison, Wisconsin. John Stuart Curry, working on his mural in the biochemistry building... In the background is the chemistry laboratory (1942), LC-USW3-001218-D', 'author': 'Jack Delano (OWI)', 'license': NKR, 'license_url': LOC,
  'source_url': 'https://www.loc.gov/item/2017829778/', 'file_url': 'https://tile.loc.gov/storage-services/master/pnp/fsa/8d03000/8d03400/8d03483u.tif',
  'local_path': S + '/test-shot/r2/hi/door_8d03483.png (left third only, reused)', 'what_it_shows': 'a wooden door casing and a laboratory beyond, a man in a work coat at the bench seen from behind',
  'verified_date_or_place': '1942, Madison, Wisconsin (LoC item)', 'used_as': 'the CAPOREPARTO doorway (real casing) and the foreman BACK view (facing OFFICE); the Curry mural is cropped out and never used'},
 {'id': 'loc-2017851041', 'title': 'Bethlehem-Fairfield shipyards, Baltimore, Maryland. A shipyard worker looking at a time clock from outside of the yard (1943), LC-USW3-023485-E', 'author': 'Arthur S. Siegel (OWI)', 'license': NKR, 'license_url': LOC,
  'source_url': 'https://www.loc.gov/item/2017851041/', 'file_url': 'https://tile.loc.gov/storage-services/service/pnp/fsa/8d28000/8d28300/8d28363v.jpg',
  'local_path': S + '/loc/8d28363v.jpg (1024 px service JPEG, reused)', 'what_it_shows': 'a man in a hard hat and work jacket, full figure, leaning on a pole and looking down to his right',
  'verified_date_or_place': '1943, Baltimore, Maryland (LoC item)', 'used_as': 'the foreman FRONT view (facing FLOOR), scaled 0.54 (a downsample); substituted by the Delano back view at the 12:01 turn'},
 {'id': 'commons-Clock_ticking.ogg', 'title': 'File:Clock ticking.ogg', 'author': 'natalie (Wikimedia Commons)', 'license': 'Public domain (Commons extmetadata, recorded in r1/r2 ledger)', 'license_url': '',
  'source_url': 'https://commons.wikimedia.org/wiki/File:Clock_ticking.ogg', 'file_url': 'https://upload.wikimedia.org/wikipedia/commons/5/56/Clock_ticking.ogg',
  'local_path': CP + '/sound/Clock_ticking.wav', 'what_it_shows': 'a mechanical clock ticking', 'verified_date_or_place': 'unverified', 'used_as': 'scratch tick bed (louder in B)'}]
checked_not_used = [
 {'id': 'loc-2017788376', 'title': 'Workers eating lunch on curb across the street from the Consolidated Airplane Factory. San Diego (1940)', 'author': 'Russell Lee (FSA)', 'license': NKR, 'source_url': 'https://www.loc.gov/item/2017788376/', 'local_path': S + '/loc/8c00283v.jpg, test-shot/8c00284v.jpg', 'used_as': 'not used (figures too small for the 1.6x MEDIUM; superseded by the Siegel Renzo)'},
 {'id': 'loc-2017851042', 'title': 'Bethlehem-Fairfield shipyards, Baltimore. Lining up before a time clock (1943)', 'author': 'Arthur S. Siegel (OWI)', 'license': NKR, 'source_url': 'https://www.loc.gov/item/2017851042/', 'local_path': S + '/loc_8d28364v.jpg', 'used_as': 'not used: no true back view in the frame (men face the camera); the Delano bench man is the real back view'},
 {'id': 'loc-2017853398', 'title': 'Bethlehem-Fairfield shipyards, Baltimore. Boy and girl worker during the lunch hour (1943)', 'author': 'Arthur S. Siegel (OWI)', 'license': NKR, 'source_url': 'https://www.loc.gov/item/2017853398/', 'local_path': S + '/loc_8d29158v.jpg', 'used_as': 'retained alternate (one photograph, one light) if the pair reads as pasted; both face the camera, so not chosen'},
 {'id': 'loc-2017829776', 'title': 'Lunch hour at the Pacific Parachute Company. San Diego (1942)', 'author': 'Russell Lee (OWI)', 'license': NKR, 'source_url': 'https://www.loc.gov/item/2017829776/', 'local_path': S + '/test-shot/r2/hi/lu_8d03481.png', 'used_as': 'r2 Luciana, now RETIRED (did not read clearly as a young woman, per review)'},
 {'id': 'loc-Ross-Heater-adjacent', 'title': 'Ross Heater series OWI-23896/23897/23898-D (8d16979v, 8d16980v, 8d16981v)', 'author': 'Marjory Collins (OWI)', 'license': 'No known restrictions (same lot; previously checked)', 'source_url': 'https://www.loc.gov/photos/?q=Ross+Heater+lunches', 'local_path': S + '/loc/8d16979v.jpg; test-shot/8d16980v.jpg, 8d16981v.jpg', 'used_as': 'looked at for alternate poses of the same woman: she does not recur in a usable pose in these three frames; OWI-23900..23902-D not checked this round (time/download budget)'}]
absences = ['A real back view of the hard-hat foreman (the same man as the front view) was not found; the turn substitutes two different real men (Siegel front, Delano back) of similar build in work clothes. Declared; no mirroring used.',
            'No second pose of the Ross Heater woman (OWI-23899-D) in the adjacent negatives in hand; her feed / bite / lid motion is forearm rotation on the elbow pin plus head tilt, the photograph\'s own pose being her bite.',
            'No openly licensed recording of a bite, a late bell or factory room tone was foraged by this unit; the scratch track uses kit synthesis (declared) for those; the sound unit owns the real cues.',
            'Renzo has no separate arm piece (the Siegel negative shows no free forearm), so in B he leaves the apple on her lid with a lean-in bite rather than a hand set-down.']
handmade = [{'what': 'typed CAPOREPARTO card (DejaVu Serif Bold on a pale card, rotated -1.2 deg) pinned on the wall at the door casing', 'where': 'cutout-build/render3.py (sign)'},
            {'what': 'paper clock hands drawn per frame on the real dial from the fixture clock (minute 6 deg / 5 s of film)', 'where': 'cutout-build/render3.py (hand())'},
            {'what': 'scissor-cut bites (scalloped arcs, pale rim) cut out of the real apple cut-out: A1 R, A2 L, A3 R; B1 R', 'where': 'cutout-build/render3.py (bite())'},
            {'what': 'backing card behind Luciana\'s lifted forearm and apple, cut from a real swatch of her own cardigan knit in the same negative', 'where': 'cutout-build/cuts3.py'},
            {'what': 'scratch sound: kit room tone, foreman steps, paper rustles, bite crunches, apple set-down click, late bell (1320 Hz kit bell)', 'where': 'cutout-build/render3.py snd(); films/kit.py'}]
pieces = {}
def P(name, file, src, piv, parent, z, scale, grade, note=''):
    pieces[name] = {'file': file, 'source_item': src, 'pivots_piece_px': piv, 'parent': parent, 'z': z, 'stage_scale': scale, 'grade_levels_gamma': grade, 'note': note}
q = r3['pieces']
P('plate', S + '/test-shot/r2/hi/plate_8c01492.png', 'loc-2017789670', {}, None, 0, 1.0, [14, 218, .55], 'stage = plate at native 1933x1087; DOF blur sigma 1.1; hands inpainted')
P('door', CP + '/pieces/r2/door_empty.png', 'loc-2017829778', {'tl': r2['door']['pivots']['tl']}, 'stage', 1, 1.0, [18, 236, 1.0], 'placed at (367,-30): casing at x~800, just left of the clock')
P('foreman_front', CP + '/pieces/foreman_front.png', 'loc-2017851041', q['foreman_front']['pivots'], 'door', 2, .54, [20, 228, .95], 'facing FLOOR; t < turn')
P('foreman_back', CP + '/pieces/r2/foreman.png', 'loc-2017829778', r2['foreman']['pivots'], 'door', 2, 1.0, [18, 236, 1.0], 'facing OFFICE; reading sway on the feet pin')
P('lu_body', CP + '/pieces/lu_body.png', 'loc-2017851428', q['lu_body']['pivots'], 'L.root', 3, .44, [12, 200, .85])
P('lu_head', CP + '/pieces/lu_head.png', 'loc-2017851428', q['lu_head']['pivots'], 'lu_body@neck', 4, .44, [10, 214, .92])
P('re_body', CP + '/pieces/r2/re_body.png', 'loc-2017835701', r2['re_body']['pivots'], 'R.root', 5, .70, [22, 200, 1.08])
P('re_head', CP + '/pieces/r2/re_head.png', 'loc-2017835701', r2['re_head']['pivots'], 're_body@neck', 6, .70, [22, 226, 1.1])
P('apple', CP + '/pieces/apple.png', 'loc-2017851428', q['apple']['pivots'], 'lu_arm@grip (until A 14.0) / pail lid', 7, .44, [10, 214, .92], 'bite states cut per frame; behind the fingers')
P('lu_arm', CP + '/pieces/lu_arm.png', 'loc-2017851428', q['lu_arm']['pivots'], 'lu_body@elbow', 8, .44, [10, 214, .92], 'A: in front of R (fingers at his mouth); B: drawn before R (she passes behind him)')
P('pails', CP + '/pieces/r2/pails.png', 'loc-2017789670', {'tl': [0, 0]}, 'stage', 9, .93, [26, 215, 1.12], 'near occluder at (470,318): hides both bodies below the hands')
P('apple_on_lid', CP + '/pieces/apple.png', 'loc-2017851428', q['apple']['pivots'], 'pails', 10, .44, [10, 214, .92])
P('clock_hands', 'handmade (render3.py)', 'handmade', {'centre': [901.6, 133.5]}, 'plate', 11, 1.0, None)
rig = {'unit': 'cutout-performance', 'revision': 'r3 (after the approved r2: Luciana recast, 1.6x MEDIUM push, grain kept in target)',
 'stage': {'size': [1933, 1087], 'camera_windows': {'WIDE': {'x0': 400, 'y0': 40, 'w': 1200}, 'MEDIUM': {'x0': 600, 'y0': 48, 'w': 960, 'note': '1:1 stage px; 1.25x push from WIDE; door jamb, dial and couple held in frame'}},
           'clock': {'centre': [901.6, 133.5], 'radius': 68.2, 'minute_deg_per_film_s': 1.2}},
 'pieces': pieces,
 'skeletons': {'Luciana': ['L.root (translation, dx)', 'hip (lu_body)', 'neck -> lu_head', 'elbow -> lu_arm', 'grip -> apple (attachment)'],
               'Renzo': ['R.root (translation dx, dy)', 'hip (re_body)', 'neck -> re_head (mouth point solved by FK onto the apple at the feed pose)'],
               'Foreman': ['feet pin (sway)', 'front/back = drawing substitution of two real photographs at the 12:01 turn']},
 'grabcut_checks': r3['checks'], 'occlusion_dag': 'plate < door < foreman < lu_body < lu_head < re_body < re_head < apple(hand) < lu_arm (A) < pails < apple(lid) < clock hands; in B lu_arm precedes re_body',
 'invariants_checked': {'never_mirrored': True, 'transforms': 'scale (<=1.0, no enlargement), rotation about pins, translation of roots, levels/gamma only',
     'rule_preserved': 'L enters the corner only after the foreman turns (A 5.1 s > 5.0; B 52.62 s, foreman back until 57); asserted from performance.json frames',
     'drawings_on_twos': True, 'joints_per_puppet': {'Luciana': 4, 'Renzo': 3, 'Foreman': 1}},
 'performance': 'films/swarm/renzo-e-luciana/performance.json', 'testshot': 'films/swarm/renzo-e-luciana/testshot.mp4 (22.5 s = A 4.5-15.0 + B 41.5-53.5, 960x540/24, H.264+AAC scratch sound)',
 'contact': 'films/swarm/renzo-e-luciana/testshot-contact.jpg', 'measures': meas,
 'evidence': ev, 'checked_not_used': checked_not_used, 'absences': absences, 'handmade': handmade,
 'build': ['films/swarm/renzo-e-luciana/cutout-build/cuts3.py', 'cutout-build/render3.py (--stills t..., --perf, render)', 'cutout-build/contact.py', 'cutout-build/locv.py', 'test-shot-build/tiffcrop.py (range-crop fetcher)'],
 'editor_notes': ['Version A from 0.4-5.0 must keep Luciana off the corner; in this performance she is offstage left until 5.08 and slides in behind the pails 5.1-6.9 (the full film can show her at a left place out of the MEDIUM window).',
                  'Late bell and bites in the test shot are kit scratch; replace with the sound unit cues.', 'Downloads this unit: 29.4 MB (one master-TIFF range crop) + LoC item JSON.']}
for ver in ('A', 'B'):
    for f in perf['segments'][ver]['frames']:
        inside = f['L.root_dx'] > -300
        assert not (inside and f['foreman'] == 'front'), f
json.dump(rig, open(D + '/rig.json', 'w'), indent=1); print('rig ok')
