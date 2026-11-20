import sys, pickle, json
from plotlib import *
from scipy import ndimage

def zone_metrics(line, F, R, dxf=0.5, ddf=0.25):
    g, fw, df = build(line, use=R[line]['keep'])
    env = envelope(g, df)
    X, Z, V, zs, Dm = fine_section(g, F[line]['rho'], *env, dxf=dxf, ddf=ddf)
    d = np.arange(0, 45.0, ddf)
    v = V.filled(np.nan)            # log10 rho, shape (nx, nd)
    xf = X[:, 0]
    nx, nd = v.shape
    cellA = dxf*ddf
    out = dict(line=line)
    # --- per-column depths
    soft_base = np.full(nx, np.nan); bed_top = np.full(nx, np.nan); full_soft = np.zeros(nx, bool)
    for i in range(nx):
        col = v[i]; ok = ~np.isnan(col)
        if not ok.any(): continue
        dmax = d[ok].max()
        soft = ok & (col < 2.0)
        if soft.any():
            last = np.where(soft)[0].max()
            soft_base[i] = d[last] + ddf/2
            if last >= np.where(ok)[0].max() - 2:      # soft up to the bottom of the investigated depth
                full_soft[i] = True
        else:
            soft_base[i] = 0.0
        bed = ok & (col >= np.log10(400))
        if bed.any(): bed_top[i] = d[np.where(bed)[0].min()]
    valid = ~np.isnan(soft_base)
    out['x_cov'] = [float(xf[valid].min()), float(xf[valid].max())]
    out['dmax_env'] = float(Dm.max())
    out['soft_base_mean'] = float(np.nanmean(soft_base[~full_soft])) if (~full_soft & valid).any() else None
    out['soft_base_min'] = float(np.nanmin(soft_base[valid & ~full_soft])) if (~full_soft & valid).any() else None
    out['soft_base_max'] = float(np.nanmax(soft_base[valid & ~full_soft])) if (~full_soft & valid).any() else None
    out['x_at_soft_base_max'] = float(xf[np.nanargmax(np.where(full_soft, np.nan, soft_base))]) if (~full_soft & valid).any() else None
    out['pct_cols_soft_to_bottom'] = float(full_soft[valid].mean()*100)
    out['bed_present_cols_pct'] = float((~np.isnan(bed_top)).sum()/valid.sum()*100)
    if (~np.isnan(bed_top)).any():
        xb = xf[~np.isnan(bed_top)]
        out['bed_x_range'] = [float(xb.min()), float(xb.max())]
        out['bed_depth_min'] = float(np.nanmin(bed_top)); out['bed_depth_mean'] = float(np.nanmean(bed_top)); out['bed_depth_max'] = float(np.nanmax(bed_top))
        out['x_at_bed_shallowest'] = float(xf[np.nanargmin(bed_top)])
    # --- areas
    tot = np.sum(~np.isnan(v))*cellA
    A_soft = np.sum(v < 2.0)*cellA; A_con = np.sum((v >= 2.0) & (v < np.log10(400)))*cellA; A_bed = np.sum(v >= np.log10(400))*cellA
    out.update(area_total=float(tot), area_soft=float(A_soft), area_cons=float(A_con), area_bed=float(A_bed))
    # --- core of strongly affected zone (<30 ohm-m): connected components, keep those > 40 m2
    lab, n = ndimage.label(np.nan_to_num(v, nan=9) < np.log10(30))
    comps = []
    for k in range(1, n+1):
        m = lab == k; area = m.sum()*cellA
        if area < 40: continue
        ii, jj = np.where(m)
        comps.append(dict(x0=float(xf[ii.min()]), x1=float(xf[ii.max()]), d0=float(d[jj.min()]), d1=float(d[jj.max()]+ddf), area=float(area), rho_min=float(10**np.nanmin(v[m]))))
    comps.sort(key=lambda c: -c['area'])
    out['core30'] = comps
    out['rho_min'] = float(10**np.nanmin(v)); out['rho_max'] = float(10**np.nanmax(v))
    out['A_core30'] = float(np.sum(v < np.log10(30))*cellA)
    # IP stats by zone (nearest-cell mapping from IP parameter model)
    Xi, Zi, Vi, _, _ = fine_section(g, F[line]['ip_m'], *env, dxf=dxf, ddf=ddf, log=False)
    vi = Vi.filled(np.nan)
    for name, msk in (('soft', v < 2.0), ('cons', (v >= 2.0) & (v < np.log10(400))), ('bed', v >= np.log10(400)), ('core30', v < np.log10(30))):
        sel = msk & ~np.isnan(vi)
        out[f'ip_{name}_mean'] = float(np.nanmean(vi[sel])) if sel.any() else None
    out['ip_max'] = float(np.nanmax(vi)); out['ip_min'] = float(np.nanmin(vi))
    ii, jj = np.where(vi == np.nanmax(vi)); out['ip_max_at'] = [float(xf[ii[0]]), float(d[jj[0]])]
    # IP high zone: > mean + 1 std of the line (connected)
    thr = np.nanmean(vi) + 1.0*np.nanstd(vi)
    lab, n = ndimage.label(np.nan_to_num(vi, nan=0) > thr)
    hi = []
    for k in range(1, n+1):
        m = lab == k; area = m.sum()*cellA
        if area < 40: continue
        ii, jj = np.where(m)
        hi.append(dict(x0=float(xf[ii.min()]), x1=float(xf[ii.max()]), d0=float(d[jj.min()]), d1=float(d[jj.max()]+ddf), area=float(area), ip_max=float(np.nanmax(vi[m])), rho_med=float(10**np.nanmedian(v[m]))))
    hi.sort(key=lambda c: -c['area']); out['ip_high'] = hi; out['ip_thr'] = float(thr)
    out['ip_low_x'] = None
    # correlation (log rho, IP) in the covered cells
    sel = ~np.isnan(v) & ~np.isnan(vi)
    out['corr_logrho_ip'] = float(np.corrcoef(v[sel], vi[sel])[0, 1])
    return out

if __name__ == '__main__':
    F, R = load_all()
    M = {l: zone_metrics(l, F, R) for l in range(1, 7)}
    json.dump(M, open(W+'zone_metrics.json', 'w'), indent=1)
    for l, m in M.items():
        print(f"--- TKI {l}: soft base depth mean {m['soft_base_mean']}, min {m['soft_base_min']}, max {m['soft_base_max']} at x={m['x_at_soft_base_max']}; cols soft to bottom {m['pct_cols_soft_to_bottom']:.0f}%; bedrock cols {m['bed_present_cols_pct']:.0f}% depth {m.get('bed_depth_min')}-{m.get('bed_depth_max')}")
        print(f"    areas m2: total {m['area_total']:.0f} soft {m['area_soft']:.0f} ({m['area_soft']/m['area_total']*100:.0f}%) cons {m['area_cons']:.0f} ({m['area_cons']/m['area_total']*100:.0f}%) bed {m['area_bed']:.0f} ({m['area_bed']/m['area_total']*100:.0f}%) core<30 {m['A_core30']:.0f}")
        print('    core30:', [(round(c['x0']), round(c['x1']), round(c['d0'],1), round(c['d1'],1), round(c['area']), round(c['rho_min'],1)) for c in m['core30'][:4]])
        print(f"    IP mean soft {m['ip_soft_mean']:.2f} cons {m['ip_cons_mean']} bed {m['ip_bed_mean']} core30 {m['ip_core30_mean']} | max {m['ip_max']:.2f} at {m['ip_max_at']} | corr {m['corr_logrho_ip']:.2f}")
        print('    IP high:', [(round(c['x0']), round(c['x1']), round(c['d0'],1), round(c['d1'],1), round(c['area']), round(c['ip_max'],1), round(c['rho_med'])) for c in m['ip_high'][:3]], 'thr', round(m['ip_thr'],2))
