import json
I={'line':'0f8a091e-f966-5adb-831a-d3ad8f0eea94','laundry':'30fe8bbc-4e09-52fd-85a8-2d3314fad7c1','dive':'652e9a2d-1bf9-57bb-9a49-33397e9432e5',
'tumble':'f24053fe-dabf-5f7d-be92-0d4890c81b66','high':'55c605ed-9ddd-563f-89b4-acf69aaed8f6','hose':'dab44545-fcdd-5775-9611-c4c1eeaf62bf',
'arch':'b6e217eb-832b-528a-9214-cb8174e2834f','gallery':'ec168197-19a9-5b9a-bd02-3a0ea2e8e1db'}
def L(key,t,audio=False,**kw): d={'src':I[key],'media':'clip','in':t,'fit':'cover','audio':audio,'gain_db':-4,'afade_in':0.1,'afade_out':0.15}; d.update(kw); return d
def E(dur,label,*layers,**kw): d=dict(dur=dur,label=label,layers=list(layers)); d.update(kw); return d
ev=[
 E(7.6,'HANGING (static outline, context): woman pegs a sheet on a clothesline; the lines run obliquely from the post (Health: Your Posture, 1953)',L('line',24.0),fade_in=0.6),
 E(5.0,'HANGING (closer, loaded): laundry strung between buildings; the line carries the garments (Story of a City: New York, 1946)',L('laundry',0.5)),
 E(2.2,'TRAJECTORY (tracked candidate): a diver runs off the board and enters the water; camera pans slightly (Industry on Parade: Sylacauga Saga, undated)',L('dive',2.4,audio=True)),
 E(3.6,'TRAJECTORY seen by a following camera: a diver tumbles from a high platform; the camera keeps him near frame centre (Selected scenes of sport personalities, 1951)',L('tumble',0.3)),
 E(7.2,'TRAJECTORY seen by a tilting camera, possibly slowed: high dive against clouds (Century of Progress Exposition, 1933)',L('high',9.2)),
 E(2.1,'JET (moving fluid, static shape): firefighters\' hose stream (Structure Protection Strategies, 2003)',L('hose',12.3,audio=True)),
 E(3.75,'ARCH (built, static outline): train enters an arched station hall; camera moves forward (Berlin: Symphony of a Great City, 1927)',L('arch',0.0)),
 E(3.0,'ARCH (built, static camera): a round-headed doorway at the end of a sculpture gallery (Miss Clark Introduces Panorama, 1960)',L('gallery',0.0)),
 E(2.0,'REPLAY + GUIDE A (model overlay): diver hip positions, camera pan compensated; fitted x linear / y quadratic in t',L('dive',2.6,audio=True)),
 E(6.4,'REPLAY + GUIDE B (model overlay, departs): screen-space track of the high diver with the same model; camera tilt makes the fit fail',L('high',9.4)),
 E(3.0,'REPLAY + GUIDE C (model overlay): the gallery doorway enlarged x3 (uniform scale only); rim marked by eye; parabola and circle fitted to the same crown samples',L('gallery',0.0,fit='register',anchor=[151/320,135/240],to=[0.5,0.5],k=6.0)),
 E(4.8,'RETURN, no guides: the clothesline as the sheet is pegged and let go (Health: Your Posture, 1953)',L('line',27.0),fade_out=0.6),
 E(3.0,'source card',card={'lines':['Sources: movingimagearchive.com · see ledger'],'size':20},fade_in=0.3,fade_out=0.5),
]
D={'id':'064-parabolas','title':'Parabolas (etc.) — Curves With Different Causes','size':[640,480],'fps':24,'source_gain_db':0,'score':None,'events':ev}
json.dump(D,open('edl.json','w'),indent=1)
