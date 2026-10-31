"""Stills from the encoded film (scene time + 3 s title)."""
import os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.dirname(HERE)
os.makedirs(os.path.join(F, 'stills'), exist_ok=True)
for t in (3.6, 9.0, 19.0, 28.0):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', '%.3f' % (t + 3.0 + 0.5 / 24), '-i', os.path.join(F, 'film.mp4'),
                    '-frames:v', '1', '-q:v', '2', os.path.join(F, 'stills', 'still_%04.1fs.jpg' % t)], check=True)
print(sorted(os.listdir(os.path.join(F, 'stills'))))
