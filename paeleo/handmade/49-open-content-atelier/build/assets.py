"""Rights and provenance adjudicator: write ../assets.json — every object used, its record, licence statement as the
museum gives it, the media URL fetched, and every part cut from it with crop coordinates and operations.
Also lists objects fetched and reviewed but not used, the hosts that were refused, and the non-image assets."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..')
parts = json.load(open(os.path.join(HERE, 'cache', 'parts', 'parts.json')))
recs = {}
for fn in ('records_fetched.jsonl',):
    for l in open(os.path.join(ROOT, 'sources', 'meta', fn)):
        d = json.loads(l)
        for m in d['content']['descriptiveNonRepeating'].get('online_media', {}).get('media', []):
            recs[m.get('idsId')] = (d, m)
dl = {}
for l in open(os.path.join(ROOT, 'sources', 'downloads.jsonl')):
    r = json.loads(l); dl[r['idsId']] = r

def ft(d, key, label=None):
    for x in d['content'].get('freetext', {}).get(key, []):
        if label is None or x.get('label') == label: return x.get('content')
    return None

def obj(ids):
    d, m = recs[ids]; dn = d['content']['descriptiveNonRepeating']
    return {'idsId': ids, 'title': d['title'], 'artist': ft(d, 'name'), 'date': ft(d, 'date'),
            'medium': ft(d, 'physicalDescription', 'Medium'), 'object_number': ft(d, 'identifier', 'Object number'),
            'museum': dn.get('data_source'), 'unit_code': dn.get('unit_code'), 'record_ID': dn.get('record_ID'),
            'record_url': dn.get('record_link'), 'item_uri': dn.get('guid'), 'media_uri': m.get('guid'),
            'ids_media_url': m.get('content'), 'credit_line': ft(d, 'creditLine'),
            'licence': {'metadata_usage.access': dn.get('metadata_usage', {}).get('access'),
                        'online_media.usage.access': m.get('usage', {}).get('access'),
                        'objectRights': ft(d, 'objectRights'),
                        'statement': 'Smithsonian Open Access: the museum marks this record and this image CC0 (no rights reserved).'},
            'fetched_from': dl.get(ids, {}).get('url'), 'bytes_downloaded': dl.get(ids, {}).get('bytes'),
            'original_px': dl.get(ids, {}).get('orig_size'), 'kept_copy': f'sources/media/{ids}.jpg',
            'kept_copy_scale': dl.get(ids, {}).get('kept_scale'), 'parts': []}

ROLES = {'w_': 'the dog (standing, walking, turning)', 'j_': 'the dog (lying, resting, looking in)', 'o_': 'the dog (head looking back / mid-turn)',
         'm_': 'the person', 'b_': 'the person (reaching / offered arm)'}
OPS = {'dog': 'polygon cut + colour key (keep cream fur and liver patches; drop green/blue/dark ground) + closing + small-hole fill',
       'juno': 'polygon cut + colour key (drop dark green-grey ground only) + hole fill',
       'dark': 'polygon cut + threshold key on black paper (cut silhouette)', 'none': 'polygon cut (scissors line is the polygon)'}
used = {}
for name, p in parts.items():
    ids = p['src']; used.setdefault(ids, obj(ids))
    rec = {'part': name, 'role': p['role'], 'crop_box_in_kept_copy_px': p['bbox_in_source'],
           'crop_box_in_original_px': [round(v / (used[ids]['kept_copy_scale'] or 1)) for v in p['bbox_in_source']],
           'operation': 'rectangular crop (plate)' if p['role'] == 'plate' else OPS[p['key']]}
    if 'polygon_in_source' in p: rec['polygon_in_kept_copy_px'] = p['polygon_in_source']
    if 'pivots' in p and p['pivots']: rec['pivots_in_part_px'] = p['pivots']
    rec['cache_files'] = [f'build/cache/parts/{name}.jpg'] + ([f'build/cache/parts/{name}_a.jpg'] if p['role'] != 'plate' else [])
    used[ids]['parts'].append(rec)
STAGE = {
    'w_head': 'rotated at the neck (head 0 down .. 1 up), lowered for the approach, chin to the paws for rest; mirrored about the neck to look back over the shoulder at 7.46 s; narrowed as it turns away at 26.4 s',
    'w_torso': 'translated along x by the score, pitched, lowered to the floor to lie (haunches first), mirrored + foreshortened (>=0.62) through the turns',
    'w_tail': 'rotated at the root (score tail + wag)', 'w_fore': 'near and far (darkened copy) forelegs: rotated + stretched (0.82-1.12) to a planted foot target',
    'w_thigh': 'two-bone IK with w_shank: hip -> hock -> paw; feet planted by distance travelled (no sliding)',
    'w_shank': 'two-bone IK with w_thigh', 'j_body': 'substituted for the standing cut when the dog lies (refusal 4.0-7.8 s; sill 23.8 s on); mirrored to face the door at the end',
    'j_head': 'rotated/lowered for rest; moved about 11 cm forward (nose 14 cm inside the inner wall face), level, warmed by the room light with a rim, for the look in (26.4 s)',
    'o_head': 'the head that leads at 7.46 s (looks back over the shoulder at the door) and the three-quarter head mid-turn',
    'm_upper': 'person torso: leans for calls, lowered when sitting', 'm_thigh': 'rotated to sit', 'm_shin': 'hung at the knee',
    'b_arm': 'mirrored, rotated from hanging to reaching (3.4 s) and to offered low (6.8 s on)',
    'door': 'hinged at the outer wall face, opening outward; drawn at width W sin(angle)',
    'bench': 'the seat the person backs onto', 'room': 'room backdrop (warm, brighter when the door opens)',
    'dusk': 'the sky and trees beyond the porch (cooled)', 'floor': 'interior floor, threshold and porch boards (strips)',
    'jamb': 'wall in section above the lintel, and the lintel', 'reveal': 'seen through the doorway: the lit inner room',
}
for o in used.values():
    for p in o['parts']: p['stage_operation'] = STAGE.get(p['part'], '')

reviewed = []
for ids, r in dl.items():
    if ids in used: continue
    d, m = recs[ids]
    reviewed.append({'idsId': ids, 'title': d['title'], 'artist': ft(d, 'name'), 'object_number': ft(d, 'identifier', 'Object number'),
                     'record_url': d['content']['descriptiveNonRepeating'].get('record_link'),
                     'licence': m.get('usage', {}).get('access'), 'metadata_licence': d['content']['descriptiveNonRepeating'].get('metadata_usage', {}).get('access'),
                     'bytes_downloaded': r['bytes'], 'kept_copy': f'sources/media/{ids}.jpg (reduced to 800 px review copy)'})
total = sum(r['bytes'] for r in dl.values())
out = {
    'about': 'PAE-02 · SCION 49 · Open-Content Atelier. Image asset registry and per-item rights manifest. Every visible picture '
             'element in the film is cut from one of the objects below; nothing is drawn by hand. Only the light (warm wedge, dusk '
             'grade, a rim on the head in the room light) and the title/end cards are computed.',
    'source_distribution': {'name': 'Smithsonian Open Access (official S3 open-data distribution of EDAN records and media)',
                            'bucket': 'https://smithsonian-open-access.s3-us-west-2.amazonaws.com/',
                            'metadata': 'metadata/edan/saam/*.txt (line-delimited EDAN JSON), streamed and filtered by build/fetch_meta.py, fetch_grep.py',
                            'media': 'media/saam/<idsId>.jpg, fetched by build/fetch_media.py only after checking both metadata_usage.access and online_media.usage.access == CC0',
                            'kept_records': ['sources/meta/records_fetched.jsonl (full EDAN record of every fetched object)',
                                             'sources/meta/candidates.tsv (index of 1,819 CC0-with-media SAAM records found by the dog/door/porch/seated, Muybridge and silhouette/Currier searches)'],
                            'download_log': 'sources/downloads.jsonl', 'total_media_bytes_downloaded': total,
                            'note': 'metadata streamed: SAAM 256 shards read in full twice (~2 x 52 MB transferred, only matching rows kept)'},
    'refused_or_unreachable': {'hosts': ['api.si.edu', 'collections.si.edu', 'ids.si.edu', 'data.getty.edu', 'www.getty.edu', 'media.getty.edu',
                                         'api.artic.edu', 'upload.wikimedia.org', 'commons.wikimedia.org', 'archive.org', 'images.metmuseum.org'],
                               'how': 'CONNECT refused (403) by the session proxy on 2026-10-30; the Smithsonian S3 open-data bucket was reachable',
                               'consequence': 'No Getty Open Content object is used. The swarm name keeps the Getty; the film does not.'},
    'objects_used': list(used.values()),
    'objects_fetched_reviewed_not_used': reviewed,
    'non_image_assets': [
        {'what': 'speech', 'source': "ffmpeg lavfi 'flite' filter (CMU Flite, voice 'rms'); lines: Come here! / Come here! Come on! / It's all right. (x2) / Come in.",
         'rights': 'synthesized here; Flite is free software (BSD-like licence)', 'operation': 'tempo, low-pass for the soft lines, gain'},
        {'what': 'all other sound', 'source': 'build/sound.py (numpy/scipy synthesis: room tone, crickets, clock, fire, door, steps, paw clicks at gait foot plants, thumps, sigh)',
         'rights': 'made here'},
        {'what': 'fonts (cards only)', 'source': 'tools/paeleo/fonts (Big Shoulders Display, Literata, JetBrains Mono)', 'rights': 'SIL Open Font License'}],
}
json.dump(out, open(os.path.join(ROOT, 'assets.json'), 'w'), indent=1, ensure_ascii=False)
print('objects used', len(used), 'reviewed not used', len(reviewed), 'MB', round(total / 1e6, 1))
