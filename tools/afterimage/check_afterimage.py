"""Measured invariants for AFTERIMAGE, read from the retina log the render writes. Whether it moves anyone is the
critic's call, not this file's.

    python3 tools/afterimage/check_afterimage.py OUT_DIR/retina.json
"""
import json, sys
import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import afterimage as A

L = json.load(open(sys.argv[1]))["log"]
t = np.array([r["t"] for r in L]); af = np.array([r["after"] for r in L]); ad = np.array([r["A"] for r in L])
b = np.array([r["blink"] for r in L])
fails = []


def mean(a, lo, hi):
    return float(a[(t >= lo) & (t < hi)].mean())


# 1. held means held: no blink before the release
if b[t < A.HELD_END].max() > 0:
    fails.append("a blink happens while the eye is held")
# 2. the burn builds: the afterimage in the last 4 s of Held is at least twice the first 4 s
early, late = mean(af, 0, 4), mean(af, A.HELD_END - 4, A.HELD_END)
if late < 2 * early:
    fails.append(f"no burn-in: afterimage {early:.4f} early vs {late:.4f} late")
# 3. each blink lets the retina rest: adaptation drops across the blink
for bt in A.BLINKS:
    i0, i1 = np.searchsorted(t, bt), np.searchsorted(t, bt + A.BLINK_LEN)
    if ad[i1] > ad[i0] * 0.9:
        fails.append(f"blink at {bt}s did not rest the retina ({ad[i0]:.4f} -> {ad[i1]:.4f})")
# 4. the glow is carried: in the dark before the flower there is no new light, yet the afterimage is still there
dark = (t >= A.RELEASE_END) & (t < 33.0)
if af[dark].min() < 0.01:
    fails.append(f"the glow goes out in the dark (min {af[dark].min():.4f})")
# 5. and it is still there at the end, before the fade
if af[np.searchsorted(t, A.CARRY_END - 1.3)] <= 0.005:
    fails.append("no glow left at the end")

# 6. the cuts keep tightening right up to the stop: never more than 8 equal gaps in a row, two- or three-frame cuts at the end
gaps = [round((e - s) * A.FPS) for s, e, *_ in A.SHOTS if e <= A.HELD_END]
run = best = 1
for a, b2 in zip(gaps, gaps[1:]):
    run = run + 1 if a == b2 else 1; best = max(best, run)
tail = [round((e - s) * A.FPS) for s, e, *_ in A.SHOTS if A.HELD_END - 2 <= s and e <= A.HELD_END]
short = [g for g in gaps if g < 6]
if best > 8 or not any(g in (2, 3) for g in tail):
    fails.append(f"the cutting levels off: {best} equal gaps in a row; last 2 s cuts {tail}")

# 7-8. read from the film itself (the critic's repair condition), when it is given
if len(sys.argv) > 2:
    import colorsys, subprocess

    def grab(sec):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(sec), "-i", sys.argv[2], "-frames:v", "1", "-f", "rawvideo",
                              "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        return np.frombuffer(raw, np.uint8).reshape(A.H, A.W, 3).astype(np.float32)

    def luma(f):
        return f @ np.array([0.299, 0.587, 0.114], np.float32)

    f = grab(29.5); y = luma(f); pink = f[(f[..., 0] > f[..., 1] + 20) & (y > 12)]
    ref = min(74.0, luma(pink).max()) if len(pink) else 74.0       # the critic's ceiling: the pink at 29.5 s, at most 74
    band = []
    for sec in (31, 34, 37, 40):
        f = grab(sec); y = luma(f)
        if (y < 20).mean() < 0.85 or y.mean() >= 15:
            fails.append(f"{sec}s is not dark: {100 * (y < 20).mean():.0f}% of pixels under 20, mean {y.mean():.1f}")
        if y.max() > ref:
            fails.append(f"{sec}s has light brighter than the pink at 29.5 s ({y.max():.0f} > {ref:.0f})")
    for sec in (31, 36):
        band.append(luma(grab(sec))[: A.H // 8].mean())
    if band[1] > 0.5 * band[0]:
        fails.append(f"the leftover at the top does not fade: {band[0]:.1f} -> {band[1]:.1f}")
    f = grab(37); y = luma(f); lit = f[y > np.percentile(y, 97)] / 255
    hs = np.array([colorsys.rgb_to_hsv(*p)[:2] for p in lit[:: max(1, len(lit) // 400)]])
    hue, sat = np.median(hs[:, 0]) * 360, np.median(hs[:, 1])
    if not (300 <= hue <= 350 and sat > 0.25):
        fails.append(f"the flower is not pink: hue {hue:.0f}, saturation {sat:.2f}")

print("\n".join(fails) if fails else
      f"afterimage: all invariants hold (burn {early:.3f}->{late:.3f}; glow in the dark >= {af[dark].min():.3f}; "
      f"{len(short)} cuts under six frames)")
sys.exit(1 if fails else 0)
