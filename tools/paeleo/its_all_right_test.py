#!/usr/bin/env python3
"""Writes paeleo/its-all-right/media/test.json: the finale test of IT'S ALL RIGHT, read from each telling's own
invariants.json (the four PAELEO invariants, measured from its render) and reviews/ (the independent critic rounds)."""
import json, os, re

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HAND = os.path.join(REPO, 'paeleo', 'handmade')
OUT = os.path.join(REPO, 'paeleo', 'its-all-right', 'media', 'test.json')
INV = [('I1_choices', 'the six choices land on the score'), ('I2_threshold', 'the dog reaches the sill'),
       ('I3_direction', 'it moves the way the score moves'), ('I4_refusal', 'it turns its back on the order')]


def rounds(d):
    rv = os.path.join(d, 'reviews')
    if not os.path.isdir(rv): return []
    out = []
    for f in sorted(os.listdir(rv), key=lambda s: int(re.sub(r'\D', '', s) or 0)):
        if not f.endswith('.md'): continue
        head = open(os.path.join(rv, f)).readline().strip().lstrip('# ')
        v = 'pass' if re.search(r'·\s*PASS', head) else 'fail'
        out.append({'round': int(re.sub(r'\D', '', f) or 0), 'verdict': v, 'narrow': 'narrow' in head.lower(), 'head': head})
    return out


def main():
    hm = json.load(open(os.path.join(REPO, 'tools', 'paeleo', 'handmade.json')))['swarms']
    rows = []
    for s in hm:
        d = os.path.join(HAND, s['dir'])
        inv = {}
        p = os.path.join(d, 'invariants.json')
        if os.path.exists(p):
            j = json.load(open(p))
            inv = {k: bool(j.get(k, {}).get('ok')) for k, _ in INV}
        r = rounds(d)
        rows.append({'id': s['id'], 'name': s['name'], 'kind': s['kind'], 'invariants': inv, 'rounds': len(r),
                     'final': r[-1]['verdict'] if r else None, 'narrow': r[-1]['narrow'] if r else False,
                     'status': s.get('status', ''), 'review': f'../handmade/{s["dir"]}/reviews/'})
    json.dump({'invariants': [{'key': k, 'label': l} for k, l in INV], 'tellings': rows}, open(OUT, 'w'), indent=1, ensure_ascii=False)
    print(OUT, len(rows), sum(1 for r in rows if r['final'] == 'pass'), 'pass')


if __name__ == '__main__':
    main()
