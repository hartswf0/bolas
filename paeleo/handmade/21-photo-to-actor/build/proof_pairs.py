"""Review pairs: the same expression (ears flat, mouth open, brow up) driven by the AUTOMATIC landmarks vs the CORRECTED
ones, on the heads where the automatic fit failed. Shows what the failure would have looked like on screen.
-> proof/expression_auto_vs_corrected.jpg"""
import os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); FOLDER = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import actor

rows = []
for name in ('profile', 'low', 'back'):
    pair = []
    for which in ('auto', 'corrected'):
        actor.LM[name]['used'] = which
        h = actor.Head(name)
        neutral = h.compose(0.65, 0.0, 0.0); act = h.compose(0.0, 1.0, 1.0)
        W, H = neutral.size
        pane = Image.new('RGB', (W * 2 * 3 + 10, H * 3 + 24), (24, 24, 30))
        for k, im in enumerate((neutral, act)):
            bg = Image.new('RGBA', im.size, (60, 62, 74, 255)); bg.alpha_composite(im)
            pane.paste(bg.convert('RGB').resize((W * 3, H * 3), Image.LANCZOS), (k * (W * 3 + 10), 24))
        ImageDraw.Draw(pane).text((4, 4), '%s head, %s landmarks: neutral | ears flat + mouth open + brow up' % (name, which.upper()), fill=(255, 255, 255))
        pair.append(pane)
    rows.append(pair)
    actor.LM[name]['used'] = 'corrected'
Wt = max(p[0].width + p[1].width + 20 for p in rows); Ht = sum(max(p[0].height, p[1].height) + 10 for p in rows)
S = Image.new('RGB', (Wt, Ht), (12, 12, 16)); y = 0
for a, b in rows:
    S.paste(a, (0, y)); S.paste(b, (a.width + 20, y)); y += max(a.height, b.height) + 10
S.save(os.path.join(FOLDER, 'proof', 'expression_auto_vs_corrected.jpg'), quality=88)
print('ok', S.size)
