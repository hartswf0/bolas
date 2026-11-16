"""Look at foraged recordings: RMS envelope, onsets, quietest windows; writes a waveform+spectrogram sheet."""
import sys, subprocess, numpy as np
from PIL import Image, ImageDraw
RATE = 44100
def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()
def env(x, hop=441):
    n = len(x) // hop
    return np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
def onsets(x, hop=441):
    e = 20 * np.log10(env(x, hop))
    d = np.diff(e, prepend=e[0])
    floor = np.percentile(e, 20)
    idx = [i for i in range(1, len(e) - 1) if d[i] > 8 and e[i] > floor + 15]
    out = []
    for i in idx:
        if not out or i - out[-1] > 8: out.append(i)
    return [round(i * hop / RATE, 2) for i in out], e
if __name__ == "__main__":
    rows = []
    for p in sys.argv[2:]:
        x = load(p); on, e = onsets(x)
        q = np.argsort(e)[:5]
        print(f"{p.split('/')[-1]}: dur {len(x)/RATE:.2f}s peak {20*np.log10(np.abs(x).max()+1e-9):.1f} dBFS floor p10 {np.percentile(e,10):.1f} dB p90 {np.percentile(e,90):.1f}; onsets {on[:30]}")
        W, H = 1200, 160
        im = Image.new("RGB", (W, H * 2), (20, 20, 20)); d = ImageDraw.Draw(im)
        ee = np.interp(np.linspace(0, len(e) - 1, W), np.arange(len(e)), e)
        for i, v in enumerate(ee):
            h = int(np.clip((v + 80) / 80, 0, 1) * H); d.line([(i, H - h), (i, H)], fill=(200, 200, 190))
        for t in on: X = int(t * RATE / 441 / len(e) * W); d.line([(X, 0), (X, 10)], fill=(255, 60, 60))
        # spectrogram
        nf = 1024; hop = max(256, (len(x) - nf) // W)
        frames = [np.abs(np.fft.rfft(x[i:i + nf] * np.hanning(nf)))[:256] for i in range(0, len(x) - nf, hop)][:W]
        S = 20 * np.log10(np.array(frames).T + 1e-6); S = np.clip((S - S.max() + 80) / 80, 0, 1)
        sp = Image.fromarray((S[::-1] * 255).astype(np.uint8)).resize((W, H)); im.paste(sp.convert("RGB"), (0, H))
        d.text((4, 2), p.split('/')[-1], fill=(255, 255, 0)); rows.append(im)
    sheet = Image.new("RGB", (1200, 320 * len(rows)))
    for i, r in enumerate(rows): sheet.paste(r, (0, 320 * i))
    sheet.save(sys.argv[1])
