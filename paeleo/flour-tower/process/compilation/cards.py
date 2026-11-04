import json
CSS="""<style>
@font-face{font-family:BSD;src:url(file:///home/claude/yt/fonts/BigShouldersDisplay.ttf)}
@font-face{font-family:LIT;src:url(file:///home/claude/yt/fonts/Literata.ttf)}
@font-face{font-family:JBM;src:url(file:///home/claude/yt/fonts/JetBrainsMono.ttf)}
html,body{margin:0;width:1920px;height:1080px;background:#0b0d10;color:#e7eaee;overflow:hidden}
.c{position:absolute;inset:0;padding:120px 150px;display:flex;flex-direction:column;justify-content:center;gap:28px}
.k{font-family:JBM;font-size:26px;letter-spacing:.14em;text-transform:uppercase;color:#7aa2ff}
h1{font-family:BSD;font-weight:800;font-size:190px;line-height:.86;margin:0;text-transform:uppercase}
h2{font-family:BSD;font-weight:800;font-size:150px;line-height:.9;margin:0}
p{font-family:LIT;font-size:44px;line-height:1.35;margin:0;max-width:1450px;color:#d6dbe1}
.m{font-family:JBM;font-size:28px;color:#8b95a1;letter-spacing:.04em}
.ok{color:#5fc187}
.sw{padding-right:880px}.sw p{font-size:40px}
.shot{position:absolute;right:120px;top:50%;transform:translateY(-50%);width:720px;border:2px solid #262d35}
</style>"""
def page(body): return "<!doctype html><meta charset=utf-8>"+CSS+body
cards={}
cards['00-open']=page("""<div class=c><div class=k>CRASH LAB · PAELEO · PAE-03</div><h1>The flour tower,<br>handmade</h1>
<p>One story. One score of ten choices. Six swarms, each building a flour sack from nothing in its own language.</p></div>""")
cards['01-story']=page("""<div class=c><div class=k>The story · 32 seconds · held still</div>
<p>A knife slices a tower of packed flour with a penny on top. A half-empty flour sack flinches, notices the tower lean, comes to it head low and holds it up.</p>
<p>The tower falls. The sack catches the penny, gathers the flour back into itself, and stands where the tower stood. The knife hovers, and leaves.</p>
<div class=m>Disney's 1930s flour-sack test: no face, no limbs. Mood by weight, silhouette and corners.</div></div>""")
SW=[('02','Silhouette theatre','Lotte Reiniger','Five cut card pieces on four pins, swapped from a library of 343 replacement lobes. Nothing is scaled.','PASS (narrow)'),
('06','Harmonic motion','John Whitney','A closed curve made of harmonics, drawn in points of light. The flour is 996 counted dots.','PASS (narrow)'),
('07','Drawn metamorphosis','Peter Foldès','One pen line of 64 corresponding points. It ends as the tower’s own outline.','PASS'),
('08','Constraint Sketchpad','Ivan Sutherland','A ring of 29 points solved every frame. It is never placed, only pulled by light-pen goals.','PASS (narrow)'),
('14','Drawing selection','Pose2Pose casting','46 hand-drawn sacks. Each frame casts one whole drawing; nothing is drawn in between.','PASS (narrow)'),
('41','Cloth and grain','Soft body','A simulated cloth bag holding real grains. The tower is the same 753 grains.','PASS')]
for n,kind,name,made,v in SW:
    cls='ok'
    FN={'02':'02-reiniger','06':'06-whitney','07':'07-foldes','08':'08-sutherland','14':'14-pose2pose','41':'41-soft-body'}[n]
    cards[f'sw{n}']=page(f"""<img class=shot src="file:///home/claude/yt/frames/{FN}/0870.jpg"><div class="c sw"><div class=k>SCION {n} · {kind}</div><h2>{name}</h2><p>{made}</p>
<div class=m>Independent critic: <span class={cls}>{v}</span></div></div>""")
cards['99-end']=page("""<div class=c><div class=k>PAE-03 · the result</div>
<p>In all six films the ten choices landed within a quarter second of the score, and the flour was accounted for.</p>
<p>Every critic kept finding the same five faults: the cause came too late, the penny got tossed, the brace vanished, the sack went top-heavy, and the self-checks were kinder than the picture.</p>
<div class=m>Watson Hartsoe · CRASH LAB · hartswf0.github.io/bolas/paeleo/flour-tower/<br>Films built by SCION swarms and judged by independent critics (Claude)</div></div>""")
json.dump(SW,open('sw.json','w'))
for k,v in cards.items(): open(f'cards/{k}.html','w').write(v)
print(list(cards))
