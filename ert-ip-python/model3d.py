"""Construccion del modelo 3D (equivalente a Voxler / Oasis Montaj) a partir de las 6 secciones 2D.
Salida: work/model3d.pkl con
  - lines[i]: dict(E, N, Z, d, logrho, ip, mask) secciones finas georreferenciadas (E,N desde GPS de cada electrodo)
  - vol: malla regular (E,N,Z) con log10(rho) e IP interpolados (IDW), mascara de cobertura y DEM
"""
import sys, pickle
from plotlib import *
from scipy.spatial import cKDTree
from scipy.interpolate import griddata, RegularGridInterpolator
import pandas as pd

TOPO = load_topo()


def line_sections(F, R, dxf=1.0, ddf=0.5):
    out = {}
    for line in range(1, 7):
        g, fw, df = build(line, use=R[line]['keep'])
        env = envelope(g, df)
        X, Z, V, zs, Dm = fine_section(g, F[line]['rho'], *env, dxf=dxf, ddf=ddf, log=True)
        Xi, Zi, Vi, _, _ = fine_section(g, F[line]['ip_m'], *env, dxf=dxf, ddf=ddf, log=False)
        t = TOPO[line]
        xe = t['electrodo_x_m'].values.astype(float)
        E = np.interp(X[:, 0], xe, t['Este_m'].values.astype(float))
        N = np.interp(X[:, 0], xe, t['Norte_m'].values.astype(float))
        d = np.arange(0, 45.0, ddf)
        out[line] = dict(x=X[:, 0], E=E, N=N, zs=zs, d=d, Z=Z, logrho=np.ma.filled(V, np.nan), ip=np.ma.filled(Vi, np.nan), Dm=Dm)
    return out


def build_volume(L, dh=5.0, dd=1.0, rad_h=45.0, rad_d=2.0, power=2.0, step_x=2.0, step_d=1.0):
    """Interpolacion 3D (IDW anisotropico) en coordenadas (E, N, profundidad bajo la superficie de cada perfil).
    Se usa la profundidad y no la cota porque las cotas GPS de los perfiles E-O y N-S difieren hasta 14 m en los cruces."""
    from scipy.ndimage import gaussian_filter
    pts, lr, ipv = [], [], []
    for line, s in L.items():
        ix = np.arange(0, len(s['x']), int(step_x / (s['x'][1] - s['x'][0])))
        id_ = np.arange(0, len(s['d']), int(step_d / (s['d'][1] - s['d'][0])))
        for i in ix:
            for j in id_:
                v = s['logrho'][i, j]
                if np.isnan(v): continue
                pts.append((s['E'][i], s['N'][i], s['d'][j])); lr.append(v); ipv.append(s['ip'][i, j])
    pts = np.array(pts); lr = np.array(lr); ipv = np.array(ipv)
    e_all = np.concatenate([TOPO[l]['Este_m'].values for l in L]).astype(float)
    n_all = np.concatenate([TOPO[l]['Norte_m'].values for l in L]).astype(float)
    z_all = np.concatenate([TOPO[l]['elevacion_m'].values for l in L]).astype(float)
    E0, E1 = pts[:, 0].min() - 10, pts[:, 0].max() + 10
    N0, N1 = pts[:, 1].min() - 10, pts[:, 1].max() + 10
    Eg = np.arange(E0, E1 + dh, dh); Ng = np.arange(N0, N1 + dh, dh); Dg = np.arange(0, 45.0 + dd, dd)
    EE, NN = np.meshgrid(Eg, Ng, indexing='ij')
    DEM = griddata((e_all, n_all), z_all, (EE, NN), method='linear')
    DEMn = griddata((e_all, n_all), z_all, (EE, NN), method='nearest')
    DEM = np.where(np.isnan(DEM), DEMn, DEM)
    DEM_s = gaussian_filter(DEM, sigma=2.0, mode='nearest')      # MDT suavizado (solo para visualizacion)
    prof_xy = np.vstack([np.c_[s['E'], s['N']] for s in L.values()])
    dist_h, _ = cKDTree(prof_xy).query(np.c_[EE.ravel(), NN.ravel()]); dist_h = dist_h.reshape(EE.shape)
    sc = np.array([1 / rad_h, 1 / rad_h, 1 / rad_d])
    tree = cKDTree(pts * sc)
    G = np.stack(np.meshgrid(Eg, Ng, Dg, indexing='ij'), -1).reshape(-1, 3)
    dhflat = np.repeat(dist_h[:, :, None], len(Dg), 2).reshape(-1)
    gi = np.where(dhflat <= rad_h)[0]
    dist, ii = tree.query(G[gi] * sc, k=12, distance_upper_bound=1.0)
    w = 1.0 / np.maximum(dist, 0.02) ** power; w[~np.isfinite(dist)] = 0
    iic = np.where(np.isfinite(dist), ii, 0); wsum = w.sum(1); valid = wsum > 0
    LR = np.full(len(G), np.nan); IPg = np.full(len(G), np.nan)
    LR[gi[valid]] = (w * lr[iic]).sum(1)[valid] / wsum[valid]
    IPg[gi[valid]] = (w * np.nan_to_num(ipv[iic])).sum(1)[valid] / wsum[valid]
    shp = (len(Eg), len(Ng), len(Dg))
    return dict(Eg=Eg, Ng=Ng, Dg=Dg, DEM=DEM_s, DEM_raw=DEM, dist_h=dist_h, logrho=LR.reshape(shp), ip=IPg.reshape(shp), dh=dh, dd=dd, rad_h=rad_h)


if __name__ == '__main__':
    F, R = load_all()
    L = line_sections(F, R)
    V = build_volume(L)
    pickle.dump(dict(lines=L, vol=V), open(W + 'model3d.pkl', 'wb'))
    lr = V['logrho']
    print('grid', lr.shape, 'validos', np.isfinite(lr).sum(), 'DEM', np.nanmin(V['DEM']), np.nanmax(V['DEM']))
    cell = V['dh'] ** 2 * V['dd']
    for thr in (100, 400):
        n = (lr < np.log10(thr)).sum() if thr == 100 else (lr >= np.log10(thr)).sum()
        print(thr, n * cell, 'm3')
