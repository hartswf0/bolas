"""SCION 15 - the 2.5D layered mesh template and its renderer.

Typed core of the learned layered puppet:
  template space  : pixel coordinates of archive frame f006 (384x288), dog facing screen-left.
  part            : one layer = RGBA texture in template space + a pivot (joint to its parent) + a bone.
  pose (dict)     : g = (tx, ty, s, rot, mirror) image placement of the torso centre;
                    per part: rot (radians, relative to parent), fx, fy (foreshortening / length scales).
  view phi        : 0 = profile facing left (template), 90 = facing the camera, 180 = profile facing right.
  render          : back-to-front inverse warp of each layer (bilinear), soft alpha union.
Nothing here is learned; learn.py fits poses and view-conditioned shape/appearance on top of it.
"""
import json, os
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.normpath(os.path.join(HERE, '../../kit/archive-dog'))
CACHE = os.path.join(HERE, 'cache')
TEMPLATE_FRAME = 6

# hand-authored skeleton on f006 (template constructor role). Coordinates in f006 pixels.
SKEL = {
    'torso':   {'parent': None,    'pivot': (165, 135), 'bone': [(126, 128), (204, 132)], 'r': 17},
    'head':    {'parent': 'torso', 'pivot': (121, 116), 'bone': [(121, 116), (92, 85)], 'r': 12},
    'tail':    {'parent': 'torso', 'pivot': (211, 124), 'bone': [(211, 124), (258, 148)], 'r': 4},
    'ff_up':   {'parent': 'torso', 'pivot': (125, 150), 'bone': [(125, 150), (124, 172)], 'r': 4},
    'ff_lo':   {'parent': 'ff_up', 'pivot': (124, 172), 'bone': [(124, 172), (122, 191)], 'r': 3},
    'fn_up':   {'parent': 'torso', 'pivot': (139, 150), 'bone': [(139, 150), (139, 176)], 'r': 5},
    'fn_lo':   {'parent': 'fn_up', 'pivot': (139, 176), 'bone': [(139, 176), (135, 199)], 'r': 4},
    'hf_up':   {'parent': 'torso', 'pivot': (190, 150), 'bone': [(190, 150), (190, 174)], 'r': 5},
    'hf_lo':   {'parent': 'hf_up', 'pivot': (190, 174), 'bone': [(190, 174), (188, 194)], 'r': 3},
    'hn_up':   {'parent': 'torso', 'pivot': (208, 150), 'bone': [(208, 150), (209, 177)], 'r': 5},
    'hn_lo':   {'parent': 'hn_up', 'pivot': (209, 177), 'bone': [(209, 177), (212, 200)], 'r': 4},
}
# layer order, back to front (visibility layers). far legs behind the torso, near legs and head in front.
ORDER = ['tail', 'ff_up', 'ff_lo', 'hf_up', 'hf_lo', 'torso', 'hn_up', 'hn_lo', 'fn_up', 'fn_lo', 'head']
PARTS = list(SKEL)
LEGS = ['ff', 'fn', 'hf', 'hn']
# named template points (part, xy) used for keypoint losses and for feet/IK
POINTS = {
    'nose': ('head', (92, 86)), 'neck': ('head', (110, 108)), 'chest': ('torso', (126, 136)),
    'tail': ('torso', (212, 126)), 'f1': ('ff_lo', (122, 191)), 'f2': ('fn_lo', (135, 199)),
    'h1': ('hf_lo', (188, 194)), 'h2': ('hn_lo', (212, 200)),
    'tailtip': ('tail', (258, 148)), 'withers': ('torso', (132, 112)), 'rump': ('torso', (205, 118)),
    'belly': ('torso', (165, 152)), 'ear': ('head', (114, 92)), 'eye': ('head', (100, 92)),
}
POSE_KEYS = ['rot', 'fx', 'fy']


def rot(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s], [s, c]])


def affine(A, t):
    M = np.eye(3); M[:2, :2] = A; M[:2, 2] = t
    return M


def T(v):
    return affine(np.eye(2), v)


def neutral_pose():
    p = {'g': {'tx': 165.0, 'ty': 135.0, 's': 1.0, 'rot': 0.0, 'mirror': 1}}
    for k in PARTS:
        p[k] = {'rot': 0.0, 'fx': 1.0, 'fy': 1.0}
    return p


def transforms(pose):
    """template -> image 3x3 matrices for every part. FK in an un-mirrored dog frame, then a global placement."""
    g = pose['g']
    G = T((g['tx'], g['ty'])) @ affine(np.diag([g['mirror'] * g['s'], g['s']]) @ rot(g['rot']), (0, 0))
    D = {}
    ang = {}
    for k in PARTS:  # parents precede children in SKEL order
        sk = SKEL[k]; q = pose[k]
        piv = np.array(sk['pivot'], float)
        S = np.diag([q['fx'], q['fy']])
        if sk['parent'] is None:
            D[k] = affine(rot(q['rot']) @ S, (0, 0)) @ T(-piv)
            ang[k] = q['rot']
        else:
            P = D[sk['parent']]
            J = (P @ np.r_[piv, 1])[:2] + np.array([q.get('dx', 0.0), q.get('dy', 0.0)])
            a = ang[sk['parent']] + q['rot']
            ang[k] = a
            D[k] = T(J) @ affine(rot(a) @ S, (0, 0)) @ T(-piv)
    return {k: G @ D[k] for k in PARTS}


def point(pose, name, M=None):
    part, xy = POINTS[name]
    M = M or transforms(pose)
    return (M[part] @ np.r_[xy, 1])[:2]


class Template:
    """layers cut from f006 by bone-Voronoi assignment of the SAM mask, inpainted under occluders."""

    def __init__(self, path=None):
        path = path or os.path.join(CACHE, 'template.npz')
        z = np.load(path)
        self.H, self.W = z['alpha'].shape[1:]
        self.alpha = z['alpha'].astype(np.float32)        # [K,H,W] part alpha (soft)
        self.rgb = z['rgb'].astype(np.float32)            # [K,H,W] gray texture (0..1) in template space
        self.bbox = z['bbox']                             # [K,4] x0,y0,x1,y1 of each part (template)

    def tex(self, k):
        return self.rgb[PARTS.index(k)], self.alpha[PARTS.index(k)]


def warp_layer(tex, alpha, M, H, W, off=(0, 0), bbox=None, scale_out=1.0, alpha_only=False):
    """inverse-warp one layer into an HxW canvas whose pixel (x,y) is image point ((x+off0)/scale_out ...).
    M maps template -> image (image units); returns (gray, alpha) canvases, cropped to the layer's bbox for speed."""
    Mi = np.linalg.inv(M)
    th, tw = alpha.shape
    if bbox is None:
        bbox = (0, 0, tw, th)
    x0, y0, x1, y1 = bbox
    cs = np.array([[x0, y0, 1], [x1, y0, 1], [x0, y1, 1], [x1, y1, 1]], float).T
    ic = (M @ cs)[:2] * scale_out - np.array(off, float)[:, None]
    ux0 = int(max(0, np.floor(ic[0].min()) - 2)); ux1 = int(min(W, np.ceil(ic[0].max()) + 2))
    uy0 = int(max(0, np.floor(ic[1].min()) - 2)); uy1 = int(min(H, np.ceil(ic[1].max()) + 2))
    g = np.zeros((H, W), np.float32); a = np.zeros((H, W), np.float32)
    if ux1 <= ux0 or uy1 <= uy0:
        return g, a, None
    yy, xx = np.mgrid[uy0:uy1, ux0:ux1].astype(np.float64)
    X = (xx + off[0]) / scale_out; Y = (yy + off[1]) / scale_out
    tx = Mi[0, 0] * X + Mi[0, 1] * Y + Mi[0, 2]
    ty = Mi[1, 0] * X + Mi[1, 1] * Y + Mi[1, 2]
    coords = np.array([ty, tx])
    a[uy0:uy1, ux0:ux1] = ndimage.map_coordinates(alpha, coords, order=1, mode='constant', cval=0)
    if not alpha_only:
        g[uy0:uy1, ux0:ux1] = ndimage.map_coordinates(tex, coords, order=1, mode='nearest')
    return g, a, (ux0, uy0, ux1, uy1)


def render(tpl, pose, H, W, scale_out=1.0, off=(0, 0), order=None, textures=None, want_layers=False, alpha_only=False):
    """composite all layers back to front. textures: optional {part: (gray, alpha)} overriding the template."""
    M = transforms(pose)
    order = order or ORDER
    out = np.zeros((H, W), np.float32); A = np.zeros((H, W), np.float32)
    layers = {}
    for k in order:
        tex, al = textures[k] if textures and k in textures else tpl.tex(k)
        g, a, bb = warp_layer(tex, al, M[k], H, W, off, tpl.bbox[PARTS.index(k)], scale_out, alpha_only)
        if bb is None:
            continue
        out = out * (1 - a) + g * a
        A = A + a * (1 - A)
        if want_layers:
            layers[k] = (g, a)
    if want_layers:
        return out, A, layers
    return out, A


def load_kit():
    masks = json.load(open(os.path.join(KIT, 'masks.json')))
    keys = json.load(open(os.path.join(KIT, 'pose_agent_v8.json')))
    return masks, keys
