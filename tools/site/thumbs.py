"""Poster and thumbnail for every film in the catalog.
The frame: 16 candidates between 10% and 90% of the film; each is scored for detail (Laplacian variance), colour and a
mid-range exposure, and frames that are mostly one flat tone (title cards, black) score low. The best becomes the clean
poster (media/posters/<id>.jpg); the thumbnail (media/thumbs/<id>.jpg) adds the program tag, the title and the running time."""
import os, sys, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H); import catalog as C
R = '/home/claude/bolas'; HOME = '/home/claude'; FP = H + '/../fontpkg/'
os.makedirs(R + '/media/posters', exist_ok=True); os.makedirs(R + '/media/thumbs', exist_ok=True)
F900 = lambda s: ImageFont.truetype(FP + 'BigShoulders900.ttf', s); FM = lambda s: ImageFont.truetype(FP + 'JetBrainsMono.ttf', s)
PROG = {p['id']: p for p in C.PROGRAMS}
def duration(p): return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p], capture_output=True, text=True).stdout)
def frame(p, t):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.2f}', '-i', p, '-frames:v', '1', '-vf', 'scale=1280:-2', '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True)
    return cv2.imdecode(np.frombuffer(r.stdout, np.uint8), 1)
def presence(im):
    """share of the frame in the family's own colours: Bola's yellow and Shim's teal"""
    h = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); sat = (h[..., 1] > 120) & (h[..., 2] > 140)
    return float((((h[..., 0] >= 20) & (h[..., 0] <= 32)) | ((h[..., 0] >= 78) & (h[..., 0] <= 92)))[sat].sum() / sat.size) if sat.any() else 0.
def score(im):
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); lap = cv2.Laplacian(g, cv2.CV_32F).var()
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); col = hsv[..., 1].mean() / 255; m = g.mean() / 255
    flat = (np.abs(g.astype(np.float32) - np.median(g)) < 12).mean()           # share of the frame that is one tone
    return np.log1p(lap) * (0.5 + col) * (1 - abs(m - .45) * 1.4) * (1.15 - flat)
def fmt(d): return f'{int(d // 60)}:{int(d % 60):02d}'
for f in C.FILMS:
    src = os.path.join(HOME, f['src']); d = duration(src); f['dur'] = d
    pick = f.get('at')
    if pick is None:
        fam = f['program'] in ('family', 'cineosis')
        cands = [(score(im) * ((1 + 4 * min(presence(im), .03) / .03) if fam else 1), t, im) for t in np.linspace(.1, .9, 24) * d for im in [frame(src, t)] if im is not None]
        _, t, im = max(cands, key=lambda c: c[0])
    else: t = pick * d; im = frame(src, t)
    im = cv2.resize(im, (1280, 720)) if im.shape[:2] != (720, 1280) else im
    cv2.imwrite(f'{R}/media/posters/{f["id"]}.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 84])
    # the thumbnail: darkened lower band, program tag block, title, running time
    pil = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)).convert('RGBA'); W, Hh = pil.size
    grad = Image.new('L', (1, Hh)); [grad.putpixel((0, y), int(max(0, (y - Hh * .45) / (Hh * .55)) ** 1.4 * 235)) for y in range(Hh)]
    shade = Image.new('RGBA', (W, Hh), (8, 9, 12, 0)); shade.putalpha(grad.resize((W, Hh))); pil = Image.alpha_composite(pil, shade)
    dr = ImageDraw.Draw(pil); p = PROG[f['program']]
    tag = (p['title'] if p['id'] != 'cineosis' else 'CINEOSIS · the crash-test family').upper()
    tw = dr.textlength(tag, font=FM(22)); dr.rectangle([40, 38, 40 + tw + 28, 38 + 40], fill=p['color']); dr.text((54, 45), tag, font=FM(22), fill=(11, 13, 16))
    title = f['title'].upper(); size = 104
    while dr.textlength(title, font=F900(size)) > W - 80 and size > 48: size -= 4
    dr.text((40, Hh - 54 - size), title, font=F900(size), fill=(255, 255, 255))
    dr.text((W - 40 - dr.textlength(fmt(d), font=FM(24)), Hh - 50), fmt(d), font=FM(24), fill=(230, 232, 236))
    dr.rectangle([40, Hh - 36, 40 + 120, Hh - 30], fill=p['color'])
    pil.convert('RGB').save(f'{R}/media/thumbs/{f["id"]}.jpg', quality=84)
    print(f['id'], fmt(d), f'frame at {t:.1f}s', flush=True)
