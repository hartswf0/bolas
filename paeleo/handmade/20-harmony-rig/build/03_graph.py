"""SCION 20 · 03: the node network, as data (scene/nodegraph.json), and its dependency test.
The renderer (render.html) evaluates exactly this graph per frame, in topological order: it refuses to run if a node
names an input that does not exist, or if the graph has a cycle. 'pos' is only the layout used on the end card."""
import json, os
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = []
def node(id, type, ins=(), pos=(0, 0), **params):
    N.append(dict(id=id, type=type, inputs=list(ins), params=params, pos=list(pos)))

node('XSHEET', 'ExposureSheet', (), (0, 0), file='scene/xsheet.json')
node('LIB', 'DrawingLibrary', (), (0, 1), file='scene/library.json')
node('PALETTE', 'Palette', (), (0, 2), file='scene/palette.json', palettes=['dusk', 'lamp'])
node('CAM', 'Camera', ('XSHEET',), (0, 3), X0=315, K=198, FLOOR=620, zoom='cam_z', center=['cam_cx', 'cam_cy'], note='static wide until 23 s, then a push-in on the doorway')
node('LIGHT', 'Light', ('XSHEET', 'CAM'), (1, 3), field='spill', key_dusk=[0.6, -0.8], key_lamp=[-0.93, -0.36])
node('BG', 'Background', ('CAM',), (1, 4), painted='build/background.js')
node('PEG_door', 'Peg', ('CAM', 'XSHEET'), (1, 0), x=0.34, swing='door')
node('DOOR', 'Element', ('PEG_door', 'LIB', 'PALETTE', 'LIGHT'), (2, 0), column=None, element='door', drawing='panel', lamp=0.85, tone=0.0)
node('PEG_person', 'Peg', ('CAM', 'XSHEET'), (1, 1), x='px')
node('PERSON', 'Element', ('PEG_person', 'LIB', 'PALETTE', 'LIGHT'), (2, 1), column='person', element='person', lamp=0.85, light_from=[-0.75, -0.66])
node('MOUTH', 'Element', ('PERSON', 'LIB', 'XSHEET'), (3, 1), column='mouth', element='person_mouth', anchor='mouth')
node('PEG_dog', 'Peg', ('CAM', 'XSHEET'), (1, 2), x='x_peg', y='y', mirror='mirror', scale=1.12)
node('BODY', 'Element', ('PEG_dog', 'LIB', 'PALETTE', 'LIGHT'), (2, 2), column='body', element='dog_body')
node('PEG_head', 'Peg', ('PEG_dog', 'XSHEET'), (2, 3), x='hx', y='hy', rot='hrot', mirror='head_rel')
node('NECK', 'CurveDeformer', ('BODY', 'PEG_head'), (3, 3), base='anchor:neck', rest_length=0.15, widths=[0.125, 0.10])
node('HEAD', 'Element', ('PEG_head', 'LIB', 'PALETTE', 'LIGHT'), (3, 4), column='head', element='dog_head')
node('EAR', 'Element', ('HEAD', 'LIB'), (4, 4), column='ear', element='dog_ear', layers=['under', 'over'], note='drawn in the head frame: under = far ear behind the head, over = near ear')
node('PEG_tail', 'Peg', ('BODY',), (3, 2), anchor='tail')
node('CHAIN_tail', 'ChainDeformer', ('PEG_tail', 'XSHEET', 'LIB'), (4, 2), rots='tail_rots', joints=6)
node('TAIL', 'Element', ('CHAIN_tail', 'LIB', 'PALETTE', 'LIGHT'), (5, 2), column='tail', element='dog_tail')
node('COMP_dog', 'Composite', ('TAIL', 'NECK', 'BODY', 'HEAD', 'EAR', 'XSHEET'), (5, 3),
     order='tail, [head if head_behind], neck+body, [head+ears], [tail if tail_front]',
     passes='each element: Outline (matte dilated 1.3 px in ink) -> colour + line -> Tone (matte minus matte shifted toward the key light, multiply) -> Highlight (lit-edge band, screen)')
node('SHADOW_dog', 'CastShadow', ('COMP_dog', 'LIGHT', 'CAM'), (6, 3), squash=0.16, blur=3)
node('TEXT', 'Text', ('XSHEET',), (6, 0), field='sub', note="the person's words, never the dog's state")
node('COMP_scene', 'Composite', ('BG', 'LIGHT', 'DOOR', 'PERSON', 'MOUTH', 'SHADOW_dog', 'COMP_dog', 'TEXT'), (7, 2), order='BG, LIGHT, DOOR, PERSON(+MOUTH), SHADOW_dog, COMP_dog, TEXT')
node('GRADE', 'Grade', ('COMP_scene',), (8, 2), vignette=0.32)
node('WRITE', 'Write', ('GRADE',), (9, 2), file='film.mp4', size=[1280, 720], fps=24)

ids = {n['id'] for n in N}
bad = [(n['id'], i) for n in N for i in n['inputs'] if i not in ids]
assert not bad, bad
# topological order (Kahn); a cycle would leave nodes behind
order, done = [], set()
while len(order) < len(N):
    ready = [n for n in N if n['id'] not in done and all(i in done for i in n['inputs'])]
    assert ready, 'cycle in node graph'
    for n in ready: order.append(n['id']); done.add(n['id'])
json.dump(dict(about='SCION 20 node network. Pegs carry transforms, Elements expose drawings from the exposure sheet column, '
                     'deformers bend drawing points before the peg, composites order the elements; Light mixes the dusk and lamp palettes.',
               nodes=N, topological_order=order), open(os.path.join(D, 'scene/nodegraph.json'), 'w'), indent=1)
print('graph', len(N), 'nodes; dependencies ok; order', ' > '.join(order))
