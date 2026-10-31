"""fonts from tools/paeleo/fonts (woff2): Big Shoulders Display, JetBrains Mono, Literata"""
import os
from PIL import ImageFont
from common import REPO
D = os.path.join(REPO, 'tools/paeleo/fonts')
FILES = dict(shoulders_600='f2.woff2', shoulders_800='f5.woff2', shoulders_900='f8.woff2', mono='f14.woff2',
             mono_600='f20.woff2', literata_italic='f27.woff2', literata='f34.woff2', literata_600='f41.woff2')
_c = {}


def font(name, size):
    k = (name, size)
    if k not in _c: _c[k] = ImageFont.truetype(os.path.join(D, FILES[name]), size)
    return _c[k]
