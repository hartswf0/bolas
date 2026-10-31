"""SCION-36 · the person: one whole archive frame of a woman at a door (Straight Talk, NTIS 1992, public domain),
seen from behind, cut from the white door by colour (the kit's SAM masks are of the door, not of her), auto-rigged
with the same BBW code: head point, chest and hip bones on the medial axis, and the arm on the open side."""
import os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from autorig import ROOT, triangulate, skeleton_graph, prune, largest_component, shortest_path, handle_vertices, bbw

DOORKIT = os.path.join(ROOT, 'paeleo/handmade/kit/archive-door/frames')
PF = 0


def person_mask(fi=PF):
    hsv = np.asarray(Image.open(os.path.join(DOORKIT, 'f%03d.jpg' % fi)).convert('HSV')).astype(float) / 255
    m = (hsv[..., 1] > .18) | (hsv[..., 2] < .42)
    m[:, :185] = False; m[:, 332:] = False; m[270:] = False
    m[:92, 283:] = False           # the door's edge beside her head
    m = ndi.binary_opening(m, iterations=1)
    m = ndi.binary_closing(m, iterations=3)       # the neck is thin under the bun: keep the head on
    lab, n = ndi.label(m); sz = ndi.sum(m, lab, range(1, n + 1)); m = lab == (1 + int(np.argmax(sz)))
    m = ndi.binary_closing(m, iterations=2)
    return ndi.binary_fill_holes(m)


def rig_person():
    m = person_mask()
    V, T = triangulate(ndi.binary_dilation(m), 3)
    adj, dist = skeleton_graph(m)
    ys, xs = np.nonzero(m); h = ys.max() - ys.min()
    adj = largest_component(prune(adj, dist, int(.08 * h)))
    pts = np.array(list(adj.keys()))
    top = tuple(pts[np.argmin(pts[:, 0])]); bot = tuple(pts[np.argmax(pts[:, 0])])
    spine = shortest_path(adj, top, bot)
    sp = [(float(q[1]), float(q[0])) for q in spine]; n = len(sp)
    # the arm on the open (right) side: the band of the silhouette's right edge between shoulder and hip
    y_sh = ys.min() + .30 * h; y_hand = ys.min() + .80 * h
    def edge(y):
        row = np.nonzero(m[int(y)])[0]; return float(row.max()) - 4.0
    arm = [(edge(y), float(y)) for y in np.linspace(y_sh, y_hand, 12)]
    H = {'head': {'type': 'point', 'at': sp[int(.06 * n)]},
         'chest': {'type': 'bone', 'a': sp[int(.55 * n)], 'b': sp[int(.25 * n)], 'path': sp[int(.25 * n):int(.55 * n)][::-1]},
         'hips': {'type': 'bone', 'a': sp[int(.62 * n)], 'b': sp[-1], 'path': sp[int(.62 * n):]},
         'arm': {'type': 'bone', 'a': arm[0], 'b': arm[-1], 'path': arm}}
    sets = handle_vertices(V, H, r=2.2)
    W, names, st = bbw(V, T, sets)
    img = np.asarray(Image.open(os.path.join(DOORKIT, 'f%03d.jpg' % PF)).convert('RGB')).astype(np.float32) / 255
    al = ndi.gaussian_filter(m.astype(np.float32), .8)
    return dict(fi=PF, mask=m, V=V, T=T, H=H, sets=sets, W=W, names=names, stats=st, facing=1,
                tex=np.dstack([img, al]).astype(np.float32), height=float(h), top=float(ys.min()), bottom=float(ys.max()),
                cx=float(xs.mean()))
