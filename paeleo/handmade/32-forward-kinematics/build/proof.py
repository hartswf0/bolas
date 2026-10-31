"""SCION 32 · proof images from the encoded film (frames extracted from ../film.mp4, never from the cache):
proof/choices_full.jpg   the choice moments, full frame
proof/choices_crop.jpg   the same, cropped on the dog at 2x
proof/joint_overlay.jpg  the joint graph projected over four film frames, and the same pose with the right hip +12 deg and the
                         right shoulder -15 deg (dashed): the descendants follow, the rest does not move."""
import json, os, subprocess
from PIL import Image, ImageDraw
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(H, '..', 'proof'); os.makedirs(P, exist_ok=True)
FILM = os.path.join(H, '..', 'film.mp4'); TMP = os.path.join(H, 'cache', 'proofframes'); os.makedirs(TMP, exist_ok=True)
tr = json.load(open(os.path.join(H, '..', 'trace.json')))['frames']
def grab(i):
    out = os.path.join(TMP, f'film_{i:03d}.jpg')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', FILM, '-vf', f'select=eq(n\\,{72 + i})', '-vsync', '0', '-frames:v', '1', '-q:v', '2', out], check=True)
    return Image.open(out).convert('RGB')
moments = [(22, 'watch 0.9 s'), (36, 'backs away 1.5 s'), (94, 'back turned 3.9 s'), (150, 'lying, back turned 6.25 s'), (176, 'head leads 7.33 s'), (182, 'head round 7.58 s'),
           (190, 'rises 7.9 s'), (216, 'watching 9 s'), (372, 'head low 15.5 s'), (528, 'head low 22 s'), (588, 'lies across 24.5 s'), (648, 'looks in 27 s'), (672, 'stays 28 s'), (760, 'stays 31.7 s')]
ims = [(grab(i), l, i) for i, l in moments]
cols = 4; rows = (len(ims) + cols - 1) // cols
full = Image.new('RGB', (cols * 480, rows * 270)); crop = Image.new('RGB', (cols * 480, rows * 270))
for k, (im, l, i) in enumerate(ims):
    x, y = (k % cols) * 480, (k // cols) * 270
    full.paste(im.resize((480, 270)), (x, y)); ImageDraw.Draw(full).text((x + 6, y + 6), l, fill=(255, 230, 120))
    f = tr[i]; cx, cy = f['x_screen'] or 640, f['y_screen'] or 400
    w, h = 480, 270; x0 = int(min(max(cx - w / 2, 0), 1280 - w)); y0 = int(min(max(cy - h / 2, 0), 720 - h))
    crop.paste(im.crop((x0, y0, x0 + w, y0 + h)), (x, y)); ImageDraw.Draw(crop).text((x + 6, y + 6), l + ' (crop 1:1)', fill=(255, 230, 120))
full.save(os.path.join(P, 'choices_full.jpg'), quality=88); crop.save(os.path.join(P, 'choices_crop.jpg'), quality=88)
sel = [86, 182, 456, 648]
J = json.loads(subprocess.run(['node', os.path.join(H, 'joints2d.js'), ','.join(map(str, sel))], capture_output=True, text=True, check=True).stdout)
sheet = Image.new('RGB', (1280, 720))
for k, i in enumerate(sel):
    im = grab(i); d = ImageDraw.Draw(im)
    jj = {j['n']: j for j in J[str(i)]['joints']}; pp = {j['n']: j for j in J[str(i)]['perturbed']}
    for j in J[str(i)]['perturbed']:
        if j['p']:
            a, b = pp[j['p']]['xy'], j['xy']
            if (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 > 0.5: d.line([tuple(a), tuple(b)], fill=(90, 220, 255), width=1)
    for j in J[str(i)]['joints']:
        if j['p']: d.line([tuple(jj[j['p']]['xy']), tuple(j['xy'])], fill=(255, 210, 80), width=2)
    for j in J[str(i)]['joints']:
        x, y = j['xy']; d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 120, 60))
    w = J[str(i)]['anchor']; d.text((10, 10), f'scene frame {i}  head anchor: profile {w["profile"]:.2f} / 3-4 {w["threeq"]:.2f} / rear {w["rear"]:.2f}', fill=(255, 255, 255))
    d.text((10, 26), 'gold: joint graph as rendered   blue: right hip +12 deg, right shoulder -15 deg (descendants follow)', fill=(160, 230, 255))
    sheet.paste(im.resize((640, 360)), ((k % 2) * 640, (k // 2) * 360))
sheet.save(os.path.join(P, 'joint_overlay.jpg'), quality=88)
print('proof images written')
