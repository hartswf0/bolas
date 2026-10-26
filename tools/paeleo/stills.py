"""Stills for the PAELEO pages, taken from the finished film. python3 tools/paeleo/stills.py FILM"""
import subprocess, sys, os
FILM = sys.argv[1]
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'paeleo/media/still')
SHOTS = [('lineage-imagetext', 3.0), ('lineage-environment', 8.2), ('lineage-worldtext', 12.6), ('threshold-title', 16.0),
         ('threshold-call', 21.6), ('threshold-refuse', 27.2), ('threshold-sit', 32.6), ('threshold-door', 35.2), ('threshold-hand', 40.6),
         ('threshold-approach', 48.0), ('threshold-comein', 56.9), ('threshold-settle', 58.8), ('threshold-sill', 61.2),
         ('threshold-scales', 70.2), ('threshold-lockup', 75.0), ('threshold-credits', 80.0)]
os.makedirs(OUT, exist_ok=True)
for name, t in SHOTS:
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(t), '-i', FILM, '-frames:v', '1', '-q:v', '4', f'{OUT}/{name}.jpg'], check=True)
print(len(SHOTS), 'stills')
