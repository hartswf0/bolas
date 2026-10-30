"""Image quality critic aid: contact sheet of fetched media (labels = idsId). Usage: contact.py out.jpg files..."""
import sys, os
from PIL import Image, ImageDraw
fs = sys.argv[2:]; c = 5; w = 360
rows = (len(fs) + c - 1) // c; sheet = Image.new('RGB', (c * w, rows * (w + 20)), 'white'); dr = ImageDraw.Draw(sheet)
for k, f in enumerate(fs):
    im = Image.open(f); im.thumbnail((w - 6, w - 6)); x, y = (k % c) * w, (k // c) * (w + 20)
    sheet.paste(im, (x + 3, y + 3)); dr.text((x + 3, y + w + 2), os.path.basename(f)[:50], fill='black')
sheet.save(sys.argv[1], quality=85)
