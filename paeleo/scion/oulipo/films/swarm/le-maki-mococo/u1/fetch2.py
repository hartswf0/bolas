import json,time,urllib.request,os,hashlib,shutil,sys,urllib.parse
UA={"User-Agent":"oulipo-film-research/1.0"}
OUT="/home/user/bolas/paeleo/scion/oulipo/films/sources/le-maki-mococo/reading"
OLD="/home/user/bolas/paeleo/scion/oulipo/films/sources/le-maki-mococo/test-shot/voice"
want=["and","dark","in","the","it","hang","swing","is","smells","of","pop","corn","never","ring","rings"]
recs={r["title"]:r for r in json.load(open("meta.json")) if not r.get("missing")}
jobs=[(f"File:LL-Q1860 (eng)-Grendelkhan-{w}.wav",f"Grendelkhan-{w}") for w in want]+[
 ("File:LL-Q1860 (eng)-Vealhurl-binturong.wav","Vealhurl-binturong"),("File:LL-Q1860 (eng)-Vealhurl-popcorn.wav","Vealhurl-popcorn")]
log={}
if os.path.exists("fetch_log.json"): log=json.load(open("fetch_log.json"))
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60).read()
for t,stem in jobs:
    r=recs[t]; wav=os.path.join(OUT,stem+".wav"); mp3=os.path.join(OUT,stem+".mp3")
    if stem in log: print("have",stem,log[stem]["form"]); continue
    w=stem.split("-",1)[1]
    for src in (os.path.join(OLD,w+".wav"),):
        if os.path.exists(src) and hashlib.sha1(open(src,"rb").read()).hexdigest()==r["sha1"]:
            shutil.copy(src,wav); log[stem]=dict(form="original wav (sha1 verified, reused from test-shot download)",path=wav)
    if stem in log: print("reused",stem); json.dump(log,open("fetch_log.json","w"),indent=1); continue
    done=False
    for k in range(4):
        try:
            b=get(r["file_url"]); assert hashlib.sha1(b).hexdigest()==r["sha1"]
            open(wav,"wb").write(b); log[stem]=dict(form="original wav (sha1 verified)",path=wav); done=True; break
        except Exception as e:
            print("orig fail",stem,str(e)[:40],flush=True)
            fu=r["file_url"]; parts=fu.split("/commons/")
            tu=parts[0]+"/commons/transcoded/"+parts[1]+"/"+parts[1].split("/")[-1]+".mp3"
            time.sleep(5)
            try:
                b=get(tu); open(mp3,"wb").write(b); log[stem]=dict(form="Commons mp3 transcode of the original (original rate-limited HTTP 429)",path=mp3,transcode_url=tu); done=True; break
            except Exception as e2:
                print("mp3 fail",stem,str(e2)[:40],flush=True); time.sleep(15*2**k)
    print(stem,log.get(stem,{}).get("form"),flush=True)
    json.dump(log,open("fetch_log.json","w"),indent=1); time.sleep(6)
