"""SCION-MAMBETY · the footage hunter. Everything this film is made of is cut from the game's own pictures (make-photo/mesa: its
stills and its two recorded clips, made by this project; no outside footage). This file gathers the plates and cuts the materials:
for each material the hunter searches the footage for the patch whose colour and grain are closest, and logs where it came from."""
import os, json, subprocess, numpy as np
from PIL import Image
SRC = '/home/user/make-photo/mesa'
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, 'footage'); os.makedirs(CACHE, exist_ok=True)
SAFE = (40, 50, 1240, 600)   # inside the game's frame: no title, no captions, no buttons

def frames():
    out = {}
    for f in sorted(os.listdir(SRC)):
        if f.endswith('.jpg') and not f.startswith('paint-sheet'): out[f] = Image.open(os.path.join(SRC, f)).convert('RGB').resize((1280, 720))
    for clip in ('paint.mp4', 'stained-glass.mp4'):
        d = os.path.join(CACHE, clip[:-4]); os.makedirs(d, exist_ok=True)
        if not os.listdir(d): subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', os.path.join(SRC, clip), '-vf', 'fps=2', os.path.join(d, '%03d.jpg')], check=True)
        for g in sorted(os.listdir(d)): out[f'{clip}@{(int(g[:3]) - 1) / 2:.1f}s'] = Image.open(os.path.join(d, g)).convert('RGB')
    return out

MATERIALS = {   # what the figures and props are cut from, by colour
 'shirt': (226, 218, 200), 'hat': (205, 182, 140), 'skin': (96, 62, 44), 'khaki': (178, 154, 108), 'boot': (52, 36, 28), 'beard': (238, 236, 230),
 'silver': (178, 182, 190), 'gold': (206, 168, 80), 'redglass': (186, 40, 40), 'blueglass': (50, 80, 170), 'sand': (196, 120, 64), 'night': (30, 20, 22),
}
def hunt(F, rng, size=72):
    log, mats = {}, {}
    names = list(F)
    for m, target in MATERIALS.items():
        best = None
        for _ in range(2600):
            n = names[rng.integers(len(names))]; im = F[n]
            x, y = rng.integers(SAFE[0], SAFE[2] - size), rng.integers(SAFE[1], SAFE[3] - size)
            a = np.asarray(im.crop((x, y, x + size, y + size))).astype(np.float32)
            mu = a.reshape(-1, 3).mean(0); sd = a.reshape(-1, 3).std(0).mean()
            score = np.abs(mu - target).sum() + .6 * abs(sd - 9)
            if best is None or score < best[0]: best = (score, n, int(x), int(y), a)
        sc_, n, x, y, a = best
        # keep the grain, set the mean to the material: a cut paper that is still the footage
        mats[m] = np.clip(a - a.reshape(-1, 3).mean(0) + np.array(target), 0, 255).astype(np.uint8)
        log[m] = dict(source=n, box=[x, y, x + size, y + size], colour_error=round(float(sc_), 1))
    return mats, log

PLATES = {   # the backdrop strips, torn from these frames
 'sky': ('sky-dawn.jpg', (40, 60, 1240, 330)),
 'glasswall': ('stained-glass-arena.jpg', (60, 70, 1080, 330)),
 'floor': ('stained-glass-arena.jpg', (40, 440, 900, 600)),
 'window': ('swarm-hall.jpg', (560, 180, 720, 470)),
 'canyon': ('touki-side.jpg', (40, 120, 640, 420)),
}
INSERTS = {   # the returning images
 'horns': ('touki-front.jpg', (230, 190, 1050, 430)),
 'sea': ('sky-idrisi-sea.jpg', (40, 60, 1240, 600)),
 'kanaga': ('swarm-kanaga.jpg', (40, 60, 1240, 600)),
 'shards': ('swarm-knight-shatter.jpg', (120, 60, 1240, 560)),
 'mural': ('paint.mp4@4.0s', (300, 60, 1000, 300)),
}
def cut(F, table):
    out, log = {}, {}
    for k, (n, box) in table.items(): out[k] = F[n].crop(box); log[k] = dict(source=n, box=list(box))
    return out, log
