"""Editor r1: apply the repair-round changes to page/build_page.py (original kept as editor/build_page.r0.py)."""
p = '/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways-template/page/build_page.py'
s = open('/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways-template/editor/build_page.r0.py').read()


def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:60], s.count(a))
    s = s.replace(a, b)


rep('''OFFICE = cv2.imread(str(PIECES / "office.plate.png"), cv2.IMREAD_GRAYSCALE).astype(np.float32)
SETP = cv2.imread(str(PIECES / "set.plate.png"), cv2.IMREAD_GRAYSCALE).astype(np.float32)''',
'''# r1 (editor): the clerk-removed plates with the head ghost, arm residue and desk smear repaired from the same
# photograph (films/swarm/99-ways-template/editor/plate_repair.py; same-column/plank-period copies + interpolation)
EDIT = SRC / "editor"
OFFICE = cv2.imread(str(EDIT / "office.plate.r1.png"), cv2.IMREAD_GRAYSCALE).astype(np.float32)
SETP = cv2.imread(str(EDIT / "set.plate.r1.png"), cv2.IMREAD_GRAYSCALE).astype(np.float32)''')
rep('''def solve_pencil_to_chin(target):
    """FK solve (in source coords): forearm angle about the elbow + pencil angle about the grip so the tip meets the chin."""''',
'''def solve_pencil_to_chin(target, head=0.0):
    """FK solve (in source coords): forearm angle about the elbow + pencil angle about the grip so the tip meets the chin.
    The chin target rides on the head, so it is carried through the collar hinge first (head angle)."""
    target = apply(about(COLLAR, R(head)), target)''')
rep('''    return dict(arm=float(a), pencil=float(ang1 - ang0), head=0.0)


CHIN_TOUCH = (CHIN[0] + 26, CHIN[1] - 4)       # the underside of the chin, his left side (source coords)
POSE_CHIN = solve_pencil_to_chin(np.array(CHIN_TOUCH))''',
'''    return dict(arm=float(a), pencil=float(ang1 - ang0), head=float(head))


# r1: the point of the chin itself (source px, read off the master between the mouth and the jaw line), not the
# collar-height 'chin' pivot, which sits on his neck
CHIN_TOUCH = (3012.0, 2060.0)
H8 = -11.0                       # P8: head tipped up on the collar hinge (he faces right; the key is on his left)
H5 = -7.0                        # P5: head up toward the clock
POSE_CHIN = solve_pencil_to_chin(np.array(CHIN_TOUCH), head=H8)''')
rep('''POSE_ARRIVE = dict(arm=-34.0, pencil=24.0, head=0.0)                      # arm lowered across his front, walking''',
'''POSE_ARRIVE = dict(arm=-34.0, pencil=24.0, head=0.0)                      # arm lowered across his front, walking
POSE_WALK = dict(arm=-52.0, pencil=30.0, head=-3.0)                       # r1 P3: arm swung down, pencil in hand''')
rep('''    lift = T(980, -170) @ about(ROOT_, R(-5))''',
'''    lift = T(P2_RIGHT, -170) @ about(ROOT_, R(-5))      # r1: only his shoulder is left at the edge: the desk is empty''')
rep('''def P2():''', '''P2_RIGHT = 1640.0
P3_VIEW = (0.49, 2790, 470)             # r1: the closed double cupboard, framed above the desk (no desk in frame)
P3_STEP = (640.0, -290.0, 4.0)          # r1: raised to standing height, pitched into the step


def P2():''')
i0 = s.index('def P3():')
i1 = s.index('VW = (0.538')
s = s[:i0] + '''def P3():
    """r1: he walks past the closed SERVICE door. Camera on the double cupboard of the same office, above the desk;
    the SERVICE card on the right leaf's upper panel, clear of the lamp cord; he is cut by the panel's lower edge
    at the waist (standing height), pitched into the step, arm swung down."""
    w, h = psize("P3")
    V = P3_VIEW
    P = Panel("P3", view_plate(OFFICE, *V, w, h))
    Mw = W2P(*V)
    sign_card(P, apply(Mw, P3_CARD), 150, -2)
    dx, dy, pitch = P3_STEP
    step = T(dx, dy) @ about(ROOT_, R(pitch))
    lay_clerk(P, Mw @ step, POSE_WALK, order=("clerk.torso", "clerk.head"), rec=FK)   # arm hangs below the frame
    SPEECH["P3"] = []
    return P


P3_CARD = (3900, 905)


''' + s[i1:]
i0 = s.index('    # the visitor beyond the frosted glass')
i1 = s.index("    # the clerk's head and shoulder enter at the right edge")
s = s[:i0] + '''    # r1: nobody is drawn behind the glass: the asker is off-panel, on the platform (the tail goes out through the window)
''' + s[i1:]
rep('''    Mc = T(505, 430) @ S(kc) @ T(-CX, -1660) @ MIR()
    lay_clerk(P, Mc, POSE_ARRIVE, rec=FK)''', '''    Mc = T(505, 430) @ S(kc) @ T(-CX, -1660) @ MIR()
    # r1: head and shoulders only (the pencil hand stays below the frame, so nothing reads as a look at a wristwatch);
    # head up on the collar, toward the voice at the window
    lay_clerk(P, Mc, dict(POSE_ARRIVE, head=H4), order=("clerk.torso", "clerk.head"), rec=FK)''')
rep('''VW = (0.538, 60, 600)''', '''VW = (0.538, 60, 600)
H4 = -6.0''')
rep('''    Mc = T(690, 395) @ S(kc) @ T(-CX, -1660) @ MIR()
    lay_clerk(P, Mc, POSE_SOURCE, rec=FK)
    mouth = apply(Mc, (2992, 2018))
    SPEECH["P5"] = [balloon(P, "b_ten_past", ["Ten past", "four!"], 70, (300, 160), (mouth[0] - 46, mouth[1] + 8), 33, tail_w=0.24, bend=0.10)]''',
'''    Mc = T(P5_AT[0], P5_AT[1]) @ S(kc) @ T(-CX, -1660)          # r1: un-mirrored, so he faces the clock (upper right)
    lay_clerk(P, Mc, dict(POSE_SOURCE, head=H5), rec=FK)
    mouth = apply(Mc @ about(COLLAR, R(H5)), (2992, 2018))
    SPEECH["P5"] = [balloon(P, "b_ten_past", ["Ten past", "four!"], 70, (250, 160), (mouth[0] - 14, mouth[1] + 4), 33, tail_w=0.24, bend=0.10)]''')
rep('''def P5():''', '''P5_AT = (600, 395)


def P5():''')
rep('''VC8 = (0.80, 2790, 600)''', '''VC8 = (0.84, 2860, 640)
P8_ROOT = (640, 1150)
FORGOT = ["Now... what", "did I come over", "here for?"]       # r1: the production's own words''')
rep('''    sign_card(P, apply(Mw, (4110, 900)), 0.80 * 330, -2)
    lay_door_key(P, *VC8, swing=0.34, rec=FK)
    kc = 0.74
    Mc = T(760, 1010) @ S(kc) @ T(-ROOT_[0], -ROOT_[1]) @ MIR()
    lay_clerk(P, Mc, POSE_CHIN, rec=FK)
    mouth = apply(Mc, (2992, 2018))
    SPEECH["P8"] = [balloon(P, "b_forgot", ["What the hell", "was I looking", "for, anyway?"], 68, (420, 190),
                            (mouth[0] + 4, mouth[1] - 4), 83, tail_w=0.22, bend=-0.08)]''',
'''    sign_card(P, apply(Mw, (4110, 900)), VC8[0] * 330, -2)
    lay_door_key(P, *VC8, swing=0.34, rec=FK)
    # r1: un-mirrored, so he faces right, AWAY from the key on the door at the left; head tipped up on the collar;
    # he stands nearer the door, the key just beyond his left elbow
    kc = 0.74
    Mc = T(P8_ROOT[0], P8_ROOT[1]) @ S(kc) @ T(-ROOT_[0], -ROOT_[1])
    lay_clerk(P, Mc, POSE_CHIN, rec=FK)
    mouth = apply(Mc @ about(COLLAR, R(H8)), (2992, 2018))
    SPEECH["P8"] = [balloon(P, "b_forgot", FORGOT, 62, B8_AT, (mouth[0] + 10, mouth[1] - 6), 83, tail_w=0.22, bend=0.08)]''')
rep('''def P8():''', '''B8_AT = (390, 160)


def P8():''')
open(p, 'w').write(s)
print("patched")
