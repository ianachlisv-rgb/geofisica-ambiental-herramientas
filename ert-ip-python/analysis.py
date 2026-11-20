import sys, pickle
from invert import *
import pandas as pd
from config import W, ENTRADA, OUT, HDIR, OUTF, PF, load_topo

def class_fractions(rho, vol):
    return [vol[rho < 100].sum()/vol.sum(), vol[(rho >= 100) & (rho < 400)].sum()/vol.sum(), vol[rho >= 400].sum()/vol.sum()]

def iteration_table(line, r, g, df):
    xs, Dm = envelope(g, df); dpar = par_depth(g)
    inside = dpar <= np.interp(g.par_cx, xs, Dm)
    vol = (np.tile(g.layer_h, g.nel)*g.sp)[inside]
    rows = []; prev = None
    ra_max = r['df'].rhoa.max()
    for h in r['hist'][1:]:
        rho = np.exp(h['m'])[inside]
        f = class_fractions(rho, vol)
        rows.append(dict(linea=line, iteracion=h['it'], RMS=h['rms'], dRMS=np.nan if prev is None else (prev-h['rms'])/prev*100,
                         rho_min=rho.min(), rho_p5=np.percentile(rho, 5), rho_med=np.median(rho), rho_p95=np.percentile(rho, 95), rho_max=rho.max(),
                         pct_blando=f[0]*100, pct_consol=f[1]*100, pct_basamento=f[2]*100, rhoa_max_datos=ra_max))
        prev = h['rms']
    return pd.DataFrame(rows), inside

def select_iteration(t):
    """criterios: (a) dRMS<5%, (b) rho_max<=2500, (c) |d p95|<15% respecto a la iteracion anterior, (d) rho_max >= 0.95*rhoa_max de los datos"""
    t = t.copy()
    t['dp95'] = t.rho_p95.pct_change()*100
    ok = (t.dRMS < 5) & (t.rho_max <= 2500) & (t.dp95.abs() < 15) & (t.rho_max >= 0.95*t.rhoa_max_datos) & (t.iteracion >= 3)
    if ok.any():
        return int(t[ok].iteracion.iloc[0]), t
    ok2 = (t.dRMS < 5) & (t.rho_max <= 2500) & (t.iteracion >= 3)
    return (int(t[ok2].iteracion.iloc[0]) if ok2.any() else int(t.iteracion.iloc[-1])), t

if __name__ == '__main__':
    R = pickle.load(open(W+'dc_results2.pkl', 'rb'))
    tabs = []
    for line in range(1, 7):
        r = R[line]; g, fw, df = build(line, use=r['keep'])
        t, inside = iteration_table(line, r, g, df)
        sel, t = select_iteration(t)
        r['inside'] = inside; r['sel'] = sel; tabs.append(t)
        print(f'LINE {line}: selected iteration {sel}')
        print(t.round(1).drop(columns=['linea', 'rhoa_max_datos']).to_string(index=False))
    pickle.dump(R, open(W+'dc_results2.pkl', 'wb'))
    pd.concat(tabs).to_csv(W+'tabla_iteraciones.csv', index=False)
