"""convert the repo's woff2 fonts (tools/paeleo/fonts) to ttf in build/cache for Pillow."""
import os
from fontTools.ttLib import TTFont
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, '../../../../tools/paeleo/fonts'))
os.makedirs(os.path.join(HERE, 'cache'), exist_ok=True)
for f, n in [('f5', 'BigShoulders800'), ('f14', 'JetBrainsMono400'), ('f27', 'Literata400'), ('f34', 'Literata400i')]:
    t = TTFont(os.path.join(SRC, f + '.woff2')); t.flavor = None; t.save(os.path.join(HERE, 'cache', n + '.ttf'))
