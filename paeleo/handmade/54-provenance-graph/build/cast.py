"""The other players: the person (a woman from 'Straight Talk' cut by hand, her legs drawn, her offered arm the hand of
'The Door to Heaven'), the door (the found door of 'Straight Talk', its own swing re-used), the lamp (a miner's lantern),
the doorway light, and the dog's turn (the archive dog's own turning frames)."""
import os
import numpy as np
from lineage import FOLDER
import world as Wd

DOOR = 'paeleo/handmade/kit/archive-door/'
DOOR_ID = 'ST:271d80c7-4f56-51b8-90fe-012dfb984b4f'
DOOR_TITLE = 'Straight Talk (NTIS, 1992)'
DOOR_URL = 'https://archive.org/details/gov.ntis.ava19144vnb1'
SIL = {'stops': [[0.0, [8, 6, 10]], [0.6, [26, 18, 22]], [1.0, [60, 42, 40]]]}
SKIN = {'stops': [[0.0, [14, 9, 9]], [0.5, [70, 44, 34]], [1.0, [196, 146, 108]]]}
DOOR_RAMP_D = {'stops': [[0.0, [14, 13, 22]], [0.6, [44, 40, 56]], [1.0, [84, 78, 92]]]}
DOOR_RAMP_L = {'stops': [[0.0, [40, 24, 16]], [0.6, [150, 104, 64]], [1.0, [236, 190, 130]]]}
WOMAN = [[258, 16], [276, 20], [288, 36], [290, 58], [284, 80], [300, 96], [314, 112], [322, 140], [324, 178], [314, 200], [310, 245],
         [306, 288], [218, 288], [216, 250], [212, 206], [202, 190], [197, 160], [200, 128], [208, 104], [232, 94], [244, 86], [238, 70], [234, 48], [240, 28]]
TURN_FRAMES = [11, 14, 15, 16, 17, 18, 19, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 45, 46]
DOOR_FRAMES = list(range(20, 32))


def build_cast(G):
    import ops as O
    O.register_more(G)
    C = {}
    # --- person torso: a woman from behind, cut along a drawn line, recoloured to a lamp-lit silhouette
    dmask = G.source(DOOR + 'masks.json', DOOR_ID + ':sam', 'SAM masks for ' + DOOR_TITLE, DOOR_URL, 'public_domain', 'masks')
    d0 = G.source(DOOR + 'frames/f000.jpg', DOOR_ID + ':f000', DOOR_TITLE, DOOR_URL, 'public_domain')
    cut = G.drawn('cut: woman, Straight Talk f000', {'polys': [WOMAN]}, 'hand-cut silhouette of the woman at the door (inferred cut line)')
    w = G.op('cut', [G.op('cutout', [d0, G.op('draw_alpha', [cut], {'size': [384, 288]})], {}), cut], {'mode': 'keep', 'feather': 0.6})
    w = G.op('crop', [w], {'box': [194, 12, 328, 288]}, label='person torso')
    C['torso'] = {'node': G.op('recolor', [w, G.drawn('ramp silhouette', SIL, 'near-black with a lamp-warm lift')], {'gain': 1.0, 'lift': 0.0}), 'origin': [194, 12],
                  'hip': [262, 272], 'top': [262, 16], 'shoulder': [306, 108], 'm_per_px': 0.86 / 256}
    # --- the offered arm: The Door to Heaven (1941), hand (SAM) + forearm (drawn box, luminance-gated), mirrored
    hp, hm = Wd.copy_found('hand-sam', [1])
    h1 = G.source(hp[1], 'DoortoHe1941:0870ef3a-b328-5284-890b-3e1ac18057c1:f001', 'The Door to Heaven (1941)', 'https://archive.org/details/DoortoHe1941', 'public_domain')
    hmk = G.source(hm, 'DoortoHe1941:0870ef3a-b328-5284-890b-3e1ac18057c1:sam', 'SAM masks for The Door to Heaven', 'https://archive.org/details/DoortoHe1941', 'public_domain', 'masks')
    hand = G.op('cutout', [h1, G.op('sam_mask', [h1, hmk], {'key': 1}, tags='documented')], {})
    fbox = G.drawn('cut: forearm box', {'polys': [[[272, 62], [384, 42], [384, 98], [272, 102]]]}, 'forearm region, inferred')
    fore = G.op('luma_gate', [G.op('cut', [G.op('cutout', [h1, G.op('draw_alpha', [fbox], {'size': [384, 288]})], {}), fbox], {'mode': 'keep', 'feather': 0.5})], {'lo': 0.26, 'soft': 0.08})
    arm = G.op('alpha_union', [hand, fore], {})
    arm = G.op('flip', [G.op('crop', [arm], {'box': [184, 38, 384, 116]})], {}, label='offered arm, mirrored to reach right')
    # in the flipped crop (200x78): elbow at the left edge, hand to the right
    C['arm'] = {'node': G.op('recolor', [arm, G.drawn('ramp skin', SKIN, 'skin at dusk, lamp-warm')], {'gain': 1.1, 'lift': -0.05}),
                'elbow': [2, 34], 'm_per_px': 0.40 / 200}
    # --- the door: the found door's own swing (frames 20..31 widen as it swings shut in the source) = our door opening
    C['door'] = []
    for f in DOOR_FRAMES:
        fr = G.source(DOOR + 'frames/f%03d.jpg' % f, DOOR_ID + ':f%03d' % f, DOOR_TITLE, DOOR_URL, 'public_domain')
        cm = G.op('cutout', [fr, G.op('sam_mask', [fr, dmask], {'key': f}, tags='documented')], {})
        cm = G.op('largest_blob', [cm], {'thr': 60})
        bb = cm_bbox(G, cm)
        cm = G.op('flip', [G.op('crop', [cm], {'box': bb})], {}, label='door f%03d, hinge on the right' % f)
        C['door'].append({'f': f, 'dusk': G.op('recolor', [cm, G.drawn('ramp door dusk', DOOR_RAMP_D, '')], {'gain': 1.0, 'lift': 0}),
                          'lit': G.op('recolor', [cm, G.drawn('ramp door lamp', DOOR_RAMP_L, '')], {'gain': 1.0, 'lift': 0}), 'size': G.get(cm).size})
    # --- the lamp: a miner's safety lantern (Anthracite: Pre-Shift Examinations), hung in the room
    lp, lm = Wd.copy_found('lantern-sam', [20])
    l20 = G.source(lp[20], 'msha.dvd614:4e46b7b2-909b-5072-8dbf-30085bb76742:f020', 'Anthracite: Pre-Shift Examinations of Underground Mines', 'https://archive.org/details/gov.msha.dvd614', 'public_domain')
    lmk = G.source(lm, 'msha.dvd614:4e46b7b2-909b-5072-8dbf-30085bb76742:sam', 'SAM masks for Anthracite', 'https://archive.org/details/gov.msha.dvd614', 'public_domain', 'masks')
    lc = G.op('cutout', [l20, G.op('sam_mask', [l20, lmk], {'key': 20}, tags='documented')], {})
    lc = G.op('crop', [G.op('largest_blob', [lc], {'thr': 60})], {'box': cm_bbox(G, G.op('largest_blob', [lc], {'thr': 60}))})
    C['lamp'] = {'lit': G.op('recolor', [lc, G.drawn('ramp lantern', Wd.LANTERN_RAMP, '')], {'gain': 1.2, 'lift': 0.05}),
                 'dusk': G.op('recolor', [lc, G.drawn('ramp lantern dim', DOOR_RAMP_D, '')], {'gain': 1.0, 'lift': 0.1})}
    C['lamp']['size'] = G.get(C['lamp']['lit']).size
    C['glow'] = G.op('radial', [], {'size': [400, 400], 'color': [255, 196, 120, 150], 'falloff': 1.8})
    # --- the doorway light, synthesised from recorded geometry at plate resolution
    C['beam'] = G.op('beam', [], {'size': [Wd.PW, Wd.PH], 'door_px': Wd.P(Wd.WALL_OUT, 0), 'color': [255, 182, 108, 165], 'reach_px': 4.6 * Wd.PPM, 'ppm': Wd.PPM, 'h1': 0.95, 'h2': 2.4})
    C['channel'] = G.op('hgradient', [], {'size': [int(0.92 * Wd.PPM), int(Wd.LINTEL * Wd.PPM)], 'color': [255, 196, 128], 'a0': 0.85, 'a1': 0.45})
    # --- the dog's own turn: the archive dog's turning frames, matted, cleaned, recoloured
    masks = [k for k, n in G.nodes.items() if n.get('source_id', '').endswith(':sam') and 'New Jersey' in n.get('title', '')][0]
    from dogrig import DOG, DOG_ID, DOG_TITLE, DOG_URL
    import assets
    C['turn'] = []
    for f in TURN_FRAMES:
        fr = G.source(DOG + 'frames/f%03d.jpg' % f, DOG_ID + ':f%03d' % f, DOG_TITLE, DOG_URL, 'public_domain')
        cm = G.op('cutout', [fr, G.op('sam_mask', [fr, masks], {'key': f}, tags='documented')], {})
        cm = G.op('largest_blob', [cm], {'thr': 60})
        bb = cm_bbox(G, cm, 3)
        cm = G.op('crop', [cm], {'box': bb}, label='dog turn f%03d' % f)
        ent = {'f': f, 'origin': bb[:2], 'size': G.get(cm).size}
        for k, (ramp, gain, lift) in {'dusk': (assets.RAMP_DUSK, 1.15, 0.02), 'lamp': (assets.RAMP_LAMP, 1.1, 0.05)}.items():
            ent[k] = G.op('recolor', [cm, G.drawn('ramp ' + k, ramp, '')], {'gain': gain, 'lift': lift})
        C['turn'].append(ent)
    return C


def cm_bbox(G, nid, pad=2):
    im = G.get(nid)
    bb = im.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox()
    return [max(0, bb[0] - pad), max(0, bb[1] - pad), min(im.size[0], bb[2] + pad), min(im.size[1], bb[3] + pad)]
