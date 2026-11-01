import json,copy
I={'pinch':'1570ec0b-a665-5157-959b-06574dc07dcf','paper':'7cc49276-6d78-54bc-a681-5b10adc65e52','foil':'72f7f4a3-dfca-58ff-b505-378a7191860a',
'dye':'4809003b-ec8c-500e-89b0-9201282ab31c','metal':'c7ae0e60-e5bf-5809-96d4-afe0026c46bb','lacquer':'b3ef2f32-ea89-5744-8940-c804848c95e0',
'choc':'b63bf343-513d-5e64-80b3-32360ca9d164','lathe':'d5ee4ae2-2924-5267-8c65-65858f743e58','grain':'efedc39b-5252-55c9-a806-12f445911ad1'}
def L(k,media,t,**kw): d={'src':I[k],'media':media,'in':t,'fit':'cover','audio':False}; d.update(kw); return d
ev=[
 dict(dur=3.6,label='PRESSURE / RECOVERY: a pinch lifts the skin of a hand into a ridge; released, it sinks back (observed, Hydration 2004)',fade_in=0.6,layers=[L('pinch','clip',0)]),
 dict(dur=3.0,label='FOLD: hands crease a paper packet; the fold stays (observed, Gardening 1940)',layers=[L('paper','loop',0)]),
 dict(dur=3.0,label='PRESSURE / PERSISTENCE: a hand presses crumpled metallised foil; the creases do not return (observed, Moonwalk One c.1970)',layers=[L('foil','loop',0)]),
 dict(dur=3.0,label='WETTING: dye falls into water and spreads in plumes (observed; source undated)',layers=[L('dye','loop',0)]),
 dict(dur=7.8,label='POUR / SPREAD: liquid lacquer poured onto a turning recording blank spreads to a disc (observed, Command Performance 1942)',layers=[L('lacquer','clip',0)]),
 dict(dur=3.0,label='MOLTEN: metal poured from a ladle (observed, Master Hands, undated in index)',layers=[L('metal','loop',0)]),
 dict(dur=8.6,label='MOLTEN -> SET: chocolate deposited from nozzles, each drop keeping the tail of its release (observed, Great American Chocolate Factory, undated). Cut from metal to chocolate is an ANALOGY of pouring, not one material.',layers=[L('choc','clip',5.2)]),
 dict(dur=9.5,label='CUT: a lathe tool peels a chip from steel; the chip curls and keeps the curl (observed, Industries of the U.S.: Steel, undated)',layers=[L('lathe','clip',6.0)]),
 dict(dur=3.5,label='CONTEXT: heat-treatment furnace door (observed)',layers=[L('grain','clip',0.4)]),
 dict(dur=10.0,label='MEMORY (CONSTRUCTED): animated diagram of grain growth in aluminium after heating -- a DIAGRAM in the source film, not a micrograph of the furnace load (Heat Treatment of Aluminum 1990)',layers=[L('grain','clip',8.0)]),
 dict(dur=3.6,label='RETURN: the same pinch again, now seen after fold, set and curl',layers=[L('pinch','clip',0)]),
]
g=[]; W=1/3; H=W*0.75*(640/480)  # 4:3 cells
y0=(1-2*H)/2
cells=[('pinch','clip',0.3),('paper','loop',0),('foil','loop',0),('lacquer','clip',4.6),('choc','clip',10.5),('lathe','clip',14.0)]
for i,(k,m,t) in enumerate(cells):
    g.append(L(k,m,t,box=[(i%3)*W,y0+(i//3)*H,W,H]))
ev.append(dict(dur=3.0,label='SAMPLES SIDE BY SIDE (constructed comparison): pinch / fold / foil / lacquer / chocolate / chip, each in its own source interval',layers=g,fade_out=0.6))
ev.append(dict(dur=3.0,label='source card',card={'lines':['Sources: movingimagearchive.com · see ledger'],'size':20},fade_in=0.3,fade_out=0.5))
E={'id':'061-matter','title':'Matter — Material Affordance Chain','size':[640,480],'fps':24,'source_gain_db':0,'score':None,'events':ev}
json.dump(E,open('edl.json','w'),indent=1)
A=copy.deepcopy(E); A['id']='061-matter-alt-sourcesound'; A['title']+=' (comparison: source sound on)'
for e in A['events']:
    for l in e.get('layers',[]): l['audio']=True; l['gain_db']=-6 if len(e['layers'])==1 else -14
json.dump(A,open('edl-alt.json','w'),indent=1)
