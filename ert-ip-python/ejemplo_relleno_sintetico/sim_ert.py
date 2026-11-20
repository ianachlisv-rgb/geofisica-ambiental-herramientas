"""Simulacion SINTETICA de ERT sobre un relleno (modelo conceptual). No son datos de campo."""
import numpy as np, pickle
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
DATOS = os.path.join(HERE, 'datos'); FIGS = os.path.join(HERE, 'figuras')
os.makedirs(DATOS, exist_ok=True); os.makedirs(FIGS, exist_ok=True)
from ert2d import Grid, Forward

NEL, SP = 48, 5.0
def ws_array(nel=NEL):
    q = []
    for a, nmax in [(1, 8), (2, 6), (3, 6), (4, 4)]:
        for n in range(1, nmax + 1):
            for p1 in range(n * a, nel - a - n * a):
                q.append((p1 - n * a, p1 + a + n * a, p1, p1 + a))
    return np.array(q)          # A,B,M,N

def kfac(A, B, M, N, x):
    r = lambda i, j: abs(x[i] - x[j])
    return 2 * np.pi / (1 / r(A, M) - 1 / r(B, M) - 1 / r(A, N) + 1 / r(B, N))

def truth(x, d):
    """Modelo verdadero (ohm.m). x: distancia (m), d: profundidad (m)."""
    rho = np.where(d < 28, 90.0, 300.0)                 # aluvion/colubion sobre roca
    rho = np.where(d < 1.5, 120.0, rho)                 # cubierta seca
    waste = (x > 55) & (x < 165) & (d > 1.5) & (d < 14)
    rho = np.where(waste, 30.0, rho)                    # cuerpo de residuos
    plume = (x > 120) & (x < 215) & (d > 10) & (d < 24) & ~waste
    rho = np.where(plume, 6.0, rho)                     # lixiviado bajo y al E
    sludge = (x > 85) & (x < 105) & (d > 3) & (d < 7)
    rho = np.where(sludge, 8.0, rho)                    # bolsa de lodos salinos
    return rho

if __name__ == '__main__':
    rng = np.random.default_rng(7)
    x = np.arange(NEL) * SP
    q = ws_array(); A, B, M, N = q.T
    k = np.array([kfac(*r, x) for r in q])
    print('mediciones', len(q))
    # --- directo con malla fina (distinta de la de inversion)
    fine = [0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.4, 1.6, 1.8, 2.0, 2.3, 2.6, 3.0, 3.4, 3.9, 4.4, 5.0, 5.6, 6.3]
    gt = Grid(np.zeros(NEL), layer_h=fine)
    fwt = Forward(gt, A, B, M, N, k)
    gtf = Grid(np.zeros(NEL), layer_h=fine); fwf = Forward(gtf, A, B, M, N, k)
    fwt.corr = 100.0 / fwf.response(np.full(gtf.npar, 100.))
    d = -gt.par_cz
    rho_t = truth(gt.par_cx, d)
    rhoa = fwt.response(rho_t)
    rhoa_n = rhoa * np.exp(rng.normal(0, 0.03, len(rhoa)))
    print('rhoa', rhoa_n.min(), rhoa_n.max())
    pickle.dump(dict(q=q, k=k, rhoa=rhoa_n, rhoa_clean=rhoa, x=x, fine=fine), open(os.path.join(DATOS,'sim_data.pkl'), 'wb'))
