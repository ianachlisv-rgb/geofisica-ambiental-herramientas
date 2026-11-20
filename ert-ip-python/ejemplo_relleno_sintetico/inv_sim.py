import numpy as np, pickle
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
DATOS = os.path.join(HERE, 'datos'); FIGS = os.path.join(HERE, 'figuras')
os.makedirs(DATOS, exist_ok=True); os.makedirs(FIGS, exist_ok=True)
from ert2d import Grid, Forward
from invert_lib import invert_dc, rms_rel
from sim_ert import truth, NEL
D = pickle.load(open(os.path.join(DATOS,'sim_data.pkl'), 'rb'))
A, B, M, N = D['q'].T
g = Grid(np.zeros(NEL)); fw = Forward(g, A, B, M, N, D['k'])
gf = Grid(np.zeros(NEL)); fwf = Forward(gf, A, B, M, N, D['k'])
fw.corr = 100.0 / fwf.response(np.full(gf.npar, 100.))
h = invert_dc(g, fw, D['rhoa'], relerr=0.03, lam0=10., lam_fac=0.8, lam_min=1.0, niter=8)
best = h[-1]
pickle.dump(dict(m=best['m'], rms=[x['rms'] for x in h], resp=best['resp']), open(os.path.join(DATOS,'sim_inv.pkl'), 'wb'))
print('RMS final', best['rms'])
