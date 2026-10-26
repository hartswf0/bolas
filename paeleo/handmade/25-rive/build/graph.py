# draw the state graph from puppet.json as an SVG (proof/state-graph.svg)
import json, os, math
B = os.path.dirname(os.path.abspath(__file__)); P = json.load(open(os.path.join(B, 'puppet.json')))
L = P['stateMachine']['layers']; W, H = 1100, 260 * len(L) + 40; o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="monospace" font-size="13"><rect width="100%" height="100%" fill="#15121a"/>',
 '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#e8c48c"/></marker></defs>']
for k, lay in enumerate(L):
    y0 = 40 + k * 260; st = list(lay['states']); n = len(st); pos = {s: (120 + j * (860 / max(1, n - 1)), y0 + 110) for j, s in enumerate(st)}
    o.append(f'<text x="20" y="{y0}" fill="#efe6da" font-size="16">layer {lay["name"]} (entry {lay["entry"]})</text>')
    for j, t in enumerate(lay['transitions']):
        srcs = st if t['from'] == '*' else [t['from']]
        for s in srcs:
            if s == t['to']: continue
            (x1, y1), (x2, y2) = pos[s], pos[t['to']]; bend = 60 if x2 > x1 else -60
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - bend
            o.append(f'<path d="M{x1},{y1 - 18} Q{mx},{my} {x2},{y2 - 18}" fill="none" stroke="#e8c48c" stroke-opacity=".7" marker-end="url(#a)"/>')
            if s == srcs[0]:
                cond = ' & '.join(' '.join(map(str, c)) for c in t['when']); o.append(f'<text x="{mx - 70}" y="{my + (12 if bend < 0 else -4)}" fill="#a99fb3" font-size="11">p{t["priority"]} {cond}{" (any)" if t["from"] == "*" else ""}</text>')
    for s, (x, y) in pos.items():
        o.append(f'<rect x="{x - 62}" y="{y - 18}" width="124" height="36" rx="8" fill="#2a2431" stroke="#efe6da"/><text x="{x}" y="{y + 5}" fill="#efe6da" text-anchor="middle">{s}</text>')
o.append('</svg>'); open(os.path.join(os.path.dirname(B), 'proof/state-graph.svg'), 'w').write('\n'.join(o))
