# extract the four stills (scene times 3.6, 9.0, 19.0, 28.0 s; the film has a 3 s title before the scene)
import os, subprocess
H = os.path.dirname(os.path.abspath(__file__)); out = os.path.join(H, '..', 'stills'); os.makedirs(out, exist_ok=True)
for t in ('03.6', '09.0', '19.0', '28.0'):
    n = 72 + round(float(t) * 24)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(H, '..', 'film.mp4'), '-vf', f'select=eq(n\\,{n})', '-vsync', '0', '-frames:v', '1', '-q:v', '2', os.path.join(out, f'still_{t}s.jpg')], check=True)
print('stills ok')
