import json,time,urllib.request,os,hashlib,shutil
UA={"User-Agent":"oulipo-film-research/1.0"}
OUT="/home/user/bolas/paeleo/scion/oulipo/films/sources/le-maki-mococo/reading"
OLD="/home/user/bolas/paeleo/scion/oulipo/films/sources/le-maki-mococo/test-shot/voice"
recs={r["title"]:r for r in json.load(open("meta.json")) if not r.get("missing")}
log=json.load(open("fetch_log.json")) if os.path.exists("fetch_log.json") else {}
for w in ["in","the","it","hang","swing","is"]:
    st="Grendelkhan-"+w
    if st not in log and os.path.exists(os.path.join(OLD,w+".mp3")):
        shutil.copy(os.path.join(OLD,w+".mp3"),os.path.join(OUT,st+".mp3"))
        log[st]=dict(form="Commons mp3 transcode of the original (downloaded 2026-11-16 by the test shot when originals were rate-limited); reused",path=os.path.join(OUT,st+".mp3"))
json.dump(log,open("fetch_log.json","w"),indent=1)
jobs=[("File:LL-Q1860 (eng)-Vealhurl-binturong.wav","Vealhurl-binturong"),("File:LL-Q1860 (eng)-Vealhurl-popcorn.wav","Vealhurl-popcorn")]+[
 (f"File:LL-Q1860 (eng)-Grendelkhan-{w}.wav",f"Grendelkhan-{w}") for w in ["smells","of","never","rings","pop","corn","ring"]]
for t,st in jobs:
    if st in log: continue
    r=recs[t]
    for k in range(8):
        try:
            b=urllib.request.urlopen(urllib.request.Request(r["file_url"],headers=UA),timeout=60).read()
            assert hashlib.sha1(b).hexdigest()==r["sha1"],"sha1 mismatch"
            p=os.path.join(OUT,st+".wav"); open(p,"wb").write(b)
            log[st]=dict(form="original wav (sha1 verified against Commons API)",path=p); print("ok",st,len(b),flush=True); break
        except Exception as e:
            print("retry",st,str(e)[:30],flush=True); time.sleep(45*1.4**k)
    json.dump(log,open("fetch_log.json","w"),indent=1); time.sleep(20)
print("DONE",flush=True)
