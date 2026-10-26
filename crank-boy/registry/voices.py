#!/usr/bin/env python3
"""Record the opening film's voices with Kokoro (kokoro-onnx).
Needs: pip install kokoro-onnx soundfile; ffmpeg; and the model files kokoro-v1.0.onnx and voices-v1.0.bin
from https://github.com/thewh1teagle/kokoro-onnx/releases (pass their folder as the first argument).
Writes assets/film/vo/<id>.mp3, assets/film/vo/timing.json and assets/film/lines.js (captions and lengths the film reads)."""
import json, os, subprocess, sys, tempfile
import soundfile as sf
from kokoro_onnx import Kokoro
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
models = sys.argv[1] if len(sys.argv) > 1 else '.'
k = Kokoro(os.path.join(models, 'kokoro-v1.0.onnx'), os.path.join(models, 'voices-v1.0.bin'))
lines = json.load(open(os.path.join(root, 'assets/film/script.json'), encoding='utf-8'))
timing = {}
for ln in lines:
    speed = 1.08 if ln['voice'] == 'am_puck' else 1.0
    samples, sr = k.create(ln['say'], voice=ln['voice'], speed=speed, lang=ln.get('lang', 'en-us'))
    with tempfile.NamedTemporaryFile(suffix='.wav') as t:
        sf.write(t.name, samples, sr)
        out = os.path.join(root, 'assets/film/vo', ln['id'] + '.mp3')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', t.name, '-ac', '1', '-b:a', '64k', out], check=True)
    timing[ln['id']] = round(len(samples) / sr, 2)
    print(ln['id'], timing[ln['id']], 's')
json.dump(timing, open(os.path.join(root, 'assets/film/vo/timing.json'), 'w'), indent=1)
lines_out = {ln['id']: {'who': ln['who'], 'cap': ln['cap'], 'dur': timing[ln['id']]} for ln in lines}
open(os.path.join(root, 'assets/film/lines.js'), 'w', encoding='utf-8').write('window.CRANK_LINES = ' + json.dumps(lines_out, ensure_ascii=False, indent=1) + ';\n')
