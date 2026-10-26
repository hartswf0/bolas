"""ACTION EDITOR, words: the spoken lines (from the score's voice timeline) and the moments shown in the end card's path.
python3 build/cues.py -> build/cache/cues.json"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
SC = json.load(open(os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')))
TEXT = {'call': ['Come here.', 'Come here.'], 'soft': ["It's all right.", "It's all right.", 'Come in.']}
lines, cur = [], None
for t, ev in SC['timeline']:
    if 'voice' not in ev: continue
    if cur: lines.append([cur[0], t, cur[1]]); cur = None
    if ev['voice'] != 'none': cur = (t, ev['voice'])
used = {'call': 0, 'soft': 0}
out = []
for a, b, kind in lines:
    out.append([a, b, TEXT[kind][used[kind]], kind]); used[kind] += 1
keys = [int(round(s * 24)) for s in (0.3, 1.6, 3.6, 3.75, 5.0, 7.5, 7.8, 8.15, 12.0, 18.0, 24.6, 27.0, 30.5)]
json.dump({'lines': out, 'end_keys': keys}, open(os.path.join(HERE, 'cache', 'cues.json'), 'w'))
print(out)
