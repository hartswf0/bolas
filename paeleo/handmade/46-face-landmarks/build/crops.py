"""proof tool: crops around the dog's projected landmarks for a list of frames into one sheet"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
from geom import Camera, CACHE
rig = json.load(open(os.path.join(CACHE, 'rig.json'))); pose = json.load(open(os.path.join(CACHE, 'pose.json')))
src = sys.argv[1]; frames = [int(x) for x in sys.argv[2].split(',')]; out = sys.argv[3]
cols = int(sys.argv[4]) if len(sys.argv) > 4 else 4
cw, ch = 400, 300
sheet = Image.new('RGB', (cols * cw, ((len(frames) + cols - 1) // cols) * ch), (0, 0, 0))
for k, i in enumerate(frames):
    f = rig[i]; c = f['camera']; cam = Camera(c['pos'], c['target'], c['fov'])
    pts = np.array(list(pose[i]['body'].values()) + list(pose[i]['head'].values()))
    q = cam.project(pts)[0]; cx, cy = q.mean(0)
    im = Image.open(os.path.join(src, f's{i:04d}.jpg'))
    x0 = int(min(max(0, cx - cw / 2), 1280 - cw)); y0 = int(min(max(0, cy - ch / 2), 720 - ch))
    cr = im.crop((x0, y0, x0 + cw, y0 + ch)); d = ImageDraw.Draw(cr); d.text((6, 4), f'{i} {f["t"]:.2f}s', fill=(255, 255, 0))
    sheet.paste(cr, ((k % cols) * cw, (k // cols) * ch))
sheet.save(out, quality=92)
