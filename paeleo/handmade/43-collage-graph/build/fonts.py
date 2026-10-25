"""convert the house fonts (woff2) to ttf for Pillow, into build/cache/fonts"""
import os
from fontTools.ttLib import TTFont
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, '../../../../tools/paeleo/fonts'))
OUT = os.path.join(HERE, 'cache/fonts'); os.makedirs(OUT, exist_ok=True)
for src, dst in (('f14.woff2', 'mono.ttf'), ('f8.woff2', 'display.ttf'), ('f34.woff2', 'serif.ttf')):
    f = TTFont(os.path.join(SRC, src)); f.flavor = None; f.save(os.path.join(OUT, dst))
print('fonts ok')
