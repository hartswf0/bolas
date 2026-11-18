"""Commons search + licence fetch with polite backoff. Usage: commons.py search "q" | info "File:..." | get URL OUT"""
import json, sys, time, urllib.parse, urllib.request

UA = "oulipo-film-research/1.0"
API = "https://commons.wikimedia.org/w/api.php"


def fetch(url, tries=6):
    d = 4
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:
            code = getattr(e, "code", None)
            print(f"  retry {i} ({code or e}) wait {d}s", file=sys.stderr)
            time.sleep(d)
            d *= 2
    raise SystemExit("failed " + url)


def api(**p):
    p["format"] = "json"
    return json.loads(fetch(API + "?" + urllib.parse.urlencode(p)))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "search":
        d = api(action="query", list="search", srnamespace=6, srlimit=15, srsearch=sys.argv[2])
        for r in d.get("query", {}).get("search", []):
            print(r["title"])
    elif cmd == "info":
        d = api(action="query", prop="imageinfo", iiprop="url|extmetadata|size|mime", titles="|".join(sys.argv[2:]))
        for pg in d["query"]["pages"].values():
            ii = pg.get("imageinfo", [{}])[0]
            em = ii.get("extmetadata", {})
            g = lambda k: em.get(k, {}).get("value", "")
            print(json.dumps({"title": pg["title"], "url": ii.get("url"), "size": ii.get("size"), "mime": ii.get("mime"),
                              "license": g("LicenseShortName"), "license_url": g("LicenseUrl"), "artist": g("Artist")[:200],
                              "desc": g("ImageDescription")[:200], "duration": ii.get("duration")}))
    elif cmd == "get":
        open(sys.argv[3], "wb").write(fetch(sys.argv[2]))
