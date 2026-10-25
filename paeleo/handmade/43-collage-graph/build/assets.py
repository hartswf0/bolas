"""../assets.json: every asset, where it came from, its rights, and the operation that made it (the source ledger)"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); TOP = os.path.dirname(HERE)
fr = json.load(open(os.path.join(HERE, 'cache/frags.json')))
gt = json.load(open(os.path.join(TOP, 'graph_trace.json')))
used = set(f for c in gt['changes'] for _, f in c['nodes'])
out = []
for f in fr['fragments']:
    s = f['source']
    out.append(dict(id=f['id'], kind='fragment', typed_as=f['type'], motif_tags=f['tags'], used_in_film=f['id'] in used or f['type'].startswith(('door', 'voice')),
                    source_title=s['title'], source_shot=s['shot'], source_frame=s['frame'], frame_file=s['frame_file'],
                    archive_url=s['url'], rights=s['rights'], operation=f['operation'], scissors_polygon_source_px=f['cut'],
                    anchors_fragment_px=f['anchors']))
for k, w in fr['world'].items():
    s = w['source']
    out.append(dict(id=k, kind='world piece', source_title=s['title'], source_shot=s['shot'], source_frame=s['frame'], archive_url=s['url'],
                    rights=s['rights'], operation=w['operation'] + '; graded to dusk / door light at render'))
out += [
    dict(id='score', kind='score', file='paeleo/handmade/score/threshold-score.json', source='PAELEO machine (paeleo/threshold/machine.js), built by tools/paeleo/build_score.js',
         rights='Bolas project', operation='read: dog state, x, act; person; door; prompts; timeline'),
    dict(id='fonts', kind='font', file='tools/paeleo/fonts/f8.woff2 (Big Shoulders Display 900), f14.woff2 (JetBrains Mono), f34.woff2 (Literata)',
         rights='SIL Open Font License', operation='woff2 -> ttf (fontTools) for the cards and prompt slips'),
    dict(id='sound', kind='sound', file='build/sound.py', source='synthesized here in numpy: formant voice (source-filter), door latch/creak, warm pad, paw taps from the gait solver, paper snips at rewrites, crickets, room tone',
         rights='made here', operation='synthesized; no recordings used'),
    dict(id='head_back_cut', kind='note', source_title='Amateur Film New Jersey C', rights='public_domain',
         operation='the one dog piece whose outline is drawn here (no frame shows the back of the dog\'s head): its own fur cut to a drawn shape'),
    dict(id='not used', kind='note', operation='No Quick, Draw! drawings, no web images, no model-generated images, nothing of unknown rights.'),
]
json.dump(dict(about='SCION 43 source ledger: every piece of the film, its source, rights and operation', assets=out),
          open(os.path.join(TOP, 'assets.json'), 'w'), indent=1)
print(len(out), 'assets')
