import json, sys, time, urllib.parse, urllib.request
UA = {'User-Agent': 'oulipo-film-research/1.0'}
def search(q, n=10):
    u = ('https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrnamespace=6'
         f'&gsrlimit={n}&gsrsearch=' + urllib.parse.quote(q) +
         '&prop=imageinfo&iiprop=url|size|mime|extmetadata&iiextmetadatafilter=LicenseShortName|Artist|LicenseUrl')
    for k in range(3):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40))
        except Exception as e:
            print('retry', e, file=sys.stderr); time.sleep(5 * (k + 1))
for q in sys.argv[1:]:
    print('==', q)
    d = search(q) or {}
    for p in (d.get('query', {}).get('pages', {}) or {}).values():
        ii = p['imageinfo'][0]; m = ii.get('extmetadata', {})
        print(p['title'][:80], '|', m.get('LicenseShortName', {}).get('value'), '|', ii.get('mime'), ii['size'], '|', ii['descriptionurl'])
    time.sleep(2)
