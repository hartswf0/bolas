"""Assemble film.mp4 (3 s title + 32 s scene + 3 s end card, 24 fps, H.264 + AAC, faststart, ≤ 12 MB) and the four stills."""
import os, shutil, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); FOLDER = os.path.dirname(HERE); C = os.path.join(HERE, 'cache')
F = os.path.join(C, 'frames'); SEQ = os.path.join(C, 'seq')
shutil.rmtree(SEQ, ignore_errors=True); os.makedirs(SEQ)
names = [f'title_{k:03d}.jpg' for k in range(72)] + [f'scene_{k:03d}.jpg' for k in range(768)] + [f'end_{k:03d}.jpg' for k in range(72)]
for n, name in enumerate(names):
    os.symlink(os.path.join(F, name), os.path.join(SEQ, f'{n:04d}.jpg'))
out = os.path.join(FOLDER, 'film.mp4')
for crf in (19, 21, 23, 25, 27):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '24', '-i', os.path.join(SEQ, '%04d.jpg'), '-i', os.path.join(C, 'sound.wav'),
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', str(crf), '-pix_fmt', 'yuv420p', '-r', '24',
                    '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', '-t', '38', out], check=True)
    size = os.path.getsize(out)
    if size <= 11.5e6: break
print('film.mp4', round(size / 1e6, 2), 'MB at crf', crf)
os.makedirs(os.path.join(FOLDER, 'stills'), exist_ok=True)
for t in (3.6, 9.0, 19.0, 28.0):
    shutil.copyfile(os.path.join(F, f'scene_{round(t * 24):03d}.jpg'), os.path.join(FOLDER, 'stills', f'still_{t:04.1f}s.jpg'))
