#!/usr/bin/env python3
"""Mirror the whole Crank Boy site into the Bolas site: python3 shorts/tools/to_bolas.py <bolas checkout>
Copies this repository (without .git and the agent instruction files CLAUDE.md and GEMINI.md) into <bolas>/crank-boy/ and:
  - moves the album, index.html, to album.html, and points every link to the repository's index.html at album.html;
  - adds <meta name="crank-mirror"> to every page, which tells room/site.js and films.html that Bolas is one folder up
    (so the Bolas films stream from ../media/films/ instead of the published site);
  - writes <bolas>/crank-boy/index.html, the landing page in the Bolas frame;
  - adds the pages to <bolas>/sitemap.xml;
  - copies registry/works.json to <bolas>/tools/site/ and runs works.py there, which adds "Part of ... how it follows" to every Bolas film page.
Run it again after any change here; it replaces the copy. Then run bolas/tools/site/build.py's checks and commit in Bolas."""
import html, json, os, re, shutil, sys
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
bolas = sys.argv[1]
out = os.path.join(bolas, 'crank-boy')
src = open(os.path.join(root, 'registry/registry.js'), encoding='utf-8').read()
R = json.loads(src[src.index('{'):src.rindex('}') + 1])
fsrc = open(os.path.join(root, 'registry/films.js'), encoding='utf-8').read()
FI = json.loads(fsrc[fsrc.index('{'):fsrc.rindex('}') + 1])
esc = html.escape

if os.path.isdir(out):
    shutil.rmtree(out)
shutil.copytree(root, out, ignore=shutil.ignore_patterns('.git', 'node_modules', 'CLAUDE.md', 'GEMINI.md', '*.cues.json', '__pycache__'))
os.rename(os.path.join(out, 'index.html'), os.path.join(out, 'album.html'))

# every page: say it is a mirror, and send links to the repository's index.html to album.html
n = 0
for d, _, fs in os.walk(out):
    for f in fs:
        if not f.endswith('.html'):
            continue
        p = os.path.join(d, f)
        t = open(p, encoding='utf-8').read()
        depth = os.path.relpath(d, out).count('/') + (0 if os.path.relpath(d, out) == '.' else 1)
        prefix = '../' * depth
        t = re.sub(r'(href=["\'])' + re.escape(prefix) + r'index\.html', r'\1' + prefix + 'album.html', t)
        if 'crank-mirror' not in t and '<head>' in t:
            t = t.replace('<head>', '<head>\n<meta name="crank-mirror" content="bolas">', 1)
        open(p, 'w', encoding='utf-8').write(t)
        n += 1

NAV = [('lab/', 'Try it'), ('family/', 'The Family'), ('cineosis/', 'CINEOSIS'), ('found-odyssey/', 'The Found Odyssey'), ('wygwyl/', 'WYGWYL'),
       ('this-side-up/', 'This Side Up'), ('crank-boy/', 'The Crank Boy'), ('films/', 'Films'), ('characters/', 'Characters'), ('process/', 'How it was made')]
nav = ''.join(f'<a href="../{h}"{" aria-current=page" if h == "crank-boy/" else ""}>{n_}</a>' for h, n_ in NAV)
T = R['town']
nfilms = len([f for f in FI['films'] if not f.get('external')])
feat = [f for f in FI['films'] if f['id'] in ('town', 'proof-school', 'v9-played')]
tiles = ''.join(f'''<a class="cb-tile" href="films.html#{esc(f["id"])}"><img src="{esc(f["thumb"])}" alt="" loading="lazy"><b>{esc(f["title"])}</b><span>{esc(f["line"][:150].rsplit(" ", 1)[0])}…</span></a>''' for f in feat)
def more(cid):
    fs = [f for f in FI['films'] if f.get('card') == cid]
    if len(fs) < 2:
        return ''
    return '<span class="cb-ops">' + str(len(fs)) + ' films for this card: ' + ' · '.join(f'<a href="films.html#{esc(f["id"])}">{esc(f.get("role") or f["kind"])}</a>' for f in fs) + '</span>'
cards = ''.join(f'''<div class="cb-card"><a href="films.html#{esc(s["id"])}"><img src="{esc(s["poster"])}" alt="" loading="lazy"></a>
<b>{esc(s["title"])}</b><span class="line">{esc(s["line"])}</span>
<span class="cb-ops">Film: {esc(s["operator"])} · Game: {esc(s["game"]["op"])} · Proposed sign: {esc(s["reading"]["sign"])}</span>
{more(s["id"])}<span class="cb-links"><a href="films.html#{esc(s["id"])}">Watch</a> · <a href="{esc(s["game"]["link"])}">Play the game</a> · <a href="shorts/index.html#{esc(s["id"])}">How it was made</a> · <a href="kit.html#card-{esc(s["id"])}">The pieces</a></span></div>''' for s in R['shorts'])
worklist = ''.join(f'<li><a href="films.html#w:{esc(w["id"])}">{esc(w["title"])}</a> · {len(w["members"])} films</li>' for w in FI['works'])
desc = 'One 1910 postcard, seven versions of a game, and Futuretown: seven cards as films, games and one playable town, with archive film from the cineosis-lab library.'
page = f'''<!doctype html><html lang="en" data-root="../"><head><meta charset="utf-8"><meta name="crank-mirror" content="bolas"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>The Crank Boy · CRASH LAB</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="https://hartswf0.github.io/bolas/crank-boy/">
<meta property="og:site_name" content="CRASH LAB"><meta property="og:title" content="The Crank Boy"><meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="website">
<meta property="og:url" content="https://hartswf0.github.io/bolas/crank-boy/"><meta property="og:image" content="https://hartswf0.github.io/bolas/crank-boy/{esc(T["poster"])}">
<meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#0b0d10">
<link rel="icon" href="../favicon.svg" type="image/svg+xml"><link rel="icon" href="../favicon-32.png" sizes="32x32"><link rel="apple-touch-icon" href="../apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;800;900&family=JetBrains+Mono:wght@400;600&family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,600;1,7..72,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../assets/site.css">
<style>
.cb-hero{{display:grid;grid-template-columns:minmax(0,3fr) minmax(0,2fr);gap:22px;align-items:start;margin:10px 0 26px}}
.cb-hero video,.cb-card video{{display:block;width:100%;height:auto;aspect-ratio:16/9;background:#000;border:1.5px solid currentColor}}
.cb-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,320px),1fr));gap:24px 18px}}
.cb-card{{display:grid;gap:6px;align-content:start;min-width:0}}
.cb-card img,.cb-tile img{{display:block;width:100%;height:auto;aspect-ratio:16/10;object-fit:cover;border:1.5px solid currentColor}}
.cb-card b,.cb-tile b{{font-family:"Big Shoulders Display","Arial Narrow",Impact,sans-serif;font-weight:800;font-size:23px;line-height:1.02;text-transform:uppercase}}
.cb-card .line,.cb-tile span{{font-size:14.5px;line-height:1.42;opacity:.85}}
.cb-tiles{{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,260px),1fr));gap:20px 18px;margin-top:10px}}
.cb-tile{{display:grid;gap:5px;align-content:start;text-decoration:none;color:inherit;min-width:0}}
.cb-ops{{font-family:"JetBrains Mono",ui-monospace,monospace;font-size:11.5px;line-height:1.5;opacity:.8}}
.cb-links a,.cb-act a{{font-weight:600}}
.cb-act{{display:flex;gap:16px;flex-wrap:wrap;margin-top:12px}}
@media (max-width:760px){{.cb-hero{{grid-template-columns:1fr}}}}
</style></head><body>
<header class="top"><a class="brand" href="../"><img src="../favicon.svg" alt="" width="28" height="28"><span>CRASH LAB</span></a><nav>{nav}</nav></header>
<main class="wrap">
<p class="crumbs"><a href="../">CRASH LAB</a> / The Crank Boy</p>
<h1>The Crank Boy</h1>
<p>One postcard printed in France in about 1910, a school in the year 2000, and what grew from it: seven versions of a game built by AI programs, an opening film, and Futuretown, where the series' seven cards become short films, games and one playable town. Every film and game uses a different operator from the SCION animation swarms, and every one lets in real archive film from the cineosis-lab library, the way CINEOSIS does.</p>
<div class="cb-hero"><video controls preload="none" playsinline poster="{esc(T["poster"])}" src="{esc(T["film"])}" aria-label="The Town, the cartoon"></video>
<div><h2>The Town</h2><p>{esc(T["line"])}</p>
<div class="cb-act"><a href="shorts/world.html">Play the town</a><a href="shorts/index.html">Futuretown</a><a href="album.html">The album</a><a href="watch.html">Watch all {nfilms} films</a><a href="films.html">The film library</a><a href="kit.html">The kit</a><a href="https://github.com/hartswf0/crank-boy">Source</a></div></div></div>
<section class="sec"><div class="sechead"><h2>Also made</h2><p>a better Crank Boy, and the first proof of a new look</p></div>
<div class="cb-tiles">{tiles}</div>
<div class="cb-act"><a href="play/v9.html">Play version 9</a><a href="shorts/school-melies.html">The trick-film proof</a><a href="shorts/requests.html">The art department</a><a href="docs/futuretown.md">The write-up</a></div></section>
<section class="sec"><div class="sechead"><h2>Toward CINEOSIS</h2><p>the archive comes into the card</p></div>
<p>CINEOSIS sets the crash-test family inside unaltered archive shots. These films take shots from the same cineosis-lab library the other way round, into a surface the card already has: a mirror, a screen, a polished floor, a sky, a fire. Each short is proposed as a candidate passage for one of the 45 signs. That is a reading, not a result: none has yet had the blind review the CINEOSIS handmade passages had.</p></section>
<section class="sec"><div class="sechead"><h2>Films that go together</h2><p>{len(FI["works"])} works of two or more films, in order</p></div><p>Some subjects have more than one film. The school card has three (a short, a trick-film proof and the game played), and the Bolas films run in chains: the family in three, CINEOSIS in five passes, the Found Odyssey as a search for its look and then seven episodes, WYGWYL from one ink cel to a poem. <a href="films.html">The film library</a> shows each chain in order, with how each film follows the one before; each Bolas film page says the same.</p><ul>{worklist}</ul></section>
<section class="sec"><div class="sechead"><h2>Seven cards</h2><p>a film, a game and a place in the Town for each</p></div><div class="cb-grid">{cards}</div></section>
</main>
<footer class="foot"><div class="wrap"><p><b>CONSEQUENCE WORKS</b> · Watson Hartsoe · built with Claude</p><p>The Crank Boy is mirrored here from <a href="https://github.com/hartswf0/crank-boy">hartswf0/crank-boy</a>. Cards: En l'an 2000, attributed to Villemard, about 1910. Archive footage comes from the cineosis-lab library and is credited inside each film. Doodles: Quick, Draw! (Google Creative Lab, CC BY 4.0), chosen by Secondhand Motion.</p></div></footer>
</body></html>
'''
open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(page)

# the sitemap
sm = os.path.join(bolas, 'sitemap.xml')
if os.path.exists(sm):
    t = open(sm, encoding='utf-8').read()
    m = re.search(r'<loc>(https?://[^<]*?/)this-side-up/</loc>', t)
    base = m.group(1) if m else 'https://hartswf0.github.io/bolas/'
    add = ''.join(f'<url><loc>{base}crank-boy/{u}</loc></url>' for u in ['', 'album.html', 'watch.html', 'films.html', 'kit.html', 'shorts/', 'shorts/world.html', 'shorts/requests.html', 'play/v9.html'] if f'crank-boy/{u}</loc>' not in t)
    if add:
        t = t.replace('</urlset>', add + '</urlset>')
        open(sm, 'w', encoding='utf-8').write(t)
wj = os.path.join(bolas, 'tools/site/works.json')
if os.path.isdir(os.path.dirname(wj)):
    shutil.copyfile(os.path.join(root, 'registry/works.json'), wj)
    if os.path.exists(os.path.join(bolas, 'tools/site/works.py')):
        import subprocess
        subprocess.run([sys.executable, os.path.join(bolas, 'tools/site/works.py')], check=True)
nfiles = sum(len(fs) for _, _, fs in os.walk(out))
size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(out) for f in fs)
print(f'crank-boy/: {nfiles} files, {size / 1e6:.1f} MB; {n} pages marked as a mirror')
