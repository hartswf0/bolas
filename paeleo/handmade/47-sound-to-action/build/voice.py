"""Alignment engineer. Synthesize each spoken line with CMU Flite (libflite 2.2, voice cmu_us_slt, called through ctypes)
and read the phoneme timing from the synthesizer's own Segment relation, so picture and sound share one time base.

(First attempt, kept in build/rejected_viterbi_aligner.py and proof/alignment_rejected_viterbi.png: a hand-set
forced aligner on energy/voicing features. It misplaced vowels into nasals; rejected for the synthesizer's own segments.)

Output: build/cache/voice/<id>.wav (16 kHz mono) and build/voice_lines.json:
  {id, text, kind, dur, words:[{w,t0,t1}], phones:[{p,t0,t1,word,stress}], stress_onset, prosody}
Times: seconds from the start of the line's wave.
python3 build/voice.py
"""
import ctypes as C, json, os, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache', 'voice')
os.makedirs(CACHE, exist_ok=True)

# id, text, kind, prosody (f0 mean Hz, duration stretch), the word that carries the cue the dog reacts to
LINES = [
    ('call1', 'Come here!', 'call', (205, 0.95), 'here'),
    ('call2', 'Come on. Come here!', 'call', (210, 0.92), 'here'),
    ('call3', 'Come here!', 'call', (228, 0.9), 'here'),
    ('call4', 'Come on!', 'call', (222, 0.9), 'on'),
    ('soft1', "It's all right.", 'soft', (150, 1.3), 'it'),
    ('soft2', "It's okay.", 'soft', (146, 1.35), 'it'),
    ('soft3', 'Come in.', 'soft', (148, 1.3), 'in'),
]


class Wave(C.Structure):
    _fields_ = [('type', C.c_char_p), ('sample_rate', C.c_int), ('num_samples', C.c_int), ('num_channels', C.c_int),
                ('samples', C.POINTER(C.c_short))]


def flite():
    fl = C.CDLL('libflite.so.1', mode=C.RTLD_GLOBAL)
    C.CDLL('libflite_usenglish.so.1', mode=C.RTLD_GLOBAL); C.CDLL('libflite_cmulex.so.1', mode=C.RTLD_GLOBAL)
    slt = C.CDLL('libflite_cmu_us_slt.so.1')
    fl.flite_init()
    slt.register_cmu_us_slt.restype = C.c_void_p
    v = slt.register_cmu_us_slt(None)
    for name, res, args in [('flite_synth_text', C.c_void_p, [C.c_char_p, C.c_void_p]),
                            ('utt_relation', C.c_void_p, [C.c_void_p, C.c_char_p]),
                            ('relation_head', C.c_void_p, [C.c_void_p]), ('item_next', C.c_void_p, [C.c_void_p]),
                            ('ffeature_string', C.c_char_p, [C.c_void_p, C.c_char_p]),
                            ('ffeature_float', C.c_float, [C.c_void_p, C.c_char_p]),
                            ('utt_wave', C.POINTER(Wave), [C.c_void_p]),
                            ('flite_feat_set_float', None, [C.c_void_p, C.c_char_p, C.c_float])]:
        f = getattr(fl, name); f.restype = res; f.argtypes = args
    feats = C.cast(v + 8, C.POINTER(C.c_void_p))[0]  # cst_voice.features
    return fl, v, feats


def main():
    fl, v, feats = flite()
    res = []
    for lid, text, kind, (f0, stretch), cue_word in LINES:
        fl.flite_feat_set_float(feats, b'int_f0_target_mean', float(f0))
        fl.flite_feat_set_float(feats, b'duration_stretch', float(stretch))
        u = fl.flite_synth_text(text.encode(), v)
        w = fl.utt_wave(u).contents
        x = np.ctypeslib.as_array(w.samples, shape=(w.num_samples,)).astype(np.float32) / 32768
        sr = w.sample_rate
        it = fl.relation_head(fl.utt_relation(u, b'Segment'))
        segs, t0 = [], 0.0
        while it:
            name = fl.ffeature_string(it, b'name').decode(); end = fl.ffeature_float(it, b'end')
            word = fl.ffeature_string(it, b'R:SylStructure.parent.parent.name').decode()
            stress = fl.ffeature_string(it, b'R:SylStructure.parent.stress').decode()
            segs.append({'p': name, 't0': t0, 't1': end, 'word': word, 'stress': stress})
            t0 = end; it = fl.item_next(it)
        # trim: start 40 ms before the first non-pause phone, end 60 ms after the last
        sp = [s for s in segs if s['p'] != 'pau']
        a = max(0.0, sp[0]['t0'] - 0.04); b = min(len(x) / sr, sp[-1]['t1'] + 0.06)
        x = x[int(a * sr):int(b * sr)]
        phones = [{'p': s['p'], 't0': round(s['t0'] - a, 4), 't1': round(s['t1'] - a, 4), 'word': s['word'],
                   'stress': s['stress']} for s in sp]
        words = []
        for p in phones:
            if words and words[-1]['w'] == p['word'] and words[-1]['t1'] == p['t0']:
                words[-1]['t1'] = p['t1']
            else:
                words.append({'w': p['word'], 't0': p['t0'], 't1': p['t1']})
        vow = set('aa ae ah ao aw ay eh er ey ih iy ow oy uh uw'.split())
        cw = [wd for wd in words if wd['w'].replace("'", '') == cue_word.replace("'", '')][-1]
        cue = next(p for p in phones if p['p'] in vow and p['t0'] >= cw['t0'] - 1e-6)
        out = os.path.join(CACHE, lid + '.wav')
        with wave.open(out, 'w') as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
            wf.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
        res.append({'id': lid, 'text': text, 'kind': kind, 'sr': sr, 'dur': round(len(x) / sr, 4), 'words': words,
                    'phones': phones, 'cue_word': cue_word, 'cue_vowel_onset': cue['t0'],
                    'prosody': {'int_f0_target_mean': f0, 'duration_stretch': stretch},
                    'synth': 'CMU Flite 2.2 (libflite, BSD-style licence), voice cmu_us_slt, via ctypes'})
        print(lid, text, round(len(x) / sr, 3), ' '.join(f"{p['p']}:{p['t0']:.2f}" for p in phones), 'cue', cue['t0'])
    json.dump(res, open(os.path.join(HERE, 'voice_lines.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
