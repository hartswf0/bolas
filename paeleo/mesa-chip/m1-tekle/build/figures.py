"""SCION-TEKLE's two figures, as *light*: shapes the backlight takes when it passes the fixed glass. They are drawn into the light
field and the label field, never into the glass. Uncle Mesa: a Black man in his sixties, long white beard, round glasses with gold
lenses, cream wide-brimmed hat, white guayabera-style shirt, khaki trousers, dark boots, the six-shooter of paint. The knight: armour
of silver, gold and red glass plates, a red plume, a red glass sword."""
import math, numpy as np
X0, SX, FLOOR, S, SILL = 470.0, 60.0, 470.0, 1.45, 322.0
def sx(x): return X0 + SX * x
def ease(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def lerp(a, b, u): return a + (b - a) * u
def rot(p, c, a):
    s, k = math.sin(a), math.cos(a); x, y = p[0] - c[0], p[1] - c[1]; return (c[0] + k * x - s * y, c[1] + s * x + k * y)

def foot_y(x):  # the steps at the left: tread tops at 382 and 406, then the floor
    return FLOOR - 60 + 30 * ease((x + 7.0) / .25) + 30 * ease((x + 6.7) / .25)

class Ops:
    """draw ops collected in order: ('cap', a, b, r, rgb, lab), ('poly', pts, rgb, lab), ('ell', c, rx, ry, rgb, lab)"""
    def __init__(s): s.ops = []
    def cap(s, a, b, r, c, l): s.ops.append(('cap', a, b, r, c, l))
    def poly(s, p, c, l): s.ops.append(('poly', p, c, l))
    def ell(s, c, rx, ry, col, l): s.ops.append(('ell', c, rx, ry, col, l))
    def xform(s, f):
        o = []
        for op in s.ops:
            if op[0] == 'cap': o.append(('cap', f(op[1]), f(op[2]), op[3], op[4], op[5]))
            elif op[0] == 'poly': o.append(('poly', [f(p) for p in op[1]], op[2], op[3]))
            else: o.append(('ell', f(op[1]), op[2], op[3], op[4], op[5]))
        s.ops = o; return s

SKIN, BEARD, HAT, SHIRT, KHAKI, BOOT, GOLD, GUN = (92, 58, 40), (240, 238, 230), (236, 222, 186), (248, 246, 238), (190, 160, 110), (52, 36, 28), (236, 190, 70), (60, 200, 210)

def mesa(t, fr, facing=1, held=None):
    """Uncle Mesa at time t. Origin at the feet, then placed."""
    st = fr['mesa']['state']; x = fr['mesa']['x']; o = Ops(); f = facing
    walking = st in ('descend', 'walk'); ph = t * 2 * math.pi * 1.6
    sw = 9 * math.sin(ph) if walking else 0; bob = 2 * abs(math.sin(ph)) if walking else 0
    aim = 0.0
    if t >= 6.5: aim = ease((t - 6.5) / .18)
    if 12.2 <= t < 14.15: aim = 0.0
    if t >= 20.6: aim = 1 - ease((t - 20.6) / .4)
    sit = ease((t - 21.7) / .5) if t >= 21.7 else 0.0
    c = 0.0   # the knees give: before he falls, as he rises
    if 12.2 <= t < 14.15: c = ease((t - 12.2) / .12) * (1 - ease((t - 13.95) / .18))
    hip = (lerp(0, -14 * f, sit), lerp(-82 + bob + 22 * c, -26, sit))
    # legs: thigh, shin, boot
    for k, s in ((0, sw), (1, -sw)):
        if sit > 0:
            knee = (lerp(s * .5, 22 * f, sit), lerp(-42, -36, sit)); footp = (lerp(s, 36 * f, sit), 0)
        else: knee = (s * .55 + 2 * f + 16 * f * c, -42 + 8 * c); footp = (s, 0)
        o.cap(hip, knee, 8.5, KHAKI, 1); o.cap(knee, footp, 7.5, KHAKI, 1); o.poly([(footp[0] - 6, -7), (footp[0] + 13 * f, -7), (footp[0] + 14 * f, 1), (footp[0] - 7, 1)], BOOT, 1)
    sh = (hip[0] + 2 * f, hip[1] - 58)
    o.poly([(hip[0] - 14, hip[1] + 4), (hip[0] + 14, hip[1] + 4), (sh[0] + 16, sh[1]), (sh[0] - 16, sh[1])], SHIRT, 1)   # guayabera
    o.poly([(sh[0] + 4 * f, sh[1] + 16), (sh[0] + 12 * f, sh[1] + 16), (sh[0] + 12 * f, sh[1] + 23), (sh[0] + 4 * f, sh[1] + 23)], (240, 200, 40), 1)  # MESA CHIP badge
    # back arm
    o.cap((sh[0] - 4 * f, sh[1] + 4), (sh[0] - 8 * f - sw * .4, sh[1] + 52), 6, SHIRT, 1)
    head = (sh[0] + 3 * f, sh[1] - 15)
    o.cap((sh[0], sh[1]), head, 6, SKIN, 1)
    o.ell(head, 11, 12, SKIN, 1)
    o.poly([(head[0] - 7 * f, head[1] + 2), (head[0] + 11 * f, head[1] + 2), (head[0] + 9 * f, head[1] + 30), (head[0] + 1 * f, head[1] + 34), (head[0] - 5 * f, head[1] + 16)], BEARD, 1)  # long white beard
    o.ell((head[0] + 4 * f, head[1] - 3), 4.5, 3.5, (250, 250, 244), 1); o.ell((head[0] + 5.5 * f, head[1] - 3), 1.8, 2.2, (20, 14, 10), 1)  # a large eye, in the icon manner
    o.ell((head[0] + 7 * f, head[1] + 1), 4.5, 4.5, GOLD, 1); o.ell((head[0] - 3 * f, head[1] + 1), 4, 4, GOLD, 1)  # the two round gold lenses
    o.ell((head[0], head[1] - 10), 26, 5, HAT, 1); o.poly([(head[0] - 11, head[1] - 10), (head[0] + 11, head[1] - 10), (head[0] + 9, head[1] - 24), (head[0] - 9, head[1] - 24)], HAT, 1)
    # gun arm: at the hip (held low) or out at the shoulder
    a0 = (sh[0] + 4 * f, sh[1] + 4)
    lo = (sh[0] + 10 * f, sh[1] + 50); hi = (sh[0] + 44 * f, sh[1] + 4)
    hand = (lerp(lo[0], hi[0], aim), lerp(lo[1], hi[1], aim))
    o.cap(a0, hand, 6, SHIRT, 1); o.ell(hand, 5, 5, SKIN, 1)
    o.poly([(hand[0] - 4 * f, hand[1] - 7), (hand[0] + 22 * f, hand[1] - 7), (hand[0] + 22 * f, hand[1] + 1), (hand[0] + 6 * f, hand[1] + 1), (hand[0] + 4 * f, hand[1] + 10), (hand[0] - 4 * f, hand[1] + 10)], GUN, 5)
    # knocked down: the whole body turns about the feet, away from the knight
    down = 0.0
    if 12.2 <= t < 14.15: down = ease((t - 12.27) / .2) * (1 - ease((t - 13.7) / .26))
    if down > 0: o.xform(lambda p: rot(p, (0, -80), -f * down * math.pi / 2 * .97)).xform(lambda p: (p[0], p[1] + 64 * down))  # he lies where he fell, centred on his place
    yy = FLOOR if sit > 0 else foot_y(x)
    X = sx(x); return o.xform(lambda p: (X + S * p[0], yy + S * p[1]))

SILV, GOLDK, RED, DARK = (200, 206, 216), (220, 178, 80), (196, 40, 40), (40, 40, 60)
def knight_pose(t, fr):
    st = fr['knight']['state']; x = fr['knight']['x']
    X = sx(x); Y = FLOOR
    if t < 4.5: X, Y = sx(6.2), SILL
    elif t < 5.2:
        u = (t - 4.5) / .7; X = lerp(sx(6.2), sx(5.4), 1 - math.exp(-u * 6)); Y = lerp(SILL, FLOOR, ease(u * 1.4)) - 40 * math.sin(math.pi * min(1, u * 1.4))
    walking = st in ('advance', 'advance_broken'); ph = t * 2 * math.pi * (1.3 if st == 'advance' else .9)
    sw = 10 * math.sin(ph) if walking else 0
    turn = ease((t - 3.0) / .12) if t >= 3.0 else 0.0
    sword = 0.0 if t < 6.0 else ease((t - 6.0) / .2)
    raise_ = 0.0
    if 11.55 <= t < 12.2: raise_ = ease((t - 11.55) / .45)
    if 12.0 <= t < 12.3: raise_ = 1 - ease((t - 12.0) / .2) * 2 if t < 12.1 else -1.0
    if 12.3 <= t < 14: raise_ = -1.0 + ease((t - 12.3) / .6) * .8
    if t >= 14: raise_ = -.2 + .65 * ease((t - 14) / .4)   # after he rises, the sword is held high, off him
    return dict(X=X, Y=Y, sw=sw, turn=turn, sword=sword, raise_=raise_, limp=st == 'advance_broken')

def knight_plates(P):
    """The knight as plates: (id, polygon, colour, label). Faces left (-x)."""
    X, Y, sw = P['X'], P['Y'], P['sw']; out = []
    hip = (X, Y - 84); sh = (X - 3, Y - 140)
    def part(a, b, w, na, nc, cols, lab=2):
        ax, ay = a; bx, by = b; dx, dy = bx - ax, by - ay; L = math.hypot(dx, dy) or 1; nx, ny = -dy / L, dx / L
        for i in range(na):
            for j in range(nc):
                u0, u1 = i / na, (i + 1) / na; v0, v1 = j / nc - .5, (j + 1) / nc - .5
                q = [(ax + dx * u + nx * w * v, ay + dy * u + ny * w * v) for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]
                out.append([len(out), q, cols[(i + j) % len(cols)], lab])
    for s in (sw, -sw):
        knee = (X + s * .5 - 3, Y - 42); ft = (X + s, Y)
        if P['limp'] and s == sw: knee = (knee[0], knee[1] + 3)
        part(hip, knee, 17, 3, 2, [SILV, GOLDK]); part(knee, ft, 15, 3, 2, [SILV, (170, 176, 190)])
    part(hip, sh, 40, 4, 4, [SILV, GOLDK, SILV, RED])
    head = (sh[0] - 2 - 4 * P['turn'], sh[1] - 18)
    part((head[0], head[1] + 12), (head[0], head[1] - 14), 24, 2, 3, [SILV, GOLDK])
    vis = (head[0] - 2 - 17 * P['turn'], head[1] - 2)
    out.append([len(out), [(vis[0] - 10, vis[1] - 4), (vis[0] + 8, vis[1] - 4), (vis[0] + 8, vis[1] + 5), (vis[0] - 10, vis[1] + 5)], (20, 20, 40), 6])
    part((head[0] + 2, head[1] - 14), (head[0] + 16, head[1] - 34), 9, 3, 1, [RED])  # plume
    # back arm (shield side) and sword arm
    part((sh[0] + 8, sh[1] + 6), (sh[0] + 12 - sw * .3, sh[1] + 54), 12, 3, 1, [SILV, GOLDK])
    r = P['raise_']; s = P['sword']
    hand = (sh[0] - lerp(6, 26, s) - 4 * r, sh[1] + lerp(50, 22, s) - 52 * max(0, r) + 18 * max(0, -r))
    part((sh[0] - 6, sh[1] + 6), hand, 12, 3, 1, [SILV, GOLDK])
    if s > 0:
        ang = math.radians(lerp(100, 35, s) + 120 * max(0, r) - 70 * max(0, -r))  # blade direction (degrees from +x, screen y down)
        tip = (hand[0] - 70 * s * math.cos(ang), hand[1] - 70 * s * math.sin(ang))
        part(hand, tip, 8, 4, 1, [RED, (230, 70, 60)], lab=4)
    for o in out: o[1] = [(X + (qx - X) * S, Y + (qy - Y) * S) for qx, qy in o[1]]
    return out
