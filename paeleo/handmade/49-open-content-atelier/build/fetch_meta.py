"""Collections researcher: stream Smithsonian Open Access EDAN metadata (official S3 distribution, CC0 dataset)
and keep only rows that (a) have online media marked CC0 and (b) mention a subject we can cast.
Usage: python3 -I fetch_meta.py <unit> <first_hex> <last_hex> <out.jsonl>"""
import json, sys, urllib.request, concurrent.futures as cf
B = 'https://smithsonian-open-access.s3-us-west-2.amazonaws.com'
unit, a, b, out = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16), sys.argv[4]
WORDS = ('dog', 'hound', 'terrier', 'spaniel', 'puppy', 'setter', 'pointer', 'collie', 'door', 'porch', 'doorway',
         'threshold', 'house', 'cottage', 'dusk', 'twilight', 'evening', 'seated', 'sitting', 'man ', 'woman', 'hand')
def one(h):
    rows = []
    with urllib.request.urlopen(f'{B}/metadata/edan/{unit}/{h:02x}.txt', timeout=120) as r:
        for line in r:
            try: d = json.loads(line)
            except Exception: continue
            c = d.get('content', {}); dn = c.get('descriptiveNonRepeating', {})
            om = dn.get('online_media', {}).get('media', [])
            if not om: continue
            if dn.get('metadata_usage', {}).get('access') != 'CC0': continue
            if not any(m.get('usage', {}).get('access') == 'CC0' for m in om): continue
            txt = (d.get('title', '') + ' ' + json.dumps(c.get('freetext', {}).get('topic', [])) + ' ' +
                   json.dumps(c.get('indexedStructured', {}).get('topic', []))).lower()
            if any(w in txt for w in WORDS): rows.append(d)
    return rows
n = 0
with open(out, 'w') as f, cf.ThreadPoolExecutor(8) as ex:
    for rows in ex.map(one, range(a, b + 1)):
        for d in rows: f.write(json.dumps(d) + '\n'); n += 1
print(unit, n, 'rows')
