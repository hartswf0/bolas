"""Write assets.json: every asset in the film, where it came from, its rights, and the operation that made it.
python3 build/assets.py"""
import hashlib, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def sha(p):
    return hashlib.sha256(open(os.path.join(ROOT, p), 'rb').read()).hexdigest()[:16]


A = []
drawn = {
    'dog_stand': 'the dog standing, in profile facing the door (body; the head is its own piece)',
    'dog_rear': 'the dog standing seen from behind: haunches, tucked tail, spine and saddle receding to the shoulders',
    'dog_sit_back': 'the dog sitting seen from behind (the held refusal), tail on the boards',
    'dog_lie': 'the dog lying sphinx-wise in profile, forelegs out, hind leg folded, tail along the boards',
    'head_side': 'the dog\'s head in profile with collar and brass tag (eye, nose and tag are feature-protected)',
    'head_back': 'the back of the dog\'s head: backs of the ears, nape, collar buckle, the tip of the muzzle and nose peeking past the cheek',
    'person_stand.body': 'the person standing in profile, cardigan with four buttons (buttons and eye feature-protected)',
    'person_stand.arm': 'the person\'s near arm (its own layer, moved by a hand handle and an IK elbow)',
    'person_sit.body': 'the person sitting on the crate beside the door',
    'person_sit.arm': 'the person\'s near arm while sitting (rests on the knee, then offered low)',
}
for k, what in drawn.items():
    A.append({'id': 'drawing:' + k, 'what': what, 'file': f'assets/drawings/{k}.png', 'sha256_16': sha(f'assets/drawings/{k}.png'),
              'source': 'drawn by this swarm in code (build/drawings.js: Catmull-Rom outlines, fills, procedural fur strokes, ink lines), rendered once in headless Chromium canvas (build/draw_assets.js)',
              'rights': 'own work made for this film; no found image, no tracing of footage, no image model',
              'operation': 'drawn'})
    A.append({'id': 'mesh:' + k, 'what': 'triangulated ARAP mesh of ' + k + ' with handles, cuts and feature-protect weights', 'file': f'assets/mesh/{k}.json',
              'source': 'computed from assets/drawings/' + k + '.png by build/mesh.py (grid cells clipped to the drawing alpha, two triangles per cell, explicit cuts by vertex duplication)',
              'rights': 'own work', 'operation': 'triangulated (computed)'})
for part in ('near', 'far'):
    A.append({'id': f'drawing:dog_stand.{part}', 'what': f'the standing dog drawing with the {"far" if part == "near" else "near"} side of the foreleg cut erased below the belly (round 2)',
              'file': f'assets/drawings/dog_stand.{part}.png', 'source': 'computed from assets/drawings/dog_stand.png by build/mesh.py', 'rights': 'own work',
              'operation': 'masked (computed): each side of the foreleg cut samples only its own leg, so a crossing leg carries none of the other'})
for line in open(os.path.join(ROOT, 'assets', 'quickdraw.ndjson')):
    d = json.loads(line)
    A.append({'id': f'quickdraw:{d["word"]}:{d["key_id"]}', 'what': f'a Quick, Draw! {d["word"]} drawing ({d["countrycode"]}, {d["timestamp"][:10]}), drawn into the dusk sky as chalk lines',
              'file': 'assets/quickdraw.ndjson', 'key_id': d['key_id'], 'source': f'/home/user/hartswf0/quickdraw/{d["word"]}.part (Quick, Draw! dataset)',
              'source_title': 'Quick, Draw! — Google Creative Lab and contributors', 'archive_url': 'https://github.com/googlecreativelab/quickdraw-dataset',
              'rights': 'CC BY 4.0, Google Creative Lab and contributors (credited on the end card)', 'operation': 'strokes copied verbatim, scaled and placed, stroked in canvas'})
A += [
    {'id': 'world', 'what': 'the house front, siding, door and frame, sill, window, porch boards, roof beam, posts, railing, steps, crate, the hall inside, dusk sky, light spill, paper grain',
     'file': 'build/render.html', 'source': 'drawn in canvas by this swarm at render time', 'rights': 'own work', 'operation': 'drawn (computed each frame)'},
    {'id': 'score', 'what': 'the PAELEO threshold score: the dog\'s decision trace, 768 frames', 'file': '../score/threshold-score.json',
     'source': 'paeleo/handmade/score/threshold-score.json (from paeleo/threshold/machine.js)', 'rights': 'Bolas project material', 'operation': 'read: times, x, acts and the person\'s circumstances drive the rig'},
    {'id': 'voice', 'what': 'the person\'s five lines: "Come here." "Come here!" "It\'s all right." (twice) "Come in."',
     'source': 'synthesized here with ffmpeg\'s flite filter (CMU Flite, voice "slt" from the CMU ARCTIC databases)', 'rights': 'CMU Flite and CMU ARCTIC are distributed under a free BSD-style licence permitting use and redistribution; the speech was generated here',
     'operation': 'synthesized (TTS), then for the soft lines low-passed, breath added, -12.5 dB'},
    {'id': 'sound', 'what': 'dusk air, crickets, paw clicks timed to the rig\'s planted feet, the sit and lie-down thumps, a sigh, tail knocks, a whine, the person\'s steps and the crate, the door creak, the warm chord that is the light, two plucks',
     'file': 'build/sound.py', 'source': 'synthesized in numpy by this swarm', 'rights': 'own work', 'operation': 'synthesized'},
    {'id': 'fonts', 'what': 'Big Shoulders Display (title, end card) and Literata (end card text, the spoken words at the foot of the frame)',
     'file': '../../../tools/paeleo/fonts/', 'source': 'tools/paeleo/fonts (Google Fonts, woff2)', 'rights': 'SIL Open Font License 1.1', 'operation': 'typeset'},
    {'id': 'not-used:archive-dog', 'what': 'paeleo/handmade/kit/archive-dog frames', 'source': 'Amateur Film New Jersey C (Home Movies, Internet Archive), public domain',
     'rights': 'public domain', 'operation': 'looked at once as a contact sheet for the build of a shepherd-type dog; nothing from it is in the film (no pixels, masks or keys)'},
]
json.dump({'swarm': 'SCION 09 · Takeo Igarashi — as-rigid-as-possible puppetry', 'assets': A}, open(os.path.join(ROOT, 'assets.json'), 'w'), indent=1)
print(len(A), 'assets')
