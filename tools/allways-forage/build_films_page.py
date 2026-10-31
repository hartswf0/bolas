"""Build paeleo/allways/films/index.html: the screening room for ALLWAYS films.

Reads each films/<NNN-slug>/ folder (edl.json, mp4s, NOTES.md) and the SCION
registry for operator titles. Standard library only.
  python3 tools/allways-forage/build_films_page.py
"""
import html, json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILMS = ROOT / 'paeleo' / 'allways' / 'films'
SCION = {e['id']: e for e in json.loads((ROOT / 'paeleo/allways/scion/scion-allways.json').read_text())}
esc = html.escape


def dur(p):
    try:
        return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(p)]).decode())
    except Exception:
        return None


def first_para(md, heading):
    m = re.search(r'^## [^\n]*' + heading + r'[^\n]*\n+(.+?)(?=\n## |\Z)', md, re.S | re.M)
    if not m:
        return ''
    txt = m.group(1).strip().split('\n\n')[0]
    return re.sub(r'[*_`]', '', txt).replace('\n', ' ')


cards = []
STATUS = json.loads((FILMS / 'status.json').read_text()) if (FILMS / 'status.json').exists() else {}
for d in sorted(p for p in FILMS.iterdir() if p.is_dir() and re.match(r'\d{3}-', p.name)):
    n = int(d.name[:3]); op = SCION.get(n, {})
    edl = json.loads((d / 'edl.json').read_text()) if (d / 'edl.json').exists() else {}
    main = d / f'{d.name}.mp4'
    if not main.exists():
        continue
    md = (d / 'NOTES.md').read_text() if (d / 'NOTES.md').exists() else ''
    theorem = first_para(md, 'Theorem') or first_para(md, 'theorem')
    if (d / 'blurb.txt').exists():          # spoiler-free summary where the notes would give the film away
        theorem = (d / 'blurb.txt').read_text().strip()
    alts = sorted(p for p in d.glob(f'{d.name}-*.mp4'))
    title = d.name.split('-', 1)[1].replace('-', ' ').upper()   # never the edl title: WORDS must not show its word
    pp = d / 'poster.jpg'
    if not pp.exists():
        t0 = (dur(main) or 10) * 0.3
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t0:.2f}', '-i', str(main), '-frames:v', '1', '-q:v', '4', str(pp)])
    if len(theorem) > 420:
        cut = theorem[:420]; k = max(cut.rfind('. '), cut.rfind('? '))
        theorem = cut[:k + 1] if k > 120 else cut.rsplit(' ', 1)[0] + ' …'
    alt_links = ''.join(f'<a href="{d.name}/{esc(a.name)}">{esc(a.stem.replace(d.name + "-", ""))} ↗</a>' for a in alts)
    poster = f' poster="{d.name}/poster.jpg"'
    t = dur(main)
    cards.append(f'''<article class="film" id="f{n:03d}">
<div class="film-head"><span class="label">SCION {n:03d} · {esc(op.get("title", ""))}</span><h3>{esc(title)}</h3><span class="label">{t:.0f} s · archive footage · {esc(STATUS.get(d.name, 'critic review pending'))}</span></div>
<video controls preload="metadata" playsinline src="{d.name}/{main.name}"{poster}></video>
<p class="theorem">{esc(theorem)}</p>
<div class="links"><a href="{d.name}/NOTES.md">Forage log, cut and self-review ↗</a><a href="{d.name}/{main.stem}.ledger.json">Source ledger ↗</a><a href="{d.name}/edl.json">Edit list ↗</a>{alt_links}<a href="../operator.html#s{n}">Operator ↗</a></div>
<img class="strip" loading="lazy" src="{d.name}/contact.jpg" alt="Frame strip of {esc(title)}, one frame every two seconds">
</article>''')

page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>ALLWAYS · First batch</title>
<meta name="description" content="The first batch of ALLWAYS experimental films: SCION's conceptual microfilms (055–065), foraged and cut by hand from movingimagearchive.com footage.">
<meta name="theme-color" content="#f4f1e9"><link rel="icon" href="../../../favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../../../tools/paeleo/fonts/local.css"><link rel="stylesheet" href="../allways.css">
<style>
.films{{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,560px),1fr));gap:56px 48px;margin:40px 0 90px}}
.film video{{width:100%;aspect-ratio:4/3;background:#000;display:block;margin:12px 0 14px}}
.film h3{{font:600 clamp(40px,6vw,64px)/.95 var(--display);text-transform:uppercase;margin:6px 0}}
.film .theorem{{font-size:16px;color:var(--ink)}}
.film .links{{display:flex;flex-wrap:wrap;gap:6px 18px;font:12px/1.6 var(--mono)}}
.film .strip{{width:100%;margin-top:14px;opacity:.9}}
.intro{{max-width:820px;margin:48px 0 8px}}
.intro h1{{font:600 clamp(56px,10vw,120px)/.9 var(--display);text-transform:uppercase;margin:10px 0 24px}}
@media(max-width:640px){{.wrap{{width:calc(100% - 32px)}}}}
</style></head>
<body><a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="wrap sitebar"><div class="parents"><a href="../../../">CRASH LAB</a><span>/</span><a href="../../">PAELEO</a><span>/</span><a href="../">ALLWAYS</a><span>/ FILMS</span></div><nav aria-label="Films"><a href="../operator.html">SCION prompts</a><a href="../../../tools/allways-forage/README.md">Forage kit</a></nav></div></header>
<main id="main" class="wrap">
<section class="intro"><span class="label">ALLWAYS · first batch · conceptual microfilms</span><h1>Foraged,<br>cut by hand.</h1>
<p>Each film realises one SCION operator from the conceptual-microfilm family (055–065). Each is cut by hand from shots of public-domain educational, industrial, amateur and newsreel film on <a href="https://www.movingimagearchive.com">movingimagearchive.com</a>, as cached in <a href="https://hartswf0.github.io/cineosis-lab/">Cineosis Lab</a>.</p>
<p>These are <strong>proofs in progress</strong>, not released works. Every film keeps a source ledger, an edit list, the comparison cut its operator asks for, and a forage log of what the archive did and did not return. Eight have had a first round from an independent critic agent; the verdicts and repairs are in <a href="CRITIC-ROUND-1.md">CRITIC-ROUND-1.md</a>. No human critic has screened them yet.</p></section>
<div class="films">{"".join(cards)}</div>
</main></body></html>
'''
(FILMS / 'index.html').write_text(page)
print(FILMS / 'index.html', len(cards), 'films')
