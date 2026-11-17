"""Fill afterlight/afterimage/index.html from the render's retina log, the critic record and the source list.

    python3 tools/afterimage/build_page.py OUT_DIR/retina.json
"""
import html, json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import afterimage as A

R = os.path.join(os.path.dirname(__file__), "..", "..")
L = json.load(open(sys.argv[1]))["log"]
t = np.array([r["t"] for r in L]); af = np.array([r["after"] for r in L])
early = af[(t >= 0) & (t < 4)].mean(); late = af[(t >= A.HELD_END - 4) & (t < A.HELD_END)].mean()
dark = af[(t >= A.RELEASE_END) & (t < 33.0)].min()
meter = [[r["t"], round(r["after"], 4)] for i, r in enumerate(L) if i % 6 == 0]
critic = json.load(open(os.path.join(os.path.dirname(__file__), "critic.json")))

rows = "\n".join(f'<tr><td class="mono">{c}</td><td><a href="{u}">{html.escape(ti)}</a></td><td>public domain</td></tr>'
                 for c, ti, u in A.SOURCES)
crit = "".join(f"<p><b>{html.escape(r['round'])} · {html.escape(r['verdict'])}.</b> {html.escape(r['note'])}</p>" for r in critic)

page = open(os.path.join(R, "afterlight/afterimage/template.html")).read()
page = (page.replace("__BURN__", f"{late / early:.1f} times the first four ({early:.3f} to {late:.3f})")
            .replace("__DARK__", f"{dark:.3f}")
            .replace("__SOURCES__", rows).replace("__CRITIC__", crit)
            .replace("__METER__", json.dumps(meter, separators=(",", ":"))))
open(os.path.join(R, "afterlight/afterimage/index.html"), "w").write(page)
print("wrote afterlight/afterimage/index.html")
