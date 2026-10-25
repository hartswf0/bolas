"""Write the human-facing records from the lineage: assets.json (every asset: what, where from, rights, operations),
lineage/permissions.json (the permission decision record), lineage/schema.json (JSON schema of the lineage)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lineage import FOLDER, REPO, SCHEMA_VERSION


def chain(nodes, k):
    """the operation chain from a source to node k (longest parent path), as text."""
    out = []
    while nodes[k]['kind'] == 'derivative':
        n = nodes[k]
        out.append(n['op'])
        # follow the first image-like parent
        ps = [p for p in n['parents'] if nodes[p]['kind'] == 'derivative' or nodes[p].get('type') not in ('drawn', 'masks')]
        k = ps[0] if ps else n['parents'][0]
    return k, list(reversed(out))


def main():
    L = json.load(open(os.path.join(FOLDER, 'lineage', 'lineage.json')))
    nodes = L['nodes']; roots = L['roots']
    audit = {}
    ap = os.path.join(FOLDER, 'lineage', 'audit.json')
    if os.path.exists(ap):
        audit = json.load(open(ap))
    sources = []
    for k, n in sorted(nodes.items(), key=lambda kv: (kv[1].get('type', ''), kv[1].get('source_id') or kv[1].get('name', ''))):
        if n['kind'] != 'source':
            continue
        e = {'node': k, 'type': n['type'], 'sha256': n['sha256'], 'rights': n['rights'], 'tags': n['tags']}
        if n['type'] == 'drawn':
            e.update(what=n['name'], origin='drawn by SCION 54 (coordinates recorded in the node)', note=n.get('note'))
        else:
            e.update(what=n['title'], path=n['path'], source_id=n['source_id'], url=n['url'], credit=n.get('credit'))
        if n['type'] == 'strokes':
            e['key_ids'] = [d['key_id'] for d in (json.loads(l) for l in open(os.path.join(REPO, n['path'])))]
        sources.append(e)
    pieces = []
    def add(name, k, role):
        s, ops = chain(nodes, k)
        pieces.append({'asset': name, 'role': role, 'node': k, 'from_source': nodes[s].get('source_id') or nodes[s].get('name'), 'operations': ops,
                       'rights': nodes[k]['rights'], 'label': nodes[k].get('label')})
    for name, v in roots['dog'].items():
        add('dog ' + name, v['dusk'], 'puppet piece (dusk recolour); a lamp recolour of the same cut is blended in the light')
    for e in roots['cast']['turn']:
        add('dog turn frame f%03d' % e['f'], e['dusk'], 'substitution drawing for the two turns')
    for e in roots['cast']['door']:
        add('door f%03d' % e['f'], e['lit'], 'the door panel, one drawing of its swing')
    add('person torso', roots['cast']['torso']['node'], 'the person, cut from Straight Talk')
    add('person hand', roots['cast']['arm']['node'], 'the offered hand and forearm')
    add('lamp', roots['cast']['lamp']['lit'], 'the lamp in the room')
    add('beam', roots['cast']['beam'], 'the light that comes out (synthesised)')
    add('plate dusk', roots['plates']['dusk'], 'the set before the door opens')
    add('plate lit', roots['plates']['lit'], 'the set with the lamp light')
    json.dump({'about': 'Every asset of SCION 54 Provenance Graph. "sources" are immutable inputs with content hashes and rights; "pieces" are the '
                        'derivatives the film shows, with the operation chain that made each from its source. The full DAG is lineage/lineage.json.',
               'sources': sources, 'pieces': pieces,
               'not_used': 'No web images, no generated images, no commercial film, no recordings of sound. Everything else that appears is drawn '
                           '(coordinates in drawn nodes) or synthesised (recipes recorded as nodes).'}, open(os.path.join(FOLDER, 'assets.json'), 'w'), indent=1)
    # permission decision record
    dec = []
    for e in sources:
        r = e['rights']
        if r == 'public_domain':
            d = 'publish'; why = 'rights_statement public_domain in the kit / found-frames record (Internet Archive / NTIS / MSHA / NARA lineage)'
        elif r == 'CC-BY-4.0':
            d = 'publish with attribution'; why = 'Quick, Draw! dataset licence CC BY 4.0; credit carried on the end card and in assets.json; key_ids kept'
        elif r == 'OFL-1.1':
            d = 'publish'; why = 'open font licence, font files already in the repository (tools/paeleo/fonts)'
        elif r == 'self-made':
            d = 'publish'; why = 'made by this swarm in this build'
        else:
            d = 'BLOCK'; why = 'unknown is not permission'
        dec.append({'source': e.get('source_id') or e['what'], 'rights': r, 'decision': d, 'why': why, 'tags': e['tags']})
    blocked = [x for x in dec if x['decision'] == 'BLOCK']
    json.dump({'about': 'Permission decision record: one decision per source; any BLOCK stops publication of the film.',
               'publication': 'blocked' if blocked else 'allowed', 'decisions': dec,
               'considered_and_rejected': ['any image fetched from the web (not allowed by the brief)', 'model-generated images (none runnable here)',
                                           'recorded voices or sound effects (none with recorded rights in the kit; all sound is synthesised)']},
              open(os.path.join(FOLDER, 'lineage', 'permissions.json'), 'w'), indent=1)
    schema = {
        '$schema': 'https://json-schema.org/draft/2020-12/schema', '$id': 'paeleo/handmade/54-provenance-graph/lineage/schema.json', 'title': SCHEMA_VERSION,
        'type': 'object', 'required': ['schema', 'ops', 'nodes', 'roots'],
        'properties': {
            'schema': {'const': SCHEMA_VERSION},
            'ops': {'type': 'object', 'additionalProperties': {'type': 'object', 'required': ['version', 'doc']}},
            'roots': {'type': 'object', 'description': 'named entry points into the DAG used by the renderer (dog pieces, cast, plates)'},
            'nodes': {'type': 'object', 'additionalProperties': {'oneOf': [
                {'type': 'object', 'title': 'source', 'required': ['id', 'kind', 'type', 'sha256', 'rights', 'parents', 'tags'],
                 'properties': {'id': {'type': 'string', 'pattern': '^[sd]_[0-9a-f]{16}$'}, 'kind': {'const': 'source'},
                                'type': {'enum': ['frame', 'masks', 'strokes', 'drawn', 'font']}, 'sha256': {'type': 'string'},
                                'path': {'type': 'string'}, 'source_id': {'type': 'string', 'description': 'immutable source id: archive:clip:frame'},
                                'title': {'type': 'string'}, 'url': {'type': 'string'}, 'rights': {'enum': ['public_domain', 'CC-BY-4.0', 'OFL-1.1', 'self-made', 'unknown']},
                                'credit': {'type': ['string', 'null']}, 'data': {}, 'parents': {'type': 'array', 'maxItems': 0},
                                'tags': {'enum': ['documented', 'inferred']}}},
                {'type': 'object', 'title': 'derivative', 'required': ['id', 'kind', 'op', 'op_version', 'op_sig', 'parents', 'params', 'sha256', 'rights', 'tags'],
                 'properties': {'id': {'type': 'string', 'pattern': '^n_[0-9a-f]{16}$', 'description': 'content hash of the output'}, 'kind': {'const': 'derivative'},
                                'op': {'type': 'string'}, 'op_version': {'type': 'integer'}, 'op_sig': {'type': 'string', 'description': 'hash of op name, version and params'},
                                'parents': {'type': 'array', 'minItems': 1, 'items': {'type': 'string'}}, 'params': {'type': 'object'},
                                'sha256': {'type': 'string'}, 'rights': {'enum': ['public_domain', 'CC-BY-4.0', 'OFL-1.1', 'self-made', 'unknown']},
                                'tags': {'enum': ['documented', 'inferred']}, 'recipe': {'type': 'boolean'}, 'label': {'type': ['string', 'null']},
                                'size': {'type': ['array', 'null']}}}]}}},
        'x-render-deps': 'lineage/render_deps.jsonl.gz: one line per scene frame {i, sha256_rgb, layers:[{node, M (2x3 affine, node px -> screen px), op, role, src?} | {synth, params, role}]}',
        'x-time-base': 'scene frame i at 24 fps, t = i/24 s, aligned to score/threshold-score.json frame i; film frame = i + 72 (3 s title card)',
        'x-coordinates': 'world metres: x along the porch as in the score (threshold 0, inside negative), y up from the porch floor; camera per frame in render.camera(t)'}
    json.dump(schema, open(os.path.join(FOLDER, 'lineage', 'schema.json'), 'w'), indent=1)
    print('assets:', len(sources), 'sources,', len(pieces), 'pieces; publication', 'blocked' if blocked else 'allowed')


if __name__ == '__main__':
    main()
