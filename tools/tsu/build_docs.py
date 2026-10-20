"""Docs for the THIS SIDE UP case pages -> bolas/docs/{prompts,reviews,notes}: verbatim prompts (.txt + .html), every critic round's
brief and report (.md + .html), and the Trouttown validation notes. Same page template as the rest of docs/."""
import json, os, re, html, time, markdown, sys
sys.path.insert(0, os.path.dirname(__file__)); import data as D
B = '/home/claude/bolas/'; U = '/root/.claude/uploads/4fcf2301-cc19-5f90-be19-3bb1b3367fc1/'
C = json.load(open('/home/claude/tsu/record/critics.json'))
e = lambda s: html.escape(s, quote=True)
NAV = [('lab/', 'Try it'), ('family/', 'The Family'), ('cineosis/', 'CINEOSIS'), ('found-odyssey/', 'The Found Odyssey'), ('wygwyl/', 'WYGWYL'), ('this-side-up/', 'This Side Up'),
       ('films/', 'Films'), ('characters/', 'Characters'), ('process/', 'How it was made')]
def head(title, desc, url, root='../../', cur=None):
    nav = ''.join(f'<a href="{root}{h}"{" aria-current=page" if h == cur else ""}>{t}</a>' for h, t in NAV)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)} · CRASH LAB</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="https://hartswf0.github.io/bolas/{url}">
<meta property="og:site_name" content="CRASH LAB"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="https://hartswf0.github.io/bolas/{url}"><meta property="og:image" content="https://hartswf0.github.io/bolas/media/og.jpg">
<meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#0b0d10">
<link rel="icon" href="{root}favicon.svg" type="image/svg+xml"><link rel="icon" href="{root}favicon-32.png" sizes="32x32"><link rel="apple-touch-icon" href="{root}apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;800;900&family=JetBrains+Mono:wght@400;600&family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,600;1,7..72,400&display=swap" rel="stylesheet"><link rel="stylesheet" href="{root}assets/site.css"></head><body>
<header class="top"><a class="brand" href="{root}"><img src="{root}favicon.svg" alt="" width="28" height="28"><span>CRASH LAB</span></a><nav>{nav}</nav></header>
'''
FOOT = '''<footer class="foot"><div class="wrap"><p><b>CONSEQUENCE WORKS</b> · Watson Hartsoe · built with Claude</p><p>Every figure is keyed by hand in a rig and rendered from code. Archive footage comes from the cineosis-lab library and is credited inside each film. <a href="../../catalog.json">catalog.json</a> · <a href="../../sitemap.xml">sitemap</a> · <a href="https://github.com/hartswf0/bolas">source</a></p></div></footer>
</body></html>'''

# ---- prompts: number, slug, attachment, title, line
ATLAS_SUMMARY = '''World Labs announcement of Atlas, an "omni world model for spatial intelligence" (dated September 1, 2026), pasted into the session at Oct 18 11:13.

It is a third-party announcement, so it is summarised here rather than republished. What the rooftop runs took from it:

- Atlas makes and poses whole places, not single pictures: images2PosedRGBD returns an image with metric depth and a camera, and generation can be conditioned on posed views.
- So the rooftop could be asked for view by view along Boone's solved turntable orbit (every 5 degrees, 0 to 205), each batch conditioned on the posed roof and the most recent views.
- Every view comes with depth, which the composite uses to stand Boone at the orbit centre at the right scale.

The product appears on this site under its model name, Marble 2.
'''
PROMPTS = [
    (13, 'tempus-fugit-the-matrix-essay', 'de53a304', 'Tempus Fugit: the dodge and the refusal', 'the essay behind Tempus Fugit v1: bullet time as a question about time (image links removed)'),
    (14, 'tempus-fugit-howard-miller-clock', 'fb907176', 'Tempus Fugit: the Howard Miller clock', 'the inscription on the family clock, and Virgil, Georgics III.284'),
    (15, 'world-labs-atlas-announcement', None, 'Atlas: a summary', 'what the Marble rooftop runs took from the World Labs announcement'),
    (16, 'tempest-fugit', '829a8841', '"Tempest fugit"', 'tempus and tempest, and the full line from Virgil; the pun in FALL'),
    (17, 'trouttown-asset-compiler', '4cd40a23', 'SCION · registered assets and executable performance', 'the asset compiler and the interaction clip, for Trouttown: Tempus Fugit'),
    (18, 'trouttown-refinement', '866a770a', 'SCION · Trouttown: Tempus Fugit, refined', 'epistemic guardrails, the four plates, the archive mechanic'),
    (19, 'trouttown-watercourse', '92b42446', 'SCION · Trouttown: Tempus Fugit', 'the episode brief: the archive reveals a buried watercourse'),
    (20, 'watching-tempus-fugit-fall', 'e3f846e7', 'Watching Tempus Fugit: FALL', 'a reading of the posted FALL film, ported to Trouttown')]
def clean(t):
    t = re.sub(r'!\[[^\]]*\]\([^)]*\)', '[image link removed]', t)        # no stills from the reference film, no hotlinks
    return t
os.makedirs(B + 'docs/prompts', exist_ok=True)
for n, slug, att, title, line in PROMPTS:
    fn = f'{n:02d}-{slug}.txt'
    txt = ATLAS_SUMMARY if att is None else clean(open(U + f'{att}-attachment.txt').read())
    open(B + 'docs/prompts/' + fn, 'w').write(txt)
    when = 'Oct 18 11:13' if att is None else time.strftime('%b %d %H:%M', time.localtime(os.path.getmtime(U + f'{att}-attachment.txt')))
    eyebrow = 'Summary' if att is None else 'Prompt'
    body = (f'<main class="wrap"><p class="crumbs"><a href="../../">Home</a> / <a href="../../docs/">Docs</a> / {e(title)}</p><p class="eyebrow">{eyebrow} · pasted {when} · <a href="{fn}">{fn}</a></p>'
            f'<h1 style="font-size:clamp(36px,6vw,72px)">{e(title)}</h1><p class="lede">{e(line)}</p><pre class="prompt">{e(txt)}</pre></main>\n')
    open(B + f'docs/prompts/{fn}.html', 'w').write(head(title, line, f'docs/prompts/{fn}.html') + body + FOOT)

# ---- critic rounds
os.makedirs(B + 'docs/reviews', exist_ok=True); REV = []
def md_page(path_md, title, eyebrow, md, desc):
    open(B + path_md, 'w').write(md)
    hb = markdown.markdown(md, extensions=['tables', 'fenced_code', 'sane_lists'])
    url = path_md[:-3] + '.html'; fn = os.path.basename(path_md)
    body = f'<main class="wrap"><p class="crumbs"><a href="../../">Home</a> / <a href="../../docs/">Docs</a> / {e(title)}</p><p class="eyebrow">{eyebrow} · <a href="{fn}">{fn}</a></p><div class="md">{hb}</div></main>\n'
    open(B + url, 'w').write(head(title, desc, url) + body + FOOT)
    return url
def when(ts):
    import calendar
    return time.strftime('%b %d %H:%M', time.localtime(calendar.timegm(time.strptime(ts[:19], '%Y-%m-%dT%H:%M:%S'))))
for c in D.CASES:
    for r in c.get('rounds', []):
        for k, ci in enumerate(r['critics']):
            x = C[ci]; suf = '' if len(r['critics']) == 1 else '-' + 'ab'[k]
            path = f'docs/reviews/tsu-{c["slug"]}-round{r["n"]}{suf}.md'
            title = f'{c["title"]} · critic round {r["n"]}' + (f' · {x["desc"].lower()}' if len(r['critics']) > 1 else '')
            md = (f'# {title}\n\n*{x["desc"]}.* A separate agent that did not make the work, started {when(x["start"])} EDT. '
                  f'Brief and report verbatim. File paths in the brief are the working paths on the day.\n\n## The brief\n\n```\n{x["brief"].strip()}\n```\n\n## The report\n\n{x["report"].strip()}\n')
            url = md_page(path, title, 'Independent review', md, f'{c["title"]}: critic round {r["n"]}, brief and report.')
            r.setdefault('docs', []).append((url, x['desc'], when(x['start'])))
            REV.append((url, title, x['desc'], os.path.basename(path)))

# ---- trouttown notes
os.makedirs(B + 'docs/notes', exist_ok=True); NOTES = []
for src, slug, title in (('validation_log.md', 'validation-log', 'Trouttown: Tempus Fugit · validation log'), ('epistemic_ledger.md', 'epistemic-ledger', 'Trouttown: Tempus Fugit · epistemic ledger'),
                         ('limitations.md', 'limitations', 'Trouttown: Tempus Fugit · limitations')):
    md = open('/home/claude/lab/tfu/validation/' + src).read()
    url = md_page(f'docs/notes/trouttown-tempus-fugit-{slug}.md', title, 'Production notes', md, title)
    NOTES.append((url, title, f'trouttown-tempus-fugit-{slug}.md'))

# ---- docs index: one This Side Up section, replaced on every run
ix = open(B + 'docs/index.html').read()
ix = re.sub(r'<section id="tsu-docs">.*?</section>', '', ix, flags=re.S)
li = lambda href, t, d, f: f'<li><a href="{href}">{e(t)}</a><span class="d">{e(d)}</span><span class="f">{e(f)}</span></li>'
sec = ('<section id="tsu-docs"><h2>This Side Up</h2><p class="note">The prompts, critic rounds and notes behind the <a href="../this-side-up/">This Side Up</a> case pages.</p><ul class="doclist">'
       + ''.join(li(f'prompts/{n:02d}-{s}.txt.html', t, l, f'{n:02d}-{s}.txt') for n, s, a, t, l in PROMPTS)
       + ''.join(li(u[5:], t, d, f) for u, t, d, f in REV) + ''.join(li(u[5:], t, 'notes written beside the film', f) for u, t, f in NOTES) + '</ul></section>')
i = ix.find('<section><h2>References</h2>'); ix = ix[:i] + sec + ix[i:]
open(B + 'docs/index.html', 'w').write(ix)
json.dump({c['slug']: [r.get('docs', []) for r in c.get('rounds', [])] for c in D.CASES}, open('/home/claude/tsu/cases/review_docs.json', 'w'), indent=1)
print('prompts', len(PROMPTS), 'reviews', len(REV), 'notes', len(NOTES))
