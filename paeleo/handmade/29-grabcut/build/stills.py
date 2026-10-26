"""stills/still_03.6s.jpg, 09.0, 19.0, 28.0 (1280x720 JPEG) from the scene frames."""
import os, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.dirname(HERE)
os.makedirs(os.path.join(F, 'stills'), exist_ok=True)
for t in (3.6, 9.0, 19.0, 28.0):
    i = int(round(t * 24))
    shutil.copy(os.path.join(HERE, 'cache/frames/s%04d.jpg' % i), os.path.join(F, 'stills', 'still_%04.1fs.jpg' % t))
print(sorted(os.listdir(os.path.join(F, 'stills'))))
