import json,copy
I={'fire':'dab44545-fcdd-5775-9611-c4c1eeaf62bf','oil':'79bc0a5e-2a30-5cc5-b2b9-440a51fa1097','moon':'60dd29ed-53b8-5715-abf0-1fe0c74c33d3',
'eagle':'4937833a-ce22-5d6c-bb4e-8aa5bcc7439a','ant':'14bea657-baec-5432-ad8a-3754df79f8e3','fed':'9970bcd5-ab92-52d9-a030-738193d8f955',
'moonred':'37dfa009-821f-511c-861f-3f57e307d220','dinner':'e4c5c3f8-ce1a-5811-803e-4a2b3c26beae'}
def L(k,media,t,**kw): d={'src':I[k],'media':media,'in':t,'fit':'cover','audio':media=='clip','gain_db':-3,'afade_in':0.15,'afade_out':0.2}; d.update(kw); return d
def E(dur,label,*layers,**kw): d=dict(dur=dur,label=label,layers=list(layers)); d.update(kw); return d
ev=[
 E(1.9,'YELLOW 1: looking out through the mesh of a yellow-painted cab; a man in a yellow shirt behind it (Structure Protection Strategies, 2003)',L('fire','clip',0.85),fade_in=0.5),
 E(2.1,'YELLOW 2: yellow-shirted crew hosing a burnt slope; yellow among ash and smoke (same film)',L('fire','clip',12.3)),
 E(3.4,'YELLOW 3 (yellow covered by use): firefighter\'s yellow shirt crossed by harness, radio and gloves; red helmet seeds the third chapter (same film)',L('fire','clip',3.3)),
 E(2.8,'TRANSITION Y->B: yellow bulldozers slung from a ship\'s derrick over blue sea (Oil Across Arabia, 1950)',L('oil','clip',21.3)),
 E(5.3,'BLUE 1: derrick work on deck against blue water; the work happens at the edge of frame (same film)',L('oil','clip',15.9)),
 E(3.3,'BLUE 2 (waiting): a ship lies at anchor on the blue-green sea (same film)',L('oil','clip',12.1)),
 E(4.3,'BLUE 3: hands working on a space-suit boot on a blue table (Moonwalk One, c.1970)',L('moon','clip',0.05)),
 E(3.3,'BLUE 4 (glove): a woman stitches suit layers; a black pressure glove waits on the blue table (same film)',L('moon','clip',9.1)),
 E(3.0,'BLUE 5 (waiting): silhouettes before a blue-lit window (The Eagle Has Landed, 1969)',L('eagle','loop',0)),
 E(2.8,'TRANSITION B->R: a crate swung over blue water toward a red hull (Oil Across Arabia, 1950)',L('oil','clip',24.15)),
 E(3.0,'RED 1 (quiet practical action): a man packs a box against red canvas (Antarctica 1939-41)',L('ant','loop',0)),
 E(3.0,'RED 2: men in red shirts unload sacks from a van (Inside the Fed, 1994)',L('fed','clip',0.0)),
 E(3.0,'RED 3: red machinery hoisted beside a corrugated wall (Moonwalk One, c.1970)',L('moonred','loop',0)),
 E(5.9,'SHARED SETTING: red curtains, yellow-orange fruit, blue blouse, pale blue cloth at one table (Inside/Outside, 1983)',L('dinner','clip',0.0),fade_out=0.6),
 E(3.0,'source card',card={'lines':['Sources: movingimagearchive.com · see ledger'],'size':20},fade_in=0.3,fade_out=0.5),
]
D={'id':'062-colors','title':'Colors — Chromatic Chapters','size':[640,480],'fps':24,'source_gain_db':0,'score':None,'events':ev}
json.dump(D,open('edl.json','w'),indent=1)
A=copy.deepcopy(D); A['id']='062-colors-alt-silent'; A['title']+=' (comparison: source sound removed)'
for e in A['events']:
    for l in e.get('layers',[]): l['audio']=False
json.dump(A,open('edl-alt.json','w'),indent=1)
