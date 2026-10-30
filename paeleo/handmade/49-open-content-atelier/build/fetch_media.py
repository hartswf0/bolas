"""Collections researcher: fetch CC0 images from the Smithsonian Open Access S3 distribution, by idsId.
Checks the object's metadata row first (record + media usage must both be CC0), refuses files over 8 MB,
keeps a <=1800 px JPEG copy in sources/media/ and logs every byte to sources/downloads.jsonl.
Usage: python3 -I fetch_media.py <meta.jsonl from fetch_meta/fetch_grep> <idsId> [...]"""
import json, os, sys, io, time, urllib.request
from PIL import Image
B = 'https://smithsonian-open-access.s3-us-west-2.amazonaws.com'
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(HERE, '..', 'sources')
meta = {}
for l in open(sys.argv[1]):
    d = json.loads(l)
    for m in d['content']['descriptiveNonRepeating'].get('online_media', {}).get('media', []):
        meta[m.get('idsId')] = (d, m)
log = open(os.path.join(SRC, 'downloads.jsonl'), 'a')
for ids in sys.argv[2:]:
    out = os.path.join(SRC, 'media', ids + '.jpg')
    if os.path.exists(out): continue
    d, m = meta[ids]
    dn = d['content']['descriptiveNonRepeating']
    if dn.get('metadata_usage', {}).get('access') != 'CC0' or m.get('usage', {}).get('access') != 'CC0':
        print('NOT CC0, skipped', ids); continue
    unit = ids.split('-')[0].lower()
    url = f'{B}/media/{unit}/{ids}.jpg'
    req = urllib.request.Request(url, method='HEAD')
    size = int(urllib.request.urlopen(req, timeout=60).headers.get('Content-Length', 0))
    if size > 8e6: print('too big', ids, size); continue
    data = urllib.request.urlopen(url, timeout=180).read()
    im = Image.open(io.BytesIO(data)).convert('RGB'); W, H = im.size
    s = min(1.0, 1800 / max(W, H)); im = im.resize((round(W * s), round(H * s)), Image.LANCZOS)
    im.save(out, quality=92)
    log.write(json.dumps({'idsId': ids, 'url': url, 'bytes': len(data), 'orig_size': [W, H], 'kept_scale': round(s, 4),
                          'record_ID': dn['record_ID'], 'access': m['usage']['access'], 'time': time.time()}) + '\n')
    print(ids, len(data), (W, H))
