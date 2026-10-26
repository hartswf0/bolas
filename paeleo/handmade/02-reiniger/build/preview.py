import sys, os, numpy as np
from PIL import Image
import render
from theatre import *
render.init()
os.makedirs(os.path.join(OUT,'preview'),exist_ok=True)
for a in sys.argv[1:]:
    if a.startswith('title'): buf=render.render_title(int(a[5:]))
    elif a.startswith('end'): buf=render.render_end(int(a[3:]))
    else: buf,m=render.render_scene(int(a)); print(a, {k:m[k] for k in ('x_screen','facing','gaze') if k in m}, m['row'].get('head'), m['limits'][:3])
    Image.frombytes('RGB',(W,H),buf).save(os.path.join(OUT,'preview',f'{a}.jpg'),quality=90)
