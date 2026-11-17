import json, time, urllib.request, urllib.parse, sys
UA={"User-Agent":"oulipo-film-research/1.0"}
def api(params):
    params.update(format="json")
    url="https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode(params)
    for k in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=30) as r: return json.load(r)
        except Exception as e:
            print("retry",e,file=sys.stderr); time.sleep(5*2**k)
titles=[l.strip() for l in open(sys.argv[1]) if l.strip()]
recs=[]
for i in range(0,len(titles),20):
    d=api(dict(action="query",prop="imageinfo",iiprop="url|extmetadata|size|mime|sha1",titles="|".join(titles[i:i+20])))
    for p in d["query"]["pages"].values():
        if "imageinfo" not in p: print("MISSING",p["title"]); recs.append(dict(title=p["title"],missing=True)); continue
        ii=p["imageinfo"][0]; em=ii["extmetadata"]; g=lambda k: em.get(k,{}).get("value","")
        r=dict(title=p["title"],artist=g("Artist"),license=g("LicenseShortName"),license_url=g("LicenseUrl"),usage=g("UsageTerms"),date=g("DateTimeOriginal") or g("DateTime"),
          source_url=ii["descriptionurl"],file_url=ii["url"],size=ii["size"],mime=ii["mime"],sha1=ii["sha1"])
        recs.append(r); print(r["title"],"|",r["license"],"|",r["size"])
    time.sleep(4)
json.dump(recs,open(sys.argv[2],"w"),indent=1)
