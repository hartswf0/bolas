#!/usr/bin/env python3
"""Cut the archive plates for the shorts out of the cineosis-lab shot library.
python3 shorts/tools/plates.py <path to a cineosis-lab checkout>
Reads shorts/plates.json, writes assets/shorts/plates/<name>.mp4 (no sound, a keyframe every 6 frames so a
page can seek to any frame) and a contact strip assets/shorts/plates/<name>.jpg."""
import json, os, subprocess, sys
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
lab = sys.argv[1]
spec = json.load(open(os.path.join(root, 'shorts/plates.json')))
out = os.path.join(root, 'assets/shorts/plates')
os.makedirs(out, exist_ok=True)
for p in spec['plates']:
    src = os.path.join(lab, 'lab/clips', p['clip'] + '.mp4')
    dst = os.path.join(out, p['name'] + '.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(p['in']), '-to', str(p['out']), '-i', src, '-an',
                    '-vf', (('crop=' + p['crop'] + ',') if p.get('crop') else '') + "scale='min(640,iw)':-2,fps=24", '-c:v', 'libx264', '-crf', '22', '-g', '6',
                    '-pix_fmt', 'yuv420p', '-movflags', '+faststart', dst], check=True)
    n = p['out'] - p['in']
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', dst, '-vf', f'fps=6/{n},scale=160:-2,tile=6x1',
                    '-frames:v', '1', os.path.join(out, p['name'] + '.jpg')], check=True)
    print(p['name'], os.path.getsize(dst) // 1024, 'KB')
