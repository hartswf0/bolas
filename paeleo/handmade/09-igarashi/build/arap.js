// SCION 09 · Igarashi — the optimization engineer's artifact: a 2D as-rigid-as-possible solver.
// Energy (per triangle t, edges e=(i,j) with cotangent weight c_e of the opposite angle, rigidity weight w_t):
//     E = Σ_t w_t Σ_e c_e ‖(x_i − x_j) − R_t (p_i − p_j)‖²  +  λ Σ_handles ‖x_h − target_h‖²
// minimized by alternating a LOCAL step (the best rotation R_t of every triangle, closed form in 2D: the local rotation
// estimates) and a GLOBAL step (one sparse linear solve for all vertices, x and y separately, with a banded Cholesky factor
// that is computed once per handle set and reused every frame). Feature-protect masks enter as larger w_t.
// Handles are small vertex sets; each vertex is pulled to target + R_h (rest − rest_centre), where R_h is given by the rig
// or, when the rig leaves it free, re-estimated from the current solution every iteration.
// Works in node (module.exports) and the browser (window.ARAP).
(function (root) {
  const LAMBDA = 600;

  class Solver {
    constructor(mesh) {
      this.mesh = mesh;
      const V = mesh.verts, T = mesh.tris, n = V.length;
      this.n = n;
      this.P = new Float64Array(2 * n); for (let i = 0; i < n; i++) { this.P[2 * i] = V[i][0]; this.P[2 * i + 1] = V[i][1]; }
      const nt = T.length;
      this.T = new Int32Array(3 * nt); for (let t = 0; t < nt; t++) for (let k = 0; k < 3; k++) this.T[3 * t + k] = T[t][k];
      this.W = Float64Array.from(mesh.weight);
      this.C = new Float64Array(3 * nt); // cot weight for edge opposite vertex k, edge = (k+1, k+2)
      const P = this.P;
      for (let t = 0; t < nt; t++) {
        for (let k = 0; k < 3; k++) {
          const a = this.T[3 * t + k], b = this.T[3 * t + (k + 1) % 3], c = this.T[3 * t + (k + 2) % 3];
          const ux = P[2 * b] - P[2 * a], uy = P[2 * b + 1] - P[2 * a + 1], vx = P[2 * c] - P[2 * a], vy = P[2 * c + 1] - P[2 * a + 1];
          const cr = Math.abs(ux * vy - uy * vx), dt = ux * vx + uy * vy;
          this.C[3 * t + k] = Math.max(0, 0.5 * dt / Math.max(cr, 1e-9)); // clamp obtuse (none on this grid)
        }
      }
      // bandwidth
      let bw = 0;
      for (let t = 0; t < nt; t++) for (let k = 0; k < 3; k++) { const a = this.T[3 * t + k], b = this.T[3 * t + (k + 1) % 3]; bw = Math.max(bw, Math.abs(a - b)); }
      this.bw = bw;
      this.R = new Float64Array(2 * nt); // cos, sin per triangle
      this.factors = new Map();
    }

    // Laplacian + λ·C as banded matrix (row i holds columns i-bw..i), then Cholesky in place
    factor(handleVerts) {
      const key = handleVerts.join(',');
      if (this.factors.has(key)) return this.factors.get(key);
      const n = this.n, bw = this.bw, B = bw + 1, A = new Float64Array(n * B);
      const at = (i, j) => i * B + (j - i + bw); // j<=i
      const nt = this.T.length / 3;
      for (let t = 0; t < nt; t++) {
        const w = this.W[t];
        for (let k = 0; k < 3; k++) {
          const i = this.T[3 * t + (k + 1) % 3], j = this.T[3 * t + (k + 2) % 3], c = this.C[3 * t + k] * w;
          A[at(i, i)] += c; A[at(j, j)] += c;
          if (i > j) A[at(i, j)] -= c; else A[at(j, i)] -= c;
        }
      }
      const isH = new Uint8Array(n); for (const v of handleVerts) { isH[v] = 1; A[at(v, v)] += LAMBDA; }
      for (let i = 0; i < n; i++) A[at(i, i)] += 1e-8;
      // banded Cholesky: A = L Lᵀ
      for (let i = 0; i < n; i++) {
        const j0 = Math.max(0, i - bw);
        for (let j = j0; j <= i; j++) {
          let s = A[at(i, j)];
          const k0 = Math.max(j0, j - bw);
          for (let k = k0; k < j; k++) s -= A[at(i, k)] * A[at(j, k)];
          if (i === j) { A[at(i, i)] = Math.sqrt(Math.max(s, 1e-12)); }
          else A[at(i, j)] = s / A[at(j, j)];
        }
      }
      const f = { A, isH };
      this.factors.set(key, f);
      return f;
    }

    backsolve(f, b) { // solve L Lᵀ x = b, in place
      const n = this.n, bw = this.bw, B = bw + 1, A = f.A;
      for (let i = 0; i < n; i++) { let s = b[i]; const j0 = Math.max(0, i - bw); for (let j = j0; j < i; j++) s -= A[i * B + (j - i + bw)] * b[j]; b[i] = s / A[i * B + bw]; }
      for (let i = n - 1; i >= 0; i--) { let s = b[i]; const j1 = Math.min(n - 1, i + bw); for (let j = i + 1; j <= j1; j++) s -= A[j * B + (i - j + bw)] * b[j]; b[i] = s / A[i * B + bw]; }
      return b;
    }

    // handles: [{verts:[...], at:[x,y], ang: number|undefined}] in drawing coordinates.
    // X: Float64Array(2n) initial guess (modified and returned)
    solve(handles, X, iters = 8) {
      const n = this.n, P = this.P, T = this.T, nt = T.length / 3;
      const hv = []; for (const h of handles) for (const v of h.verts) hv.push(v);
      const f = this.factor(hv.slice().sort((a, b) => a - b));
      const bx = new Float64Array(n), by = new Float64Array(n);
      // rest centres of handles
      for (const h of handles) if (!h.rc) { let cx = 0, cy = 0; for (const v of h.verts) { cx += P[2 * v]; cy += P[2 * v + 1]; } h.rc = [cx / h.verts.length, cy / h.verts.length]; }
      for (let it = 0; it < iters; it++) {
        // local step
        for (let t = 0; t < nt; t++) {
          let m00 = 0, m01 = 0, m10 = 0, m11 = 0;
          for (let k = 0; k < 3; k++) {
            const i = T[3 * t + (k + 1) % 3], j = T[3 * t + (k + 2) % 3], c = this.C[3 * t + k];
            const ex = P[2 * i] - P[2 * j], ey = P[2 * i + 1] - P[2 * j + 1], fx = X[2 * i] - X[2 * j], fy = X[2 * i + 1] - X[2 * j + 1];
            m00 += c * ex * fx; m01 += c * ex * fy; m10 += c * ey * fx; m11 += c * ey * fy;
          }
          const th = Math.atan2(m01 - m10, m00 + m11);
          this.R[2 * t] = Math.cos(th); this.R[2 * t + 1] = Math.sin(th);
        }
        // global step rhs
        bx.fill(0); by.fill(0);
        for (let t = 0; t < nt; t++) {
          const w = this.W[t], co = this.R[2 * t], si = this.R[2 * t + 1];
          for (let k = 0; k < 3; k++) {
            const i = T[3 * t + (k + 1) % 3], j = T[3 * t + (k + 2) % 3], c = this.C[3 * t + k] * w;
            const ex = P[2 * i] - P[2 * j], ey = P[2 * i + 1] - P[2 * j + 1];
            const rx = co * ex - si * ey, ry = si * ex + co * ey;
            bx[i] += c * rx; by[i] += c * ry; bx[j] -= c * rx; by[j] -= c * ry;
          }
        }
        for (const h of handles) {
          let co = 1, si = 0;
          if (h.ang !== undefined && h.ang !== null) { co = Math.cos(h.ang); si = Math.sin(h.ang); }
          else if (h.verts.length > 1) { // re-estimate the handle's rotation from the current solution
            let cx = 0, cy = 0; for (const v of h.verts) { cx += X[2 * v]; cy += X[2 * v + 1]; } cx /= h.verts.length; cy /= h.verts.length;
            let a = 0, b = 0; for (const v of h.verts) { const ex = P[2 * v] - h.rc[0], ey = P[2 * v + 1] - h.rc[1], fx = X[2 * v] - cx, fy = X[2 * v + 1] - cy; a += ex * fx + ey * fy; b += ex * fy - ey * fx; }
            const th = Math.atan2(b, a); co = Math.cos(th); si = Math.sin(th);
          }
          const s = h.scale || 1;
          for (const v of h.verts) {
            const ex = (P[2 * v] - h.rc[0]) * s, ey = (P[2 * v + 1] - h.rc[1]) * s;
            bx[v] += LAMBDA * (h.at[0] + co * ex - si * ey); by[v] += LAMBDA * (h.at[1] + si * ex + co * ey);
          }
        }
        this.backsolve(f, bx); this.backsolve(f, by);
        for (let i = 0; i < n; i++) { X[2 * i] = bx[i]; X[2 * i + 1] = by[i]; }
      }
      return X;
    }

    // Solve, then repair: wherever a triangle has turned over, make it and its neighbours stiffer (×4) and solve again.
    // The stiffening is kept, so the mesh accumulates a heat map of where this rig fails (this.heat), which is reported.
    solveRepair(handles, X, iters = 8, rounds = 4) {
      this.solve(handles, X, iters);
      if (!this.heat) { this.heat = new Float64Array(this.T.length / 3).fill(1); this.vt = null; }
      for (let r = 0; r < rounds; r++) {
        const bad = this.inverted(X); if (!bad.length) break;
        if (!this.vt) { this.vt = Array.from({ length: this.n }, () => []); const nt = this.T.length / 3; for (let t = 0; t < nt; t++) for (let k = 0; k < 3; k++) this.vt[this.T[3 * t + k]].push(t); }
        const hit = new Set(); for (const t of bad) for (let k = 0; k < 3; k++) for (const u of this.vt[this.T[3 * t + k]]) hit.add(u);
        for (const t of hit) { if (this.heat[t] < 256) { this.heat[t] *= 4; this.W[t] *= 4; } }
        this.factors.clear(); this.repairs = (this.repairs || 0) + 1;
        this.solve(handles, X, iters + 4);
      }
      return X;
    }
    inverted(X) {
      const T = this.T, nt = T.length / 3, out = [];
      for (let t = 0; t < nt; t++) { const a = T[3 * t], b = T[3 * t + 1], c = T[3 * t + 2]; const ar = (X[2 * b] - X[2 * a]) * (X[2 * c + 1] - X[2 * a + 1]) - (X[2 * b + 1] - X[2 * a + 1]) * (X[2 * c] - X[2 * a]); if (ar <= 0) out.push(t); }
      return out;
    }

    rest() { return Float64Array.from(this.P); }

    // a similarity fit of the rest mesh to the handle targets: the starting guess after a drawing swap
    initFrom(handles) {
      const P = this.P, n = this.n; let sx = 0, sy = 0, tx = 0, ty = 0, m = 0;
      const pts = []; for (const h of handles) for (const v of h.verts) pts.push([P[2 * v], P[2 * v + 1], h.at[0] + (P[2 * v] - (h.rc ? h.rc[0] : P[2 * v])), h.at[1] + (P[2 * v + 1] - (h.rc ? h.rc[1] : P[2 * v + 1]))]);
      for (const h of handles) { let cx = 0, cy = 0; for (const v of h.verts) { cx += P[2 * v]; cy += P[2 * v + 1]; } h.rc = [cx / h.verts.length, cy / h.verts.length]; }
      const Q = handles.map(h => [h.rc[0], h.rc[1], h.at[0], h.at[1]]);
      for (const q of Q) { sx += q[0]; sy += q[1]; tx += q[2]; ty += q[3]; m++; }
      sx /= m; sy /= m; tx /= m; ty /= m;
      let a = 0, b = 0, d = 0;
      for (const q of Q) { const ex = q[0] - sx, ey = q[1] - sy, fx = q[2] - tx, fy = q[3] - ty; a += ex * fx + ey * fy; b += ex * fy - ey * fx; d += ex * ex + ey * ey; }
      const th = Q.length > 1 ? Math.atan2(b, a) : 0, co = Math.cos(th), si = Math.sin(th);
      const X = new Float64Array(2 * n);
      for (let i = 0; i < n; i++) { const ex = P[2 * i] - sx, ey = P[2 * i + 1] - sy; X[2 * i] = tx + co * ex - si * ey; X[2 * i + 1] = ty + si * ex + co * ey; }
      return X;
    }

    // diagnostics: inverted triangles, normalized ARAP energy, worst feature distortion (max |σ−1| over protected triangles)
    diagnose(X) {
      const P = this.P, T = this.T, nt = T.length / 3;
      let inv = 0, e = 0, e0 = 0, featWorst = 0, minArea = Infinity;
      for (let t = 0; t < nt; t++) {
        const a = T[3 * t], b = T[3 * t + 1], c = T[3 * t + 2];
        const ux = X[2 * b] - X[2 * a], uy = X[2 * b + 1] - X[2 * a + 1], vx = X[2 * c] - X[2 * a], vy = X[2 * c + 1] - X[2 * a + 1];
        const ar = ux * vy - uy * vx;
        const px = P[2 * b] - P[2 * a], py = P[2 * b + 1] - P[2 * a + 1], qx = P[2 * c] - P[2 * a], qy = P[2 * c + 1] - P[2 * a + 1];
        const ar0 = px * qy - py * qx;
        minArea = Math.min(minArea, ar / ar0);
        if (ar <= 0) inv++;
        const co = this.R[2 * t], si = this.R[2 * t + 1];
        for (let k = 0; k < 3; k++) {
          const i = T[3 * t + (k + 1) % 3], j = T[3 * t + (k + 2) % 3], cc = this.C[3 * t + k] * this.W[t];
          const ex = P[2 * i] - P[2 * j], ey = P[2 * i + 1] - P[2 * j + 1], fx = X[2 * i] - X[2 * j], fy = X[2 * i + 1] - X[2 * j + 1];
          const rx = co * ex - si * ey, ry = si * ex + co * ey;
          e += cc * ((fx - rx) ** 2 + (fy - ry) ** 2); e0 += cc * (ex * ex + ey * ey);
        }
        if (this.W[t] > 1) {
          // Jacobian J = [u v][p q]^-1, singular values
          const det = px * qy - py * qx;
          const j00 = (ux * qy - vx * py) / det, j01 = (vx * px - ux * qx) / det, j10 = (uy * qy - vy * py) / det, j11 = (vy * px - uy * qx) / det;
          const E = (j00 + j11) / 2, F = (j00 - j11) / 2, G = (j10 + j01) / 2, H = (j10 - j01) / 2;
          const Q = Math.hypot(E, H), R = Math.hypot(F, G);
          featWorst = Math.max(featWorst, Math.abs(Q + R - 1), Math.abs(Q - R - 1));
        }
      }
      return { inverted: inv, energy: e / e0, feature_distortion: featWorst, min_area_ratio: minArea };
    }
  }

  // Weighted linear-blend skinning on the same mesh and handles — the honest comparison the bar asks for.
  // Each vertex blends the handles' similarity transforms with weights ∝ 1/d² (geodesic-free, as in common cutout rigs).
  function skin(mesh, handles, X0) {
    const P = mesh.verts, n = P.length, out = new Float64Array(2 * n);
    const H = handles.map(h => { let cx = 0, cy = 0; for (const v of h.verts) { cx += P[v][0]; cy += P[v][1]; } return { rc: [cx / h.verts.length, cy / h.verts.length], at: h.at, ang: h.ang || 0 }; });
    // each handle's translation; rotation from the rig or 0
    for (let i = 0; i < n; i++) {
      let ws = 0, x = 0, y = 0;
      for (const h of H) {
        const d2 = (P[i][0] - h.rc[0]) ** 2 + (P[i][1] - h.rc[1]) ** 2 + 25, w = 1 / (d2 * d2);
        const co = Math.cos(h.ang), si = Math.sin(h.ang), ex = P[i][0] - h.rc[0], ey = P[i][1] - h.rc[1];
        x += w * (h.at[0] + co * ex - si * ey); y += w * (h.at[1] + si * ex + co * ey); ws += w;
      }
      out[2 * i] = x / ws; out[2 * i + 1] = y / ws;
    }
    return out;
  }

  const api = { Solver, skin, LAMBDA };
  if (typeof module !== 'undefined') module.exports = api; else root.ARAP = api;
})(typeof window !== 'undefined' ? window : globalThis);
