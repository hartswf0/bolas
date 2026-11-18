"""Fetch Commons file info + original by title; save to dir; print ledger json line."""
import json, sys, time, urllib.parse, urllib.request, os, re
UA = {'User-Agent': 'oulipo-film-research/1.0'}
def get(u):
    for k in range(4):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
        except Exception as e: print('retry', e, file=sys.stderr); time.sleep(8 * (k + 1))
out = sys.argv[1]
for t in sys.argv[2:]:
    u = ('https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url|extmetadata&titles=' + urllib.parse.quote(t))
    p = list(json.loads(get(u))['query']['pages'].values())[0]; ii = p['imageinfo'][0]; m = ii['extmetadata']
    fn = re.sub(r'[^A-Za-z0-9._-]', '_', t.split(':', 1)[1])
    open(os.path.join(out, fn), 'wb').write(get(ii['url'])); time.sleep(3)
    print(json.dumps({'title': t, 'file': fn, 'author': re.sub('<[^>]+>', '', m.get('Artist', {}).get('value', '')).strip(),
        'license': m.get('LicenseShortName', {}).get('value'), 'license_url': m.get('LicenseUrl', {}).get('value', ''),
        'source_url': ii['descriptionurl'], 'file_url': ii['url']}))
