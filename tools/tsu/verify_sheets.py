"""Contact sheet per case of the sheets as used, caption ABOVE each image, to check every caption against its picture."""
import sys, os, json, textwrap
sys.path.insert(0, '.'); import data as D
from PIL import Image, ImageDraw, ImageFont
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
S = '/tmp/claude-0/-home-claude/4fcf2301-cc19-5f90-be19-3bb1b3367fc1/scratchpad/'
for c in D.CASES:
    if len(sys.argv) > 1 and c['slug'] not in sys.argv[1:]: continue
    items = [x for x in c['sheets'] if not isinstance(x, str)]
    TW, TH, cols = 420, 260, 4; rows = (len(items) + cols - 1) // cols
    out = Image.new('RGB', (cols * TW, rows * (TH + 60)), (25, 25, 25)); d = ImageDraw.Draw(out)
    for i, (p, cap) in enumerate(items):
        x, y = (i % cols) * TW, (i // cols) * (TH + 60)
        d.text((x + 4, y + 2), '\n'.join(textwrap.wrap(f'{i} {cap}', 52)[:3]), fill=(255, 220, 120), font=F)
        im = Image.open(p).convert('RGB'); im.thumbnail((TW - 8, TH - 6)); out.paste(im, (x + 4, y + 56))
    out.save(S + f'vf_{c["slug"]}.jpg', quality=72); print(c['slug'], len(items))
