import json
d={e['id'][:8]:e['id'] for e in json.load(open('/home/user/bolas/tools/allways-forage/index.json'))}
L=[0,.25,.5,.5]; R=[.5,.25,.5,.5]; FULL=[0,0,1,1]
def lay(p,i,box,audio=True,g=0): return {"src":d[p],"media":"clip","in":i,"box":box,"fit":"contain","audio":audio,"gain_db":g,"afade_in":.15,"afade_out":.2}
CARD={"dur":4,"label":"source card","fade_in":.5,"fade_out":.8,"card":{"lines":["Sources: movingimagearchive.com · see ledger"],"size":20}}
ev=[
 # P1 desks: left Two Pay Days 1927 (silent), right Bookkeeping and Accounting 1945
 {"dur":6.8,"fade_in":.6,"label":"P1 correspondence: two men bent over paperwork at desks. L Two Pay Days 1927 counts (silent); R Bookkeeping & Accounting 1945 writes in ledger, on the phone (source sound)",
  "layers":[lay('3b9d2889',0.0,L),lay('c688de99',0.0,R,True,4)]},
 {"dur":4.6,"label":"P1 mismatch held: right footage ends (black, silence); left continues to its own cut — the calendar insert 'Pay Day' (source's own cut at 8.5s)",
  "layers":[lay('3b9d2889',6.8,L)]},
 # P2 hands
 {"dur":13.0,"label":"P2a: two hands placing small parts. L Learning to Set Type 1959 sets type into a composing stick (its sound); R Wallops Island 1965 hands fit payload parts (muted)",
  "layers":[lay('aaf17c56',1.0,L,True,6),lay('e617813e',2.0,R,False)]},
 {"dur":5.5,"label":"P2b: rhythms briefly together, both sounds; L holds the filled stick still; R hands withdraw, parts stand alone",
  "layers":[lay('aaf17c56',14.0,L,True,6),lay('e617813e',15.0,R,True,0)]},
 {"dur":4.5,"label":"P2c: L silent and still; R hands return and lift the top part off again — the assembly restarts",
  "layers":[lay('aaf17c56',19.5,L,False),lay('e617813e',20.5,R,True,0)]},
 # P3 doors
 {"dur":12.6,"label":"P3a: two men in dark suits, backs to camera, before closed doors. L Door to Heaven 1941 knocks on a painted-sky set (its sound); R Wreckless 1935 stands with hat in hand beside a seated secretary (its room tone)",
  "layers":[lay('9199c819',0.6,L,True,6),lay('ef7bfc89',5.6,R,True,8)]},
 {"dur":1.7,"label":"P3b final hold: left has faded out in its own source; right man turns from the door and walks toward camera",
  "layers":[lay('ef7bfc89',18.2,R,True,8)]},
 {"dur":1.2,"label":"black hold","layers":[]},
 CARD]
E={"id":"056-symmetry","title":"Symmetry — Imperfect Pairing (archive proof)","size":[640,480],"fps":24,"source_gain_db":6,"score":None,"events":ev}
json.dump(E,open('/home/user/bolas/paeleo/allways/films/056-symmetry/edl.json','w'),indent=1)
# sequential alternative: same in/out, one after another, full frame
seq=[('3b9d2889',0.0,11.4,0,'P1 left alone: Two Pay Days 1927'),('c688de99',0.0,6.8,4,'P1 right alone: Bookkeeping and Accounting 1945'),
     ('aaf17c56',1.0,23.0,6,'P2 left alone: Learning to Set Type 1959'),('e617813e',2.0,23.0,0,'P2 right alone: Wallops Island 1965'),
     ('9199c819',0.6,12.6,6,'P3 left alone: Door to Heaven 1941'),('ef7bfc89',5.6,14.3,8,'P3 right alone: Wreckless 1935')]
ev2=[{"dur":du,"label":lab+" (sequential comparison)","fade_in":.3 if k==0 else 0,"layers":[lay(p,i,FULL,True,g)]} for k,(p,i,du,g,lab) in enumerate(seq)]+[{"dur":1.2,"label":"black hold","layers":[]},CARD]
E2=dict(E,id="056-symmetry-alt",title="Symmetry — sequential-cut comparison",events=ev2)
json.dump(E2,open('/home/user/bolas/paeleo/allways/films/056-symmetry/edl-alt.json','w'),indent=1)
