import json
d={e['id'][:8]:e['id'] for e in json.load(open('/home/user/bolas/tools/allways-forage/index.json'))}
def lay(p,i,media='clip',g=10): return {"src":d[p],"media":media,"in":i,"box":[0,0,1,1],"fit":"contain","audio":media!='still',"gain_db":g,"afade_in":.1,"afade_out":.15}
CARD={"dur":4,"label":"source card","fade_in":.5,"fade_out":.8,"card":{"lines":["Beginning to Date (1953) · a staged social-guidance film","Sources: movingimagearchive.com · see ledger"],"size":18}}
TIGHT={"dur":6.95,"label":"TIGHT: a huddle of boys in suits; one is talked at, nudged; the others turn away and he is left in frame smiling (source 499.87–506.84 s)","layers":[lay('3b640aa6',0.0)]}
WIDE={"dur":10.15,"label":"WIDE (the source's next shot): the room — girls lined along the far wall, boys cross the open floor; one boy asks a girl in a white dress and they begin to dance (source 506.84–516.99 s)","layers":[lay('3b640aa6',7.0)]}
GAP={"dur":1.0,"label":"black seam: what follows is a LATER scene of the same film, not the same moment","layers":[]}
CODA={"dur":14.6,"label":"CODA, montage relation (same film, ~95 s later): packed dance floor; then a girl seated at the margin by a table, a boy beside her looks up; neither resolves (source 594.76–609.36 s)","layers":[lay('22ba9c11',0.0,g=10)]}
EST={"dur":3.0,"label":"ESTABLISHING (still frame only): the shot that precedes the huddle in the source — girls in a curve along the wall, boys in the foreground, empty floor between (source 490.66–499.87 s; held thumbnail, motion not available locally)","layers":[lay('22a114dd',0,'still')]}
base={"size":[640,480],"fps":24,"source_gain_db":8,"score":None}
TIGHT1=dict(TIGHT,fade_in=.4)
json.dump(dict(base,id="060-losers",title="Losers — tight opening (archive proof)",events=[TIGHT1,WIDE,GAP,CODA,CARD]),open('/home/user/bolas/paeleo/allways/films/060-losers/edl.json','w'),indent=1)
EST1=dict(EST,fade_in=.4)
json.dump(dict(base,id="060-losers-wide",title="Losers — wide-opening comparison",events=[EST1,TIGHT,WIDE,GAP,CODA,CARD]),open('/home/user/bolas/paeleo/allways/films/060-losers/edl-alt.json','w'),indent=1)
