"""Same-moment frame grids for the case pages -> media/case/<slug>/cmp/*.jpg + media/case/compare.json"""
import os, json, subprocess
B = '/home/claude/bolas/this-side-up/'; H = '/home/claude/'; RR = H + 'rerender/'
def grab(src, t, out):
    if not os.path.exists(B + out):
        os.makedirs(os.path.dirname(B + out), exist_ok=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.2f}', '-i', src, '-frames:v', '1', '-vf', 'scale=480:-2', '-q:v', '6', B + out], check=True)
    return out
import sys
G = json.load(open(B + 'media/case/compare.json')) if os.path.exists(B + 'media/case/compare.json') else {}
W = sys.argv[1:]
F = H + 'lab/fall/out/tempus_fugit_fall_cut%d.mp4'
if not W or 'fall' in W:
  cuts = [('Cut 1', RR + 'cut1.mp4'), ('Cut 2', RR + 'cut2.mp4'), ('Cut 3', RR + 'cut3.mp4'), ('Cut 4', F % 4), ('Cut 5', F % 5), ('Cut 6', F % 6)]
  T = [3, 12, 20.5, 23.5, 30, 37, 46.5, 50.5, 56, 62, 71]
  G['fall'] = dict(title='Same moment, six cuts', note='Every cut keeps the same 80 s timeline (time stops at 21 s and comes back at 50.5 s), so each column is the same moment of the story. Cuts 1 to 3 are the re-renders.',
                 cols=[f'{t:g} s' for t in T], rows=[dict(label=l, files=[grab(s, t, f'media/case/fall/cmp/c{k + 1}_{t:g}.jpg') for t in T]) for k, (l, s) in enumerate(cuts)])
if not W or 'bullet-time' in W:
  L = H + 'neo/tempus/out/'
  leans = [('1 · cards', 'lean'), ('2 · churn', 'lean_churn'), ('3 · Marble', 'lean_atlas'), ('4 · run 1', 'lean_run1'), ('5 · run 1b', 'lean_run1b'), ('6 · run 2', 'lean_run2')]
  T2 = [1, 3, 5, 7, 9, 10.4]
  G['bullet-time'] = dict(title='Same moment, six leans', note='The lean is 10.6 s in every version, on the same measured camera path, so each column is the same instant.',
                        cols=[f'{t:g} s' for t in T2], rows=[dict(label=l, files=[grab(L + s + '.mp4', t, f'media/case/bullet-time/cmp/{s}_{t:g}.jpg') for t in T2]) for l, s in leans])
if not W or 'trouttown' in W:
  P = H + 'lab/tfu/renders/'
  T3 = [34, 36, 38, 40, 41, 41.8]
  rows = [('v2', P + 'tempus_fugit_passage_v2.mp4', 0), ('v3', P + 'tempus_fugit_passage_v3.mp4', 0), ('v5 tail', P + 'passage_v5_tail_33-42.mp4', 33)]
  G['trouttown'] = dict(title='The release, three versions', note='Passage time in seconds. The v5 render covers only 33 to 42 s. v1 and v4 were not kept as films.',
                      cols=[f'{t:g} s' for t in T3], rows=[dict(label=l, files=[grab(s, t - off, f'media/case/trouttown/cmp/{l.split()[0]}_{t:g}.jpg') for t in T3]) for l, s, off in rows])
json.dump(G, open(B + 'media/case/compare.json', 'w'), indent=0); print('ok')
