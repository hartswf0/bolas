"""print title, creator, date, rights, tiff url for LoC items (by item id or by service id search)."""
import json, sys, urllib.request, urllib.parse
UA = {'User-Agent': 'oulipo-film-research/1.0'}
def get(u): return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90))
for a in sys.argv[1:]:
    if not a.isdigit():
        d = get('https://www.loc.gov/photos/?' + urllib.parse.urlencode({'q': a, 'fo': 'json', 'at': 'results'}))
        ids = [r['id'].rstrip('/').split('/')[-1] for r in d['results'] if any(a in u for u in r.get('image_url', []))]
        if not ids: print(a, 'NOT FOUND'); continue
        a = ids[0]
    d = get(f'https://www.loc.gov/item/{a}/?fo=json'); it = d['item']
    tif = [x['url'] for r in d.get('resources', []) for f in r.get('files', []) for x in f if x.get('mimetype') == 'image/tiff']
    print(json.dumps({'id': a, 'title': it.get('title'), 'creator': it.get('contributor_names'), 'date': it.get('date'),
                      'rights': (it.get('rights_information') or '')[:60] if isinstance(it.get('rights_information'), str) else it.get('rights_information'),
                      'source_url': f'https://www.loc.gov/item/{a}/', 'tiff': tif}))
