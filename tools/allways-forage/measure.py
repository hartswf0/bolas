"""Measure the registration circle for one image or clip frame.
  python3 measure.py <id-prefix> <still|clip> [t] [hint_cx hint_cy] [--out check.jpg]
Prints anchor (cx, cy normalised to source w/h) and r (normalised to source height),
choosing the Hough circle with the best rim support (nearest to the hint if given)."""
import cv2, json, sys, subprocess, numpy as np, os
HERE = os.path.dirname(os.path.abspath(__file__))
IDX = json.load(open(os.path.join(HERE, 'index.json')))
def load(pref, kind, t=0.0):
    e = next(x for x in IDX if x['id'].startswith(pref))
    if kind == 'still': return e, cv2.imread(e['media']['still'])
    o = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t), '-i', e['media'][kind], '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True).stdout
    return e, cv2.imdecode(np.frombuffer(o, np.uint8), 1)
def cands(img, p2=30):
    g = cv2.medianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 5); H, W = g.shape
    cs = cv2.HoughCircles(g, cv2.HOUGH_GRADIENT, dp=1.2, minDist=10, param1=110, param2=p2, minRadius=int(H*.08), maxRadius=int(H*.6))
    ed = cv2.dilate(cv2.Canny(g, 60, 140), None); out = []
    for cx, cy, r in (cs[0][:25] if cs is not None else []):
        a = np.linspace(0, 2*np.pi, 120, endpoint=False); xs = (cx + r*np.cos(a)).astype(int); ys = (cy + r*np.sin(a)).astype(int)
        ok = (xs >= 0) & (xs < W) & (ys >= 0) & (ys < H)
        out.append((float((ed[ys[ok], xs[ok]] > 0).sum())/120, float(cx)/W, float(cy)/H, float(r)/H))
    return out
if __name__ == '__main__':
    a = sys.argv[1:]; outp = None
    if '--out' in a: i = a.index('--out'); outp = a[i+1]; del a[i:i+2]
    pref, kind = a[0], a[1]; t = float(a[2]) if len(a) > 2 else 0
    hint = (float(a[3]), float(a[4])) if len(a) > 4 else None
    e, img = load(pref, kind, t); H, W = img.shape[:2]
    cs = cands(img)
    if hint: cs.sort(key=lambda c: -(c[0] - 2*np.hypot(c[1]-hint[0], c[2]-hint[1])))
    else: cs.sort(key=lambda c: -c[0])
    for c in cs[:3]: print(json.dumps({'sup': round(c[0],2), 'anchor': [round(c[1],4), round(c[2],4)], 'r': round(c[3],4)}))
    print(e['id'], W, H)
    if outp and cs:
        s, cx, cy, r = cs[0]; cv2.circle(img, (int(cx*W), int(cy*H)), int(r*H), (0, 0, 255), 2); cv2.imwrite(outp, img)
