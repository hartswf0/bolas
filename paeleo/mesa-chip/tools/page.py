"""Writes the PAE-09 page (index.html) from the swarms' own files: prompt, method, invariants, stills and critic rounds."""
import json, os, re, html
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'); PAE = os.path.join(ROOT, '..')
head = open(os.path.join(PAE, 'handmade', 'index.html')).read().split('<div class="wrap">\n<p class="crumbs">')[0]
TITLE, TAG = 'MESA CHIP, handmade', 'One scene from the game, the glass knight under the dune, held still as a description and a score. Four SCION swarms each build it from the bottom up. Does the scene survive, and is each world its own?'
head = re.sub(r'<title>.*?</title>', f'<title>PAE-09 · {TITLE} · CRASH LAB</title>', head)
head = re.sub(r'content="Hold the description[^"]*"', f'content="{html.escape(TAG)}"', head)
head = head.replace('paeleo/handmade/', 'paeleo/mesa-chip/').replace('PAE-02 · The threshold, handmade', f'PAE-09 · {TITLE}').replace('53-civic-footage/stills/scene_28.00s.jpg', 'poster.jpg')
S = [('m1-tekle', 'M1', 'Afewerk Tekle', 'Leaded light', 'One window, cut once; only the light moves.', 'a light passing through one fixed window of about 4,970 pieces of glass'),
     ('m2-lucasfilm-1985', 'M2', 'Lucasfilm Computer Division, 1985', 'Convex shard CG', 'Every pose keyed by hand; every shard catches its own light.', '160 convex shards on a hand-keyed skeleton, with a specular pass, motion blur and a rack focus'),
     ('m3-mambety', 'M3', 'Djibril Diop Mambéty', 'Griot collage', 'The clock is kept and the angle broken: told, not shot.', "torn paper cut from the game's own footage, stiff cards, a griot's cutting"),
     ('m4-moebius-otomo', 'M4', 'Mœbius and Otomo', 'Ligne claire', 'Calm drawing, uncalm events: the outline blooms, then breaks.', 'one constant black line, flat colour, cast shadow, light trails and a bloom before each break')]
def md_inline(s): return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', re.sub(r'`([^`]+)`', r'<code>\1</code>', html.escape(s)))
def section(md, name):
    m = re.search(r'## ' + name + r'.*?\n(.*?)(?=\n## |\Z)', md, re.S); return m.group(1).strip() if m else ''
def bullets(txt): return '<ul>' + ''.join(f'<li>{md_inline(l.strip()[2:])}</li>' if l.startswith('- ') else f'<li style="margin-left:1.2em;list-style:circle">{md_inline(l.strip()[2:])}</li>' for l in txt.splitlines() if l.strip().startswith('- ')) + '</ul>'
def verdict_of(md):
    v = md.splitlines()[0].split('·')[-1].strip(); cls = 'pass' if v.startswith('PASS') else ('fail' if 'REFERENCE' in v or 'NOT' in v else 'part'); return v, cls
rows, boxes = [], []
for slug, code, name, kind, q, isof in S:
    d = os.path.join(ROOT, slug); inv = json.load(open(os.path.join(d, 'invariants.json'))); meth = open(os.path.join(d, 'method.md')).read()
    revs = sorted(f for f in os.listdir(os.path.join(d, 'reviews')) if f.startswith('round')) if os.path.isdir(os.path.join(d, 'reviews')) else []
    last = verdict_of(open(os.path.join(d, 'reviews', revs[-1])).read()) if revs else ('not yet reviewed', 'part')
    ok = all(inv[k]['ok'] for k in ('I1', 'I2', 'I3', 'I4')); n_ok = sum(inv[k]['ok'] for k in ('I1', 'I2', 'I3', 'I4'))
    rows.append(f'<tr><td><a href="#{slug}">{code} {html.escape(name)}</a></td><td>{html.escape(isof)}</td><td>{"all four hold" if ok else f"{n_ok} of four hold"}</td><td><span class="verdict {last[1]}">{html.escape(last[0])}</span>{f" (round {len(revs)})" if revs else ""}</td></tr>')
    stills = sorted(f for f in os.listdir(os.path.join(d, 'stills')) if f.startswith('still_'))
    pick = [s for s in stills if any(k in s for k in ('03.2', '09.9', '12.5', '20.0', '22.8'))]
    sheets = ''.join(f'<figure><img src="{slug}/stills/{s}" alt="{code} {name}, {s[6:-5]} s" loading="lazy"><figcaption>{s[6:-5].lstrip("0")} s</figcaption></figure>' for s in pick)
    facts = ''.join(f'<span>{e["what"].replace("_", " ")} <b>{e["t"]:.2f} → {e["found_at"]:.2f} s</b></span>' if e['found_at'] is not None else f'<span>{e["what"]} <b>{e["t"]:.2f} → not found</b></span>' for e in inv['I1']['events'])
    i2, i3, i4 = inv['I2'], inv['I3'], inv['I4']
    meas = (f'<li><b>Out of the glass.</b> {"Holds" if i2["ok"] else "Fails"}: inside the window in {i2["inside_before_4_5"]:.0%} of frames before 4.5 s, outside it in {i2["outside_after_5_5"]:.0%} after 5.5 s.</li>'
            f'<li><b>The pieces stay, in their colour.</b> {"Holds" if i3["ok"] else "Fails"}: ' + ', '.join(f'{p["paint"]} {p["colour_match"]:.0%}' for p in i3['pieces']) + ' of each shot\'s pixels hold its paint to the end.</li>'
            f'<li><b>The distance follows the score.</b> {"Holds" if i4["ok"] else "Fails"}: {i4["within_15pct"]:.0%} of frames within 15 %, r = {i4["r"]:.3f}.</li>')
    if inv.get('skipped_frames'): meas += f'<li><b>Measured on the master.</b> {inv["measured_frames"]} of 576 frames. The {inv["skipped_frames"]} insert and re-telling frames are listed in the <a href="{slug}/trace.json">trace</a>.</li>'
    crit = ''.join(f'<details><summary>Critic round {i + 1} · <span class="verdict {verdict_of(open(os.path.join(d, "reviews", r)).read())[1]}">{html.escape(verdict_of(open(os.path.join(d, "reviews", r)).read())[0])}</span></summary><pre class="prompt">{html.escape(open(os.path.join(d, "reviews", r)).read())}</pre></details>' for i, r in enumerate(revs))
    boxes.append(f'''<section class="box" id="{slug}">
  <div class="boxhead"><div class="row"><span class="code">SCION {code}</span><span class="lbl">{kind} · 24 s · <span class="verdict {last[1]}">{html.escape(last[0])}</span></span></div>
    <h2>{html.escape(name)}</h2><p class="q">{html.escape(q)}</p></div>
  <div class="hero">
    <figure class="film" data-src="{slug}/film.mp4" data-seg="2.0,20.5" data-len="0:24"><div class="screen"><video muted playsinline preload="metadata" poster="{slug}/stills/{[s for s in stills if "16.4" in s][0]}"></video></div><figcaption class="cap">The scene on the score, frame for frame.</figcaption></figure>
    <div class="trick"><span class="lbl">Thesis</span>{bullets(section(meth, "Thesis"))}<span class="lbl">Made of</span>{bullets(section(meth, "Made of"))}</div>
  </div>
  <div class="part"><h3>The sheets</h3><div class="sheets">{sheets}</div></div>
  <div class="cols">
    <div class="part"><h3>Did the description survive?</h3><p>Measured from this swarm's own pixels and label mask by <code>tools/common.py</code>. For each event, the score's time, then the time it appears on screen.</p><div class="facts">{facts}</div><ul>{meas}</ul>
      <p class="note"><b>Known limits.</b> {md_inline(section(meth, "Known limits"))}</p></div>
    <div class="part"><h3>The critics</h3><p>Each round is a fresh agent. It sees the film, the brief and this swarm's SCION prompt, never the builder's notes or code.</p>{crit or "<p>Not yet reviewed.</p>"}
      <p><a href="{slug}/prompt.md">The SCION prompt</a> · <a href="{slug}/method.md">Method</a> · <a href="{slug}/invariants.json">Invariants</a> · <a href="{slug}/build/">Build</a></p></div>
  </div>
</section>''')
body = f'''<div class="wrap">
<p class="crumbs"><a href="../../">CRASH LAB</a> / <a href="../../paeleo/">PAELEO</a> / PAE-09</p>
<header class="lockup"><div class="l"><span class="lbl">PAE-09 · one scene from the game, four operations</span><h1 style="font-size:clamp(52px,9vw,112px)">{TITLE}</h1>
  <p class="tag">{html.escape(TAG)}</p>
  <p>In the MESA CHIP game (make-photo/mesa), Uncle Mesa goes down into a glass cathedral under the dune, and a knight of stained glass steps out of the canyon wall. PAE-09 does what PAE-02 did with the dog at the threshold. The <a href="EKPHRASIS.txt">description</a> and the <a href="score/glass-knight-score.json">score</a> are held still. The score is the game's own knight machine run once: ten events in 24 s. Four new SCION swarms each build the scene themselves.</p>
  <p><b>Uncle Mesa</b> is a Black man in his sixties with a long white beard and gold-lensed round glasses. He wears a cream wide-brimmed hat, a white guayabera-style shirt, khaki trousers and dark boots, and carries a six-shooter of paint. <b>The knight</b> is made of silver, gold and red glass, with a red glass sword.</p>
  <p><a class="btn" href="#cohort">The swarms</a> <a class="btn" href="BRIEF.md">The brief</a> <a class="btn" href="swarms.json">The four prompts</a> <a class="btn" href="https://hartswf0.github.io/make-photo/mesa/">Play the game</a></p></div>
  <div class="r"><span class="lbl">Held still, then let go</span><dl class="letters"><dt>P</dt><dd>the prompts: four new SCION studios in the operator's eight sections, inheriting the fifteen-point doctrine word for word</dd><dt>E</dt><dd>the ekphrasis and the score: ten events, six shots of paint, 576 frames</dd><dt>O</dt><dd>the operation: entirely the swarm's</dd></dl>
  <p class="lbl">If the description is operative, the scene survives every operation, and that can be measured from the pixels. Whether it reads as the scene is for a critic to say.</p></div></header>
<section class="sec" id="cohort"><div class="sechead"><h2>The swarms</h2><p>Four lineages named in the brief for the game's knight, as far apart as possible in what they build with.</p></div>
  <div class="tw"><table class="names"><thead><tr><th>Swarm</th><th>The scene is</th><th>Invariants</th><th>Critic</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
  <p class="note">The invariants are the description: every event within ¼ s; the knight out of the glass and from nowhere else; every piece on the floor to the end, in the colour of the shot that freed it; the distance between them moving with the score.</p>
</section>
{"".join(boxes)}
<footer>
  <span>PAELEO · a research program of CRASH LAB · Bolas · Watson Hartsoe, with Claude.</span>
  <span>SCION prompts are new operational prompts inspired by documented work; they are not claims that the people named wrote or endorsed them. Every picture here is made by this project: the swarms' own code, and for M3 the game's own frames.</span>
</footer>
</div>
'''
script = open(os.path.join(PAE, 'handmade', 'index.html')).read(); script = script[script.rindex('<script>'):]
open(os.path.join(ROOT, 'index.html'), 'w').write(head + body + script)
print('page written', len(head + body + script))
