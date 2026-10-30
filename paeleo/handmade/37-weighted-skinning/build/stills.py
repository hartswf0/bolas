"""the four stills, extracted from the finished film.mp4 (scene time + 3 s title), 1280x720 JPEG"""
import os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
os.makedirs(os.path.join(ROOT, 'stills'), exist_ok=True)
for t in (3.6, 9.0, 19.0, 28.0):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', '%.3f' % (t + 3 + 1 / 48), '-i', os.path.join(ROOT, 'film.mp4'),
                    '-frames:v', '1', '-q:v', '2', os.path.join(ROOT, 'stills', 'still_%04.1fs.jpg' % t)], check=True)
print('stills ok')
