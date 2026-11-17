import json,time,urllib.request,os,hashlib,shutil,sys
UA={"User-Agent":"oulipo-film-research/1.0"}
OUT="/home/user/bolas/paeleo/scion/oulipo/films/sources/le-maki-mococo/reading"
OLD="/home/user/bolas/paeleo/scion/oulipo/films/sources/le-maki-mococo/test-shot/voice"
want=["in","the","dark","it","hang","and","swing","is","smells","of","pop","corn","never","ring","rings"]
recs={r["title"]:r for r in json.load(open("meta.json")) if not r.get("missing")}
jobs=[(f"File:LL-Q1860 (eng)-Grendelkhan-{w}.wav",f"Grendelkhan-{w}.wav") for w in want]+[
 ("File:LL-Q1860 (eng)-Vealhurl-binturong.wav","Vealhurl-binturong.wav"),("File:LL-Q1860 (eng)-Vealhurl-popcorn.wav","Vealhurl-popcorn.wav")]
for t,fn in jobs:
    r=recs[t]; p=os.path.join(OUT,fn)
    old=os.path.join(OLD,fn.split("-",1)[1])
    if not os.path.exists(p) and os.path.exists(old) and hashlib.sha1(open(old,"rb").read()).hexdigest()==r["sha1"]:
        shutil.copy(old,p); print("reused",fn)
    if os.path.exists(p) and hashlib.sha1(open(p,"rb").read()).hexdigest()==r["sha1"]: print("ok",fn); continue
    for k in range(7):
        try:
            b=urllib.request.urlopen(urllib.request.Request(r["file_url"],headers=UA),timeout=60).read()
            assert hashlib.sha1(b).hexdigest()==r["sha1"],"sha1"
            open(p,"wb").write(b); print("got",fn,len(b),flush=True); break
        except Exception as e:
            print("retry",fn,e,flush=True); time.sleep(8*2**k)
    time.sleep(4)
