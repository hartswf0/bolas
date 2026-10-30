"""Numeric invariants for proof 0. Perception is judged by the critic, not here.

    python3 tools/clockwork_pink/check_proof0.py
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import proof0 as P


def bbox(poly):
    a = np.asarray(poly)
    return a[:, 0].min(), a[:, 1].min(), a[:, 0].max(), a[:, 1].max()


def overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


fails = []
# 1. on twos: every pose holds for exactly two frames
for f in range(0, P.N_FRAMES - 1, 2):
    if P.pose(f) != P.pose(f + 1):
        fails.append(f"pose changes inside a twos pair at frame {f}")
        break
# 2. during the hold nothing moves: clamp-to-eye distance and hand placement constant
held = [P.placed(P.pose(f)) for f in range(*P.HOLD)]
ref = held[0]
for (pieces, hand), f in zip(held, range(*P.HOLD)):
    if hand != ref[1] or [q for _, q, _ in pieces] != [q for _, q, _ in ref[0]]:
        fails.append(f"piece moved during hold at frame {f}")
        break
lo = dict((n, q) for n, q, _ in ref[0])["clamp_lo"]
gap = bbox(lo)[1] - P.CY
if abs(gap - P.HMAX) > 4:  # the ragged cut edge varies by about 3 sigma of 1.4 px
    fails.append(f"lower clamp not at the lid edge during hold: {gap:.1f} px from centre, want {P.HMAX}")
# 3. contact: a fingertip rests on the lower clamp bar, and no fingertip is on the eye
x0, y0, x1, y1 = bbox(lo)
tips = P.tips(P.pose(P.HOLD[0]))
if not any(x0 - 4 <= x <= x1 + 4 and y0 - 4 <= y <= y1 + 4 for x, y in tips):
    fails.append(f"no fingertip on the lower clamp bar during the hold: {[(round(x), round(y)) for x, y in tips]}")
if any(abs(x - P.CX) < P.RX and abs(y - P.CY) < P.HMAX * (1 - ((x - P.CX) / P.RX) ** 2) for x, y in tips):
    fails.append("a fingertip lands on the eye, not the clamp")
# 6. the tear runs at least a quarter of the face card's height, before the bulb pops
if P.TEAR_RUN < 0.25 * 400 or P.pose(P.POP - 2)["tear"] < 0.9:
    fails.append("tear too short or still running at the pop")
# 4. the clamp is free of the lid by the end of the swivel
end = P.pose(P.SWIVEL[1])
if end["gap_lo"] > 56 or end["clamp_up_y"] > 0:
    fails.append("clamps not released by the end of the swivel")
# 5. the blink fully closes on at least one drawing
if min(P.pose(f)["gap_up"] for f in range(*P.BLINK)) != 0:
    fails.append("blink never closes")

print("\n".join(fails) if fails else "proof0: 6/6 invariants hold")
sys.exit(1 if fails else 0)
