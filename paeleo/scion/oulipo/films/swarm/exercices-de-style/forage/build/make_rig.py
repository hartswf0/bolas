import json, math
WS = '/home/user/bolas/paeleo/scion/oulipo/films/swarm/exercices-de-style/forage/'
P = json.load(open(WS + 'build/_pieces.json'))
J = ['torso', 'head', 'hem', 'upper_arm', 'forearm_hand', 'thigh_front', 'shin_shoe_front', 'thigh_back', 'shin_shoe_back']
def r(x): return round(x, 2)
walk = []
for i in range(12):
    p = i / 12.0; w = 2 * math.pi * p
    tf = 18 * math.sin(w); tb = -tf
    sf = -32 * max(0.0, math.cos(w)) ** 1.5   # knee folds while the leg swings forward
    sb = -32 * max(0.0, -math.cos(w)) ** 1.5
    walk.append(dict(drawing=i + 1, root_dx_frac=r(-0.035 * i), bob_frac=r(-0.012 * math.cos(2 * w)), torso=r(2.0 + 0.8 * math.cos(2 * w)),
                     head=r(-1.5 + 1.0 * math.sin(2 * w + 0.5)), hem=r(-4.0 * math.sin(w - 0.7)), upper_arm=r(-2.5 * math.sin(w)), forearm_hand=r(1.0 * math.sin(w)),
                     thigh_front=r(tf), shin_shoe_front=r(sf), thigh_back=r(tb), shin_shoe_back=r(sb),
                     contact=('front' if i == 3 else 'back' if i == 9 else None)))
Z = lambda **k: {j: k.get(j, 0.0) for j in J}
poses = {
 'E1_arrive': dict(note='18:00 stands, envelope held at the pocket (hand in pocket pose of the negative)', **Z(torso=1.5)),
 'E2_bell': dict(note='18:02 head jerks up toward the bell: +12 deg over 3 frames, then 6-frame overshoot to +15 and back to +12', **Z(torso=-1.0, head=12.0)),
 'E3_tear': dict(note='18:04 forearm raised to chest to tear; the tear itself is the handmade S5b paper', **Z(torso=3.0, head=-6.0, upper_arm=38.0, forearm_hand=-95.0)),
 'E4_find': dict(note='18:05 holds the key up at shoulder height, looking at it', **Z(torso=-1.0, head=-4.0, upper_arm=70.0, forearm_hand=-60.0)),
 'E5_leave': dict(note='18:06 stoops to the bench: lean, knees give, arm forward and down', **Z(torso=14.0, head=-8.0, upper_arm=42.0, forearm_hand=-20.0, thigh_front=12.0, shin_shoe_front=-14.0, thigh_back=-4.0, shin_shoe_back=-10.0, hem=-6.0)),
 'E6_exit': dict(note='18:07 walks away left: use walk_cycle drawings 1-12, at least 2 cycles, scale -3% per step', **Z()),
}
rig = dict(
  rig_id='visitor-bain-1909@1', units='crop pixels of films/sources/exercices-de-style/forage/bain_03026_visitor_crop.png (804x2173); angles in degrees, +clockwise on screen (y down), local to parent',
  source=dict(title='Judge Crane and Chief Clerk (Hains trial) [on sidewalk, New York], LC-B2-623-4; the unnamed man at right', crop_box_in_tif=[3966, 1505, 4770, 3678]),
  facing='three-quarter left; forward = -x; positive thigh angle swings the foot forward (left)',
  root='torso', root_pivot='hip', fk_order='world = parent_world @ T(pivot_parent_offset) @ R(angle) ; draw by z ascending',
  pieces={k: dict(v, joint_name={'torso': 'hip', 'head': 'neck', 'hem': 'coat_waist', 'upper_arm': 'shoulder', 'forearm_hand': 'elbow', 'thigh_front': 'hip_front', 'shin_shoe_front': 'knee_front', 'thigh_back': 'hip_back', 'shin_shoe_back': 'knee_back'}[k]) for k, v in P['pieces'].items()},
  z_order=sorted(P['pieces'], key=lambda k: P['pieces'][k]['z']),
  bone_lengths=P['bones'],
  joint_limits=dict(head=[-15, 18], upper_arm=[-20, 80], forearm_hand=[-110, 10], thigh_front=[-25, 25], thigh_back=[-25, 25], shin_shoe_front=[-45, 0], shin_shoe_back=[-45, 0], hem=[-8, 8], torso=[-5, 18]),
  invariants=['bone lengths constant (pivots are fixed points of each piece)', 'head pivot stays on the collar pin (neck)', 'during a contact drawing the planted foot does not slide: root_dx per drawing equals the stance foot travel (0.035 of figure height)', 'door layer is not part of this rig'],
  walk_cycle=dict(drawings=12, exposure='on twos (each drawing held 2 frames at 24 fps): one cycle = 24 frames = 2 steps', step_sound_on=['drawing 4 (front heel)', 'drawing 10 (back heel)'], table=walk),
  beat_poses=poses,
  inventions=P['inventions'] + [dict(piece='all', region='hat, face and trouser outlines are drawn scissor paths where the soft-focus negative gives GrabCut no edge (see build/cut_visitor.py HEAD/LEGS)', px=None)],
  closeup_hand=P['closeup'],
  fallback=dict(file='films/sources/exercices-de-style/forage/man_rgba.png', note='Agence Rol 1917 waist-up portrait, re-cut: hat with drawn brim, sleeve flower debris removed (magenta in man_failmask.png)'),
  key=dict(file='films/sources/exercices-de-style/forage/key_rgba.png', note='Edna C. Rex watercolour, bow hole open; 299x800; pivot for settle at the bit-end contact point', settle_pivot_local=[150, 790]),
)
json.dump(rig, open(WS + 'rig.json', 'w'), indent=1, ensure_ascii=False)
print('rig ok', len(walk))
