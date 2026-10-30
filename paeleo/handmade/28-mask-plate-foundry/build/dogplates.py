"""Rotoscope/matte artist: the dog's performance plates. Every plate is an archive frame of the real dog
(Amateur Film New Jersey C) cut by a bezier mask (the SAM polygon re-drawn as a smooth path, eroded and feathered)
and split into parts by further bezier masks (add / subtract). Coordinates are the source frame's pixels."""
import os, json
import numpy as np
from comp import load, BezierMask, mask_stack, match_stats

HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(os.path.dirname(HERE), 'sources', 'dog')
SAM = json.load(open(os.path.join(SRC, 'masks.json')))
POSE = json.load(open(os.path.join(SRC, 'pose_agent_v8.json')))
SIZE = (384, 288)
TARGET = (0.30, 0.15)   # luma mean / std every dog plate is matched to before the light pass


def sam_mask(i, expand=-1.6, feather=1.1):   # choked 1.6 px: removes the bright source-ground fringe (halo)
    polys = sorted(SAM[str(i)], key=len, reverse=True)
    P = np.array(polys[0], float)
    if len(P) > 90: P = P[::max(1, len(P) // 90)]
    return BezierMask(P, feather=feather, expand=expand, name='sam%d' % i)


# ---- part masks on f010 (facing left, head up, four legs planted). pivots are where a part hinges on its parent.
F10 = dict(
    head=[(70, 72), (104, 72), (124, 90), (140, 108), (138, 124), (118, 130), (104, 122), (90, 108), (74, 98)],
    head_pivot=(124, 120),
    fore_far=[(97, 146), (119, 144), (120, 166), (104, 186), (94, 200), (74, 200), (76, 186), (95, 166)],
    fore_far_pivot=(110, 150), fore_far_foot=(84, 194),
    fore_near=[(120, 149), (147, 149), (148, 182), (147, 208), (124, 208), (123, 180)],
    fore_near_pivot=(134, 153), fore_near_foot=(136, 202),
    hind=[(176, 138), (216, 138), (216, 170), (206, 204), (180, 204), (178, 170)],
    hind_pivot=(196, 144), hind_foot=(192, 199),
    belly=[(56, 170), (100, 162), (122, 160), (150, 161), (178, 164), (226, 162), (226, 226), (56, 226)],
    # lying key of the same 8 vertices: the cut rises under the chest and rounds the haunch (the folded hind leg)
    belly_lying=[(56, 164), (100, 156), (122, 156), (150, 160), (178, 160), (226, 150), (226, 226), (56, 226)],
    ground=(150, 201), back=(165, 116), tail_end=(213, 150), nose=(80, 84), neck=(124, 120),
)
# ---- the approach head: f044 (head low, facing right); mirrored at use. pivot at the withers.
F44_HEAD = dict(mask=[(206, 112), (232, 120), (252, 140), (268, 165), (272, 186), (256, 192), (236, 180), (220, 160), (204, 142)],
                pivot=(214, 130), nose=(262, 182))
# ---- the looking-in head: f000 (the back of the dog's head, toward the camera, muzzle away)
F00_HEAD = dict(mask=[(104, 62), (142, 60), (158, 82), (162, 108), (158, 132), (150, 146), (128, 146), (118, 124), (104, 104)],
                pivot=(140, 130), nose=(120, 70))
# ---- the look-back head: f038 (face toward the camera), mirrored at use so the face turns toward the door
F38_HEAD = dict(mask=[(194, 106), (222, 108), (238, 116), (240, 140), (234, 160), (214, 165), (198, 154), (190, 128)],
                pivot=(208, 150))
# ---- the tail: f019 (the only frame with the tail held clear of the body); base hinges on the f010 rump
F19_TAIL = dict(mask=[(206, 139), (219, 141), (233, 151), (246, 162), (242, 169), (226, 167), (213, 161), (204, 152)],
                base=(209, 146), tip=(243, 165))
# ---- whole-body turn plates (yaw order, facing left -> camera -> facing right); their own pose keys give the neck track
# chosen by eye from a cut-out sheet of f013-f041 for ONE legible head each (f016: head hidden; f040: smeared double head)
TURN1 = [13, 30, 32, 36]          # facing the door -> head and body turned away
TURN2 = [38, 37, 13]              # coming back round: face toward the camera, then the door
TURN = sorted(set(TURN1 + TURN2))
TURN_FACING = {13: 1, 30: -1, 32: -1, 36: -1, 37: 0, 38: 0}


class Plate:
    def __init__(self, i):
        self.i = i
        self.rgb = load(os.path.join(SRC, 'f%03d.jpg' % i))
        self.sam = sam_mask(i)
        a = self.sam.raster(SIZE)
        self.rgb, self.match = match_stats(self.rgb, a, *TARGET)
        self.alpha = a

    def cut(self, masks, t=0.0):
        """alpha = SAM matte x add/sub bezier masks"""
        if not masks: return self.alpha
        return self.alpha * mask_stack(masks, SIZE, t)


def build():
    out = {}
    p10 = Plate(10)
    legs = ['fore_far', 'fore_near', 'hind']
    out['f10'] = p10
    out['head10'] = p10.cut([BezierMask(F10['head'], feather=2.2)])
    for k in legs:
        out[k] = p10.cut([BezierMask(F10[k], feather=1.6)])
    # body: everything but the head, and the legs below the belly line
    out['body_masks'] = [BezierMask([(0, 0), (384, 0), (384, 288), (0, 288)], feather=0),
                         BezierMask(F10['head'], feather=2.2, expand=-3, mode='sub'),
                         BezierMask({0.0: F10['belly'], 1.0: F10['belly_lying']}, feather=2.5, mode='sub', name='belly (keyed by lie)')]
    out['body10'] = p10.cut(out['body_masks'], 0.0)
    p44 = Plate(44); out['f44'] = p44
    out['head44'] = p44.cut([BezierMask(F44_HEAD['mask'], feather=2.2)])
    p38 = Plate(38); out['f38'] = p38
    out['head38'] = p38.cut([BezierMask(F38_HEAD['mask'], feather=2.0)])
    p19 = Plate(19); out['f19'] = p19
    out['tail19'] = p19.cut([BezierMask(F19_TAIL['mask'], feather=1.4)])
    p0 = Plate(0); out['f00'] = p0
    out['head00'] = p0.cut([BezierMask(F00_HEAD['mask'], feather=2.2)])
    out['turn'] = {}
    for i in TURN:
        p = Plate(i)
        out['turn'][i] = dict(plate=p, alpha=p.alpha)
    return out
