"""Proof sheets: render frames A..B step S straight from the machine (no film needed) and crop around the dog at 1:1.
python3 proofcrops.py A B S out.jpg"""
import sys, json, os
import render as R
from PIL import Image, ImageDraw

M = json.load(open(os.path.join(R.CACHE, 'machine.json')))
G = R.gait_tracks(M['frames'])
a, b, st = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]); out = sys.argv[4]
ims = []
for i in range(a, b, st):
    f = M['frames'][i]; R.set_camera(R.camera_for(i))
    s, em, fl, n, meas = R.render_frame(f, f['t'], None, *G[i])
    img = Image.fromarray(R.compose(s, em, fl))
    cx, cy = int(meas['cx']), int(meas['cy'])
    w, h = 420, 280
    c = img.crop((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2))
    ImageDraw.Draw(c).text((6, 6), f"{f['t']:.2f}s", fill=(255, 255, 255))
    ims.append(c)
cols = 3
W = Image.new('RGB', (cols * 420, ((len(ims) + cols - 1) // cols) * 280))
for k, c in enumerate(ims):
    W.paste(c, ((k % cols) * 420, (k // cols) * 280))
W.save(out, quality=88)
