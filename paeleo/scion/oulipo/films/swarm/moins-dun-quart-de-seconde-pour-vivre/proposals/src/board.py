import os
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(H, '..')
REF = os.path.normpath(os.path.join(H, '../../../../../assets/references/iteration-001.webp'))
f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 26)
f2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
CW, CH, LB, GAP = 960, 540, 64, 20
B = Image.new('RGB', (2 * CW + 3 * GAP, 2 * (CH + LB) + 3 * GAP), (24, 24, 24))
d = ImageDraw.Draw(B)
cells = [(Image.open(REF).convert('RGB'), 'REFERENCE', 'Menu & Trondheim (1991): one plate, changing balloons, panel 3 silent'),
         (Image.open(os.path.join(P, 'kf-1.png')), '1 · BRUSH PLATE, WRITTEN BALLOONS', 'handmade brush plate x8, hand lettering written on stroke by stroke · 0:47'),
         (Image.open(os.path.join(P, 'kf-2.png')), '2 · LIGHTBOX PUPPET, HINGED BALLOONS', 'cut-card silhouette + foraged 1865 envelope (LoC, PD), rod balloons · 0:41'),
         (Image.open(os.path.join(P, 'kf-3.png')), '3 · PROOF PRESS AND LETTER STAMPS', 'white-line relief pulled x4, letters pressed one stamp at a time · 0:12')]
for i, (im, t, s) in enumerate(cells):
    cx, cy = GAP + (i % 2) * (CW + GAP), GAP + (i // 2) * (CH + LB + GAP)
    if i == 0:
        sc = CW / im.width; im = im.resize((CW, int(im.height * sc)), Image.LANCZOS)
        bg = Image.new('RGB', (CW, CH), (255, 255, 255)); bg.paste(im, (0, (CH - im.height) // 2)); im = bg
    else:
        im = im.resize((CW, CH), Image.LANCZOS)
    B.paste(im, (cx, cy))
    d.text((cx, cy + CH + 8), t, font=f, fill=(240, 236, 226))
    d.text((cx, cy + CH + 38), s, font=f2, fill=(180, 176, 168))
B.save(os.path.join(P, 'board.jpg'), quality=90)
print(B.size)
