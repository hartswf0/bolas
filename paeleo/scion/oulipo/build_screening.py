"""Build screening/index.html: every Oulipo SCION film on one page, in the PAELEO page style.

Run after build.py (python3 build_screening.py). Reads catalogue/*.json, assets/films/*.mp4,
films/notes/*.txt, films/credits/*.json and assets/pages/. Uses ffprobe for running times.
"""
import html
import json
import subprocess
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
OUT = PROJECT / "screening" / "index.html"

# Review outcome of each film's latest swarm build (from films/notes/*.txt).
STATUS = {
    "recits-dellis-island": "passed", "les-lieux-dune-fugue": "passed", "la-mort-en-ce-jardin": "passed",
    "bang-bang": "passed", "teuf-teuf": "passed", "anemic-cinema": "passed",
    "moins-dun-quart-de-seconde-pour-vivre": "passed", "boucle-la": "passed", "les-caids-de-la-gaudriole": "passed",
    "zazie-dans-le-metro": "near", "mauro-martino-exercises-in-style": "near", "le-maki-mococo": "near",
    "le-chant-du-styrene": "near", "a-morning-stroll": "near", "exercices-de-style": "near",
}
LABEL = {"passed": "Passed review", "near": "Nearly passed", "open": "Not yet passed", "earlier": "Earlier version"}
SWARM_MADE = set(STATUS) | {
    "la-cite-raymond-queneau", "la-machine-a-tuer-le-temps", "monsieur-ripois", "renzo-e-luciana",
    "un-homme-qui-dort", "la-belle-hortense", "quatre-vingt-quinze", "99-ways-template",
}
SECTIONS = [
    ("Cinema", "Oucipo and the films around it: the constraint is a rule for shots, montage or the camera.", ["Cinema"]),
    ("Animation", "Animated films after Jabely, Studio AKA and the storyboard page.", ["Animation"]),
    ("Variations", "One incident, retold: literature and exercises in style.", ["Variations", "Literature"]),
    ("Comics", "Oubapo pages. Each comic is a real page and a film that performs its reading.", ["Comics"]),
]


def esc(s):
    return html.escape(str(s), quote=True)


def duration(path):
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                             capture_output=True, text=True, timeout=30).stdout.strip()
        return float(out)
    except Exception:
        return 0.0


def entries():
    rows = []
    for f in sorted((PROJECT / "catalogue").glob("*.json")):
        data = json.loads(f.read_text())
        items = data if isinstance(data, list) else data.get("entries", [data])
        rows.extend(e for e in items if isinstance(e, dict) and "slug" in e)
    return rows


def card(e):
    slug = e["slug"]
    mp4 = PROJECT / "assets" / "films" / f"{slug}.mp4"
    d = duration(mp4)
    if d <= 0:
        return None
    a, b = round(d * 0.30, 1), round(min(d * 0.30 + 12, d * 0.85), 1)
    status = STATUS.get(slug, "open" if slug in SWARM_MADE else "earlier")
    note = PROJECT / "films" / "notes" / f"{slug}.txt"
    text = note.read_text().strip() if note.is_file() else ""
    if "Review status" in text:
        text = text.split("Review status")[0].strip()
    elif "Review (" in text:
        text = text.split("Review (")[0].strip()
    credits = PROJECT / "films" / "credits" / f"{slug}.json"
    ncred = len(json.loads(credits.read_text())) if credits.is_file() else 0
    page = PROJECT / "assets" / "pages" / f"{slug}.png"
    links = [f'<a href="../s/{esc(slug)}/">The work and its prompt</a>']
    if page.is_file():
        links.append(f'<a href="../assets/pages/{esc(slug)}.png">The page</a>')
    links.append(f'<a href="../assets/films/{esc(slug)}.mp4" download>Download</a>')
    mins = f"{int(d // 60)}:{int(round(d % 60)):02d}"
    return f'''<article class="sc {status}" id="{esc(slug)}" data-status="{status}">
  <figure class="film" data-src="../assets/films/{esc(slug)}.mp4" data-seg="{a},{b}" data-len="{mins}"><div class="screen"><video muted playsinline preload="none" poster="../assets/films/{esc(slug)}.webp"></video></div></figure>
  <div class="meta"><span class="st">{LABEL[status]}</span><span class="lbl">{esc(e.get("byline", ""))}</span></div>
  <h3>{esc(e["work"])}</h3>
  <p class="rule">{esc(e.get("title", ""))}. {esc(e.get("line", ""))}</p>
  <details><summary>How it was made{f" · {ncred} foraged sources" if ncred else ""}</summary><p>{esc(text)}</p></details>
  <p class="links">{" · ".join(links)}</p>
</article>'''


def ninety_nine():
    pages = sorted((PROJECT / "assets" / "pages" / "99-ways").glob("[0-9][0-9]-*.jpg"))
    if not pages:
        return ""
    canon = PROJECT / "films" / "swarm" / "99-ways" / "canon.json"
    titles = {}
    if canon.is_file():
        titles = {c["n"]: c["title"] for c in json.loads(canon.read_text()).get("constraints", [])}
    cells = "".join(
        f'<a class="pg" href="../assets/pages/99-ways/{esc(p.name)}"><img src="../assets/pages/99-ways/{esc(p.name)}" alt="" loading="lazy"><span>{p.name[:2]} · {esc(titles.get(int(p.name[:2]), p.stem[3:]))}</span></a>'
        for p in pages)
    return f'''<section class="sec" id="ninety-nine"><div class="sechead"><h2>99 ways</h2><p>One station incident told 99 times, one constraint per page, in the lineage of Queneau and Madden: our own constraints, our own words, mixed media. {len(pages)} of 99 pages so far; the film that leafs through them comes when the book is complete.</p></div>
<div class="pages">{cells}</div></section>'''


WORKSHOPS = [
    ("Words and code", "The constraint touches language and programs.", [
        ("oulipo", "Oulipo", "Literature", "Combinatorial lines and a lipogram", "Interchangeable line slots stay grammatical across recombinations, while one forbidden letter never appears."),
        ("alamo", "ALAMO", "Computational prose", "Grammatical mold, donor lexicon", "The syntactic skeleton and inflection slots stay locked; nouns, verbs and adjectives come only from a donor word list."),
        ("ouinpo", "Ou’inpo", "Software code", "Runnable code with an acrostic", "The source file runs its computation cleanly, while the first character of each line spells a readable message."),
        ("outypopo", "Outypopo", "Typography", "An acrostic made with line breaks", "The wording stays verbatim; only the rag and the line breaks reveal the hidden vertical text."),
    ]),
    ("Time and performance", "The constraint touches duration, order and playing.", [
        ("oucipo", "Oucipo", "Cinema montage", "Fibonacci montage", "Shot durations follow exact Fibonacci counts; the critic checks the frame lengths and whether tension builds across the cuts."),
        ("outrapo", "Outrapo", "Stage and theatre", "A reversible stage score", "Entrances, props and spoken cues stay playable and legible when the piece is performed from end to start."),
        ("oumupo", "Oumupo", "Music", "Music that survives a shuffle", "Harmonic boundaries and cadences let every bar or phrase play in any order without clashing."),
        ("exercices-de-style-animated", "Exercices de style · Animated", "Animatics", "One animatic, three ways to see a beat", "The event timing stays locked while camera, rhythm and staging give three different readings."),
    ]),
    ("Space and sight", "The constraint touches the picture, the page and the plan.", [
        ("oupeinpo", "Oupeinpo", "Painting", "Tile permutation and a forbidden hue", "Painted tiles rotate or swap cleanly across their borders, and one banned band of colour never appears."),
        ("oubapo", "Oubapo", "Comics", "One image, two orders of captions", "The drawn panels stay untouched while reordering the captions flips cause, motive or punchline."),
        ("ouphopo", "Ouphopo", "Photography", "A route sampled by the clock", "The camera fires at strict clock intervals along a mapped walk, not when a picture looks good."),
        ("ouarchpo", "Ouarchpo", "Architecture", "Rooms on a knight’s tour", "Doorways and circulation make a visitor enter every room once, by chess-knight L-steps."),
        ("ougrapo", "Ougrapo", "Graphic design", "Five primitives, two poster hierarchies", "Exactly five shapes and type blocks rearrange to invert what the eye reads first and last."),
    ]),
    ("Evidence, appetite and civic order", "The constraint touches proof, the table and the record.", [
        ("oulipopo", "Oulipopo", "Detective fiction", "One solution, two clue orders", "The physical clues stay fixed; the order they are found in shifts suspicion without breaking the proof of the culprit."),
        ("ouhispo", "Ouhispo", "History", "Change one event in the record", "The chronology before one counterfactual hinge stays intact, and every later document updates consistently."),
        ("oucuipo", "Oucuipo", "Cooking", "A palindromic tasting menu", "Textures, temperatures and flavours read the same forward and backward around a central dish."),
        ("oupolpot", "Oupolpot", "Civic procedure", "Rotate the agenda", "The people and motions stay the same while rotating the speaking and voting order shifts the outcome."),
    ]),
]

INTRO = """
<header class="lockup">
  <div class="l">
    <span class="lbl">PAELEO · SCION · Oulipo · the Screening Room</span>
    <h1>OULIPO</h1>
    <div class="exp"><span>Ouxpo: workshops of potential everything</span><b>Foraged or handmade, never faked</b></div>
    <p class="tag">Playful rulebooks from the Oulipo and its sister workshops, used as building codes for an AI film crew.</p>
    <p>Most AI video tools guess pixels frame by frame, so rooms melt and stories drift. We went back to the Oulipo and the workshops that grew from it across cinema, comics, music, cooking, theatre, history, code and architecture. Each one locks a single strict rule: tell a story backward, fold a comic page to hide a clue, recut one fixed pool of shots. Our {nprompts} prompts turn those rules into assignments for a crew of AI agents. The crew forages real archive clips or makes the material by hand, and an independent critic rejects any cut where a viewer cannot see the rule at work.</p>
  </div>
  <div class="r">
    <span class="lbl">The three names</span>
    <dl class="names"><dt>PAELEO</dt><dd>The studio: Promptable Augmented Environments Lab · Ekphrastic Operations. From describing worlds to operating within them.</dd><dt>Oulipo</dt><dd>Ouvroir de littérature potentielle, the Workshop for Potential Literature, founded in 1960 by Raymond Queneau and François Le Lionnais. Le Lionnais's idea grew into the Ouxpo: a workshop of potential X for any craft.</dd><dt>SCION</dt><dd>Our AI production crews. Each prompt is a SCION: a rule, a proof to build, a test, and the crew that builds and checks it.</dd></dl>
  </div>
</header>

<section class="sec" id="ouxpo"><div class="sechead"><h2>Seventeen workshops</h2><p>Literature is one parent among many. The Oulipo, founded in 1960 inside the Collège de ’Pataphysique, was followed by workshops for detective fiction, painting, comics, photography, cinema, cooking, music and more. The Collège itself says the list will never be complete. Here, every workshop is tested on the same railway-station incident: a visitor, a sealed envelope, a bell, a brass key left on a bench, a service door that stays closed. They are grouped by what the constraint touches.</p></div>
<div class="wgroups">{groups}</div>
<p class="cap">Each workshop links to its prompt. Sources: <a href="https://www.college-de-pataphysique.fr/presentation/ouxpo/">Collège de ’Pataphysique, Ouxpo</a> · <a href="https://en.wikipedia.org/wiki/Ouxpo">Ouxpo on Wikipedia</a>.</p>
</section>

<section class="sec" id="crew"><div class="sechead"><h2>The vow and the crew</h2><p>Every film follows one material rule and is made by one kind of crew.</p></div>
<div class="cols">
  <div class="part"><h3>The material vow</h3><p class="vow">Foraged or handmade, never faked.</p><p>Every image and sound is foraged or handmade. Foraged means a real archival photograph, film clip or recording under an open licence (public domain, CC0, CC BY or CC BY-SA), each one credited. Handmade means made for the film: cut-paper puppets, brush and pen drawings, a paper strip folded on a table, engraved rings. No synthetic stock footage, and no style filters that fake a look. The films here cite between 2 and {nsources} foraged sources each.</p></div>
  <div class="part"><h3>Six roles</h3><ol class="roles"><li><b>Director</b> reads the prompt, writes the plan and freezes the test the film must pass.</li><li><b>Builders</b> forage archives or make the material by hand.</li><li><b>Editor</b> assembles, animates and renders the cut.</li><li><b>Blind readers</b> watch with no briefing and say what they saw.</li><li><b>Independent critic</b> judges the cut against the frozen test and the reference.</li><li><b>Rights reviewer</b> traces every source to an open licence.</li></ol></div>
</div></section>

<section class="sec" id="failures"><div class="sechead"><h2>The failures stay public</h2><p>A referee only means something if it can say no. Of {total} films, {passed} pass the independent critic. {near} narrowly miss, {open} have not passed, and {earlier} are earlier builds not yet remade. Each card below says which, and why.</p></div>
<div class="cols tallyrow">
  <dl class="tally"><dt style="color:var(--teal)">{passed}</dt><dd>passed independent review</dd><dt style="color:var(--lamp-2)">{near}</dt><dd>nearly passed (one narrow point)</dd><dt style="color:var(--stamp)">{open}</dt><dd>made by a crew, not yet passed</dd><dt style="color:var(--ink-2)">{earlier}</dt><dd>earlier versions, not yet remade</dd></dl>
  <div class="part"><p>The critic fails a film when a viewer who hasn't been told the rule cannot see it work. <a href="#la-machine-a-tuer-le-temps">La Machine à tuer le temps</a> passed the rights review and still failed the critic. So did <a href="#la-belle-hortense">La Belle Hortense</a>, after Jacques Roubaud.</p><div class="filters" role="group" aria-label="Show"><button class="btn" type="button" data-f="all" aria-pressed="true">All</button><button class="btn" type="button" data-f="passed" aria-pressed="false">Passed</button><button class="btn" type="button" data-f="near" aria-pressed="false">Nearly</button><button class="btn" type="button" data-f="open" aria-pressed="false">Not yet</button></div></div>
</div></section>

<section class="sec" id="start"><div class="sechead"><h2>Where to start</h2><p>Four stops, about ten minutes.</p></div>
<ol class="tour">
  <li><b>A page that folds into a film.</b> Watch <a href="#boucle-la">Boucle-là !</a> or <a href="#les-caids-de-la-gaudriole">Les caïds de la gaudriole</a>. Each comic is both a printable page and a short film that reverses or folds it in time. Then leaf through <a href="#ninety-nine">99 ways</a>, {npages} of 99 pages so far, after Raymond Queneau and Matt Madden.</li>
  <li><b>A film the critic failed.</b> Open <a href="#la-machine-a-tuer-le-temps">La Machine à tuer le temps</a> and read why it failed even though its rights review passed.</li>
  <li><b>One incident, seventeen crafts.</b> Open the <a href="#ouxpo">workshops</a> and follow the same station incident through montage, a tasting menu, a floor plan and an agenda.</li>
  <li><b>The same rule-first idea at scale.</b> Finish in <a href="https://hartswf0.github.io/burning-house/paeleo/abominable-house/live/player.html">The Burning House</a>, after Calvino's The Burning of the Abominable House, where you recast the four flour-sack tenants from a casting card.</li>
</ol></section>
"""


def introduction(counts, total, nsources, nprompts, npages):
    groups = "".join(
        f'<div class="wg"><h3>{esc(g)}</h3><p class="lbl">{esc(sub)}</p><table><thead><tr><th>Workshop</th><th>Craft</th><th>The rule</th><th>What stays fixed, and what the critic tests</th></tr></thead><tbody>'
        + "".join(f'<tr><td><a href="../s/{esc(slug)}/">{esc(name)}</a></td><td>{esc(craft)}</td><td>{esc(rule)}</td><td>{esc(fixed)}</td></tr>' for slug, name, craft, rule, fixed in rows)
        + "</tbody></table></div>"
        for g, sub, rows in WORKSHOPS)
    return INTRO.format(groups=groups, total=total, nsources=nsources, nprompts=nprompts, npages=npages, **counts)


def main():
    rows = [e for e in entries() if (PROJECT / "assets" / "films" / f"{e['slug']}.mp4").is_file()]
    secs, counts = [], {"passed": 0, "near": 0, "open": 0, "earlier": 0}
    for title, blurb, fams in SECTIONS:
        cards = [c for c in (card(e) for e in rows if e.get("family") in fams) if c]
        for e in rows:
            if e.get("family") in fams:
                counts[STATUS.get(e["slug"], "open" if e["slug"] in SWARM_MADE else "earlier")] += 1
        if cards:
            secs.append(f'<section class="sec" id="{title.lower()}"><div class="sechead"><h2>{title}</h2><p>{blurb}</p></div><div class="grid">{"".join(cards)}</div></section>')
    total = sum(counts.values())
    nsources = max([len(json.loads(f.read_text())) for f in (PROJECT / 'films' / 'credits').glob('*.json') if f.name != '99-ways.json'] or [0])
    nprompts = len(list((PROJECT / 'prompts').glob('*.md')))
    npages = len(list((PROJECT / 'assets' / 'pages' / '99-ways').glob('[0-9][0-9]-*.jpg')))
    doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Oulipo Screening Room · PAELEO</title>
<meta name="description" content="PAELEO Oulipo: rulebooks from the Oulipo and the seventeen Ouxpo workshops, used as building codes for an AI film crew. Foraged or handmade, never faked.">
<meta name="theme-color" content="#0b0d10">
<link rel="icon" href="../../../../favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;800;900&family=JetBrains+Mono:wght@400;600&family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,600;1,7..72,400&display=swap">
<link rel="stylesheet" href="../../../paeleo.css">
<style>
.names{{display:grid;gap:10px;margin:0}} .names dt{{font-family:var(--display);font-weight:900;font-size:30px;line-height:1;color:var(--stamp)}} .names dd{{margin:0;font-size:15px;line-height:1.45}}
.wgroups{{display:grid;gap:30px}} .wg{{display:grid;gap:6px;min-width:0;overflow-x:auto}} .wg h3{{font-size:28px;font-weight:800;text-transform:uppercase}}
.wg table{{border-collapse:collapse;width:100%;font-size:14.5px;min-width:620px}} .wg th{{font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;text-align:left;color:var(--ink-2);border-bottom:2px solid var(--ink);padding:6px 8px}}
.wg td{{border-bottom:1px solid var(--rule);padding:8px;vertical-align:top}} .wg td:first-child{{font-weight:600;white-space:nowrap}} .wg td:nth-child(2){{font-family:var(--mono);font-size:12.5px;color:var(--ink-2)}}
.vow{{font-family:var(--display);font-weight:900;font-size:clamp(30px,4.4vw,46px);line-height:1;text-transform:uppercase;color:var(--stamp)}}
.roles{{margin:0;padding-left:1.2em;display:grid;gap:6px}} .tour{{margin:0;padding-left:1.2em;display:grid;gap:12px;font-size:17px}}
.tallyrow{{align-items:start}}
@media (max-width:640px){{.wg table{{min-width:0}} .wg thead{{display:none}} .wg tr{{display:grid;gap:2px;padding:10px 0;border-bottom:1px solid var(--rule)}} .wg td{{border:0;padding:0}} .wg td:nth-child(3){{font-style:italic}} .wg td:nth-child(4){{color:var(--ink-2);font-size:14px}}}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,340px),1fr));gap:34px 26px}}
.sc{{display:grid;gap:8px;align-content:start;min-width:0}}
.sc h3{{font-size:30px;font-weight:800;text-transform:uppercase}}
.sc .meta{{display:flex;gap:10px;align-items:center;flex-wrap:wrap}}
.st{{font-family:var(--mono);font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;padding:2px 8px;border:1.5px solid currentColor;border-radius:2px}}
.passed .st{{color:var(--teal)}} .near .st{{color:var(--lamp-2)}} .open .st{{color:var(--stamp)}} .earlier .st{{color:var(--ink-2)}}
.sc .rule{{font-size:15.5px;color:var(--ink-2)}}
.sc details{{font-size:15px}} .sc summary{{cursor:pointer;font-family:var(--mono);font-size:12.5px;color:var(--ink-2)}}
.sc details p{{margin-top:6px}}
.links{{font-family:var(--mono);font-size:12.5px}}
.filters{{display:flex;gap:8px;flex-wrap:wrap}}
.filters button[aria-pressed="true"]{{background:var(--ink);color:var(--paper)}}
.tally{{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;align-items:baseline;margin:0}}
.tally dt{{font-family:var(--display);font-weight:900;font-size:34px;line-height:1}}
.tally dd{{margin:0;font-family:var(--mono);font-size:13px}}
.pages{{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(46%,150px),1fr));gap:14px}}
.pg{{display:grid;gap:4px;text-decoration:none}} .pg img{{border:1px solid var(--rule);aspect-ratio:2200/2850;object-fit:cover;width:100%;background:var(--panel)}}
.pg span{{font-family:var(--mono);font-size:11.5px;color:var(--ink-2)}}
@media (max-width:760px){{.lockup{{grid-template-columns:minmax(0,1fr)}}.lockup .l{{border-right:0;border-bottom:2px solid var(--ink)}}}}
</style></head><body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><symbol id="spk" viewBox="0 0 12 12"><path d="M1 4 H3.5 L7 1 V11 L3.5 8 H1 Z" fill="currentColor"/><path d="M8.5 3.5 Q10.5 6 8.5 8.5" stroke="currentColor" fill="none" stroke-width="1.2"/></symbol></svg>
<div class="wrap"><div class="sitebar"><a class="home" href="../../../../"><img src="../../../../favicon.svg" alt="" width="22" height="22">CRASH LAB</a><nav><a href="../../../">PAELEO</a><a href="../../">SCION</a><a href="../">Oulipo prompts</a><a href="./" aria-current="page">Screening Room</a></nav></div>
<p class="crumbs"><a href="../../../">PAELEO</a> / <a href="../../">SCION</a> / <a href="../">Oulipo</a> / Screening Room</p>

{introduction(counts, total, nsources, nprompts, npages)}
<section class="sec" id="films"><div class="sechead"><h2>The films</h2><p>Each film loops a silent excerpt while it is on screen. Press the button to watch the whole film with sound.</p></div></section>
{"".join(secs)}
{ninety_nine()}
</div>
<script>
(()=>{{const films=[...document.querySelectorAll('.film')];
films.forEach(f=>{{const v=f.querySelector('video'),[a,b]=f.dataset.seg.split(',').map(Number);let full=false;
  const bar=document.createElement('div');bar.className='bar';
  bar.innerHTML=`<button class="btn" type="button"><svg viewBox="0 0 12 12"><use href="#spk"/></svg>Watch with sound · ${{f.dataset.len}}</button>`;
  f.append(bar);
  v.addEventListener('loadedmetadata',()=>{{if(!full){{try{{v.currentTime=a}}catch(e){{}}}}}});
  v.addEventListener('timeupdate',()=>{{if(!full&&(v.currentTime>b||v.currentTime<a-.3)){{try{{v.currentTime=a}}catch(e){{}}}}}});
  bar.querySelector('button').addEventListener('click',()=>{{f._load();full=true;films.forEach(o=>{{if(o!==f){{const ov=o.querySelector('video');ov.pause()}}}});v.muted=false;v.controls=true;v.currentTime=0;v.play().catch(()=>{{}});bar.remove()}});
  f._load=()=>{{if(!v.src){{v.preload='metadata';v.src=f.dataset.src}}}}}});
const io=new IntersectionObserver(es=>es.forEach(e=>{{const f=e.target,v=f.querySelector('video');
  if(e.isIntersecting){{f._load();if(v.muted&&!matchMedia('(prefers-reduced-motion: reduce)').matches)v.play().catch(()=>{{}})}}else if(v.muted)v.pause()}}),{{rootMargin:'150px'}});
films.forEach(f=>io.observe(f));
document.querySelectorAll('.filters button').forEach(btn=>btn.addEventListener('click',()=>{{const k=btn.dataset.f;
  document.querySelectorAll('.filters button').forEach(o=>o.setAttribute('aria-pressed',String(o===btn)));
  document.querySelectorAll('.sc').forEach(c=>{{c.hidden=!(k==='all'||c.dataset.status===k)}});}}));}})();
</script>
</body></html>'''
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(doc)
    print(f"Built {OUT.relative_to(PROJECT)}: {total} films, {counts}")


if __name__ == "__main__":
    main()
