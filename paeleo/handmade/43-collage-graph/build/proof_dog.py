"""proof: the dog graph alone, enlarged, at chosen score frames (with anchors and planted feet)"""
import sys, os
from PIL import Image, ImageDraw
import scene
fs = [int(a) for a in sys.argv[1:]] or [0, 30, 60, 84, 88, 94, 110, 150, 180, 186, 196, 200, 360, 372, 384, 396, 540, 576, 600, 640, 660, 700]
tiles = []
for i in fs:
    lay = Image.new('RGBA', (scene.W, scene.H), (120, 130, 150, 255))
    info = scene.draw_dog(lay, i)
    gy = info['gy']; x = scene.PX(info['g']['x'])
    c = lay.crop((int(x - 170), int(gy - 200), int(x + 170), int(gy + 20))).resize((680, 440), Image.LANCZOS)
    d = ImageDraw.Draw(c)
    d.text((6, 4), '%d t=%.2f %s %s' % (i, info['g']['t'], info['g']['state'], info['g']['head'][0]), fill=(255, 255, 0))
    d.line([(0, 400), (680, 400)], fill=(255, 0, 0))
    tiles.append(c)
cols = 4
sh = Image.new('RGB', (680 * cols, 440 * ((len(tiles) + cols - 1) // cols)))
for n, c in enumerate(tiles): sh.paste(c, ((n % cols) * 680, (n // cols) * 440))
sh.save(os.path.join(scene.HERE, '../proof/dog_poses.jpg'), quality=85)
