"""SCION 37 rig: skeletons (bind/rest matrices), forward kinematics, linear blend skinning and dual-quaternion skinning.
All numpy. Coordinates: the character's local frame is x forward, y up, z to its left; metres.
Rest frames are axis-aligned at each joint position, so the bind matrix of joint j is Trans(p_j) and its inverse Trans(-p_j).
A pose is a dict joint -> 3x3 local rotation; the root transform places the character in the world."""
import numpy as np

# ---------------------------------------------------------------- rotations / quaternions

def rx(a):
    c, s = np.cos(a), np.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def ry(a):
    c, s = np.cos(a), np.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

def rz(a):
    c, s = np.cos(a), np.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

def euler(yaw=0., pitch=0., roll=0.):
    """yaw about y (turn), pitch about z (nod / leg swing, + lifts the front), roll about x (twist about the forward axis)."""
    return ry(yaw) @ rz(pitch) @ rx(roll)

def mat2quat(R):
    """rotation matrices (...,3,3) -> unit quaternions (...,4) as (w,x,y,z)"""
    R = np.asarray(R); sh = R.shape[:-2]; R = R.reshape(-1, 3, 3); q = np.zeros((len(R), 4))
    for n, m in enumerate(R):
        t = np.trace(m)
        if t > 0:
            s = np.sqrt(t + 1.) * 2; q[n] = [.25 * s, (m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s]
        elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
            s = np.sqrt(1. + m[0, 0] - m[1, 1] - m[2, 2]) * 2; q[n] = [(m[2, 1] - m[1, 2]) / s, .25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s]
        elif m[1, 1] > m[2, 2]:
            s = np.sqrt(1. + m[1, 1] - m[0, 0] - m[2, 2]) * 2; q[n] = [(m[0, 2] - m[2, 0]) / s, (m[0, 1] + m[1, 0]) / s, .25 * s, (m[1, 2] + m[2, 1]) / s]
        else:
            s = np.sqrt(1. + m[2, 2] - m[0, 0] - m[1, 1]) * 2; q[n] = [(m[1, 0] - m[0, 1]) / s, (m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, .25 * s]
    return q.reshape(sh + (4,))

def qmul(a, b):
    w1, x1, y1, z1 = np.moveaxis(a, -1, 0); w2, x2, y2, z2 = np.moveaxis(b, -1, 0)
    return np.stack([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2, w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                     w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2], -1)

def quat2mat(q):
    w, x, y, z = np.moveaxis(q, -1, 0)
    return np.stack([np.stack([1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], -1),
                     np.stack([2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], -1),
                     np.stack([2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)], -1)], -2)

def slerp_mat(A, B, t):
    qa, qb = mat2quat(A), mat2quat(B)
    if np.dot(qa, qb) < 0: qb = -qb
    d = np.clip(np.dot(qa, qb), -1, 1); th = np.arccos(d)
    q = qa if th < 1e-6 else (np.sin((1 - t) * th) * qa + np.sin(t * th) * qb) / np.sin(th)
    return quat2mat(q / np.linalg.norm(q))

# ---------------------------------------------------------------- skeleton

class Skeleton:
    """joints: list of (name, parent_name or None, rest position (3,)); segs: name -> (a, b) bone segment used for weights."""
    def __init__(self, joints, segs):
        self.names = [j[0] for j in joints]; self.ix = {n: i for i, n in enumerate(self.names)}
        self.parent = np.array([-1 if j[1] is None else self.ix[j[1]] for j in joints])
        self.rest = np.array([j[2] for j in joints], float)
        self.segs = segs
        self.deform = [n for n in self.names if n in segs]          # joints that own skin
        self.dix = np.array([self.ix[n] for n in self.deform])

    def fk(self, pose, root=np.eye(4)):
        """pose: name -> 3x3 local rotation (missing = identity); returns global 4x4 per joint"""
        G = np.zeros((len(self.names), 4, 4))
        for i, n in enumerate(self.names):
            L = np.eye(4); L[:3, :3] = pose.get(n, np.eye(3))
            p = self.parent[i]
            L[:3, 3] = self.rest[i] - (self.rest[p] if p >= 0 else 0)
            G[i] = (G[p] if p >= 0 else root) @ L
        return G

    def skin_mats(self, G):
        """S_j = G_j * inverse(bind_j), bind_j = Trans(rest_j); only the deforming joints, in self.deform order"""
        S = G[self.dix].copy()
        S[:, :3, 3] = G[self.dix, :3, 3] - np.einsum('nij,nj->ni', G[self.dix, :3, :3], self.rest[self.dix])
        return S

# ---------------------------------------------------------------- skinning

def lbs(V, idx, w, S):
    """linear blend skinning: v' = sum_k w_k S_{idx_k} v.  V (n,3), idx/w (n,K), S (J,4,4)"""
    M = np.einsum('nk,nkij->nij', w, S[idx])                      # blended (non-rigid) matrices
    return np.einsum('nij,nj->ni', M[:, :3, :3], V) + M[:, :3, 3]

def dq_from_mats(S):
    q = mat2quat(S[:, :3, :3]); t = S[:, :3, 3]
    tq = np.concatenate([np.zeros((len(t), 1)), t], 1)
    return q, .5 * qmul(tq, q)

def dqs(V, idx, w, S):
    """dual-quaternion skinning (Kavan et al. 2007): blend unit dual quaternions with antipodality fixed against the
    vertex's heaviest bone, normalise, apply.  Rigid by construction, so no candy-wrapper collapse."""
    q0, qe = dq_from_mats(S)
    Q0, QE = q0[idx], qe[idx]                                      # (n,K,4)
    piv = Q0[np.arange(len(V)), np.argmax(w, 1)]
    sgn = np.sign(np.einsum('nki,ni->nk', Q0, piv)); sgn[sgn == 0] = 1
    ww = w * sgn
    b0 = np.einsum('nk,nki->ni', ww, Q0); be = np.einsum('nk,nki->ni', ww, QE)
    nrm = np.linalg.norm(b0, axis=1, keepdims=True); b0 /= nrm; be /= nrm
    R = quat2mat(b0)
    conj = b0 * np.array([1, -1, -1, -1])
    t = 2 * qmul(be, conj)[:, 1:]
    return np.einsum('nij,nj->ni', R, V) + t

def blend_shrink(idx, w, S):
    """per-vertex determinant of the LBS-blended 3x3: 1 = rigid, <1 = the volume loss that makes the candy wrapper"""
    M = np.einsum('nk,nkij->nij', w, S[idx])[:, :3, :3]
    return np.linalg.det(M)

# ---------------------------------------------------------------- the dog skeleton (rest pose, dog local frame)

def dog_skeleton():
    J = []
    def j(n, p, x, y, z=0.): J.append((n, p, (x, y, z)))
    j('pelvis', None, -0.24, .52)
    j('spine', 'pelvis', 0.0, .53)
    j('chest', 'spine', .20, .55)
    j('neck1', 'chest', .32, .60)
    j('neck2', 'neck1', .40, .70)
    j('head', 'neck2', .46, .79)
    j('muzzle', 'head', .68, .74)                 # end
    for s, z in (('L', .045), ('R', -.045)):
        j('ear' + s, 'head', .455, .855, z); j('eartip' + s, 'ear' + s, .44, .965, z * 1.4)
    j('tail1', 'pelvis', -.36, .57); j('tail2', 'tail1', -.50, .52); j('tail3', 'tail2', -.63, .46); j('tailtip', 'tail3', -.77, .39)
    for s, z in (('L', .09), ('R', -.09)):
        j('shoulder' + s, 'chest', .24, .46, z); j('elbow' + s, 'shoulder' + s, .20, .30, z)
        j('wrist' + s, 'elbow' + s, .23, .10, z); j('fpaw' + s, 'wrist' + s, .255, .04, z); j('ftoe' + s, 'fpaw' + s, .32, .02, z)
        j('hip' + s, 'pelvis', -.25, .45, z * .95); j('stifle' + s, 'hip' + s, -.17, .30, z * .95)
        j('hock' + s, 'stifle' + s, -.32, .12, z * .95); j('hpaw' + s, 'hock' + s, -.30, .04, z * .95); j('htoe' + s, 'hpaw' + s, -.235, .02, z * .95)
    P = {n: np.array(p) for n, _, p in J}
    segs = {'pelvis': (P['pelvis'] + [-.06, 0, 0], P['spine']), 'spine': (P['spine'], P['chest']), 'chest': (P['chest'], P['neck1']),
            'neck1': (P['neck1'], P['neck2']), 'neck2': (P['neck2'], P['head']), 'head': (P['head'], P['muzzle']),
            'tail1': (P['tail1'], P['tail2']), 'tail2': (P['tail2'], P['tail3']), 'tail3': (P['tail3'], P['tailtip'])}
    for s in 'LR':
        segs['ear' + s] = (P['ear' + s], P['eartip' + s])
        for a, b in (('shoulder', 'elbow'), ('elbow', 'wrist'), ('wrist', 'fpaw'), ('fpaw', 'ftoe'),
                     ('hip', 'stifle'), ('stifle', 'hock'), ('hock', 'hpaw'), ('hpaw', 'htoe')):
            segs[a + s] = (P[a + s], P[b + s])
    return Skeleton(J, segs)


def person_skeleton():
    """a person, local frame x forward (toward the dog), y up, z to their left"""
    J = []
    def j(n, p, x, y, z=0.): J.append((n, p, (x, y, z)))
    j('hips', None, 0, .95); j('spine', 'hips', 0, 1.15); j('chestp', 'spine', 0, 1.38); j('neck', 'chestp', 0, 1.52)
    j('headp', 'neck', .01, 1.62); j('crown', 'headp', .01, 1.80)
    for s, z in (('L', 1), ('R', -1)):
        j('clav' + s, 'chestp', 0, 1.44, .07 * z); j('sh' + s, 'clav' + s, 0, 1.40, .21 * z); j('el' + s, 'sh' + s, 0, 1.13, .275 * z)
        j('wr' + s, 'el' + s, 0, .88, .305 * z); j('hand' + s, 'wr' + s, 0, .76, .315 * z)
        j('th' + s, 'hips', 0, .90, .10 * z); j('kn' + s, 'th' + s, .01, .50, .10 * z); j('an' + s, 'kn' + s, 0, .09, .10 * z)
        j('toe' + s, 'an' + s, .16, .03, .10 * z)
    P = {n: np.array(p) for n, _, p in J}
    segs = {'hips': (P['hips'], P['spine']), 'spine': (P['spine'], P['chestp']), 'chestp': (P['chestp'], P['neck']),
            'neck': (P['neck'], P['headp']), 'headp': (P['headp'], P['crown'])}
    for s in 'LR':
        for a, b in (('clav', 'sh'), ('sh', 'el'), ('el', 'wr'), ('wr', 'hand'), ('th', 'kn'), ('kn', 'an'), ('an', 'toe')):
            segs[a + s] = (P[a + s], P[b + s])
    return Skeleton(J, segs)
