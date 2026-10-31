"""Index every archive shot whose media is on disk in cineosis-lab, with the
archive queries that returned it (the archive's own CLIP search, cached),
CLIP subjects, colour and audio features. Writes index.json here."""
import json, os, glob, collections, sys
LAB = sys.argv[1] if len(sys.argv) > 1 else '/home/user/cineosis-lab'
L = os.path.join(LAB, 'lab')
data = json.load(open(f'{L}/lab-data.json'))
shots = {s['id']: s for s in data['shots'] if not s['id'].startswith('wg_')}
corpus = json.load(open(f'{L}/cache/corpus.json'))
q = collections.defaultdict(set)
for f in glob.glob(f'{LAB}/results/*.json'):
    for query, clips in json.load(open(f)).items():
        for c in clips: q[c['id']].add(query)
for e in json.load(open(f'{L}/cutbastard/forage/search.json')).values():
    for c in e['clips']: q[c['id']].add(e['q'])
idx = []
tempest = {os.path.basename(p)[:-4]: p for p in glob.glob(f'{L}/wygwyl/tempest/*.mp4')}
for sid, s in shots.items():
    media = []
    if s.get('clip') and os.path.exists(f"{L}/{s['clip']}"): media.append(('clip', f"{L}/{s['clip']}"))
    if sid in tempest: media.append(('loop', tempest[sid]))
    if os.path.exists(f"{L}/{s['thumb']}"): media.append(('still', f"{L}/{s['thumb']}"))
    if not media: continue
    c = corpus.get(sid, {})
    idx.append({'id': sid, 'title': s['title'], 'year': s.get('year'), 'slug': s.get('slug'),
                'page': s.get('page'), 'start': s.get('start'), 'end': s.get('end'), 'read_t': s.get('read_t'),
                'media': dict(media), 'bw': s.get('bw'), 'hue': s.get('hue'), 'lum': s.get('lum'), 'sat': s.get('sat'),
                'palette': s.get('palette'), 'subjects': s.get('subjects'), 'scale': s.get('scale'),
                'audio': s.get('audio'), 'queries': sorted(q.get(sid, [])),
                'notes': [g.get('note') for g in (s.get('signs') or []) if g.get('note')]})
json.dump(idx, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.json'), 'w'))
k = collections.Counter(m for e in idx for m in e['media'])
print(len(idx), dict(k), 'with queries', sum(1 for e in idx if e['queries']))
