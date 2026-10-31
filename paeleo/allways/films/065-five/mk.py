import json
d={e['id'][:8]:e['id'] for e in json.load(open('/home/user/bolas/tools/allways-forage/index.json'))}
def ev(p,i,du,lab,g=0,**kw): return dict({"dur":du,"label":lab,"layers":[{"src":d[p],"media":"clip","in":i,"box":[0,0,1,1],"fit":"contain","audio":True,"gain_db":g,"afade_in":.15,"afade_out":.25}]},**kw)
CARD={"dur":4,"label":"source card","fade_in":.5,"fade_out":.8,"card":{"lines":["Five records, five sources, 1953–1970 and undated","Sources: movingimagearchive.com · see ledger"],"size":18}}
K,G,C,H,B='d2156bef','4f70731f','0f8a091e','46cd8d58','c015a7f0'
main=[
 ev(K,0.0,11.0,"OPEN 1 kitchen (Toute La Bande ep.9, 1970): camera pulls back from a frying pan to a woman stirring potatoes at a stove — uninterrupted",fade_in=.4),
 ev(G,0.0,6.0,"OPEN 2 garden (Victory Gardens, undated): hands take from a bowl and press into a furrow — uninterrupted"),
 ev(C,24.4,4.2,"OPEN 3 clothesline (Health: Your Posture, 1953): a woman lifts a sheet to the line — uninterrupted"),
 ev(H,1.1,5.6,"OPEN 4 lawn chairs (amateur film, undated, silent): two people sit in wicker chairs, backs to camera, one with a paper — the whole surviving shot"),
 ev(B,0.0,10.5,"OPEN 5 / EXCEPTION barber's chair (Barbers, 1959): a barber combs and lifts a boy's hair (shot 1, 0-7.4 s uninterrupted), then the source's own cut to a close view: the boy holds still while another person's clippers work. The only practice done TO someone; the longest opening; it does not return"),
 ev(K,11.0,6.5,"MIDDLE kitchen: scooping onto the plate (same take continues)"),
 ev(G,6.0,4.0,"MIDDLE garden: the last of the bowl into the ground (same shot continues)"),
 ev(C,28.6,2.6,"MIDDLE clothesline: the sheet goes over the line (same shot continues, ends at the source's dissolve)"),
 ev(K,17.5,5.2,"RETURN kitchen: she lifts the plate and leaves; the stove remains"),
 ev(G,10.8,7.0,"RETURN garden: after a dissolve in the source, a man stands in the planted plot"),
 {"dur":1.0,"label":"black","layers":[]},CARD]
base={"size":[640,480],"fps":24,"source_gain_db":0,"score":None}
json.dump(dict(base,id="065-five",title="Five — parallel practices (archive proof)",events=main),open('/home/user/bolas/paeleo/allways/films/065-five/edl.json','w'),indent=1)
alt=[ev(K,0.0,22.7,"kitchen whole take",fade_in=.4),ev(G,0.0,17.8,"garden whole clip (hands, dissolve, man standing)"),ev(C,24.4,6.8,"clothesline whole shot"),
     ev(H,1.1,5.6,"lawn chairs whole shot"),ev(B,0.0,10.5,"barber both shots (stops before the source dissolves to a different salon)"),{"dur":1.0,"label":"black","layers":[]},CARD]
json.dump(dict(base,id="065-five-alt",title="Five — longer individual passages",events=alt),open('/home/user/bolas/paeleo/allways/films/065-five/edl-alt.json','w'),indent=1)
