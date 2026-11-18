#!/usr/bin/env python3
"""La Machine a tuer le temps -- direction 1 'Le cahier rebattu' (assembly).

A handmade red spiral notebook (paper stop-motion, on twos) holds a frozen
pool of eight public-domain Jack Delano photographs (Union Station, Chicago,
1943; LoC FSA/OWI).  Cut A plays them in pool order; the prints are then
lifted, re-slotted and re-numbered in red pencil, translation only; cut B plays
the same frozen frames in the new order.  Coda: the A->B permutation graph in
red pencil.

Assembly only: every picture element comes from the swarm units.
  notebook segments  swarm/la-machine-a-tuer-le-temps/notebook_rig.py (U2)
  cut segments       frozen pool PNGs (U1 pool-manifest.json) expanded from the
                     recipes A1 / B1 in edit-recipes.json (U3)
  sound              versioned stems from sound_build.py (U4), placed with mix.add
Kit grain is switched off on every frame (ink._grain = False): the pool frames
must stay byte-identical to the manifest and the paper has its own fibre.

Timeline: the animator's 1608 f (67.0 s).  S5 is 216 f, not plan section 7's
192 f, because one print per page needs four page turns; every later segment is
+24 f.

Run from the project root:
  python3 films/la-machine-a-tuer-le-temps.py                 both exports
  python3 films/la-machine-a-tuer-le-temps.py --only final    the film only
  python3 films/la-machine-a-tuer-le-temps.py --only shared   screening-1 export only
  python3 films/la-machine-a-tuer-le-temps.py --stills 5 30 ... PNG stills
"""
import hashlib, json, math, os, sys, wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
SLUG = 'la-machine-a-tuer-le-temps'
SW = HERE / 'swarm' / SLUG
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SW))

import numpy as np
from PIL import Image
from kit import Film, OUT
import notebook_rig as R

FPS = 24
TL = R.TL
TOTAL = TL['total']                      # 1608
SECONDS = TOTAL / FPS                    # 67.0
SRC = HERE / 'sources' / SLUG
ASSETS = SRC / 'registrar' / 'assets'
SND = SRC / 'sound'
CACHE = SRC / 'assembly' / 'nb'
LEDGER = SW / 'render-ledger.json'
MAN = json.load(open(SW / 'pool-manifest.json'))
RECIPES = json.load(open(SW / 'edit-recipes.json'))
POOL_HASH = MAN['pool_hash']
POOL_MD5 = {a['asset_id']: a['frame_md5'] for a in MAN['assets']}
CUTS = {'S3': 'A1', 'S7': 'B1'}


# ------------------------------------------------------------ recipes
def expand(ev):
    """validate.py expansion: src_k = in + step*floor(k*speed)."""
    step = 1 if ev['direction'] == 'fwd' else -1
    return [(ev['asset_id'], ev['in'] + step * int(math.floor(k * ev['speed']))) for k in range(ev['out_frames'])]


EDITS = {e['edit_id']: e for e in RECIPES['edits']}
SEQ = {}
for seg, eid in CUTS.items():
    ed = EDITS[eid]
    assert ed['base_pool_hash'] == POOL_HASH, eid
    SEQ[seg] = [x for ev in ed['events'] for x in expand(ev)]
    assert len(SEQ[seg]) == TL[seg][1] - TL[seg][0] + 1, (seg, len(SEQ[seg]))


def cut_src(k):
    seg = R.segment_of(k)
    if seg in SEQ:
        return seg, SEQ[seg][k - TL[seg][0]]
    return seg, None


# ------------------------------------------------------------ notebook cache
def _rig_key():
    h = hashlib.sha256()
    for p in (SW / 'notebook_rig.py', SW / 'registrar_build.py', SW / 'pool-manifest.json'):
        h.update(p.read_bytes())
    return h.hexdigest()


def _nb_one(f):
    im, led = R.notebook_frame(f)
    im.save(CACHE / f'{f:04d}.png', compress_level=1)
    return f, led


def build_notebook_cache():
    """Render every notebook frame once (4 processes) and keep its rig ledger."""
    CACHE.mkdir(parents=True, exist_ok=True)
    key = _rig_key(); kf = CACHE / 'key.json'
    frames = [f for f in range(TOTAL) if R.segment_of(f) not in SEQ]
    if kf.exists() and json.load(open(kf)).get('key') == key and all((CACHE / f'{f:04d}.png').exists() for f in frames):
        return json.load(open(CACHE / 'rig-ledger.json'))
    R.slips(); R.meta()
    import multiprocessing as mp
    led = {}
    with mp.get_context('fork').Pool(4) as pool:
        for i, (f, l) in enumerate(pool.imap_unordered(_nb_one, frames, chunksize=4)):
            led[str(f)] = l
            if i % 100 == 0:
                print(f'  notebook {i}/{len(frames)}', flush=True)
    json.dump(led, open(CACHE / 'rig-ledger.json', 'w'))
    json.dump({'key': key}, open(kf, 'w'))
    return led


def nb_image(f):
    p = CACHE / f'{f:04d}.png'
    if p.exists() and (CACHE / 'key.json').exists():
        return Image.open(p).convert('RGB')
    return R.notebook_frame(f)[0]


# ------------------------------------------------------------ picture
def picture(t, ink):
    k = ink.i
    ink._grain = False                     # no kit grain on prints or paper
    seg, a = cut_src(k)
    if a is not None:
        img = Image.open(ASSETS / a[0] / f'{a[1]:04d}.png').convert('RGB')
    else:
        img = nb_image(k)
    ink.paste(img, (0, 0))


# ------------------------------------------------------------ sound
def _wav(name):
    with wave.open(str(SND / name)) as w:
        assert w.getframerate() == 44100 and w.getnchannels() == 2
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float64) / 32768


def _put(mix, x, frame):
    at = frame / FPS
    mix.add(x[:, 0], at, gain=1 / 1.414, pan=-1.0)   # kit pan law: L only, x1.414
    mix.add(x[:, 1], at, gain=1 / 1.414, pan=1.0)


XF = 6                                   # cut-mix -> bed crossfade, last frames of cut A


def _fr(n):
    return int(round(n / FPS * 44100))


def _fade(x, a, b, up):
    """Linear gain ramp over samples [a, b) (up: 0->1, else 1->0); beyond b: 1 (up) or 0."""
    g = np.ones(len(x))
    r = np.linspace(0, 1, b - a) if up else np.linspace(1, 0, b - a)
    if up:
        g[:a] = 0; g[a:b] = r
    else:
        g[a:b] = r; g[b:] = 0
    return x * g[:, None]


def sound_for(variant):
    """variant 'final': T0 + T2 + mix A (T3) under S3 + mix B (T4) under S7.
    variant 'shared': T0 + T2 + the same shared bed T1 under both cuts.

    Repair round 1: outside S3/S7 the two exports carry the same samples.
      - S4 (pull-out after A) is the T1 bed's fall in BOTH exports; in the film,
        mix A crossfades into it over the last 6 frames of cut A.
      - S8 (pull-out after B) has no cut bed in either export: mix B already
        reaches digital zero at cut frame 559; the shared bed fades out over
        cut frames 552-563.
      - T0 room is identical under A's and B's frames 0..479 (sound_build.py),
        so the shared export is sample-identical from each cut's frame 0."""
    def fn(mix):
        _put(mix, _wav('T0_room_v2.wav'), 0)
        _put(mix, _wav('T2_foley_v2.wav'), 0)
        pre = _wav('T1_bed_preroll_v2.wav')
        _put(mix, pre, TL['S1'][0])                       # bed fades in under S1, rises under S2
        _put(mix, pre[-int(18 / FPS * 44100):], TL['S6'][0])   # rise under the S6 push
        bedA = _wav('T1_bed_cutA-slot_v2.wav')            # 498 f: identical to T1 for 0..479, then falls
        nA, nB = TL['S3'][1] - TL['S3'][0] + 1, TL['S7'][1] - TL['S7'][0] + 1
        if variant == 'final':
            a = _fr(nA - XF)
            _put(mix, _fade(_wav('T3_mixA_v2.wav')[:_fr(nA)], a, _fr(nA), up=False), TL['S3'][0])
            _put(mix, _fade(bedA, a, _fr(nA), up=True), TL['S3'][0])
            _put(mix, _wav('T4_mixB_v2.wav')[:_fr(nB)], TL['S7'][0])
        else:
            _put(mix, bedA, TL['S3'][0])
            _put(mix, _fade(_wav('T1_bed_v2.wav')[:_fr(nB)], _fr(nB - 12), _fr(nB), up=False), TL['S7'][0])
    return fn


def master_pcm(variant):
    """The exact int16 PCM kit hands to ffmpeg for this export (kit Mix + master)."""
    from kit import Mix
    m = Mix(SECONDS)
    sound_for(variant)(m)
    return m.master()


# ------------------------------------------------------------ ledger
_PMD5 = {}


def print_md5(k):
    """md5 of the frozen toned card print at its (only) table scale."""
    if k not in _PMD5:
        s = R.slips()[k]
        _PMD5[k] = hashlib.md5(R.sample_print(k, (0, 0, 1, 1), (s.pw, s.ph)).tobytes()).hexdigest()
    return _PMD5[k]


def nb_entry(f, rl, md5):
    V = rl['view']; S = R.OW / (V[2] - V[0])
    prints = []
    for p in rl.get('prints', []):
        k = p['asset']; o = p['rect_out']
        tw = (o[2] - o[0]) / S                               # measured table width of the print
        pw = R.meta()[k]['pyr_size'][0]
        declared = R.slips()[k].pw / pw
        measured = tw / pw                                   # rect_out is rounded to 1e-3 px by the rig
        if abs(measured - declared) > 1e-4:
            raise SystemExit(f'frame {f}: print {k} table scale {measured} != {declared}')
        prints.append(dict(asset_id=k, dx=round(V[0] + o[0] / S, 3), dy=round(V[1] + o[1] / S, 3),
                           scale=round(declared, 6), scale_measured=round(measured, 6),
                           camera_scale=p['scale'], rot=0, print_md5=print_md5(k)))
    e = dict(frame=f, segment=rl['segment'], asset_id='notebook', drawing=rl.get('drawing'),
             view=V, prints=prints, md5=md5)
    if rl.get('turning'):
        e['turning'] = rl['turning']
        e['note'] = ('leaf turn: prints on the turning leaf are foreshortened by the physical turn and '
                     'prints at rest are composited at table resolution; excluded from the print check')
    if 'slips' in rl:
        e['slips'] = rl['slips']
    return e


def make_film(variant, ledger):
    slug = SLUG if variant == 'final' else SLUG + '-shared-bed'
    film = Film(slug, seconds=SECONDS, size=(1280, 720), fps=FPS)
    film.picture(picture)
    film.sound(sound_for(variant))
    film.poster_at = (TL['S5'][1] - 6 + 0.5) / FPS         # re-numbered spread at the end of S5
    orig = film.frame

    def frame(k):
        img = orig(k)
        ledger[k] = hashlib.md5(img.tobytes()).hexdigest()
        return img
    film.frame = frame
    return film


def write_ledger(md5s, rig):
    led = []
    for f in range(TOTAL):
        seg, a = cut_src(f)
        if a is not None:
            e = dict(frame=f, segment=seg, edit_id=CUTS[seg], asset_id=a[0], src_frame=a[1], md5=md5s[f])
            if md5s[f] != POOL_MD5[a[0]][a[1]]:
                raise SystemExit(f'frame {f}: rendered md5 differs from pool {a}')
            led.append(e)
        else:
            led.append(nb_entry(f, rig[str(f)], md5s[f]))
    json.dump(dict(slug=SLUG, base_pool_hash=POOL_HASH, fps=FPS, frames=TOTAL, timeline=TL,
                   md5_is='md5 of the RGB24 bytes of the frame handed to ffmpeg (pre-encode)',
                   ledger=led), open(LEDGER, 'w'))
    print('ledger ->', LEDGER)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--stills':
        film = Film(SLUG, seconds=SECONDS, size=(1280, 720), fps=FPS)
        film.picture(picture)
        film.render()
        sys.exit(0)
    if '--reledger' in sys.argv:                 # rebuild the ledger from the recorded frame md5s
        old = json.load(open(LEDGER))['ledger']
        write_ledger({e['frame']: e['md5'] for e in old}, build_notebook_cache())
        sys.exit(0)
    only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else None
    sys.argv = sys.argv[:1]
    rig = build_notebook_cache()
    md5 = {}
    for variant in ('final', 'shared'):
        if only and only != variant:
            continue
        m = {}
        make_film(variant, m).render()
        if variant == 'shared':
            web = OUT / f'{SLUG}-shared-bed.webp'
            if web.exists():
                web.unlink()                                 # only the film keeps a poster
        md5[variant] = m
    if 'final' in md5 and 'shared' in md5:
        same = all(md5['final'][k] == md5['shared'][k] for k in range(TOTAL))
        print('pre-encode picture identical in both exports:', same)
        if not same:
            raise SystemExit('picture differs between exports')
    first = md5.get('final') or md5.get('shared')
    if first:
        write_ledger(first, rig)
