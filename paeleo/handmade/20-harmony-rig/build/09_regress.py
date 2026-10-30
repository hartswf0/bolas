"""SCION 20 · 09: regression suite (structural assertions where the representation supports them).
Writes build/regress.json. Perceptual questions (does the turn read, does the look read in depth) are not here: they
are for the critic watching the film."""
import json, os, subprocess
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda f: json.load(open(os.path.join(D, f)))
LIB, XS, G, TR = J('scene/library.json')['elements'], J('scene/xsheet.json'), J('scene/nodegraph.json'), J('trace.json')
res = {}
ids = {n['id'] for n in G['nodes']}
res['graph_no_broken_dependencies'] = all(i in ids for n in G['nodes'] for i in n['inputs'])
res['graph_topological_covers_all'] = sorted(G['topological_order']) == sorted(ids)
cols = {'body': 'dog_body', 'head': 'dog_head', 'ear': 'dog_ear', 'tail': 'dog_tail', 'person': 'person', 'mouth': 'person_mouth'}
missing = [(f['i'], c, f[c]) for f in XS['frames'] for c, el in cols.items() if f[c] not in LIB[el]]
res['xsheet_every_exposure_is_a_library_drawing'] = not missing
res['xsheet_768_frames'] = len(XS['frames']) == 768
# whole-drawing substitution: every frame exposes exactly one drawing per column (no blends, no opacity field anywhere)
res['no_cross_dissolve_fields'] = all(not any('opacity' in k or 'blend' in k for k in f) for f in XS['frames'])
# anchors: every ear drawing's view has a head drawing with the same view; every body has neck+tail anchors
res['anchors_present'] = all('neck' in d['anchors'] and 'tail' in d['anchors'] for d in LIB['dog_body'].values())
res['ear_views_match_heads'] = all(f['ear'].rsplit('_', 1)[0] == LIB['dog_head'][f['head']]['view'] for f in XS['frames'])
# walk drawings: planted feet. For consecutive frames with walk drawings, a foot in stance keeps its world x within 1.5 cm
slide = 0.0
for a, b in zip(XS['frames'], XS['frames'][1:]):
    if a['body'][:-2] in ('walk', 'cwalk', 'lwalk') and b['body'][:-2] == a['body'][:-2]:
        da, db = LIB['dog_body'][a['body']], LIB['dog_body'][b['body']]
        for leg, off in (('nh', 0), ('nf', .25), ('fh', .5), ('ff', .75)):
            qa, qb = (da['phase'] + off) % 1, (db['phase'] + off) % 1
            if qa < 0.62 and qb < 0.62:
                wa = a['x_peg'] + 1.12 * da['feet'][leg][0]; wb = b['x_peg'] + 1.12 * db['feet'][leg][0]
                slide = max(slide, abs(wa - wb))
res['planted_feet_max_slide_m'] = round(slide, 4)
res['planted_feet_ok'] = slide < 0.015
on = TR['measured_onsets']
res['measured_onsets_within_0.25s'] = all(abs(v['dt']) <= 0.25 for k, v in on.items() if k != 'looks_in')
lev = TR['sound_levels_db']
res['soft_voice_6db_under_calls'] = lev['soft_under_call_db'] >= 6
res['soft_voice_above_room_tone'] = lev['soft_over_room_db'] > 0
fr = TR['frames']
res['dog_never_inside'] = min(f['x_score'] for f in fr) >= 0.56
res['ends_half_in_door_frame'] = 0.25 <= fr[-1]['dog_in_door_frame'] <= 0.8
res['looks_in_head_inside_room'] = max(f['head_in_room'] for f in fr[640:676]) >= 0.5
p = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames,width,height', '-of', 'json', os.path.join(D, 'film.mp4')], capture_output=True, text=True)
st = json.loads(p.stdout)['streams'][0]
res['film_912_frames_1280x720'] = int(st['nb_read_frames']) == 912 and st['width'] == 1280 and st['height'] == 720
res['film_under_12MB'] = os.path.getsize(os.path.join(D, 'film.mp4')) <= 12 * 1024 * 1024
res['all_ok'] = all(v for k, v in res.items() if isinstance(v, bool))
json.dump(res, open(os.path.join(D, 'build/regress.json'), 'w'), indent=1)
for k, v in res.items(): print('%-45s %s' % (k, v))
