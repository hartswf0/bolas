"""convert the repo's woff2 fonts (tools/paeleo/fonts) to TrueType for Pillow, into build/cache/."""
import os
from fontTools.ttLib import TTFont
HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, '..', '..', '..', '..', 'tools', 'paeleo', 'fonts')
OUT = {'literata_it': 'f27.woff2', 'literata': 'f34.woff2', 'literata_sb': 'f41.woff2', 'mono': 'f14.woff2', 'shoulders': 'f8.woff2'}
if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'cache'), exist_ok=True)
    for k, f in OUT.items():
        t = TTFont(os.path.join(FD, f)); t.flavor = None
        t.save(os.path.join(HERE, 'cache', k + '.ttf'))
    print('fonts ok')
