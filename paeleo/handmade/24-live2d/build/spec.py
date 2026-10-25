# python3 spec.py wav out.png t0 t1 : log-magnitude spectrogram for looking at the synthesized sound
import sys, wave, numpy as np
from PIL import Image
w = wave.open(sys.argv[1]); sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768
t0, t1 = float(sys.argv[3]), float(sys.argv[4]); x = x[int(t0 * sr):int(t1 * sr)]
n, hop = 1024, 128; cols = []
for i in range(0, len(x) - n, hop): cols.append(np.abs(np.fft.rfft(x[i:i + n] * np.hanning(n)))[:342])  # up to 8 kHz
S = 20 * np.log10(np.array(cols).T + 1e-9); S = np.clip((S - S.max() + 70) / 70, 0, 1)[::-1]
Image.fromarray((S * 255).astype(np.uint8)).resize((1200, 400)).save(sys.argv[2])
