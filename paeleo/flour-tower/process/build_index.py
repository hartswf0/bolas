import html, json, os, re
R = '/home/claude/pae03'
def md(p):
    p = os.path.join(R, p)
    return open(p).read() if os.path.exists(p) else None

SCORE = [
 (1.00,'knife cut 1','flinches back'),(4.00,'knife cut 2','flinches again, less'),
 (6.50,'tower starts to lean, flour sifts','notices'),(9.00,'','comes, head low'),
 (14.50,'','props the tower'),(18.00,'knife cut 3','braces'),
 (21.00,'cut 4; the tower falls; the penny drops',''),(21.40,'','leaps'),
 (22.40,'the penny lands on the sack','catches'),(23.00,'','lands in a squash'),
 (24.50,'','gathers the flour in'),(30.00,'the knife hovers over the penny','stays'),
 (31.20,'the knife withdraws',''),
]

SW = [
 dict(n='02', name='Lotte Reiniger', kind='Silhouette theatre', file=None, status='building',
      thesis='A sack with no face must decide in silhouette alone.',
      made='Hand-cut black card on a lit screen, built from pieces on pins, with a library of replacement lobes for each fullness.'),
 dict(n='06', name='John Whitney', kind='Harmonic motion', file='06-whitney.html', status='pass',
      verdict='PASS (narrow) · round 3', crit=['critic/06/round1.md','critic/06/r2/round2.md','critic/06/r3/round3.md'],
      thesis='A sack is a chord: knocked out of tune by the knife, it comes into tune as it decides, and it is full when every partial locks.',
      made='Only points of light on black. The sack is about 150 dots on a closed curve whose radius is a sum of harmonics: low terms and a sin 3θ gravity term pool the bottom, two cosine sums make the corners. The flour is 996 dots, counted every frame and never created or destroyed; the sack holds one dot per unit of its volume.',
      moved='The score times only retarget damped oscillators or fire impulses into them; five phase oscillators carry the mood, detuned under the knife and locking as it decides. The gait, the knife strike and each grain flight are scheduled phasor windows, named on the card. The penny falls by an integrated ballistic step.',
      honest='Breach kept on record: at 14.0 s the sack is at x 0.30, against the score\'s 0.40; the film\'s own check marked this HOLDS with a self-set 0.1 m tolerance. The flank pressed against the tower is a plane projection, not a harmonic.',
      onsets=[('flinch',1,1.00),('flinch less',4,4.00),('notice',6.5,6.58),('come, head low',9,9.00),('prop',14.5,14.29),('brace',18,18.04),('leap',21.4,21.46),('catch',22.4,22.42),('land',23,23.00),('gather',24.5,24.54),('stay',30,29.79)]),
 dict(n='07', name='Peter Foldès', kind='Drawn metamorphosis', file='07-foldes.html', status='pass',
      verdict='PASS (round 2)', crit=['critic/07/round1.md','critic/07/round2.md'],
      thesis='A shape turns into another shape only because something happened to it: the sack ends as the tower\'s outline because it caught what fell.',
      made='Every body is one closed pen line of 64 points; point i is the same place in every drawing. 22 contour keys for the sack, 7 for the tower and pile. The full sack\'s key is the uncut tower\'s outline with its two corners tied up.',
      moved='Each frame blends two keys point for point, paced by the score. Corners take the pose from three frames earlier, so they drag. Travel comes only from a planted bottom corner or a parabola in the air. The tower\'s lean stops where it meets the sack\'s drawn points. In the gather the pile\'s outline is carried point for point into the sack\'s.',
      honest='Volume is held by one vertical rescale after each blend (raw blends drift −3.7% to +5.7%); the page says so.'),
 dict(n='08', name='Ivan Sutherland', kind='Constraint Sketchpad', file='08-sutherland.html', status='pass',
      verdict='PASS (narrow) · round 3', crit=['critic/08/round1.md','critic/08/r2/round2.md','critic/08/r3/round3.md'],
      thesis='Nothing on this scope is drawn where it stands; every point is where the constraints leave it.',
      made='Points and lines on a simulated phosphor scope. The sack is a ring of 29 points held by edge, strut, fold-limit and AREA constraints, with two corner points on springs; the tower is 48 welded blocks; tower, pile, grains in transit and the sack\'s area target are one ledger that sums to a constant.',
      moved='A relaxation solver runs every frame, warm-started from the last: edge length, enclosed area, floor contact with stick-or-step friction, tower and penny contact. The sack is never placed; it is driven only by light-pen goals on its seam and base, drawn as dashed lines. The sack\'s contact can stop the tower\'s tipping but cannot push it back. After the fourth cut the penny is a free point that falls.',
      honest='The penny falls at a capped 0.20 m/s, so it drifts more than drops. During the gather the seam goal is computed from fill, not solved. At 14.0 s the sack\'s centre is at x −0.2 (its leading edge near 0.40): this sack is about 1 m wide.',
      onsets=[('flinch',1,1.04),('flinch less',4,4.04),('notice',6.5,6.67),('come, head low',9,9.08),('prop',14.5,14.42),('brace',18,18.04),('leap',21.4,21.42),('catch',22.4,22.21),('land',23,23.00),('gather',24.5,24.54),('stay',30,29.875)]),
 dict(n='14', name='Pose2Pose casting', kind='Drawing selection', file='14-pose2pose.html', status='pass',
      verdict='PASS (narrow) · round 3', crit=['critic/14/round1.md','critic/14/round2.md','critic/14/r3/round3.md'],
      thesis='Performance is casting: every frame, pick one whole drawing from the bank, and never draw between them.',
      made='A bank of 46 separate ink-and-wash sack drawings, each a hand-placed outline with its own folds and corners, plus small banks for the tower, pile, knife and penny.',
      moved='The score names a pose family per exposure; a Viterbi path over pose distance and transition cost picks one whole drawing, held on twos (threes on the approach). Nothing is tweened. While a drawing is held its base does not move; travel comes from shuffle drawings with alternating planted corners.',
      honest='Each drawing has one fixed height trim (0.91–1.16) so its area matches its class; the family is a hard filter, so selection works within a family.'),
 dict(n='41', name='Soft body', kind='Simulated cloth and grain', file='41-soft-body.html', status='pass',
      verdict='PASS (round 3)', crit=['critic/41/round1.md','critic/41/r2/round2.md','critic/41/r3/round3.md'],
      thesis='A sack is a bag of flour: if the cloth and the grains are simulated, weight, drag and volume come out of the physics, and the only acting left is when the sack chooses to pull a muscle.',
      made='A closed ring of 48 Verlet points with nearly inextensible stretch links, soft bend links, an area constraint and two spring-chain corner flaps, filled with 327 colliding flour grains that pool at the bottom. The tower, the pile and the sack\'s filling are the same 753 grains, counted every frame.',
      moved='The score sets only muscles: pulls toward a pose, a mid-height bend, push-offs while touching the table. Everything after a choice is integrated at a fixed 1/144 s step: squash, rebound, ear drag, slosh, hops held by friction, the gather. The run is deterministic and cached per frame for scrubbing.',
      honest='Scored, and named on the card: the tower\'s lean creep and slow righting, the timed knife, a fixed penny flick, the leap aimed at the penny, the caught penny riding the cloth, the gather flow field, and gravity at 1.8 m/s² as a style choice.',
      onsets=[('flinch',1,1.083),('flinch less',4,4.083),('notice',6.5,6.708),('come, head low',9,9.167),('prop',14.5,14.583),('brace',18,18.167),('leap',21.4,21.458),('catch',22.4,22.417),('land',23,22.75),('gather',24.5,24.583),('stay',30,30.0)]),
]

def onsets(n):
    p = f'{R}/stills/{n}-check.json'
    if not os.path.exists(p): return None
    c = json.loads(open(p).read())
    rows = []
    if n == '07':
        for k, v in c['onsets'].items(): rows.append((k, v['score'], v['measured']))
    elif n == '14':
        m = [('flinch','flinch1',1),('flinch less','flinch2',4),('notice','notice',6.5),('come, head low','comes',9),('prop','props',14.5),('brace','braces',18),('leap','leaps',21.4),('catch','catches',22.4),('land','lands',23),('gather','gathers',24.5),('stay','stays',30)]
        for a, k, s in m: rows.append((a, s, c[k]))
    return rows

E = html.escape
def section(s):
    st = {'pass':'PASS','repair':'IN REPAIR','review':'UNDER REVIEW','building':'BUILDING'}[s['status']]
    out = [f'<section class="sw" id="s{s["n"]}"><div class="swhead"><span class="no">SCION {s["n"]}</span><span class="kind">{E(s["kind"])}</span><span class="st st-{s["status"]}">{st}</span></div>',
           f'<h3>{E(s["name"])}</h3><p class="thesis">{E(s["thesis"])}</p>']
    if s['status'] != 'pass':
        out.append(f'<p class="note">{E(s["made"])} {("<b>"+E(s["verdict"])+".</b>") if s.get("verdict") else "Still being built; it will appear here after an independent critic passes it."}</p></section>')
        return ''.join(out)
    out.append('<div class="sheets">' + ''.join(
        f'<figure><img src="stills/{s["n"]}-{t}.jpg" alt="SCION {s["n"]}, {lab}, {t} s" loading="lazy"><figcaption>{lab} · {t} s</figcaption></figure>'
        for t, lab in [('4.1','flinch'),('15.5','propping'),('22.5','the catch'),('29.0','full, the penny on top')]) + '</div>')
    out.append(f'<div class="two"><div><h4>Made of</h4><p>{E(s["made"])}</p></div><div><h4>Moved by</h4><p>{E(s["moved"])}</p></div></div>')
    out.append(f'<p class="note">{E(s["honest"])}</p>')
    rows = s.get('onsets') or onsets(s['n'])
    if rows:
        out.append('<h4>Did the description survive?</h4><p class="sub">Measured from this film\'s own render. Score time, then the time the choice appears.</p><div class="ons">')
        for k, a, b in rows:
            ok = abs(b - a) <= 0.25
            out.append(f'<span class="on {"" if ok else "bad"}">{E(k)} <b>{a:.2f} → {b:.2f} s</b></span>')
        out.append('</div>')
    out.append(f'<p class="act"><a class="btn" href="films/{s["file"]}">Play the film</a><span class="verdict">{E(s["verdict"])}</span></p>')
    cr = [(p, md(p)) for p in s.get('crit', [])]
    cr = [(p, t) for p, t in cr if t]
    if cr:
        out.append('<h4>The critics</h4><p class="sub">Each round is a fresh agent that sees the film, the brief and the lineage\'s bar, never the builder\'s notes.</p>')
        for p, t in cr:
            head = t.splitlines()[0].lstrip('# ').strip()
            out.append(f'<details><summary>{E(head)}</summary><pre>{E(t)}</pre></details>')
    out.append('</section>')
    return ''.join(out)

rows = ''.join(
    f'<tr><td><a href="#s{s["n"]}">{s["n"]} {E(s["name"])}</a></td><td>{E(s["made"].split(".")[0])}</td><td class="stc st-{s["status"]}">{ {"pass":"PASS","repair":"in repair","review":"under review","building":"building"}[s["status"]] }</td></tr>'
    for s in SW)
score = ''.join(f'<tr><td class="num">{t:.2f}</td><td>{E(w)}</td><td><b>{E(c)}</b></td></tr>' for t, w, c in SCORE)

import sys
BOLAS = len(sys.argv) > 1
page = open(f'{R}/index.tpl.html').read()
page = page.replace('{{ROOT}}', '../../' if BOLAS else 'https://hartswf0.github.io/bolas/')
page = page.replace('{{VIDEO}}', '<figure class="cut"><video controls playsinline preload="metadata" poster="film/thumbnail.jpg" src="film/pae03-flour-tower.mp4"></video><figcaption>All six films cut together, 4 min. The same score plays under each one.</figcaption></figure>' if BOLAS else '')
page = page.replace('{{COHORT}}', rows).replace('{{SCORE}}', score).replace('{{SWARMS}}', ''.join(section(s) for s in SW))
open(sys.argv[1] if BOLAS else f'{R}/index.html', 'w').write(page)
print('ok', len(page))
