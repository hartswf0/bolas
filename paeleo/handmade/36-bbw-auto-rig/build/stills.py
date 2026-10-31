"""SCION-36 · the four stills, extracted from the encoded film (scene time + 3 s title)."""
import os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
os.makedirs(os.path.join(OUT, 'stills'), exist_ok=True)
for t in (3.6, 9.0, 19.0, 28.0):
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', '%.3f' % (3.0 + t + 1 / 48), '-i', os.path.join(OUT, 'film.mp4'),
                    '-frames:v', '1', '-q:v', '3', os.path.join(OUT, 'stills', 'still_%04.1fs.jpg' % t)], check=True)
print('stills ok')
