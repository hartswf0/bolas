"""The person, engraved: drawn here, in profile facing RIGHT (toward the porch). A woman in a long work smock with her
hair in a bun, after the woman in kit/archive-door (Straight Talk, NTIS, public domain), who is seen only from behind
there; nothing of that footage is used but the idea of the figure. No face is portrayed: a profile line only.

Drawings (mm, y up, feet on y = 0):
  Q_stand  standing body (head, torso, smock, shoes)        Q_sit  seated on a low stool
  Q_arm    the near arm, its own mesh (shoulder at the origin), hanging straight down
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DRAW
from engrave import Drawing, catmull, INK, PAPER
from draw_dog import save


def head_parts(d, c, lean=0.0):
    cx, cy = c
    prof = catmull([(cx - 85, cy - 60), (cx - 95, cy + 40), (cx - 50, cy + 110), (cx + 30, cy + 125), (cx + 85, cy + 85),
                    (cx + 100, cy + 30), (cx + 120, cy - 5), (cx + 102, cy - 20), (cx + 108, cy - 45), (cx + 95, cy - 70),
                    (cx + 70, cy - 100), (cx + 20, cy - 110), (cx - 40, cy - 95)], 10)
    d.add('head', d.poly_mask(prof), 3, ('dir', 0.35), tone=0.05, spacing=12)
    hair = catmull([(cx - 95, cy + 20), (cx - 60, cy + 115), (cx + 40, cy + 130), (cx + 80, cy + 90), (cx + 40, cy + 70),
                    (cx - 10, cy + 40), (cx - 30, cy - 30), (cx - 80, cy - 50)], 10)
    d.add('hair', d.poly_mask(hair), 4, ('dir', 0.9), tone=0.45, spacing=9)
    d.add('bun', d.ellipse_mask((cx - 115, cy + 45), 50, 45), 4, ('dir', 0.6), tone=0.4, spacing=9)


def Q_stand():
    d = Drawing(700, 1800, 330, 1760)
    d.add('shoe_back', d.poly_mask(catmull([(-150, 0), (-150, 60), (-60, 70), (20, 40), (20, 0)], 6)), 0, ('dir', 0.0), tone=0.5, spacing=10)
    d.add('neck', d.poly_mask(catmull([(-20, 1380), (-15, 1480), (60, 1490), (70, 1390)], 6)), 1, ('dir', 1.4), tone=0.15, spacing=12)
    torso = catmull([(-110, 1060), (-125, 1250), (-95, 1400), (10, 1440), (110, 1395), (150, 1260), (115, 1060)], 10)
    d.add('torso', d.poly_mask(torso), 2, ('dir', 1.5), tone=0.05, spacing=13)
    skirt = catmull([(-115, 1070), (-150, 700), (-205, 90), (5, 70), (240, 90), (170, 700), (120, 1070)], 10)
    d.add('smock', d.poly_mask(skirt), 2, ('dir', 1.62), tone=0.0, spacing=14)
    d.add('shoe_front', d.poly_mask(catmull([(20, 0), (20, 60), (120, 75), (230, 40), (240, 0)], 6)), 2, ('dir', 0.0), tone=0.45, spacing=10)
    head_parts(d, (40, 1590))
    d.points = {k: np.array(v, float) for k, v in dict(shoulder=(15, 1360), hip=(0, 1050), head=(40, 1590),
                                                        foot_f=(130, 30), foot_b=(-60, 30), chest=(20, 1250)).items()}
    rgba, label, layers = d.render(light=(0.6, 0.5, 0.62))
    save('Q_stand', d, rgba, label, layers)


def Q_sit():
    d = Drawing(900, 1500, 330, 1460)
    # stool is part of the world; the body only. hips at (-30, 470), knees at (330, 520), feet near x = 360
    d.add('shoe_back', d.poly_mask(catmull([(250, 0), (250, 55), (330, 65), (400, 35), (400, 0)], 6)), 0, ('dir', 0.0), tone=0.5, spacing=10)
    d.add('neck', d.poly_mask(catmull([(-10, 1000), (0, 1090), (75, 1100), (80, 1000)], 6)), 1, ('dir', 1.4), tone=0.15, spacing=12)
    torso = catmull([(-110, 470), (-140, 700), (-110, 900), (-60, 1030), (30, 1060), (120, 1010), (150, 860), (120, 650),
                     (90, 520)], 10)
    d.add('torso', d.poly_mask(torso), 2, ('dir', 1.45), tone=0.05, spacing=13)
    lap = catmull([(-120, 420), (-110, 590), (100, 600), (340, 590), (400, 520), (420, 330), (430, 80), (290, 80),
                   (300, 330), (280, 430), (60, 420)], 10)
    d.add('smock', d.poly_mask(lap), 2, ('dir', 0.05), tone=0.0, spacing=14)
    d.add('shoe_front', d.poly_mask(catmull([(320, 0), (320, 60), (420, 75), (520, 40), (530, 0)], 6)), 3, ('dir', 0.0), tone=0.45, spacing=10)
    head_parts(d, (55, 1200))
    d.points = {k: np.array(v, float) for k, v in dict(shoulder=(30, 970), hip=(-20, 480), head=(55, 1200),
                                                        knee=(380, 540), foot=(420, 30)).items()}
    rgba, label, layers = d.render(light=(0.6, 0.5, 0.62))
    save('Q_sit', d, rgba, label, layers)


def Q_arm():
    d = Drawing(260, 700, 120, 80)    # shoulder at (0, 0), arm hangs down to y = -600
    ch = [(0, 0), (8, -260), (22, -500)]
    d.add('arm', d.capsules_mask(ch, [52, 42, 34]), 0, ('axis', ch, [52, 42, 34]), tone=0.1, spacing=12)
    hand = catmull([(0, -480), (-10, -560), (10, -620), (45, -615), (60, -560), (48, -485)], 8)
    d.add('hand', d.poly_mask(hand), 1, ('dir', 1.5), tone=-0.05, spacing=9)
    d.add('cuff', d.capsules_mask([(22, -470), (24, -488)], [38, 38]), 2, ('dir', 0.0), tone=0.4, spacing=8)
    d.points = {k: np.array(v, float) for k, v in dict(shoulder=(0, -20), elbow=(8, -260), wrist=(22, -500), hand=(28, -575)).items()}
    rgba, label, layers = d.render(light=(0.6, 0.5, 0.62))
    save('Q_arm', d, rgba, label, layers)


if __name__ == '__main__':
    Q_stand(); Q_sit(); Q_arm()
