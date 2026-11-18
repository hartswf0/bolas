"""Commons search + licence metadata (read from extmetadata)."""
import json, sys, time, urllib.parse, urllib.request
UA = {'User-Agent': 'oulipo-film-research/1.0'}
API = 'https://commons.wikimedia.org/w/api.php?'
def get(params):
    for k in range(4):
        try:
            r = urllib.request.urlopen(urllib.request.Request(API + urllib.parse.urlencode(params), headers=UA), timeout=30)
            return json.load(r)
        except Exception as e:
            time.sleep(3 * (k + 1))
    return {}
def search(q, n=10):
    d = get(dict(action='query', format='json', list='search', srnamespace=6, srlimit=n, srsearch=q))
    return [r['title'] for r in d.get('query', {}).get('search', [])]
def info(titles):
    d = get(dict(action='query', format='json', prop='imageinfo', iiprop='url|extmetadata|size|mime', titles='|'.join(titles)))
    out = []
    for p in d.get('query', {}).get('pages', {}).values():
        ii = (p.get('imageinfo') or [{}])[0]; em = ii.get('extmetadata', {})
        g = lambda k: em.get(k, {}).get('value', '')
        out.append(dict(title=p['title'], url=ii.get('url'), page=ii.get('descriptionurl'), size=ii.get('size'), mime=ii.get('mime'),
                        license=g('LicenseShortName'), license_url=g('LicenseUrl'), artist=g('Artist'), desc=g('ImageDescription')[:160]))
    return out
if __name__ == '__main__':
    for q in sys.argv[1:]:
        t = search(q)
        print('==', q)
        for r in (info(t) if t else []):
            print(' ', r['title'], '|', r['license'], '|', r['size'], '|', r['mime'])
        time.sleep(1)
