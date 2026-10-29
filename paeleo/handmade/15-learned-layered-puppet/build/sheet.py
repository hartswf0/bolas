"""quick look: crops around the dog at given frames -> one JPEG. usage: sheet.py out.jpg i i i ... [--raw]"""
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render
mode = 'raw' if '--raw' in sys.argv else 'corrected'
args = [a for a in sys.argv[1:] if not a.startswith('--')]
out, fs = args[0], [int(a) for a in args[1:]]
tiles = []
for i in fs:
    img, m = render.render_frame(render.CTRL[i], mode)
    cx, cy = int(m['cx']), int(m['cy'])
    x0 = max(0, min(1280 - 400, cx - 200)); y0 = max(0, min(720 - 300, cy - 170))
    tiles.append(Image.fromarray(img).crop((x0, y0, x0 + 400, y0 + 300)))
S = Image.new('RGB', (400 * 5, 300 * ((len(tiles) + 4) // 5)))
for j, t in enumerate(tiles):
    S.paste(t, ((j % 5) * 400, (j // 5) * 300))
S.save(out, quality=88)
