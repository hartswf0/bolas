import json, time, urllib.request, os, sys
UA={"User-Agent":"oulipo-film-research/1.0"}
OUT="/home/user/bolas/paeleo/scion/oulipo/films/sources/le-maki-mococo/test-shot/voice"
recs=json.load(open(os.path.join(OUT,"meta.json")))
for r in recs:
    if not r["mime"].startswith("audio"): continue
    fn=os.path.join(OUT,r["title"].split("-")[-1])
    if os.path.exists(fn) and os.path.getsize(fn)>1000: continue
    for k in range(8):
        try:
            with urllib.request.urlopen(urllib.request.Request(r["file_url"].split("?")[0],headers=UA),timeout=60) as resp: data=resp.read()
            open(fn,"wb").write(data); print("ok",fn,len(data),flush=True); break
        except Exception as e:
            print("retry",fn,e,flush=True); time.sleep(45*1.4**k)
    time.sleep(20)
