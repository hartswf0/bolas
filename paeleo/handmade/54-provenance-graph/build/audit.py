"""The audit: can every image in the film answer where it came from and how it changed?
  A1 lineage     every derivative has parents that exist; every chain ends in a source with a content hash that matches its file
  A2 rebuild     every derivative is re-executed from its recorded parents, op and params (from the source files, not the cache)
                 and must reproduce its content hash
  A3 rights      every node has a rights state; 'unknown' anywhere blocks publication; CC BY sources carry a credit
  A4 render deps every layer of every frame names a node in the lineage or a recorded synthesised op; no orphan layers
  A5 rebuilt shot sample frames are recomposed solely from render_deps + lineage and must match the recorded frame hash
  A6 tags        documented vs inferred tags are present on every node
Writes lineage/audit.json. Exit code 1 if anything fails."""
import gzip, hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lineage import Graph, FOLDER, REPO, sha, img_bytes, combine_rights
import ops

SYNTH_OPS = {'draw', 'text', 'rail'}


def main(sample=(0, 85, 100, 182, 300, 456, 580, 660, 767)):
    L = json.load(open(os.path.join(FOLDER, 'lineage', 'lineage.json')))
    nodes = L['nodes']
    res = {}
    # A1
    bad = []
    for k, n in nodes.items():
        for p in n['parents']:
            if p not in nodes:
                bad.append((k, 'missing parent ' + p))
        if n['kind'] == 'derivative' and not n['parents']:
            bad.append((k, 'derivative without parent'))
        if n['kind'] == 'source' and n.get('path'):
            h = sha(open(os.path.join(REPO, n['path']), 'rb').read())
            if h != n['sha256']:
                bad.append((k, 'source hash mismatch'))
    res['A1_lineage'] = {'ok': not bad, 'nodes': len(nodes), 'sources': sum(1 for n in nodes.values() if n['kind'] == 'source'), 'problems': bad[:20]}
    # A2: re-execute from sources
    G = Graph(); ops.register_all(G); ops.register_world(G); ops.register_more(G)
    import world as Wd
    import ops as O
    G.register('qd_strokes', 1, lambda dr, key_id, size, width, color: O.op_strokes(next(d for d in dr if d['key_id'] == key_id), size, width, color), '')
    G.register('draw_alpha', 1, lambda pd, size: O.poly_alpha(tuple(size), pd['polys'], 4, 0.6), '')
    memo = {}
    from PIL import Image
    import io

    def value(k):
        if k in memo:
            return memo[k]
        n = nodes[k]
        if n['kind'] == 'source':
            if n['type'] == 'drawn':
                v = n['data']
            else:
                raw = open(os.path.join(REPO, n['path']), 'rb').read()
                p = n['path']
                if p.endswith(('.jpg', '.png')):
                    v = Image.open(io.BytesIO(raw)).convert('RGB')
                elif p.endswith('.ndjson'):
                    v = [json.loads(l) for l in raw.decode().splitlines() if l.strip()]
                elif p.endswith('.json'):
                    v = json.loads(raw)
                else:
                    v = raw
        else:
            fn = G.ops[n['op']]['fn']
            ins = [] if n.get('recipe') else [value(p) for p in n['parents']]
            v = fn(*ins, **n['params'])
        memo[k] = v
        return v
    mism = []
    nder = 0
    for k, n in nodes.items():
        if n['kind'] != 'derivative':
            continue
        nder += 1
        v = value(k)
        b = img_bytes(v) if isinstance(v, Image.Image) else json.dumps(v, sort_keys=True).encode()
        if sha(b) != n['sha256']:
            mism.append(k)
    res['A2_rebuild'] = {'ok': not mism, 'derivatives_reexecuted': nder, 'mismatched': mism[:20]}
    # A3 rights
    unknown = [k for k, n in nodes.items() if n.get('rights') in (None, 'unknown')]
    wrong = [k for k, n in nodes.items() if n['kind'] == 'derivative' and n['rights'] != combine_rights(nodes[p]['rights'] for p in n['parents'])]
    ccby = [n for n in nodes.values() if n['kind'] == 'source' and n['rights'] == 'CC-BY-4.0']
    res['A3_rights'] = {'ok': not unknown and not wrong and all(n.get('credit') for n in ccby), 'unknown_blocks': unknown, 'misderived': wrong[:10],
                        'by_rights': {r: sum(1 for n in nodes.values() if n['rights'] == r) for r in set(n['rights'] for n in nodes.values())},
                        'credits': sorted(set(n['credit'] for n in ccby))}
    # A4 render deps
    deps = [json.loads(l) for l in gzip.open(os.path.join(FOLDER, 'lineage', 'render_deps.jsonl.gz'), 'rt')]
    orphans = []; used = set(); nl = 0
    for d in deps:
        for l in d['layers']:
            nl += 1
            if 'node' in l:
                if l['node'] not in nodes:
                    orphans.append((d['i'], l['node']))
                else:
                    used.add(l['node'])
            elif l.get('synth') not in SYNTH_OPS:
                orphans.append((d['i'], l.get('synth')))
    reach = set()
    for k in used:
        st = [k]
        while st:
            q = st.pop()
            if q in reach:
                continue
            reach.add(q); st.extend(nodes[q]['parents'])
    srcs_used = sorted({nodes[k].get('source_id') or nodes[k].get('name') for k in reach if nodes[k]['kind'] == 'source'})
    res['A4_render_deps'] = {'ok': not orphans, 'frames': len(deps), 'layers': nl, 'orphan_layers': orphans[:10], 'nodes_used_directly': len(used),
                             'nodes_in_ancestry': len(reach), 'nodes_unused': len(nodes) - len(reach), 'sources_reached': len(srcs_used)}
    # A5 rebuilt shot: recompose sample frames from deps alone, with nodes re-executed from source (memo) rather than the cache
    import render
    import numpy as np
    class MemG:
        def get(self, k):
            return value(k)
    mg = MemG(); bad5 = []
    for i in sample:
        d = deps[i]
        img, _, _ = render.compose_frame(mg, d['layers'], want_alpha=False)
        if sha(img.tobytes()) != d['sha256_rgb']:
            a = np.asarray(img, int); b = np.asarray(Image.open(os.path.join(FOLDER, 'build', 'cache', 'frames', 'scene_%04d.png' % i)).convert('RGB'), int)
            bad5.append({'i': i, 'max_abs_diff': int(np.abs(a - b).max())})
    res['A5_rebuilt_shot'] = {'ok': not bad5, 'frames_rebuilt': list(sample), 'mismatch': bad5,
                              'note': 'matrices in render_deps are rounded to 5 decimals; a mismatch reports the largest pixel difference'}
    # A6 tags
    tags = {}
    for n in nodes.values():
        tags[n.get('tags')] = tags.get(n.get('tags'), 0) + 1
    res['A6_tags'] = {'ok': set(tags) <= {'documented', 'inferred'}, 'counts': tags}
    res['all_ok'] = all(v['ok'] for k, v in res.items() if k[:1] == 'A')
    json.dump(res, open(os.path.join(FOLDER, 'lineage', 'audit.json'), 'w'), indent=1)
    for k, v in res.items():
        if k[:1] == 'A':
            print(k, 'ok' if v['ok'] else 'FAIL', {kk: vv for kk, vv in v.items() if kk not in ('ok', 'problems', 'credits', 'unknown_blocks', 'misderived', 'mismatched', 'orphan_layers')})
    print('AUDIT', 'PASS' if res['all_ok'] else 'FAIL')
    return res


if __name__ == '__main__':
    r = main()
    sys.exit(0 if r['all_ok'] else 1)
