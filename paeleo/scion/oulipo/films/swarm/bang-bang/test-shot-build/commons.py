# Commons API helper with Retry-After backoff. Usage: commons.py search "q" | info "File:X" | get URL OUT
import sys, json, time, urllib.request, urllib.parse, urllib.error
UA = {"User-Agent": "oulipo-film-research/1.0"}
API = "https://commons.wikimedia.org/w/api.php?"
def fetch(url, tries=8):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                w = int(e.headers.get("retry-after", "20") or 20) + 2; print("429, wait", w, file=sys.stderr); time.sleep(w); continue
            raise
    raise SystemExit("gave up")
cmd = sys.argv[1]
if cmd == "search":
    q = API + urllib.parse.urlencode(dict(action="query", list="search", srnamespace=6, srlimit=20, format="json", srsearch=sys.argv[2]))
    for r in json.loads(fetch(q))["query"]["search"]: print(r["title"])
elif cmd == "info":
    q = API + urllib.parse.urlencode(dict(action="query", titles=sys.argv[2], prop="imageinfo", iiprop="url|size|mime|extmetadata", iiurlwidth=sys.argv[3] if len(sys.argv) > 3 else 1280, format="json"))
    for p in json.loads(fetch(q))["query"]["pages"].values():
        ii = p["imageinfo"][0]; m = ii["extmetadata"]
        print(json.dumps({"title": p["title"], "w": ii.get("width"), "h": ii.get("height"), "mime": ii.get("mime"), "url": ii["url"], "thumb": ii.get("thumburl"),
                          "page": ii.get("descriptionurl"), **{k: m.get(k, {}).get("value", "")[:400] for k in ["LicenseShortName", "License", "LicenseUrl", "Artist", "DateTimeOriginal", "ImageDescription", "Credit"]}}, ensure_ascii=False, indent=1))
elif cmd == "get":
    open(sys.argv[3], "wb").write(fetch(sys.argv[2])); print("ok", sys.argv[3])
