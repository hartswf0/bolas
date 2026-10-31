"""SCION 40 · writes assets.json: every asset in film.mp4, its source, rights and the operation that made it."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

CARDS = json.load(open(os.path.join(DATA, 'cards.json')))


def main():
    A = []
    hand = json.load(open(os.path.join(os.path.dirname(HAND_SRC), 'hand', 'source.json')))['source']
    A.append(dict(id='archive-hands', what='the performers\' hands in the capture plate (inset and title card only; never in the replayed scene)',
                  source=HAND_SRC + '/frames f000-f061 + masks.json', source_title=hand['source_title'] + ' (' + str(hand.get('source_year', '')) + ')',
                  archive_url=hand['original_source_url'], clip_page=hand['shot_page_url'], rights='public domain (' + hand['rights_statement'] + ', kit found-frames.json)',
                  operation='SAM 2.1 hand mask per frame; forearm traced column by column as the bright run continuous with the wrist; arm extended beyond the frame edge by repeating its last columns along its slope; tinted warm; scaled 1.5x, rotated and placed with fingertips on each puppet tab (build/hands.py, build/plate.py); mirrored for the two left hands'))
    dogb = [n for n, m in CARDS.items() if m['kind'] == 'dog_body']
    dogh = [n for n, m in CARDS.items() if m['kind'] == 'dog_head']
    A.append(dict(id='dog-body-cards', what='%d paper body cards of the dog (stand, 8 walk-low, 8 back-away crouched, 8 upright steps, 3+3 turn views, settle and lie, facing both ways)' % len(dogb),
                  cards=dogb, source='drawn here (build/cards.py)', rights='made for this film (SCION 40); no source material',
                  operation='silhouettes drawn from a small geometric guide (ellipsoids and limbs posed per card, orthographic view at a fixed yaw) only to keep the views consistent; each card cut once as flat paper (scissor-wobble edge, grain, marker line); cut twice: plate style (white card + fiducial tab) and skin style (ochre paper, dark saddle)'))
    A.append(dict(id='dog-head-cards', what='%d paper head cards (profile both ways, ears up/back/flat, rear and front views, the back-of-head look-in card)' % len(dogh),
                  cards=dogh, source='drawn here (build/cards.py)', rights='made for this film', operation='as the body cards; pinned at the neck by the contact constraint in the replay'))
    A.append(dict(id='person-cards', what='7 paper cards of the person (stand, call, reach, step, going down, sit, sit with a low hand)', source='drawn here (build/cards.py)', rights='made for this film',
                  operation='capsule shapes cut as paper; drawn face, not a real person'))
    A.append(dict(id='door-and-light', what='3 door-leaf cards (ajar, mid, open) and a yellow tissue light piece', source='drawn here', rights='made for this film', operation='cut paper; the light is slid out through the doorway by a hand; the room\'s lit/dark mix follows that recovered slide'))
    A.append(dict(id='layout-sheet', what='the layout sheet on the table: pencil floor line, wall, doorway, metre ruler, 4 corner fiducials', source='drawn here (build/set.py)', rights='made for this film', operation='drawn; synthesized onto a procedural wood table under a synthesized overhead camera (homography, lamp falloff, blur, noise, JPEG)'))
    A.append(dict(id='finished-set', what='torn-paper dusk sky, moon, hills, fence, porch boards and steps, cut-away house and room (lamp, table, picture), dark and lit versions', source='drawn here (build/set.py)', rights='made for this film', operation='procedural torn and cut paper with grain and lifted shadows'))
    A.append(dict(id='fiducials', what='8-bit-id square markers (7 id bits, complement, parity, orientation cells)', source='designed here (build/common.py)', rights='made for this film', operation='printed on each plate card tab and the sheet corners; decoded by build/track.py'))
    A.append(dict(id='sound', what='voice (Come here x2, It\'s all right x2, Come in), paper foley driven by the recovered event stream, room tone, crickets', source='synthesized here (build/sound.py, numpy formant synthesis)', rights='made for this film', operation='synthesized; no recorded audio used'))
    A.append(dict(id='fonts', what='Big Shoulders Display, JetBrains Mono, Literata', source='tools/paeleo/fonts', rights='SIL Open Font License (repo fonts)', operation='title and end cards, inset caption'))
    A.append(dict(id='score', what='the dog\'s decision trace', source='paeleo/handmade/score/threshold-score.json', rights='PAELEO project', operation='read to write the performers\' sheet (perform.py) and to check the invariants'))
    json.dump(dict(about='SCION 40 · Physical Tabletop Capture: every asset in film.mp4. Nothing from the web; no generated images from models; no faces.', assets=A),
              open(os.path.join(F, 'assets.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
