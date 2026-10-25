"""Extract the four stills from film.mp4 (scene time + 3 s title) and proof images (sprite sheet of the exposed drawings)."""
import os, subprocess, json
HERE = os.path.dirname(os.path.abspath(__file__)); F = os.path.dirname(HERE)
os.makedirs(os.path.join(F, 'stills'), exist_ok=True)
for t in (3.6, 9.0, 19.0, 28.0):
    # frame-exact: scene frame round(t*24) is film frame 72 + that
    n = 72 + round(t * 24)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(F, 'film.mp4'), '-vf', f'select=eq(n\\,{n})', '-vsync', '0',
                    '-frames:v', '1', '-q:v', '2', os.path.join(F, 'stills', f'still_{t:04.1f}s.jpg')], check=True)
print('stills written')
