import hashlib, json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maquette as M
H = os.path.dirname(os.path.abspath(__file__))
sha = json.load(open(os.path.join(H, "..", "out", "master.sha1.json")))["sha1"]
ks = sorted(random.Random(20261116).sample(range(720), 10))
res = [dict(k=k, recorded=sha[k], rerender=hashlib.sha1(M.frame(k).tobytes()).hexdigest()) for k in ks]
for r in res: r["equal"] = r["recorded"] == r["rerender"]
out = dict(frames=ks, all_equal=all(r["equal"] for r in res), checks=res)
json.dump(out, open(os.path.join(H, "determinism-check.json"), "w"), indent=1)
print(out["all_equal"])
