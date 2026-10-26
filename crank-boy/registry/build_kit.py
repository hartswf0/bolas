#!/usr/bin/env python3
"""Build registry/kit.js: every element of the Futuretown and version 9 kits, for kit.html.
python3 registry/build_kit.py
Reads: registry/registry.js, shorts/plates.json, shorts/parts/<card>.json (the cut outlines), assets/shorts/parts/<card>/ (cut pieces,
parts.json, inks.json, clean.jpg, empty.jpg), assets/shorts/doodles.json, assets/v9/ (aligned plates, layers, cast), docs/operators/,
and the first docstring or comment of every tool. Writes registry/kit.js (window.CRANK_KIT). Run after changing any of them."""
import glob, json, os, re
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda p: json.load(open(os.path.join(root, p), encoding='utf-8'))
src = open(os.path.join(root, 'registry/registry.js'), encoding='utf-8').read()
R = json.loads(src[src.index('{'):src.rindex('}') + 1])
exists = lambda p: os.path.exists(os.path.join(root, p))
from PIL import Image

def size(p):
    try:
        return list(Image.open(os.path.join(root, p)).size)
    except Exception:
        return None

cards = []
for s in R['series']:
    cid = s['id']; base = f'assets/shorts/parts/{cid}/'
    if not exists(base + 'parts.json'):
        continue
    m = J(base + 'parts.json')
    spec = J(f'shorts/parts/{cid}.json') if exists(f'shorts/parts/{cid}.json') else {'parts': []}
    sp = {p['name']: p for p in spec['parts']}
    parts = [{'name': k, 'file': base + k + '.png', 'w': v['w'], 'h': v['h'], 'x': v['x'], 'y': v['y'], 'pivot': v['pivot'],
              'slot': bool(sp.get(k, {}).get('slot')), 'matte': sp.get(k, {}).get('matte', '')} for k, v in m['parts'].items()]
    sh = next((x for x in R['shorts'] if x['id'] == cid), {})
    cards.append({'id': cid, 'title': s['title'], 'image': s['image'], 'size': m['size'], 'clean': base + 'clean.jpg', 'empty': base + 'empty.jpg' if exists(base + 'empty.jpg') else None,
                  'inks': J(base + 'inks.json') if exists(base + 'inks.json') else [], 'parts': parts, 'holes': len(spec.get('holes', [])),
                  'film': sh.get('operator', ''), 'game': (sh.get('game') or {}).get('op', ''), 'plates': sh.get('plates', [])})

P = J('shorts/plates.json')
plates = []
for p in P['plates']:
    n = p['name']
    plates.append({'name': n, 'clip': p['clip'], 'title': p['title'], 'year': p['year'], 'in': p['in'], 'out': p['out'], 'shows': p['shows'], 'short': p.get('short', ''),
                   'video': f'assets/shorts/plates/{n}.mp4', 'strip': f'assets/shorts/plates/{n}.jpg', 'motion': exists(f'assets/shorts/plates/{n}.motion.json')})

D = J('assets/shorts/doodles.json')
doodles = [{'word': w, 'key_id': d['key_id'], 'country': d.get('countrycode'), 'drawing': d['drawing']} for w, d in sorted(D['doodles'].items())]

v9 = {'plates': [{'file': 'assets/v9/src/' + f, 'name': f.replace('.jpg', '').replace('plate-', '')} for f in sorted(os.listdir(os.path.join(root, 'assets/v9/src')))],
      'layers': [{'file': 'assets/v9/' + f, 'name': f.replace('.png', ''), 'size': size('assets/v9/' + f)} for f in ('machine.png', 'lectern.png', 'lectern_front.png', 'tables_front.png', 'tables_back.png')],
      'cast': [{'file': 'assets/v9/cast/' + f, 'name': f.replace('.png', ''), 'size': size('assets/v9/cast/' + f)} for f in sorted(os.listdir(os.path.join(root, 'assets/v9/cast'))) if f.endswith('.png') and not f.endswith('_rig.png')],
      'rigs': len([f for f in os.listdir(os.path.join(root, 'assets/v9/cast')) if f.endswith('_rig.png')])}

ops = []
for l in R['library']:
    if l['file'].startswith('docs/operators/'):
        first = open(os.path.join(root, l['file']), encoding='utf-8').read().splitlines()
        title = next((x.lstrip('# ').strip() for x in first if x.startswith('# ')), l['title'])
        ops.append({'key': l['key'], 'title': l['title'], 'file': l['file'], 'note': l['note'], 'heading': title, 'chars': os.path.getsize(os.path.join(root, l['file']))})
for o in ops:
    nm = o['file'].split('/')[-1].replace('.md', '')
    o['filmFor'] = [s['title'] for s in R['shorts'] if s['doc'].endswith(nm + '.md')]
    o['gameFor'] = [s['title'] for s in R['shorts'] if s['game']['doc'].endswith(nm + '.md')]

def doc(path):
    t = open(os.path.join(root, path), encoding='utf-8').read()
    m = re.search(r'^(?:#!.*\n)?(?:"""|\'\'\')(.*?)(?:"""|\'\'\')', t, re.S) or re.search(r'^(?:#!.*\n)?/\*(.*?)\*/', t, re.S)
    if m:
        txt = m.group(1).strip()
    else:
        txt = ' '.join(l.lstrip('/# ').strip() for l in t.splitlines()[:4] if l.strip().startswith(('//', '#')) and not l.startswith('#!'))
    t1 = re.sub(r'\s+', ' ', txt.split('\n\n')[0]).strip()
    t1 = re.split(r'\s(?:python3|node)\s|\sReads?:|\sWrites?:', t1)[0].strip()
    return t1[:260]
tools = []
for pth, what in [('shorts/tools/cut.py', 'Cut'), ('shorts/tools/plates.py', 'Archive'), ('shorts/tools/stencil.py', 'Archive'), ('shorts/tools/inks.py', 'Archive'), ('shorts/tools/motion.py', 'Archive'),
                  ('assets/v9/build_layers.py', 'Cut'), ('shorts/stage.js', 'Compose'), ('shorts/world.js', 'Compose'), ('shorts/tools/sound.py', 'Render'), ('shorts/tools/render.mjs', 'Render'),
                  ('shorts/tools/to_bolas.py', 'Publish'), ('registry/build_films.py', 'Publish'), ('registry/build_kit.py', 'Publish'), ('registry/build_library.py', 'Publish'), ('registry/check.js', 'Publish'), ('registry/links.mjs', 'Publish')]:
    if exists(pth):
        tools.append({'file': pth, 'stage': what, 'what': doc(pth)})

prompts = [{'title': l['title'], 'file': l['file'], 'key': l['key']} for l in R['library'] if l['key'] in ('shorts', 'town', 'art', 'futuretown')]
out = {'cards': cards, 'plates': plates, 'doodles': doodles, 'doodleSource': D['about'], 'v9': v9, 'operators': ops, 'tools': tools, 'prompts': prompts}
open(os.path.join(root, 'registry/kit.js'), 'w', encoding='utf-8').write('window.CRANK_KIT = ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';\n')
print(len(cards), 'cards,', sum(len(c['parts']) for c in cards), 'parts,', len(plates), 'plates,', len(doodles), 'doodles,', len(v9['cast']), 'cast,', len(ops), 'operators,', len(tools), 'tools')
