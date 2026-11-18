"""Commons search/info helper with backoff. Usage: commons.py search "query" [ns6 filetype]  |  info "File:..." """
import json, re, sys, time, urllib.parse, urllib.request
UA = "oulipo-film-research/1.0"
API = "https://commons.wikimedia.org/w/api.php"
def get(params, tries=6):
    url = API + "?" + urllib.parse.urlencode(dict(params, format="json"))
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=40) as r:
                body = r.read().decode()
            return json.loads(body)
        except Exception as e:
            w = 8 * (i + 1); print(f"  backoff {w}s ({str(e)[:60]})", file=sys.stderr); time.sleep(w)
    raise SystemExit("gave up")
def strip(s): return re.sub("<[^>]+>", "", s or "").strip()
def search(q, n=15, width=None):
    p = dict(action="query", generator="search", gsrsearch=q, gsrnamespace=6, gsrlimit=n, prop="imageinfo",
             iiprop="url|extmetadata|size|mime", iiextmetadatafilter="LicenseShortName|Artist|LicenseUrl|ImageDescription")
    if width: p["iiurlwidth"] = width
    d = get(p); out = []
    for pg in d.get("query", {}).get("pages", {}).values():
        ii = pg["imageinfo"][0]; m = ii.get("extmetadata", {})
        out.append(dict(title=pg["title"], license=m.get("LicenseShortName", {}).get("value"),
                        license_url=m.get("LicenseUrl", {}).get("value", ""), author=strip(m.get("Artist", {}).get("value")),
                        w=ii.get("width"), h=ii.get("height"), mime=ii.get("mime"), size=ii.get("size"),
                        url=ii["url"], thumb=ii.get("thumburl"), page=ii.get("descriptionurl"),
                        desc=strip(m.get("ImageDescription", {}).get("value"))[:120], duration=ii.get("duration")))
    return out
if __name__ == "__main__":
    res = search(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 15, 1280)
    for r in res:
        print(f"{r['title'][:80]} | {r['license']} | {r['author'][:30]} | {r['w']}x{r['h']} {r['mime']} {r['size']}")
    if len(sys.argv) > 3: json.dump(res, open(sys.argv[3], "w"), indent=1)
