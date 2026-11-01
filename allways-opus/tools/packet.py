"""Everything an independent critic gets, and nothing of the builder's reasons: frames with timecodes, a transcript with timecodes, loudness per 2 s, and the operator's own criteria.
run with ~/.cache/mlxw-venv/bin/python (needs mlx_whisper; PIL comes from the system python via packet_sheet). usage: packet.py <film> <scion id> ..."""
import json, os, subprocess, sys, re
import mlx_whisper
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
film = sys.argv[1]; v = f"{ROOT}/films/{film}/{film}.mp4"; d = f"{ROOT}/films/{film}/critic"; os.makedirs(d, exist_ok=True)
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", v])); step = max(1.0, dur / 48)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", v, "-vf", f"fps=1/{step:.3f},scale=240:-1,drawtext=fontfile=/System/Library/Fonts/Menlo.ttc:text='%{{pts\\:hms}}':x=4:y=4:fontsize=13:fontcolor=white:box=1:boxcolor=black", "-q:v", "4", f"{d}/f%03d.jpg"], capture_output=True)
txt = []
r = mlx_whisper.transcribe(v, path_or_hf_repo="mlx-community/whisper-large-v3-turbo", word_timestamps=True, language="en", condition_on_previous_text=False)
for s in r["segments"]: txt.append(f"{s['start']:6.1f}-{s['end']:6.1f} {s['text'].strip()}")
loud = []
for t in range(0, int(dur), 2):
    o = subprocess.run(["ffmpeg", "-hide_banner", "-ss", str(t), "-t", "2", "-i", v, "-af", "volumedetect", "-vn", "-f", "null", "-"], capture_output=True, text=True).stderr; m = re.search(r"mean_volume: (-?[\d.]+)", o); loud.append(f"{t}s:{m.group(1) if m else 'x'}")
open(f"{d}/transcript.txt", "w").write(f"step between frames {step:.2f}s; total {dur:.2f}s\nspeech recognition (may mishear; hiss can produce false words):\n" + "\n".join(txt) + "\n\nmean loudness dB per 2s:\n" + " ".join(loud) + "\n"); print(film, dur, len(txt))
