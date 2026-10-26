"""Proof image for the mix editor: level (dBFS, 50 ms RMS) of each stem over the scene clock, with the dog's measured
choice onsets as vertical lines -> proof/mix_levels.png. (The builder cannot listen; this is what was looked at.)"""
import json, os, wave
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); F = os.path.dirname(HERE)
tr = json.load(open(os.path.join(F, 'trace.json')))['meta']
cols = {'voice_call': (40, 90, 230), 'voice_soft': (230, 140, 30), 'room': (120, 120, 120), 'foley_person': (60, 160, 60), 'door': (160, 60, 160), 'dog': (200, 40, 40)}
W, H, T0 = 1600, 520, 3.0
im = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(im)
X = lambda t: 40 + t / 32 * (W - 60); Y = lambda db: 20 + (-db) / 70 * (H - 80)
for db in range(0, -71, -10):
    d.line([(40, Y(db)), (W - 20, Y(db))], fill=(225, 225, 225)); d.text((2, Y(db) - 6), f'{db}', fill=(0, 0, 0))
for t in range(33): d.text((X(t) - 4, H - 50), str(t), fill=(0, 0, 0))
for o in tr['onsets']:
    if o.get('measured_onset_t'): d.line([(X(o['measured_onset_t']), 20), (X(o['measured_onset_t']), H - 60)], fill=(0, 0, 0)); d.text((X(o['measured_onset_t']) + 2, 22), o['choice'].split('->')[-1].strip()[:12], fill=(0, 0, 0))
y = H - 30
for k, c in cols.items():
    w = wave.open(os.path.join(HERE, 'cache', 'stems', k + '.wav')); sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(np.float64).reshape(-1, 2).mean(1) / 32768
    x = x[int(T0 * sr):int((T0 + 32) * sr)]; hop = int(0.05 * sr)
    lv = [20 * np.log10(np.sqrt((x[i:i + hop] ** 2).mean()) + 1e-9) for i in range(0, len(x) - hop, hop)]
    pts = [(X(i * 0.05), Y(max(-70, v))) for i, v in enumerate(lv)]
    d.line(pts, fill=c, width=2); d.text((40 + list(cols).index(k) * 200, y), k, fill=c)
d.text((40, 4), 'Stem levels on the scene clock (dBFS, 50 ms RMS); black lines = measured onsets of the dog\'s answers', fill=(0, 0, 0))
im.save(os.path.join(F, 'proof', 'mix_levels.png'))
