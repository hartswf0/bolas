"""U3 sound engine (#47 Sound-to-Action: pen strokes play the role of visemes).

cues.build(...) reads the letterer's write-on schedule (balloons.json), the plate-artist's prologue
schedule (S0 brush strokes) and the film timeline (plan.json 'shots'), and emits:
  * one real pen-scratch grain per written stroke (grain length = stroke duration, gain = stroke speed),
  * a soft real pen tap at the pen lift of every full stop and of the '?' dot,
  * a soft paper tap for each S1 panel stamp,
  * the low night-ambience bed (fade in over S0, fade out over the last 2 s; A3 is ambience only).
Returns mono float64 numpy arrays at kit.RATE, ready for kit Mix.add(sig, 0.0, gain=1.0).

Editor use:
    sys.path.insert(0, '<swarm>/sound-build'); import cues
    S = cues.build()                      # or cues.build(s1=dict(stamp_t0=..., header_t0=...))
    mix.add(S['ambience'], 0.0, pan=-0.1); mix.add(S['pen'], 0.0, pan=0.08)
    # S['cues'] is the cue list, S['checks'] the invariant checks.
Run as a script to print the checks and write sound/cues.json, pen.wav, ambience-bed.wav, mix-preview.wav.
"""
import json, os, sys, wave
import numpy as np

FPS = 24
SR = 44100
SLUG = 'moins-dun-quart-de-seconde-pour-vivre'
OULIPO = '/home/user/bolas/paeleo/scion/oulipo'
SWARM = f'{OULIPO}/films/swarm/{SLUG}'
SRC = f'{OULIPO}/films/sources/{SLUG}'
SND = f'{SRC}/sound'
FILM_S = 66.0
A3 = (21.6, 26.0)
LETTERED = ('A1', 'A2', 'A4', 'B1', 'B2', 'B3', 'B4')


# ------------------------------------------------------------------ io
def read_wav(path):
    with wave.open(path, 'rb') as w:
        assert w.getframerate() == SR and w.getnchannels() == 1 and w.getsampwidth() == 2
        return np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float64) / 32767


def write_wav(path, x, sr=SR):
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())


def lowpass(x, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / (1 + (f / hi) ** 4), len(x))


def path_len(p):
    p = np.asarray(p, float)
    return float(np.hypot(*np.diff(p, axis=0).T).sum()) if len(p) > 1 else 0.0


# ------------------------------------------------------------------ schedules
def shot_starts(plan):
    return {s['id']: float(s['t'][0]) for s in plan['shots']}


def balloon_strokes(balloons, starts):
    """Every written stroke of every lettered panel, in film time."""
    out = []
    for key in LETTERED:
        p = balloons['panels'][key]
        F0 = int(round(starts[key] * FPS))       # panels start on a whole film frame (A2 15.6 s -> frame 374)
        for s in p['strokes']:
            L = s.get('length_px') or path_len(s['path'])
            out.append(dict(src=key, idx=s['idx'], kind=s['kind'], ch=s.get('ch'), stroke_in_glyph=s.get('stroke_in_glyph'),
                            t0=(F0 + s['t0_f']) / FPS, t1=(F0 + s['t1_f']) / FPS, length_px=L,
                            ref_frame=int(round(F0)) + int(s['on_frame'])))
        # full-stop / question-mark taps at the pen lift of the dot
        strokes = p['strokes']
        for i, s in enumerate(strokes):
            nxt = strokes[i + 1] if i + 1 < len(strokes) else None
            is_last_of_glyph = nxt is None or nxt.get('glyph_index') != s.get('glyph_index')
            if s.get('ch') in ('.', '?') and is_last_of_glyph:
                out.append(dict(src=key, idx=s['idx'], kind='tap', ch=s['ch'], t0=(F0 + s['t1_f']) / FPS, t1=None,
                                length_px=0.0, ref_frame=int(round(F0)) + int(s['done_frame'])))
    return out


def pen_hold_window(balloons, starts):
    h = balloons['panels']['B4']['pen_hold']
    F0 = int(round(starts['B4'] * FPS))
    return ((F0 + h['t0_f']) / FPS, (F0 + h['t1_f']) / FPS)


def prologue_strokes(prologue, plate_strokes, t_start=0.0):
    """S0 brush strokes: onset = first frame on which part of stroke k is on the plate,
    end = first frame on which it is complete. Length = its dab-op count (brush path)."""
    args = prologue['draw_on']['render_upto_args_after_frame']
    f_lo = prologue['draw_on']['frames'][0]
    n = len(plate_strokes)
    out = []
    for k in range(n):
        on = next((f for f, (i, part) in enumerate(args) if i > k or (i == k and part > 0)), None)
        done = next((f for f, (i, part) in enumerate(args) if i > k), len(args) - 1)
        if on is None:
            continue
        ops = len(plate_strokes[k]['ops']) if isinstance(plate_strokes[k]['ops'], list) else 0
        out.append(dict(src='S0', idx=k, kind='brush', ch=plate_strokes[k]['name'], t0=t_start + (f_lo + on) / FPS,
                        t1=t_start + (f_lo + done + 1) / FPS, length_px=float(ops), ref_frame=int(round(t_start * FPS)) + f_lo + on))
    return out


def s1_events(balloons, starts, stamp_t0=None, stamp_every_f=4, header_t0=None, header_frames=19):
    """S1 'the page is printed': 7 panel stamps (soft paper taps) every 4 frames, then header and strip
    labels written on in ~0.8 s (strokes scaled by header_frames/natural_write_frames, items in parallel).
    The defaults are provisional until the editor fixes S1; pass the editor's values."""
    t = starts['S1']
    stamp_t0 = t + 0.5 if stamp_t0 is None else stamp_t0
    header_t0 = stamp_t0 + 7 * stamp_every_f / FPS + 2 / FPS if header_t0 is None else header_t0
    ev = [dict(src='S1', idx=i, kind='stamp', ch=None, t0=stamp_t0 + i * stamp_every_f / FPS, t1=None, length_px=0.0,
               ref_frame=int(round((stamp_t0 + i * stamp_every_f / FPS) * FPS))) for i in range(7)]
    for item in ('header', 'header-right', 'label-A', 'label-B'):
        it = balloons['page_lettering'][item]
        sc = header_frames / it['natural_write_frames']
        for s in it['strokes']:
            t0 = header_t0 + s['t0_f'] * sc / FPS
            ev.append(dict(src='S1:' + item, idx=s['idx'], kind='label', ch=s.get('ch'), t0=t0, t1=header_t0 + s['t1_f'] * sc / FPS,
                           length_px=path_len(s['path']), ref_frame=int(np.floor(t0 * FPS + 1e-9))))
    return ev


# ------------------------------------------------------------------ the engine
class Bank:
    def __init__(self):
        self.meta = json.load(open(f'{SND}/bank.json'))
        self.pen = read_wav(f'{SND}/pen-44k.wav')
        self.amb = read_wav(f'{SND}/ambience-44k.wav')
        self.onsets = [g['a'] for g in self.meta['grains']]
        self.taps = [read_wav(f"{SND}/{t['file']}") for t in self.meta['taps']]

    def grain(self, dur, rs, max_n=None):
        """A real scratch: the recording from a detected pen-down onset, for exactly the stroke's duration
        (at least 35 ms so a tiny stroke is still heard, but never running into a protected silence)."""
        n = max(int(0.035 * SR), int(dur * SR))
        if max_n is not None:
            n = max(int(0.012 * SR), min(n, max_n))
        cands = [a for a in self.onsets if a + n < len(self.pen)]
        a = cands[rs.randint(len(cands))]
        g = self.pen[a:a + n].copy()
        att, rel = int(0.003 * SR), min(n // 3, int(0.012 * SR))
        g[:att] *= np.linspace(0, 1, att)
        g[-rel:] *= np.linspace(1, 0, rel)
        return g / max(1e-9, np.sqrt((g ** 2).mean())) * 0.065, a   # level-normalised (RMS), gain applied by speed


def speed_gain(speed, ref):
    return float(np.clip(0.45 + 0.55 * np.sqrt(speed / ref), 0.35, 1.15))


def build(s1=None, seed=47, pen_gain=1.0, amb_rms=0.014):
    plan = json.load(open(f'{SWARM}/plan.json'))
    balloons = json.load(open(f'{SWARM}/balloons.json'))
    starts = shot_starts(plan)
    prologue = json.load(open(f'{SRC}/plate-artist/prologue-schedule.json'))
    plate_strokes = json.load(open(f'{SRC}/plate/strokes.json'))['strokes']
    bank = Bank()
    rs = np.random.RandomState(seed)
    N = int(FILM_S * SR)
    hold = pen_hold_window(balloons, starts)
    protected = [A3, hold]
    pen = np.zeros(N)

    ev = prologue_strokes(prologue, plate_strokes, starts['S0']) + s1_events(balloons, starts, **(s1 or {})) + balloon_strokes(balloons, starts)
    ev.sort(key=lambda e: e['t0'])
    glyph_speeds = [e['length_px'] / max(1e-3, e['t1'] - e['t0']) for e in ev if e['kind'] in ('glyph', 'outline', 'tail-stub')]
    ref_glyph = float(np.median(glyph_speeds))
    brush_speeds = [e['length_px'] / max(1e-3, e['t1'] - e['t0']) for e in ev if e['kind'] == 'brush']
    ref_brush = float(np.median(brush_speeds)) if brush_speeds else 1.0

    cues = []
    for e in ev:
        i = int(round(e['t0'] * SR))
        if e['kind'] in ('tap', 'stamp'):
            tap = bank.taps[rs.randint(len(bank.taps))]
            if e['kind'] == 'stamp':
                sig, g, src_a = lowpass(tap, 1800) * 0.6, 0.30, None      # paper stamp: same real tap, duller, far
            else:
                sig, g, src_a = tap, 0.38, None
            dur = len(sig) / SR
        else:
            dur = max(0.035, e['t1'] - e['t0'])
            room = [int(a * SR) - i - 1 for a, b in protected if int(a * SR) > i]
            sig, src_a = bank.grain(dur, rs, max_n=min(room) if room else None)
            speed = e['length_px'] / dur
            if e['kind'] == 'brush':
                g = 0.55 * speed_gain(speed, ref_brush)
                sig = lowpass(sig, 4200) * 1.4                             # brush: same paper scratch, softer edge
            elif e['kind'] == 'label':
                g = 0.40 * speed_gain(speed, ref_glyph)                    # page seen far off at S1
                sig = lowpass(sig, 6000)
            else:
                g = speed_gain(speed, ref_glyph)
                if e['kind'] == 'outline':
                    sig = lowpass(sig, 5000) * 1.2                         # balloon contour is brushed
        sig = sig * g * pen_gain
        j = min(N, i + len(sig))
        pen[i:j] += sig[: j - i]
        cues.append(dict(src=e['src'], idx=e['idx'], kind=e['kind'], ch=e['ch'], t=round(i / SR, 4), frame=round(i / SR * FPS, 3),
                         stroke_t=round(e['t0'], 4), i0=i, i1=j,
                         ref_frame=e['ref_frame'], dur=round(len(sig) / SR, 4), end=round(j / SR, 4), gain=round(g, 3),
                         length_px=round(e['length_px'], 1), grain_src_offset_s=None if src_a is None else round(src_a / SR, 3)))

    amb = ambience_bed(bank.amb, N, starts, amb_rms)
    checks = run_checks(cues, pen, starts, hold, balloons)
    return dict(pen=pen, ambience=amb, amb_offset_s=round(ambience_bed.offset_s, 2), cues=cues, checks=checks, pen_hold=hold, starts=starts,
                s1=s1 or 'provisional defaults (stamps from S1+0.5 s every 4 f, header/labels after the 7th stamp, 19 f)')


def loop_bed(src, N, offset, xf):
    """Real recording looped from `offset` with equal-power crossfades of xf samples."""
    bed = np.zeros(N + 2 * len(src))
    w = np.sin(np.linspace(0, np.pi / 2, xf)) ** 2
    seg0 = src[offset:].copy()
    pos, first = 0, True
    while pos < N:
        seg = (seg0 if first else src).copy()
        if not first:
            seg[:xf] *= np.sqrt(w)
        seg[-xf:] *= np.sqrt(w[::-1])
        bed[pos:pos + len(seg)] += seg
        pos += len(seg) - xf
        first = False
    return bed[:N]


def choose_offset(src, N, starts, xf):
    """The recording has natural pauses in the insect chorus. Pick the loop start so the chorus is
    steady through A3 (the declared silence must be heard as night, not as a dropout) and through
    the last 4 s of the film. Searched on a 0.25 s grid; score = quietest 0.5 s window in those spans."""
    hop = int(0.5 * SR)
    best = (-1e9, 0)
    for off in range(0, len(src) - xf, int(0.25 * SR)):
        b = loop_bed(src, N, off, xf)
        score = 1e9
        for a, z in ((A3[0] - 0.5, A3[1] + 0.5), (FILM_S - 4.0, FILM_S - 0.5), (starts['S0'] + 2.0, starts['S1'])):
            seg = b[int(a * SR):int(z * SR)]
            n = len(seg) // hop
            r = np.sqrt((seg[: n * hop].reshape(n, hop) ** 2).mean(1)).min()
            score = min(score, r)
        if score > best[0]:
            best = (score, off)
    return best[1]


def ambience_bed(src, N, starts, rms):
    """Loop the real night recording with 1.5 s equal-power crossfades, set to a low RMS,
    fade in over S0 (0-6 s) and out over the last 2 s. Nothing is ducked or removed in A3."""
    xf = int(1.5 * SR)
    off = choose_offset(src, N, starts, xf)
    bed = loop_bed(src, N, off, xf)
    bed *= rms / max(1e-9, np.sqrt((bed ** 2).mean()))
    t = np.arange(N) / SR
    fin = np.clip(t / starts['S1'], 0, 1) ** 2
    fout = np.clip((FILM_S - t) / 2.0, 0, 1)
    ambience_bed.offset_s = off / SR
    return bed * fin * fout


def run_checks(cues, pen, starts, hold, balloons):
    fr = lambda c: c['t'] * FPS
    stroke_cues = [c for c in cues if c['kind'] not in ('stamp',)]
    off = [abs(fr(c) - c['ref_frame']) for c in stroke_cues]
    # measured onset in the rendered track: first 1 ms window over -40 dB of the grain peak, within each cue
    meas = []
    for c in stroke_cues:
        i = int(c['t'] * SR); n = int(c['dur'] * SR)
        seg = np.abs(pen[i:i + n])
        if not len(seg):
            continue
        thr = seg.max() * 0.01
        k = int(np.argmax(seg > thr))
        meas.append(abs((i + k) / SR - c['stroke_t']) * FPS)

    def in_win(c, a, b):
        return c['i0'] < int(b * SR) and c['i1'] > int(a * SR)
    a3_cues = [c for c in cues if in_win(c, *A3)]
    hold_cues = [c for c in cues if in_win(c, *hold)]
    a3_peak = float(np.abs(pen[int(A3[0] * SR):int(A3[1] * SR)]).max())
    hold_peak = float(np.abs(pen[int(hold[0] * SR):int(hold[1] * SR)]).max())
    # no flapping in silence: post-write holds of every lettered panel carry no cue
    flaps = {}
    for key in LETTERED:
        p = balloons['panels'][key]
        F0 = int(round(starts[key] * FPS))
        last = max(s['t1_f'] for s in p['strokes'])
        a, b = (F0 + last) / FPS + 0.10, starts[key] + p['slot_s'] - 0.0
        flaps[key] = len([c for c in cues if in_win(c, a, b)])
    per_stroke = {}
    for key in LETTERED:
        per_stroke[key] = dict(strokes=len(balloons['panels'][key]['strokes']),
                               grains=len([c for c in cues if c['src'] == key and c['kind'] != 'tap']),
                               taps=len([c for c in cues if c['src'] == key and c['kind'] == 'tap']))
    ch = dict(
        n_cues=len(cues),
        onset_vs_stroke_max_frames_scheduled=round(max(off), 3),
        onset_vs_stroke_definition='scheduled: cue onset vs the first film frame on which the stroke is visible (panel start frame + on_frame; taps vs done_frame); measured: first 1 ms of the rendered pen track over 1% of the grain peak vs the stroke t0 in the schedule',
        onset_vs_stroke_max_frames_measured=round(max(meas), 3),
        onset_within_1_frame=bool(max(off) <= 1.0 and max(meas) <= 1.0),
        one_grain_per_stroke=all(v['strokes'] == v['grains'] for v in per_stroke.values()),
        per_panel=per_stroke,
        A3_window_s=list(A3), A3_cues=len(a3_cues), A3_pen_peak=a3_peak,
        B4_pen_hold_s=[round(hold[0], 4), round(hold[1], 4)], B4_hold_cues=len(hold_cues), B4_hold_pen_peak=hold_peak,
        post_balloon_hold_cues=flaps,
        no_flapping_in_holds=all(v == 0 for v in flaps.values()),
        taps=[(c['src'], c['ch'], c['t']) for c in cues if c['kind'] == 'tap'],
    )
    ch['all_pass'] = bool(ch['onset_within_1_frame'] and ch['one_grain_per_stroke'] and ch['A3_cues'] == 0 and a3_peak == 0.0
                          and ch['B4_hold_cues'] == 0 and hold_peak == 0.0 and ch['no_flapping_in_holds'])
    return ch


if __name__ == '__main__':
    S = build()
    c = S['checks']
    print('cues', c['n_cues'], '| onset vs stroke onset: scheduled max', c['onset_vs_stroke_max_frames_scheduled'],
          'f, measured max', c['onset_vs_stroke_max_frames_measured'], 'f ->', 'PASS' if c['onset_within_1_frame'] else 'FAIL')
    print('one grain per stroke:', c['one_grain_per_stroke'], c['per_panel'])
    print('A3', c['A3_window_s'], 'cues', c['A3_cues'], 'pen peak', c['A3_pen_peak'])
    print('B4 pen hold', c['B4_pen_hold_s'], 'cues', c['B4_hold_cues'], 'pen peak', c['B4_hold_pen_peak'])
    print('post-balloon holds cues', c['post_balloon_hold_cues'])
    print('taps', c['taps'])
    print('ALL PASS' if c['all_pass'] else 'CHECKS FAIL')
    write_wav(f'{SND}/pen-track.wav', S['pen'])
    write_wav(f'{SND}/ambience-bed.wav', S['ambience'])
    m = S['pen'] * 0.6 + S['ambience']
    write_wav(f'{SND}/mix-preview.wav', m / max(1e-9, np.abs(m).max()) * 0.89)
    json.dump(dict(amb_offset_s=S['amb_offset_s'], cues=S['cues'], checks=c, pen_hold=S['pen_hold'], s1=S['s1']), open(f'{SND}/cues.json', 'w'), indent=0)
    sys.exit(0 if c['all_pass'] else 1)
