"""Download the public records used by build_catalog.py (stdlib only)."""
import concurrent.futures
import json
import re
import sys
import urllib.request
from pathlib import Path

BASE = 'https://hartswf0.github.io/bolas/'
dest = Path(sys.argv[1])


def get(path):
    target = dest / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(urllib.request.urlopen(BASE + path, timeout=45).read())
    return target


for path in ['allways-argon/studio/index.html', 'allways-sol/catalog.json', 'allways-sonnet/index.html']:
    get(path)
s = (dest/'allways-argon/studio/index.html').read_text()
start = s.index('const FILMS = ') + len('const FILMS = ')
films, _ = json.JSONDecoder().raw_decode(s[start:])
(dest/'argon-films.json').write_text(json.dumps(films))
paths = ['allways-sol/films/055/records/v04/EDIT_LEDGER.json']
s = (dest/'allways-sonnet/index.html').read_text()
paths += ['allways-sonnet/'+p+'index.html' for p in re.findall(r'<a class="fcard" href="([^"]+)"', s)]
paths += ['allways-opus/films/'+slug+'/index.html' for slug in ['nobody-home','almost-human','terra-incognita','split-second','cut-to-the-chase','kinetic','zero-memory','homonym','anybody-anywhere','collective-inventories','mnemonil','planimetric']]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    for path in pool.map(get, paths):
        print(path.relative_to(dest))
