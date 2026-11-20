import sys, json
from plotlib import *
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.path import Path as MPath
from scipy.spatial import ConvexHull
import pandas as pd

M = pickle.load(open(W + 'model3d.pkl', 'rb')); V = M['vol']; L = M['lines']
TOPO = load_topo()
Eg, Ng, Dg = V['Eg'], V['Ng'], V['Dg']; dh, dz = V['dh'], V['dd']
LR, IPV, DEM = V['logrho'], V['ip'], V['DEM']
EE, NN = np.meshgrid(Eg, Ng, indexing='ij')
LINECOL = {1: '#e6194b', 2: '#f58231', 3: '#9a6324', 4: '#3cb44b', 5: '#4363d8', 6: '#911eb4'}
E0, N0 = Eg[0], Ng[0]


# ------------------------------------------------------------------------------------------------
def soft_maps():
    """espesor de la capa blanda (profundidad al primer valor >=100 Ohm.m) y profundidad al techo del basamento (>=400) por columna"""
    nE, nN, nD = LR.shape
    th = np.full((nE, nN), np.nan); bd = np.full((nE, nN), np.nan); bottom = np.zeros((nE, nN), bool)
    for i in range(nE):
        for j in range(nN):
            col = LR[i, j, :]; k = np.where(np.isfinite(col))[0]
            if len(k) == 0: continue
            v = col[k]; dd = Dg[k]
            below = np.where(v >= 2.0)[0]
            if len(below): th[i, j] = dd[below[0]]
            else: th[i, j] = dd[-1]; bottom[i, j] = True      # cota inferior: no se alcanza 100 Ohm.m dentro de la profundidad investigada
            b = np.where(v >= np.log10(400))[0]
            if len(b): bd[i, j] = dd[b[0]]
    return th, bd, bottom


def hull_mask():
    pts = np.vstack([np.c_[s['E'], s['N']] for s in L.values()])
    h = ConvexHull(pts); poly = pts[h.vertices]
    inside = MPath(poly).contains_points(np.c_[EE.ravel(), NN.ravel()]).reshape(EE.shape)
    return inside, poly, h.volume


def volume_metrics():
    inside, poly, harea = hull_mask()
    th, bd, bottom = soft_maps()
    out = {'hull_area_m2': float(harea), 'cell_m3': dh*dh*dz}
    for name, mask in (('envolvente_perfiles', inside), ('radio_15m', V['dist_h'] <= 15), ('radio_25m', V['dist_h'] <= 25), ('radio_45m_todo', V['dist_h'] <= 45)):
        m3 = mask[:, :, None]
        out[name] = dict(area_m2=float(mask.sum()*dh*dh),
                         vol_rho_lt100=float(np.nansum((LR < 2.0) & m3)*dh*dh*dz),
                         vol_rho_lt70=float(np.nansum((LR < np.log10(70)) & m3)*dh*dh*dz),
                         vol_rho_lt30=float(np.nansum((LR < np.log10(30)) & m3)*dh*dh*dz),
                         vol_100_400=float(np.nansum((LR >= 2.0) & (LR < np.log10(400)) & m3)*dh*dh*dz),
                         vol_gt400=float(np.nansum((LR >= np.log10(400)) & m3)*dh*dh*dz),
                         espesor_blando_medio=float(np.nanmean(th[mask])),
                         espesor_blando_mediana=float(np.nanmedian(th[mask])),
                         pct_columnas_blando_hasta_el_fondo=float(100*bottom[mask].mean()),
                         prisma_area_x_espesor=float(mask.sum()*dh*dh*np.nanmean(th[mask])))
    json.dump(out, open(W + 'vol3d.json', 'w'), indent=1)
    return out, th, bd, bottom, inside, poly


# ------------------------------------------------------------------------------------------------
def fence(ax, which='rho', stride=2):
    for line, s in L.items():
        x, E, N, Z = s['x'], s['E'], s['N'], s['Z']
        val = s['logrho'] if which == 'rho' else s['ip']
        sl = (slice(None, None, stride), slice(None, None, stride))
        Es, Ns = np.repeat(E[::stride, None], Z[sl].shape[1], 1), np.repeat(N[::stride, None], Z[sl].shape[1], 1)
        Zs, Vs = Z[sl], val[sl]
        # colores por celda
        vc = 0.25*(Vs[:-1, :-1] + Vs[1:, :-1] + Vs[:-1, 1:] + Vs[1:, 1:])
        if which == 'rho':
            idx = np.digitize(vc, np.log10(RHO_LEVELS[1:-1])); cols = np.array([matplotlib.colors.to_rgba(c) for c in RHO_COLORS])[idx]
        else:
            idx = np.digitize(vc, IP_LEVELS[1:-1]); cols = np.array([matplotlib.colors.to_rgba(c) for c in IP_COLORS])[idx]
        cols[~np.isfinite(vc)] = (0, 0, 0, 0)
        ax.plot_surface(Es - E0, Ns - N0, Zs, facecolors=cols, rstride=1, cstride=1, shade=False, linewidth=0, antialiased=False)
        ax.plot(E - E0, N - N0, s['zs'] + 0.3, color='k', lw=1.2)
        ax.text(E[0] - E0, N[0] - N0, s['zs'][0] + 8, f'TKI{line}', fontsize=8, fontweight='bold', ha='center')


def style3d(ax, view, vexag=2.0):
    ax.view_init(elev=view[0], azim=view[1])
    ax.set_box_aspect((Eg[-1]-Eg[0], Ng[-1]-Ng[0], vexag*50), zoom=1.12)
    ax.set_xlabel('Este − %d (m)' % E0, fontsize=8, labelpad=2); ax.set_ylabel('Norte − %d (m)' % N0, fontsize=8, labelpad=2)
    ax.set_zlabel('Elevación (m)', fontsize=8, labelpad=2)
    ax.tick_params(labelsize=7, pad=0)
    ax.set_xlim(0, Eg[-1]-E0); ax.set_ylim(0, Ng[-1]-N0); ax.set_zlim(52, 102)
    ax.xaxis.pane.set_alpha(0.05); ax.yaxis.pane.set_alpha(0.05); ax.zaxis.pane.set_alpha(0.05)


def fig_fence():
    for which in ('rho', 'ip'):
        fig = plt.figure(figsize=(16, 7.6))
        for k, view in enumerate(((24, -50), (24, -130))):
            ax = fig.add_subplot(1, 2, k+1, projection='3d')
            fence(ax, which); style3d(ax, view)
            ax.set_title(f'Vista desde el {"SE" if k == 0 else "SO"}', fontsize=9)
        fig.subplots_adjust(left=0.0, right=1.0, top=0.97, bottom=0.12, wspace=0.0)
        cax = fig.add_axes([0.3, 0.07, 0.4, 0.022])
        (rho_legend if which == 'rho' else ip_legend)(fig, cax=cax)
        fig.suptitle('Diagrama de cercas (fence) de las 6 secciones ' + ('de resistividad' if which == 'rho' else 'de cargabilidad') +
                     ' georreferenciadas (E, N, elevación GPS) – exageración vertical ×2', fontsize=11)
        fig.savefig(OUTF + ('fig12_3D_cercas_resistividad.png' if which == 'rho' else 'fig12b_3D_cercas_cargabilidad.png'), dpi=160, bbox_inches='tight')
        plt.close(fig)


# ------------------------------------------------------------------------------------------------
def depth_volume(vol, d):
    """corte horizontal a profundidad d bajo la superficie (interpolacion lineal entre capas)"""
    j = np.searchsorted(Dg, d); j0, j1 = max(j-1, 0), min(j, len(Dg)-1)
    if j0 == j1: return vol[:, :, j0]
    t = (d - Dg[j0]) / (Dg[j1] - Dg[j0])
    return (1-t)*vol[:, :, j0] + t*vol[:, :, j1]


def draw_profiles(ax, annotate=True):
    for line, s in L.items():
        ax.plot(s['E'], s['N'], ':', color='#222222', lw=1.1)
        ax.plot(s['E'][[0, -1]], s['N'][[0, -1]], 'k.', ms=3)
        if annotate:
            ax.text(s['E'][0], s['N'][0], f' TKI{line}', fontsize=7.5, fontweight='bold', va='center', ha='left' if line > 3 else 'left',
                    bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='none', alpha=0.7))


def fig_slices():
    depths = [2, 5, 10, 15, 20, 30]
    for which in ('rho', 'ip'):
        fig, axs = plt.subplots(2, 3, figsize=(15, 9.3), sharex=True, sharey=True)
        for ax, d in zip(axs.ravel(), depths):
            if which == 'rho':
                S = depth_volume(LR, d)
                ax.contourf(EE, NN, S, levels=np.log10(RHO_LEVELS), colors=RHO_COLORS, extend='both')
                ax.contour(EE, NN, S, levels=[2.0], colors='k', linewidths=1.2)
                ax.contour(EE, NN, S, levels=[np.log10(400)], colors='k', linewidths=1.2, linestyles='--')
            else:
                S = depth_volume(IPV, d)
                ax.contourf(EE, NN, S, levels=IP_LEVELS, colors=IP_COLORS, extend='both')
            draw_profiles(ax, annotate=(d == depths[0]))
            ax.set_title(f'Profundidad {d} m bajo la superficie', fontsize=10)
            ax.set_aspect('equal'); ax.tick_params(labelsize=7)
        for ax in axs[1]: ax.set_xlabel('Este RSO (m)', fontsize=8)
        for ax in axs[:, 0]: ax.set_ylabel('Norte RSO (m)', fontsize=8)
        cax = fig.add_axes([0.3, 0.035, 0.4, 0.018])
        (rho_legend if which == 'rho' else ip_legend)(fig, cax=cax)
        extra = '  (línea continua: 100 Ω·m, discontinua: 400 Ω·m)' if which == 'rho' else ''
        fig.suptitle('Cortes horizontales a profundidad constante – ' + ('resistividad' if which == 'rho' else 'cargabilidad') + extra, fontsize=11)
        fig.subplots_adjust(top=0.93, bottom=0.11, hspace=0.12, wspace=0.05)
        fig.savefig(OUTF + ('fig13_cortes_profundidad_resistividad.png' if which == 'rho' else 'fig13b_cortes_profundidad_cargabilidad.png'), dpi=150, bbox_inches='tight')
        plt.close(fig)


# ------------------------------------------------------------------------------------------------
def iso_mesh(level, high_inside):
    """isosuperficie log10(rho)=level en (E,N,d); el cuerpo se cierra con relleno 'exterior' en los bordes. Devuelve vertices en (E, N, cota)."""
    from skimage import measure
    from scipy.interpolate import RegularGridInterpolator
    A = LR.copy(); out = np.isnan(A)
    A[out] = -9.0 if high_inside else 9.0
    A = np.pad(A, 1, mode='constant', constant_values=(-9.0 if high_inside else 9.0))
    verts, faces, _, _ = measure.marching_cubes(A, level=level, spacing=(dh, dh, dz))
    verts = verts + np.array([Eg[0]-dh, Ng[0]-dh, Dg[0]-dz])
    fdem = RegularGridInterpolator((Eg, Ng), DEM, bounds_error=False, fill_value=None)
    z = fdem(verts[:, :2]) - np.maximum(verts[:, 2], 0)
    return np.c_[verts[:, 0], verts[:, 1], z], faces


def fig_iso():
    fig = plt.figure(figsize=(16, 7.6))
    meshes = [(2.0, '#1f9bd7', 0.22, False), (np.log10(30), '#e000e0', 0.95, False), (np.log10(400), '#8b4513', 0.5, True)]
    for k, view in enumerate(((26, -50), (26, -130))):
        ax = fig.add_subplot(1, 2, k+1, projection='3d')
        for lev, col, alpha, high in meshes:
            v, f = iso_mesh(lev, high)
            v2 = v.copy(); v2[:, 0] -= E0; v2[:, 1] -= N0
            ax.add_collection3d(Poly3DCollection(v2[f], facecolor=col, edgecolor='none', alpha=alpha, linewidths=0))
        for line, s in L.items():
            ax.plot(s['E'] - E0, s['N'] - N0, s['zs'] + 0.5, color='k', lw=1.3)
            ax.text(s['E'][0] - E0, s['N'][0] - N0, s['zs'][0] + 6, f'TKI{line}', fontsize=8, fontweight='bold', ha='center')
        style3d(ax, view)
        ax.set_title(f'Vista desde el {"SE" if k == 0 else "SO"}', fontsize=9)
    from matplotlib.patches import Patch
    fig.subplots_adjust(left=0.0, right=1.0, top=0.97, bottom=0.1, wspace=0.0)
    fig.legend(handles=[Patch(fc='#1f9bd7', alpha=0.5, label='ρ < 100 Ω·m (residuos / capa blanda)'),
                        Patch(fc='#e000e0', alpha=0.95, label='ρ < 30 Ω·m (núcleo más afectado)'),
                        Patch(fc='#8b4513', alpha=0.6, label='ρ ≥ 400 Ω·m (basamento)')], loc='lower center', ncol=3, fontsize=9, frameon=False)
    fig.suptitle('Isosuperficies de resistividad del modelo 3D (exageración vertical ×2)', fontsize=11, y=0.995)
    fig.savefig(OUTF + 'fig14_3D_isosuperficies.png', dpi=160, bbox_inches='tight')
    plt.close(fig)


# ------------------------------------------------------------------------------------------------
def fig_thickness(th, bd, inside, poly):
    fig, axs = plt.subplots(1, 2, figsize=(14, 6.4), sharex=True, sharey=True)
    cov = V['dist_h'] <= 35
    T = np.where(cov, th, np.nan); B = np.where(cov, bd, np.nan)
    lev = np.arange(0, 32, 2)
    c0 = axs[0].contourf(EE, NN, T, levels=lev, cmap='YlOrRd', extend='max')
    plt.colorbar(c0, ax=axs[0], label='Espesor de la capa blanda ρ < 100 Ω·m (m)', fraction=0.04, pad=0.02)
    axs[0].contour(EE, NN, T, levels=[10, 15, 20], colors='k', linewidths=0.8)
    axs[0].set_title('Espesor de la capa blanda / residuos (hasta ρ = 100 Ω·m)', fontsize=10)
    c1 = axs[1].contourf(EE, NN, B, levels=np.arange(10, 40, 2.5), cmap='YlGnBu_r', extend='max')
    plt.colorbar(c1, ax=axs[1], label='Profundidad al techo del basamento ρ ≥ 400 Ω·m (m)', fraction=0.04, pad=0.02)
    axs[1].set_title('Profundidad al basamento (blanco: no se alcanza ρ ≥ 400 Ω·m)', fontsize=10)
    for ax in axs:
        draw_profiles(ax); ax.plot(*np.vstack([poly, poly[:1]]).T, 'k:', lw=1)
        ax.set_aspect('equal'); ax.set_xlabel('Este RSO (m)'); ax.tick_params(labelsize=8)
    axs[0].set_ylabel('Norte RSO (m)')
    fig.suptitle('Mapas derivados del modelo 3D (cobertura ≤ 35 m de algún perfil; línea punteada: envolvente de los perfiles)', fontsize=11)
    fig.savefig(OUTF + 'fig15_mapas_espesor_basamento.png', dpi=150, bbox_inches='tight')
    plt.close(fig)


# ------------------------------------------------------------------------------------------------
def crossings():
    """cruces entre perfiles E-O (1-3) y N-S (4-6): distancia horizontal minima entre trazas y comparacion de rho(z)"""
    rows = []; pairs = []
    for a in (1, 2, 3):
        for b in (4, 5, 6):
            sa, sb = L[a], L[b]
            A = np.c_[sa['E'], sa['N']]; B = np.c_[sb['E'], sb['N']]
            D = np.sqrt(((A[:, None, :] - B[None, :, :])**2).sum(-1))
            i, j = np.unravel_index(np.argmin(D), D.shape)
            pairs.append((a, b, int(i), int(j), float(D[i, j])))
    return pairs


def fig_crossings(pairs):
    fig, axs = plt.subplots(3, 3, figsize=(12, 10), sharey=True)
    rows = []
    for (a, b, i, j, dmin) in pairs:
        ax = axs[a-1, b-4]
        sa, sb = L[a], L[b]
        ra = 10**sa['logrho'][i]; rb = 10**sb['logrho'][j]
        da, db = sa['d'], sb['d']
        ax.semilogx(ra, da, color=LINECOL[a], lw=2, label=f'TKI{a} (x={sa["x"][i]:.0f} m)')
        ax.semilogx(rb, db, color=LINECOL[b], lw=2, ls='--', label=f'TKI{b} (x={sb["x"][j]:.0f} m)')
        ax.invert_yaxis(); ax.set_xlim(5, 3000); ax.grid(alpha=0.3, which='both')
        ax.axvline(100, color='gray', lw=0.7); ax.axvline(400, color='gray', lw=0.7)
        ok = np.isfinite(ra) & np.isfinite(rb[:len(ra)]) if len(ra) == len(rb) else None
        dm = np.nanmax(np.minimum(da.max(), db.max()))
        n = min(np.isfinite(ra).sum(), np.isfinite(rb).sum())
        z = np.arange(0.5, min(da[np.isfinite(ra)].max(), db[np.isfinite(rb)].max()), 0.5)
        la = np.interp(z, da[np.isfinite(ra)], np.log10(ra[np.isfinite(ra)])); lb = np.interp(z, db[np.isfinite(rb)], np.log10(rb[np.isfinite(rb)]))
        diff = la - lb
        rows.append(dict(linea_EO=a, linea_NS=b, dist_trazas_m=dmin, x_EO=float(sa['x'][i]), x_NS=float(sb['x'][j]), prof_comun_m=float(z.max()),
                         dif_media_log10=float(np.mean(diff)), rms_log10=float(np.sqrt(np.mean(diff**2))), factor_rms=float(10**np.sqrt(np.mean(diff**2))),
                         corr=float(np.corrcoef(la, lb)[0, 1])))
        ax.set_title(f'TKI{a} × TKI{b}  (dist. trazas {dmin:.0f} m)\nRMS Δlog₁₀ρ = {rows[-1]["rms_log10"]:.2f}', fontsize=8.5)
        ax.legend(fontsize=7, loc='lower left')
    for ax in axs[:, 0]: ax.set_ylabel('Profundidad (m)')
    for ax in axs[-1]: ax.set_xlabel('ρ (Ω·m)')
    fig.suptitle('Consistencia 3D: columnas de resistividad en el punto de máximo acercamiento entre perfiles E–O (filas) y N–S (columnas)', fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(OUTF + 'fig16_consistencia_cruces.png', dpi=140, bbox_inches='tight')
    plt.close(fig)
    pd.DataFrame(rows).to_csv(W + 'cruces.csv', index=False)
    return rows


if __name__ == '__main__':
    what = sys.argv[1:] or ['vol', 'fence', 'slices', 'iso', 'thick', 'cross']
    out, th, bd, bottom, inside, poly = volume_metrics()
    if 'vol' in what: print(json.dumps(out, indent=1))
    if 'fence' in what: fig_fence()
    if 'slices' in what: fig_slices()
    if 'iso' in what: fig_iso()
    if 'thick' in what: fig_thickness(th, bd, inside, poly)
    if 'cross' in what:
        pairs = crossings(); print(pairs)
        rows = fig_crossings(pairs); print(pd.DataFrame(rows).round(2).to_string())
