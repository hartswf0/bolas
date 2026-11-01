"""Scan stills and clip frames for strong circles (Hough), score by edge support
along the rim. Writes circles.json: id, src kind, t, cx, cy, r, support."""
import cv2, json, numpy as np, os, subprocess, sys
from concurrent.futures import ProcessPoolExecutor
cv2.setNumThreads(1)
HERE = os.path.dirname(os.path.abspath(__file__))
IDX = json.load(open(os.path.join(HERE, 'index.json')))

def best(img):
    h0, w0 = img.shape[:2]
    img = cv2.resize(img, (round(w0 * 240 / h0), 240), interpolation=cv2.INTER_AREA)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY); g = cv2.medianBlur(g, 5)
    H, W = g.shape
    if (cv2.Canny(g, 55, 110) > 0).mean() > 0.12: return None   # too busy: Hough explodes, circles unreadable
    cs = cv2.HoughCircles(g, cv2.HOUGH_GRADIENT, dp=1.2, minDist=40, param1=110, param2=38, minRadius=int(H*.12), maxRadius=int(H*.48))
    if cs is None: return None
    ed = cv2.Canny(g, 60, 140); ed = cv2.dilate(ed, None)
    out = []
    for cx, cy, r in cs[0][:5]:
        a = np.linspace(0, 2*np.pi, 90, endpoint=False)
        xs = (cx + r*np.cos(a)).astype(int); ys = (cy + r*np.sin(a)).astype(int)
        ok = (xs >= 0) & (xs < W) & (ys >= 0) & (ys < H)
        sup = float((ed[ys[ok], xs[ok]] > 0).sum()) / 90
        out.append((sup, float(cx)/W, float(cy)/H, float(r)/H))
    return max(out)

def job(e):
    res = []
    m = e['media']
    if 'still' in m:
        im = cv2.imread(m['still'])
        if im is not None:
            b = best(im)
            if b: res.append({'id': e['id'], 'kind': 'still', 't': None, 'sup': b[0], 'cx': b[1], 'cy': b[2], 'r': b[3]})
    p = m.get('clip')
    if p:
        cap = cv2.VideoCapture(p); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); fps = cap.get(cv2.CAP_PROP_FPS) or 25
        for k in range(0, n, max(1, int(3 * fps))):
            cap.set(cv2.CAP_PROP_POS_FRAMES, k); ok, im = cap.read()
            if not ok: break
            b = best(im)
            if b: res.append({'id': e['id'], 'kind': 'clip', 't': k/fps, 'sup': b[0], 'cx': b[1], 'cy': b[2], 'r': b[3]})
    return res

if __name__ == '__main__':
    kind = sys.argv[1] if len(sys.argv) > 1 else 'all'
    todo = [e for e in IDX if kind == 'all' or (kind == 'still' and 'still' in e['media']) or (kind == 'clip' and 'clip' in e['media'])]
    if kind == 'still':
        for e in todo: e['media'] = {'still': e['media']['still']}
    if kind == 'clip':
        for e in todo: e['media'] = {'clip': e['media']['clip']}
    out = []
    for i, e in enumerate(todo):
        out += job(e)
        if i % 1000 == 0: print(i, len(out), flush=True)
    out.sort(key=lambda x: -x['sup'])
    json.dump(out, open(os.path.join(HERE, f'circles-{kind}.json'), 'w'))
    print(len(out), sum(1 for x in out if x['sup'] > .7))
