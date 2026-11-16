"""Editor repair round 2 (E3): bring scenes.json, print.json, ledger.json and the credits to the E3 state.

    python3 -I films/swarm/la-belle-hortense/editor/docs_e3.py
"""
import json, os

ROOT = '/home/user/bolas/paeleo/scion/oulipo'
SW = os.path.join(ROOT, 'films/swarm/la-belle-hortense')
ED = 'films/sources/la-belle-hortense/editor'
TYPE = ED + '/type/HortenseSlab-{Bold,Regular}.ttf'

def load(p): return json.load(open(os.path.join(ROOT, p)))
def save(p, o): json.dump(o, open(os.path.join(ROOT, p), 'w'), indent=1, ensure_ascii=False)

# ------------------------------------------------------------------ print.json: hook, pencil outline, typeface
pj = load('films/swarm/la-belle-hortense/print.json')
pj['objects'] = [o for o in pj['objects'] if o['id'] not in ('HOOK', 'KEY-OUTLINE', 'TYPEFACE')]
pj['objects'] += [
    {'id': 'HOOK', 'what': 'VI.5: a bent-wire key hook (drawn stroke by stroke: shank, eye, curl), the key hung on it by its bow',
     'made_by': 'editor', 'script': 'films/swarm/la-belle-hortense/editor/editor_beats.py hook_draw()', 'slots': ['VI.5'],
     'licence': 'handmade for this film (CC BY-SA 4.0 with the film)'},
    {'id': 'KEY-OUTLINE', 'what': "II.6: red grease-pencil outline traced round the key's own cut mask, foreshortened on the empty seat (the key's absence)",
     'made_by': 'editor E3', 'script': 'films/swarm/la-belle-hortense/editor/repair3_beats.py chalk_outline()', 'slots': ['II.6'],
     'licence': 'handmade for this film (CC BY-SA 4.0 with the film)'},
    {'id': 'TYPEFACE', 'what': 'Hortense Slab Bold / Regular: a monospaced slab-serif typewriter face drawn glyph by glyph as pen strokes and slab serifs, traced to TrueType outlines (all type in the film, sigma included)',
     'made_by': 'editor E3', 'script': 'films/swarm/la-belle-hortense/editor/typeface.py', 'files': [TYPE, ED + '/type/specimen.png'],
     'licence': 'handmade for this film (CC BY-SA 4.0 with the film)',
     'replaces': 'Courier 10 Pitch (X Consortium/Bitstream licence) and the DejaVu Sans Mono sigma (Bitstream Vera licence): neither licence is in the allowed set'},
]
pj['font'] = {'face': 'Hortense Slab Bold / Regular (handmade, see object TYPEFACE)', 'files': TYPE,
              'licence': 'handmade for the work; CC BY-SA 4.0 with the film'}
for o in pj['objects']:
    if o['id'] == 'ENVELOPE':
        o['status'] = 'superseded on screen in I.3 by the LoC 1861 envelope (ENVELOPE-LOC, LoC 2010652109); kept here as a built object, not shown'
save('films/swarm/la-belle-hortense/print.json', pj)

# ------------------------------------------------------------------ scenes.json: evidence to the E3 state
sc = load('films/swarm/la-belle-hortense/scenes.json')
ev = sc['evidence']
ev['revision'] = 'E3 (editor repair round 2, 2026-11-16)'
ids = {f['id'] for f in ev['foraged']}
ev['foraged'] = [f for f in ev['foraged'] if f['id'] != 'FONT']
cr = {c['title']: c for c in load('films/credits/la-belle-hortense.json')}
def crd(prefix):
    return [c for t, c in cr.items() if t.startswith(prefix)][0]
for fid, pre in (('ENVELOPE-LOC', '[Stamped envelope'), ('KEYS-SND', 'Keys hitting tree 2'), ('HANDLE', 'Door handle creaking'),
                 ('HINGE', 'Squeaky door hinge'), ('LOCK', '342706 spacejoe'), ('PAPER', 'Book paper pages'),
                 ('BELL-SND', 'Glockenschlagwerk')):
    if fid in ids: continue
    c = crd(pre)
    ev['foraged'].append(dict(id=fid, title=c['title'], author=c['author'], license=c['license'], license_url=c['license_url'],
                              source_url=c['source_url'], file_url=c['file_url'], used_as=c['used_as']))
ev['handmade'] = [h for h in ev['handmade'] if h['id'] not in ('ENVELOPE', 'TICKET', 'TYPE', 'HOOK', 'KEY-OUTLINE', 'TYPEFACE', 'RIG-E3')]
ev['handmade'] += [
    {'id': 'TICKET', 'what': "receipt card (U4 print.json RECEIPT): REÇU N° 6 / une clé / porte de service / remise au banc, red circled 6, strike-through and underline type-on, RENDU stamp", 'where': 'print.json RECEIPT'},
    {'id': 'TYPEFACE', 'what': 'Hortense Slab, handmade typewriter face for all type', 'where': 'print.json TYPEFACE; editor/typeface.py'},
    {'id': 'HOOK', 'what': 'VI.5 bent-wire key hook', 'where': 'print.json HOOK'},
    {'id': 'KEY-OUTLINE', 'what': "II.6 pencilled outline of the key on the empty seat", 'where': 'print.json KEY-OUTLINE'},
    {'id': 'RIG-E3', 'what': "visitor: upper-arm piece cut from the back-view body along the sleeve's inner edge, hinged at the shoulder, forearm child at the elbow (I.4); conductor 'without his coat': his own print undyed, narrowed 0.70 below the collar, jacket-length sleeve (II.2); II.2 reach pose swings the forearm to -100 deg (declared extension of the runner's [-30, 22] limit, this beat only)",
     'where': 'editor/repair3_beats.py'},
]
ev['absences'] = [a for a in ev['absences'] if 'key-tink' not in a['searched'] and 'key hook' not in a['searched']]
ev['absences'].append({'searched': 'a PD/CC photograph of a man without an overcoat in the conductor\'s pose', 'result': 'not searched (time budget): II.2 builds him from his own print, undyed and narrowed (RIG-E3)'})
ev['superseded'] = ['ENVELOPE (typed-address handmade envelope): replaced on screen by ENVELOPE-LOC',
                    "absence 'Keys hitting tree 2.ogg missing ... key tinks synthesised': the Gravity Sound .wav (CC BY 4.0) was found and live-verified by U4 and review-2; the tinks are that recording",
                    'FONT Courier 10 Pitch and the DejaVu sigma: replaced by TYPEFACE (handmade)']
E = 'films/sources/la-belle-hortense/editor/clips/'
NEW = {'I.1': 'I1_manteau_E3', 'I.2': 'I2_cloche_E3', 'I.4': 'I4_banc_E3', 'I.5': 'I5_recu_E3', 'I.6': 'I6_porte_E3',
       'II.2': 'II2_manteau_E3', 'II.6': 'II6_cle_E3', 'III.4': 'III4_manteau_E3', 'IV.2': 'I4_banc_E3', 'VI.2': 'I4_banc_E3',
       'VI.6': 'I1_manteau_E3'}
FN = {'I4_banc_E3': 'repair3_beats.I4(t_local, sil=False)', 'II2_manteau_E3': 'repair3_beats.II2(t_local, sil=False)',
      'II6_cle_E3': 'repair3_beats.II6(t_local)', 'III4_manteau_E3': 'repair3_beats.III4(t_local)'}
for s in sc['slots']:
    if s['id'] in NEW:
        n = NEW[s['id']]
        s['clip'] = E + n + '.mp4'; s['still'] = 'films/sources/la-belle-hortense/editor/stills/' + n + '_mid.png'
        s['frame_function'] = FN.get(n, s.get('frame_function', '') + ' via repair3_beats (coat 0.30 on the bench\'s left half)')
        s['owner'] = 'editor E3'
        if s['id'] in ('IV.2', 'VI.2'): s['note'] = 'replay of the I.4 pixels, framed and tagged I·4'
sc['revision'] = 'A1 + editor E3'
sc['type_font'] = 'Hortense Slab (handmade; print.json TYPEFACE)'
save('films/swarm/la-belle-hortense/scenes.json', sc)

# ------------------------------------------------------------------ ledger.json: E3 record
lg = load('films/swarm/la-belle-hortense/ledger.json')
lg['editor_E3'] = {
    'date': '2026-11-16',
    'commons_live_recheck': {'record': 'films/swarm/la-belle-hortense/review-2/commons_retry.txt',
                             'result': 'all 10 Commons items re-read live from the API on 2026-11-16 (review-2): licences and authors match the credits; closes the E2 gap "Commons licences were not re-read live"'},
    'typeface': 'Courier 10 Pitch and the DejaVu sigma removed from the film; all type is Hortense Slab (handmade, print.json TYPEFACE)',
    'new_handmade': ['TYPEFACE', 'KEY-OUTLINE', 'HOOK (recorded)', 'RIG-E3'],
    'fresh_reader': 'see reader-log.md',
}
save('films/swarm/la-belle-hortense/ledger.json', lg)

# ------------------------------------------------------------------ credits
c = load('films/credits/la-belle-hortense.json')
c = [x for x in c if not x['title'].startswith('Courier 10 Pitch') and not x['title'].startswith('DejaVu')]
for x in c:
    if x['title'].startswith('Bourré (Loir-et-Cher) (50866798791)') and 'V.4' not in x['used_as']:
        x['used_as'] += '; the V.4 grass close-up the key lands on (crop of this plate)'
    if x['source_url'].endswith('2017750547/') and 'I.4' not in x['used_as']:
        x['used_as'] = 'the visitor, back profile: I.4 (cut with an upper-arm and forearm hinge, mirrored; she lays the key on the coat), I.6 walking off, III.1 shadow-theatre turn'
    if x['source_url'].endswith('2017844115/') and 'II.2' not in x['used_as']:
        x['used_as'] += '; II.2: the same print undyed and narrowed as the conductor before he puts the coat on'
c.insert(len(c) - 1, dict(title='Hortense Slab (Bold and Regular), typeface', author='made for this film (editor unit, SCION swarm)',
                          license='Handmade for this work; CC BY-SA 4.0 with the film', license_url='https://creativecommons.org/licenses/by-sa/4.0/',
                          source_url='films/swarm/la-belle-hortense/editor/typeface.py', file_url='',
                          used_as='all type: title block, slot numerals, captions, glosses, slot lines, receipt, plate, tags, end card, sigma'))
save('films/credits/la-belle-hortense.json', c)
print('credits', len(c), '| scenes foraged', [f['id'] for f in ev['foraged']], '| print objects', [o['id'] for o in pj['objects']])
