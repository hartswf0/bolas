"""Title card (3 s) and end card (3 s). The end card shows the actual weight heat maps and the measured test numbers from
proof/weights_tests.json; it claims only what the film and the tests show. Writes cache/cards/title.jpg and end.jpg."""
import json, os
import numpy as np
from PIL import Image, ImageDraw
import world as Wd
from proof import draw_mesh

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'cache', 'cards'); os.makedirs(OUT, exist_ok=True)
PROOF = os.path.join(HERE, '..', 'proof')
BG = (20, 20, 38)
CREAM = (240, 230, 206)
RED = (214, 62, 40)


def base():
    c = np.zeros((Wd.H, Wd.W, 3), np.float32); c[:] = BG
    c *= Wd.TEX[..., None]
    return Image.fromarray(np.clip(c, 0, 255).astype(np.uint8))


def title():
    z = np.load(os.path.join(HERE, 'cache', 'proof_mesh.npz'))
    V, F = z['V'], z['F']
    img = base(); d = ImageDraw.Draw(img)
    sc = 520; ox, oy = 700, 650
    tp = lambda q: (ox + q[0] * sc, oy - q[1] * sc)
    for f in F:
        d.line([tp(V[f[0]]), tp(V[f[1]]), tp(V[f[2]]), tp(V[f[0]])], fill=(120, 40, 34), width=1)
    big = Wd.font('f8.ttf', 74, 800); mid = Wd.font('f27.ttf', 30); mono = Wd.font('f14.ttf', 18)
    d.text((64, 70), 'PAE-02 · SCION 12', font=big, fill=CREAM)
    d.text((64, 150), 'Alec Jacobson — Localized Deformation Weights', font=Wd.font('f8.ttf', 46, 700), fill=RED)
    d.text((64, 222), 'The threshold, cut from one sheet of lace paper.', font=mid, fill=CREAM)
    d.text((64, 640), 'the dog’s triangle mesh: %d vertices, %d triangles, %d pierced holes' %
           (len(V), len(F), json.load(open(os.path.join(PROOF, 'weights_tests.json')))['mesh']['holes']), font=mono, fill=(170, 160, 150))
    img.save(os.path.join(OUT, 'title.jpg'), quality=94)


def end():
    z = np.load(os.path.join(HERE, 'cache', 'proof_mesh.npz'))
    V, F, W, Wn, Xb, Xn = (z[k] for k in ('V', 'F', 'W', 'Wn', 'Xb', 'Xn'))
    T = json.load(open(os.path.join(PROOF, 'weights_tests.json')))
    import dog as D
    hs = D.handles(); names = [h['name'] for h in hs]
    img = base(); d = ImageDraw.Draw(img)
    h1 = Wd.font('f8.ttf', 40, 800); lab = Wd.font('f14.ttf', 15); txt = Wd.font('f27.ttf', 21); mono = Wd.font('f14.ttf', 17)
    d.text((40, 24), 'Made of: one red paper dog, drawn in code and pierced with %d holes, moved only by its weights.' % T['mesh']['holes'],
           font=Wd.font('f27.ttf', 24), fill=CREAM)
    box = (-0.66, -0.02, 0.56, 0.92)
    tiles = [('fn_lower', 'bone: near foreleg'), ('ff_lower', 'bone: far foreleg'), ('cage1', 'cage vertex: back'),
             ('ear_near', 'point: ear tip')]
    for k, (nm, label) in enumerate(tiles):
        j = names.index(nm)
        im = draw_mesh(V, F, W[:, j], (290, 224), box, bg=(14, 14, 28), handles=[j], hs=hs)
        x = 40 + k * 302
        img.paste(im, (x, 74)); d.text((x + 6, 302), label, font=lab, fill=(200, 190, 180))
    j = names.index('fn_lower')
    row = [(draw_mesh(V, F, W[:, j], (290, 224), box, bg=(14, 14, 28), X=Xb), 'BBW: lift the near foreleg 50°'),
           (draw_mesh(V, F, Wn[:, j], (290, 224), box, bg=(14, 14, 28), X=Xn), 'naive inverse distance: same lift')]
    for k, (im, label) in enumerate(row):
        x = 40 + k * 302
        img.paste(im, (x, 336)); d.text((x + 6, 564), label, font=lab, fill=(200, 190, 180))
    L = T['locality_max_weight_across_leg_gap']; lift = T['lift_near_foreleg_50deg']
    lines = [
        'weights measured on the mesh:',
        '  bounds            %.3f .. %.3f' % (T['bounds']['min'], T['bounds']['max']),
        '  partition of 1    max error %.0e' % T['partition_of_unity_max_error'],
        '  exactly zero      %d %% of weights' % round(100 * T['sparsity']['share_of_weights_exactly_zero']),
        '  near leg on far   %.3f   (naive %.3f)' % (L['bbw']['fn_lower on ff paw/shin'], L['naive_inverse_distance']['fn_lower on ff paw/shin']),
        '  far leg moves     %.0f mm   (naive %.0f mm,' % (1000 * lift['bbw']['far_foreleg_max_displacement_m'],
                                                      1000 * lift['naive_inverse_distance']['far_foreleg_max_displacement_m']),
        '                    %d folded triangles)' % lift['naive_inverse_distance']['folded_triangles'],
        '  handles  %d bones, %d points, %d-vertex cage' % (T['mesh']['handles']['bones'], T['mesh']['handles']['points'],
                                                           T['mesh']['handles']['cage_vertices']),
    ]
    for k, s in enumerate(lines):
        d.text((660, 344 + k * 26), s, font=mono, fill=CREAM if k == 0 else (210, 200, 188))
    foot = ('Person, house, porch and dusk: cut-paper shapes drawn in code, the person rigged the same way. Voice: a formant '
            'synthesizer; all sounds synthesized. No recordings, no archive or web images. Type: Literata, Big Shoulders, JetBrains Mono (OFL).')
    import textwrap
    for k, s in enumerate(textwrap.wrap(foot, 118)):
        d.text((40, 604 + k * 26), s, font=Wd.font('f27.ttf', 18), fill=(190, 180, 168))
    img.save(os.path.join(OUT, 'end.jpg'), quality=94)


if __name__ == '__main__':
    title(); end()
