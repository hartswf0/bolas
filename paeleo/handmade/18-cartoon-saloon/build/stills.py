"""Extract the four required stills (scene 3.6, 9, 19, 28 s) from film.mp4 as 1280x720 JPEGs."""
import subprocess, os
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(os.path.join(D, 'stills'), exist_ok=True)
for t in ['03.6', '09.0', '19.0', '28.0']:
    f = 72 + round(float(t) * 24)  # film frame of that scene time
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(D, 'film.mp4'), '-vf', f'select=eq(n\\,{f})', '-vframes', '1', '-q:v', '2',
                    os.path.join(D, 'stills', f'still_{t}s.jpg')], check=True)
print('stills ok')
