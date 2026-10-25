"""Proof image for the alignment engineer: spectrogram of each line with the synthesizer's phone boundaries and the
viseme each phone exposes -> proof/alignment.png"""
import json, os, wave
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache', 'voice')
lines = json.load(open(os.path.join(HERE, 'voice_lines.json')))
VIS = {}
for ps, v in [('aa ah ay aw ae', 'AA'), ('ao ow oy uw uh w', 'OO'), ('iy ih ey eh y', 'EE'), ('r er', 'R'), ('m b p', 'MBP'),
              ('f v', 'FV'), ('l', 'L'), ('t d s z n th dh sh ch jh zh', 'TS'), ('k g hh ng', 'KG')]:
    for p in ps.split(): VIS[p] = v
HOP, WIN, PX = 80, 320, 2
rows = []
for L in lines:
    w = wave.open(os.path.join(CACHE, L['id'] + '.wav')); sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    n = 1 + (len(x) - WIN) // HOP
    fr = np.stack([x[i * HOP:i * HOP + WIN] * np.hanning(WIN) for i in range(n)])
    s = 10 * np.log10(np.abs(np.fft.rfft(fr, 512, axis=1)) ** 2 + 1e-10)[:, :200].T[::-1]
    s = np.clip((s - (s.max() - 70)) / 70, 0, 1)
    img = Image.fromarray((255 * (1 - s)).astype(np.uint8)).resize((n * PX, 200)).convert('RGB')
    im = Image.new('RGB', (img.width + 10, 270), 'white'); im.paste(img, (5, 20)); d = ImageDraw.Draw(im)
    for p in L['phones']:
        x0 = 5 + p['t0'] * sr / HOP * PX
        d.line([(x0, 20), (x0, 225)], fill=(0, 90, 255)); d.text((x0 + 2, 228), p['p'], fill=(0, 0, 0))
        d.text((x0 + 2, 244), VIS.get(p['p'], 'KG'), fill=(200, 0, 0))
    cx = 5 + L['cue_vowel_onset'] * sr / HOP * PX; d.line([(cx, 20), (cx, 225)], fill=(255, 0, 0), width=2)
    d.text((5, 3), f"{L['id']} '{L['text']}' - blue: Flite segment starts, red: cue vowel the dog answers, red text: viseme", fill=(0, 0, 0))
    rows.append(im)
out = Image.new('RGB', (max(r.width for r in rows), sum(r.height for r in rows)), 'white'); y = 0
for r in rows: out.paste(r, (0, y)); y += r.height
os.makedirs(os.path.join(HERE, '..', 'proof'), exist_ok=True)
out.save(os.path.join(HERE, '..', 'proof', 'alignment.png'))
