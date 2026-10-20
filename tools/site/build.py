"""CRASH LAB site generator. Everything comes from catalog.py (programs, characters, films, lab pages) and process.json
(the process archive). Run after thumbs.py; it moves films into media/films/, writes every page, the sitemap and catalog.json.
    python3 build.py"""
import os, sys, re, json, html, shutil, subprocess, glob, datetime, markdown
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H); import catalog as C
R = '/home/claude/bolas'; HOME = '/home/claude'; S = os.path.dirname(H)
TR = '/root/.claude/projects/-home-claude/6076dc87-a15e-52b2-839b-b8f3e08107ac/tool-results'
PROG = {p['id']: p for p in C.PROGRAMS}; CHAR = {c['id']: c for c in C.CHARACTERS}; FILM = {f['id']: f for f in C.FILMS}; LAB = {l['id']: l for l in C.LAB}
PROC = {s['id']: s for s in json.load(open(S + '/process.json'))}
esc = html.escape

def w(path, text):
    p = os.path.join(R, path); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w').write(text)
def git(*a): return subprocess.run(['git', '-C', R] + list(a), capture_output=True, text=True)
def dur(p):
    try: return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p], capture_output=True, text=True).stdout)
    except Exception: return 0.
def mmss(d): return f'{int(d // 60)}:{int(d % 60):02d}'

# ---------------------------------------------------------------- media: films into media/films, cast into media/cast, icons
def relocate():
    old = {}
    for line in open(S + '/encode_site.sh'):
        m = re.match(r'enc \$H/(\S+) (\S+)', line)
        if m: old[m[1]] = m[2]
    os.makedirs(R + '/media/films', exist_ok=True)
    for f in C.FILMS:
        dst = f'media/films/{f["id"]}.mp4'; src = old.get(f['src'])
        if src and os.path.exists(os.path.join(R, src)) and not os.path.exists(os.path.join(R, dst)):
            if git('ls-files', '--error-unmatch', src).returncode == 0: git('mv', src, dst)
            else: shutil.move(os.path.join(R, src), os.path.join(R, dst))
        p = os.path.join(R, dst); f['ready'] = os.path.exists(p); f['dur'] = dur(p) if f['ready'] else dur(os.path.join(HOME, f['src']))
        f['mb'] = round(os.path.getsize(p) / 1e6) if f['ready'] else None
    os.makedirs(R + '/media/cast', exist_ok=True)
    for fn in glob.glob(S + '/cast/out/*.png'):
        im = fn; dst = R + '/media/cast/' + os.path.basename(fn); shutil.copyfile(im, dst)
    for fn in ('favicon.svg', 'apple-touch-icon.png', 'favicon-32.png', 'icon-512.png'): shutil.copyfile(os.path.join(H, fn), os.path.join(R, fn))

# ---------------------------------------------------------------- page frame
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;800;900&family=JetBrains+Mono:wght@400;600&family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,600;1,7..72,400&display=swap" rel="stylesheet">'
NAV = [('lab/', 'Try it'), ('family/', 'The Family'), ('cineosis/', 'CINEOSIS'), ('found-odyssey/', 'The Found Odyssey'), ('wygwyl/', 'WYGWYL'), ('this-side-up/', 'This Side Up'), ('films/', 'Films'), ('characters/', 'Characters'), ('process/', 'How it was made')]
def page(path, title, body, desc='', image='media/og.jpg', kind='website', extra_head='', crumbs=None):
    depth = path.count('/'); up = '../' * depth; here = path.rsplit('index.html', 1)[0]
    nav = ''.join(f'<a href="{up}{h}"{" aria-current=page" if here.startswith(h) else ""}>{n}</a>' for h, n in NAV)
    cr = ''
    if crumbs: cr = '<p class="crumbs">' + ' / '.join(f'<a href="{up}{h}">{esc(n)}</a>' if h is not None else esc(n) for n, h in crumbs) + '</p>'
    full = title if title == C.BRAND['name'] else f'{title} · {C.BRAND["name"]}'
    url = C.BASE + here; img = C.BASE + image
    return f"""<!doctype html><html lang="en" data-root="{up}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(full)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{url}">
<meta property="og:site_name" content="{C.BRAND['name']}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="{kind}"><meta property="og:url" content="{url}"><meta property="og:image" content="{img}">
<meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#0b0d10">
<link rel="icon" href="{up}favicon.svg" type="image/svg+xml"><link rel="icon" href="{up}favicon-32.png" sizes="32x32"><link rel="apple-touch-icon" href="{up}apple-touch-icon.png">
{FONTS}<link rel="stylesheet" href="{up}assets/site.css">{extra_head}</head><body>
<header class="top"><a class="brand" href="{up}"><img src="{up}favicon.svg" alt="" width="28" height="28"><span>{C.BRAND['name']}</span></a><nav>{nav}</nav></header>
<main class="wrap">{cr}{body}</main>
<footer class="foot"><div class="wrap"><p><b>{C.BRAND['studio']}</b> · {C.BRAND['author']} · built with Claude</p><p>Every figure is keyed by hand in a rig and rendered from code. Archive footage comes from the cineosis-lab library and is credited inside each film. <a href="{up}docs/">documents and prompts</a> · <a href="{up}catalog.json">catalog.json</a> · <a href="{up}sitemap.xml">sitemap</a> · <a href="https://github.com/hartswf0/bolas">source</a></p></div></footer>
<script src="{up}assets/cameo-data.js" defer></script><script src="{up}assets/cameo.js" defer></script>
</body></html>"""
def up_of(path): return '../' * path.count('/')

# ---------------------------------------------------------------- pieces
import cameo as CM
PREFIX = {'family': 'FAM', 'cineosis': 'CIN', 'odyssey': 'ODY', 'wygwyl': 'WYG'}
TID = {}
for _p in PREFIX:
    _n = 0
    for _f in C.FILMS:
        if _f['program'] != _p: continue
        if _f.get('ep'): TID[_f['id']] = f"{PREFIX[_p]}-E{_f['ep']}"
        else: _n += 1; TID[_f['id']] = f"{PREFIX[_p]}-{_n:02d}"
def cam(who, pose, at, film=None, lines=True, style=''):
    L = [] if who == 'poet' or not lines else [l for l in [CM.FILM.get(film, {}).get(who)] + CM.LINES.get(who, []) if l]
    flip = ' flip' if at in ('l', 'tl') else ''
    return f'<span class="cam {at}{flip}" data-who="{who}" data-c="{who}-{pose}" data-say="{esc(json.dumps(L))}"{f' style="{style}"' if style else ''}></span>'
def card_cam(f):
    opts = CM.CARD.get(f['program']) or []
    if not opts: return ''
    who, pose, at = opts[sum(map(ord, f['id'])) % len(opts)]
    return cam(who, pose, at, f['id'])
def film_card(f, up, big=False):
    p = PROG[f['program']]
    return f"""<a class="card film{' big' if big else ''}" href="{up}films/{f['id']}/" style="--c:{p['color']}">{card_cam(f)}<img src="{up}media/thumbs/{f['id']}.jpg" alt="" loading="lazy" width="1280" height="720">
<span class="meta"><span class="tid">{TID[f['id']]}</span> {mmss(f['dur'])}{' · ' + f['kind'] if f.get('kind') else ''}</span><b>{esc(f['title'])}</b><span class="line">{esc(f['line'])}</span></a>"""
def char_card(c, up, turn=False):
    img = c.get('turn') if turn and c.get('turn') else c['img']; p = PROG[c['program']]
    return f"""<article class="char{' turn' if turn and c.get('turn') else ''}" id="{c['id']}" style="--c:{p['color']}"><div class="fig"><img src="{up}media/cast/{img}" alt="{esc(c['name'])}" loading="lazy"></div>
<h3>{esc(c['name'])}</h3>{f'<p class="spec">{esc(c["spec"])}</p>' if c.get('spec') else ''}<p>{esc(c['line'])}</p>{appears(c, up)}</article>"""
def appears(c, up):
    fs = [f for f in C.FILMS if c['id'] in f.get('chars', [])]
    if not fs: return ''
    return '<p class="in">In: ' + ', '.join(f'<a href="{up}films/{f["id"]}/">{esc(f["title"])}</a>' for f in fs[:8]) + ('…' if len(fs) > 8 else '') + '</p>'
def lab_card(l, up):
    return try_tile(dict(href=f'lab/{l["id"]}/', img=f'media/lab/{l["id"]}.jpg', title=l['title'], verb=TRYVERB.get(l['id'], ''), line=l['line']), up)
TRYVERB = {'pencil-test': 'Scrub every beat of three scenes, frame by frame', 'range-test': 'Run 54 range tests, or load a video of a person and get the same report',
           'the-physical': 'Step through 47 proofs and see which joints each one drives', 'crash-lab': 'Filter 191 crash tests by instrument and play any of them', 'all-worlds': 'Open any of 159 worlds in the full rig'}
TRY = [dict(href='lab/crash-lab/', img='media/lab/crash-lab.jpg', title='Dramaturgy Crash Lab', id='crash-lab'), dict(href='lab/range-test/', img='media/lab/range-test.jpg', title='Range test and Video to Bolas', id='range-test'),
       dict(href='lab/the-physical/', img='media/lab/the-physical.jpg', title='The Physical', id='the-physical'), dict(href='lab/pencil-test/', img='media/lab/pencil-test.jpg', title='Pencil test', id='pencil-test'),
       dict(href='lab/crash-lab/all-worlds.html', img='media/lab/all-worlds.jpg', title='All worlds', id='all-worlds')]
def try_tile(t, up, cams=''):
    return f"""<a class="card try" href="{up}{t['href']}" style="--c:var(--amber)">{cams}<span class="shot"><img src="{up}{t['img']}" alt="" loading="lazy"><span class="go">Open</span></span><span class="meta"><span class="tid">Interactive</span> runs in your browser</span><b>{esc(t['title'])}</b><span class="line">{esc(t.get('verb') or TRYVERB.get(t.get('id'), ''))}</span></a>"""
def process_strip(stage_ids, up, n=6):
    out = ''
    for sid in stage_ids:
        s = PROC.get(sid)
        if not s or not s['images']: continue
        pick = s['images'][:: max(1, len(s['images']) // n)][:n]
        imgs = ''.join(f'<img src="{up}{i["src"]}" alt="{esc(i["caption"])}" loading="lazy">' for i in pick)
        out += f'<a class="strip" href="{up}process/{sid}/"><span class="meta">{esc(s["title"])} · {len(s["images"])} sheets</span><span class="imgs">{imgs}</span></a>'
    return out
def md(path):
    return '<div class="md">' + markdown.markdown(open(path).read(), extensions=['tables', 'fenced_code', 'sane_lists']) + '</div>'
def section(title, inner, sub=''):
    return f'<section class="sec"><div class="sechead"><h2>{esc(title)}</h2>{f"<p>{esc(sub)}</p>" if sub else ""}</div>{inner}</section>'
def grid(items, cls='grid'): return f'<div class="{cls}{" cams" if any("class=\"cam " in i for i in items) else ""}">{"".join(items)}</div>'

# ---------------------------------------------------------------- pages
# the This Side Up case pages are built by the session that made the films (they are static here; see this-side-up/<slug>/)
TSU_CASES = ['gust', 'mammoth', 'kit', 'reference', 'bullet-time', 'cardboard', 'two-clocks', 'thaw', 'fall', 'trouttown', 'wygwyl']
TSU_CARD = ('<div class="chans"><a class="chan" href="this-side-up/" style="--c:#b98a52"><span class="shot"><img src="this-side-up/media/still/tsu-ice.jpg" alt="" loading="lazy"></span>'
            '<span class="txt"><span class="meta"><span class="tid">TSU</span> 10 case studies</span><b>This Side Up</b>'
            '<span class="line">Boone, a handmade cardboard puppet, cut into parts and set into worlds where time stops for everything except him. How each film was made, with something to try.</span></span></a></div>')
def home():
    up = ''
    floor = ''.join(cam(w, p, 'f lo' if x < 50 else 'f hi', lines=False, style=f'left:{x}%' + (';top:calc(var(--floor) - var(--cam) * .3)' if w == 'critic' else '')) for w, p, x in CM.BAY)
    crate = '<span class="crate" style="left:calc(84% - var(--cam) * .3)"></span>'
    marks = ''.join(f'<span class="tgt" style="left:{x}%;top:{y}%"></span>' for x, y in ((62, 10), (94, 22), (78, 40)))
    rows = ''
    for p in C.PROGRAMS:
        fs = [f for f in C.FILMS if f['program'] == p['id']]; lead = FILM[{'family': 'crash-lab-film', 'cineosis': 'cineosis-hand-butter', 'odyssey': 'ep7-the-loop', 'wygwyl': 'wygwyl-poem07-paper-poet'}[p['id']]]
        c = {'family': cam('bola', 'sit', 'tl', lead['id']), 'cineosis': cam('critic', 'peek', 'tr', lead['id']), 'odyssey': cam('odysseus', 'sit', 'tr', lead['id']), 'wygwyl': ''}[p['id']]
        rows += f"""<a class="chan" href="{p['path']}" style="--c:{p['color']}"><span class="shot">{c}<img src="media/thumbs/{lead['id']}.jpg" alt="" loading="lazy"></span>
<span class="txt"><span class="meta"><span class="tid">{PREFIX[p['id']]}</span> {len(fs)} films</span><b>{esc(p['title'])}</b><span class="line">{esc(p['tag'])}</span></span></a>"""
    latest = [FILM[i] for i in ('wygwyl-poem07-paper-poet', 'ep7-the-loop', 'cineosis-hand-butter', 'crash-lab-film')]
    tiles = ''.join(try_tile(t, up, cam('dot', 'peek', 'tr', lines=True) if i == 0 else '') for i, t in enumerate(TRY[:4]))
    body = f"""<section class="bayhero">{marks}
<div class="baycopy"><p class="eyebrow">{esc(C.BRAND['studio'])} · {esc(C.BRAND['author'])}</p><h1>Crash Lab<span class="stripe"></span></h1>
<p class="lede">Films made as tests. Crash-test dummies, a drawn Odysseus and a paper poet, measured in a bay and set into archive film.</p>
<p class="quote">A report can say the knee hit the dashboard. The film shows it.</p>
<p><a class="btn" href="films/crash-lab-film/">Watch the crash lab</a> <a class="btn ghost" href="lab/">Move the dummies yourself</a></p></div>
<div class="baystage" style="--cam:clamp(110px,19vw,230px)">{crate}{floor}<span class="rule"></span></div></section>
{section('Try it', f'<div class="tries">{tiles}</div><p class="more"><a href="lab/">All five interactive pages</a></p>', 'interactive pages: every figure is computed in your browser')}
{section('Four channels', f'<div class="chans">{rows}</div>')}
{section('This Side Up', TSU_CARD, 'everything made of cardboard cut-outs')}
{section('Latest tests', grid([film_card(f, up) for f in latest]), 'every film has a test number, a logline and its notes')}
<p class="more"><a href="process/">How it was made: 18 case studies</a> · <a href="characters/">Every character</a> · <a href="films/">All {len(C.FILMS)} films</a></p>"""
    w('index.html', page('index.html', C.BRAND['name'], body, C.BRAND['about'], 'media/thumbs/crash-lab-film.jpg'))

def lab_index():
    path = 'lab/index.html'; up = up_of(path)
    tiles = ''.join(try_tile(t, up, cam(*[('dot', 'peek', 'tr'), ('bola', 'sit', 'tl'), ('shim', 'peek', 'tr'), ('bola', 'peek', 'tr'), ('critic', 'sit', 'tr')][i])) for i, t in enumerate(TRY))
    body = f"""<section class="hero"><p class="eyebrow">Interactive</p><h1>Try it<span class="stripe"></span></h1><p class="lede">Five pages where the figures are computed in your browser. Scrub, filter, play, and load your own video.</p></section>
<div class="tries all">{tiles}</div>"""
    w(path, page(path, 'Try it', body, 'Five interactive CRASH LAB pages: the rig, the range test, the physical, the pencil test and every world.', 'media/lab/crash-lab.jpg', crumbs=[('Home', ''), ('Try it', None)]))

def family():
    path = 'family/index.html'; up = up_of(path); p = PROG['family']
    chars = ''.join(char_card(CHAR[i], up, True) for i in ('bola', 'shim', 'dot', 'extras'))
    bay = '<ul class="instr">' + ''.join(f'<li><b>{t}</b>{d}</li>' for t, d in [('Weight', 'the centre of mass stays inside whatever holds the body up'), ('Feet', 'a planted heel moves less than 0.6 cm a frame'), ('Hands', 'a hand lands within 2 cm of where it was sent'), ('Contact', 'two bodies never pass through each other')]) + '</ul>'
    labs = ''.join(lab_card(LAB[i], up) for i in p['parts'])
    films = grid([film_card(f, up) for f in C.FILMS if f['program'] == 'family'])
    cin = PROG['cineosis']
    cineo = f"""<a class="prog wide" href="{up}cineosis/" style="--c:{cin['color']}"><img src="{up}media/thumbs/cineosis-hybrid-atlas.jpg" alt=""><span class="meta">the family's longest project</span><b>CINEOSIS</b><span class="line">{esc(cin['line'])}</span></a>"""
    body = f"""<section class="hero"><p class="eyebrow">Program · {esc(p['tag'])}</p><h1>The Crash-Test Family<span class="stripe"></span></h1><p class="lede">{esc(p['line'])}</p></section>
{section('The family', f'<div class="chars">{chars}</div>', 'front, three-quarter, side and back, drawn by the lab\'s own renderer')}
{section('The measured bay', bay, 'every vignette is a small drama and a crash test, read by four instruments')}
{section('Try it', f'<div class="tries">{labs}</div>', 'interactive pages: every figure is computed in your browser')}
{section('Films', films)}
{section('CINEOSIS', cineo)}
<p class="more"><a href="{up}process/">How it was made: the case studies</a></p>"""
    w(path, page(path, p['title'], body, p['line'], 'media/cast/family-lineup.png', crumbs=[('Home', ''), (p['title'], None)]))

def cineosis():
    path = 'cineosis/index.html'; up = up_of(path); p = PROG['cineosis']
    main = [FILM[i] for i in ('cineosis-crash-lab', 'cineosis-hybrid-pilot', 'cineosis-hybrid-atlas', 'cineosis-handmade-film', 'cineosis-hand-butter')]
    reels = [f for f in C.FILMS if f['program'] == 'cineosis' and f.get('kind') == 'reel']
    steps = ''.join(f'<li><b>{esc(t)}</b> {esc(d)}</li>' for t, d in [
        ('In the bay.', 'The family performs each sign over measured worlds; a critic judges each sign from stills against its test and its counterfeit.'),
        ('Hybrid pilot.', 'Six signs put into their real archive clips, each plate fitted by hand: camera, light, shadows, occlusion.'),
        ('Hybrid atlas.', 'An automatic pipeline puts Bola into two clips for every sign: 84 passages.'),
        ('Handmade.', 'Every sign authored again by hand, reviewed blind in rounds by fresh critics.'),
        ('Hand Butter.', 'The making-of, performed by the cast, with the Critic as a character.')])
    body = f"""<section class="hero"><p class="eyebrow">Program · {esc(p['tag'])}</p><h1>CINEOSIS<span class="stripe"></span></h1><p class="lede">{esc(p['line'])}</p></section>
{section('Five stages', f'<ol class="steps">{steps}</ol>')}
{section('Films', grid([film_card(f, up) for f in main]))}
{section('Cast', '<div class="chars">' + ''.join(char_card(CHAR[i], up, True) for i in ('bola', 'shim', 'critic')) + '</div>', 'the family, and the Critic who joined them for Hand Butter')}
{section('Review reels', grid([film_card(f, up) for f in reels]))}
<p class="more"><a href="{up}process/">How it was made: the case studies</a></p>"""
    w(path, page(path, 'CINEOSIS', body, p['line'], 'media/thumbs/cineosis-hybrid-atlas.jpg', crumbs=[('Home', ''), ('The Crash-Test Family', 'family/'), ('CINEOSIS', None)]))

def odyssey():
    path = 'found-odyssey/index.html'; up = up_of(path); p = PROG['odyssey']
    eps = sorted([f for f in C.FILMS if f.get('ep')], key=lambda f: f['ep']); tests = [f for f in C.FILMS if f['program'] == 'odyssey' and not f.get('ep')]
    cast = ''.join(f'<a class="mini" href="{up}found-odyssey/cast/#{c["id"]}"><img src="{up}media/cast/{c["img"]}" alt="" loading="lazy"><span>{esc(c["name"])}</span></a>' for c in C.CHARACTERS if c['program'] == 'odyssey')
    body = f"""<section class="hero"><p class="eyebrow">Program · {esc(p['tag'])}</p><h1>The Found Odyssey<span class="stripe"></span></h1><p class="lede">{esc(p['line'])}</p></section>
{section('Episodes', grid([film_card(f, up, True) for f in eps], 'grid eps'))}
{section('The cast', f'<div class="minis">{cast}</div><p><a class="btn" href="{up}found-odyssey/cast/">Cast and character development</a></p>', 'one body, many costumes')}
{section('Tests', grid([film_card(f, up) for f in tests]))}
<p class="more"><a href="{up}process/fo-tests/">How it was made: the case studies</a></p>
<p class="lede">The method as a prompt: <a href="{up}docs/prompts/12-found-footage-animation.poml.html">found-footage-animation.poml</a>.</p>"""
    w(path, page(path, p['title'], body, p['line'], 'media/thumbs/ep7-the-loop.jpg', crumbs=[('Home', ''), (p['title'], None)]))
    # cast page with character development sheets
    path = 'found-odyssey/cast/index.html'; up = up_of(path)
    dev = []
    for sid in C.PROCESS['odyssey']:
        for i in PROC.get(sid, {}).get('images', []):
            if re.search(r'(toon-t1|t-gods|t-py|ody-t\d|lab-|ref-|/dx-|line|test-(poly|odys|athena|beggar|circe|seer|mother|king|ajax|trench)\b)', i['src']): dev.append((sid, i))
    devhtml = ''.join(f'<figure><a href="{up}{i["src"]}"><img src="{up}{i["src"]}" alt="" loading="lazy"></a><figcaption>{esc(i["caption"])}<span>{esc(PROC[sid]["title"])} · {esc(i["time"])}</span></figcaption></figure>' for sid, i in dev)
    body = f"""<section class="hero"><p class="eyebrow">The Found Odyssey · cast</p><h1>The cast<span class="stripe"></span></h1><p class="lede">Every character is the same keyed body in a different costume, drawn by one ink renderer: a new character is a costume preset, not a new body. The black-figure style is the same renderer with every fill black and every line incised.</p></section>
{section('Characters', '<div class="chars">' + ''.join(char_card(c, up) for c in C.CHARACTERS if c['program'] == 'odyssey') + '</div>')}
{section('Character development', f'<div class="gallery">{devhtml}</div>', 'first drawn figures, costume tests, line studies and scene tests, in the order they were made')}"""
    w(path, page(path, 'The Found Odyssey · cast', body, 'The cast of The Found Odyssey: one body, many costumes.', 'media/cast/ody-odysseus.png', crumbs=[('Home', ''), ('The Found Odyssey', 'found-odyssey/'), ('Cast', None)]))

def wygwyl():
    path = 'wygwyl/index.html'; up = up_of(path); p = PROG['wygwyl']
    fs = [f for f in C.FILMS if f['program'] == 'wygwyl']
    body = f"""<section class="hero"><p class="eyebrow">Program · {esc(p['tag'])}</p><h1>WYGWYL<span class="stripe"></span></h1><p class="lede">{esc(p['line'])}</p></section>
{section('Poem 07', grid([film_card(fs[0], up, True)], 'grid one'))}
{section('The cast', '<div class="chars">' + ''.join(char_card(c, up) for c in C.CHARACTERS if c['program'] == 'wygwyl') + '</div>')}
{section('How a patch is built', '<ol class="steps"><li><b>Words to gestures.</b> A cue table maps words in the patch\'s line to one held gesture each (ear, mic, open hands, reach, heart, chin up, head down, camera, glasses) and writes the rig world.</li><li><b>Heads.</b> Each frame takes the replacement head nearest the rig\'s turn and tilt; some words ask for a particular head.</li><li><b>Plates.</b> His own photographs with him painted out; the puppet goes back where he stood.</li><li><b>Inset.</b> The patch\'s own archive cel, framed on a cardboard plinth, labelled from the cel database.</li></ol>')}
{section('Proofs', grid([film_card(f, up) for f in fs[1:]]))}
<p class="more"><a href="{up}process/wygwyl/">How it was made: the case study</a></p>"""
    w(path, page(path, 'WYGWYL', body, p['line'], 'media/thumbs/wygwyl-poem07-paper-poet.jpg', crumbs=[('Home', ''), ('WYGWYL', None)]))

def characters():
    path = 'characters/index.html'; up = up_of(path); body = '<section class="hero"><p class="eyebrow">Characters</p><h1>Characters<span class="stripe"></span></h1><p class="lede">Every cast in CRASH LAB, by program. Each card links the films a character appears in.</p></section>'
    for pid in ('family', 'cineosis', 'odyssey', 'wygwyl'):
        cs = [c for c in C.CHARACTERS if c['program'] == pid]
        body += section(PROG[pid]['title'], '<div class="chars">' + ''.join(char_card(c, up, pid in ('family', 'cineosis')) for c in cs) + '</div>', PROG[pid]['tag'])
    w(path, page(path, 'Characters', body, 'Every cast in CRASH LAB: the crash-test family, the Critic, The Found Odyssey and the paper poet.', 'media/cast/family-lineup.png', crumbs=[('Home', ''), ('Characters', None)]))

import notes as NT, cases as CS
STAGE_OF = {fid: sid for sid, k in CS.CASES.items() for fid in k.get('films', [])}
def guided_notes(f, up, here):
    sid = STAGE_OF.get(f['id']); mine = PROC[sid]['images'] if sid in PROC else []
    k = ORDER.index(sid) if sid in ORDER else -1     # scene tests can fall in the neighbouring stage's time window; they are matched by scene name only
    near = [i for j in (k - 1, k + 1) if 0 <= j < len(ORDER) and PROC[ORDER[j]]['program'] == f['program'] for i in PROC[ORDER[j]]['images'] if '-test-' in i['src']] if k >= 0 else []
    ownset = {i['src'] for i in mine}; imgs = mine + near
    who = 'odysseus' if f['program'] == 'odyssey' else 'critic' if re.search(r'findings|validation|report|hand-butter', f['notes']) else 'bola'
    h, n = NT.render(os.path.join(HOME, f['notes']), NT.Film(f['id'], f['dur']), f['id'], imgs, up, here, who, sid, CM.FILM.get(f['id'], {}).get(who, ''), lambda i: i['src'] in ownset, f.get('ep'))
    print('notes', f['id'], n, 'parts with pictures')
    return h + LIGHTBOX
def films():
    path = 'films/index.html'; up = up_of(path); body = f'<section class="hero"><p class="eyebrow">Films</p><h1>Films<span class="stripe"></span></h1><p class="lede">{len(C.FILMS)} films, {mmss(sum(f["dur"] for f in C.FILMS))} in all, by program.</p></section>'
    for pid in ('family', 'cineosis', 'odyssey', 'wygwyl'):
        body += section(PROG[pid]['title'], grid([film_card(f, up) for f in C.FILMS if f['program'] == pid]))
    w(path, page(path, 'Films', body, f'All {len(C.FILMS)} CRASH LAB films with loglines.', 'media/thumbs/crash-lab-film.jpg', crumbs=[('Home', ''), ('Films', None)]))
    for f in C.FILMS:
        path = f'films/{f["id"]}/index.html'; up = up_of(path); p = PROG[f['program']]
        chars = ', '.join(f'<a href="{up}characters/#{c}">{esc(CHAR[c]["name"])}</a>' if c in CHAR else esc(c) for c in f.get('chars', [])) or '—'
        notes = guided_notes(f, up, True) if f.get('notes') else ''
        rel = [g for g in C.FILMS if g['program'] == f['program'] and g['id'] != f['id']][:4]
        prog_link = {'family': 'family/', 'cineosis': 'cineosis/', 'odyssey': 'found-odyssey/', 'wygwyl': 'wygwyl/'}[f['program']]
        video = f'<video controls preload="none" playsinline poster="{up}media/posters/{f["id"]}.jpg" src="{up}media/films/{f["id"]}.mp4"></video>' if f['ready'] else f'<img class="still" src="{up}media/posters/{f["id"]}.jpg" alt=""><p class="note">The web copy of this film is still being encoded.</p>'
        ld = dict({'@context': 'https://schema.org', '@type': 'VideoObject', 'name': f['title'], 'description': f['line'], 'thumbnailUrl': C.BASE + f'media/thumbs/{f["id"]}.jpg',
                   'uploadDate': f['date'], 'duration': f'PT{int(f["dur"] // 60)}M{int(f["dur"] % 60)}S', 'contentUrl': C.BASE + f'media/films/{f["id"]}.mp4', 'creator': {'@type': 'Person', 'name': C.BRAND['author']}})
        cams = ''.join(cam(wh, po, at, f['id']) for wh, po, at in CM.PLAYER.get(f['program'], []))
        body = f"""<section class="filmpage"><p class="eyebrow" style="color:{p['color']}"><span class="tid">Test {TID[f['id']]}</span> {esc(p['title'])}{' · ' + esc(f['kind']) if f.get('kind') else ''}</p><h1 class="ft">{esc(f['title'])}</h1><div class="player">{video}{cams}</div>
<p class="logline">{esc(f['line'])}</p>
<dl class="facts"><div><dt>Running time</dt><dd>{mmss(f['dur'])}</dd></div><div><dt>Made</dt><dd>{f['date']}</dd></div><div><dt>Program</dt><dd><a href="{up}{prog_link}">{esc(p['title'])}</a></dd></div><div><dt>Characters</dt><dd>{chars}</dd></div><div><dt>File</dt><dd>{'<a href="' + up + 'media/films/' + f['id'] + '.mp4">mp4</a>, 960 wide, ' + str(f['mb']) + ' MB' if f['ready'] else 'encoding'}</dd></div></dl>
{notes}</section>{section('More from ' + p['title'], grid([film_card(g, up) for g in rel]))}"""
        w(path, page(path, f['title'], body, f['line'], f'media/thumbs/{f["id"]}.jpg', 'video.other', f'<script type="application/ld+json">{json.dumps(ld)}</script><meta property="og:video" content="{C.BASE}media/films/{f["id"]}.mp4">',
                     crumbs=[('Home', ''), (p['title'], prog_link), (f['title'], None)]))

ORDER = [sid for pid in ('family', 'cineosis', 'odyssey', 'wygwyl') for sid in C.PROCESS[pid]]
def clean_cap(c):
    if re.fullmatch(r'(Critic: )?[a-z0-9 ]{1,6}', c): return 'Test frames'
    if re.fullmatch(r'[a-z]+', c): return 'Scene still, ' + c
    return c
def steps(images, gap=20 * 60, most=14):
    """split a stage's images into steps at gaps in working time, capped in size"""
    T = lambda i: datetime.datetime.strptime('2026 ' + i['time'], '%Y %b %d %H:%M').timestamp()
    out = []
    for i in images:
        if not out or T(i) - T(out[-1][-1]) > gap or len(out[-1]) >= most: out.append([])
        out[-1].append(i)
    return out
def step_label(g):
    import collections
    c = collections.Counter(re.split(r',| \d| sign| round', clean_cap(i['caption']))[0].strip() for i in g).most_common(2)
    return ' and '.join(k for k, _ in c)
def case_map(cur, up):
    out = ''
    for n, sid in enumerate(ORDER, 1):
        s = PROC[sid]; col = PROG[s['program']]['color']
        out += f'<a href="{up}process/{sid}/" style="--c:{col}"{" aria-current=page" if sid == cur else ""} title="{esc(s["title"])}">{n:02d}</a>'
    return f'<nav class="casemap" aria-label="All cases">{out}</nav>'
def fig(i, up, big=False):
    return f'<figure{" class=big" if big else ""}><a href="{up}{i["src"]}" data-lb><img src="{up}{i["src"]}" alt="{esc(clean_cap(i["caption"]))}" loading="lazy" width="{i["w"]}" height="{i["h"]}"></a><figcaption>{esc(clean_cap(i["caption"]))}<span>{esc(i["time"])}</span></figcaption></figure>'
LIGHTBOX = """<div class="lb" hidden><button class="lbx" aria-label="Close">Close</button><button class="lbp" aria-label="Previous">&larr;</button><img alt=""><p></p><button class="lbn" aria-label="Next">&rarr;</button></div>
<script>(()=>{const L=document.querySelector('.lb'),I=L.querySelector('img'),P=L.querySelector('p');let a=[...document.querySelectorAll('[data-lb]')],k=0;
const show=n=>{a=[...document.querySelectorAll('[data-lb]')].filter(x=>x.offsetParent);k=(n+a.length)%a.length;const x=a[k];I.src=x.href;P.textContent=(k+1)+' / '+a.length+'  ·  '+x.querySelector('img').alt;L.hidden=false;document.body.style.overflow='hidden'};
const hide=()=>{L.hidden=true;document.body.style.overflow=''};
document.addEventListener('click',e=>{const x=e.target.closest('[data-lb]');if(x){e.preventDefault();a=[...document.querySelectorAll('[data-lb]')].filter(y=>y.offsetParent);show(a.indexOf(x))}});
L.querySelector('.lbx').onclick=hide;L.querySelector('.lbp').onclick=()=>show(k-1);L.querySelector('.lbn').onclick=()=>show(k+1);L.onclick=e=>{if(e.target===L)hide()};
document.addEventListener('keydown',e=>{if(L.hidden)return;if(e.key==='Escape')hide();if(e.key==='ArrowLeft')show(k-1);if(e.key==='ArrowRight')show(k+1)})})()</script>"""

def process():
    import cases; K = cases.CASES
    path = 'process/index.html'; up = up_of(path)
    body = f"""<section class="hero"><p class="eyebrow">Process · 18 case studies</p><h1>How it was made<span class="stripe"></span></h1>
<p class="lede">Every stage of the work, from the first stick figure to the paper poet, written up as a case study: the question it asked, how it was made, what broke, what changed, and what it teaches that the others do not. Each case links to the next, so they can be read in order.</p>
<p><a class="btn" href="{up}process/{ORDER[0]}/">Start with case 01</a></p></section>"""
    n = 0
    for pid in ('family', 'cineosis', 'odyssey', 'wygwyl'):
        p = PROG[pid]; rows = ''
        for sid in C.PROCESS[pid]:
            n += 1; s = PROC[sid]; k = K[sid]; im = s['images'][-1] if s['images'] else None
            rows += f"""<a class="caserow" href="{up}process/{sid}/" style="--c:{p['color']}"><span class="num">{n:02d}</span>
<span class="txt"><b>{esc(s['title'])}</b><span class="q">{esc(k['q'])}</span><span class="t"><em>Teaches</em> {esc(k['teaches'][0])}</span><span class="meta">{len(s['images'])} sheets · {esc(s['images'][0]['time'] if s['images'] else '')}</span></span>
{f'<img src="{up}{im["src"]}" alt="" loading="lazy">' if im else ''}</a>"""
        body += section(p['title'], f'<div class="caselist">{rows}</div>', p.get('line', ''))
    w(path, page(path, 'How it was made', body, 'Eighteen case studies from CRASH LAB: the question each stage asked, what broke, what changed and what it teaches.', 'media/thumbs/cineosis-hand-butter.jpg', crumbs=[('Home', ''), ('Process', None)]))

    for n, sid in enumerate(ORDER, 1):
        s = PROC[sid]; k = K[sid]; path = f'process/{sid}/index.html'; up = up_of(path); prog = PROG[s['program']]; col = prog['color']
        ims = s['images']; groups = steps(ims)
        prev = ORDER[n - 2] if n > 1 else None; nxt = ORDER[n] if n < len(ORDER) else None
        span = f'{ims[0]["time"]} to {ims[-1]["time"]}' if ims else ''
        outs = ''.join(film_card(FILM[f], up) for f in k.get('films', []) if f in FILM)
        if k.get('lab'): outs = lab_card(LAB[k['lab']], up) + outs
        docs = ''.join(f'<li><a href="{up}{h}">{esc(t)}</a></li>' for t, h in k.get('docs', []))
        fixes = ''.join(f'<li><span class="pb">{esc(a)}</span><span class="fx">{esc(b)}</span></li>' for a, b in k.get('fixes', []))
        sb = ''
        for gi, g in enumerate(groups, 1):
            t0, t1 = g[0]['time'], g[-1]['time'][-5:]
            head = f'<div class="stephead"><span class="sn">Step {gi}</span><b>{esc(step_label(g)[:1].upper() + step_label(g)[1:])}</b><span>{esc(t0)}{"–" + t1 if t1 != t0[-5:] else ""} · {len(g)} {"sheet" if len(g) == 1 else "sheets"}</span></div>'
            first, rest = g[:4], g[4:]
            more = f'<details><summary>Show {len(rest)} more from this step</summary><div class="stepgrid">{"".join(fig(i, up) for i in rest)}</div></details>' if rest else ''
            sb += f'<section class="step">{head}<div class="stepgrid">{"".join(fig(i, up) for i in first)}</div>{more}</section>'
        bef = f'<div class="ba">{fig(ims[0], up)}{fig(ims[-1], up)}</div>' if len(ims) > 1 else ''
        nav = lambda sid2, lab_: (f'<a href="{up}process/{sid2}/" class="{lab_}"><span>{"Previous" if lab_ == "p" else "Next"} · case {ORDER.index(sid2) + 1:02d}</span><b>{esc(PROC[sid2]["title"])}</b></a>' if sid2 else f'<a href="{up}process/" class="{lab_}"><span>All cases</span><b>Back to the list</b></a>')
        body = f"""<article class="case" style="--c:{col}">
<section class="hero casehero"><p class="eyebrow" style="color:{col}">Case {n:02d} of {len(ORDER)} · {esc(prog['title'])}</p><h1 class="ft">{esc(s['title'])}</h1>
<p class="question">{esc(k['q'])}</p><p class="lede">{esc(k['made'])}</p><p class="meta">{len(ims)} sheets · {esc(span)}</p></section>
{case_map(sid, up)}
<div class="casebody">
<section class="block"><h2>How it was made</h2><ol class="method">{''.join(f'<li>{esc(m)}</li>' for m in k['method'])}</ol></section>
<section class="block teach"><h2>What this case teaches</h2><ol>{''.join(f'<li>{esc(t)}</li>' for t in k['teaches'])}</ol><p class="vs"><b>How it differs.</b> {esc(k['vs'])}</p></section>
{f'<section class="block"><h2>What broke and what changed</h2><ul class="fixes">{fixes}</ul></section>' if fixes else ''}
{f'<section class="block"><h2>First sheet and last sheet</h2><p class="note">Where the stage started and where it finished.</p>{bef}</section>' if bef else ''}
</div>
<section class="sec sheetsteps"><div class="sechead"><h2>The sheets, step by step</h2><p>Grouped by working session. Click any sheet to view it full size; use the arrow keys to move through them.</p></div>{sb}</section>
<div class="casebody">
{f'<section class="block"><h2>What came out of it</h2><div class="grid">{outs}</div></section>' if outs else ''}
{f'<section class="block"><h2>Read the record</h2><ul class="doclist">{docs}</ul></section>' if docs else ''}
<section class="block carry"><h2>Carried forward</h2><p>{esc(k['carry'])}</p></section>
</div></article>
<nav class="casenav">{nav(prev, 'p')}{nav(nxt, 'n')}</nav>{LIGHTBOX}"""
        w(path, page(path, f'Case {n:02d}: {s["title"]}', body, f'{k["q"]} {k["teaches"][0]}', ims[-1]['src'] if ims else 'media/og.jpg', kind='article',
                     crumbs=[('Home', ''), ('Process', 'process/'), (f'Case {n:02d}', None)]))

def lab():
    srcs = {'pencil-test': f'{TR}/artifact-7c451a71-1792177164-c4fe.html', 'range-test': f'{TR}/artifact-98495112-1792182661-cba3.html',
            'the-physical': f'{TR}/artifact-e234b3ca-1792184744-dee7.html', 'crash-lab': f'{TR}/artifact-1ca71376-1792277033-03b9.html'}
    for l in C.LAB:
        t = open(srcs[l['id']]).read()
        head = (f'<link rel="icon" href="../../favicon.svg" type="image/svg+xml"><meta name="description" content="{esc(l["line"])}"><meta property="og:title" content="{esc(l["title"])}">'
                f'<meta property="og:image" content="{C.BASE}media/thumbs/{l.get("film") or "crash-lab-film"}.jpg">')
        bar = ('<a href="../../family/" style="position:fixed;z-index:9999;top:calc(env(safe-area-inset-top,0px) + 8px);right:max(10px,env(safe-area-inset-right,0px));'
               'font:600 11px/1 \'JetBrains Mono\',ui-monospace,monospace;letter-spacing:.06em;text-transform:uppercase;background:#0b0d10;color:#fff;padding:7px 10px;text-decoration:none;border:1.5px solid #fff">'
               'CRASH LAB · the family</a>')
        t = t.replace('</head>', head + '</head>', 1).replace('<body>', '<body>' + bar, 1)
        w(f'lab/{l["id"]}/index.html', t)
        if l['id'] == 'range-test': shutil.copyfile(S + '/range/movenet.js', R + '/lab/range-test/movenet.js')
        if l['id'] == 'crash-lab':
            a = open(S + '/crash/hyb.html').read().replace('<body>', '<body>' + bar, 1) if '<body>' in open(S + '/crash/hyb.html').read() else bar + open(S + '/crash/hyb.html').read()
            w('lab/crash-lab/all-worlds.html', a)

def docs():
    """the documents section from the first build, re-framed in the new page shell"""
    for fp in glob.glob(R + '/docs/**/*.html', recursive=True):
        if fp.endswith('movement-acting-library.html'): continue
        t = open(fp).read(); m = re.search(r'<nav class="bar">.*?</nav>\s*(.*?)\s*<p class="foot">', t, re.S)
        if not m: continue
        rel = os.path.relpath(fp, R); title = re.search(r'<title>(.*?)</title>', t).group(1)
        w(rel, page(rel, html.unescape(title), m.group(1), 'CRASH LAB documents and prompts.', 'media/og.jpg', crumbs=[('Home', ''), ('Docs', 'docs/'), (html.unescape(title), None)] if not rel.endswith('docs/index.html') else [('Home', ''), ('Docs', None)]))

    for f in C.FILMS:   # the notes pages under docs/ get the same guided read, with frames linking to the film
        if not f.get('notes'): continue
        rel = f'docs/notes/{f["notes"][:-3]}.html'; up = up_of(rel)
        body = f'<section class="hero"><p class="eyebrow">Production notes</p><h1 class="ft">{esc(f["title"])}</h1><p class="lede">{esc(f["line"])} <a href="{up}films/{f["id"]}/">Watch the film</a>.</p></section>' + guided_notes(f, up, False)
        w(rel, page(rel, f'{f["title"]} · production notes', body, f['line'], f'media/thumbs/{f["id"]}.jpg', crumbs=[('Home', ''), ('Docs', 'docs/'), (f['title'], None)]))

def extras():
    urls = ['', 'lab/'] + [p['path'] for p in C.PROGRAMS] + ['this-side-up/'] + [f'this-side-up/{s}/' for s in TSU_CASES] + ['found-odyssey/cast/', 'characters/', 'films/', 'process/', 'docs/'] + [f'films/{f["id"]}/' for f in C.FILMS] + [f'process/{s}/' for s in PROC] + [f'lab/{l["id"]}/' for l in C.LAB]
    w('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{C.BASE}{u}</loc></url>' for u in urls) + '</urlset>\n')
    w('robots.txt', f'User-agent: *\nAllow: /\nSitemap: {C.BASE}sitemap.xml\n')
    w('catalog.json', json.dumps(dict(brand=C.BRAND, programs=C.PROGRAMS, characters=C.CHARACTERS, lab=C.LAB,
        films=[{k: v for k, v in f.items() if k not in ('ready',)} | dict(file=f'media/films/{f["id"]}.mp4', thumb=f'media/thumbs/{f["id"]}.jpg', poster=f'media/posters/{f["id"]}.jpg') for f in C.FILMS],
        process=[dict(id=s['id'], title=s['title'], program=s['program'], count=len(s['images'])) for s in PROC.values()]), indent=1))
    shutil.copyfile(R + '/media/thumbs/crash-lab-film.jpg', R + '/media/og.jpg')
    w('README.md', f"""# {C.BRAND['name']}

{C.BRAND['line']}. {C.BRAND['about']}

Live: {C.BASE}

| Program | |
|---|---|
""" + ''.join(f"| [{p['title']}]({p['path']}) | {p['line']} |\n" for p in C.PROGRAMS) + f"""
- [This Side Up](this-side-up/): case studies of the cardboard cut-out films, each with a full case page of versions, prompts, critic rounds and sheets
- [Characters](characters/) · [Films](films/) ({len(C.FILMS)}) · [Process](process/) · [Docs and prompts](docs/)
- Lab pages: """ + ' · '.join(f"[{l['title']}](lab/{l['id']}/)" for l in C.LAB) + """

## How the site is built

The site is generated from one catalog. `catalog.json` is its published form: programs, characters, films (with loglines,
running times, thumbnails) and process stages. Pages, thumbnails and the sitemap are generated from it; adding a film is one
catalog entry plus its file under `media/films/`. Every film gets a test number (FAM-03, CIN-05, ODY-E7, WYG-01) from its
program and its order in the catalog.

## The cast around the films

The characters that sit on cards, peek over players and talk to the viewer are sprite strips in `media/cameo/`, rendered
from the rig at one shared scale (`cameos.json` records each strip's frame size and its anchor: soles, seat or hands).
`site/cameo.py` says who appears around which program's films and what they say; `assets/cameo.js` places them, animates
them and has them react to the player (they sit down and turn to watch on play, turn back on pause, cheer at the end).
A new character is a set of sprites plus one entry for its size and lines. The poet is a real person: he appears but never speaks.
""")

def cameo_assets():
    sp = json.load(open(R + '/media/cameo/cameos.json'))
    data = dict(s={k: dict(w=v['w'], h=v['h'], n=v['n'], ay=v['ay']) for k, v in sp.items()}, k=CM.SIZE, play=CM.ON_PLAY, pause=CM.ON_PAUSE, end=CM.ON_END, talk=CM.BAY_TALK)
    w('assets/cameo-data.js', 'window.CAM=' + json.dumps(data, separators=(',', ':')) + ';\n')
    shutil.copy(H + '/cameo.js', R + '/assets/cameo.js')
def main():
    relocate(); cameo_assets(); lab(); lab_index(); home(); family(); cineosis(); odyssey(); wygwyl(); characters(); films(); process(); docs(); extras()
    # the first build's section folders are replaced by the structure above
    for d in ('01-pencil-test', '02-range-test', '03-the-physical', '04-crash-lab', '05-hybrid-atlas', '06-hand-butter', '07-found-odyssey'):
        p = os.path.join(R, d)
        if not os.path.exists(p): continue
        left = [f for f in glob.glob(p + '/**/*.mp4', recursive=True) if not f.endswith('.part.mp4')]
        if left: print('keeping', d, 'films not yet moved:', len(left)); continue
        if any(f.endswith('.part.mp4') for f in glob.glob(p + '/**/*', recursive=True)): print('keeping', d, '(encoding)'); continue
        git('rm', '-r', '-q', '--cached', d); shutil.rmtree(p)
    old = R + '/wygwyl'
    for f in glob.glob(old + '/*.jpg') + glob.glob(old + '/*sheet*'):
        if os.path.exists(f): git('rm', '-q', '--cached', os.path.relpath(f, R)); os.remove(f)
    print('built', len(C.FILMS), 'films', sum(f['ready'] for f in C.FILMS), 'ready')
if __name__ == '__main__': main()
