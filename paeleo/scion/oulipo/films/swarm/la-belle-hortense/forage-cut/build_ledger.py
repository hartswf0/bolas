"""Write swarm/la-belle-hortense/ledger.json and the draft films/credits/la-belle-hortense.json."""
import json
F = '/home/user/bolas/paeleo/scion/oulipo/films/'
S = 'films/sources/la-belle-hortense/'
FR = S + 'forage/raw/'
FS = S + 'forage/sound/'
ED = S + 'forage-cut-forager-licence-verifier-grabcut-cutter-scion-29-/'
CM = 'Commons extmetadata LicenseShortName/Artist read via API 2026-11-16 (saved: ' + S + 'forage/commons_extmetadata_2026-11-16.json)'
FSA = 'https://www.loc.gov/rr/print/res/071_fsab.html'

items = [
 dict(id='COND', title='Chicago, Illinois. Conductor checking his time in the telegraphers office at Union Station (1943)',
      author='Jack Delano (1914-1997), photographer; U.S. Office of War Information (FSA/OWI)',
      license='Public domain (US government work, FSA/OWI). LoC rights advisory: No known restrictions',
      license_url=FSA, source_url='https://www.loc.gov/item/2017844115/',
      file_url='https://tile.loc.gov/storage-services/master/pnp/fsa/8d13000/8d13100/8d13125u.tif (master, as recorded in credits/la-machine-a-tuer-le-temps.json; local 791x1024 derivative copied from disk)',
      local_path=FR + 'loc_2017844115.jpg', what_it_shows='A conductor in a long dark overcoat and cap, holding a watch, newspaper in pocket; standing/walking in a station office',
      verified_date_or_place='2026-11-16 from the on-disk LoC item JSON (' + FR + 'loc_2017844115.json, copied from la-machine-a-tuer-le-temps/registrar): rights_advisory "No known restrictions", rights "in the public domain and are free to use and reuse"; live www.loc.gov re-fetch timed out',
      used_as='the conductor: GrabCut rig pieces coat_panel / coat_upper + skirtN + skirtF, head_cap, arm, newspaper, thighN/F, shinN/F (cut/conductor); coat stencil-dyed red #e2011b'),
 dict(id='VISITOR', title='[Untitled photo, possibly related to: Old woman and Pekingese walking along a street in Saint Albans, Vermont] (1941 Sept.)',
      author='Jack Delano (1914-1997), photographer; U.S. Farm Security Administration/Office of War Information',
      license='Public domain (US government work, FSA/OWI). LoC rights advisory: No known restrictions', license_url=FSA,
      source_url='https://www.loc.gov/item/2017750547/',
      file_url='https://tile.loc.gov/storage-services/service/pnp/fsa/8a36000/8a36800/8a36813v.jpg',
      local_path=FR + 'loc_8a36813v.jpg', what_it_shows='An older woman in a print dress and dark hat walking away from camera on a sidewalk, shins and shoes visible, leading a dog on a leash',
      verified_date_or_place='2026-11-16 from the LoC item JSON fetched by the animator unit 17:26 (' + FR + 'loc_2017750547.json): rights_advisory "No known restrictions", contributor Delano, Jack; file md5 identical to animator/dl copy; IIIF tile service serves only the 1024 px derivative',
      used_as='the visitor: cut/visitor body (hat+dress), forearm (carries the envelope), shinL, shinR hinged at the hem; dog and leash excluded. NOT in a coat (no coat walker found, see absences)'),
 dict(id='SHED-DOOR', title='Bourré (Loir-et-Cher) (50866795131).jpg', author='Daniel Jolivet', license='CC BY 2.0',
      license_url='https://creativecommons.org/licenses/by/2.0', source_url='https://commons.wikimedia.org/wiki/File:Bourr%C3%A9_(Loir-et-Cher)_(50866795131).jpg',
      file_url='https://upload.wikimedia.org/wikipedia/commons/e/e4/Bourr%C3%A9_%28Loir-et-Cher%29_%2850866795131%29.jpg',
      local_path=FR + 'bourre_50866795131.jpg', what_it_shows='Goods shed with red/white brick quoins and a shut plank door, platform edge, grass, overcast sky',
      verified_date_or_place=CM, used_as='shed / door plate; door leaf cut (cut/door/leaf.png, hinge on the left jamb); dye masks green/brick'),
 dict(id='SHED-MEADOW', title='Bourré (Loir-et-Cher) (50866798791).jpg', author='Daniel Jolivet', license='CC BY 2.0',
      license_url='https://creativecommons.org/licenses/by/2.0', source_url='https://commons.wikimedia.org/wiki/File:Bourr%C3%A9_(Loir-et-Cher)_(50866798791).jpg',
      file_url='https://upload.wikimedia.org/wikipedia/commons/8/88/Bourr%C3%A9_%28Loir-et-Cher%29_%2850866798791%29.jpg',
      local_path=FR + 'bourre_50866798791.jpg', what_it_shows='The goods shed seen across a meadow; long grass foreground',
      verified_date_or_place=CM, used_as='multiplane planes (far / mid grass / near grass) and the pan-exposure streak ground'),
 dict(id='STATION', title='Bourré (Loir-et-Cher) (50866891867).jpg', author='Daniel Jolivet', license='CC BY 2.0',
      license_url='https://creativecommons.org/licenses/by/2.0', source_url='https://commons.wikimedia.org/wiki/File:Bourr%C3%A9_(Loir-et-Cher)_(50866891867).jpg',
      file_url='https://upload.wikimedia.org/wikipedia/commons/6/69/Bourr%C3%A9_%28Loir-et-Cher%29_%2850866891867%29.jpg',
      local_path=FR + 'bourre_50866891867.jpg', what_it_shows='The station house with the BOURRÉ sign (portrait frame)',
      verified_date_or_place=CM, used_as='station plate for module I (and colour-fill source for the top band: real trees/roof instead of grey sky)'),
 dict(id='BENCH', title='Park bench in Sacramento, the capital city of the U.S. state of California and the county seat of Sacramento County (2012)',
      author='Carol M. Highsmith', license='Public domain (Carol M. Highsmith Archive, Library of Congress; rights advisory: No known restrictions on publication)',
      license_url='https://www.loc.gov/rr/print/res/482_high.html', source_url='https://www.loc.gov/item/2013633886/',
      file_url='https://tile.loc.gov/image-services/iiif/service:pnp:highsm:23400:23429/full/pct:25/0/default.jpg',
      local_path=FR + 'highsmith_bench_sac_23429.jpg', what_it_shows='A slatted park bench with cast-iron ends on autumn leaves under trees',
      verified_date_or_place='2026-11-16 from the earlier rights record in credits/les-lieux-dune-fugue.json (LoC item rights_advisory quoted there); file copied from sources/les-lieux-dune-fugue/r2/bench/sac_23429.jpg; live LoC JSON re-fetch timed out',
      used_as='the bench (cut/bench/bench.png): colour-key + GrabCut, gaps between slats kept'),
 dict(id='BELL', title='File:Bahnhofsglocke HLB 1.jpg (2009-04-25)', author='Reinhard Dietrich', license='Public domain',
      license_url='https://commons.wikimedia.org/wiki/File:Bahnhofsglocke_HLB_1.jpg (PD release on the file page)',
      source_url='https://commons.wikimedia.org/wiki/File:Bahnhofsglocke_HLB_1.jpg',
      file_url='https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Bahnhofsglocke_HLB_1.jpg/960px-Bahnhofsglocke_HLB_1.jpg',
      local_path=FR + 'commons_Bahnhofsglocke_HLB_1_960px.jpg', what_it_shows='A bronze station bell of the Hessische Ludwigsbahn hung from an iron yoke between two concrete posts; clapper visible',
      verified_date_or_place='Commons extmetadata LicenseShortName=Public domain, Artist=Reinhard Dietrich, read 2026-11-16 (' + S + 'forage/commons_extmetadata_bell_2026-11-16.json)',
      used_as='the bell: cut/bell yoke (fixed), body (pendulum), clapper (child pendulum). On a post bracket, not a wall bracket'),
 dict(id='KEY', title='File:Skeletonkey.png', author='Blenheimears', license='CC0', license_url='http://creativecommons.org/publicdomain/zero/1.0/deed.en',
      source_url='https://commons.wikimedia.org/wiki/File:Skeletonkey.png', file_url='https://upload.wikimedia.org/wikipedia/commons/2/21/Skeletonkey.png',
      local_path=FR + 'skeletonkey.png', what_it_shows='Two flat pin-tumbler keys scanned on white (not a skeleton key despite the name)',
      verified_date_or_place=CM, used_as='the key (left key, cut/key/key.png, bow hole kept), dyed brass #c9a23a'),
 dict(id='BELL-SND', title='Glockenschlagwerk Bahnhof Fridingen.ogg', author='Olga Ernst', license='CC BY-SA 4.0',
      license_url='https://creativecommons.org/licenses/by-sa/4.0', source_url='https://commons.wikimedia.org/wiki/File:Glockenschlagwerk_Bahnhof_Fridingen.ogg',
      file_url='https://upload.wikimedia.org/wikipedia/commons/f/fa/Glockenschlagwerk_Bahnhof_Fridingen.ogg',
      local_path=FS + 'Glockenschlagwerk_Bahnhof_Fridingen.ogg.mp3 (decode: ' + ED + 'sound/Glockenschlagwerk_Bahnhof_Fridingen.wav)',
      what_it_shows='Station bell striking mechanism, 14 strikes (onsets 0.02, 0.70, 1.34, 2.08, 2.98, 3.82, 4.76, 5.76, 6.96, 8.12, 9.34, 10.58, 11.60, 12.92 s)',
      verified_date_or_place=CM, used_as='bell strikes in each cloche slot; grains: Fridingen_last_strike_12.90s_free_decay.wav, Fridingen_strike_4.74s_1.0s.wav'),
 dict(id='STEPS', title='Concrete Steps 2.ogg', author='Pwaivers', license='CC BY-SA 3.0', license_url='https://creativecommons.org/licenses/by-sa/3.0',
      source_url='https://commons.wikimedia.org/wiki/File:Concrete_Steps_2.ogg', file_url='https://upload.wikimedia.org/wikipedia/commons/b/bf/Concrete_Steps_2.ogg',
      local_path=FS + 'Concrete_Steps_2.ogg (wav: ' + ED + 'sound/Concrete_Steps_2.wav)', what_it_shows='Two footsteps on concrete',
      verified_date_or_place=CM, used_as='footsteps (walk and run, cut as grains)'),
 dict(id='HANDLE', title='Door handle creaking.ogg', author='stephan', license='Public domain', license_url='https://commons.wikimedia.org/wiki/File:Door_handle_creaking.ogg',
      source_url='https://commons.wikimedia.org/wiki/File:Door_handle_creaking.ogg', file_url='https://upload.wikimedia.org/wikipedia/commons/7/74/Door_handle_creaking.ogg',
      local_path=FS + 'Door_handle_creaking.ogg (wav: ' + ED + 'sound/Door_handle_creaking.wav)', what_it_shows='A door handle being worked, creaking',
      verified_date_or_place=CM, used_as='locked-door rattle (II.1, III.2, IV.4)'),
 dict(id='HINGE', title='Squeaky door hinge.ogg', author='MKFI', license='Public domain', license_url='https://commons.wikimedia.org/wiki/File:Squeaky_door_hinge.ogg',
      source_url='https://commons.wikimedia.org/wiki/File:Squeaky_door_hinge.ogg', file_url='https://upload.wikimedia.org/wikipedia/commons/6/6a/Squeaky_door_hinge.ogg',
      local_path=FS + 'Squeaky_door_hinge.ogg (wav: ' + ED + 'sound/Squeaky_door_hinge.wav)', what_it_shows='A door swinging on a squeaky hinge',
      verified_date_or_place=CM, used_as='the door opening (V.5)'),
 dict(id='KEYS-SND', title='Keys hitting tree 2 (Gravity Sound).wav', author='Gravity Sound', license='CC BY 4.0', license_url='https://creativecommons.org/licenses/by/4.0',
      source_url='https://commons.wikimedia.org/wiki/File:Keys_hitting_tree_2_(Gravity_Sound).wav',
      file_url='https://upload.wikimedia.org/wikipedia/commons/c/c8/Keys_hitting_tree_2_%28Gravity_Sound%29.wav',
      local_path=FS + 'Keys_hitting_tree_2_(Gravity_Sound).wav.mp3 (wav: ' + ED + 'sound/Keys_hitting_tree_2__Gravity_Sound_.wav)',
      what_it_shows='Keys striking wood', verified_date_or_place=CM, used_as='key tinks (I.4 key on coat, V.4 landing, VI.5)'),
 dict(id='LOCK', title='342706 spacejoe lock-3-open-lock-3.wav', author='SpaceJoe', license='CC0', license_url='http://creativecommons.org/publicdomain/zero/1.0/deed.en',
      source_url='https://commons.wikimedia.org/wiki/File:342706_spacejoe_lock-3-open-lock-3.wav',
      file_url='https://upload.wikimedia.org/wikipedia/commons/a/a7/342706_spacejoe_lock-3-open-lock-3.wav',
      local_path=FS + 'spacejoe_lock-3-open.wav (mono 48k: ' + ED + 'sound/spacejoe_lock-3-open.wav)', what_it_shows='A lock being opened (key turn and latch)',
      verified_date_or_place=CM + '; downloaded 2026-11-16 (94 KB)', used_as='key in the lock, latch (V.5)'),
 dict(id='MIA-BELFRY', title='Communications and Our Town (1947)', author='via movingimagearchive.com',
      license='Rights as listed by movingimagearchive.com (largely public domain); not independently verified', license_url='',
      source_url='https://www.movingimagearchive.com/sources/communications-and-our-town-e75e0b4f?clip=381d177e-aa67-5119-9f0a-eca87325fd86',
      file_url='', local_path=ED + 'mia_381d177e_belfry_4.4-10.8.mp4, mia_381d177e_belfry_bells.wav, mia_381d177e_belfry_7.0.png (cache clip 381d177e, source film 333.1-355.4 s; trimmed 4.4-10.8 s of the clip)',
      what_it_shows='B&W church belfry and spire against sky, with a town bell ringing on the source track (partials ~456/760 Hz); clip continues with an alarm clock and a whistle/steam',
      verified_date_or_place='allways-forage index.json entry (title, year, page) read 2026-11-16; viewed frames and analysed audio; no copyright marking on title/page entry',
      used_as='optional: distant bell bed under the title (0.4 s) or VI; the belfry picture is not in the plan'),
 dict(id='FONT', title='Courier 10 Pitch Bold / Regular (c0583bt_.pfb, c0419bt_.pfb)', author='Bitstream',
      license='Bitstream donation to the X Consortium (free licence, X11 Type1 fonts)', license_url='', source_url='/usr/share/fonts/X11/Type1/',
      file_url='', local_path='/usr/share/fonts/X11/Type1/c0583bt_.pfb', what_it_shows='slab typewriter face', verified_date_or_place='system font, licence as recorded for the test shot', used_as='all type'),
]

handmade = [
 dict(id='CUTS', what='SCION 29 GrabCut cutouts with failure masks, QA sheets and per-figure manifests: conductor (8 pieces + run-variant coat_upper/skirtN/skirtF + coat/arm/flap dye masks), visitor (4), bell (3), key, bench, door leaf',
      where=S + 'forage/cut/<figure>/ ; scripts swarm/la-belle-hortense/forage-cut/{gcut,cut_conductor,cut_props}.py'),
 dict(id='RIG', what='joint graph: parents, pivots (crop + piece px), angle limits, dye masks', where='films/swarm/la-belle-hortense/rig.json (build_rig.py)'),
 dict(id='SCISSOR', what='hand-placed scissor polygons: conductor right-arm/counter fringe and coat flap seed; bench cast-iron strokes (armrest, front legs, strut); visitor dog/leash exclusion', where='cut_conductor.py, cut_props.py'),
]

absences = [
 'LoC search (www.loc.gov/photos/?q=...&fo=json) for a woman in a COAT walking with legs visible, handbag/letter: www.loc.gov timed out from this unit for most of the session (30-40 s timeouts at 17:20 and 17:45); only tile.loc.gov answered. The visitor is therefore the Delano 1941 St Albans walker (print dress, not a coat) already fetched by the animator unit. Gap: no coat, no handbag/letter in hand (the envelope must be attached as a prop at the forearm hand pivot).',
 'Commons searches "woman walking coat FSA Office of War Information", "filetype:bitmap woman walking coat 1942 loc.gov fsa", "Bubley woman walking", "woman walking street 1940s public domain coat handbag": returned nothing usable or were rate-limited (HTTP 429) before completing. Only hit: File:SailorWomanCanalStrNOLA1943.jpg (John Vachon 1943, Public domain; woman and sailor walking away) - thumbnail download got 429, not inspected, not used.',
 'A different PD photograph of a figure RUNNING (to replace the walking conductor): Commons "man running 1940s Office of War Information", "Muybridge running man clothed", "man running catch train", "boy running street 1940s Farm Security": no usable PD result (rate-limited / irrelevant hits). MIA cache forage.py "running|runs|runner|hurr|woman walking|walking away": no clip with a legible running figure (hits: crowd on stairs, firefighters, fog walker). Instead the conductor rig gains a knee per leg and a run variant whose coat skirt is split into two flaps hinged at the hip (skirtN/skirtF follow the thighs) so the stride shows in the coat.',
 'A station bell on a WALL bracket: Commons "Bahnhofsglocke", "Läutewerk Bahnhof" give museum bells (CC BY-SA) and Läutewerk posts; the best PD hit (Bahnhofsglocke HLB 1, Reinhard Dietrich) hangs between two posts. Used; the yoke can be pinned to the station wall plate. File:Glocke HLB 2.jpg (PD, same author) thumbnail got 429, not inspected.',
 'PD envelope photograph: not searched (rate limits); the envelope is left to print-sound as a handmade object, as the plan allows.',
 'Live re-verification of LoC 2017844115 and 2013633886: www.loc.gov timed out; on-disk LoC JSON / earlier credit records used (stated per item).',
]

ledger = {'unit': 'U2 forage-cut (FORAGER + LICENCE VERIFIER + GRABCUT CUTTER, SCION 29)', 'verified': '2026-11-16',
          'downloads_this_unit_bytes_approx': 600000, 'items': items, 'handmade': handmade, 'absences': absences,
          'editor_media': ED}
json.dump(ledger, open(F + 'swarm/la-belle-hortense/ledger.json', 'w'), indent=1, ensure_ascii=False)
cred = [{k: it[k] for k in ('title', 'author', 'license', 'license_url', 'source_url', 'file_url', 'used_as')} for it in items if it['id'] != 'FONT']
json.dump(cred, open(F + 'credits/la-belle-hortense.json', 'w'), indent=1, ensure_ascii=False)
print(len(items), 'items;', len(cred), 'credits')
