# sequential downloader honouring Retry-After. args: outdir then pairs name url
import sys, time, urllib.request, os
UA = {"User-Agent": "oulipo-film-research/1.0"}
out = sys.argv[1]; items = list(zip(sys.argv[2::2], sys.argv[3::2]))
for name, url in items:
    dst = os.path.join(out, name)
    if os.path.exists(dst) and os.path.getsize(dst) > 0: continue
    for k in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                data = r.read()
            open(dst, "wb").write(data); print("ok", name, len(data), flush=True); time.sleep(5); break
        except urllib.error.HTTPError as e:
            if e.code == 429:
                ra = e.headers.get("Retry-After"); w = int(ra) if ra and ra.isdigit() else 60
                print("429", name, "wait", w, flush=True); time.sleep(min(w, 620) + 5); continue
            print("err", name, e.code, flush=True); break
