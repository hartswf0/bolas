"""Copy the Quick, Draw! drawings this film cuts into its backdrop (CC BY 4.0, Google Creative Lab and contributors).
Indexes are into the recognized drawings of each category file, as chosen from contact sheets (build/cache/qd_*.png)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'assets', 'quickdraw_used.ndjson')
PICK = {'moon': [7], 'tree': [3, 30], 'fence': [28, 24]}
rows = []
for cat, idx in PICK.items():
    src = '/home/user/hartswf0/quickdraw/%s.part' % cat
    L = open(src).read().split('\n')[:-1]          # last line may be partial: drop it
    rec = []
    for l in L:
        try: d = json.loads(l)
        except Exception: continue
        if d.get('recognized'): rec.append(d)
    for i in idx:
        d = rec[i]; d['_source'] = src; d['_index_recognized'] = i
        rows.append(d)
with open(OUT, 'w') as f:
    for d in rows: f.write(json.dumps(d) + '\n')
for d in rows: print(d['word'], d['key_id'], d['countrycode'], len(d['drawing']), [len(s[0]) for s in d['drawing']])
