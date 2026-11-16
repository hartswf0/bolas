"""fetch small IIIF previews of LoC FSA/OWI negatives by service id (e.g. 8d17941v), then make a labelled sheet."""
import sys, os, urllib.request, time
from PIL import Image, ImageDraw
OUT = sys.argv[1]; W = int(sys.argv[2]); ids = sys.argv[3:]
UA = {'User-Agent': 'oulipo-film-research/1.0'}
def iiif(i, w):
    a, b = i[:2] + i[2:3] + '000', i[:2] + i[2:4] + '00'
    a = i[:4] + '000'; b = i[:5] + '00'
    return f'https://tile.loc.gov/image-services/iiif/service:pnp:fsa:{a}:{b}:{i}/full/{w},/0/default.jpg'
tiles = []
for i in ids:
    p = f'{OUT}/{i}_{W}.jpg'
    if not os.path.exists(p):
        try:
            d = urllib.request.urlopen(urllib.request.Request(iiif(i, W), headers=UA), timeout=60).read(); open(p, 'wb').write(d)
        except Exception as e: print('ERR', i, e); continue
    im = Image.open(p).convert('L'); print(i, im.size)
    im.thumbnail((400, 400)); t = Image.new('L', (400, 420), 255); t.paste(im, (0, 20)); ImageDraw.Draw(t).text((4, 4), i, fill=0); tiles.append(t)
if tiles:
    c = 5; r = (len(tiles) + c - 1) // c; S = Image.new('L', (c * 400, r * 420), 255)
    for k, t in enumerate(tiles): S.paste(t, ((k % c) * 400, (k // c) * 420))
    S.save(f'{OUT}/sheet.jpg')
