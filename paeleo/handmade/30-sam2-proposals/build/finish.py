"""Mux picture + sound into film.mp4 (faststart), cut the four stills from the encoded film, export the proposal
ledger (proposals/), and write assets.json."""
import json, os, subprocess, shutil
import numpy as np
from PIL import Image
from common import *
import film

SECT = os.path.join(OUT, 'proposals')


def mux():
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(CACHE, 'picture.mp4'), '-i', os.path.join(CACHE, 'sound.wav'),
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-shortest', '-movflags', '+faststart',
                    os.path.join(OUT, 'film.mp4')], check=True)
    pr = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v', '-show_entries',
                         'stream=nb_read_frames,duration', '-of', 'json', os.path.join(OUT, 'film.mp4')], capture_output=True, text=True)
    st = json.loads(pr.stdout)['streams'][0]
    size = os.path.getsize(os.path.join(OUT, 'film.mp4'))
    print('film frames', st['nb_read_frames'], 'duration', st['duration'], 'bytes', size)
    assert int(st['nb_read_frames']) == 912 and size <= 12 * 1024 * 1024


def stills():
    os.makedirs(os.path.join(OUT, 'stills'), exist_ok=True)
    for t in (3.6, 9.0, 19.0, 28.0):
        # frame-exact: scene frame round(t*24) is film frame 72 + that
        n = 72 + int(round(t * 24))
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(OUT, 'film.mp4'), '-vf', 'select=eq(n\\,%d)' % n,
                        '-frames:v', '1', '-q:v', '2', os.path.join(OUT, 'stills', 'still_%04.1fs.jpg' % t)], check=True)


def export_proposals():
    os.makedirs(SECT, exist_ok=True)
    props = json.load(open(os.path.join(CACHE, 'proposals.json')))
    jdump(props, os.path.join(SECT, 'proposals.json'))
    import render, pieces
    corr = [
        dict(id='c1', piece='dog lying body', src='dog', frame=4, op='sub', polygon=render.LEGS[4],
             why='legs: no source frame shows this dog lying or its legs folded; the region is not made, and on stage it is behind the porch board'),
        dict(id='c2', piece='dog tail', src='dog', frame=19, op='keep', polygon=render.TAIL6, mirror=True,
             why='tail part box; frame 19 holds the tail clear of the body. Mirrored so it lies back from a right-facing body'),
        dict(id='c3', piece='dog heads', src='dog', frames=[40, 44, 47], op='keep', rule='neck half-plane (5 px behind the neck prompt) AND disk around nose/neck prompts',
             why='head part proposals substituted on the lying body at the neck prompt point'),
        dict(id='c4', piece='every dog piece', src='dog', op='adjudicate', rule='1 px choke; keep largest 4-connected component',
             why='SAM debris on gravel next to the dog (e.g. frames 12, 13, 15 tail region)'),
        dict(id='c5', piece='hand', src='hand', frames=[20, 30], op='add', rule='box (270,62)-(384,116), luminance > 0.42, largest component',
             why='the "a hand." proposal stops at the wrist; the forearm is in the frame'),
        dict(id='c6', piece='sitter', src='sitter', frame=36, op='sub', polygon=[(272, 0), (384, 0), (384, 256), (272, 256)], why='empty bag spread'),
        dict(id='c7', piece='person', src='door', frame=2, op='close', rule='dilate 5 / erode 5', why='pale hair clip left a hole in the silhouette'),
        dict(id='c8', piece='person', src='door', frame=2, op='fade', rule='alpha fades over the lowest 22% of the proposal',
             why='the source frame cuts the person at mid-thigh; the legs are not made, they stay in the dark of the doorway'),
    ]
    jdump(dict(note='correction strokes, in source coordinates; every one changes a model mask and says why', strokes=corr),
          os.path.join(SECT, 'corrections.json'))
    refusals = [
        dict(part='legs of the lying dog', evidence='none of the 50 frames shows the dog lying', decision='not made; the body (f04) is lowered behind the porch board'),
        dict(part='rear view straight from behind', evidence='nearest are f00-f02 (rear three-quarter, head up, back of the head dark)',
             decision='the refusal holds on f00-f02 instead of a constructed rear view'),
        dict(part='dog lying during the refusal (score lie=1 at 5-7 s)', evidence='no lying frame', decision='the dog stays standing with its back turned'),
        dict(part='ears and tail acting (score ear/tail/wag)', evidence='not separable at 384x288', decision='only what each chosen proposal shows'),
        dict(part="person's legs and face", evidence='Straight Talk frames show her from behind and cut at mid-thigh', decision='silhouette that fades into the dark doorway'),
        dict(part='head over the shoulder at 7.46', evidence='f26-f36: the head turns right (toward the door) while the body still faces the camera',
             decision='the turn back is played forward through f17-f40 so the head leads; no composite head'),
    ]
    jdump(refusals, os.path.join(SECT, 'refusals.json'))
    used = film.used_dog_frames()
    jdump([dict(frame=f, mirrored=bool(m), parts=sorted(p)) for (f, m), p in sorted(used.items())], os.path.join(SECT, 'accepted_used.json'))
    shutil.copy(os.path.join(CACHE, 'end_card.jpg'), os.path.join(SECT, 'contact_sheet.jpg'))


def assets():
    S = SOURCES
    used = film.used_dog_frames()
    A = []
    for (f, m), parts in sorted(used.items()):
        A.append(dict(asset='dog#1 f%02d%s' % (f, ' mirrored' if m else ''), what='mask proposal of the dog (%s)' % ','.join(sorted(parts)),
                      file='paeleo/handmade/kit/archive-dog/frames/f%03d.jpg + masks.json["%d"]' % (f, f), source_title=S['dog']['title'],
                      collection=S['dog']['collection'], archive_url=S['dog']['archive'], shot_url=S['dog']['shot'], rights='public_domain',
                      operation='SAM 2.1 proposal (Grounding DINO box) -> adjudicated (confidence proxy, debris removal) -> cut%s -> exposure-matched, '
                                'cool/warm graded -> scaled 1.65' % (' -> mirrored' if m else '')))
    A += [
        dict(asset='door#5 f31', what='door leaf (swings open at 6.2 s)', file='/home/user/hartswf0/secondhand-motion/shots/door-sam/frames/f031.jpg (= kit/archive-door)',
             source_title='Straight Talk', collection='NTIS', archive_url='see paeleo/handmade/kit/archive-door/source.json', rights='public_domain',
             operation='SAM 2.1 proposal -> cut -> warm grade -> scaled, horizontally foreshortened by the door angle'),
        dict(asset='person#1 f02', what='standing person (silhouette in the doorway)', file='/home/user/hartswf0/secondhand-motion/shots/door-sam/frames/f002.jpg',
             source_title='Straight Talk', collection='NTIS', rights='public_domain',
             operation='our proposal: box (185,10)-(330,288) + positive/negative points, HSV colour growth, largest component, holes filled, closing; filled dark'),
        dict(asset='hand#1 f20', what='the reaching arm (silhouette), 3.4-4.6 s', file='/home/user/hartswf0/secondhand-motion/shots/hand-sam/frames/f020.jpg',
             source_title='Door to Heaven, The (1941)', archive_url='https://archive.org/details/DoortoHe1941', rights='public_domain',
             operation='SAM 2.1 hand proposal + forearm correction stroke -> filled dark -> stretched and rotated with the reach'),
        dict(asset='hand#1 f30', what='the hand offered low, from 6.8 s', file='/home/user/hartswf0/secondhand-motion/shots/hand-sam/frames/f030.jpg',
             source_title='Door to Heaven, The (1941)', archive_url='https://archive.org/details/DoortoHe1941', rights='public_domain',
             operation='SAM 2.1 hand proposal + forearm correction stroke -> lamp-warm grade'),
        dict(asset='sitter#1 f36', what='the person sitting beside the door', file='/home/user/hartswf0/secondhand-motion/shots/sleeping-bag-sam/frames/f036.jpg',
             source_title='Survival Stresses', collection='found-frames.json', rights='public_domain',
             operation='SAM 2.1 proposal -> correction (bag spread removed) -> colour kept, lamp-warmed -> scaled'),
        dict(asset='world', what='sky, tree line, porch rail, porch board and lattice, wall section, room, lamp light, light from the door',
             rights='ours (computed in build/render.py)', operation='synthesized with numpy'),
        dict(asset='voice', what='"Come here." x2, "It\'s all right." x2, "Come in."', rights='ours (synthesized)', operation='ffmpeg flite filter, voice slt'),
        dict(asset='sound', what='room tone, crickets, door creak and latch, paw ticks, body settling, exhale, end tone', rights='ours (synthesized)',
             operation='numpy (build/sound.py)'),
        dict(asset='fonts', what='Big Shoulders Display, JetBrains Mono (cards only)', file='tools/paeleo/fonts/', rights='SIL Open Font License', operation='text'),
    ]
    jdump(dict(assets=A), os.path.join(OUT, 'assets.json'))


if __name__ == '__main__':
    mux(); stills(); export_proposals(); assets()
