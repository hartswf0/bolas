"""SCION 40 · the MOTION EDITOR's replay: renders the 768 scene frames from the RECOVERED data (data/tracked.json) with
the finished paper pieces on the finished set, with the capture plate as an inset, and measures the trace from the
render. Edits applied to the recovered stream (and only these):
  - contact constraint: the head card's pivot is pinned to the body card's neck (the raw recovered gap is recorded);
  - nothing else: no smoothing, no re-timing; the performers' timing is kept as captured.
Writes cache/film/%04d.jpg (scene frames 72..839 of the film), trace.json, data/onsets.json, data/contact.json."""
import json, math, os, sys
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import replay

CARDS = json.load(open(os.path.join(DATA, 'cards.json')))
TITLE = 72
INSET = (904, 14, 360, 203)      # x, y, w, h


def recovered(fr):
    P = {k: dict(card=v['card'], X=v['X'], Y=v['Y'], th=v['th']) for k, v in fr['pieces'].items()}
    b = P['dog.body']
    bm = CARDS[b['card']]
    nx, ny = to_stage(bm['neck'], bm['anchor'], b['X'], b['Y'], b['th'])
    gap = math.hypot(P['dog.head']['X'] - nx, P['dog.head']['Y'] - ny)
    P['dog.head']['X'], P['dog.head']['Y'] = nx, ny
    return P, gap


def inset(img, i, fr, Hs2p):
    x0, y0, w, h = INSET
    pl = Image.open(os.path.join(CACHE, 'plate', '%04d.jpg' % i)).convert('RGB')
    # overlay what the tracker recovered: the hand matte (red) and each piece's tab and axes (cyan)
    m = Image.open(os.path.join(CACHE, 'matte', '%04d.png' % i)).resize((W, H), Image.BILINEAR)
    inv = np.linalg.inv(Hs2p); inv /= inv[2, 2]
    mp = m.transform((W, H), Image.PERSPECTIVE, tuple(inv.reshape(-1)[:8]), resample=Image.BILINEAR)
    red = Image.new('RGB', (W, H), (230, 40, 30))
    pl = Image.composite(Image.blend(pl, red, 0.45), pl, mp)
    d = ImageDraw.Draw(pl)
    for fam, p in fr['pieces'].items():
        cm = CARDS[p['card']]
        mk = to_stage(cm['tab']['marker'], cm['anchor'], p['X'], p['Y'], p['th'])
        an = (p['X'], p['Y'])
        c, s = math.cos(p['th']), math.sin(p['th'])
        q = apply_h(Hs2p, [mk, an, (an[0] + 40 * c, an[1] - 40 * s), (mk[0] - 18, mk[1] - 18), (mk[0] + 18, mk[1] + 18)])
        d.rectangle([q[3][0], q[3][1], q[4][0], q[4][1]], outline=(60, 230, 230), width=3)
        d.line([tuple(q[0]), tuple(q[1])], fill=(60, 230, 230), width=2)
        d.line([tuple(q[1]), tuple(q[2])], fill=(250, 230, 60), width=4)
    pl = pl.resize((w, h), Image.LANCZOS)
    fr_ = Image.new('RGB', (w + 6, h + 26), (18, 16, 18))
    fr_.paste(pl, (3, 3))
    dd = ImageDraw.Draw(fr_)
    dd.text((6, h + 7), 'CAPTURE (synthesized) %05.2fs  tracked: cyan  hand matte: red' % (i / FPS), fill=(220, 214, 200), font=font('mono', 11))
    img.paste(fr_, (x0 - 3, y0 - 3))


def work(args):
    i, fr, Hs2p = args
    P, gap = recovered(fr)
    img, ba, ha = replay.compose(P)
    inset(img, i, fr, np.array(Hs2p))
    img.save(os.path.join(CACHE, 'film', '%04d.jpg' % (TITLE + i)), quality=93)
    # measure the dog from its own rendered layers
    B = np.asarray(ba) > 127
    Hh = np.asarray(ha) > 127
    A = B | Hh
    ys, xs = np.nonzero(A)
    bys, bxs = np.nonzero(B)
    hys, hxs = np.nonzero(Hh)
    hm = CARDS[P['dog.head']['card']]
    hp = P['dog.head']
    mz = to_stage(hm['muzzle'], hm['anchor'], hp['X'], hp['Y'], hp['th'])
    sk = to_stage(hm['skull'], hm['anchor'], hp['X'], hp['Y'], hp['th'])
    behind = CARDS[P['dog.body']['card']]['head_behind']
    # how much of the head is actually seen (not hidden behind the body in the render)
    seen = float((Hh & ~B).sum() / max(Hh.sum(), 1)) if behind else 1.0
    return dict(i=i, x=float(xs.mean()), y=float(ys.mean()), body_h=float(bys.max() - bys.min()), body_top=float(bys.min()),
                head_y=float(hys.mean()), head_x=float(hxs.mean()), muzzle_x=mz[0], skull_x=sk[0], muzzle_hidden=hm['muzzle_hidden'],
                behind=behind, head_seen=seen, gap=gap, X=P['dog.body']['X'], card=P['dog.body']['card'], head=hp['card'],
                xmin=float(xs.min()), xmax=float(xs.max()))


def segment(M):
    """states from measured signals only"""
    h0 = np.median([m['body_h'] for m in M[:12]])
    x0 = np.median([m['x'] for m in M[:12]])
    st = 'watch'
    states, onsets = [], []
    rest_x = x0
    for k, m in enumerate(M):
        t = m['i'] / FPS
        fac = m['facing']
        ratio = m['body_h'] / h0
        nxt = st
        if st == 'watch' and not any(o['to'] == 'retreat' for o in onsets) and t > 0.4 and (m['x'] - x0 > 3 or ratio < 0.88):
            nxt = 'retreat'
        elif st == 'retreat' and ratio > 0.92:
            nxt = 'watch'
        elif st == 'watch' and any(o['to'] == 'retreat' for o in onsets) and not any(o['to'] == 'refuse' for o in onsets) and fac != 1:
            nxt = 'refuse'
        elif st == 'refuse' and fac == 1:
            nxt = 'watch'; rest_x = None
        elif st == 'watch' and any(o['to'] == 'refuse' for o in onsets):
            if rest_x is None and ratio > 0.92 and fac == 1:
                rest_x = m['x']
            if rest_x is not None and t - onsets[-1]['t'] > 1.0 and rest_x - m['x'] > 3:
                nxt = 'approach'
        elif st == 'approach' and ratio < 0.8:
            nxt = 'lie_down'
        if nxt != st:
            onsets.append(dict(t=round(t, 3), i=m['i'], frm=st, to=nxt))
            st = nxt
        states.append(st)
    return states, onsets, h0


def main():
    T = json.load(open(os.path.join(DATA, 'tracked.json')))['frames']
    cal = json.load(open(os.path.join(DATA, 'calibration.json')))
    Hs2p = np.linalg.inv(np.array(cal['H_plate_to_stage'])); Hs2p /= Hs2p[2, 2]
    os_makedirs(os.path.join(CACHE, 'film'))
    only = [int(a) for a in sys.argv[1:]]
    todo = [(f['i'], f, Hs2p.tolist()) for f in T if (not only or f['i'] in only)]
    with Pool(3) as pool:
        M = sorted(pool.map(work, todo, chunksize=6), key=lambda m: m['i'])
    if only:
        return
    for m in M:
        if m['behind'] or m['muzzle_hidden']:
            m['facing'] = 0                       # the head is round the far side: the dog shows its back
        else:
            dx = m['muzzle_x'] - m['skull_x']
            m['facing'] = 1 if dx < -4 else (-1 if dx > 4 else 0)
    states, onsets, h0 = segment(M)
    frames = []
    for m, s in zip(M, states):
        r = m['body_h'] / h0
        frames.append(dict(i=m['i'], t=round(m['i'] / FPS, 4), state=s, x_score=round(x_score_from_stage(m['X']), 4), x_screen=round(m['x'], 2),
                           y_screen=round(m['y'], 2), facing=m['facing'], posture='standing' if r > 0.88 else ('crouched' if r > 0.66 else 'lying'),
                           body_card=m['card'], head_card=m['head'], head_below_back=bool(m['head_y'] > m['body_top'] + 8),
                           dog_px_extent=[round(m['xmin'], 1), round(m['xmax'], 1)]))
    about = ("SCION 40 · trace measured from the replayed render (not copied from the score).\n"
             "x_screen, y_screen: centroid of the dog's rendered layers (body card + head card alpha > .5), px.\n"
             "facing: +1 when the rendered head card's muzzle point lies left of its skull point (toward the door), -1 right, "
             "0 when the head is round the far side of the body (rear views) or the muzzle is hidden.\n"
             "posture: rendered body-card height against its height in the first half second (standing > .88, crouched > .66, else lying).\n"
             "state: segmented at onsets measured on these signals (see data/onsets.json).\n"
             "x_score: the recovered body-card anchor X mapped back to score metres (the sill 0.56 m sits on the wall line).\n"
             "dog_px_extent: the rendered dog's leftmost and rightmost pixel; the wall line (threshold) is x = %d px." % SILL_X)
    json.dump(dict(about=about, camera='static', frames=frames), open(os.path.join(F, 'trace.json'), 'w'), indent=0)
    sc = SCORE['choices']
    on = []
    for c in sc:
        hit = next((o for o in onsets if o['to'] == c['to'] and o['t'] >= c['t'] - .5), None)
        on.append(dict(score_t=c['t'], to=c['to'], measured_t=hit and hit['t'], dt=hit and round(hit['t'] - c['t'], 3)))
    # 26.4: looking in, measured as the first frame the head card shows the back of the head toward us while lying
    li = next((m for m in M if m['i'] / FPS > 25 and m['head'] == 'h_in'), None)
    on.append(dict(score_t=26.4, to='looks_in', measured_t=li and round(li['i'] / FPS, 3), dt=li and round(li['i'] / FPS - 26.4, 3)))
    gaps = np.array([m['gap'] for m in M])
    json.dump(dict(onsets=on, raw=onsets), open(os.path.join(DATA, 'onsets.json'), 'w'), indent=1)
    json.dump(dict(about='raw recovered distance between the head card pivot and the body card neck before the contact constraint pinned it',
                   mean_px=float(gaps.mean()), p95_px=float(np.percentile(gaps, 95)), max_px=float(gaps.max())), open(os.path.join(DATA, 'contact.json'), 'w'), indent=1)
    print(json.dumps(on, indent=0))
    print('contact gap px mean %.2f p95 %.2f max %.2f' % (gaps.mean(), np.percentile(gaps, 95), gaps.max()))


if __name__ == '__main__':
    main()
