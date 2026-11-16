"""Editor E2: finalise films/credits/la-belle-hortense.json and add E2 records to ledger.json (run once, idempotent)."""
import json
ROOT = '/home/user/bolas/paeleo/scion/oulipo'
CP = ROOT + '/films/credits/la-belle-hortense.json'
LP = ROOT + '/films/swarm/la-belle-hortense/ledger.json'
c = [r for r in json.load(open(CP)) if not r.get('e2')]
LIVE = " Re-verified live on www.loc.gov 2026-11-16 (rights advisory: No known restrictions)."
for r in c:
    if 'loc.gov' in r['source_url'] and 'Highsmith' not in r['author']:
        r['license'] = r['license'].split(' Re-verified')[0] + LIVE
    if 'Highsmith' in r['author']:
        r['license'] = r['license'].split(' Re-verified')[0] + " Re-verified live on www.loc.gov 2026-11-16."
    if r['title'].startswith('Book paper pages'):
        r['license_url'] = 'https://commons.wikimedia.org/wiki/File:Book_paper_pages_assorted.ogg'
    if r['title'].startswith('Chicago, Illinois. Conductor'):
        r['used_as'] += '; E2: the coat panel re-hung over the bench back (collar, sleeve, folded skirt) in I.1-I.6, VI.6; the sleeve and hand that lift it in II.2 and take the key in V.4'
    if r['title'].startswith('File:Skeletonkey'):
        r['used_as'] += '; E2: re-sampled at 205 px for I.3 (half out of the envelope) and the V.4 close-up; dangling in III.1'
new = [
    dict(title='[Stamped envelope addressed to Lieut Edwin T. Carrington] (back), 1861', author='Unknown (William A. Gladstone collection, Library of Congress)',
         license='No known restrictions on publication (LoC rights advisory; 1861, public domain by age). Checked live 2026-11-16.',
         license_url='https://www.loc.gov/item/2010652109/', source_url='https://www.loc.gov/item/2010652109/',
         file_url='https://tile.loc.gov/storage-services/service/pnp/ppmsca/11300/11331v.jpg',
         used_as='I.3: the envelope (back, flap side), cut out with GrabCut, the key sliding out of its top edge; two library pencil marks on the lower edge inpainted', e2=True),
    dict(title='Courier 10 Pitch (Bold and Regular)', author='Bitstream Inc. (contributed to the X Consortium)',
         license='X Consortium / Bitstream free licence (as distributed with X11 Type1 fonts)', license_url='https://metadata.ftp-master.debian.org/changelogs/main/x/xfonts-scalable/',
         source_url='/usr/share/fonts/X11/Type1/c0583bt_.pfb, c0419bt_.pfb', file_url='',
         used_as='all type: title, slot numerals, captions, glosses, slot lines, receipt, plate, tags, end card', e2=True),
    dict(title='DejaVu Sans Mono Bold (glyph σ only)', author='DejaVu fonts team, after Bitstream Vera',
         license='Bitstream Vera licence with DejaVu public-domain changes', license_url='https://dejavu-fonts.github.io/License.html',
         source_url='DejaVuSansMono-Bold.ttf (system font)', file_url='', used_as='the single glyph σ on the end card (Courier 10 Pitch has none)', e2=True),
    dict(title='La belle Hortense (this film)', author='SCION oulipo swarm',
         license='CC BY-SA 4.0 (the film synchronises CC BY-SA 3.0/4.0 recordings, so it is shared alike)',
         license_url='https://creativecommons.org/licenses/by-sa/4.0/', source_url='', file_url='',
         used_as='licence of the film itself; stated on the end card. Fiction re-staging archive photographs; hommage to the novel by Jacques Roubaud (1985), nothing taken from the novel or its cover', e2=True),
]
json.dump(c + new, open(CP, 'w'), ensure_ascii=False, indent=1)
L = json.load(open(LP))
L['editor_E2'] = dict(
    evidence=[dict(id='ENVELOPE-LOC', source_url='https://www.loc.gov/item/2010652109/', file='films/sources/la-belle-hortense/editor/forage/loc_11331v.jpg',
                   licence='No known restrictions (LoC), 1861', record='films/sources/la-belle-hortense/editor/forage/loc_2010652109.json',
                   replaces='print.json ENVELOPE (U4 handmade polygon envelope) on screen in I.3')],
    live_reverification={k: 'www.loc.gov/item/%s/ fetched 2026-11-16: No known restrictions' % k for k in ('2017844115', '2017750547', '2017750548', '2013633886')},
    live_records='films/sources/la-belle-hortense/editor/forage/live_loc_*.json',
    commons='Commons API returned HTTP 429 throughout this round (6 tries with back-off); Commons items keep the licences read by U2/U4 on 2026-11-16.',
    fresh_reader=dict(status='NOT RUN', reason='no naive human viewer is available to this unit; protocol in reader-protocol.md stands ready; fair play remains structurally verified only (verify.py S2: every support of S at or before 21.0 s)'),
    film_licence='CC BY-SA 4.0')
json.dump(L, open(LP, 'w'), ensure_ascii=False, indent=1)
print(len(c + new), 'credit records')
