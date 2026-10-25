"""Build every asset node of the film from its sources, recording the DAG (lineage/lineage.json)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lineage import Graph, FOLDER, REPO
import ops
from dogrig import K11, K18, DOG, DOG_ID, DOG_TITLE, DOG_URL

RAMP_DUSK = {'stops': [[0.0, [18, 17, 34]], [0.35, [58, 54, 82]], [0.7, [138, 128, 140]], [1.0, [222, 206, 186]]]}
RAMP_LAMP = {'stops': [[0.0, [34, 20, 18]], [0.35, [104, 62, 40]], [0.7, [206, 150, 96]], [1.0, [255, 228, 176]]]}


def bbox_of(G, nid, pad=3):
    im = G.get(nid)
    bb = im.getchannel('A').point(lambda v: 255 if v > 6 else 0).getbbox()
    return [max(0, bb[0] - pad), max(0, bb[1] - pad), min(im.size[0], bb[2] + pad), min(im.size[1], bb[3] + pad)]


def piece(G, nid, label, recolor_ramps):
    """crop a full-frame piece to its bbox; return {variant: node} plus origin offset (piece px = frame px - origin)."""
    box = bbox_of(G, nid)
    c = G.op('crop', [nid], {'box': box}, label=label + ' crop')
    out = {'raw': c, 'origin': box[:2]}
    for k, (ramp, gain, lift) in recolor_ramps.items():
        out[k] = G.op('recolor', [c, ramp], {'gain': gain, 'lift': lift}, label=label + ' recolour ' + k)
    return out


def build_dog(G):
    masks = G.source(DOG + 'masks.json', DOG_ID + ':sam', 'SAM masks for ' + DOG_TITLE, DOG_URL, 'public_domain', 'masks')
    f11 = G.source(DOG + 'frames/f011.jpg', DOG_ID + ':f011', DOG_TITLE, DOG_URL, 'public_domain')
    f18 = G.source(DOG + 'frames/f018.jpg', DOG_ID + ':f018', DOG_TITLE, DOG_URL, 'public_domain')
    m11 = G.op('sam_mask', [f11, masks], {'key': 11}, tags='documented', label='SAM matte f011')
    c11 = G.op('cutout', [f11, m11], {}, label='dog cut out of f011')
    m18 = G.op('sam_mask', [f18, masks], {'key': 18}, tags='documented', label='SAM matte f018')
    c18 = G.op('cutout', [f18, m18], {}, label='dog cut out of f018')
    d = lambda name, polys, note: G.drawn(name, {'polys': polys}, note)
    rd = G.drawn('ramp dusk', RAMP_DUSK, 'dusk gradient map, dark indigo to warm grey')
    rl = G.drawn('ramp lamp', RAMP_LAMP, 'lamplight gradient map, umber to candle')
    ramps = {'dusk': (rd, 1.15, 0.02), 'lamp': (rl, 1.1, 0.05)}
    P = {}
    head_poly = d('cut: f011 head/neck', [K11['neck_cut']], 'cut line through the neck, inferred')
    P['head_up'] = piece(G, G.op('cut', [c11, head_poly], {'mode': 'keep', 'feather': 1.2}, label='head (up) of f011'), 'head_up', ramps)
    body = G.op('cut', [c11, d('cut: f011 body minus head', [K11['neck_cut_body']], 'overlap band behind the head cut')], {'mode': 'remove', 'feather': 0.8})
    body = G.op('cut', [body, d('cut: f011 below belly', [K11['legs_below']], 'legs removed from the body below the belly line')], {'mode': 'remove', 'feather': 1.5})
    P['body'] = piece(G, body, 'body', ramps)
    for leg in ('F1', 'F2', 'H'):
        poly = d('cut: f011 leg ' + leg, [K11[leg]], 'leg region, inferred from pose and silhouette')
        lg = G.op('cut', [c11, poly], {'mode': 'keep', 'feather': 0.8})
        # feather the top of the leg so the seam under the body blends
        top = K11[leg][0][1]
        lg = G.op('cut', [lg, d('cut: leg top feather ' + leg, [[[0, top + 6], [384, top + 6], [384, 288], [0, 288]]], 'soft top')], {'mode': 'keep', 'feather': 3.0})
        P[leg] = piece(G, lg, 'leg ' + leg, ramps)
    hl = G.op('cut', [c18, d('cut: f018 head low', [K18['head_cut']], 'head carried low, from f018')], {'mode': 'keep', 'feather': 1.2})
    P['head_low'] = piece(G, hl, 'head_low', ramps)
    tl = G.op('cut', [c18, d('cut: f018 tail', [K18['tail_cut']], 'the tail, from f018')], {'mode': 'keep', 'feather': 0.8})
    P['tail'] = piece(G, tl, 'tail', ramps)
    return P


def main():
    G = Graph(); ops.register_all(G)
    P = build_dog(G)
    import world
    ops.register_world(G)
    plates = world.build_world(G)
    import cast
    C = cast.build_cast(G)
    import PIL
    G.get(plates['dusk']).convert('RGB').resize((world.PW // 2, world.PH // 2)).save(os.path.join(FOLDER, 'build', 'cache', 'plate_dusk.jpg'))
    G.get(plates['lit']).convert('RGB').resize((world.PW // 2, world.PH // 2)).save(os.path.join(FOLDER, 'build', 'cache', 'plate_lit.jpg'))
    os.makedirs(os.path.join(FOLDER, 'lineage'), exist_ok=True)
    G.save(os.path.join(FOLDER, 'lineage', 'lineage.json'), {'dog': P, 'plates': plates, 'cast': C})
    print(len(G.nodes), 'nodes')
    return G, P, plates, C


if __name__ == '__main__':
    main()
