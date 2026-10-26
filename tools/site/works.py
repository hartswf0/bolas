#!/usr/bin/env python3
"""Films that belong together (tools/site/works.json, copied from crank-boy/registry/works.json).
build.py calls row() for each film page and lede() for each program on films/index.html.
Run `python3 tools/site/works.py` to patch the already-built pages in place (idempotent), for when build.py cannot run."""
import html, json, os, re
H = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(H))
W = json.load(open(os.path.join(H, 'works.json'), encoding='utf-8'))
esc = html.escape
BY = {}
for w in W['works']:
    for i, m in enumerate(w['members']):
        BY[m['film']] = (w, i, m)
CB = 'crank-boy/films.html#w:'

def row(fid, up):
    """one <div> for the film page's facts list: which work this film is part of and how it follows the one before"""
    if fid not in BY: return ''
    w, i, m = BY[fid]
    prev = w['members'][i - 1]['film'] if i else None
    nxt = w['members'][i + 1]['film'] if i + 1 < len(w['members']) else None
    s = f'<a href="{up}{CB}{w["id"]}">{esc(w["title"])}</a> · part {i + 1} of {len(w["members"])}, {esc(m["role"])}'
    s += f'<br><span class="meta">{esc(m["note"])}</span>'
    nav = ' · '.join(x for x in [f'<a href="{up}films/{prev}/">← before</a>' if prev and not prev.startswith(('v9', 'proof', 'school')) else '', f'<a href="{up}films/{nxt}/">next →</a>' if nxt and not nxt.startswith(('v9', 'proof', 'school')) else ''] if x)
    return f'<div class="work"><dt>Part of</dt><dd>{s}{"<br>" + nav if nav else ""}</dd></div>'

def lede(group):
    """one line under a program heading on films/index.html"""
    ws = [w for w in W['works'] if w['group'] == group]
    if not ws: return ''
    return ' '.join(f'{esc(w["title"])}: {len(w["members"])} films in order. {esc(w["line"])}' for w in ws)

if __name__ == '__main__':
    n = 0
    for fid in BY:
        p = os.path.join(ROOT, 'films', fid, 'index.html')
        if not os.path.exists(p): continue
        t = open(p, encoding='utf-8').read()
        t = re.sub(r'<div class="work">.*?</div>(?=<div>|</dl>)', '', t)
        r = row(fid, '../../')
        t2 = t.replace('<dl class="facts">', '<dl class="facts">' + r, 1)
        if t2 != t or r: open(p, 'w', encoding='utf-8').write(t2); n += 1
    p = os.path.join(ROOT, 'films/index.html')
    t = open(p, encoding='utf-8').read()
    t = re.sub(r'<p class="worknote">.*?</p>', '', t)
    for g, title in (('family', 'The Crash-Test Family'), ('cineosis', 'CINEOSIS'), ('odyssey', 'The Found Odyssey'), ('wygwyl', 'WYGWYL')):
        t = t.replace(f'<h2>{esc(title)}</h2></div>', f'<h2>{esc(title)}</h2></div><p class="worknote">{lede(g)}</p>', 1)
    open(p, 'w', encoding='utf-8').write(t)
    print('patched', n, 'film pages and films/index.html')
