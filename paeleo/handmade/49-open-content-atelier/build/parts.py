"""Semantic cropper + character extraction lead.
Every visible piece of the film is cut here from a Smithsonian Open Access (CC0) object image kept in sources/media/.
A part = (source idsId, polygon in source-file pixels, key mode, pivots).  The polygon is the scissors line drawn by hand
on gridded crops (build/grid.py); the key refines the cut inside the polygon:
  dog   : keep cream-white fur and liver-brown patches, drop green/blue/dark ground (Currier lithographs)
  dark  : keep black paper (Edouart cut silhouettes)
  none  : the polygon is the cut
Writes build/cache/parts/<name>.jpg (RGB) + <name>_a.jpg (alpha) and build/cache/parts/parts.json (provenance + pivots).
Coordinates in parts.json are in the part's own pixel frame (origin = top-left of the polygon's bounding box)."""
import json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'sources', 'media')
OUT = os.path.join(HERE, 'cache', 'parts'); os.makedirs(OUT, exist_ok=True)

WOOD = 'SAAM-1973.122.4_1'     # Currier & Ives, Woodcock Shooting (standing pointer, faces left)
JUNO = 'SAAM-1973.122.5_1'     # Currier, Juno (pointer lying, faces right)
POINT = 'SAAM-1973.122.13_1'   # Parsons / Currier & Ives, American Field Sports "On a Point" (look-back head)
FAM = 'SAAM-1981.172.33_1'     # Edouart, Father, Mother, and Boy (cut silhouette)
BOY = 'SAAM-1981.172.31_1'     # Edouart, Boy with Dog (cut silhouette, pointing arm)
DOOR = 'SAAM-1989.30.3_1'      # Jose Dolores Lopez, Screen Door (carved pine and aspen)
ROOM = 'SAAM-1916.6.39_1'      # E. F. Andrews, Interior of a House
DUSK = 'SAAM-1913.3.3_2'       # N. MacGilvary, Twilight after the Rain

P = {
 # ---------------- the dog, standing (Woodcock Shooting pointer); faces left in the source
 'w_head': dict(src=WOOD, key='dog', poly=[(518, 726), (536, 711), (575, 704), (612, 709), (645, 716), (668, 727), (680, 760),
          (678, 800), (660, 814), (628, 808), (608, 792), (585, 777), (560, 770), (535, 762), (518, 748)],
          piv={'neck': (668, 778), 'nose': (527, 736)}, role='dog head + ear (profile)'),
 'w_torso': dict(src=WOOD, key='dog', poly=[(640, 716), (700, 708), (780, 708), (860, 710), (905, 716), (930, 728), (940, 748),
          (925, 790), (905, 812), (870, 820), (830, 828), (790, 834), (740, 838), (700, 838), (668, 830), (652, 805), (646, 760)],
          piv={'neck': (668, 778), 'tail': (930, 742), 'shoulder': (690, 812), 'hip': (895, 800), 'hip_far': (850, 815),
               'back': (790, 712)}, role='dog torso + neck'),
 'w_tail': dict(src=WOOD, key='dog', poly=[(918, 728), (960, 734), (1010, 744), (1062, 752), (1062, 762), (1000, 758), (950, 754),
          (918, 756)], piv={'root': (925, 744)}, role='dog tail'),
 'w_fore': dict(src=WOOD, key='dog', poly=[(668, 808), (712, 808), (716, 834), (700, 850), (680, 868), (676, 882), (662, 890),
          (640, 890), (636, 876), (652, 860), (666, 838)], piv={'top': (690, 812), 'foot': (652, 884)},
          role='dog near foreleg'),
 'w_hind': dict(src=WOOD, key='dog', poly=[(880, 790), (918, 792), (950, 812), (985, 832), (1000, 852), (1012, 872), (1022, 886),
          (1012, 896), (994, 892), (986, 868), (966, 848), (930, 836), (896, 822), (878, 806)],
          piv={'top': (895, 800), 'foot': (1006, 888)}, role='dog near hind leg'),
 'w_thigh': dict(src=WOOD, key='dog', poly=[(876, 788), (918, 790), (950, 810), (985, 824), (1000, 834), (994, 848), (966, 848),
          (930, 838), (896, 824), (874, 806)], piv={'top': (895, 800), 'hock': (990, 838)}, role='dog hind thigh (hip to hock)'),
 'w_shank': dict(src=WOOD, key='dog', poly=[(972, 826), (1000, 828), (1012, 868), (1024, 886), (1014, 897), (994, 893), (986, 870),
          (976, 846)], piv={'hock': (990, 838), 'foot': (1006, 888)}, role='dog hind shank + paw (hock to paw)'),
 'w_hindfar': dict(src=WOOD, key='dog', poly=[(812, 822), (862, 818), (878, 832), (872, 852), (862, 870), (858, 886), (842, 890),
          (832, 884), (842, 866), (846, 846), (822, 838)], piv={'top': (850, 815), 'foot': (846, 884)},
          role='dog far hind leg'),
 # ---------------- the dog, lying (Juno); faces right in the source
 'j_body': dict(src=JUNO, key='juno', hole=40000, poly=[(250, 880), (265, 790), (330, 730), (430, 690), (640, 662), (860, 648), (1010, 640),
          (1060, 690), (1190, 690), (1200, 780), (1215, 870), (1290, 885), (1450, 890), (1572, 898), (1594, 925), (1560, 950),
          (1370, 950), (1230, 975), (1140, 1000), (1138, 1092), (940, 1098), (860, 1062), (740, 1108), (600, 1092),
          (430, 1142), (285, 1108), (252, 1045)], piv={'neck': (1120, 690), 'rump': (255, 900), 'paw': (1590, 925),
          'floor': (900, 1100)}, role='dog lying body, legs folded'),
 'j_head': dict(src=JUNO, key='none', poly=[(1030, 445), (1060, 425), (1090, 412), (1160, 405), (1240, 405), (1268, 412),
          (1300, 450), (1335, 505), (1342, 522), (1372, 535), (1398, 555), (1396, 585), (1370, 596), (1312, 592), (1262, 612),
          (1215, 640), (1196, 690), (1130, 704), (1060, 700), (1024, 660), (1016, 560), (1022, 480)],
          piv={'neck': (1120, 690), 'nose': (1390, 565)}, role='dog head (lying), 3/4'),
 'j_neck': dict(src=JUNO, key='none', poly=[(1050, 615), (1180, 615), (1198, 650), (1188, 700), (1060, 705), (1040, 660)],
          piv={'neck': (1120, 690)}, role='dog neck (lying): stretches when the head reaches in'),
 # ---------------- the look-back head (On a Point, left pointer, head turned over its shoulder); faces left
 'o_head': dict(src=POINT, key='none', poly=[(855, 525), (868, 506), (886, 482), (890, 456), (898, 436), (950, 418),
          (990, 420), (1040, 440), (1064, 462), (1062, 520), (1066, 560), (1052, 598), (1002, 612), (962, 602), (932, 582),
          (900, 562), (872, 558), (855, 545)], piv={'neck': (1000, 592), 'nose': (856, 534)},
          role='dog head looking back (3/4)'),
 # ---------------- the person (Edouart): standing man, faces right; pointing arm from the boy
 'm_upper': dict(src=FAM, key='dark', poly=[(505, 480), (600, 470), (650, 520), (700, 640), (700, 980), (660, 985),
          (520, 985), (505, 900)], piv={'hip': (590, 960), 'shoulder': (625, 640), 'neck': (615, 600)},
          role='person torso + head (silhouette)'),
 'm_thigh': dict(src=FAM, key='dark', poly=[(540, 930), (660, 930), (660, 1075), (545, 1075)],
          piv={'hip': (595, 945), 'knee': (600, 1065)}, role='person thighs'),
 'm_shin': dict(src=FAM, key='dark', poly=[(530, 1050), (680, 1050), (690, 1205), (520, 1205)],
          piv={'knee': (600, 1062), 'heel': (575, 1190)}, role='person shins + shoes'),
 'b_arm': dict(src=BOY, key='dark', poly=[(668, 712), (760, 708), (840, 690), (905, 690), (912, 760), (840, 790), (760, 776),
          (680, 760)], piv={'shoulder': (890, 725), 'hand': (680, 735)}, role='person reaching arm (pointing)'),
 # ---------------- the world
 'bench': dict(src=ROOM, key='none', poly=[(90, 805), (380, 805), (380, 880), (362, 880), (362, 1100), (330, 1100), (330, 880),
          (135, 880), (135, 1100), (100, 1100), (100, 880), (90, 880)], piv={'seat': (235, 808)}, role='bench (seat)'),
 'door': dict(src=DOOR, key='none', poly=[(60, 40), (860, 40), (860, 1760), (60, 1760)], piv={}, role='door leaf'),
}


def polymask(size, poly):
    m = Image.new('L', size, 0); ImageDraw.Draw(m).polygon(poly, fill=255); return np.array(m) > 0


def key(rgb, mode):
    r, g, b = [rgb[..., k].astype(float) for k in range(3)]
    lum = .3 * r + .59 * g + .11 * b; mx = rgb.max(-1).astype(float); mn = rgb.min(-1).astype(float)
    if mode == 'dog':
        white = (lum > 125) & (r >= g - 6) & (mx - mn < 80)
        liver = (r > 80) & (r - b > 38) & (r - g > 14)
        return white | liver
    if mode == 'juno':   # Juno: drop only the dark green-grey ground; keep the liver patch and spots
        return ~((lum < 128) & (g >= r - 10))
    if mode == 'dark':
        return lum < 95
    return np.ones(rgb.shape[:2], bool)


def cut(name, d):
    im = Image.open(os.path.join(SRC, d['src'] + '.jpg')).convert('RGB')
    xs = [p[0] for p in d['poly']]; ys = [p[1] for p in d['poly']]
    x0, y0, x1, y1 = min(xs) - 2, min(ys) - 2, max(xs) + 3, max(ys) + 3
    crop = np.array(im.crop((x0, y0, x1, y1)))
    pm = polymask((x1 - x0, y1 - y0), [(x - x0, y - y0) for x, y in d['poly']])
    k = key(crop, d['key']) & pm
    if d['key'] != 'none':
        k = ndi.binary_closing(k, iterations=2) & pm
        holes = ndi.binary_fill_holes(k) & ~k
        lab, n = ndi.label(holes)
        if n:
            sizes = ndi.sum(holes, lab, range(1, n + 1))
            k |= np.isin(lab, 1 + np.nonzero(sizes < d.get('hole', 400))[0])
        lab, n = ndi.label(k)
        if n:
            sizes = ndi.sum(k, lab, range(1, n + 1)); k = lab == (1 + int(np.argmax(sizes)))
    a = Image.fromarray((k * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    Image.fromarray(crop).save(os.path.join(OUT, name + '.jpg'), quality=95)
    a.save(os.path.join(OUT, name + '_a.jpg'), quality=95)
    return {'src': d['src'], 'role': d['role'], 'key': d['key'], 'bbox_in_source': [x0, y0, x1, y1],
            'polygon_in_source': d['poly'], 'pivots': {k2: [v[0] - x0, v[1] - y0] for k2, v in d['piv'].items()},
            'size': [x1 - x0, y1 - y0], 'area_px': int(k.sum())}


def plates():
    """Backdrop plates (rectangular crops, no mask): name -> (src, box)."""
    return {'room': (ROOM, (0, 0, 1120, 1261)), 'dusk': (DUSK, (0, 60, 1469, 1150)),
            'floor': (ROOM, (0, 1010, 1800, 1261)), 'jamb': (ROOM, (470, 60, 560, 1000)),
            'reveal': (ROOM, (590, 140, 960, 1000))}


if __name__ == '__main__':
    meta = {n: cut(n, d) for n, d in P.items()}
    for n, (s, box) in plates().items():
        Image.open(os.path.join(SRC, s + '.jpg')).convert('RGB').crop(box).save(os.path.join(OUT, n + '.jpg'), quality=92)
        meta[n] = {'src': s, 'role': 'plate', 'key': 'none', 'bbox_in_source': list(box), 'size': [box[2] - box[0], box[3] - box[1]]}
    json.dump(meta, open(os.path.join(OUT, 'parts.json'), 'w'), indent=1)
    # proof sheet: every masked part on mid-grey
    ims = []
    for n in P:
        rgb = Image.open(os.path.join(OUT, n + '.jpg')); a = Image.open(os.path.join(OUT, n + '_a.jpg')).convert('L')
        bg = Image.new('RGB', rgb.size, (120, 140, 120)); bg.paste(rgb, (0, 0), a); bg.thumbnail((360, 360)); ims.append((n, bg))
    W = 1800; sheet = Image.new('RGB', (W, 380 * ((len(ims) + 4) // 5)), 'white'); dr = ImageDraw.Draw(sheet)
    for i, (n, im) in enumerate(ims):
        x, y = (i % 5) * 360, (i // 5) * 380; sheet.paste(im, (x, y)); dr.text((x + 4, y + 362), n, fill='black')
    sheet.save(os.path.join(HERE, 'cache', 'parts_sheet.jpg'), quality=85)
    print('parts', len(P), 'plates', len(plates()))
