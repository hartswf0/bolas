"""SCION 54 Provenance Graph: the lineage engine.

Every image in the film is a node in a derivative DAG. A node is either a SOURCE (an immutable file with a content hash,
a source id, a title, an archive URL and a rights status) or a DERIVATIVE (an operation with a signature, applied to
parent nodes with recorded parameters). A node's id is the content hash of what it produced, so a rebuild that does not
reproduce the same pixels does not reproduce the same id, and the audit catches it.

Rights propagate: a derivative carries the most restrictive rights of its parents; any 'unknown' parent blocks it.
Tags on parameters are either 'documented' (they come from the archive or kit: SAM masks, pose_agent_v8 keys) or
'inferred' (this swarm decided them: my keys, my cut lines, my colours)."""
import hashlib, io, json, os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(FOLDER, '..', '..', '..'))
CACHE = os.path.join(HERE, 'cache', 'nodes')
os.makedirs(CACHE, exist_ok=True)

RIGHTS_ORDER = ['self-made', 'public_domain', 'CC-BY-4.0', 'unknown']   # later = more restrictive; unknown blocks
SCHEMA_VERSION = 'pg-lineage/1.1'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def img_bytes(im):
    """canonical bytes for hashing: mode, size and raw pixels (not PNG, whose encoder may vary)."""
    return (im.mode + '%dx%d' % im.size).encode() + im.tobytes()


def combine_rights(rs):
    rs = list(rs)
    if any(r == 'unknown' for r in rs):
        return 'unknown'
    return max(rs, key=RIGHTS_ORDER.index) if rs else 'self-made'


class Graph:
    def __init__(self):
        self.nodes = {}
        self.ops = {}
        self.mem = {}

    def register(self, name, version, fn, doc):
        self.ops[name] = {'fn': fn, 'version': version, 'doc': doc}

    def sig(self, name, params):
        o = self.ops[name]
        return sha(json.dumps({'op': name, 'v': o['version'], 'params': params}, sort_keys=True).encode())[:16]

    # ---- sources ----
    def source(self, path, source_id, title, url, rights, kind='frame', credit=None, extra=None):
        p = os.path.join(REPO, path) if not os.path.isabs(path) else path
        raw = open(p, 'rb').read()
        h = sha(raw)
        nid = 's_' + h[:16]
        if path.endswith(('.jpg', '.png')):
            im = Image.open(io.BytesIO(raw)).convert('RGB')
            self.mem[nid] = im
        elif path.endswith('.json'):
            self.mem[nid] = json.loads(raw)
        elif path.endswith('.ndjson'):
            self.mem[nid] = [json.loads(l) for l in raw.decode().splitlines() if l.strip()]
        self.nodes[nid] = {'id': nid, 'kind': 'source', 'type': kind, 'path': os.path.relpath(p, REPO), 'sha256': h,
                           'source_id': source_id, 'title': title, 'url': url, 'rights': rights, 'credit': credit,
                           'parents': [], 'tags': 'documented', **(extra or {})}
        return nid

    def drawn(self, name, data, note):
        """a source this swarm made itself (a cut line, a polygon, a colour ramp): recorded as data, rights self-made."""
        h = sha(json.dumps(data, sort_keys=True).encode())
        nid = 'd_' + h[:16]
        self.nodes[nid] = {'id': nid, 'kind': 'source', 'type': 'drawn', 'name': name, 'data': data, 'sha256': h,
                           'rights': 'self-made', 'parents': [], 'tags': 'inferred', 'note': note}
        self.mem[nid] = data
        return nid

    # ---- derivatives ----
    def op(self, name, parents, params, tags='inferred', label=None):
        o = self.ops[name]
        ins = [self.get(p) for p in parents]
        out = o['fn'](*ins, **params)
        b = img_bytes(out) if isinstance(out, Image.Image) else json.dumps(out, sort_keys=True).encode()
        h = sha(b)
        nid = 'n_' + h[:16]
        self.mem[nid] = out
        if isinstance(out, Image.Image):
            cp = os.path.join(CACHE, nid + '.png')
            if not os.path.exists(cp):
                out.save(cp)
        self.nodes[nid] = {'id': nid, 'kind': 'derivative', 'op': name, 'op_version': o['version'], 'op_sig': self.sig(name, params),
                           'parents': list(parents), 'params': params, 'sha256': h, 'tags': tags, 'label': label,
                           'rights': combine_rights(self.nodes[p]['rights'] for p in parents),
                           'size': list(out.size) if isinstance(out, Image.Image) else None}
        return nid

    def get(self, nid):
        if nid in self.mem:
            return self.mem[nid]
        n = self.nodes[nid]
        if n['kind'] == 'derivative':
            cp = os.path.join(CACHE, nid + '.png')
            im = Image.open(cp); im.load(); self.mem[nid] = im
            return im
        raise KeyError(nid)

    def ancestry(self, nid):
        seen, stack = [], [nid]
        while stack:
            k = stack.pop()
            if k in seen:
                continue
            seen.append(k)
            stack.extend(self.nodes[k]['parents'])
        return seen

    def save(self, path, roots=None):
        json.dump({'schema': SCHEMA_VERSION, 'ops': {k: {'version': v['version'], 'doc': v['doc']} for k, v in self.ops.items()},
                   'nodes': self.nodes, 'roots': roots or {}}, open(path, 'w'), indent=1, sort_keys=True)

    @staticmethod
    def load_meta(path):
        return json.load(open(path))
