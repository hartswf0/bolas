"""proof: every fitted archive frame with the fitted layered template drawn over it (layer colours) and its IoU."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from puppet import Template, PARTS, render, KIT, CACHE
from fit import unpack, frame_mask

COLS = np.array([[200, 120, 60], [240, 220, 80], [120, 200, 240], [90, 90, 200], [60, 60, 160], [80, 200, 90], [40, 140, 60],
                 [200, 90, 200], [140, 50, 140], [240, 80, 80], [160, 40, 40]], float)

if __name__ == '__main__':
    tpl = Template()
    F = json.load(open(os.path.join(CACHE, 'fits.json')))
    tiles = []
    for i in range(50):
        f = F['frames'][str(i)]
        pose = unpack(np.array(f['x']), f['mirror'])
        gray = np.asarray(Image.open(os.path.join(KIT, 'frames/f%03d.jpg' % i)).convert('L'), np.float32)
        _, A, L = render(tpl, pose, 288, 384, want_layers=True)
        vis = np.stack([gray] * 3, -1) * 0.6
        for k, (g, a) in L.items():
            vis = vis * (1 - 0.45 * a[..., None]) + 0.45 * a[..., None] * COLS[PARTS.index(k)]
        m = frame_mask(i)
        edge = m ^ np.roll(m, 1, 0) | m ^ np.roll(m, 1, 1)
        vis[edge] = [255, 255, 255]
        im = Image.fromarray(np.clip(vis, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im)
        d.text((4, 4), 'f%02d IoU %.2f %s%s' % (i, f['iou'], 'M' if f['mirror'] < 0 else '', ' SUSPECT MASK' if f['mask_suspect'] else ''), fill=(255, 255, 0))
        tiles.append(im.resize((256, 192)))
    sheet = Image.new('RGB', (256 * 10, 192 * 5))
    for j, t in enumerate(tiles):
        sheet.paste(t, ((j % 10) * 256, (j // 10) * 192))
    sheet.save(os.path.join(CACHE, '..', '..', 'proof', 'fits_sheet.jpg'), quality=85)
