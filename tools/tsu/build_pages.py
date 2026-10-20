"""THIS SIDE UP case pages -> bolas/this-side-up/<slug>/index.html, in the format of the process pages (site.css) plus cases.css.
Reads data.py (the record), media/case/manifest.json (built media), review_docs.json (critic doc pages), compare.json (frame grids)."""
import os, sys, json, time, html, re
sys.path.insert(0, os.path.dirname(__file__)); import data as D
from build_docs import head, PROMPTS
B = '/home/claude/bolas/'; T = B + 'this-side-up/'
MAN = json.load(open(T + 'media/case/manifest.json')); RD = json.load(open('/home/claude/tsu/cases/review_docs.json'))
CMP = json.load(open(T + 'media/case/compare.json')) if os.path.exists(T + 'media/case/compare.json') else {}
CR = json.load(open('/home/claude/tsu/record/critics.json'))
e = lambda s: html.escape(str(s), quote=True)
R = '../../'; TS = '../'
fmt = lambda t: time.strftime('%b %d %H:%M', time.localtime(t))
def mmss(d): d = int(round(d)); return f'{d // 60}:{d % 60:02d}'
PNUM = {s: n for n, s, *_ in PROMPTS}
def prompt_file(slug):
    for f in os.listdir(B + 'docs/prompts'):
        if f.endswith('.html') and f.startswith(slug + '.'): return f[:-5]
    raise KeyError(slug)
FOOT = '''<footer class="foot"><div class="wrap"><p><b>CONSEQUENCE WORKS</b> · Watson Hartsoe · built with Claude</p><p>Every figure is keyed by hand in a rig and rendered from code. Archive footage comes from the cineosis-lab library and is credited inside each film. The Matrix rooftop scene was measured, not shown: no frame of it appears on this site. <a href="../../docs/">documents and prompts</a> · <a href="../../sitemap.xml">sitemap</a> · <a href="https://github.com/hartswf0/bolas">source</a></p></div></footer>'''
LB = '''<div class="lb" hidden><button class="lbx" aria-label="Close">Close</button><button class="lbp" aria-label="Previous">&larr;</button><img alt=""><p></p><button class="lbn" aria-label="Next">&rarr;</button></div>
<script>(()=>{const L=document.querySelector('.lb'),I=L.querySelector('img'),P=L.querySelector('p');let a=[],k=0;
const show=n=>{a=[...document.querySelectorAll('[data-lb]')].filter(x=>x.offsetParent);k=(n+a.length)%a.length;const x=a[k];I.src=x.href;P.textContent=(k+1)+' / '+a.length+'  ·  '+(x.querySelector('img')||{}).alt;L.hidden=false;document.body.style.overflow='hidden'};
const hide=()=>{L.hidden=true;document.body.style.overflow=''};
document.addEventListener('click',ev=>{const x=ev.target.closest('[data-lb]');if(x){ev.preventDefault();a=[...document.querySelectorAll('[data-lb]')].filter(y=>y.offsetParent);show(a.indexOf(x))}});
L.querySelector('.lbx').onclick=hide;L.querySelector('.lbp').onclick=()=>show(k-1);L.querySelector('.lbn').onclick=()=>show(k+1);L.onclick=ev=>{if(ev.target===L)hide()};
document.addEventListener('keydown',ev=>{if(L.hidden)return;if(ev.key==='Escape')hide();if(ev.key==='ArrowLeft')show(k-1);if(ev.key==='ArrowRight')show(k+1)});
document.querySelectorAll('video').forEach(v=>v.addEventListener('play',()=>document.querySelectorAll('video').forEach(o=>{if(o!==v)o.pause()})))})()</script>'''
def fig(sh, cap, cls=''):
    f = sh['file']; return (f'<figure{cls}><a href="{TS}{f}" data-lb><img src="{TS}{f}" alt="{e(cap)}" loading="lazy" width="{sh["w"]}" height="{sh["h"]}"></a>'
                            f'<figcaption>{e(cap)}<span>{fmt(sh["t"])}</span></figcaption></figure>')
def vclass(v):
    v = v.lower()
    if v.startswith('pass') or 'fit as' in v: return 'pass'
    if 'partial' in v or 'near miss' in v: return 'part'
    return 'fail'

def page(i, c):
    m = MAN[c['slug']]; n = len(D.CASES); slug = c['slug']
    vers = c['versions']; rounds = c.get('rounds', []); prompts = c.get('prompts', []); sheets = c['sheets']
    nfilm = sum(1 for v in vers if v['id'] in m['versions'])
    counts = [f'{len(vers)} versions', f'{len(rounds)} critic rounds' if rounds else None, f'{len(prompts) + len(c.get("feedback", []))} prompts and notes' if prompts or c.get('feedback') else None, f'{len([x for x in sheets if not isinstance(x, str)])} sheets']
    counts = [x for x in counts if x]
    o = [head(f'{c["code"]} · {c["title"]}', c['question'], f'this-side-up/{slug}/', R, 'this-side-up/').replace('</head>', f'<link rel="stylesheet" href="../cases.css"></head>')]
    o.append(f'<main class="wrap tsu"><p class="crumbs"><a href="{R}">Home</a> / <a href="{TS}">This Side Up</a> / {c["code"]}</p><article class="case" style="--c:#b8834a">')
    o.append(f'<section class="hero casehero"><p class="eyebrow" style="color:#b8834a">{c["code"]} · case {i + 1} of {n} · This Side Up</p><h1 class="ft">{e(c["title"])}</h1>'
             f'<p class="question">{e(c["question"])}</p><p class="lede">{e(c["lede"])}</p><p class="meta">{" · ".join(counts)} · {e(c["when"])}</p></section>')
    o.append('<nav class="casemap" aria-label="All This Side Up cases">' + ''.join(
        f'<a href="{TS}{x["slug"]}/" style="--c:#b8834a"{" aria-current=page" if x is c else ""} title="{e(x["title"])}">{x["code"][4:]}</a>' for x in D.CASES) + '</nav>')
    toc = [('versions', 'Versions', len(vers))]
    if CMP.get(slug): toc.append(('compare', 'Same moment', None))
    if prompts or c.get('feedback'): toc.append(('prompts', 'Prompts', len(prompts) + len(c.get('feedback', []))))
    if rounds: toc.append(('critics', 'Critics', len(rounds)))
    toc += [('sheets', 'Sheets', len([x for x in sheets if not isinstance(x, str)]))]
    if c['fixes']: toc.append(('fixes', 'What broke', len(c['fixes'])))
    toc.append(('record', 'Record', None))
    o.append('<ul class="contents">' + ''.join(f'<li><a href="#{a}">{t}{f"<b>{k}</b>" if k else ""}</a></li>' for a, t, k in toc) + '</ul>')
    # method / teaches
    o.append('<div class="casebody"><section class="block"><h2>How it was made</h2><ol class="method">' + ''.join(f'<li>{e(x)}</li>' for x in c['method']) + '</ol></section>')
    o.append('<section class="block teach"><h2>What this case teaches</h2><ol>' + ''.join(f'<li>{e(x)}</li>' for x in c['teaches']) + f'</ol><p class="vs"><b>How it differs.</b> {e(c["vs"])}</p></section></div>')
    if c.get('keys'):
        o.append('<section class="sec"><div class="sechead"><h2>The five keys</h2><p>Observed means photographed; authored means made from the photograph.</p></div><table class="keys"><tr><th>Key</th><th>Time</th><th>Pose</th><th>Source</th></tr>'
                 + ''.join(f'<tr><td>{k}</td><td>{t}</td><td>{e(nm)}</td><td>{e(s)}</td></tr>' for k, t, nm, s in c['keys']) + '</table></section>')
    # versions
    o.append(f'<section class="sec" id="versions"><div class="sechead"><h2>Versions, in order</h2><p>Every cut that was rendered, oldest first, with what changed from the one before. Videos are 640 px web encodes.</p></div>')
    if c.get('lost'): o.append(f'<p class="lost">{e(c["lost"])}</p>')
    o.append('<ol class="vtl">')
    for k, v in enumerate(vers):
        mv = m['versions'].get(v['id']); when = v.get('when') or (fmt(mv['t']) if mv else '')
        meta = [when] + ([mmss(mv['dur'])] if mv else [])
        if v.get('critic') is not None:
            rn = next((r['n'] for r in rounds if v['critic'] in r['critics']), None)
            if rn: meta.append(f'<a href="#round{rn}">reviewed in critic round {rn}</a>')
        o.append('<li class="ver" id="v-' + v['id'] + '">')
        if v.get('feedback'):
            o.append(f'<div class="note-in"><p class="who">Watson&rsquo;s note, before this cut</p><q>{e(v["feedback"])}</q></div>')
        o.append(f'<div class="vh"><span class="vn">{k + 1:02d}</span><h3>{e(v["title"])}</h3><span class="vm">{" · ".join(meta)}</span>'
                 + ('<span class="rr">re-rendered Oct 20 from the saved script</span>' if v.get('rerender') else '') + '</div>')
        if mv:
            o.append(f'<video controls preload="none" playsinline poster="{TS}{mv["poster"]}" src="{TS}{mv["file"]}" width="640" height="360"></video>')
        else:
            o.append('<div class="novid">No film kept for this version.<br>Its frames are under Critics and Sheets.</div>')
        o.append(f'<div class="vt"><p>{e(v["note"])}</p>')
        if v.get('changed'):
            o.append('<p class="chg">What changed</p><ul>' + ''.join(f'<li>{e(x)}</li>' for x in v['changed']) + '</ul>')
        o.append('</div></li>')
    o.append('</ol></section>')
    # compare grid
    if CMP.get(slug):
        g = CMP[slug]
        o.append(f'<section class="sec" id="compare"><div class="sechead"><h2>{e(g["title"])}</h2><p>{e(g["note"])}</p></div><div class="cmp"><table><tr><th></th>'
                 + ''.join(f'<th>{e(t)}</th>' for t in g['cols']) + '</tr>')
        for row in g['rows']:
            o.append(f'<tr><th>{e(row["label"])}</th>' + ''.join(f'<td><a href="{TS}{f}" data-lb><img src="{TS}{f}" alt="{e(row["label"])} at {e(col)}" loading="lazy" width="320" height="180"></a></td>' for f, col in zip(row['files'], g['cols'])) + '</tr>')
        o.append('</table></div></section>')
    # prompts
    if prompts or c.get('feedback'):
        o.append('<section class="sec" id="prompts"><div class="sechead"><h2>Prompts and notes</h2><p>What was pasted into the session, in order, and what each one did. Full text verbatim; each also has its own page under Docs.</p></div>')
        for slug_p, when, what in prompts:
            f = prompt_file(slug_p); txt = open(B + 'docs/prompts/' + f).read()
            title = re.search(r'<h1[^>]*>(.*?)</h1>', open(B + 'docs/prompts/' + f + '.html').read()).group(1)
            o.append(f'<div class="prm"><div class="ph"><b>{title}</b><span>pasted {when} · <a href="{R}docs/prompts/{f}.html">{f}</a></span></div><p>{e(what)}</p>'
                     f'<details><summary>Read it all ({len(txt.split()):,} words)</summary><pre class="prompt">{e(txt)}</pre></details></div>')
        for when, q, vid in c.get('feedback', []):
            vt = next(v['title'] for v in vers if v['id'] == vid)
            o.append(f'<div class="prm"><div class="ph"><b>Watson&rsquo;s note · {e(when)}</b><span>became <a href="#v-{vid}">{e(vt)}</a></span></div><p><q>{e(q)}</q></p></div>')
        o.append('</section>')
    # critics
    if rounds:
        o.append('<section class="sec" id="critics"><div class="sechead"><h2>Critic rounds</h2><p>Each round is a separate agent that did not make the work and had not seen the earlier rounds. It saw only the sheet shown, plus any frames it pulled itself. The brief and the report are verbatim.</p></div><div class="rounds">')
        docs = RD.get(slug, [])
        for k, r in enumerate(rounds):
            dd = docs[k] if k < len(docs) else []
            sh = m['sheets'].get(r['sheet'])
            o.append(f'<div class="round" id="round{r["n"]}"><div class="rh"><h3>Round {r["n"]}</h3><span class="verdict {vclass(r["verdict"])}">{e(r["verdict"])}</span><span class="vm">{" · ".join(x[2] for x in dd[:1])}</span></div>')
            if sh is None:
                # the reviewed sheet isn't in the sheet list: add it on the fly from the manifest key written by build_media (sheet file)
                sh = m.get('round_sheets', {}).get(r['sheet'])
            o.append(fig(sh, f'From what round {r["n"]} was shown.') if sh else '<div></div>')
            o.append('<div><ul>' + ''.join(f'<li>{e(x)}</li>' for x in r['found']) + '</ul>' + f'<p class="next"><b>What changed next.</b> {e(r["changed"])}</p>')
            o.append('<p class="src">' + ' · '.join(f'<a href="{R}{u}">{e(d)}</a>' for u, d, w in dd) + '</p>')
            for ci in r['critics']:
                x = CR[ci]
                o.append(f'<details><summary>{e(x["desc"])}: brief</summary><pre>{e(x["brief"].strip())}</pre></details><details><summary>{e(x["desc"])}: report</summary><pre>{e(x["report"].strip())}</pre></details>')
            o.append('</div></div>')
        o.append('</div></section>')
    # sheets, grouped by working session
    groups = []; label = None
    for x in sheets:
        if isinstance(x, str): groups.append([x, []]); continue
        p, cap = x
        if p not in m['sheets']: continue
        if not groups: groups.append([None, []])
        groups[-1][1].append((m['sheets'][p], cap))
    groups = [(l, sorted(g, key=lambda y: y[0]['t'])) for l, g in groups if g]
    o.append('<section class="sec sheetsteps" id="sheets"><div class="sechead"><h2>The sheets, step by step</h2><p>Grouped by stage of the work, with the time each file was written. Click any sheet to see it full size; the arrow keys move through them.</p></div>')
    for k, (label, g) in enumerate(groups):
        t0, t1 = fmt(g[0][0]['t']), fmt(g[-1][0]['t'])
        o.append(f'<section class="step"><div class="stephead"><span class="sn">Step {k + 1}</span><b>{e(label or 'Sheets')}</b><span>{t0}{(" to " + (t1[7:] if t1[:6] == t0[:6] else t1)) if t1 != t0 else ""} · {len(g)} sheet{"s" if len(g) > 1 else ""}</span></div>')
        o.append('<div class="stepgrid">' + ''.join(fig(sh, cap) for sh, cap in g[:6]) + '</div>')
        if len(g) > 6: o.append(f'<details><summary>Show {len(g) - 6} more from this step</summary><div class="stepgrid">' + ''.join(fig(sh, cap) for sh, cap in g[6:]) + '</div></details>')
        o.append('</section>')
    o.append('</section>')
    # fixes, record, carry
    o.append('<div class="casebody">')
    if c['fixes']:
        o.append('<section class="block" id="fixes"><h2>What broke and what changed</h2><ul class="fixes">' + ''.join(f'<li><span class="pb">{e(a)}</span><span class="fx">{e(b)}</span></li>' for a, b in c['fixes']) + '</ul></section>')
    rec = [(f'{TS}#{c["reader"]}', f'{c["code"]} in the This Side Up reader')] + [(R + u, t) for u, t in c['docs']]
    for r, dd in zip(rounds, RD.get(slug, [])): rec += [(R + u, f'Critic round {r["n"]}: {d}') for u, d, w in dd]
    o.append('<section class="block" id="record"><h2>Read the record</h2><ul class="doclist">' + ''.join(f'<li><a href="{u}">{e(t)}</a></li>' for u, t in rec) + '</ul></section>')
    o.append(f'<section class="block carry"><h2>Carried forward</h2><p>{e(c["carry"])}</p></section></div></article>')
    p = D.CASES[i - 1] if i > 0 else None; nx = D.CASES[i + 1] if i + 1 < n else None
    o.append('<nav class="casenav">' + (f'<a href="{TS}{p["slug"]}/" class="p"><span>Previous · {p["code"]}</span><b>{e(p["title"])}</b></a>' if p else f'<a href="{TS}" class="p"><span>Back</span><b>This Side Up</b></a>')
             + (f'<a href="{TS}{nx["slug"]}/" class="n"><span>Next · {nx["code"]}</span><b>{e(nx["title"])}</b></a>' if nx else f'<a href="{TS}" class="n"><span>Back</span><b>This Side Up</b></a>') + '</nav>')
    o.append(LB + '</main>\n' + FOOT + '\n</body></html>')
    os.makedirs(T + slug, exist_ok=True); open(T + slug + '/index.html', 'w').write('\n'.join(o))
    return slug
for i, c in enumerate(D.CASES): print(page(i, c), end=' ')
print()
