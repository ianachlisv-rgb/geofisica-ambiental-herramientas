import sys, json
from plotlib import *
from scipy import ndimage
import matplotlib.patheffects as pe

TOPO_ELEV = None
def surf_xy(g): return g.xel, g.Z[g.ixc0+1+2*np.arange(g.nel), 0]

def annotate_zones(ax, g, rho, env, M, line):
    X, Z, V, zs, Dm = fine_section(g, rho, *env)
    v = V.filled(np.nan)
    xf = X[:, 0]; d = np.arange(0, 45.0, 0.25)
    # contours
    ax.contour(X, Z, V, levels=[2.0], colors='k', linewidths=1.6, linestyles='-')
    ax.contour(X, Z, V, levels=[np.log10(400)], colors='k', linewidths=1.6, linestyles='--')
    # strongly affected core (<30 ohm-m)
    ax.contour(X, Z, V, levels=[np.log10(30)], colors='#d000d0', linewidths=1.8, linestyles='-')
    # class labels at centroid of the largest connected region of each class
    lab = class_regions(V)
    names = {0: 'Capa blanda / residuos\n(< 100 Ω·m)', 1: 'Capa consolidada\n(100–400 Ω·m)', 2: 'Basamento\n(> 400 Ω·m)'}
    for k in (0, 1, 2):
        comp, n = ndimage.label(lab == k)
        if n == 0: continue
        sizes = ndimage.sum(np.ones_like(comp), comp, index=range(1, n+1))
        j = int(np.argmax(sizes)) + 1
        if sizes[j-1]*0.5*0.25 < 120: continue
        ii, jj = np.where(comp == j)
        # place label at the point of the component closest to its centroid
        ci, cj = ii.mean(), jj.mean()
        arrows_x = [v for v in (M.get('x_at_soft_base_max'), M.get('x_at_bed_shallowest')) if v is not None]
        pen = np.zeros(len(ii))
        for ax_ in arrows_x: pen += (np.abs(X[ii, jj] - ax_) < 24)*1e6
        idx = np.argmin(((ii-ci)*0.5)**2 + ((jj-cj)*0.25)**2 + pen)
        xx, zz = X[ii[idx], jj[idx]], Z[ii[idx], jj[idx]]
        t = ax.text(xx, zz, names[k], ha='center', va='center', fontsize=8.5, fontweight='bold', color='k',
                    bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='none', alpha=0.75))
    # dimension arrows: max thickness of soft layer, shallowest bedrock
    if M.get('x_at_soft_base_max') is not None:
        x0 = M['x_at_soft_base_max']; z0 = np.interp(x0, xf, zs)
        ax.annotate('', xy=(x0, z0-M['soft_base_max']), xytext=(x0, z0), arrowprops=dict(arrowstyle='<->', color='k', lw=1.4))
        ax.text(x0-1.5, z0-M['soft_base_max']*0.85, f"≈{M['soft_base_max']:.0f} m", fontsize=8, va='center', ha='right', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.85))
    if M.get('x_at_bed_shallowest') is not None:
        x0 = M['x_at_bed_shallowest']; z0 = np.interp(x0, xf, zs)
        ax.annotate('', xy=(x0, z0-M['bed_depth_min']), xytext=(x0, z0), arrowprops=dict(arrowstyle='<->', color='w', lw=1.4, path_effects=[pe.withStroke(linewidth=3, foreground='k')]))
        ax.text(x0-1.5, z0-M['bed_depth_min']*0.6, f"≈{M['bed_depth_min']:.0f} m", fontsize=8, va='center', ha='right', fontweight='bold', color='w',
                path_effects=[pe.withStroke(linewidth=2.2, foreground='k')])
    return X, Z, V, zs

def section_figure(line, F, R, M, fname, vexag=2.0, with_ip=False):
    g, fw, df = build(line, use=R[line]['keep'])
    env = envelope(g, df)
    nrows = 2 if with_ip else 1
    fig, axs = plt.subplots(nrows, 1, figsize=(11.5, 4.0*nrows+1.2), sharex=True)
    axs = np.atleast_1d(axs)
    ax = axs[0]
    X, Z, V, zs, Dm, cs = draw_section(ax, g, F[line]['rho'], env, 'rho')
    annotate_zones(ax, g, F[line]['rho'], env, M, line)
    xe, ze = surf_xy(g)
    ax.plot(xe, ze+0.3, 'v', color='k', ms=3.5, clip_on=False)
    ax.plot(np.arange(0, 200.1, 0.5), np.interp(np.arange(0, 200.1, 0.5), xe, ze), 'k-', lw=1.0)
    ttl = f"TKI {line} — Modelo de resistividad (iteración {SEL}, RMS = {F[line]['rms']:.1f} %)"
    ax.set_title(ttl, fontsize=11, loc='left', fontweight='bold')
    ax.set_ylabel('Elevación (m s.n.m.)')
    if with_ip:
        ax2 = axs[1]
        X2, Z2, V2, zs2, Dm2, cs2 = draw_section(ax2, g, F[line]['ip_m'], env, 'ip')
        ax2.contour(X, Z, V, levels=[2.0], colors='k', linewidths=1.1, linestyles='-')
        ax2.contour(X, Z, V, levels=[np.log10(400)], colors='k', linewidths=1.1, linestyles='--')
        ax2.plot(xe, ze+0.3, 'v', color='k', ms=3.5, clip_on=False)
        ax2.set_title(f"TKI {line} — Modelo de cargabilidad (IP), contornos de 100 y 400 Ω·m superpuestos", fontsize=11, loc='left', fontweight='bold')
        ax2.set_ylabel('Elevación (m s.n.m.)')
    axs[-1].set_xlabel('Distancia a lo largo del perfil (m)   [0 m = ' + ('extremo Este' if line <= 3 else 'extremo Sur') + ']')
    for a in axs:
        a.set_xlim(0, 200); lo = np.nanmin(Z) - 1; hi = ze.max() + 4
        a.set_ylim(lo, hi); a.set_aspect(vexag)
        a.grid(alpha=0.25, lw=0.5)
    # legends
    fig.subplots_adjust(right=0.88)
    cax = fig.add_axes([0.905, 0.55 if with_ip else 0.2, 0.014, 0.33 if with_ip else 0.6])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=RHO_NORM, cmap=RHO_CMAP), cax=cax, ticks=np.log10(RHO_LEVELS)); cb.ax.set_yticklabels([str(l) for l in RHO_LEVELS], fontsize=8); cb.set_label('ρ (Ω·m)', fontsize=9)
    if with_ip:
        cax2 = fig.add_axes([0.905, 0.1, 0.014, 0.33])
        cb2 = fig.colorbar(plt.cm.ScalarMappable(norm=IP_NORM, cmap=IP_CMAP), cax=cax2, ticks=IP_LEVELS); cb2.ax.set_yticklabels([str(l) for l in IP_LEVELS], fontsize=8); cb2.set_label('Cargabilidad (ms)', fontsize=9)
    fig.savefig(fname, dpi=170, bbox_inches='tight'); plt.close(fig)

SEL = 4
if __name__ == '__main__':
    F, R = load_all(); M = {int(k): v for k, v in json.load(open(W+'zone_metrics.json')).items()}
    for l in (1, 3, 5):
        section_figure(l, F, R, M[l], W+f'test_sec_{l}.png')
