"""Measured registration check: re-detect the rim in the rendered film at the middle
of each registered shot and report centre and radius error against the target."""
import json, subprocess, sys, cv2, numpy as np
sys.path.insert(0, '/home/user/bolas/tools/allways-forage')
led = json.load(open('059-ball.ledger.json')); edl = json.load(open('edl.json'))
R = edl['registration']['target_radius_px']; out = []
for ev in led['events']:
    L = (ev['layers'] or [{}])[0]
    if L.get('transform', {}).get('fit') != 'register': continue
    t = (ev['t_in'] + ev['t_out']) / 2
    o = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t), '-i', '059-ball.mp4', '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True).stdout
    g = cv2.medianBlur(cv2.cvtColor(cv2.imdecode(np.frombuffer(o, np.uint8), 1), cv2.COLOR_BGR2GRAY), 5)
    cs = cv2.HoughCircles(g, cv2.HOUGH_GRADIENT, dp=1.2, minDist=5, param1=110, param2=25, minRadius=int(R * .6), maxRadius=int(R * 1.5))
    if cs is None: out.append({'n': ev['n'], 'label': ev['label'][:40], 'detected': None}); continue
    c = min(cs[0][:15], key=lambda c: np.hypot(c[0] - 320, c[1] - 240) + abs(c[2] - R))
    out.append({'n': ev['n'], 't': round(t, 2), 'label': ev['label'].split(' · ')[0], 'centre_err_px': round(float(np.hypot(c[0] - 320, c[1] - 240)), 1), 'radius_err_px': round(float(c[2] - R), 1)})
json.dump(out, open('registration-check.json', 'w'), indent=1)
for x in out: print(x)
