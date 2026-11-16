# Commons API helper with backoff. usage: cm.py meta <out.json> <title>... | search <out.json> <query> | get <out> <url>
import sys, json, time, urllib.request, urllib.parse
UA = {"User-Agent": "oulipo-film-research/1.0"}
API = "https://commons.wikimedia.org/w/api.php"
def fetch(url, tries=6):
    d = 4
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                ra = e.headers.get("Retry-After"); w = int(ra) if ra and ra.isdigit() else d
                print("429, wait", w, file=sys.stderr); time.sleep(min(w, 60)); d *= 2; continue
            raise
    raise SystemExit("gave up")
cmd, out = sys.argv[1], sys.argv[2]
if cmd == "meta":
    q = dict(action="query", format="json", prop="imageinfo", iiprop="url|extmetadata|size|mime", titles="|".join(sys.argv[3:]))
    open(out, "wb").write(fetch(API + "?" + urllib.parse.urlencode(q)))
elif cmd == "search":
    q = dict(action="query", format="json", list="search", srnamespace="6", srlimit="30", srsearch=sys.argv[3])
    open(out, "wb").write(fetch(API + "?" + urllib.parse.urlencode(q)))
elif cmd == "get":
    open(out, "wb").write(fetch(sys.argv[3]))
