"""Paint pieces onto a Pillow canvas: fill, then a thin ink edge (the cut edge of the paper)."""
import numpy as np
from PIL import ImageDraw
from kit import PAPER


def to_px(pieces, M):
    out = []
    for p in pieces:
        q = p.pts @ M[:2, :2].T + M[:2, 2]
        out.append((q, p))
    return out


def paint(img, pieces, M, edge=3, ink=None, draw=None):
    d = draw or ImageDraw.Draw(img)
    ink = ink or PAPER['ink']
    items = to_px(pieces, M)
    first = {}
    for n, (q, p) in enumerate(items):
        if p.grp and p.grp not in first: first[p.grp] = n
    for n, (q, p) in enumerate(items):
        xy = [tuple(v) for v in q.tolist()]
        if len(xy) < 3: continue
        if p.grp and first.get(p.grp) == n and edge:
            # one silhouette per merge group: all its ink edges first, then its fills, so inner seams vanish
            for q2, p2 in items:
                if p2.grp == p.grp:
                    xy2 = [tuple(v) for v in q2.tolist()]
                    d.line(xy2 + [xy2[0]], fill=ink, width=edge * 2, joint='curve')
        if p.grp:
            d.polygon(xy, fill=p.fill)
        elif p.outline and edge:
            d.polygon(xy, fill=p.fill, outline=ink, width=edge)
        else:
            d.polygon(xy, fill=p.fill)
    return d


def cm_to_px(scale, ox, oy):
    """figure cm (y up) -> canvas px (y down)"""
    return np.array([[scale, 0, ox], [0, -scale, oy], [0, 0, 1.0]])
