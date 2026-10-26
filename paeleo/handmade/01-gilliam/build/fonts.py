"""Decompress the program's woff2 fonts (tools/paeleo/fonts) to TTF so Pillow can set type."""
import os
from fontTools.ttLib import TTFont
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'tools', 'paeleo', 'fonts'))
OUT = os.path.join(HERE, 'fonts'); os.makedirs(OUT, exist_ok=True)
for f, n in [('f8', 'BigShoulders-900'), ('f5', 'BigShoulders-800'), ('f27', 'Literata-Italic'), ('f34', 'Literata-Regular'),
             ('f14', 'JetBrainsMono-400')]:
    t = TTFont(os.path.join(SRC, f + '.woff2')); t.flavor = None; t.save(os.path.join(OUT, n + '.ttf'))
print('fonts ok')
