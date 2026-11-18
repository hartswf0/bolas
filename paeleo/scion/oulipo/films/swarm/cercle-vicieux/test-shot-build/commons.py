"""Polite Commons API helper with backoff. Usage: python3 -I commons.py info 'File:A' 'File:B' > out.json"""
import sys, json, time, urllib.request, urllib.parse
UA = {"User-Agent": "oulipo-film-research/1.0"}
def get(params):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    for k in range(8):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:
            time.sleep(15 * (k + 1))
    raise SystemExit("gave up")
if sys.argv[1] == "info":
    d = get(dict(action="query", format="json", prop="imageinfo", iiprop="url|extmetadata|size|mime", titles="|".join(sys.argv[2:])))
    out = []
    for p in d["query"]["pages"].values():
        ii = p["imageinfo"][0]; m = ii["extmetadata"]
        out.append(dict(title=p["title"], size=ii["size"], mime=ii["mime"], url=ii["url"], page=ii["descriptionurl"],
                        **{k: m.get(k, {}).get("value") for k in ["LicenseShortName", "License", "Artist", "ImageDescription", "LicenseUrl", "Credit"]}))
    print(json.dumps(out, indent=1))
elif sys.argv[1] == "search":
    d = get(dict(action="query", format="json", list="search", srnamespace=6, srlimit=25, srsearch=sys.argv[2]))
    for x in d["query"]["search"]: print(x["title"], x["size"])
