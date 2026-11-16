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
for q in sys.argv[1:]:
    d=api(dict(action="query",list="search",srnamespace=6,srlimit=40,srsearch=q))
    print(q, [h["title"] for h in d.get("query",{}).get("search",[])][:40]); time.sleep(4)
