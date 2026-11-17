"""Side-by-side: chosen keyframe kf-2 beside three frames of the test shot, labelled."""
import cv2, numpy as np
WS = "/home/user/bolas/paeleo/scion/oulipo/films/swarm/cercle-vicieux/"
W = "/home/user/bolas/paeleo/scion/oulipo/films/sources/cercle-vicieux/test-shot/work/"
def lab(im, text):
    im = cv2.resize(im, (960, 540), interpolation=cv2.INTER_AREA)
    bar = np.full((46, 960, 3), 255, np.uint8)
    cv2.putText(bar, text, (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2, cv2.LINE_AA)
    return np.vstack([bar, im])
a = lab(cv2.imread(WS + "proposals/kf-2.png"), "CHOSEN KEYFRAME kf-2 (page 3)")
b = lab(cv2.imread(W + "c_2.0.png"), "TEST SHOT 2.0 s: purposeful p2->p3 leaf turn")
c = lab(cv2.imread(W + "c_4.25.png"), "TEST SHOT 4.25 s: X, the hand behind the glass pulls")
d = lab(cv2.imread(W + "c_9.6.png"), "TEST SHOT 9.6 s: H again (identical panel)")
g = np.vstack([np.hstack([a, b]), np.hstack([c, d])])
cv2.imwrite(WS + "test-shot-compare.jpg", g, [cv2.IMWRITE_JPEG_QUALITY, 88])
