"""SCION 21 . Photo-to-Actor Factory . the hand annotations (the operator's typed inputs).

Every coordinate here is in SOURCE PIXELS of the named archive frame (384x288, Amateur Film New Jersey C, public domain),
read by eye off 4x/5x gridded enlargements (proof/annotation_grids.jpg). These are the manual inputs the factory needs:
which frame serves which view, the body-template joints on the profile frame, and the head cut polygons.
The landmarks that the automatic fitter gets wrong are corrected in CORRECTIONS (see fit.py), not here.
"""

KIT_DOG = 'paeleo/handmade/kit/archive-dog'
KIT_DOOR = 'paeleo/handmade/kit/archive-door'

# ---------------------------------------------------------------- body template (profile, facing screen-left), frame 9
BODY_FRAME = 9
GROUND_Y = 201          # paws rest here in f009
JOINTS = {              # the template skeleton on f009
    'S': (124, 132),    # shoulder (fore-leg root)
    'H': (195, 138),    # hip (hind-leg root)
    'N': (113, 112),    # neck base
    'P': (102, 94),     # head pivot (occiput) in the template
    'T': (208, 126),    # tail root
}
TORSO_POLY = [(100, 108), (112, 96), (130, 100), (150, 110), (168, 118), (198, 119), (209, 122), (215, 140), (214, 156),
              (204, 160), (186, 158), (165, 155), (146, 154), (128, 156), (112, 152), (102, 132)]
NECK = {'a': (114, 118), 'b': (102, 95), 'w': 24}           # strip from neck base to head pivot
# legs: root, middle joint, paw ; widths (upper, lower); bend: +1 joint bends backward (fore), -1 forward (hind stifle)
LEGS = {
    'fore_far':  {'pts': [(136, 140), (140, 174), (137, 200)], 'w': (15, 10), 'bend': 1, 'z': 'far'},
    'hind_far':  {'pts': [(201, 140), (206, 180), (207, 200)], 'w': (18, 10), 'bend': -1, 'z': 'far'},
    'fore_near': {'pts': [(119, 140), (113, 168), (99, 190)], 'w': (16, 11), 'bend': 1, 'z': 'near'},
    'hind_near': {'pts': [(189, 140), (187, 178), (190, 198)], 'w': (20, 11), 'bend': -1, 'z': 'near'},
}

# ---------------------------------------------------------------- tail, frame 12 (the only frame where it stands clear)
TAIL = {'frame': 12, 'a': (206, 156), 'b': (246, 165), 'w': 9}

# ---------------------------------------------------------------- angle artwork: heads from five different frames
# poly = the cut; pivot = where it joins the neck. 'faces' = which way the muzzle points in the source.
HEADS = {
    'profile': {'frame': 9, 'faces': 'left', 'pivot': (104, 98),
                'poly': [(70, 76), (95, 74), (110, 80), (120, 92), (120, 106), (108, 112), (97, 108), (86, 95), (74, 90)]},
    'low':     {'frame': 46, 'faces': 'right', 'pivot': (238, 136),
                'poly': [(228, 124), (254, 124), (270, 143), (281, 168), (281, 189), (266, 192), (249, 176), (235, 156), (227, 140)]},
    'tq':      {'frame': 37, 'faces': 'right', 'pivot': (211, 146),
                'poly': [(193, 102), (233, 98), (236, 120), (232, 146), (214, 151), (197, 141), (191, 120)]},
    'front':   {'frame': 38, 'faces': 'viewer', 'pivot': (219, 154),
                'poly': [(196, 106), (241, 102), (245, 128), (239, 153), (222, 158), (204, 151), (197, 130)]},
    'back':    {'frame': 0, 'faces': 'away', 'pivot': (138, 104), 'key': 'dark', 'key_level': 150,
                'poly': [(115, 58), (151, 55), (161, 74), (159, 98), (141, 107), (120, 101), (114, 80)]},
}

# ---------------------------------------------------------------- whole-body angle artwork for the turns (sprite replacement)
BODY_VIEWS = {
    'front': {'frame': 38, 'faces': 'right'},    # three-quarter front, nearly frontal
    'tq':    {'frame': 37, 'faces': 'right'},    # three-quarter front
    'back':  {'frame': 0,  'faces': 'left'},     # rear three-quarter, head away
}

# ---------------------------------------------------------------- the person, the door, the lit room (Straight Talk, NTIS)
PERSON = {
    'torso': {'frame': 2, 'poly': [(250, 18), (268, 10), (290, 16), (298, 40), (292, 66), (318, 80), (328, 110), (332, 180),
                                     (330, 262), (300, 270), (260, 272), (222, 266), (206, 240), (192, 180), (196, 120),
                                     (208, 86), (240, 70), (248, 50)]},
    'arm':   {'frame': 9, 'poly': [(600 - 384, 82), (612 - 384, 90), (606 - 384, 150), (590 - 384, 178), (565 - 384, 186),
                                     (548 - 384, 180), (552 - 384, 168), (575 - 384, 160), (588 - 384, 120)]},
    'legs':  {'frame': 12, 'poly': [(203, 196), (262, 196), (262, 288), (240, 288), (232, 236), (226, 288), (203, 288)]},
}
DOOR_LEAF = {'frame': 30}           # the SAM mask of f030 is the door leaf
ROOM = {'frame': 21, 'box': (216, 76, 236, 200)}   # the lit hallway seen past the opened door
