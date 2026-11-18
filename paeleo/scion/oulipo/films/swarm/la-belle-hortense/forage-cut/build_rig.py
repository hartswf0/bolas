"""Merge the cut manifests into swarm/la-belle-hortense/rig.json (SCION 29 deliverable; SCION 2 joint graph).

Coordinates: every pivot is given in source-crop px ('pivots_crop') and in trimmed-piece px ('pivots_piece').
crop_box is in the source file's px. Angles in degrees, positive = clockwise on screen (image y down).
"""
import json, os
ROOT = '/home/user/bolas/paeleo/scion/oulipo/films'
CUT = ROOT + '/sources/la-belle-hortense/forage/cut/'
REL = 'films/sources/la-belle-hortense/forage/'

SRC = {
    'conductor': ('COND', 'LoC 2017844115 (Jack Delano 1943, FSA/OWI, PD)', 'forage/raw/loc_2017844115.jpg'),
    'bell': ('BELL', 'Commons File:Bahnhofsglocke HLB 1.jpg (Reinhard Dietrich, PD)', None),
    'key': ('KEY', 'Commons File:Skeletonkey.png (Blenheimears, CC0)', None),
    'bench': ('BENCH', 'LoC 2013633886 (Carol M. Highsmith 2012, PD)', None),
    'door': ('SHED-DOOR', 'Commons File:Bourré (Loir-et-Cher) (50866795131).jpg (Daniel Jolivet, CC BY 2.0)', None),
    'visitor': ('VISITOR', 'LoC 2017750547 (Jack Delano 1941, FSA/OWI, PD), file 8a36813v.jpg', None),
}
JOINTS = {
    'conductor': {
        'coat_panel': (None, None, [-2, 14], 'root: coat + body; lean forward 9 deg in the run; dyed red via coat_dye.png'),
        'coat_upper': (None, None, [-2, 14], 'RUN VARIANT root: coat above the waist (y<448); use with skirtN/skirtF instead of coat_panel'),
        'skirtN': ('coat_upper', 'pivot_hipN', [-25, 30], 'RUN VARIANT near coat flap hinged at the hip, follows thighN; dye skirtN_dye.png'),
        'skirtF': ('coat_upper', 'pivot_hipF', [-25, 30], 'RUN VARIANT far coat flap hinged at the hip, follows thighF; dye skirtF_dye.png'),
        'head_cap': ('coat_panel', 'pivot_neck', [-8, 8], 'nods with the stride (counter-rotation)'),
        'arm': ('coat_panel', 'pivot_shoulder', [-35, 35], 'sleeve + forearm + hand, one piece; arm swing; dyed via arm_dye.png'),
        'newspaper': ('coat_panel', 'pivot_paper', [-6, 6], 'in the coat pocket; secondary flutter only'),
        'thighF': ('coat_panel', 'pivot_hemF', [-35, 40], 'far leg upper part below the hem (hip hidden by coat); print darker'),
        'shinF': ('thighF', 'pivot_knee', [0, 75], 'far shin + shoe, knee hinge'),
        'thighN': ('coat_panel', 'pivot_hemN', [-35, 40], 'near leg upper part below the hem'),
        'shinN': ('thighN', 'pivot_knee', [0, 75], 'near shin + shoe, knee hinge'),
    },
    'bell': {
        'yoke': (None, None, [0, 0], 'fixed crossbar + hub (wall/post bracket)'),
        'body': ('yoke', 'pivot_axle', [-38, 38], 'pendulum, theta(t)=theta0 exp(-t/tau) cos(wt)'),
        'clapper': ('body', 'pivot_clapper', [-25, 25], 'child pendulum, lags the body; strike when |clapper-body| hits limit'),
    },
    'key': {'key': (None, None, [-180, 180], 'free body: falls, turns, lands; dyed brass #c9a23a')},
    'visitor': {
        'body': (None, None, [-6, 6], 'root: hat + dress + right arm with leash hand; seen from behind, walks away/into depth'),
        'forearm': ('body', 'pivot_elbowL', [-20, 25], 'left forearm + hand; carries the envelope (prop attached at hand)'),
        'shinL': ('body', 'pivot_kneeL', [-30, 35], 'left shin + shoe, hinged at the dress hem (knee hidden by the dress)'),
        'shinR': ('body', 'pivot_kneeR', [-30, 35], 'right shin + shoe, hinged at the dress hem'),
    },
    'bench': {'bench': (None, None, [0, 0], 'static prop; seat line for the coat and key')},
    'door': {'leaf': (None, 'hinge_top', [0, 80], 'swings on the left jamb; render as horizontal foreshortening cos(angle)')},
}

rig = {'generated_by': 'swarm/la-belle-hortense/forage-cut/build_rig.py', 'verified': '2026-11-16',
       'angle_convention': 'degrees, positive clockwise on screen; 0 = pose as photographed',
       'figures': {}}
for fig, joints in JOINTS.items():
    mf = CUT + fig + '/manifest.json'
    if not os.path.exists(mf):
        continue
    m = json.load(open(mf))
    sid, sdesc, sfile = SRC[fig]
    entry = {'source_id': sid, 'source': sdesc, 'source_file': REL + (m.get('source_file', '') or sfile or '').replace('forage/', ''),
             'crop_box': m['crop_box'], 'grabcut_report': m['grabcut'],
             'failure_mask': REL + f'cut/{fig}/failure_mask.png', 'full_mask': REL + f'cut/{fig}/grabcut_mask.png',
             'pieces': {}}
    if fig == 'conductor':
        entry['dye_masks'] = {'coat': REL + 'cut/conductor/coat_dye.png', 'arm': REL + 'cut/conductor/arm_dye.png',
                              'frame': 'full crop (312x715), same frame as crop_box',
                              'dye': '#e2011b laid as multiply over the monochrome print so the coat folds show through'}
        entry['fullcrop_npz'] = REL + 'cut/conductor/pieces_fullcrop.npz'
    for p, (parent, piv, lim, note) in joints.items():
        pm = m['pieces'][p]
        entry['pieces'][p] = {'png': REL + pm['png'], 'offset_in_crop': pm['offset_in_crop'], 'size': pm['size'],
                              'parent': parent, 'joint_pivot': piv, 'angle_limits_deg': lim,
                              'pivots_crop': pm['pivots_crop'], 'pivots_piece': pm['pivots_piece'], 'note': note}
    if 'extra' in m:
        entry['extra'] = m['extra']
    rig['figures'][fig] = entry
json.dump(rig, open(ROOT + '/swarm/la-belle-hortense/rig.json', 'w'), indent=1, ensure_ascii=False)
print('figures', list(rig['figures']))
