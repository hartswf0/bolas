#!/usr/bin/env python3
"""Build registry/films.js: every film in the Crank Boy and in Bolas, for films.html.
python3 registry/build_films.py <bolas checkout>
Reads: registry/registry.js (shorts, town, versions, lab), registry/works.json (which films belong together), <bolas>/catalog.json (the 26 Bolas films), the films in
assets/shorts/films/. Copies each Bolas film's thumbnail into assets/films/thumbs/ so the page works without the network.
Bolas films themselves are not copied (595 MB): films.html streams them from Bolas, from ../media/films/ when this site is
mirrored inside Bolas and from the published site otherwise.
Writes: registry/films.js  (window.CRANK_FILMS = {updated, bolas, groups, films}). Run after adding any film."""
import json, os, shutil, subprocess, sys, datetime
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bolas = sys.argv[1] if len(sys.argv) > 1 else '/home/user/bolas'
src = open(os.path.join(root, 'registry/registry.js'), encoding='utf-8').read()
R = json.loads(src[src.index('{'):src.rindex('}') + 1])
cat = json.load(open(os.path.join(bolas, 'catalog.json'), encoding='utf-8'))
os.makedirs(os.path.join(root, 'assets/films/thumbs'), exist_ok=True)

def probe(p):
    try:
        d = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p], capture_output=True, text=True).stdout)
    except Exception:
        d = 0.
    return round(d, 1), round(os.path.getsize(p) / 1e6, 1)

GROUPS = [
    {'id': 'crankboy', 'title': 'The Crank Boy', 'line': 'The opening film for the album of seven versions.'},
    {'id': 'futuretown', 'title': 'Futuretown', 'line': 'The seven cards brought to life, the Town they make together, and the proof scenes.'},
    {'id': 'family', 'title': 'The Crash-Test Family', 'line': 'Bola, Shim and little Dot in a measured bay, from the first pencil test to the full crash lab.', 'path': 'family/', 'bolas': True},
    {'id': 'cineosis', 'title': 'CINEOSIS', 'line': 'The family performs the 45 signs of Deleuze\'s cinema books, in a measured bay and inside real archive film.', 'path': 'cineosis/', 'bolas': True},
    {'id': 'odyssey', 'title': 'The Found Odyssey', 'line': 'Homer\'s lines answered by archive speech, with a drawn cast acting in graded archive plates.', 'path': 'found-odyssey/', 'bolas': True},
    {'id': 'wygwyl', 'title': 'WYGWYL', 'line': 'The poet as a jointed paper cut-out, set over the cineosis-lab cel cuts.', 'path': 'wygwyl/', 'bolas': True},
    {'id': 'elsewhere', 'title': 'Elsewhere', 'line': 'Related films that live in other places.'}]
films = []

# ---- The Crank Boy: the live opening film and the games played by a script
films.append({'id': 'opening', 'group': 'crankboy', 'kind': 'live', 'title': 'The Crank Boy · the opening film', 'date': '2026-10-23', 'dur': 105, 'mb': None,
              'line': 'Crank Boy turns a hand-cranked projector, and the screen shows the 1910 cards, the programs that built games from them, the three theories behind their instructions and the lab\'s other films. Drawn live in the browser, with recorded voices.',
              'thumb': 'assets/films/opening.jpg', 'open': 'index.html#film', 'links': [{'label': 'The album', 'href': 'index.html'}, {'label': 'The voices', 'href': 'assets/film/script.json'}], 'tags': ['live', 'voices']})
for v in R['versions']:
    if v.get('film'):
        d, mb = probe(os.path.join(root, v['film']))
        films.append({'id': v['id'] + '-played', 'group': 'futuretown', 'card': 'school', 'kind': 'game', 'title': f"Version {v['tag']} · {v['title']}, played", 'date': v['date'], 'dur': d, 'mb': mb,
                      'line': v['line'], 'thumb': v['film'].replace('.mp4', '.jpg'), 'src': {'local': v['film']},
                      'links': [{'label': 'Play it', 'href': v['play']}, {'label': 'How it was made', 'href': v['making']}], 'tags': ['game', 'plates'],
                      'made': {'op': 'Layers cut from clean plates', 'steps': [
                          'Took the five aligned At School plates and verified the alignment (best shift 0, 0 px).',
                          'Cut each layer by plate difference and by outline: the whole class, the lectern, the machine.',
                          'Built the game on the layers and recorded it played by a script.'],
                          'learned': 'Clean plates turn a postcard into a stage: the layers come out by subtraction, not by guessing.'}})

# ---- Futuretown: the shorts, the Town, the proofs
for s in R['shorts']:
    d, mb = probe(os.path.join(root, s['film']))
    films.append({'id': s['id'], 'group': 'futuretown', 'kind': 'short', 'title': s['title'], 'date': '2026-10-24', 'dur': d, 'mb': mb, 'line': s['line'],
                  'thumb': s['poster'], 'src': {'local': s['film']}, 'card': s['id'], 'op': s['operator'], 'plates': s['plates'],
                  'links': [{'label': 'The game', 'href': s['game']['link']}, {'label': 'How it was made', 'href': 'shorts/index.html#' + s['id']}, {'label': 'The composition', 'href': s['page']}],
                  'tags': ['archive'] + [s['operator'].split(',')[0].split(' ')[0].lower()],
                  'made': {'op': s['operator'], 'game': s['game']['op'], 'steps': s['process'], 'critic': s['critic'], 'learned': s['learned'], 'plates': s['plates']}})
T = R['town']
d, mb = probe(os.path.join(root, T['film']))
films.append({'id': 'town', 'group': 'futuretown', 'kind': 'cartoon', 'title': 'The Town', 'date': '2026-10-24', 'dur': d, 'mb': mb, 'line': T['line'], 'thumb': T['poster'], 'src': {'local': T['film']},
              'links': [{'label': 'Play the Town', 'href': T['page']}, {'label': 'The method', 'href': 'docs/prompts/town.md'}], 'tags': ['town', 'doodles'],
              'made': {'op': 'One world: a drawn power line from the crank, recastable handle-holders', 'steps': [
                  'Put the seven cards in a row under one power line drawn the Secondhand Motion way, with real Quick, Draw! doodles over them.',
                  'Made nothing run unless the crank in the school turns, with power reaching each card later the farther it is from the boy.',
                  'Gave each card a game with an operator its short did not use; all seven passed a headless play test with real inputs.',
                  'Cut the crank boy, the maid and the barber\'s lever man into performing upper bodies and planted legs so any can stand in another\'s place.',
                  'Stepped the same engine from a fixed script and rendered it frame by frame with a synthesised soundtrack.'],
                  'learned': 'A cast can be replaced without remaking the performance, if the performance is a function of the actor\'s height only.'}})
for p in T.get('proofs', []):
    d, mb = probe(os.path.join(root, p['film']))
    films.append({'id': 'proof-' + p['card'], 'group': 'futuretown', 'kind': 'proof', 'title': p['title'] + ' · proof scene', 'date': '2026-10-24', 'dur': d, 'mb': mb,
                  'line': 'The first call sheet of the art department made real: ' + p['aesthetic'] + '. A fixed camera, stop-substitutions, and the stars of The Eclipse (1907) re-printed in the card\'s own inks.',
                  'thumb': p['poster'], 'src': {'local': p['film']}, 'card': p['card'],
                  'links': [{'label': 'The composition', 'href': p['page']}, {'label': 'The call sheets', 'href': 'shorts/requests.html#' + p['card']}], 'tags': ['art department', 'archive'],
                  'made': {'op': 'Méliès\'s trick-film grammar', 'steps': [
                      'Fixed the camera and stood the card on a stage behind a proscenium, with curtains and footlights.',
                      'Turned the wall and window into the falling stars of The Eclipse (Méliès, 1907), re-printed live in the card\'s own darkest inks, keyed out by the card\'s wall and glass colours.',
                      'Made the teacher\'s book come out of the machine as a moon drawn from two Quick, Draw! records, and turn back into a book on his desk.',
                      'Ran the story\'s clock as fast as the boy cranks, shown at 16 frames a second with gate weave, flicker, scratches and dust.'],
                      'learned': 'An archive frame from the card\'s own decade, re-printed in the card\'s inks, can replace a surface of the card without reading as a seam. Not yet blind-reviewed.'}})

# ---- Bolas
PROC = {'bolas-videotext': 'pencil-test', 'the-physical': 'the-physical', 'crash-lab-film': 'crash-lab', 'cineosis-crash-lab': 'cineosis-crash-lab', 'cineosis-hybrid-pilot': 'hybrid-pilot',
        'cineosis-hybrid-atlas': 'hybrid-atlas', 'cineosis-handmade-film': 'handmade', 'cineosis-handmade-batch1': 'handmade', 'cineosis-handmade-signs1-8': 'handmade',
        'cineosis-handmade-signs13-41': 'handmade', 'cineosis-hand-butter': 'hand-butter', 'found-odyssey-drawn-tests': 'fo-tests', 'found-odyssey-style-lab': 'fo-tests',
        'found-odyssey-drawn-v2': 'fo-tests', 'ep2-draft-opening': 'fo-tests', 'wygwyl-poem07-paper-poet': 'wygwyl', 'wygwyl-poet-paper-proof': 'wygwyl',
        'wygwyl-celstyle-proof': 'wygwyl', 'wygwyl-inkcel-P05-008': 'wygwyl'}
for i in range(1, 8):
    for f in cat['films']:
        if f['id'].startswith(f'ep{i}-') and 'draft' not in f['id']:
            PROC[f['id']] = f'fo-ep{i}'
PROG = {p['id']: p for p in cat['programs']}
CHAR = {c['id']: c['name'] for c in cat['characters']}
for f in cat['films']:
    th = os.path.join(bolas, f['thumb'])
    dst = os.path.join(root, 'assets/films/thumbs', f['id'] + '.jpg')
    if os.path.exists(th):
        shutil.copyfile(th, dst)
    kind = f.get('kind', 'film')
    prog = f['program']
    links = [{'label': 'Film page in Bolas', 'bolas': f'films/{f["id"]}/'}]
    if f.get('notes'):
        links.append({'label': 'Notes', 'bolas': 'docs/notes/' + f['notes'].replace('.md', '.html')})
    if f['id'] in PROC:
        links.append({'label': 'How it was made', 'bolas': f'process/{PROC[f["id"]]}/'})
    links.append({'label': PROG[prog]['title'], 'bolas': PROG[prog]['path']})
    films.append({'id': f['id'], 'group': prog, 'kind': kind, 'title': f['title'], 'date': f['date'], 'dur': round(f['dur'], 1), 'mb': f['mb'], 'line': f['line'],
                  'thumb': 'assets/films/thumbs/' + f['id'] + '.jpg', 'src': {'bolas': f['file']}, 'cast': [CHAR.get(c, c) for c in f.get('chars', [])], 'links': links, 'tags': []})

# ---- elsewhere
for e in [
    {'id': 'wygwyl-cuts', 'title': 'WYGWYL · four cuts', 'line': 'A 24-minute poem suite cut four ways from archive footage, one shot per beat, no shot repeated: Suite, Scenes, Cineosis and Drift. Streams from the cineosis-lab release.', 'href': 'https://hartswf0.github.io/cineosis-lab/lab/wygwyl.html', 'label': 'cineosis-lab'},
    {'id': 'cineosis-reel', 'title': 'The cineosis reel', 'line': 'Ten minutes: every sign as a title card with its deciding test, then its strongest shots.', 'href': 'https://github.com/hartswf0/cineosis-lab/releases/tag/v0.1', 'label': 'cineosis-lab release'},
    {'id': 'secondhand-motion', 'title': 'Secondhand Motion · moving drawings', 'line': 'Archive shots watched as moving Quick, Draw! cartoons: 41 integrated clips beside their footage. The doodle layer in the Town comes from this project.', 'href': 'https://hartswf0.github.io/secondhand-motion/shots/moving-drawings.html', 'label': 'secondhand-motion'}]:
    films.append({'id': e['id'], 'group': 'elsewhere', 'kind': 'external', 'title': e['title'], 'date': None, 'dur': None, 'mb': None, 'line': e['line'], 'thumb': None, 'external': e['href'], 'links': [{'label': 'Open at ' + e['label'], 'href': e['href']}], 'tags': []})
for f in R['lab'].get('films', []):
    if f.get('video'):
        continue
    if any(x.get('external') == f['url'] for x in films):
        continue
    films.append({'id': 'x-' + ''.join(c for c in f['title'].lower() if c.isalnum())[:24], 'group': 'elsewhere', 'kind': 'external', 'title': f['title'], 'date': None, 'dur': None, 'mb': None, 'line': f['what'], 'thumb': None, 'external': f['url'], 'links': [{'label': 'Open', 'href': f['url']}], 'tags': []})

# ---- works: films that belong together (registry/works.json)
W = json.load(open(os.path.join(root, 'registry/works.json'), encoding='utf-8'))
by = {f['id']: f for f in films}
for w in W['works']:
    for i, m in enumerate(w['members']):
        f = by.get(m['film'])
        assert f, f"works.json: unknown film {m['film']} in {w['id']}"
        assert 'work' not in f, f"film {f['id']} is in two works"
        f.update({'work': w['id'], 'role': m['role'], 'step': i + 1, 'of': len(w['members']), 'how': m['note']})
works = [{'id': w['id'], 'group': w['group'], 'title': w['title'], 'line': w['line'], 'members': [m['film'] for m in w['members']]} for w in W['works']]

ids = [f['id'] for f in films]
assert len(ids) == len(set(ids)), 'duplicate film id'
out = {'updated': datetime.date.today().isoformat(), 'bolas': 'https://hartswf0.github.io/bolas/', 'groups': GROUPS, 'works': works, 'relations': W.get('relations', []), 'films': films}
open(os.path.join(root, 'registry/films.js'), 'w', encoding='utf-8').write('window.CRANK_FILMS = ' + json.dumps(out, indent=1, ensure_ascii=False) + ';\n')
tot = sum(f['dur'] or 0 for f in films)
print(f'{len(films)} films, {tot / 3600:.1f} h; thumbs in assets/films/thumbs: {len(os.listdir(os.path.join(root, "assets/films/thumbs")))}')
