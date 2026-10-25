"""convert the repo's woff2 fonts to TTF for PIL (cache only)."""
import os
from fontTools.ttLib import TTFont
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', '..', '..', '..', 'tools', 'paeleo', 'fonts')
OUT = os.path.join(HERE, 'cache', 'fonts'); os.makedirs(OUT, exist_ok=True)
NAMES = {'f27': 'Literata-Italic', 'f34': 'Literata-Regular', 'f14': 'JetBrainsMono-Regular', 'f20': 'JetBrainsMono-SemiBold', 'f5': 'BigShoulders-800'}
for k, v in NAMES.items():
    p = os.path.join(OUT, v + '.ttf')
    if not os.path.exists(p):
        f = TTFont(os.path.join(SRC, k + '.woff2')); f.flavor = None; f.save(p)
print('fonts ok')
