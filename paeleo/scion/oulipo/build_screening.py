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
    return f'''<article class="sc {status}" data-status="{status}">
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
    doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Oulipo Films · PAELEO</title>
<meta name="description" content="Every Oulipo SCION proof film on one page: made by swarms from foraged and handmade material, each with its review outcome.">
<meta name="theme-color" content="#0b0d10">
<link rel="icon" href="../../../../favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;800;900&family=JetBrains+Mono:wght@400;600&family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,600;1,7..72,400&display=swap">
<link rel="stylesheet" href="../../../paeleo.css">
<style>
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
<div class="wrap"><div class="sitebar"><a class="home" href="../../../../"><img src="../../../../favicon.svg" alt="" width="22" height="22">CRASH LAB</a><nav><a href="../../../">PAELEO</a><a href="../../">SCION</a><a href="../">Oulipo prompts</a><a href="./" aria-current="page">Oulipo films</a></nav></div>
<p class="crumbs"><a href="../../../">PAELEO</a> / <a href="../../">SCION</a> / <a href="../">Oulipo</a> / Films</p>

<header class="lockup">
  <div class="l">
    <span class="lbl">PAELEO · SCION · Oulipo</span>
    <h1>OULIPO FILMS</h1>
    <div class="exp"><span>Proof films made by swarms</span><b>foraged or handmade, never faked</b></div>
    <p class="tag">Each film tests one constraint from the Oulipo, Oucipo or Oubapo.</p>
    <p>Every film was made by its own swarm of agents from the work's SCION prompt. Each swarm had a director, units that forage archives or make the material by hand, an editor, blind readers, an independent critic and a rights reviewer. The films loop a silent excerpt as you scroll; press the button to watch the whole film with sound.</p>
  </div>
  <div class="r">
    <span class="lbl">{total} films</span>
    <dl class="tally"><dt style="color:var(--teal)">{counts["passed"]}</dt><dd>passed independent review</dd><dt style="color:var(--lamp-2)">{counts["near"]}</dt><dd>nearly passed (one narrow point)</dd><dt style="color:var(--stamp)">{counts["open"]}</dt><dd>swarm-made, not yet passed</dd><dt style="color:var(--ink-2)">{counts["earlier"]}</dt><dd>earlier versions, not yet remade</dd></dl>
    <div class="filters" role="group" aria-label="Show"><button class="btn" type="button" data-f="all" aria-pressed="true">All</button><button class="btn" type="button" data-f="passed" aria-pressed="false">Passed</button><button class="btn" type="button" data-f="near" aria-pressed="false">Nearly</button><button class="btn" type="button" data-f="open" aria-pressed="false">Not yet</button></div>
  </div>
</header>
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
