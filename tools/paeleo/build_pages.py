"""Build the PAELEO pages: paeleo/ (the program), paeleo/threshold/ (PAE-00's full case) and paeleo/scion/ (the 54-swarm queue).
python3 tools/paeleo/build_pages.py   (reads tools/paeleo/case.json and paeleo/scion/swarms.json)"""
import html, json, os, subprocess

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(R, 'paeleo')
esc = html.escape
CASE = json.load(open(os.path.join(R, 'tools/paeleo/case.json')))
SW = json.load(open(os.path.join(P, 'scion/swarms.json')))
RUN = {48: ('PAE-00', 'threshold/')}   # swarms that have been run, and the case they made
HM = json.load(open(os.path.join(R, 'tools/paeleo/handmade.json')))
for _s in HM['swarms']: RUN[_s['id']] = ('PAE-02', f'handmade/#s{_s["id"]:02d}')

NAV = [('lab/', 'Try it'), ('family/', 'The Family'), ('cineosis/', 'CINEOSIS'), ('found-odyssey/', 'The Found Odyssey'), ('wygwyl/', 'WYGWYL'),
       ('this-side-up/', 'This Side Up'), ('paeleo/', 'PAELEO'), ('films/', 'Films'), ('process/', 'How it was made')]
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;800;900&family=JetBrains+Mono:wght@400;600&family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,600;1,7..72,400&display=swap">')
BASE = 'https://hartswf0.github.io/bolas/'
ICONS = '''<svg width="0" height="0" style="position:absolute" aria-hidden="true">
  <symbol id="spk" viewBox="0 0 12 12"><path d="M1 4 H3.5 L7 1 V11 L3.5 8 H1 Z" fill="currentColor"/><path d="M8.5 3.5 Q10.5 6 8.5 8.5" stroke="currentColor" fill="none" stroke-width="1.2"/></symbol>
</svg>'''


def page(path, title, desc, body, image='paeleo/media/still/threshold-sill.jpg', scripts=''):
    up = '../' * path.count('/')
    here = path.rsplit('index.html', 1)[0]
    nav = ''.join(f'<a href="{up}{h}"{" aria-current=page" if here.startswith(h) else ""}>{n}</a>' for h, n in NAV)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title)} · CRASH LAB</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{BASE}{here}"><meta property="og:site_name" content="CRASH LAB"><meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="{BASE}{here}"><meta property="og:image" content="{BASE}{image}">
<meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#0b0d10">
<link rel="icon" href="{up}favicon.svg" type="image/svg+xml"><link rel="icon" href="{up}favicon-32.png" sizes="32x32"><link rel="apple-touch-icon" href="{up}apple-touch-icon.png">
{FONTS}<link rel="stylesheet" href="{up}paeleo/paeleo.css"></head><body>
{ICONS}
<div class="wrap"><div class="sitebar"><a class="home" href="{up}"><img src="{up}favicon.svg" alt="" width="22" height="22">CRASH LAB</a><nav>{nav}</nav></div></div>
<div class="wrap">
{body}
<footer>
  <span>PAELEO · a research program of CRASH LAB · Bolas · Watson Hartsoe, with Claude.</span>
  <span>Augmented Environments Lab is the name of the Georgia Tech laboratory and its lineage; PAELEO is a proposed program and language that develops from that tradition. It is not an official name of the lab. SCION prompts are new operational prompts inspired by documented work; they are not claims that the people named wrote or endorsed them.</span>
</footer>
</div>
{scripts}
</body></html>
'''


FILM_JS = '''<script>
(()=>{const films=[...document.querySelectorAll('.film')];
films.forEach(f=>{const v=f.querySelector('video'),[a,b]=f.dataset.seg.split(',').map(Number);let full=false;
  const bar=document.createElement('div');bar.className='bar';
  bar.innerHTML=`<button class="btn" type="button"><svg viewBox="0 0 12 12"><use href="#spk"/></svg>Watch the whole film with sound · ${f.dataset.len}</button>`;
  f.insertBefore(bar,f.querySelector('figcaption'));
  v.addEventListener('loadedmetadata',()=>{if(!full){try{v.currentTime=a}catch(e){}}});
  v.addEventListener('timeupdate',()=>{if(!full&&(v.currentTime>b||v.currentTime<a-.3)){try{v.currentTime=a}catch(e){}}});
  bar.querySelector('button').addEventListener('click',()=>{full=true;films.forEach(o=>{if(o!==f)o.querySelector('video').pause()});v.muted=false;v.controls=true;v.currentTime=0;v.play().catch(()=>{});bar.remove()});
  f._load=()=>{if(!v.src){v.src=f.dataset.src}}});
const io=new IntersectionObserver(es=>es.forEach(e=>{const f=e.target,v=f.querySelector('video');
  if(e.isIntersecting){f._load();if(v.muted&&!matchMedia('(prefers-reduced-motion: reduce)').matches)v.play().catch(()=>{})}else if(v.muted)v.pause()}),{rootMargin:'200px'});
films.forEach(f=>io.observe(f));})();
</script>'''


def try_block(up):
    seg = lambda k, opts: '<div class="seg" role="group">' + ''.join(f'<button type="button" data-k="{k}" data-v="{v}">{esc(n)}</button>' for v, n in opts) + '</div>'
    return f'''<div class="try" data-threshold id="try">
    <div class="head"><span class="lbl">Try it</span><h3>Earn the approach</h3></div>
    <p>You are the operator. You cannot move the dog. You can only change the circumstances, the way the prompts do in the film. It is the same dog: the same machine and the same paper, running in your browser.</p>
    <canvas class="stage" width="1280" height="720" aria-label="The porch at dusk: a person by a door and a dog"></canvas>
    <div class="ctrls">
      <div class="ctrl"><span class="lbl">The person</span>{seg('posture', [('stand', 'stand'), ('sit', 'sit down')])}</div>
      <div class="ctrl"><span class="lbl">Where</span>{seg('place', [('doorway', 'in the doorway'), ('beside', 'beside the door')])}</div>
      <div class="ctrl"><span class="lbl">The door</span>{seg('door', [('ajar', 'ajar'), ('open', 'open')])}</div>
      <div class="ctrl"><span class="lbl">Voice</span><div class="seg" role="group"><button type="button" class="call" data-call>call: Come here!</button><button type="button" data-k="voice" data-v="soft">softly</button><button type="button" data-k="voice" data-v="none">silent</button></div></div>
      <div class="ctrl"><span class="lbl">Hand</span>{seg('hand', [('none', 'none'), ('low', 'offer, low'), ('reach', 'reach for it')])}</div>
      <div class="ctrl"><span class="lbl">Start over</span><div class="seg"><button type="button" data-reset>reset</button></div></div>
    </div>
    <div class="readout"><span>the dog is <b class="st">watching</b></span><span>trust <b class="tr">0.20</b></span><span>threat <b class="th">0</b></span><span>pressure <b class="pr">0</b></span></div>
    <p class="why"></p>
    <pre class="log" aria-label="The dog's last choices, newest first"></pre>
  </div>'''


def threshold_box(up, full=True):
    c = CASE
    sheets = ''.join(f'<figure><img src="{up}paeleo/media/still/{s["img"]}" alt="" loading="lazy"><figcaption>{esc(s["cap"])}</figcaption></figure>' for s in c['sheets'][:4])
    fixes = ''.join(f'<div class="fix"><div class="b">{esc(b)}</div><div class="arr">→</div><div class="c">{esc(a)}</div></div>' for b, a in c['fixes'])
    recipe = ''.join(f'<li>{esc(r)}</li>' for r in c['recipe'])
    chips = ''.join(f'<span class="chip{" m" if m else ""}">{esc(t)}</span>' for t, m in c['chips'])
    return f'''<section class="box" id="pae-00">
  <div class="boxhead"><div class="row"><span class="code">PAE-00</span><span class="lbl">{esc(c["meta"])}</span></div>
    <h2>The threshold</h2><p class="q">{esc(c["question"])}</p></div>
  <div class="hero">
    <figure class="film" data-src="{up}paeleo/media/film/paeleo-00.mp4" data-seg="{c["seg"]}" data-len="{c["len"]}"><div class="screen"><video muted playsinline preload="metadata" poster="{up}paeleo/media/still/threshold-sill.jpg"></video></div><figcaption class="cap">{esc(c["cap"])}</figcaption></figure>
    <div class="trick"><span class="lbl">The trick</span><p>{esc(c["trick"])}</p>
      <div class="facts">{''.join(f'<span>{esc(k)} <b>{esc(v)}</b></span>' for k, v in c["facts"])}</div></div>
  </div>
  {try_block(up)}
  <div class="cols">
    <div class="part"><h3>Recipe</h3><div class="chips">{chips}</div><ol class="recipe">{recipe}</ol></div>
    <div class="part"><h3>The sheets</h3><div class="sheets">{sheets}</div></div>
  </div>
  <div class="part"><h3>What broke and what changed</h3><div class="fixes">{fixes}</div></div>
  {f'<div class="fullcase"><a href="{up}paeleo/threshold/"><i>PAE-00</i> Full case<span>{esc(c["fullcase"])}</span></a><a href="{up}paeleo/scion/"><i>SCION</i> The swarm it was made with<span>and the 53 others in the queue</span></a></div>' if full else ''}
  <a class="carry" href="{up}paeleo/scion/"><span class="lbl">Carries forward</span><b>{esc(c["carries"])}</b></a>
</section>'''


def queue(up, link_case=True):
    out = ''
    fams = []
    for s in SW:
        if s['family'] not in fams: fams.append(s['family'])
    for fam in fams:
        tiles = ''
        for s in [x for x in SW if x['family'] == fam]:
            name, _, kind = s['title'].partition(' — ')
            run = RUN.get(s['id'])
            href = f'{up}paeleo/{run[1]}' if run and link_case else f'{up}paeleo/scion/#lens-{s["id"]}'
            tiles += (f'<a class="sw{" run" if run else ""}" href="{href}"><img src="{up}paeleo/media/scion/lens-{s["id"]:02d}.jpg" alt="" loading="lazy" width="800" height="450"><span class="id"><span>SCION {s["id"]:02d}</span>{f"<em>{run[0]} · run</em>" if run else "<span>lens only</span>"}</span>'
                      f'<b>{esc(name)}</b><i>{esc(kind)}</i></a>')
        out += f'<div class="fam"><h3>{esc(fam)}</h3><div class="queue">{tiles}</div></div>'
    return out


def index():
    up = '../'
    body = f'''
<header class="lockup">
  <div class="l">
    <span class="lbl">A research program of CRASH LAB · Bolas</span>
    <h1>PAELEO</h1>
    <div class="exp"><span>Promptable Augmented Environments Lab</span><b>Ekphrastic Operations</b></div>
    <p class="tag">From describing worlds to operating within them.</p>
    <p>One research program at three scales of operation. <b>AEL</b> is the place, the laboratory and its lineage. <b>PEO</b> is the method: Prompt, Ekphrasis, Operation, how descriptions become consequential actions. <b>PAELEO</b> is the language and studio where the method operates across environments, archives, games, films and agents.</p>
  </div>
  <div class="r">
    <span class="lbl">Six letters, read two ways</span>
    <dl class="letters"><dt>P</dt><dd>Promptable</dd><dt>A</dt><dd>Augmented</dd><dt>E</dt><dd>Environments</dd><dt>L</dt><dd>Lab <i>/ Language</i></dd><dt>E</dt><dd>Ekphrastic</dd><dt>O</dt><dd>Operations</dd></dl>
    <p class="dbl">The L is a deliberate double reading. As a studio, PAELEO is a <b>Lab</b>. As an artifact, it is a <b>Language</b>: Promptable Augmented Environments Language for Ekphrastic Operations. AEL always keeps its official expansion, Augmented Environments Lab.</p>
    <p class="lbl">It sounds like <i>paleo</i>: sediment, earlier media, and futures buried in the past.</p>
  </div>
</header>

<section class="sec" id="scales"><div class="sechead"><h2>Three scales</h2><p>Not three competing acronyms. One intellectual and technical system, nested like crates.</p></div>
  <div class="scales">
    <div class="scale" style="--c:var(--kraft)"><div class="hd"><b>AEL</b><span>the place · institution</span></div><p class="nm">Augmented Environments Lab</p><p class="ln">Where situated worlds are investigated and made. The laboratory and its historical lineage.</p>
      <div class="scale in" style="--c:var(--teal)"><div class="hd"><b>PAELEO</b><span>the language and the studio · research artifact</span></div><p class="nm">Promptable Augmented Environments Lab / Language for Ekphrastic Operations</p><p class="ln">The language and working environment in which descriptions can be authored, executed, contested and evaluated. PAELEO Studio is its practice: film, games, XR, archives, animation and multi-agent production.</p>
        <div class="scale in peo" style="--c:var(--stamp)"><div class="hd"><b>PEO</b><span>the method · theory and authoring grammar</span></div><p class="nm">Prompt · Ekphrasis · Operation</p><p class="ln">How descriptions become consequential actions. Its object is not simply a prompt, but a situated operation with observable consequences.</p>
          <div class="cycle"><div><b>P</b><span>Prompt</span><i>intent</i></div><div><b>E</b><span>Ekphrasis</span><i>description</i></div><div><b>O</b><span>Operation</span><i>consequence</i></div></div>
          <p class="loop">↻ recursive: the consequence changes the situation from which the next prompt is made.</p>
        </div></div></div>
  </div>
  <div class="opor">
    <div style="--c:var(--stamp)"><b>Operation</b>changes a state of affairs. A single person can perform one. This is the primary research concept: operative ekphrasis is the phenomenon, ekphrastic operations the umbrella.</div>
    <div style="--c:var(--teal)"><b>Orchestration</b>arranges participants, agents, tools and sequences. It is one way of coordinating many operations: an important technique inside the program, not its name.</div>
  </div>
</section>

<section class="sec" id="lineage"><div class="sechead"><h2>Imagetext · environment text · worldtext</h2><p>The program's lineage, and the first thing its first film shows.</p></div>
  <div class="lineage">
    <div><span class="n">1 · representation</span><h3>Imagetext</h3><span class="k">text beside a picture · the page</span><img src="media/still/lineage-imagetext.jpg" alt="A picture of the porch on a page, with the caption: A dog at a door." loading="lazy"><p>Text and image remediate each other on a flat plane: the page, the screen, the early interface. The Bolter and Mitchell paradigm.</p></div>
    <div><span class="n">2 · situatedness</span><h3>Environment text</h3><span class="k">text pinned to a place · AEL</span><img src="media/still/lineage-environment.jpg" alt="The caption has become paper tags pinned to the door, the person and the dog." loading="lazy"><p>The imagetext is lifted off the screen and anchored to coordinates, markers and space. The AEL era: DART, Argon, locative media.</p></div>
    <div><span class="n">3 · execution</span><h3>Worldtext</h3><span class="k">text the place runs on · PAELEO</span><img src="media/still/lineage-worldtext.jpg" alt="The dog's tag lists what it may do, including refuse, and the dog has risen to watch." loading="lazy"><p>The environment text gains rules and agency. The text does not just sit in a space; it generates and governs it, as a move in a language game.</p></div>
  </div>
  <p class="note">Why not <i>videotext</i>: a video implies a fixed timeline meant to be watched. A world is inhabited, queried and simulated. Videotext is a closed loop, a broadcast; environment text is an open system, a space; worldtext is a playable language game.</p>
</section>

<section class="sec" id="boxes"><div class="sechead"><h2>The boxes</h2><p>Each box is one film made by one SCION swarm, with its case: the question, the trick, the recipe, something to try, what broke. The first box is open.</p></div>
{threshold_box(up)}


<section class="box" id="pae-01"><div class="boxhead"><div class="row"><span class="code">PAE-01</span><span class="lbl">Oct 24 · 1 min 35 s · all 54 SCION lenses</span></div>
    <h2>SCION through the dog</h2><p class="q">Before a swarm makes its own film, what does it see first in this one?</p></div>
  <div class="hero"><figure class="film" data-src="media/film/paeleo-01.mp4" data-seg="4.0,30.0" data-len="1:35"><div class="screen"><video muted playsinline preload="metadata" poster="media/scion/lens-02.jpg"></video></div><figcaption class="cap">Fifty-four lenses on one porch: shadow theatre, Sketchpad constraints, GrabCut masks, a halftone print, a provenance graph. The dog underneath is the same machine every time.</figcaption></figure>
    <div class="trick"><span class="lbl">The trick</span><p>The stage records every paper piece and joint as it draws them. Each swarm gets a lens that reads that record and draws its own formal language over the same running scene: meshes, bones, mattes, weights, state graphs, archive frames.</p>
      <div class="facts"><span>lenses <b>54</b>, one per swarm</span><span>loop <b>32 s</b> of prompts, shared</span><span>live <b>in the browser</b>, any lens</span></div></div></div>
  <div class="fullcase"><a href="scion/#viewer"><i>PAE-01</i> Every lens, live<span>with the write-up of the operator</span></a></div>
</section>
{handmade_box(up)}
</section>

<section class="sec" id="queue"><div class="sechead"><h2>The swarm queue</h2><p>Fifty-four SCION animation swarms, each a standalone prompt studio with its own proof scene and research loop. PAE-00 was made by number 48; every one is shown through the dog in PAE-01. <a href="scion/">The operator, written up</a> · <a href="scion/operator.html">open the operator</a>.</p></div>
{queue(up)}
</section>

<section class="sec" id="names"><div class="sechead"><h2>The names record</h2><p>Which terms do which work, and where they collide.</p></div>
  <div class="tw"><table class="names"><thead><tr><th>Candidate</th><th>What it emphasizes</th><th>Assessment</th></tr></thead><tbody>
    <tr><td>Ekphrastic Operations</td><td>descriptions that act upon worlds</td><td>best umbrella</td></tr>
    <tr><td>Ekphrastic Orchestration</td><td>coordinating agents, tools, media and performances</td><td>excellent subsystem</td></tr>
    <tr><td>Operative Ekphrasis</td><td>the foundational theoretical concept</td><td>best dissertation term</td></tr>
    <tr><td>Prompt Orchestration</td><td>coordinating prompts and model workflows</td><td>useful technique, too narrow for the thesis</td></tr>
    <tr><td>Ekphrastic Ontologies</td><td>descriptions constituting objects and worlds</td><td>useful research branch</td></tr>
  </tbody></table></div>
  <div class="cols">
    <div class="part"><h3>Collisions</h3><ul>
      <li><b>POML</b> already names Microsoft's Prompt Orchestration Markup Language. A reference or substrate, not the identity of this contribution.</li>
      <li><b>PEO</b> is the Person–Environment–Occupation model in occupational therapy. A collision, and also a precedent for a situated, relational understanding of action.</li>
      <li>The Georgia Tech name is <b>Augmented Environments Lab</b>, singular words exactly as they are. PAELEO never renames the lab.</li></ul></div>
    <div class="part"><h3>Formal and public</h3><ul>
      <li>For the dissertation: <i>Ekphrasis as Operation</i>, the theoretical subtitle.</li>
      <li>For the studio: <i>Ekphrastic Operations</i>. Shorter, more active, broad enough for film, games, archives, XR and agentic performance.</li>
      <li><i>Promptable</i> names an affordance of the environment. A place, a character, a film or an archive can become promptable and keep its own constraints and agency.</li></ul></div>
  </div>
  <div class="fam4">
    <div><span>institution</span><b>AEL</b>the laboratory and its lineage</div>
    <div><span>theory + method</span><b>PEO</b>Prompt · Ekphrasis · Operation</div>
    <div><span>research artifact</span><b>PAELEO</b>the language and authoring environment implementing PEO</div>
    <div><span>creative practice</span><b>PAELEO Studio</b>film, games, XR, archives, animation, multi-agent production</div>
  </div>
  <p class="note">The argument in one breath: operative ekphrasis is the phenomenon investigated. PEO is the theoretical and experimental model. PAELEO is the language and working environment in which descriptions are authored, executed, contested and evaluated. AEL is the institutional lineage from which it develops: a laboratory that develops a language for operating within environments.</p>
</section>
'''
    scripts = ('<script src="threshold/machine.js"></script><script src="threshold/stage.js"></script><script src="threshold/try.js"></script>' + FILM_JS)
    open(os.path.join(P, 'index.html'), 'w').write(page('paeleo/index.html', 'PAELEO', 'Promptable Augmented Environments Lab · Ekphrastic Operations. One research program at three scales: AEL the place, PEO the method, PAELEO the language and studio. The first film: a dog that can refuse.', body, scripts=scripts))


def case_page():
    up = '../../'; c = CASE
    vers = ''
    for v in c['versions']:
        vid = f'<video controls preload="none" playsinline poster="{up}paeleo/media/still/{v["poster"]}" src="{up}paeleo/media/film/{v["file"]}"></video>' if v.get('file') else ''
        vers += f'''<article class="ver"><div class="vh"><span class="vn">{esc(v["n"])}</span><h3>{esc(v["title"])}</h3><span class="vm">{esc(v["meta"])}</span></div>
  <div>{vid}</div><div class="part"><p>{esc(v["text"])}</p>{"<ul>" + "".join(f"<li>{esc(x)}</li>" for x in v.get("changes", [])) + "</ul>" if v.get("changes") else ""}</div></article>'''
    rounds = ''
    for r in c['rounds']:
        cls = {'pass': 'pass', 'reference stronger': 'fail', 'does not pass': 'fail', 'inconclusive': 'part'}[r['verdict']]
        figs = ''.join(f'<figure><img src="{up}paeleo/media/still/{f["img"]}" alt="" loading="lazy"><figcaption>{esc(f["cap"])}</figcaption></figure>' for f in r.get('figs', []))
        rounds += f'''<article class="round"><div class="rh"><h3>{esc(r["title"])}</h3><span class="verdict {cls}">{esc(r["verdict"])}</span><span class="vm">{esc(r["meta"])}</span></div>
  <div>{figs}</div><div class="part"><p><b>Largest gap.</b> {esc(r["gap"])}</p><p class="next"><b>Repair condition.</b> {esc(r["repair"])}</p>
  <ul>{"".join(f"<li>{esc(x)}</li>" for x in r["notes"])}</ul><p><b>Keep.</b> {esc(r["keep"])}</p><p><b>What was done.</b> {esc(r["done"])}</p>
  <details><summary>The critic's report, verbatim</summary><pre class="prompt">{esc(r["report"])}</pre></details></div></article>'''
    sheets = ''.join(f'<figure><img src="{up}paeleo/media/still/{s["img"]}" alt="" loading="lazy"><figcaption>{esc(s["cap"])}</figcaption></figure>' for s in c['sheets'])
    prompt = next(s for s in SW if s['id'] == 48)['prompt']
    body = f'''<p class="crumbs"><a href="{up}">CRASH LAB</a> / <a href="{up}paeleo/">PAELEO</a> / PAE-00</p>
{threshold_box(up, full=False)}
<section class="sec" id="chart"><div class="sechead"><h2>The state chart</h2><p>Five states. Guards are checked in priority order every frame; each state holds for a minimum window so the dog never flickers between choices. Danger (retreat, refuse) may cut a window short; nothing else can.</p></div>
  {c["chart_svg"]}
  <div class="tw"><table class="names"><thead><tr><th>Guard</th><th>Goes to</th><th>When</th></tr></thead><tbody>{"".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(w)}</td></tr>" for a, b, w in c["guards"])}</tbody></table></div>
  <div class="cols"><div class="part"><h3>What the dog perceives</h3><ul>{"".join(f"<li>{esc(x)}</li>" for x in c["perceive"])}</ul></div>
  <div class="part"><h3>The tests</h3><p>Run with <code>node tools/paeleo/test_machine.js</code>.</p><ul>{"".join(f"<li>{esc(x)}</li>" for x in c["tests"])}</ul></div></div>
</section>
<section class="sec" id="trace"><div class="sechead"><h2>The decision trace</h2><p>Every choice the dog made in the film, with the guard that made it. Film time is machine time plus {c["T0"]} s.</p></div>
  <div class="tw"><table class="names"><thead><tr><th>Film time</th><th>Prompt or choice</th><th>Why</th></tr></thead><tbody>{"".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(w)}</td></tr>" for a, b, w in c["trace"])}</tbody></table></div>
</section>
<section class="sec" id="versions"><div class="sechead"><h2>Versions</h2><p>Every cut, in order.</p></div>{vers}</section>
<section class="sec" id="critic"><div class="sechead"><h2>Critic rounds</h2><p>An independent critic watched each cut without the makers' notes and returned a verdict, the moments behind it, the largest gap and a condition a re-check could test.</p></div><div style="display:grid;gap:22px">{rounds}</div></section>
<section class="sec" id="next"><div class="sechead"><h2>Next</h2><p>Accepted at round 4. What the last critic left for the next cut, in order.</p></div><ol class="recipe">{"".join(f"<li>{esc(x)}</li>" for x in c["next"])}</ol></section>
<section class="sec" id="sheets"><div class="sechead"><h2>Sheets</h2></div><div class="sheets">{sheets}</div></section>
<section class="sec" id="prompt"><div class="sechead"><h2>The prompt</h2><p>SCION 48, State Machines: Characters That Can Refuse, verbatim from the SCION operator. Its proof scene is this film's middle: a dog chooses among watch, approach, retreat, lie down and refuse, and the player has to change circumstances to earn approach.</p></div>
  <details open><summary>SCION-STATE-MACHINES</summary><pre class="prompt">{esc(prompt)}</pre></details>
  <div class="part"><h3>How the inputs were filled</h3><ul>{"".join(f"<li><b>{esc(k)}</b> {esc(v)}</li>" for k, v in c["inputs"])}</ul></div>
</section>
<section class="sec" id="files"><div class="sechead"><h2>Files</h2></div><ul>{"".join(f'<li><a href="{up}{esc(h)}"><code>{esc(h)}</code></a> {esc(t)}</li>' for h, t in c["files"])}</ul></section>
'''
    scripts = ('<script src="machine.js"></script><script src="stage.js"></script><script src="try.js"></script>' + FILM_JS)
    open(os.path.join(P, 'threshold/index.html'), 'w').write(page('paeleo/threshold/index.html', 'PAE-00 · The threshold', c['question'], body, scripts=scripts))


def lens_data():
    """the 54 lenses as the page needs them, read from lenses.js itself"""
    js = ("global.window=global;global.DOMMatrix=class{};global.Path2D=class{};global.Threshold=require('./paeleo/threshold/machine.js');"
          "global.Stage=require('./paeleo/threshold/stage.js');require('./paeleo/scion/lenses.js');"
          "console.log(JSON.stringify(Scion.LENSES.map(l=>({id:l.id,look:l.look,show:l.show}))))")
    return json.loads(subprocess.run(['node', '-e', js], cwd=R, capture_output=True, text=True, check=True).stdout)


def anatomy():
    """what every SCION prompt is made of, counted from the prompts themselves"""
    import re
    heads = [re.findall(r'^## (.+)$', x['prompt'], re.M) for x in SW]
    words = [len(x['prompt'].split()) for x in SW]
    doc = SW[0]['prompt']; doc = doc[doc.index('## INHERITED'):doc.index('## START NOW')]
    doctrine = [(n, t.split('. ')[0].rstrip('.') + '.') for n, t in re.findall(r'^\d+\. \*\*(.+?)\.\*\* (.+)$', doc, re.M)]
    same_doc = len({x['prompt'][x['prompt'].index('## INHERITED'):x['prompt'].index('## START NOW')] for x in SW}) == 1
    sec = lambda x, k: x['prompt'].split(f'## {k}')[1].split('\n## ')[0].strip()
    per = {x['id']: dict(theorem=sec(x, '1 · Creative theorem to prove').split('\n')[0], proof=sec(x, '4 · Hard proof scene; produce before scaling').split('\n')[0],
                         swarm=sec(x, '3 · Assemble the smallest capable swarm').split('\n')[0], url=(re.search(r'Research starting point: (\S+)', x['prompt']) or [None, None])[1]) for x in SW}
    import re as _re
    secs = [_re.sub(r'^\d+ · ', '', h) for h in heads[0] if _re.match(r'^\d+ · ', h)]
    return dict(secs=secs, heads=heads[0], same_heads=all(h == heads[0] for h in heads), words=(min(words), max(words), sum(words)), doctrine=doctrine, same_doc=same_doc, per=per,
                fams=[(f, sum(1 for x in SW if x['family'] == f)) for f in dict.fromkeys(x['family'] for x in SW)], urls=sum(1 for x in SW if 'Research starting point' in x['prompt']))


RAN = [  # how PAE-00 kept each point of the doctrine (the record is the case page)
    ('Creative thesis', 'A dog the person can understand but not command. Bland would have been a dog that obeys.'),
    ('Inspectable bar', 'No reference film was available, so every critic judged against the bar in the prompt and said so: three times "inconclusive" or "does not pass" before a pass.'),
    ('Hard proof first', 'The proof scene in the prompt (watch, approach, retreat, lie down, refuse; earn the approach) became the film\'s middle, built end to end with sound before anything else was added.'),
    ('Accountable swarm', 'The six roles were merged into one working session (dramaturg, state graph, clip assembly, interaction, model-based testing), because the coupling was tight. The critic was always a separate agent.'),
    ('Acting', 'Attention, intention, gesture, resistance, changed state: ears, tail, crouch, the turned back, the chin on the paws. The tags say the same thing, but the critics checked it with the tags masked.'),
    ('Consequential world', 'The sill, the door, the floor and the distance between the two bodies are in the machine; nothing crosses the threshold that the machine does not allow.'),
    ('Audio and staging', 'Keys for the prompts, a wordless voice, the door, paws that come nearer, and a quiet hold at the end.'),
    ('Canonical state', 'One deterministic timeline: the film renders identically from tools/paeleo, and every cut is committed.'),
    ('Independent criticism', 'Four rounds, four fresh critics. Each saw the film and the bar, never the makers\' notes, and each left a falsifiable condition for the next.'),
    ('Root-cause repair', 'An absorbing state and a speed jump were found by the model-based tests, a neck that stood up like a plank by a critic; each was fixed in the rig or the machine, not painted over.'),
    ('Recursive inquiry', 'When the "come in" beat failed twice, the question changed from "is it visible" to "does it read as a choice": the look in through the door, then the chin down for good.'),
    ('Creative mutation', 'The jamb drawn over the dog\'s back, first a fix, became the image of the idea: half in, half out.'),
    ('Whole-work assembly', 'Every critic watched the whole 82 s, not the repaired shot.'),
    ('Honest evidence', 'Critics measured the sound; none could hear it, and the page says so. No human viewing is claimed.'),
    ('Resources and stopping', 'Stopped at the first independent pass; what the last critic left is listed as the next repairs, not done quietly.'),
]


def reel_rounds(up):
    out = ''
    for n in range(1, 6):
        f = os.path.join(R, f'tools/paeleo/reviews/reel-round{n}.json')
        if not os.path.exists(f): continue
        r = json.load(open(f)); rep = open(f[:-5] + '.txt').read()
        cls = {'pass': 'pass', 'does not pass': 'fail', 'inconclusive': 'part'}[r['verdict']]
        out += f'''<article class="round"><div class="rh"><h3>{esc(r["title"])}</h3><span class="verdict {cls}">{esc(r["verdict"])}</span><span class="vm">{esc(r["meta"])}</span></div>
  <div class="part"><p><b>Largest gap.</b> {esc(r["gap"])}</p><p class="next"><b>Repair condition.</b> {esc(r["repair"])}</p></div>
  <div class="part"><ul>{"".join(f"<li>{esc(x)}</li>" for x in r["notes"])}</ul><p><b>What was done.</b> {esc(r["done"])}</p>
  <details><summary>The critic's report, verbatim</summary><pre class="prompt">{esc(rep)}</pre></details></div></article>'''
    return f'<div style="display:grid;gap:18px"><h3 style="font:800 26px/1 var(--display);text-transform:uppercase;margin:0">The reel\'s critic rounds</h3>{out}</div>' if out else ''


def scion_page():
    up = '../../'; A = anatomy(); LD = {l['id']: l for l in lens_data()}
    fams = ' · '.join(f'{f} {n}' for f, n in A['fams'])
    tiles = ''
    for fam, _ in A['fams']:
        t = ''
        for x in [y for y in SW if y['family'] == fam]:
            name, _, kind = x['title'].partition(' — '); l = LD[x['id']]; p = A['per'][x['id']]; run = RUN.get(x['id'])
            t += (f'<article class="lens{" run" if run else ""}" id="s{x["id"]}"><a href="#lens-{x["id"]}" data-lens="{x["id"]}" class="im"><img src="{up}paeleo/media/scion/lens-{x["id"]:02d}.jpg" alt="{esc(name)} through the dog: {esc(l["look"])}" loading="lazy" width="800" height="450"></a>'
                  f'<div class="tx"><span class="id">SCION {x["id"]:02d}{f" · <em>{run[0]}</em>" if run else ""}</span><b>{esc(name)}</b><i>{esc(kind)}</i>'
                  f'<p class="sh">{esc(l["show"])}</p><dl><dt>theorem</dt><dd>{esc(p["theorem"])}</dd><dt>proof scene</dt><dd>{esc(p["proof"])}</dd><dt>lineage</dt><dd>{esc(x["lineage"])}</dd></dl>'
                  f'<p class="lk"><a href="operator.html#s{x["id"]}">the prompt</a>{f" · <a href=\"{up}paeleo/{run[1]}\">the film it made</a>" if run else ""}{f" · <a href=\"{esc(p["url"])}\">research start</a>" if p["url"] else ""}</p></div></article>')
        tiles += f'<div class="fam"><h3>{esc(fam)}</h3><div class="lenses">{t}</div></div>'
    heads = ''.join(f'<li><b>{esc(h)}</b></li>' for h in A['secs'])
    ex = next(x for x in SW if x['id'] == 48)['prompt']
    doctrine = ''.join(f'<li><b>{esc(n)}.</b> {esc(t)}</li>' for n, t in A['doctrine'])
    ran = ''.join(f'<tr><td>{esc(n)}</td><td>{esc(t)}</td></tr>' for n, t in RAN)
    body = f'''<p class="crumbs"><a href="{up}">CRASH LAB</a> / <a href="{up}paeleo/">PAELEO</a> / SCION</p>
<header class="lockup"><div class="l"><span class="lbl">SCION / lineage forge · the swarm operator</span><h1 style="font-size:clamp(64px,12vw,140px)">SCION</h1>
  <p class="tag">Fifty-four animation swarms. Each is a standalone prompt that turns one artist, researcher, studio, algorithm or archive into a working studio with a proof to make and a critic to answer to.</p>
  <p>The SCION operator is a single page: search the 54, read one, copy it whole or save it as Markdown. Each prompt names a lineage, states a creative theorem, gives the swarm its native formal language and the smallest crew that could build it, and sets a hard proof scene to produce before anything else. Then all 54 inherit the same fifteen-point doctrine. PAELEO films are made with them, one swarm per box.</p>
  <p><a class="btn" href="operator.html">Open the operator</a> <a class="btn" href="#viewer">See all 54 through the dog</a> <a class="btn" href="#reel">Watch the reel</a></p></div>
  <div class="r"><span class="lbl">Counted from the prompts</span><dl class="letters">
    <dt>54</dt><dd>swarms, in five families: <i>{esc(fams)}</i></dd><dt>8</dt><dd>numbered sections in every prompt, in the same order{"" if A["same_heads"] else " (not in all)"}</dd>
    <dt>15</dt><dd>points of doctrine, {"word for word the same in all 54" if A["same_doc"] else "varying"}</dd><dt>5</dt><dd>inputs to fill: work, direction, delivery, resources, rights</dd>
    <dt>{A["words"][0]:,}</dt><dd>to {A["words"][1]:,} words each, {A["words"][2]:,} in all; {A["urls"]} name a research starting point</dd></dl>
  <p class="lbl">Each name is a lineage, not an endorsement. The prompts say so themselves.</p></div></header>

<section class="sec" id="viewer-sec"><div class="sechead"><h2>Through the dog</h2><p>Every swarm shown on the same porch, the same paper dog and the same running loop of prompts (called, pressed, then earned). A lens is not that swarm's film. It is its first move: its native formal language made visible on a character you already know. The machine underneath never changes.</p></div>
  <div class="try" id="viewer">
    <div class="head"><span class="lbl">Live</span><h3 class="t">State Machines</h3></div>
    <p class="n lbl"></p>
    <canvas width="1280" height="720" aria-label="The porch, the person and the dog, drawn through the chosen swarm"></canvas>
    <div class="ctrls">
      <div class="ctrl"><span class="lbl">Swarm</span><select class="pick" aria-label="Choose a swarm"></select></div>
      <div class="ctrl"><span class="lbl">Step</span><div class="seg"><button type="button" data-prev>← previous</button><button type="button" data-next>next →</button></div></div>
      <div class="ctrl"><span class="lbl">Play</span><div class="seg"><button type="button" data-tour aria-pressed="false">tour all 54</button><button type="button" data-restart>restart the loop</button></div></div>
    </div>
    <p><b class="look"></b>. <span class="show"></span></p>
    <p class="lbl">lineage: <span class="lin"></span> · <a class="op" href="operator.html">read the prompt</a></p>
  </div>
  <div class="box" id="reel"><div class="boxhead"><div class="row"><span class="code">PAE-01</span><span class="lbl">Oct 24 · 1 min 35 s · all 54 lenses, 1.6 s each</span></div><h2>SCION through the dog</h2>
    <p class="q">The same dog, 54 ways: what does each swarm see first?</p></div>
    <figure class="film" data-src="{up}paeleo/media/film/paeleo-01.mp4" data-seg="4.0,30.0" data-len="1:35"><div class="screen"><video muted playsinline preload="metadata" poster="{up}paeleo/media/scion/lens-02.jpg"></video></div><figcaption class="cap">In operator order, each lens at its own telling moment. The sound is the loop's own: calls, the door, the soft voice, a paper flick on every cut, a chord for each family.</figcaption></figure></div>
  {reel_rounds(up)}
</section>

<section class="sec" id="anatomy"><div class="sechead"><h2>Anatomy of a swarm</h2><p>Every prompt has the same skeleton. What changes from swarm to swarm is what fills it.</p></div>
  <div class="cols">
    <div class="part"><h3>The header</h3><ul><li><b>Operator lineage</b>: the documented work it descends from.</li><li><b>Interpretation</b>: a new operational prompt inspired by that work, not a claim that its people wrote or endorsed it.</li><li><b>Identity</b>: "You are SCION-…, an autonomous animation swarm responsible for an exceptional finished, watchable animated work, not an essay or asset dump."</li><li><b>Input</b>: five slots to fill: <code>[WORK]</code>, <code>[DIRECTION_AND_REFERENCES]</code>, <code>[DELIVERY]</code>, <code>[RESOURCES]</code>, <code>[RIGHTS_SCOPE]</code>. Unknown rights are not permission.</li></ul></div>
    <div class="part"><h3>The eight sections</h3><ol class="recipe">{heads}</ol></div>
  </div>
  <div class="cols">
    <div class="part"><h3>What each section asks</h3><ul>
      <li><b>Theorem.</b> One claim the work must prove. For State Machines: turn a cast into actors who perceive, choose, resist and remember.</li>
      <li><b>Native formal language.</b> The primitives to keep as first-class things in the project, not flatten to pixels, with at least one invariant testable by number and one achievement judged only by viewing.</li>
      <li><b>Smallest capable swarm.</b> Named roles, each building or verifying a real artifact, merged when talking costs more than parallel work saves, and always a separate independent critic.</li>
      <li><b>Hard proof scene.</b> The most revealing short passage, produced first, with picture and sound, before any asset catalogue.</li>
      <li><b>The bar.</b> What has to be true, and the critic\'s return: pass, reference stronger or inconclusive; the exact frames; the largest gap; a falsifiable repair condition; the strengths to keep.</li>
      <li><b>Evolving inquiry.</b> What to test when it fails, and when two fixes fail, fork competing hypotheses with the same material and budget.</li>
      <li><b>Discovery.</b> A vocabulary to grow from what worked, and a living method library: technique, conditions, proof clip, failures, repair, rejected alternatives.</li>
      <li><b>Deliverable contract.</b> What to hand over, always including a phone-readable operator page with a playable preview, the current revision, the decisive verdict and the next blocking failure.</li></ul></div>
    <div class="part"><h3>One, in full</h3><details><summary>SCION 48 · State Machines, verbatim</summary><pre class="prompt">{esc(ex)}</pre></details>
      <p>All 54 are in the <a href="operator.html">operator</a>, and as data in <a href="swarms.json"><code>swarms.json</code></a>.</p></div>
  </div>
</section>

<section class="sec" id="doctrine"><div class="sechead"><h2>The doctrine</h2><p>Fifteen points every swarm inherits, headed "execute, do not summarize". The first sentence of each, as the prompts put it:</p></div>
  <ol class="recipe">{doctrine}</ol>
  <p class="note">And the line under them: use real tools and sources, never simulate an agent run in prose, and if something can\'t be run, deliver the smallest executable artifact and say what was not run. Success is a film someone can open and watch, or a bounded playable milestone that has actually passed its tests.</p>
</section>

<section class="sec" id="ran"><div class="sechead"><h2>How PAE-00 ran it</h2><p>The doctrine, point by point, against what actually happened when SCION 48 made <a href="{up}paeleo/threshold/">The threshold</a>. The case page has the full record.</p></div>
  <div class="tw"><table class="names"><thead><tr><th>Doctrine</th><th>What happened</th></tr></thead><tbody>{ran}</tbody></table></div>
</section>

<section class="sec" id="run"><div class="sechead"><h2>Running a swarm</h2></div>
  <ol class="recipe">
    <li>Pick the lineage whose theorem is the question your work is asking. Its lens here shows what that swarm will look at first.</li>
    <li>Copy the prompt from the operator and fill the five inputs. Leave nothing implied about rights.</li>
    <li>Build the hard proof scene first, end to end, with sound, before anything is scaled.</li>
    <li>Hand the playable proof to a critic who has the bar and the intended experience, not your notes. Keep its report word for word.</li>
    <li>Repair causes, not symptoms, and hand the new cut to a fresh critic. Stop at an independent pass, a human stop, the budget, or a justified no-progress boundary.</li>
    <li>Publish the operator page: the preview, the revision, the verdict, the next blocking failure. In PAELEO that page is the box\'s case.</li>
  </ol>
</section>

<section class="sec" id="all"><div class="sechead"><h2>The 54</h2><p>Each with its lens, its theorem, its proof scene and its lineage. Tap a picture to see that lens live.</p></div>{tiles}</section>
'''
    css = '''<style>
.lenses{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,330px),1fr));gap:16px}
.lens{border:1.5px solid var(--rule);background:var(--panel);border-radius:3px;display:grid;align-content:start;min-width:0;scroll-margin-top:16px}
.lens.run{border:2px solid var(--stamp);background:var(--label)}
.lens .im img{width:100%;height:auto;display:block;border-radius:2px 2px 0 0}
.lens .tx{padding:10px 12px 12px;display:grid;gap:4px}
.lens .id{font:600 11px var(--mono);color:var(--ink-2)}.lens .id em{font-style:normal;color:#fff;background:var(--stamp);padding:0 5px}
.lens b{font:800 22px/1.05 var(--display);text-transform:uppercase}.lens i{font-style:normal;font-size:14px;color:var(--ink-2)}
.lens .sh{font-size:15px;line-height:1.45;margin-top:4px}
.lens dl{margin:6px 0 0;display:grid;gap:2px;font-size:13.5px;line-height:1.4}.lens dt{font:600 10.5px var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--stamp);margin-top:4px}.lens dd{margin:0;color:var(--ink-2)}
.lens .lk{font:12px var(--mono);margin-top:6px}
#viewer canvas{width:100%;aspect-ratio:16/9;border-radius:2px;background:#1d2a4a}
#viewer select{font:13px var(--mono);padding:6px 8px;border:1.5px solid var(--ink);background:var(--label);color:var(--ink);width:100%;max-width:100%}
#viewer .look{font-family:var(--mono);font-size:14px}
</style>'''
    scripts = (f'<script src="{up}paeleo/threshold/machine.js"></script><script src="{up}paeleo/threshold/stage.js"></script><script src="swarms.js"></script><script src="lenses.js"></script><script src="viewer.js"></script>' + FILM_JS)
    html_ = page('paeleo/scion/index.html', 'SCION · the swarm operator', 'The SCION swarm operator: 54 animation swarms, how each prompt is built, the doctrine they share, and every one of them shown through the same paper dog.', body, image='paeleo/media/scion/lens-02.jpg', scripts=scripts)
    open(os.path.join(P, 'scion/index.html'), 'w').write(html_.replace('</head>', css + '</head>', 1))
    # the same write-up as Markdown, for reading in the repository
    md = ['# SCION · the swarm operator', '', 'Fifty-four animation swarms. Each is a standalone prompt that turns one artist, researcher, studio, algorithm or archive into a working studio with a proof to make and a critic to answer to. PAELEO films are made with them, one swarm per box. Live: ' + BASE + 'paeleo/scion/', '',
          f'- {len(SW)} swarms, in five families: {fams}', f'- 8 numbered sections in every prompt, in the same order; 15 points of doctrine, word for word the same in all 54; 5 inputs (work, direction, delivery, resources, rights)',
          f'- {A["words"][0]:,} to {A["words"][1]:,} words each, {A["words"][2]:,} in all; {A["urls"]} name a research starting point', '- Each name is a lineage, not an endorsement; the prompts say so themselves.', '',
          '## Anatomy', '', 'Header: operator lineage, interpretation, identity, the five inputs. Then:', ''] + [f'{k}. {h}' for k, h in enumerate(A['secs'], 1)] + ['', 'Then the inherited doctrine, and START NOW.', '',
          '## The doctrine', ''] + [f'{k}. **{n}.** {t}' for k, (n, t) in enumerate(A['doctrine'], 1)] + ['', '## How PAE-00 ran it', '', '| Doctrine | What happened |', '|---|---|'] + [f'| {n} | {t} |' for n, t in RAN] + ['',
          '## The 54 through the dog', '', 'Each lens (`lenses.js`) draws the same porch, dog and loop of prompts the way that swarm would; stills in `paeleo/media/scion/`, the reel is PAE-01.', '']
    for x in SW:
        md += [f'### SCION {x["id"]:02d} · {x["title"]}', '', f'*{x["family"]} · {x["lineage"]}*', '', f'- **Through the dog ({LD[x["id"]]["look"]}).** {LD[x["id"]]["show"]}', f'- **Theorem.** {A["per"][x["id"]]["theorem"]}', f'- **Proof scene.** {A["per"][x["id"]]["proof"]}', '']
    open(os.path.join(P, 'scion/README.md'), 'w').write('\n'.join(md) + '\n')


CHOICE = {'retreat': 'backs away', 'watch': 'watches', 'refuse': 'turns its back', 'approach': 'comes, head low', 'lie_down': 'lies across the sill'}


def rounds_of(d):
    """The critic rounds for one swarm folder: [(n, verdict class, verdict text, report)]."""
    import glob, re
    out = []
    for f in sorted(glob.glob(os.path.join(d, 'reviews/round*.md')), key=lambda f: int(re.findall(r'\d+', os.path.basename(f))[0])):
        txt = open(f).read(); head = txt.split('\n', 1)[0].rsplit('·', 1)[-1].strip()
        cls = 'fail' if head.upper().startswith('DOES NOT') else 'pass' if head.upper().startswith('PASS') else 'part'
        out.append((int(re.findall(r'\d+', os.path.basename(f))[0]), cls, head, txt))
    return out


def handmade_box(up):
    sw = [x for x in HM['swarms'] if os.path.exists(os.path.join(P, 'handmade', x['dir'], 'film.mp4'))]
    passed = sum(1 for x in sw if (rounds_of(os.path.join(P, 'handmade', x['dir'])) or [(0, '', '')])[-1][1] == 'pass')
    tiles = ''.join(f'<a class="sw run" href="handmade/#s{x["id"]:02d}"><img src="handmade/{x["dir"]}/stills/{os.path.basename(sorted(os.listdir(os.path.join(P, "handmade", x["dir"], "stills")))[-1])}" alt="" loading="lazy"><span class="id"><span>SCION {x["id"]:02d}</span><em>{esc(x["kind"])}</em></span><b>{esc(x["name"])}</b><i>{esc(x["trick"])}</i></a>' for x in sw)
    return f'''<section class="box" id="pae-02"><div class="boxhead"><div class="row"><span class="code">PAE-02</span><span class="lbl">Oct 24 · {len(sw)} swarms · 38 s each · {passed} passed by an independent critic</span></div>
    <h2>The threshold, handmade</h2><p class="q">{esc(HM["question"])}</p></div>
  <div class="trick"><span class="lbl">The trick</span><p>A lens restyles one drawing; PAE-02 asks each swarm to make the whole scene itself, from found footage, silhouettes, constraints, doodles or a torrent of archive tiles, under one score of the dog's choices. The score is checked against every film. Everything else differs.</p></div>
  <div class="queue">{tiles}</div>
  <div class="fullcase"><a href="handmade/"><i>PAE-02</i> All six films<span>each with its sheets, its measured invariants and its critic rounds</span></a></div>
</section>'''


def handmade_page():
    import glob, re
    up = '../../'; boxes = ''; rows = ''
    for s in HM['swarms']:
        d = os.path.join(P, 'handmade', s['dir'])
        if not os.path.exists(os.path.join(d, 'film.mp4')): continue
        inv = json.load(open(os.path.join(d, 'invariants.json')))
        rs = rounds_of(d); last = rs[-1] if rs else (0, 'part', 'awaiting the critic', '')
        stills = sorted(glob.glob(os.path.join(d, 'stills/*')), key=lambda f: float(re.findall(r'(\d+(?:\.\d+)?)s', os.path.basename(f))[0]))
        cap = ['refusal, 3.6 s', 'watching, 9 s', 'approach, 19 s', 'across the sill, 28 s']
        sh = ''.join(f'<figure><img src="{s["dir"]}/stills/{os.path.basename(f)}" alt="SCION {s["id"]:02d}, {c}" loading="lazy"><figcaption>{c}</figcaption></figure>' for f, c in zip(stills, cap))
        ch = ''.join(f'<span>{esc(CHOICE[c["to"]])} <b>{c["t"]:.2f} → {c["found_at"]:.2f} s</b></span>' for c in inv['I1_choices']['choices'])
        i2, i3, i4 = inv['I2_threshold'], inv['I3_direction'], inv['I4_refusal']
        rnd = ''.join(f'<details><summary>Critic round {n} · <span class="verdict {c}">{esc(v)}</span></summary><pre class="prompt">{esc(t)}</pre></details>' for n, c, v, t in rs)
        boxes += f'''<section class="box" id="s{s["id"]:02d}">
  <div class="boxhead"><div class="row"><span class="code">SCION {s["id"]:02d}</span><span class="lbl">{esc(s["kind"])} · 38 s · <span class="verdict {last[1]}">{esc(last[2])}</span></span></div>
    <h2>{esc(s["name"])}</h2><p class="q">{esc(s["trick"])}</p></div>
  <div class="hero">
    <figure class="film" data-src="{s["dir"]}/film.mp4" data-seg="3.0,35.0" data-len="0:38"><div class="screen"><video muted playsinline preload="metadata" poster="{s["dir"]}/stills/{os.path.basename(stills[2]) if len(stills) > 2 else ""}"></video></div><figcaption class="cap">The 32 s scene on the score, frame for frame; the whole film adds a title and a card saying what it is made of.</figcaption></figure>
    <div class="trick"><span class="lbl">Made of</span><p>{esc(s["made"])}</p><span class="lbl">Moved by</span><p>{esc(s["moved"])}</p></div>
  </div>
  <div class="part"><h3>The sheets</h3><div class="sheets">{sh}</div></div>
  <div class="cols">
    <div class="part"><h3>Did the description survive?</h3><p>Measured from this swarm's own render (its <a href="{s["dir"]}/trace.json">trace</a>) by <code>check_handmade.py</code>. The score's time, then the time the choice appears.</p>
      <div class="facts">{ch}</div>
      <ul><li><b>Never inside.</b> {"Holds" if i2["ok"] else "Fails"}: closest {i2["min_x"]:.2f} m from the door (the sill is at {SILL:.2f}); ends {i2["end_x"]:.2f} m.</li>
      <li><b>Follows the score.</b> {"Holds" if i3["ok"] else "Fails"}: r = {i3["r"]:.3f} between its position and the score's.</li>
      <li><b>The refusal shows the back.</b> {"Holds" if i4["ok"] else "Fails"}: turned in {i4["share_turned"]:.0%} of the refusal's frames.</li></ul></div>
    <div class="part"><h3>The critics</h3><p>Each round is a fresh agent that sees the film, the brief and this swarm's SCION prompt, never the builder's notes, and returns a verdict and falsifiable repairs. Stopped at an independent pass.</p>{rnd}
      <p class="lk"><a href="{s["dir"]}/method.md">method</a> · <a href="{s["dir"]}/assets.json">every asset and its rights</a> · <a href="{s["dir"]}/ledger.jsonl">ledger of attempts</a> · <a href="{s["dir"]}/build/make.sh">build</a> · <a href="{up}paeleo/scion/operator.html#s{s["id"]}">the prompt</a></p></div>
  </div>
</section>
'''
        rows += f'<tr><td><a href="#s{s["id"]:02d}">{s["id"]:02d} {esc(s["name"])}</a></td><td>{esc(s["made"].split(".")[0])}</td><td>{"all four hold" if inv["all_ok"] else "fails"}</td><td><span class="verdict {last[1]}">{esc(last[2])}</span>{f" (round {last[0]})" if last[0] else ""}</td></tr>'
    body = f'''<p class="crumbs"><a href="{up}">CRASH LAB</a> / <a href="{up}paeleo/">PAELEO</a> / PAE-02</p>
<header class="lockup"><div class="l"><span class="lbl">PAE-02 · one description, many operations</span><h1 style="font-size:clamp(56px,10vw,120px)">The threshold, handmade</h1>
  <p class="tag">{esc(HM["question"])}</p>
  <p>PAE-01 showed every SCION swarm as a lens on one paper dog: a style laid over a drawing it did not make. That shows what each swarm would look at, not what it would make. In PAE-02 each swarm builds the same scene itself: what the dog is made of, how it moves, what the place is and what it sounds like. Only two things are shared: the <a href="BRIEF.md">description</a> and the <a href="score/threshold-score.json">score</a> of the dog's six choices from the PAELEO machine.</p>
  <p><a class="btn" href="#cohort">The six</a> <a class="btn" href="BRIEF.md">The brief</a> <a class="btn" href="README.md">The write-up</a></p></div>
  <div class="r"><span class="lbl">Held still, then let go</span><dl class="letters"><dt>P</dt><dd>the prompts: <i>call, call and reach, sit down beside the door, open the door, offer a hand low, say it softly, come in</i></dd><dt>E</dt><dd>the ekphrasis and the score: six choices at fixed times, 768 frames</dd><dt>O</dt><dd>the operation: entirely the swarm's</dd></dl>
  <p class="lbl">If description is operative, the choices survive every operation, and that can be measured. Whether they read as choices is for a critic to say.</p></div></header>

<section class="sec" id="cohort"><div class="sechead"><h2>The first six</h2><p>One swarm from each family and two from the algorithms, chosen to be as far apart as possible in what they build with.</p></div>
  <div class="tw"><table class="names"><thead><tr><th>Swarm</th><th>The dog is</th><th>Invariants</th><th>Critic</th></tr></thead><tbody>{rows}</tbody></table></div>
  <p class="note">The invariants are the description (the six choices within ¼ s, never inside the house and ending on the sill, moving with the score, the back shown in the refusal). Everything that differs between the films is the operation.</p>
</section>
{boxes}
<section class="sec" id="next"><div class="sechead"><h2>What comes after</h2></div><ul>
  <li><b>The other 48.</b> Each swarm's lens in PAE-01 is its sketch for PAE-02; these six decide what the brief needs before it scales.</li>
  <li><b>After the threshold.</b> The next evening, when the door is already open: a swarm that kept the invariants carries its dog one scene further with the same materials. That tests whether its world is a world, or only a look.</li>
  <li><b>The language.</b> The score is the first piece of PAELEO the language: a description precise enough to operate and loose enough to be built six ways. Its next form is a file a person writes rather than a machine run.</li></ul>
</section>
'''
    open(os.path.join(P, 'handmade/index.html'), 'w').write(page('paeleo/handmade/index.html', 'PAE-02 · The threshold, handmade', HM['question'], body, image='paeleo/handmade/53-civic-footage/stills/scene_28.00s.jpg', scripts=FILM_JS))


SILL = json.load(open(os.path.join(P, 'handmade/score/threshold-score.json')))['places']['sill']

if __name__ == '__main__':
    index(); case_page(); scion_page(); handmade_page(); print('built paeleo pages')
