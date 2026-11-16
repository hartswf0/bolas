"""LoC photo search (JSON), FSA/OWI only; prints id | title | service-image name. Data only, no execution."""
import json, sys, urllib.parse, urllib.request
UA = {'User-Agent': 'oulipo-film-research/1.0'}
for q in sys.argv[1:]:
    url = 'https://www.loc.gov/photos/?' + urllib.parse.urlencode({'q': q, 'fo': 'json', 'c': 60, 'at': 'results'})
    try: d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
    except Exception as e: print('ERR', q, e); continue
    print('==', q)
    for r in d.get('results', []):
        im = r.get('image_url', [])
        if not im or '/fsa/' not in im[0]: continue
        print(r.get('id', '').rstrip('/').split('/')[-1], '|', r.get('title', '')[:160], '|', im[0].split('/')[-1].split('.')[0].split('_')[0])
