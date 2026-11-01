"""ALLWAYS editions: validate edition.json files and build the landing section and comparison page.

Used by tools/allways/build.py. Run alone to check:  python3 tools/allways/editions.py
Standard library only. The contract is in paeleo/allways/EDITIONS.md.
"""
from pathlib import Path
import html, json, re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'paeleo' / 'allways'
esc = html.escape


def tone(v):
    v = (v or '').lower()
    return 'fail' if 'fail' in v else 'pass' if 'pass' in v else 'mid' if 'inconclusive' in v else 'open'


def sol_catalog(cat, summary_fallback):
    """Read ALLWAYS / SOL's catalog.json (films[] with id, title, film.url, poster, status) into the edition shape."""
    films = []
    for f in cat.get('films', []):
        m = f.get('film') or {}
        if not m.get('url'): continue
        prep = m.get('kind') not in (None, 'film')
        films.append({'operator': f['id'], 'title': f['title'], 'duration': round(m.get('duration', 0)), 'film': m['url'], 'poster': f.get('poster', ''),
                      'page': f'index.html#film{f["number"]}', 'verdict': f'{f.get("status", "")} \u00b7 {f.get("version", "")}'.strip(' \u00b7') + (' (preparatory)' if prep else ''), 'preparatory': prep})
    first = next((f['poster'] for f in films if f['poster']), '')
    return {'films': films, 'cover': first, 'page': 'index.html',
            'summary': f'{cat.get("completed_films", len(films))} completed adaptations of SCION {cat.get("range", "")} and {cat.get("comparison_edits", 0)} comparison edits, with critic reports and source records. {cat.get("review_scope", "")}'.strip()}


def load():
    reg = json.loads((OUT / 'editions.json').read_text())['editions']
    ops = {e['id']: e for e in json.loads((OUT / 'scion' / 'scion-allways.json').read_text())}
    eds, problems = [], []
    for r in reg:
        d = (OUT / r['path']).resolve()
        meta = {}
        ej = d / 'edition.json'
        if r.get('format') == 'allways-sol-catalog':
            mf = d / r.get('manifest', 'catalog.json')
            if mf.exists(): meta = sol_catalog(json.loads(mf.read_text()), r.get('summary', ''))
            else: problems.append(f'{r["id"]}: {r.get("manifest", "catalog.json")} not in this checkout; cards and links for it were not built')
        elif ej.exists():
            try: meta = json.loads(ej.read_text())
            except Exception as e: problems.append(f'{r["id"]}: edition.json is not valid JSON ({e})')
        elif r.get('status') != 'expected':
            problems.append(f'{r["id"]}: no edition.json in {r["path"]}')
        ed = {**r, **{k: v for k, v in meta.items() if k not in ('path',)}}
        if r.get('summary') and not meta.get('summary'): ed['summary'] = r['summary']
        ed.setdefault('films', []); ed['dir'] = r['path']
        if meta and r.get('status') == 'expected': ed['status'] = meta.get('status', 'published')
        for f in ed['films']:
            adapted = r.get('format') is not None      # an edition with its own site owns its files
            for k in ('operator', 'title', 'film', 'poster', 'page'):
                if k not in f: problems.append(f'{r["id"]}: a film is missing "{k}": {f.get("title", f)}')
            if f.get('operator') not in ops: problems.append(f'{r["id"]}: operator {f.get("operator")} is not a SCION id')
            for k in ('film', 'poster'):
                if not adapted and k in f and not (d / f[k]).exists(): problems.append(f'{r["id"]}: {k} file missing: {f[k]}')
            if not adapted and 'page' in f and not (d / f['page'].split('#')[0]).exists(): problems.append(f'{r["id"]}: page missing: {f["page"]}')
        eds.append(ed)
    return eds, ops, problems


def landing_section(eds, num='04'):
    cards = ''
    for e in eds:
        if e['status'] == 'expected' and not e['films']:
            cards += (f'<article class="ecard expected"><span class="label">Expected</span><h3>{esc(e["label"])}</h3>'
                      f'<p>A pass at the same operators by this maker. Waiting for <code>{esc(e["dir"])}edition.json</code>.</p></article>')
            continue
        cover = f'<img loading="lazy" src="{esc(e["dir"] + e["cover"])}" alt="Still from the {esc(e["label"])} edition" width="640" height="480">' if e.get('cover') else ''
        ops = sorted({f['operator'] for f in e['films']})
        rng = f'SCION {ops[0]:03d}–{ops[-1]:03d}' if len(ops) > 1 else (f'SCION {ops[0]:03d}' if ops else '')
        cards += (f'<a class="ecard" href="{esc(e["dir"] + (e.get("page") or "").removeprefix("./"))}">{cover}<span class="label">{len(e["films"])} films · {rng} · {esc(e.get("made", ""))}</span>'
                  f'<h3>{esc(e["label"])}</h3><p>{esc(e.get("summary", ""))}</p><span class="label">Open the case studies ↗</span></a>')
    return (f'<section id="editions" class="section"><div class="section-head"><div><span class="label">{num} / Editions</span><h2>The same prompts,<br>different hands.</h2></div>'
            f'<p>Each edition runs the SCION operators once, with its own maker, method and judgment. Films are matched by operator, so one prompt can be read across editions.</p></div>'
            f'<div class="editions">{cards}</div><div class="links note-links"><a href="editions.html">Compare films by operator ↗</a><a href="EDITIONS.md">How to add an edition ↗</a></div></section>')


def matrix_page(eds, ops):
    cols = eds
    rows_ids = sorted({f['operator'] for e in eds for f in e['films']})
    head = ''.join(f'<th scope="col">{esc(e["label"])}<small>{"expected" if e["status"] == "expected" and not e["films"] else str(sum(1 for f in e["films"] if not f.get("preparatory"))) + " films" + (f" + {sum(1 for f in e['films'] if f.get('preparatory'))} study" if any(f.get("preparatory") for f in e["films"]) else "")}</small></th>' for e in cols)
    body = ''
    for n in rows_ids:
        cells = ''
        for e in cols:
            f = next((x for x in e['films'] if x['operator'] == n), None)
            if f:
                cells += (f'<td><a class="mcell" href="{esc(e["dir"] + f["page"])}"><img loading="lazy" src="{esc(e["dir"] + f["poster"])}" alt="" width="160" height="120">'
                          f'<b>{esc(f["title"])}</b><span class="vline v-{tone(f.get("verdict"))}"><span class="dot"></span>{esc(f.get("verdict", ""))}</span><small>{f.get("duration", "")} s</small></a></td>')
            else:
                cells += '<td class="none">—</td>'
        t = ops[n]['title']
        body += f'<tr><th scope="row"><a href="operator.html#s{n}">SCION {n:03d}</a><span>{esc(t.split(" — ")[0])}</span></th>{cells}</tr>'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>ALLWAYS editions compared</title><meta name="description" content="Films from every ALLWAYS edition lined up by SCION operator.">
<link rel="canonical" href="https://hartswf0.github.io/bolas/paeleo/allways/editions.html"><meta name="theme-color" content="#f4f1e9"><link rel="icon" href="../../favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../../tools/paeleo/fonts/local.css"><link rel="stylesheet" href="allways.css"></head>
<body id="top"><a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="wrap sitebar"><div class="parents"><a href="../../">CRASH LAB</a><span>/</span><a href="../">PAELEO</a><span>/</span><a href="./">ALLWAYS</a><span>/ EDITIONS</span></div></div></header>
<main id="main" class="wrap"><section class="section"><div class="section-head"><div><span class="label">Edition comparison</span><h2>One prompt,<br>every hand.</h2></div><p>Each row is a SCION operator. Each column is an edition. Open a cell for that film’s case study. A dash means the edition has not made that operator yet.</p></div>
<div class="matrix-wrap"><table class="matrix"><thead><tr><th scope="col">Operator</th>{head}</tr></thead><tbody>{body}</tbody></table></div>
<div class="links note-links" style="margin-top:28px"><a href="EDITIONS.md">How to add an edition ↗</a><a href="./#editions">Back to ALLWAYS</a></div></section></main>
<footer><div class="wrap"><div class="footer-row"><p>ALLWAYS · a cinema practice by Watson Hartsoe within PAELEO. Verdicts are as reported by each edition.</p></div></div></footer></body></html>'''


CSS = '''
/* editions (landing section and comparison page) */
.editions{align-items:start;display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,290px),1fr));gap:34px 26px;margin-bottom:26px}
.ecard{display:block;text-decoration:none;min-width:0}.ecard img{width:100%;height:auto;aspect-ratio:4/3;object-fit:cover;background:#000;display:block;margin-bottom:10px}
.ecard h3{font:800 clamp(28px,3vw,40px)/1.05 var(--display);text-transform:uppercase;margin:4px 0 6px}.ecard p{font-size:15px;line-height:1.5;color:var(--quiet);margin:0 0 8px}.ecard:hover h3{color:var(--accent)}
.ecard.expected{border:1px dashed var(--rule);padding:18px;min-height:150px}.ecard.expected h3{color:var(--quiet)}
.matrix-wrap{overflow-x:auto;max-width:100%}.matrix{border-collapse:collapse;width:auto;min-width:640px}
.matrix th,.matrix td{text-align:left;vertical-align:top;padding:12px 14px 12px 0;border-bottom:1px solid var(--rule)}
.matrix thead th{font:11px/1.5 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--quiet);border-bottom:1px solid var(--ink)}.matrix thead th small{display:block;text-transform:none;letter-spacing:0}
.matrix tbody th{font:11px/1.6 var(--mono);width:200px;font-weight:400}.matrix tbody th a{display:block;color:var(--accent)}.matrix tbody th span{font:700 17px/1.2 var(--display);text-transform:uppercase;display:block;margin-top:2px}
.mcell{display:block;text-decoration:none;width:200px;max-width:100%}.mcell img{width:100%;height:auto;display:block;background:#000;margin-bottom:6px}.mcell b{font:700 16px/1.2 var(--display);text-transform:uppercase;display:block;margin:2px 0 4px}.mcell small{font:11px var(--mono);color:var(--quiet)}
.matrix .none{color:var(--quiet);font:13px var(--mono)}
.vline{display:flex;gap:7px;align-items:flex-start;font:11px/1.45 var(--mono);color:var(--ink);margin:0 0 3px}.dot{width:9px;height:9px;border-radius:50%;background:#555e57;flex:none;margin-top:3px;display:inline-block}
.v-pass .dot{background:#2f6b3d}.v-mid .dot{background:#8a6a12}.v-fail .dot{background:#9a3328}
'''


def ensure_css():
    p = OUT / 'allways.css'; s = p.read_text()
    marker = '/* editions (landing section and comparison page) */'
    if marker in s: s = s[:s.index(marker)].rstrip('\n') + '\n'
    p.write_text(s + CSS)


if __name__ == '__main__':
    eds, ops, problems = load()
    print(len(eds), 'editions;', sum(len(e['films']) for e in eds), 'films;', len(problems), 'problems')
    for p in problems: print(' -', p)
