"""Build the ALLWAYS landing page from its Markdown statement and JSON slate.

Run from any directory: python3 tools/allways/build.py
Uses the Python standard library. Does not rebuild other programs or modify media.
"""
from pathlib import Path
import html
import json
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'paeleo' / 'allways'
esc = html.escape


def inline(text):
    text = esc(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    return re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)


def statement():
    # Controlled source format: headings and prose paragraphs; no executable HTML.
    blocks = (OUT / 'STATEMENT.md').read_text().strip().split('\n\n')[2:]
    rendered = []
    for block in blocks:
        if block.startswith('### '):
            rendered.append('<h3>' + inline(block[4:]) + '</h3>')
        else:
            rendered.append('<p>' + inline(block.replace('\n', ' ')) + '</p>')
    return '\n'.join(rendered)


def scion_link(number, label=''):
    return f'<a href="operator.html#s{number}">SCION {number:03d}{esc(label)}</a>'


def work_card(work, index):
    methods = scion_link(work['primary'], ' · primary') + ''.join(scion_link(n) for n in work['supporting'])
    return f'''<article class="work" id="{esc(work['slug'])}">
      <span class="work-no">{index:02d}</span>
      <div><h3>{esc(work['title'])}</h3><div class="subtitle">{esc(work['subtitle'])} · concept</div></div>
      <div class="work-copy"><p>{esc(work['logline'])}</p><details><summary>Proposed first proof</summary>
      <p>{esc(work['proof'])}</p><div class="method-links">{methods}</div><p class="note">{esc(work['note'])}</p></details></div>
    </article>'''


def main():
    slate = json.loads((OUT / 'works.json').read_text())
    entries = json.loads((OUT / 'scion' / 'scion-allways.json').read_text())
    assert len(slate['works']) == 12
    ids = {e['id'] for e in entries}
    assert ids == set(range(55, 114))
    for work in slate['works']:
        assert {work['primary'], *work['supporting']} <= ids
    works = '\n'.join(work_card(w, i) for i, w in enumerate(slate['works'], 1))
    studies = '\n'.join(f'<article><h4>{esc(s["title"])}</h4><p>{esc(s["description"])}</p><div class="method-links">{"".join(scion_link(n) for n in s["scion"])}</div></article>' for s in slate['studies'])
    families = []
    for e in entries:
        if not families or families[-1]['name'] != e['family']:
            families.append({'name': e['family'], 'first': e['id'], 'last': e['id'], 'count': 1})
        else:
            families[-1]['last'] = e['id']
            families[-1]['count'] += 1
    rows = ''.join(f'<tr><td>{f["first"]:03d}–{f["last"]:03d}</td><td><a href="operator.html#s{f["first"]}">{esc(f["name"])}</a></td><td>{f["count"]}</td></tr>' for f in families)
    precedents = [
        ('Afterlight', '../../afterlight/', '../../media/afterlight/thumbs/afl-07-spacetime.jpg', 'Light, duration, and what remains after a source changes. Films presented with the writing that shaped them.', 'Films and videotext · existing project'),
        ('The Found Odyssey', '../../found-odyssey/', '../../media/thumbs/ep1-nobody.jpg', 'An authored text encounters archive speech, footage, and a drawn cast. Each episode takes on a formal experiment.', 'Archive and performance · existing project'),
        ('CINEOSIS', '../../cineosis/', '../../media/thumbs/cineosis-handmade-film.jpg', 'Cinematic concepts become staged actions, archive encounters, and handmade film studies.', 'Cinema and semiosis · existing project'),
        ('WYGWYL', '../../wygwyl/', '../../media/thumbs/wygwyl-poem07-paper-poet.jpg', 'A reading, photographs, and a jointed paper figure meet in moving image.', 'Poem and image · existing project'),
        ('The threshold, handmade', '../handmade/', '../media/still/lineage-worldtext.jpg', 'Different SCION methods build from one description while the dog’s choices remain consequential.', 'PAELEO / PAE-02 · existing study'),
    ]
    precedent_html = ''.join(f'<a class="precedent" href="{url}"><img src="{image}" alt="Preview from {esc(title)}" width="800" height="500" loading="lazy"><h3>{esc(title)}</h3><p>{esc(text)}</p><span class="label">{esc(kind)} ↗</span></a>' for title, url, image, text, kind in precedents)
    fragments = [('The interval', 'A moment does not have to explain a life to be worth keeping.'), ('The match', 'The cut belongs to the editor. The lives on either side do not.'), ('The unnamed', 'We can meet a gesture before we know a name. A name remains worth finding.'), ('The gap', 'Leaving an interval open can be the most exact decision in the film.')]
    fragment_html = ''.join(f'<article class="fragment"><div class="label">{esc(title)}</div><p>{esc(text)}</p></article>' for title, text in fragments)
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>ALLWAYS · Cinema from the rest of the frame</title>
<meta name="description" content="ALLWAYS is a cinema practice within PAELEO: films, playable archives, and machine-assisted editing around ordinary gestures, overlooked work, and the differences that survive a match.">
<link rel="canonical" href="https://hartswf0.github.io/bolas/paeleo/allways/">
<meta property="og:title" content="ALLWAYS · Cinema from the rest of the frame"><meta property="og:description" content="What else was happening? A cinema practice within PAELEO, with a proposed film slate and 59 SCION production prompts."><meta property="og:type" content="website"><meta property="og:url" content="https://hartswf0.github.io/bolas/paeleo/allways/">
<meta name="theme-color" content="#f4f1e9"><link rel="icon" href="../../favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../../tools/paeleo/fonts/local.css"><link rel="stylesheet" href="allways.css"></head>
<body id="top"><a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="wrap sitebar"><div class="parents"><a href="../../">CRASH LAB</a><span>/</span><a href="../">PAELEO</a><span>/ ALLWAYS</span></div><nav aria-label="ALLWAYS"><a href="#statement">Statement</a><a href="#works">Works</a><a href="#methods">Methods</a><a href="#notebook">Notebook</a></nav></div></header>
<main id="main" class="wrap">
<section class="hero" aria-labelledby="brand"><div class="hero-top"><span class="label">A cinema practice within PAELEO</span><span class="label edition">Record / Work / Machine<br>Notes toward a cinema</span></div><h1 id="brand" class="wordmark">ALLWAYS</h1><div class="hero-bottom"><div><h2>Cinema from the<br>rest of the frame.</h2><div class="hero-name">ALWAYS / recurrence in time<br>ALL WAYS / different routes through the record</div></div><div class="description"><p>Films, playable archives, and experiments in machine-assisted editing. Ordinary gestures. Overlooked work. The differences that survive a match.</p><p>What becomes visible when the event stops organizing our attention?</p><div class="links"><a href="#works">Explore the proposed works ↓</a><a href="operator.html">Open the SCION prompts ↗</a></div></div></div></section>
<div class="opening"><h2>What else<br>was happening?</h2><p>A hand enters the frame, sets something right, and leaves. A preparation becomes the subject. A hesitation determines the cut. A room holds our attention after the action we were told to watch has finished.</p></div>
<section id="statement" class="section"><div class="section-head"><div><span class="label">01 / Statement</span><h2>The life around<br>the event.</h2></div><p>Attention can be reassigned. The new frame still has to answer for what it leaves out.</p></div><div class="essay-layout"><aside class="essay-aside"><p class="question">Record.<br>Work.<br>Machine.</p><p>Three strands of one practice: the material that reaches us, the activity that sustains it, and the procedures through which we encounter it again.</p><div class="links"><a href="STATEMENT.md">Read the statement</a></div></aside><div class="essay">{statement()}</div></div><div class="principle"><p>NEARMATCH<br>Our editorial principle</p><blockquote>A match should make a difference easier to notice.</blockquote></div></section>
<section id="works" class="section"><div class="section-head"><div><span class="label">02 / Proposed series</span><h2>B-roll of<br>civilization.</h2></div><p>Labor, routine, domestic space, and the unstable relation between a recording and its reconstruction. Each title gives the practice a different question to test.</p></div><div class="status-line"><span><i class="status-dot" aria-hidden="true"></i>12 development concepts</span><span>Proofs proposed · films not yet produced</span><a href="WORKS.md">Complete development notes ↗</a></div><div class="works">{works}</div><details class="study-box"><summary>Other studies and ways into the archive</summary><div class="study-grid">{studies}</div><div class="links note-links"><a href="NAMING.md">All names, collections, and earlier proposals ↗</a></div></details></section>
<section id="methods" class="section"><div class="method-panel"><div class="section-head"><div><span class="label">03 / Production methods</span><h2>SCION</h2><p>A lineage becomes a working operation.</p></div><div class="count">59<small>New standalone prompts / 055–113</small></div></div><p>Choose a question, a bounded source set, and a method. Make a small proof. Let another viewer encounter it. Repair what fails before expanding.</p><div class="links"><a href="operator.html">Search and copy the prompts ↗</a><a href="METHOD.md">Read the method ↗</a></div><table class="family-table"><thead><tr><th scope="col">IDs</th><th scope="col">Family</th><th scope="col">Count</th></tr></thead><tbody>{rows}</tbody></table><p class="method-foot">These are reviewed prompt specifications; their proposed proofs remain unexecuted. Reference films are lineages, with source records and qualifications in each entry. The original <a href="../scion/operator.html">54 animation swarms</a> and their <a href="../scion/">existing studies</a> remain available.</p><div class="links note-links"><a href="scion/SCION_CINEMA_LINEAGE_FORGE.md">Make another SCION</a><a href="scion/README.md">Files, sources, and reviews</a></div></div></section>
<section id="earlier-work" class="section"><div class="section-head"><div><span class="label">04 / Earlier work</span><h2>Already in<br>motion.</h2></div><p>Related work in CRASH LAB and PAELEO. These projects keep their established names, credits, and case records. They provide precedents for ALLWAYS.</p></div><div class="precedents">{precedent_html}</div></section>
<section id="notebook" class="section"><div class="section-head"><div><span class="label">05 / Between Takes</span><h2>Notes in<br>the margin.</h2></div><p>Working propositions. A film, a source, or a viewer's objection may change them.</p></div><div class="fragments">{fragment_html}</div><div class="links note-links"><a href="NOTEBOOK.md">Read the notebook ↗</a><a href="EDITORIAL.md">How the drafts changed ↗</a></div></section>
<section class="section architecture"><div><span class="label">The arrangement</span><h2>One practice.<br>Different roles.</h2></div><dl><dt>PAELEO</dt><dd>The research language and environment.</dd><dt>ALLWAYS</dt><dd>The cinema practice.</dd><dt>SCION</dt><dd>The production methods and criticism.</dd><dt>B-ROLL</dt><dd>The first proposed archival series.</dd><dt>NEARMATCH</dt><dd>The editorial principle.</dd><dt>BETWEEN TAKES</dt><dd>The working notebook.</dd></dl></section>
</main><footer><div class="wrap"><div class="footer-row"><p>ALLWAYS · a cinema practice by Watson Hartsoe within PAELEO.<br>Statement and development slate · October 2026.</p><div><a href="https://github.com/hartswf0/bolas/tree/main/paeleo/allways">GitHub</a><a href="README.md">Project notes</a><a class="back-top" href="#top">Back to the beginning ↑</a></div></div><div class="end-word" aria-hidden="true">LOOK AGAIN.</div></div></footer></body></html>'''
    # GitHub renders the companion Markdown; Pages serves the cinematic landing page.
    page = re.sub(r'href="([^"<>]+\.md)"', lambda m: 'href="https://github.com/hartswf0/bolas/blob/main/paeleo/allways/' + m.group(1) + '"', page)
    (OUT / 'index.html').write_text(page)
    print(json.dumps({'page': str(OUT / 'index.html'), 'works': len(slate['works']), 'scion_prompts': len(entries), 'families': len(families)}, indent=2))


if __name__ == '__main__':
    main()
