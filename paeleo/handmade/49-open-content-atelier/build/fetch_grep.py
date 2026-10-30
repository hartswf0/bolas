"""Stream a unit's Smithsonian Open Access EDAN metadata and keep rows whose JSON matches a regex and has CC0 media.
Usage: python3 -I fetch_grep.py <unit> <regex> <out.jsonl> [nfiles=256]"""
import json, re, sys, urllib.request, concurrent.futures as cf
B = 'https://smithsonian-open-access.s3-us-west-2.amazonaws.com'
unit, rx, out = sys.argv[1], re.compile(sys.argv[2], re.I), sys.argv[3]
nf = int(sys.argv[4]) if len(sys.argv) > 4 else 256
def one(h):
    rows = []
    try:
        with urllib.request.urlopen(f'{B}/metadata/edan/{unit}/{h:02x}.txt', timeout=180) as r:
            for line in r:
                if not rx.search(line.decode('utf8', 'ignore')): continue
                d = json.loads(line); dn = d.get('content', {}).get('descriptiveNonRepeating', {})
                om = dn.get('online_media', {}).get('media', [])
                if any(m.get('usage', {}).get('access') == 'CC0' for m in om): rows.append(d)
    except Exception as e: print('skip', h, e)
    return rows
n = 0
with open(out, 'w') as f, cf.ThreadPoolExecutor(8) as ex:
    for rows in ex.map(one, range(nf)):
        for d in rows: f.write(json.dumps(d) + '\n'); n += 1
print(unit, n)
