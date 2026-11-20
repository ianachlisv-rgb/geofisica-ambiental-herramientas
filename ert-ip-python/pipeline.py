import sys, pickle, time
from invert import *
from config import W

def flag_electrodes(df, mis_raw):
    """Electrodes whose potential-role data are systematically bad (IP>10 ms in >60% or |misfit|>20% in >=50%)"""
    flagged = {}
    am = np.abs(mis_raw)
    for e in range(41):
        pot = (df.M == e) | (df.N == e)
        n = pot.sum()
        if n < 10: continue
        f_ip = (df.ip[pot] > 10).mean(); f_rho = (am[pot.values] > 20).mean()
        if f_ip > 0.60 or f_rho >= 0.50:
            flagged[e] = dict(n=int(n), frac_ip10=float(f_ip), frac_mis20=float(f_rho), mean_ip=float(df.ip[pot].median()), mean_mis=float(am[pot.values].mean()))
    return flagged

def process_line(line, verbose=True):
    out = dict(line=line)
    g, fw, df = build(line)
    # pass 0: raw data, quick inversion to get misfits
    h0 = invert_dc(g, fw, df.rhoa.values, lam0=5, niter=4, verbose=False)
    mis0 = (df.rhoa.values - h0[-1]['resp'])/df.rhoa.values*100
    out.update(df_raw=df, rms_raw=h0[-1]['rms'], mis_raw=mis0)
    # A: systematic electrode problems
    fl = flag_electrodes(df, mis0)
    keepA = ~(df.M.isin(list(fl)) | df.N.isin(list(fl))).values
    out['flagged'] = fl
    # B: re-invert without flagged electrodes, remove remaining outliers
    gA, fwA, dfA = build(line, use=keepA)
    h1 = invert_dc(gA, fwA, dfA.rhoa.values, lam0=5, niter=4, verbose=False)
    misA = (dfA.rhoa.values - h1[-1]['resp'])/dfA.rhoa.values*100
    sig = 1.4826*np.median(np.abs(misA - np.median(misA))); thr = max(25.0, 3*sig)
    keepB_sub = np.abs(misA) <= thr
    keep = keepA.copy(); idxA = np.where(keepA)[0]; keep[idxA[~keepB_sub]] = False
    out.update(keep=keep, keepA=keepA, thr=thr, sig=sig, rms_afterA=h1[-1]['rms'], n_raw=len(df), n_A=int((~keepA).sum()), n_B=int((~keepB_sub).sum()))
    # C: final DC inversions (all iterates)
    g2, fw2, df2 = build(line, use=keep)
    h2 = invert_dc(g2, fw2, df2.rhoa.values, lam0=20, lam_fac=0.7, lam_min=2.0, niter=10, verbose=False)
    out.update(df=df2, hist=[dict(it=x['it'], m=x['m'], rms=x['rms'], lam=x['lam'], resp=x['resp']) for x in h2])
    if verbose:
        print(f'line {line}: raw RMS {h0[-1]["rms"]:.1f}% | flagged electrodes {list(fl)} -> removed {out["n_A"]} | outliers removed {out["n_B"]} (thr {thr:.0f}%) | kept {keep.sum()}/{len(keep)}')
        print('    RMS by iteration:', ' '.join(f'{x["rms"]:.1f}' for x in h2))
    return out

if __name__ == '__main__':
    R = {}
    for line in range(1, 7):
        R[line] = process_line(line)
    pickle.dump(R, open(W + 'dc_results2.pkl', 'wb'))
