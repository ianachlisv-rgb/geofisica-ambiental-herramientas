import sys, numpy as np, scipy.sparse as sp
from ert_tools import load_line, TOPO
from ert2d import Grid, Forward

def build(line, use=None, topo=True, nk=14):
    h, df = load_line(line)
    if use is not None:
        df = df[use].reset_index(drop=True)
    zs = TOPO[line].elevacion_m.values.astype(float) if topo else np.zeros(41)
    g = Grid(zs)
    fw = Forward(g, df.A, df.B, df.M, df.N, df.k, nk=nk)
    gf = Grid(np.zeros(41)); fwf = Forward(gf, df.A, df.B, df.M, df.N, df.k, nk=nk)
    fw.corr = 100.0/fwf.response(np.full(gf.npar, 100.))      # mesh-error correction (flat homogeneous reference)
    return g, fw, df

def rms_rel(obs, calc):
    return 100*np.sqrt(np.mean(((obs-calc)/obs)**2))

def invert_dc(g, fw, rhoa_obs, relerr=0.03, lam0=10., lam_min=None, lam_fac=1.0, zw=1.0, niter=8, m0=None, verbose=True):
    d = np.log(rhoa_obs); nd = len(d)
    Wd = 1.0/np.full(nd, relerr)
    C = g.roughness(zw); CtC = (C.T @ C).toarray()
    m = np.full(g.npar, np.mean(d)) if m0 is None else m0.copy()
    hist = []
    lam = lam0
    def phi(m, lam):
        f = np.log(fw.response(np.exp(m)))
        return np.sum((Wd*(d-f))**2) + lam*np.sum((C@m)**2), f
    ph, f = phi(m, lam)
    hist.append(dict(it=0, m=m.copy(), rms=rms_rel(rhoa_obs, np.exp(f)), lam=lam, resp=np.exp(f)))
    for it in range(1, niter+1):
        ra, S = fw.response(np.exp(m), jac=True)
        f = np.log(ra); r = Wd*(d-f)
        Jw = S*Wd[:, None]
        H = Jw.T @ Jw + lam*CtC
        gvec = Jw.T @ r - lam*(CtC @ m)
        dm = np.linalg.solve(H, gvec)
        a = 1.0
        for _ in range(6):
            mn = m + a*dm
            phn, fn = phi(mn, lam)
            if phn < ph or a < 0.1: break
            a *= 0.5
        m, ph, f = mn, phn, fn
        hist.append(dict(it=it, m=m.copy(), rms=rms_rel(rhoa_obs, np.exp(f)), lam=lam, step=a, resp=np.exp(f), S=S))
        if verbose:
            print(f'  it {it:2d}  lam {lam:7.3f} step {a:.2f}  RMS {hist[-1]["rms"]:6.2f}%  rho [{np.exp(m).min():8.1f}, {np.exp(m).max():8.1f}]')
        lam = lam*lam_fac if lam_min is None else max(lam*lam_fac, lam_min)
    return hist

def invert_ip(g, S, ma_obs, relerr=0.10, abserr=0.2, lam=1.0, zw=1.0, upper=200.0):
    """Linearised IP inversion: ma = S m (S=dln(rho_a)/dln(rho) from DC model), m>=0, smoothness-constrained."""
    from scipy.optimize import lsq_linear
    err = np.maximum(relerr*ma_obs, abserr)
    W = 1.0/err
    C = g.roughness(zw)
    A = sp.vstack([sp.csr_matrix(S*W[:, None]), np.sqrt(lam)*C]).tocsr()
    b = np.concatenate([ma_obs*W, np.zeros(C.shape[0])])
    sol = lsq_linear(A, b, bounds=(0, upper), method='trf', lsmr_tol='auto', max_iter=200)
    m = sol.x
    pred = S @ m
    chi2 = np.mean(((ma_obs-pred)*W)**2)
    return m, pred, chi2

def envelope(g, df, factor=1.10, win=7.5, smooth=15.0):
    """Res2DInv-like display envelope: max depth (below local surface) supported by the data pseudo-depth (Edwards, 0.17*L)."""
    ze = 0.17*df.L.values; xm = df.xmid.values
    xs = np.arange(-2.5, g.xel[-1]+2.5+1e-9, 1.0)
    D = np.zeros_like(xs)
    for i, x in enumerate(xs):
        s = np.abs(xm - x) <= win
        D[i] = ze[s].max()*factor if s.any() else 0.0
    # smooth with moving average
    k = int(smooth); ker = np.ones(k)/k
    Dp = np.convolve(np.pad(D, (k//2, k//2), mode='edge'), ker, mode='valid')[:len(D)]
    return xs, np.maximum(Dp, 0)

def par_depth(g):
    """depth below local surface of each parameter-cell centre, and in-envelope mask helper"""
    z_surf = np.repeat(g.Z[g.ixc0+1+2*np.arange(g.nel), 0], g.nz)
    return z_surf - g.par_cz

def invert_ip2(g, S, ma, relerr=0.15, abserr=0.3, lam=0.3, zw=1.0, upper=300.0):
    from scipy.optimize import lsq_linear
    err = np.maximum(relerr*ma, abserr); W = 1.0/err
    C = g.roughness(zw).toarray()
    A = np.vstack([S*W[:, None], np.sqrt(lam)*C]); b = np.concatenate([ma*W, np.zeros(C.shape[0])])
    sol = lsq_linear(A, b, bounds=(0, upper), method='bvls', max_iter=3000)
    m = sol.x; pred = S@m
    return m, pred, err
