"""SCION 40 · the two sets.
  layout sheet (capture): the paper sheet taped to the table under the overhead camera: pencil layout of the floor line,
      the wall, the doorway, a metre ruler along the porch and four corner fiducials for calibration.
  finished set (replay):  the new set the capture is replayed on: torn-paper dusk, a cut-away house with a room that can
      be dark or lit, porch boards, steps. Two versions of the room (dark, lit); the film mixes them by how far the
      light tissue has been slid out (a recovered transform).
Writes cache/set_sheet.png, cache/set_dark.png, cache/set_lit.png, cache/set_front.png (pieces drawn over the dog: none
for now), and data/sheet.json (the corner fiducial ids and their stage positions)."""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

CORNER_IDS = [120, 121, 122, 123]
CORNERS = [(28, 28), (W - 28, 28), (W - 28, H - 28), (28, H - 28)]


def paper_fill(img, poly, col, seed, amt=0.08, jit=1.2, line=None, blur=0):
    lay = Image.new('L', img.size, 0)
    d = ImageDraw.Draw(lay)
    d.polygon([tuple(p) for p in jitter_poly(poly, jit, seed, 5.0)], fill=255)
    if blur:
        lay = lay.filter(ImageFilter.GaussianBlur(blur))
    g = grain(img.size[1], img.size[0], seed)
    c = np.clip(np.array(col, np.float32)[None, None, :] * (1 + amt * g)[..., None], 0, 255).astype(np.uint8)
    # a soft shadow under each layer: the paper is lifted a little
    sh = lay.filter(ImageFilter.GaussianBlur(3)).point(lambda v: int(v * .33))
    shadow = Image.new('RGBA', img.size, (18, 12, 8, 255))
    shadow.putalpha(sh)
    img.alpha_composite(shadow.transform(img.size, Image.AFFINE, (1, 0, -2, 0, 1, -3)))
    top = Image.fromarray(c, 'RGB').convert('RGBA')
    top.putalpha(lay)
    img.alpha_composite(top)
    if line:
        ImageDraw.Draw(img).line([tuple(p) for p in jitter_poly(poly, jit, seed, 5.0)] + [tuple(jitter_poly(poly, jit, seed, 5.0)[0])], fill=line, width=1)


def torn_band(y0, amp, seed, x0=-20, x1=W + 20, bottom=H + 20):
    rng = np.random.default_rng(seed)
    xs = np.linspace(x0, x1, 90)
    ys = y0 + amp * (np.sin(xs / 140 + rng.random() * 6) * .6 + np.sin(xs / 37 + rng.random() * 6) * .3) + rng.normal(0, amp * .12, len(xs))
    return np.array(list(zip(xs, ys)) + [(x1, bottom), (x0, bottom)])


def finished(lit):
    img = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    # sky: dusk in torn bands
    bands = [(0, (40, 44, 82)), (150, (66, 62, 104)), (270, (112, 84, 116)), (360, (172, 112, 104)), (420, (214, 150, 106))]
    for k, (y, c) in enumerate(bands):
        paper_fill(img, torn_band(y, 10, 30 + k), c, 30 + k, amt=0.05)
    # the moon
    d = ImageDraw.Draw(img)
    moon = Image.new('L', (W, H), 0); dm = ImageDraw.Draw(moon)
    dm.ellipse([760, 70, 812, 122], fill=255); dm.ellipse([774, 62, 826, 114], fill=0)
    mc = Image.new('RGBA', (W, H), (236, 226, 196, 255)); img.paste(mc, (0, 0), moon)
    # hills and a far fence of paper strips
    paper_fill(img, torn_band(470, 16, 41), (46, 50, 66), 41, amt=0.06)
    paper_fill(img, torn_band(520, 8, 42), (36, 40, 52), 42, amt=0.06)
    for k, x in enumerate(range(560, 1280, 64)):
        paper_fill(img, np.array([(x, 512), (x + 9, 510), (x + 10, 600), (x - 1, 600)]), (64, 60, 66), 60 + k, amt=0.05, jit=0.6)
    paper_fill(img, np.array([(550, 534), (1290, 528), (1290, 538), (550, 544)]), (64, 60, 66), 59, amt=0.05, jit=0.6)
    # porch floor and boards; steps at the end of the porch (x = 4.9 m)
    xs = x_stage(4.9)
    paper_fill(img, np.array([(WALL[0], 598), (xs, 598), (xs, H + 5), (WALL[0], H + 5)]), (104, 76, 56), 70, amt=0.1)
    for k, y in enumerate((612, 632, 656, 684)):
        paper_fill(img, np.array([(WALL[0], y), (xs, y - 1), (xs, y + 2), (WALL[0], y + 2)]), (72, 52, 40), 71 + k, amt=0.05, jit=0.4)
    for k in range(3):
        paper_fill(img, np.array([(xs + k * 22, 610 + k * 30), (W + 5, 610 + k * 30), (W + 5, H + 5), (xs + k * 22, H + 5)]), (90 - 8 * k, 66 - 6 * k, 50 - 4 * k), 80 + k, amt=0.1)
    # the room: back wall, floor, lamp, table, picture
    room_w = (196, 150, 104) if lit else (70, 64, 78)
    paper_fill(img, np.array([(-5, ROOF + 10), (WALL[0], ROOF + 10), (WALL[0], GROUND), (-5, GROUND)]), room_w, 90, amt=0.07, jit=0.5)
    paper_fill(img, np.array([(-5, GROUND - 2), (WALL[0], GROUND - 2), (WALL[0], H + 5), (-5, H + 5)]), (122, 84, 56) if lit else (52, 42, 40), 91, amt=0.1, jit=0.5)
    for k, y in enumerate((620, 650, 690)):
        paper_fill(img, np.array([(-5, y), (WALL[0], y), (WALL[0], y + 2), (-5, y + 2)]), (90, 60, 42) if lit else (40, 32, 30), 92 + k, amt=0.05, jit=0.3)
    # picture frame on the back wall
    paper_fill(img, np.array([(40, 250), (120, 248), (122, 330), (42, 332)]), (110, 80, 52) if lit else (48, 42, 50), 95, amt=0.06, jit=0.5)
    paper_fill(img, np.array([(50, 260), (112, 258), (112, 320), (52, 322)]), (150, 160, 140) if lit else (60, 62, 70), 96, amt=0.06, jit=0.5)
    # lamp on a small table at the back of the room
    paper_fill(img, np.array([(176, 500), (266, 500), (262, 512), (180, 512)]), (90, 60, 40) if lit else (40, 34, 36), 97, amt=0.06, jit=0.4)
    for lx in (186, 252):
        paper_fill(img, np.array([(lx, 510), (lx + 6, 510), (lx + 6, GROUND), (lx, GROUND)]), (80, 54, 38) if lit else (36, 30, 32), 98 + lx, amt=0.05, jit=0.3)
    paper_fill(img, np.array([(218, 420), (224, 420), (224, 500), (218, 500)]), (50, 40, 34), 99, amt=0.05, jit=0.3)
    paper_fill(img, np.array([(196, 380), (246, 380), (258, 424), (184, 424)]), (255, 226, 150) if lit else (110, 100, 96), 100, amt=0.05, jit=0.5)
    if lit:
        glow = Image.new('L', (W, H), 0)
        ImageDraw.Draw(glow).ellipse([60, 260, 380, 560], fill=120)
        glow = glow.filter(ImageFilter.GaussianBlur(60))
        img.alpha_composite(Image.merge('RGBA', (Image.new('L', (W, H), 255), Image.new('L', (W, H), 214), Image.new('L', (W, H), 140), glow)))
    # the house in section: the wall cut through, above the door and below the floor; the roof
    paper_fill(img, np.array([(WALL[0], ROOF), (WALL[1], ROOF), (WALL[1], LINTEL), (WALL[0], LINTEL)]), (46, 34, 30), 110, amt=0.06, jit=0.4)
    paper_fill(img, np.array([(-5, ROOF - 6), (WALL[1] + 4, ROOF - 6), (WALL[1] + 4, ROOF + 12), (-5, ROOF + 12)]), (46, 34, 30), 111, amt=0.06, jit=0.4)
    paper_fill(img, np.array([(-30, ROOF - 4), (180, 20), (WALL[1] + 70, ROOF - 2), (WALL[1] + 70, ROOF + 4), (-30, ROOF + 4)]), (88, 52, 46), 112, amt=0.08, jit=1.0)
    # the door frame faces (light wood), the sill (a raised strip at the threshold)
    paper_fill(img, np.array([(WALL[0] - 4, LINTEL - 4), (WALL[1] + 4, LINTEL - 4), (WALL[1] + 4, LINTEL + 6), (WALL[0] - 4, LINTEL + 6)]), (176, 150, 112), 113, amt=0.06, jit=0.3)
    paper_fill(img, np.array([(WALL[0] - 6, GROUND - 6), (WALL[1] + 6, GROUND - 6), (WALL[1] + 8, GROUND + 2), (WALL[0] - 8, GROUND + 2)]), (176, 150, 112), 114, amt=0.06, jit=0.3)
    paper_fill(img, np.array([(WALL[0], GROUND + 2), (WALL[1], GROUND + 2), (WALL[1], H + 5), (WALL[0], H + 5)]), (46, 34, 30), 115, amt=0.06, jit=0.3)
    # the outside face of the house wall above/beside: siding strip to the right of the section is not shown (cut-away)
    a = np.asarray(img.convert('RGB'), np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    vig = 1 - 0.28 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2
    a *= vig[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def sheet():
    """the layout sheet, as it lies on the table: off-white paper, pencil, corner fiducials"""
    g = grain(H, W, 7)
    a = np.zeros((H, W, 3), np.float32) + np.array([232, 228, 214])
    a *= (1 + 0.025 * g)[..., None]
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    pen = (120, 118, 116)
    d.line([(0, GROUND), (W, GROUND)], fill=pen, width=2)
    d.rectangle([WALL[0], ROOF, WALL[1], LINTEL], outline=pen, width=2)
    d.rectangle([WALL[0], GROUND, WALL[1], H - 60], outline=pen, width=2)
    d.line([(0, ROOF), (WALL[1], ROOF)], fill=pen, width=2)
    for m in range(0, 5):
        X = x_stage(m + 0.56) if m else SILL_X
        X = x_stage(float(m))
        if X < W - 40:
            d.line([(X, GROUND + 4), (X, GROUND + 22)], fill=pen, width=2)
            d.text((X + 3, GROUND + 26), '%d m' % m, fill=pen, font=font('mono', 14))
    d.text((WALL[0] - 6, GROUND + 70), 'SILL', fill=pen, font=font('mono', 14))
    d.text((40, 140), 'ROOM (inside)', fill=pen, font=font('mono', 14))
    d.text((720, 140), 'PORCH (outside)', fill=pen, font=font('mono', 14))
    d.text((60, H - 56), 'PAE-02 / SCION 40 layout sheet  1 m = 200 px', fill=pen, font=font('mono', 13))
    a = np.asarray(img).copy()
    for ident, (cx, cy) in zip(CORNER_IDS, CORNERS):
        fi = fid_image(ident, cell=6)
        s = fi.shape[0]
        a[cy - s // 2 - 4:cy + s // 2 + 4, cx - s // 2 - 4:cx + s // 2 + 4] = 246
        a[cy - s // 2:cy - s // 2 + s, cx - s // 2:cx - s // 2 + s] = fi[..., None]
    return Image.fromarray(a)


def main():
    os_makedirs(CACHE, DATA)
    finished(False).save(os.path.join(CACHE, 'set_dark.png'))
    finished(True).save(os.path.join(CACHE, 'set_lit.png'))
    sheet().save(os.path.join(CACHE, 'set_sheet.png'))
    json.dump(dict(corner_ids=CORNER_IDS, corners_stage=CORNERS, cell=6), open(os.path.join(DATA, 'sheet.json'), 'w'), indent=1)
    print('sets ok')


if __name__ == '__main__':
    main()
