"""Build edl.json and score.wav for ALLWAYS 059 · BALL (SCION 059, graphic constancy).

Every registration value below was measured with tools/allways-forage/measure.py
(Hough circle with rim-edge support, checked by eye on a drawn overlay) except the
octagonal clock, whose anchor is set by hand and is deliberately approximate.
Run: python3 mk.py && python3 ../../../../tools/allways-forage/render.py edl.json [--control]
"""
import json, os, wave
import numpy as np

H = 480
R = 0.28 * H          # target rim radius on screen, px
TO = [0.5, 0.5]       # common anchor: screen centre
SR = 48000

# (label, src, media, in, dur, anchor, r (normalised to source height), source-height px or None = probe, material, use)
# The reel (an ellipse in perspective) and the moving wheel were marked by hand on gridded frames
# at the middle of their windows; both move inside the shot, so their registration drifts by design.
SHOTS = [
    ("sun through cloud", "1ec03509-6d16-5a31-8672-48137c55b5ac", "clip", 0.6, 3.5, [0.4256, 0.4025], 0.2372, 240, "sky", "light"),
    ("the Earth, painted globe", "13bb478b-a1ef-5b30-91e7-0a0aa8fe07cd", "still", 0, 2.25, [0.4931, 0.4875], 0.2772, None, "sky", "model"),
    ("a lens over the moon map", "0f379c56-af09-52cd-bf67-bdc2e4151a18", "still", 0, 2.25, [0.3281, 0.4275], 0.1772, None, "glass", "looking"),
    ("a lens over a signature", "3bbf2026-6f83-5ccb-8a3e-2af0f8dbace2", "still", 0, 2.25, [0.6431, 0.3825], 0.3002, None, "glass", "looking"),
    ("a lens over an eye", "72063aac-2b6a-547f-ad1c-0e721a2582e7", "still", 0, 2.5, [0.4894, 0.4275], 0.3057, None, "glass", "looking back"),
    ("a wall clock", "adfad259-0558-53eb-82f8-350609a70480", "clip", 1.5, 2.5, [0.4631, 0.5025], 0.3492, None, "metal", "time"),
    ("a slide-rule dial, BORON", "3eb9d17a-4cce-5cd1-9df5-4deaecaf1f5d", "still", 0, 2.25, [0.2081, 0.5125], 0.2802, None, "metal", "calculation"),
    ("an octagonal clock: the rim fails", "0d3b87de-0fbb-5930-adfb-54557a5d0acf", "still", 0, 2.75, [0.52, 0.43], 0.34, None, "plastic", "time"),
    # contextual release: unregistered, whole frame, a hand turns the control beside the gauge
    ("RELEASE: a hand at the gauge panel", "18c68920-99d5-5367-abf3-43d755b5a2ce", "clip", 7.4, 3.45, None, None, 240, "release", "control"),
    ("a shower rose", "4dc7dd14-6b64-5aa2-8cde-1d32038426d9", "still", 0, 2.75, [0.2606, 0.4275], 0.3207, None, "metal", "water"),
    ("a speaker grille and a pointer", "09f05564-267d-5b2d-a056-d65ff834b162", "still", 0, 2.75, [0.5044, 0.4725], 0.4072, None, "paper", "voice"),
    ("a film reel in a boy's hands", "8266284b-8fbb-5b36-9d7f-3987ddc4af17", "clip", 6.4, 2.2, [0.51, 0.395], 0.35, None, "metal", "pictures"),
    ("a motorcycle wheel, running", "c1e30693-35b6-5d39-9540-a8e1b574c71a", "clip", 9.2, 2.2, [0.31, 0.49], 0.58, None, "rubber", "travel"),
    ("a jet intake", "a393b728-390d-554d-a7dc-234de357c36d", "clip", 11.7, 1.6, [0.4894, 0.5075], 0.2222, 240, "metal", "flight"),
    # exit: unregistered original moving shot, the moon drifts out of frame
    ("EXIT: a painted moon drifts out of frame", "201b010b-d025-5ea8-8ec8-714d0faf41ae", "clip", 17.6, 4.6, None, None, 240, "exit", "leaving"),
]

# Why each shot is here, written into the edit list as the event label (and shown on the case-study page).
WHY = [
 "The opening anchor. A sun behind cloud is the plainest circle in the archive, bright enough to set the target size and centre. Held 3.5 s so the viewer learns where the rim lives before anything changes.",
 "A painted globe from a climate film. The first change of kind: from a sky object to a model of one. The rim lands within 5 px of the sun's.",
 "First of three lenses (moon map, signature, eye), from two films twenty years apart. The archive keeps showing someone looking through a circle. Chosen because the use changes while the pose stays the same.",
 "Second lens, over a handwritten signature. The rim is the lens's own metal ring, so it registers within 4 px.",
 "Third lens: the circle looks back. An eye behind glass, in the same place on screen as the sun was.",
 "A wall clock from a 1966 earthquake film: the first circle that measures something. The second hand keeps moving inside the held rim. The source clip is 720\u00d7480, so the anchor is about 22 px off.",
 "A slide-rule dial. A second measuring circle; its twin on the right is cut by the crop. Rim error under 3 px.",
 "The irregular object. An octagonal clock whose edge is not a circle. The anchor was set by hand and left approximate (rim about 29 px small), so the registration visibly fails here instead of being corrected.",
 "The contextual release. Unregistered and whole frame, with the expected beat withheld. A hand turns a control beside the gauge panel: the first shot in which a circle is used rather than shown.",
 "After the instruments, the bathroom. A shower head from a 1956 appliance film, rim within 3 px. The taps return here, slower.",
 "A speaker grille and a pointer from a 1929 cartoon. A paper-surfaced circle that looks like a dial and turns out to be a voice.",
 "A film reel in a boy's hands: the archive's own medium turns up as a circle. The tilted ellipse and the boy's movement make the registration drift about 25 px, kept as an honest seam. It stands in for the prompt's object used in play.",
 "A motorcycle wheel. The rim was marked by hand on gridded frames because the detector kept reading the hub. The wheel moves, so it drifts: the first circle that goes somewhere.",
 "A jet intake, 2007: the last registered circle and the largest dark disc. It ends at 35.2 s, before the source clip's own page-turn transition.",
 "The exit. Unregistered. In a 1965 space-animation clip a painted moon drifts out to the left and leaves the starfield empty, then the image fades. The circle leaves the frame in a moving shot, as the prompt asks."]


def still_h(src, media='still'):
    """Pixel height of the source file actually rendered (stills and clips vary in size)."""
    import subprocess
    idx = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../tools/allways-forage/index.json')))
    e = next(x for x in idx if x['id'] == src)
    return int(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=height',
                                        '-of', 'csv=p=0', e['media'][media]]).decode().split()[0])


events, t, cuts = [], 0.0, []
for (label, src, media, tin, dur, anchor, r, sh, mat, use) in SHOTS:
    L = {"src": src, "media": media, "in": tin, "audio": False}
    if anchor:
        sh = sh or still_h(src, media)
        L.update({"fit": "register", "anchor": anchor, "to": TO, "k": round(R / (r * sh), 4)})
    else:
        L.update({"fit": "cover"})
    ev = {"dur": dur, "label": f"{label}. {WHY[len(events)]}", "use": use, "material": mat, "layers": [L]}
    if label.startswith("EXIT"):
        ev["fade_out"] = 1.2
    events.append(ev)
    cuts.append((t, dur, mat))
    t += dur
events.append({"dur": 3.0, "label": "source card", "card": {"lines": ["BALL", "round things from thirteen films, 1929–2007", "movingimagearchive.com · see ledger"], "size": 22}, "fade_in": .4})

# ---- score: newly composed taps, one per beat; timbre follows material; the beat at the release is omitted
TOTAL = t + 3.0
y = np.zeros(int(TOTAL * SR) + SR)


def tap(at, mat, amp=0.5):
    n = int(0.6 * SR); tt = np.arange(n) / SR
    rng = np.random.default_rng(int(at * 1000))
    if mat == 'sky':
        s = np.sin(2 * np.pi * 98 * tt) * np.exp(-tt * 5) + .3 * np.sin(2 * np.pi * 196 * tt) * np.exp(-tt * 7)
    elif mat == 'glass':
        s = np.sin(2 * np.pi * 2637 * tt) * np.exp(-tt * 18) + .4 * np.sin(2 * np.pi * 3951 * tt) * np.exp(-tt * 25)
    elif mat == 'metal':
        s = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * d) for f, d in [(880, 9), (1397, 12), (2217, 16)]) / 2
    elif mat == 'plastic':
        s = np.sin(2 * np.pi * 660 * tt) * np.exp(-tt * 40) + .5 * rng.standard_normal(n) * np.exp(-tt * 60)
    elif mat == 'paper':
        nz = rng.standard_normal(n); nz = np.convolve(nz, np.ones(12) / 12, 'same')
        s = nz * np.exp(-tt * 35) * 1.5
    elif mat == 'rubber':
        s = np.sin(2 * np.pi * 150 * tt * (1 - .3 * tt)) * np.exp(-tt * 14)
    else:
        return
    s[:48] *= np.linspace(0, 1, 48)
    i = int(at * SR); y[i:i + n] += amp * s


BEAT = 0.75
for (c0, d, mat) in cuts:
    if mat == 'release':
        continue                         # the expected beat is withheld; the room goes quiet
    if mat == 'exit':
        tap(c0, 'sky', .35)              # one last low beat as the moon starts to leave
        continue
    k = 0
    while k * BEAT < d - 0.2:
        tap(c0 + k * BEAT, mat, .5 if k == 0 else .22)
        k += 1
y = y / max(1e-9, np.abs(y).max()) * 0.6
st = np.stack([y, y], 1)
with wave.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'score.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype('<i2').tobytes())

edl = {"id": "059-ball", "title": "BALL", "size": [640, 480], "fps": 24,
       "operator": "SCION 059 · Ball — Graphic Constancy Across Sources",
       "registration": {"target_radius_px": R, "target_centre": TO, "transforms": "translation + uniform scale only"},
       "score": {"file": "score.wav", "gain_db": 0, "note": "newly composed synthetic taps; no source audio used"},
       "events": events}
json.dump(edl, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'edl.json'), 'w'), indent=1)
print(f"{len(SHOTS)} shots, {t:.2f}s + 3.0s card")
