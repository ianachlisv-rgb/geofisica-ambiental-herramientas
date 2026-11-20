"""
Modelado directo 2.5D por elementos finitos (triangulos lineales) + inversion Gauss-Newton suavizada
(ERT e IP linealizado) con topografia. Implementacion propia (scipy) para esta actividad.
Convenciones: un parametro = bloque rectangular (5 m de ancho, centrado en cada electrodo) x capa.
La malla sigue la topografia en superficie y se aplana con la profundidad (rejilla "distorsionada amortiguada").
"""
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spla
from scipy.special import k0e, k1e

# ---------------------------------------------------------------- wavenumbers (Gauss-Legendre en ln k)
def wavenumbers(n=16, kmin=2e-4, kmax=3.0):
    x, w = np.polynomial.legendre.leggauss(n)
    s0, s1 = np.log(kmin), np.log(kmax)
    s = 0.5*(s1-s0)*x + 0.5*(s1+s0)
    k = np.exp(s)
    wk = 0.5*(s1-s0)*w*k           # dk = k ds
    return k, wk

# ---------------------------------------------------------------- mesh
class Grid:
    def __init__(self, zs, spacing=5.0, layer_h=None, n_ext_x=11, g_x=1.5, n_ext_z=7, g_z=1.7, fade=45.0):
        zs = np.asarray(zs, float)
        self.nel = len(zs)                       # electrodes = parameter columns
        self.xel = np.arange(self.nel)*spacing
        self.sp = spacing
        if layer_h is None:
            layer_h = [1.0, 1.2, 1.4, 1.6, 1.9, 2.2, 2.5, 2.9, 3.3, 3.8, 4.4, 5.0, 5.7, 6.5]
        self.layer_h = np.array(layer_h, float)
        self.nz = len(layer_h)
        dxf = spacing/2.0
        # central FE node x (from -sp/2 to L+sp/2 every dxf)
        xc = np.arange(-spacing/2, self.xel[-1] + spacing/2 + 1e-9, dxf)
        left = xc[0] - dxf*np.cumsum(g_x**np.arange(1, n_ext_x+1))
        right = xc[-1] + dxf*np.cumsum(g_x**np.arange(1, n_ext_x+1))
        self.xn = np.concatenate([left[::-1], xc, right])
        self.ncol_f = len(self.xn) - 1           # FE columns
        self.ixc0 = n_ext_x                       # index of first central node
        # nominal depths
        hz = list(self.layer_h) + list(self.layer_h[-1]*g_z**np.arange(1, n_ext_z+1))
        self.D = np.concatenate([[0.0], np.cumsum(hz)])
        self.nrow_f = len(hz)
        # surface elevation at all FE nodes (linear between electrodes, flat outside)
        self.zs_node = np.interp(self.xn, self.xel, zs)
        z0 = zs.mean(); self.z0 = z0
        w = np.clip(1.0 - self.D/fade, 0, 1)
        self.Z = (z0 - self.D)[None, :] + (self.zs_node - z0)[:, None]*w[None, :]   # (nxn, nD)
        self.X = np.repeat(self.xn[:, None], len(self.D), axis=1)
        nn = self.X.size
        self.nn = nn
        idx = np.arange(nn).reshape(self.X.shape)
        self.idx = idx
        # triangles: quad (i,j) -> 2 triangles, alternating diagonal
        tris, tri_quad = [], []
        for i in range(self.ncol_f):
            for j in range(self.nrow_f):
                a, b, c, d = idx[i, j], idx[i+1, j], idx[i+1, j+1], idx[i, j+1]
                if (i + j) % 2 == 0:
                    tris += [[a, b, c], [a, c, d]]
                else:
                    tris += [[a, b, d], [b, c, d]]
                tri_quad += [(i, j), (i, j)]
        self.tri = np.array(tris); self.tri_quad = np.array(tri_quad)
        self.ntri = len(self.tri)
        # parameter map: FE quad -> (param col, param layer)
        # param column p covers FE central columns 2p, 2p+1 (central index offset ixc0)
        col_to_p = np.zeros(self.ncol_f, int)
        for i in range(self.ncol_f):
            ic = i - self.ixc0
            col_to_p[i] = int(np.clip(ic//2, 0, self.nel-1))
        row_to_p = np.minimum(np.arange(self.nrow_f), self.nz-1)
        self.npar = self.nel*self.nz
        self.tri_par = col_to_p[self.tri_quad[:, 0]]*self.nz + row_to_p[self.tri_quad[:, 1]]
        self.P = sp.csr_matrix((np.ones(self.ntri), (self.tri_par, np.arange(self.ntri))), shape=(self.npar, self.ntri))
        # electrode nodes
        self.enode = np.array([idx[self.ixc0 + 1 + 2*p, 0] for p in range(self.nel)])
        # geometry
        x = self.X.ravel()[self.tri]; z = self.Z.ravel()[self.tri]
        b = np.stack([z[:, 1]-z[:, 2], z[:, 2]-z[:, 0], z[:, 0]-z[:, 1]], 1)
        c = np.stack([x[:, 2]-x[:, 1], x[:, 0]-x[:, 2], x[:, 1]-x[:, 0]], 1)
        A2 = (x[:, 1]-x[:, 0])*(z[:, 2]-z[:, 0]) - (x[:, 2]-x[:, 0])*(z[:, 1]-z[:, 0])
        self.area = 0.5*np.abs(A2)
        sgn = np.sign(A2)
        self.gx = b/(2*self.area[:, None])*sgn[:, None]     # dN_i/dx
        self.gz = c/(2*self.area[:, None])*sgn[:, None]
        self.Ks = self.area[:, None, None]*(self.gx[:, :, None]*self.gx[:, None, :] + self.gz[:, :, None]*self.gz[:, None, :])
        self.Ms = self.area[:, None, None]/12.0*(1 + np.eye(3))[None]
        ii = np.repeat(self.tri[:, :, None], 3, 2).reshape(self.ntri, 9)
        jj = np.repeat(self.tri[:, None, :], 3, 1).reshape(self.ntri, 9)
        self.I, self.J = ii.ravel(), jj.ravel()
        self.Ks9, self.Ms9 = self.Ks.reshape(self.ntri, 9), self.Ms.reshape(self.ntri, 9)
        # boundary edges (left, right, bottom) with adjacent triangle
        self._boundary()
        # cell centers of parameters (for plotting)
        self.par_cx, self.par_cz, self.par_poly = self._param_geometry()

    def _boundary(self):
        edges = []   # (n1, n2, quad(i,j), normal-outward direction)
        i_l, i_r = 0, self.ncol_f - 1
        for j in range(self.nrow_f):
            edges.append((self.idx[0, j], self.idx[0, j+1], (i_l, j)))
            edges.append((self.idx[-1, j], self.idx[-1, j+1], (i_r, j)))
        for i in range(self.ncol_f):
            edges.append((self.idx[i, -1], self.idx[i+1, -1], (i, self.nrow_f-1)))
        self.bedges = np.array([[e[0], e[1]] for e in edges])
        self.bquad = [e[2] for e in edges]
        xe = self.X.ravel()[self.bedges]; ze = self.Z.ravel()[self.bedges]
        self.blen = np.hypot(xe[:, 1]-xe[:, 0], ze[:, 1]-ze[:, 0])
        self.bmid = np.stack([xe.mean(1), ze.mean(1)], 1)
        t = np.stack([xe[:, 1]-xe[:, 0], ze[:, 1]-ze[:, 0]], 1)
        nrm = np.stack([t[:, 1], -t[:, 0]], 1)/self.blen[:, None]
        # make outward: pointing away from the domain centre
        cx, cz = self.xel.mean(), self.z0 - 20.0
        outv = self.bmid - np.array([cx, cz])
        flip = (nrm*outv).sum(1) < 0
        nrm[flip] *= -1
        self.bnrm = nrm
        # triangle adjacent to each boundary edge: take any triangle of that quad containing both nodes
        q2t = {}
        for t_i, q in enumerate(map(tuple, self.tri_quad)):
            q2t.setdefault(q, []).append(t_i)
        bt = []
        for (n1, n2), q in zip(self.bedges, self.bquad):
            for t_i in q2t[q]:
                if n1 in self.tri[t_i] and n2 in self.tri[t_i]:
                    bt.append(t_i); break
        self.btri = np.array(bt)

    def _param_geometry(self):
        # polygons of each parameter block (central region): corners from FE nodes
        polys, cx, cz = [], [], []
        for p in range(self.nel):
            i0 = self.ixc0 + 2*p
            for l in range(self.nz):
                j0, j1 = l, l+1
                pts = [(self.X[i0, j0], self.Z[i0, j0]), (self.X[i0+2, j0], self.Z[i0+2, j0]),
                       (self.X[i0+2, j1], self.Z[i0+2, j1]), (self.X[i0, j1], self.Z[i0, j1])]
                polys.append(pts)
                cx.append(self.xel[p]); cz.append(np.mean([q[1] for q in pts]))
        return np.array(cx), np.array(cz), polys

    # roughness operator (volume-weighted first differences)
    def roughness(self, zweight=1.0):
        rows, cols, vals = [], [], []
        r = 0
        for p in range(self.nel):
            for l in range(self.nz):
                k = p*self.nz + l
                if p+1 < self.nel:
                    w = np.sqrt(self.layer_h[l]/self.sp)
                    rows += [r, r]; cols += [k, k+self.nz]; vals += [-w, w]; r += 1
                if l+1 < self.nz:
                    dzc = 0.5*(self.layer_h[l] + self.layer_h[l+1])
                    w = zweight*np.sqrt(self.sp/dzc)
                    rows += [r, r]; cols += [k, k+1]; vals += [-w, w]; r += 1
        return sp.csr_matrix((vals, (rows, cols)), shape=(r, self.npar))

# ---------------------------------------------------------------- forward / jacobian
class Forward:
    def __init__(self, grid, A, B, M, N, kflat, nk=14, kmin=2e-4, kmax=3.0):
        self.g = grid
        self.A, self.B, self.M, self.N = [np.asarray(v, int) for v in (A, B, M, N)]
        self.kflat = np.asarray(kflat, float)
        self.k, self.wk = wavenumbers(nk, kmin, kmax)
        self.ref = np.array([grid.xel.mean(), grid.z0])
        # mixed BC geometry factors (r measured from line centre at surface)
        d = grid.bmid - self.ref
        self.r = np.hypot(d[:, 0], d[:, 1]); self.cos = (d*grid.bnrm).sum(1)/self.r
        self.corr = np.ones(len(self.A))      # mesh-error correction factors (set via calibrate())

    def _solve(self, sigma_tri, k):
        g = self.g
        vals = sigma_tri[:, None]*(g.Ks9 + k**2*g.Ms9)
        K = sp.coo_matrix((vals.ravel(), (g.I, g.J)), shape=(g.nn, g.nn)).tocsr()
        c = k*k1e(k*self.r)/k0e(k*self.r)*self.cos
        w = sigma_tri[g.btri]*c*g.blen/6.0
        e1, e2 = g.bedges[:, 0], g.bedges[:, 1]
        Kb = sp.coo_matrix((np.concatenate([2*w, 2*w, w, w]), (np.concatenate([e1, e2, e1, e2]), np.concatenate([e1, e2, e2, e1]))), shape=(g.nn, g.nn))
        K = (K + Kb).tocsc()
        lu = spla.splu(K)
        rhs = np.zeros((g.nn, g.nel)); rhs[g.enode, np.arange(g.nel)] = 1.0
        return lu.solve(rhs)

    def response(self, rho_par, jac=False):
        g = self.g
        rho_tri = rho_par[g.tri_par]; sigma = 1.0/rho_tri
        V = np.zeros(len(self.A))
        if jac:
            S = np.zeros((len(self.A), g.ntri))
        for k, wk in zip(self.k, self.wk):
            phi = self._solve(sigma, k)               # nn x nel
            pe = phi[g.enode, :]                      # electrode potentials (nel x nel): pe[m, a]
            V += wk/np.pi*(pe[self.M, self.A] - pe[self.N, self.A] - pe[self.M, self.B] + pe[self.N, self.B])
            if jac:
                S += wk/np.pi*self._sens(phi, k)
        R = V
        rhoa = self.kflat*R*self.corr
        if not jac:
            return rhoa
        # d ln(rhoa)/d ln(rho_p) = (1/R) * sum_eps sigma_eps * S_eps   (S already = -dV/dsigma sign-handled)
        Slog = (S*sigma[None, :]) @ g.P.T.toarray() if False else (g.P @ (S*sigma[None, :]).T).T
        Slog = Slog/R[:, None]
        return rhoa, np.asarray(Slog)

    def _sens(self, phi, k):
        """ sum over triangles of  A [ gMN.gAB + k^2/12 ((sum phiMN)(sum phiAB) + sum phiMN*phiAB) ]  (positive = -dV/dsigma) """
        g = self.g
        pA, pB, pM, pN = phi[:, self.A], phi[:, self.B], phi[:, self.M], phi[:, self.N]
        pab = pA - pB; pmn = pM - pN                      # nn x nq
        tn = g.tri
        out = np.zeros((len(self.A), g.ntri))
        # process in chunks of quadripoles to limit memory
        nq = len(self.A); ch = 64
        for s in range(0, nq, ch):
            sl = slice(s, min(nq, s+ch))
            ab = pab[:, sl]; mn = pmn[:, sl]
            ab_t = ab[tn]; mn_t = mn[tn]                   # ntri x 3 x nqc
            gab_x = np.einsum('ti,tiq->tq', g.gx, ab_t); gab_z = np.einsum('ti,tiq->tq', g.gz, ab_t)
            gmn_x = np.einsum('ti,tiq->tq', g.gx, mn_t); gmn_z = np.einsum('ti,tiq->tq', g.gz, mn_t)
            sab = ab_t.sum(1); smn = mn_t.sum(1); pp = (ab_t*mn_t).sum(1)
            val = g.area[:, None]*(gab_x*gmn_x + gab_z*gmn_z + k*k/12.0*(sab*smn + pp))
            out[sl] = val.T
        return out
