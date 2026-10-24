"""Build the PAELEO pages: paeleo/ (the program), paeleo/threshold/ (PAE-00's full case) and paeleo/scion/ (the 54-swarm queue).
python3 tools/paeleo/build_pages.py   (reads tools/paeleo/case.json and paeleo/scion/swarms.json)"""
import html, json, os

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(R, 'paeleo')
esc = html.escape
CASE = json.load(open(os.path.join(R, 'tools/paeleo/case.json')))
SW = json.load(open(os.path.join(P, 'scion/swarms.json')))
RUN = {48: ('PAE-00', 'threshold/')}   # swarms that have been run, and the case they made

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
            href = f'{up}paeleo/{run[1]}' if run and link_case else f'{up}paeleo/scion/operator.html#s{s["id"]}'
            tiles += (f'<a class="sw{" run" if run else ""}" href="{href}"><span class="id"><span>SCION {s["id"]:02d}</span>{f"<em>{run[0]} · run</em>" if run else "<span>unopened</span>"}</span>'
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
</section>

<section class="sec" id="queue"><div class="sechead"><h2>The swarm queue</h2><p>Fifty-four SCION animation swarms, each a standalone prompt studio with its own proof scene and research loop. PAE-00 was made by number 48. The rest are unopened boxes. <a href="scion/">Read the queue</a> · <a href="scion/operator.html">open the operator</a>.</p></div>
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
<section class="sec" id="sheets"><div class="sechead"><h2>Sheets</h2></div><div class="sheets">{sheets}</div></section>
<section class="sec" id="prompt"><div class="sechead"><h2>The prompt</h2><p>SCION 48, State Machines: Characters That Can Refuse, verbatim from the SCION operator. Its proof scene is this film's middle: a dog chooses among watch, approach, retreat, lie down and refuse, and the player has to change circumstances to earn approach.</p></div>
  <details open><summary>SCION-STATE-MACHINES</summary><pre class="prompt">{esc(prompt)}</pre></details>
  <div class="part"><h3>How the inputs were filled</h3><ul>{"".join(f"<li><b>{esc(k)}</b> {esc(v)}</li>" for k, v in c["inputs"])}</ul></div>
</section>
<section class="sec" id="files"><div class="sechead"><h2>Files</h2></div><ul>{"".join(f'<li><a href="{up}{esc(h)}"><code>{esc(h)}</code></a> {esc(t)}</li>' for h, t in c["files"])}</ul></section>
'''
    scripts = ('<script src="machine.js"></script><script src="stage.js"></script><script src="try.js"></script>' + FILM_JS)
    open(os.path.join(P, 'threshold/index.html'), 'w').write(page('paeleo/threshold/index.html', 'PAE-00 · The threshold', c['question'], body, scripts=scripts))


def scion_page():
    up = '../../'
    body = f'''<p class="crumbs"><a href="{up}">CRASH LAB</a> / <a href="{up}paeleo/">PAELEO</a> / SCION</p>
<header class="lockup"><div class="l"><span class="lbl">SCION / lineage forge</span><h1 style="font-size:clamp(64px,12vw,140px)">SCION</h1>
  <p class="tag">Fifty-four animation swarms. Each is a standalone prompt studio with a creative theorem, a native formal language, a smallest capable swarm, a hard proof scene, a bar, and an independent critic.</p>
  <p>They come from four families: artists and directors, research pioneers, studios and software, algorithms and techniques, and archives and provenance. Every one inherits the same fifteen-point operating doctrine: hard proof first, an independent critic, honest evidence, and stop when the film is watchable.</p>
  <p><a class="btn" href="operator.html">Open the operator</a> &nbsp; search all 54, copy any prompt, save it as Markdown</p></div>
  <div class="r"><span class="lbl">Run so far</span><p><b>SCION 48 · State Machines</b> made <a href="{up}paeleo/threshold/">PAE-00 The threshold</a>, the program's introduction.</p>
  <p class="lbl">Each name is a lineage, not an endorsement: these are new operational prompts inspired by documented work.</p></div></header>
<section class="sec"><div class="sechead"><h2>The queue</h2></div>{queue(up)}</section>
'''
    open(os.path.join(P, 'scion/index.html'), 'w').write(page('paeleo/scion/index.html', 'SCION · the swarm queue', 'The 54 SCION animation swarms PAELEO films are made with, and which ones have been run.', body))


if __name__ == '__main__':
    index(); case_page(); scion_page(); print('built paeleo pages')
