import sys, pickle
from invert import *
from config import W, ENTRADA, OUT, HDIR, OUTF, PF, load_topo
SEL = 4
IP_REL, IP_ABS, IP_LAM = 0.10, 0.7, 0.3
R = pickle.load(open(W+'dc_results2.pkl', 'rb'))
F = {}
for line in range(1, 7):
    r = R[line]; g, fw, df = build(line, use=r['keep'])
    m = r['hist'][SEL]['m']; ra, S = fw.response(np.exp(m), jac=True)
    ma = df.ip.values; keep = np.ones(len(ma), bool)
    for rnd in range(3):
        mm, pred, err = invert_ip2(g, S[keep], ma[keep], relerr=IP_REL, abserr=IP_ABS, lam=IP_LAM)
        z = (ma - S@mm)/np.maximum(IP_REL*ma, IP_ABS)
        zs = 1.4826*np.median(np.abs(z[keep]-np.median(z[keep])))
        newkeep = np.abs(z) <= max(3.5, 3*zs)
        if (newkeep == keep).all(): break
        keep = newkeep
    mm, pred, err = invert_ip2(g, S[keep], ma[keep], relerr=IP_REL, abserr=IP_ABS, lam=IP_LAM)
    zfin = (ma[keep]-pred)/err
    ip_rms_abs = np.sqrt(np.mean((ma[keep]-pred)**2))
    F[line] = dict(grid=None, df=df, m_rho=m, rho=np.exp(m), resp=r['hist'][SEL]['resp'], rms=r['hist'][SEL]['rms'], S=S, ip_keep=keep,
                   ip_m=mm, ip_pred_full=S@mm, ip_rms_abs=ip_rms_abs, ip_chi2=np.mean(zfin**2), n_ip_removed=int((~keep).sum()), ip_obs=ma)
    print(f'line {line}: DC it {SEL} RMS {F[line]["rms"]:.1f}% | IP: kept {keep.sum()}/{len(keep)} (removed {(~keep).sum()}), RMS abs {ip_rms_abs:.2f} ms, chi2 {F[line]["ip_chi2"]:.2f}, m in [{mm.min():.2f}, {mm.max():.1f}] ms')
pickle.dump(F, open(W+'final.pkl', 'wb'))
