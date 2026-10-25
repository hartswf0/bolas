"""The voice track, made first (as a cutout animator reads the track before shooting): flite speech synthesis
(via ffmpeg's libflite filter, run here), one take per line, then the track is read into a per-frame mouth chart
(cache/voice_chart.json) that the exposure sheet uses for the hinged jaw."""
import json, os, subprocess, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache')
SR = 48000
# (scene time s, text, register). Calls at 1.0 and 3.4; soft lines at 7.4, 10.4 and 26.4 (the score's timeline)
LINES = [(1.0, 'Come here.', 'call'), (3.4, 'Come here!', 'call'), (7.4, "It's all right.", 'soft'),
         (10.4, "It's all right.", 'soft'), (26.4, 'Come in.', 'soft')]


def synth(text, reg, fn):
    tempo = '1.0' if reg == 'call' else '0.86'
    filt = ('highpass=f=140,lowpass=f=5200' if reg == 'call' else 'highpass=f=120,lowpass=f=3000')
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi', '-i',
                    f"flite=text='{text}':voice=slt", '-af', f'aresample={SR},atempo={tempo},{filt}', '-ac', '1',
                    '-ar', str(SR), '-sample_fmt', 's16', fn], check=True)
    with wave.open(fn) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    a = a / (np.abs(a).max() + 1e-9)
    return a


def main():
    os.makedirs(CACHE, exist_ok=True)
    takes = []
    chart = np.zeros(768, np.float32)
    for k, (t, text, reg) in enumerate(LINES):
        fn = os.path.join(CACHE, f'voice_{k}.wav')
        a = synth(text.replace("'", ''), reg, fn) if "'" in text else synth(text, reg, fn)
        np.save(os.path.join(CACHE, f'voice_{k}.npy'), a)
        # read the track: RMS per film frame, gated, normalised per line
        hop = SR // 24
        n = len(a) // hop + 1
        rms = np.array([np.sqrt(np.mean(a[j * hop:(j + 1) * hop] ** 2) + 1e-12) for j in range(n)])
        env = np.clip((rms / rms.max() - .12) / .6, 0, 1)
        f0 = int(round(t * 24))
        for j, v in enumerate(env):
            if 0 <= f0 + j < 768:
                chart[f0 + j] = max(chart[f0 + j], v * (1.0 if reg == 'call' else .45))
        takes.append({'t': t, 'text': text, 'register': reg, 'file': os.path.relpath(fn, os.path.dirname(HERE)),
                      'dur_s': round(len(a) / SR, 3)})
    json.dump({'lines': takes, 'mouth': [round(float(v), 3) for v in chart]}, open(os.path.join(CACHE, 'voice_chart.json'), 'w'))
    print(json.dumps(takes, indent=0))


if __name__ == '__main__':
    main()
