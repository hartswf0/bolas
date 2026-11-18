"""re-verify LoC item licences from item JSON; save raw JSON (data only) and a summary."""
import json, sys, urllib.request, time
UA = {'User-Agent': 'oulipo-film-research/1.0'}
OUT = '/home/user/bolas/paeleo/scion/oulipo/films/sources/renzo-e-luciana/cutout-performance/loc_json'
res = []
for a in sys.argv[1:]:
    for k in range(3):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(f'https://www.loc.gov/item/{a}/?fo=json', headers=UA), timeout=90)); break
        except Exception as e: err = e; time.sleep(3)
    else: print(a, 'ERR', err); continue
    json.dump(d.get('item', {}), open(f'{OUT}/{a}.json', 'w'))
    it = d['item']; ri = it.get('rights_information') or it.get('rights') or ''
    if isinstance(ri, list): ri = ' '.join(ri)
    res.append({'id': a, 'title': it.get('title'), 'creator': it.get('contributor_names') or it.get('creator'), 'date': it.get('date'),
                'call': it.get('call_number'), 'nkr': 'No known restrictions' in json.dumps(it), 'rights': ri[:120],
                'service': [u for u in it.get('image_url', [])][-1:] })
    print(json.dumps(res[-1])); time.sleep(.5)
json.dump(res, open(OUT + '/summary.json', 'w'), indent=1)
