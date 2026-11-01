#!/usr/bin/env python3
"""Build the run pages and the film case-study pages for every run listed in paeleo/allways/runs.json.

Reads   paeleo/allways/runs.json, works.json, scion/scion-allways.json,
        <run>/run.json, <run>/PROMPT.md, <run>/films/<slug>/film.json
Writes  <run>/index.html, <run>/films.json, <run>/films/<slug>/index.html

Python standard library only. See paeleo/allways/RUNS.md for the data each run supplies. Run from the repository root:
    python3 tools/allways/runs.py
"""
import html, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AW = ROOT / 'paeleo' / 'allways'
esc = html.escape
SITE = 'https://hartswf0.github.io/bolas/'
OPERATOR = SITE + 'paeleo/allways/operator.html'
RUNS_MD = 'https://github.com/hartswf0/bolas/blob/main/paeleo/allways/RUNS.md'
STATES = ['concept', 'proof in progress', 'proof reviewed', 'work in development', 'released']


def read_json(p, default=None):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return default


def chip(text, kind=''):
    return f'<span class="chip {kind}">{esc(text)}</span>' if text else ''


def verdict_kind(v):
    v = (v or '').lower()
    if v.startswith('pass'):
        return 'ok'
    if 'reference stronger' in v and 'leaning' not in v:
        return 'stronger'
    return 'mid'


def fmt_t(s):
    s = float(s or 0)
    return f'{int(s // 60)}:{s % 60:04.1f}' if s >= 60 else f'{s:.1f}s'


def head(title, desc, up, canonical):
    # up: relative path from the page back to the repository root
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{esc(canonical)}">
<meta name="theme-color" content="#f4f1e9"><link rel="icon" href="{up}favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{up}tools/paeleo/fonts/local.css"><link rel="stylesheet" href="{up}paeleo/allways/allways.css"><link rel="stylesheet" href="{up}paeleo/allways/run.css"></head>'''


def header(up, trail):
    return f'''<body id="top"><a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="wrap sitebar"><div class="parents"><a href="{up}">CRASH LAB</a><span>/</span><a href="{up}paeleo/">PAELEO</a><span>/</span><a href="{up}paeleo/allways/">ALLWAYS</a>{trail}</div><nav aria-label="ALLWAYS"><a href="{up}paeleo/allways/#runs">Runs</a><a href="{up}paeleo/allways/#works">Works</a><a href="{RUNS_MD}">Add a run</a></nav></div></header>'''


FOOT = '''<footer><div class="wrap"><div class="footer-row"><p>ALLWAYS · a cinema practice by Watson Hartsoe within PAELEO.<br>A run is a maker's attempt, not a released work.</p><div><a href="https://github.com/hartswf0/bolas/tree/main/paeleo/allways">GitHub</a><a class="back-top" href="#top">Back to the beginning ↑</a></div></div></div></footer>
<script>
document.querySelectorAll('[data-copy]').forEach(function(b){b.dataset.label=b.textContent;b.addEventListener('click',async function(){var el=document.getElementById(b.dataset.copy);try{await navigator.clipboard.writeText(el.textContent);b.textContent='Copied'}catch(e){var r=document.createRange();r.selectNodeContents(el);var s=getSelection();s.removeAllRanges();s.addRange(r);b.textContent='Selected: copy it now'}setTimeout(function(){b.textContent=b.dataset.label},2200)})});
document.querySelectorAll('[data-save]').forEach(function(b){b.addEventListener('click',function(){var el=document.getElementById(b.dataset.save);var a=document.createElement('a');a.href=URL.createObjectURL(new Blob([el.textContent],{type:'text/markdown'}));a.download=b.dataset.name;document.body.appendChild(a);a.click();a.remove()})});
</script></body></html>'''


def promptbox(pid, text, name, label='Copy prompt'):
    return f'''<div class="promptbox"><div class="prompt-actions"><button type="button" data-copy="{pid}">{esc(label)}</button><button type="button" data-save="{pid}" data-name="{esc(name)}">Save .md</button><span class="label">{len(text.split()):,} words</span></div><pre id="{pid}" tabindex="0">{esc(text)}</pre></div>'''


def load_all():
    reg = read_json(AW / 'runs.json', {'runs': []})['runs']
    works = read_json(AW / 'works.json')['works']
    scion = {e['id']: e for e in read_json(AW / 'scion' / 'scion-allways.json', [])}
    runs = []
    for r in reg:
        base = ROOT / r['path'].strip('/')
        meta = {**r, **(read_json(base / 'run.json', {}) or {})}
        films = {}
        for w in works:
            fj = read_json(base / 'films' / w['slug'] / 'film.json') if r.get('kind') != 'linked' else None
            if fj:
                films[w['slug']] = fj
        runs.append({'reg': r, 'meta': meta, 'dir': base, 'films': films, 'prompt': (base / 'PROMPT.md').read_text() if (base / 'PROMPT.md').exists() else '', 'linked': r.get('kind') == 'linked'})
    return runs, works, scion


def film_prompt(run, work, scion):
    s = scion.get(work['primary'], {})
    sup = ', '.join(f"SCION {n} · {scion[n]['title']}" for n in work['supporting'] if n in scion)
    crit = '\n'.join('- ' + c for c in s.get('acceptance_criteria', []))
    block = f'''---

## This film

**Title:** {work['title']} ({work['subtitle']})

**Concept:** {work['logline']}

**First proof:** {work['proof']}

**Development boundary:** {work['note']}

**Primary operator:** SCION {work['primary']} · {s.get('title', '')}. Full operator prompt: {OPERATOR}#s{work['primary']}
**Supporting:** {sup}

**Operator's creative theorem:** {s.get('creative_theorem', '')}

**Acceptance criteria (from the operator):**
{crit}
'''
    method = run['prompt']
    if '\n---\n' in method:                      # the front matter explains the file; the prompt starts after the rule
        method = method.split('\n---\n', 1)[1]
    return (method.strip() + '\n\n' + block).strip() + '\n'


def shot_rows(shots):
    out = []
    for i, s in enumerate(shots, 1):
        src = esc(str(s.get('source') or ''))
        if s.get('url'):
            src = f'<a href="{esc(s["url"])}">{src}</a>'
        side = f' <span class="dim">{esc(s["side"])}</span>' if s.get('side') else ''
        snd = ''.join(f'<div class="dim">sound: {esc(str(x.get("source")))} ({x.get("year") or "undated"}) {x.get("source_in", 0):.1f}–{x.get("source_out", 0):.1f}</div>' if not x.get('authored') else f'<div class="dim">sound: {esc(str(x.get("source")))}</div>' for x in s.get('sound_from', []))
        tr = ''.join(f'<div class="dim">{esc(t)}</div>' for t in s.get('transforms', []))
        pos = s.get('position') or s.get('pair') or i
        out.append(f'<tr><td>{pos}</td><td>{fmt_t(s.get("at"))}<br><span class="dim">{s.get("dur", 0):.1f}s</span></td><td>{src} <span class="dim">{s.get("year") or "undated"}</span>{side}{tr}{snd}</td><td>{s.get("source_in", 0):.1f}–{s.get("source_out", 0):.1f}</td><td>{esc(s.get("why", ""))}</td></tr>')
    return ''.join(out)


def img(src, cap, cls=''):
    return f'<figure class="{cls}"><a href="{esc(src)}"><img src="{esc(src)}" alt="{esc(cap)}" loading="lazy"></a><figcaption>{esc(cap)}</figcaption></figure>'


def film_page(run, work, f, scion, prev, nxt, runs):
    depth = len(Path(run['reg']['path'].strip('/')).parts)
    up = '../' * (depth + 2)
    meta = run['meta']
    slug = work['slug']
    v = f.get('video', {})
    reviews = f.get('reviews', [])
    last = reviews[-1] if reviews else {}
    crit = ''.join(f'<li>{esc(c)}</li>' for c in scion.get(work['primary'], {}).get('acceptance_criteria', []))
    methods = ' · '.join(f'<a href="{OPERATOR}#s{n}">SCION {n}</a>' for n in [work['primary'], *work['supporting']])
    stats = [(len(f.get('searches', [])), 'searches'), (len(f.get('looks', [])), 'filmstrips looked at'), (len(f.get('shots', [])), 'shots'), (len(reviews), 'review rounds')]
    stat_html = ''.join(f'<div><b>{n}</b><span>{esc(l)}</span></div>' for n, l in stats if n)
    searches = ''.join(img(s['sheet'], f'{s["q"]} · {s["results"]} results', 'sheet') for s in f.get('searches', []))
    looks = ''.join(f'<figure class="strip {"used" if l.get("in_cut") else ""}"><a href="{esc(l["img"])}"><img src="{esc(l["img"])}" alt="{esc(l["label"])}" loading="lazy"></a><figcaption>{esc(l["label"])} · {"in the cut" + (" (shot " + ", ".join(str(x) for x in l["used"]) + ")" if l.get("used") else " for its sound") if l.get("in_cut") else "looked at, not used"}</figcaption></figure>' for l in f.get('looks', []))
    extras = ''
    for e in f.get('extras', []):
        imgs = ''.join(img(i['src'], i.get('caption', ''), 'sheet') for i in e.get('images', []))
        vid = f'<figure class="extra-video"><video controls preload="metadata" src="{esc(e["video"]["src"])}"></video><figcaption>{esc(e["video"].get("caption", ""))}</figcaption></figure>' if e.get('video') else ''
        extras += f'<section class="step"><h2>{esc(e["title"])}</h2>{e.get("html", "")}{vid}<div class="sheets">{imgs}</div></section>'
    rv = ''
    for r in reviews:
        pk = r.get('packet', {})
        pk_html = ''
        if pk.get('sheet'):
            pk_html = f'<p class="dim">What the critic was given: {esc(pk.get("note", ""))}. <a href="{esc(pk["sheet"])}">the contact sheet</a>{" · <a href=" + chr(34) + esc(pk["transcript"]) + chr(34) + ">the transcript</a>" if pk.get("transcript") else ""}.</p><a href="{esc(pk["sheet"])}"><img class="packet" src="{esc(pk["sheet"])}" alt="Contact sheet given to the critic" loading="lazy"></a>'
        elif pk.get('note'):
            pk_html = f'<p class="dim">{esc(pk["note"])}</p>'
        bn = f'<div class="builder"><b>The builder, after reading it</b><p>{esc(r["builder_note"])}</p></div>' if r.get('builder_note') else ''
        rv += f'<article class="review"><h3>Round {r.get("round")} {chip(r.get("verdict"), verdict_kind(r.get("verdict")))}</h3><p class="dim">{esc(r.get("who", ""))}. Its report, verbatim:</p><details open><summary>The report</summary><pre class="report">{esc(r.get("text", ""))}</pre></details>{pk_html}{bn}</article>'
    notes = f.get('notes', {})
    cols = ''.join(f'<div><h3>{t}</h3><ul>{"".join("<li>" + esc(x) + "</li>" for x in notes.get(k, []))}</ul></div>' for k, t in (('worked', 'What worked'), ('failed', 'What failed'), ('open', 'What is still open')) if notes.get(k))
    repairs = f'<h3>Repairs after review</h3><ul>{"".join("<li>" + esc(x) + "</li>" for x in f["repairs"])}</ul>' if f.get('repairs') else ''
    files = ''.join(f'<li><a href="{esc(x["path"])}">{esc(x["path"])}</a> <span class="dim">{esc(x.get("label", ""))}</span></li>' for x in f.get('files', []))
    others = ''
    for o in runs:
        if o is run or slug not in o['films']:
            continue
        of = o['films'][slug]
        ov = (of.get('reviews') or [{}])[-1].get('verdict', '')
        others += f'<a class="xrun" href="{up}{o["reg"]["path"].strip("/")}/films/{slug}/"><img src="{up}{o["reg"]["path"].strip("/")}/films/{slug}/{of.get("video", {}).get("poster", "poster.jpg")}" alt="" loading="lazy"><b>{esc(o["meta"].get("name", o["reg"]["id"]))}</b><span>{esc(of.get("state", ""))}{" · " + esc(ov) if ov else ""}</span></a>'
    others = f'<div class="xruns">{others}</div>' if others else '<p class="dim">No other run has made this film yet. <a href="' + RUNS_MD + '">How to add one</a>.</p>'
    nav = ''.join(x for x in (f'<a href="../{prev["slug"]}/">← {esc(prev["title"])}</a>' if prev else '', f'<a href="../{nxt["slug"]}/">{esc(nxt["title"])} →</a>' if nxt else '') if x)
    pid = 'fp-' + slug
    body = f'''<main id="main" class="wrap film">
<div class="film-top"><span class="label">{esc(meta.get('name', run['reg']['id']))} · case study</span>{chip(f.get('state'), 'state')}{chip(last.get('verdict'), verdict_kind(last.get('verdict'))) if last else ''}</div>
<h1 class="film-title">{esc(work['title'])}</h1><p class="film-sub">{esc(work['subtitle'])} · {methods}</p>
<div class="player"><video controls preload="metadata" poster="{esc(v.get('poster', 'poster.jpg'))}" src="{esc(v.get('src', slug + '.mp4'))}"></video><p class="dim">{v.get('duration', 0):.0f} s{(' · ' + esc(v['card'])) if v.get('card') else ''}. I cannot hear; neither could the critics. Sound is unjudged until a person listens.</p></div>
<p class="lede">{esc(f.get('summary', ''))}</p><div class="stats">{stat_html}</div>
<section class="step"><h2><span>1</span> The brief</h2><p>{esc(work['logline'])}</p><p><b>First proof.</b> {esc(work['proof'])}</p><p class="dim"><b>Development boundary.</b> {esc(work['note'])}</p>{('<h3>The operator&rsquo;s acceptance criteria</h3><ul>' + crit + '</ul>') if crit else ''}</section>
<section class="step"><h2><span>2</span> The prompt</h2><p>The method prompt for this run, followed by this film's inputs. Paste it into an agent with a shell, ffmpeg, a speech recognizer and image reading. It is a reconstruction of what the run did, written afterwards; the run itself began from a short request.</p>{promptbox(pid, film_prompt(run, work, scion), 'allways-' + slug + '-prompt.md')}</section>
{('<section class="step"><h2><span>3</span> What was searched</h2><p>One search at a time, in plain visible-action language. Each sheet is what came back: numbered thumbnails with duration, year and title. These are the images the maker looked at (or, where it could not, see the note below).</p><div class="sheets">' + searches + '</div></section>') if searches else ''}
{('<section class="step"><h2><span>4</span> What was looked at closely</h2><p>A time-coded filmstrip and waveform for each candidate. Outlined strips are in the cut.</p><div class="strips">' + looks + '</div></section>') if looks else ''}
<section class="step"><h2><span>5</span> The cut</h2>{('<p>The finished film, shot by shot (first, middle and last frame of each):</p>' + img(f['reel'], 'The final cut as a contact sheet', 'reel')) if f.get('reel') else ''}<p>Every shot, where it came from, and why it is here. Source seconds are in the original film. Links go to the archive's own copy of the clip.</p><div class="w"><table class="shots"><thead><tr><th>#</th><th>at</th><th>source</th><th>src s</th><th>why</th></tr></thead><tbody>{shot_rows(f.get('shots', []))}</tbody></table></div></section>
{extras}
{('<section class="step"><h2><span>6</span> Review</h2><p>A fresh agent was given only a timecoded contact sheet of the film, a transcript with loudness, and the brief. Not the edit list, the ledger, or these reasons. It cannot hear.</p>' + rv + '</section>') if rv else ''}
<section class="step"><h2><span>7</span> What happened</h2>{repairs}<div class="cols">{cols}</div></section>
<section class="step"><h2><span>8</span> Files</h2><ul class="files">{files}<li><a href="film.json">film.json</a> <span class="dim">this page's data</span></li></ul></section>
<section class="step"><h2><span>9</span> Other runs of this film</h2>{others}</section>
<nav class="film-nav" aria-label="Films in this run"><a href="../../">All films in {esc(meta.get('name', run['reg']['id']))}</a>{nav}</nav></main>'''
    return head(f'{work["title"]} · {meta.get("name", run["reg"]["id"])} · ALLWAYS', f.get('summary', work['logline']), up, f'{SITE}{run["reg"]["path"].strip("/")}/films/{slug}/') + header(up, f'<span>/</span><a href="../../">{esc(run["reg"]["id"])}</a><span>/ {esc(work["title"])}</span>') + body + FOOT


def run_page(run, works, scion):
    up = '../' * len(Path(run['reg']['path'].strip('/')).parts)
    m = run['meta']
    films = []
    for w in works:
        f = run['films'].get(w['slug'])
        if not f:
            continue
        rv = f.get('reviews', [])
        films.append({'slug': w['slug'], 'title': w['title'], 'state': f.get('state', ''), 'verdict': rv[-1].get('verdict', '') if rv else '', 'duration': f.get('video', {}).get('duration', 0), 'poster': f'films/{w["slug"]}/{f.get("video", {}).get("poster", "poster.jpg")}', 'rounds': len(rv), 'searches': len(f.get('searches', [])), 'shots': len(f.get('shots', []))})
    (run['dir'] / 'films.json').write_text(json.dumps({'films': films}, indent=1))
    cards = ''.join(f'<a class="film-card" href="films/{x["slug"]}/"><img src="{x["poster"]}" alt="" loading="lazy"><div><b>{esc(x["title"])}</b><span class="dim">{esc(next(w["subtitle"] for w in works if w["slug"] == x["slug"]))} · {x["duration"]:.0f} s</span><div>{chip(x["state"], "state")}{chip(x["verdict"], verdict_kind(x["verdict"]))}</div><span class="dim">{x["searches"]} searches · {x["shots"]} shots · {x["rounds"]} review round{"s" if x["rounds"] != 1 else ""}</span></div></a>' for x in films)
    per = m.get('perception', {})
    perc = f'<dl class="kv"><dt>Could see images</dt><dd>{"yes" if per.get("sees") else "no"}</dd><dt>Could hear audio</dt><dd>{"yes" if per.get("hears") else "no"}</dd></dl><p>{esc(per.get("notes", ""))}</p>' if per else ''
    roles = ''.join(f'<li><b>{esc(r["role"])}</b> {esc(r["who"])}</li>' for r in m.get('roles', []))
    cav = ''.join(f'<li>{esc(c)}</li>' for c in m.get('caveats', []))
    fnd = ''.join(f'<li>{esc(c)}</li>' for c in m.get('findings', []))
    tools = sorted(p.name for p in (run['dir'] / 'tools').glob('*.py')) if (run['dir'] / 'tools').exists() else []
    tl = ''.join(f'<li><a href="tools/{esc(t)}">{esc(t)}</a></li>' for t in tools)
    body = f'''<main id="main" class="wrap run">
<section class="run-hero"><span class="label">ALLWAYS / run</span><h1 class="film-title">{esc(m.get('id', ''))}</h1><p class="film-sub">{esc(m.get('maker', ''))} · {esc(m.get('date', ''))}</p><p class="lede">{esc(m.get('summary', ''))}</p>{('<p class="dim"><b>The request.</b> ' + esc(m['request']) + '</p>') if m.get('request') else ''}</section>
{('<section class="step warn"><h2>Read this before trusting the films</h2><ul>' + cav + '</ul></section>') if cav else ''}
<section class="step"><h2>The films</h2><div class="film-grid">{cards}</div></section>
<section class="step"><h2>The method prompt</h2><p>Paste this into an agent, then add one film's inputs; each film's case-study page does that for you. Change one step and compare.</p>{promptbox('run-prompt', run['prompt'], m.get('id', 'run') + '-PROMPT.md', 'Copy method prompt') if run['prompt'] else ''}</section>
{('<section class="step"><h2>What this run learned</h2><ul>' + fnd + '</ul></section>') if fnd else ''}
<section class="step"><h2>Who did what, and what they could perceive</h2>{('<ul>' + roles + '</ul>') if roles else ''}{perc}</section>
{('<section class="step"><h2>Tools</h2><p>The code used. It renders, measures and records; it never chooses a shot.</p><ul class="files">' + tl + '</ul></section>') if tl else ''}
<section class="step"><h2>Other runs</h2><p>Gemini, Argon, Sol and other makers add their own run beside this one. <a href="{RUNS_MD}">How to add a run</a>. <a href="{up}paeleo/allways/#runs">All runs, on the ALLWAYS page</a>.</p></section></main>'''
    return head(f'{m.get("id", "run")} · ALLWAYS runs', m.get('summary', ''), up, f'{SITE}{run["reg"]["path"].strip("/")}/') + header(up, f'<span>/ {esc(m.get("id", ""))}</span>') + body + FOOT


def main():
    runs, works, scion = load_all()
    wl = [dict(w) for w in works]
    for run in runs:
        if run['linked']:
            continue
        (run['dir'] / 'index.html').write_text(run_page(run, works, scion))
        for i, w in enumerate(wl):
            f = run['films'].get(w['slug'])
            if not f:
                continue
            prev = next((wl[j] for j in range(i - 1, -1, -1) if wl[j]['slug'] in run['films']), None)
            nxt = next((wl[j] for j in range(i + 1, len(wl)) if wl[j]['slug'] in run['films']), None)
            (run['dir'] / 'films' / w['slug'] / 'index.html').write_text(film_page(run, w, f, scion, prev, nxt, runs))
    print(json.dumps({'runs': [r['reg']['id'] for r in runs], 'film_pages': sum(len(r['films']) for r in runs)}))


if __name__ == '__main__':
    main()
