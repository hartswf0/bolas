import json, time, urllib.request, urllib.parse, sys, os
UA={"User-Agent":"oulipo-film-research/1.0"}
OUT="/home/user/bolas/paeleo/scion/oulipo/films/sources/le-maki-mococo/test-shot/voice"
words=["in","the","dark","it","hang","and","swing","is"]
titles=[f"File:LL-Q1860 (eng)-Grendelkhan-{w}.wav" for w in words]
titles.append("File:Brehm's Life of animals (Page 265) (6220164475).jpg")
def get(url):
    for k in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=60) as r: return r.read()
        except Exception as e:
            print("retry",e,file=sys.stderr); time.sleep(5*2**k)
q=dict(action="query",prop="imageinfo",iiprop="url|extmetadata|size|mime",titles="|".join(titles),format="json")
d=json.loads(get("https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode(q)))
recs=[]
for p in d["query"]["pages"].values():
    ii=p["imageinfo"][0]; em=ii["extmetadata"]
    g=lambda k: em.get(k,{}).get("value","")
    r=dict(title=p["title"],author=g("Artist"),license=g("LicenseShortName"),license_url=g("LicenseUrl"),
           source_url=ii["descriptionurl"],file_url=ii["url"],size=ii["size"],mime=ii["mime"])
    recs.append(r); print(r["title"],r["license"],r["size"])
json.dump(recs,open(os.path.join(OUT,"meta.json"),"w"),indent=1)
for r in recs:
    if r["mime"].startswith("audio"):
        fn=os.path.join(OUT,r["title"].split("-")[-1])
        if not os.path.exists(fn):
            open(fn,"wb").write(get(r["file_url"])); time.sleep(3)
