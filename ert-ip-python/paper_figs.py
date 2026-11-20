import re
"""Figuras a tamano de articulo IEEE (columna = 3.5 in, dos columnas = 7.16 in), texto ~6-7 pt."""
import os, sys, re, json
os.environ['LEG_FS'] = '5.5'; os.environ['LEG_LBL'] = '6'
from make_figures import *
from PIL import Image
from config import PF
import os
os.makedirs(PF, exist_ok=True)
plt.rcParams.update({'font.size': 6.5, 'axes.titlesize': 7, 'axes.labelsize': 6.5, 'xtick.labelsize': 6, 'ytick.labelsize': 6, 'legend.fontsize': 6,
                     'axes.linewidth': 0.6, 'xtick.major.width': 0.5, 'ytick.major.width': 0.5, 'xtick.major.size': 2.5, 'ytick.major.size': 2.5, 'lines.linewidth': 1.0})
CW, TW = 3.5, 7.16


def save(fig, name, dpi=300):
    fig.savefig(PF + name, dpi=dpi, bbox_inches='tight', pad_inches=0.02); plt.close(fig)


def p_fotos():
    im = Image.open(ENTRADA + 'photos_sheet.png').convert('RGB'); w, h = im.size
    tw, th = w // 3, h // 4
    pick = [(0, 0), (0, 1), (2, 1), (3, 0), (3, 2), (1, 1)]
    fig, axs = plt.subplots(2, 3, figsize=(CW, CW*0.62))
    for k, (r, c) in enumerate(pick):
        a = axs.ravel()[k]; a.imshow(im.crop((c*tw, r*th, (c+1)*tw, (r+1)*th))); a.axis('off')
        a.text(0.03, 0.95, '(%s)' % 'abcdef'[k], transform=a.transAxes, color='w', fontsize=6.5, fontweight='bold', va='top', bbox=dict(fc='k', ec='none', alpha=0.5, pad=1))
    fig.subplots_adjust(wspace=0.02, hspace=0.02, left=0, right=1, top=1, bottom=0)
    save(fig, 'p_fotos.png')


def p_mapa():
    fig, ax = plt.subplots(figsize=(CW, 2.9))
    for l in range(1, 7):
        t = TOP[l]
        sc = ax.scatter(t.Este_m, t.Norte_m, c=t.elevacion_m, cmap='terrain', vmin=78, vmax=102, s=6, zorder=3, edgecolor='none')
        ax.plot(t.Este_m, t.Norte_m, '-', color=LC[l], lw=1.0, zorder=2)
        ax.annotate(f'TKI{l}', (t.Este_m.iloc[0], t.Norte_m.iloc[0]), xytext=((4, -9) if l == 5 else (3, -2 if l > 3 else 3)), textcoords='offset points', fontsize=6, color=LC[l], fontweight='bold')
        j = 20
        ax.annotate('', xy=(t.Este_m.iloc[j+2], t.Norte_m.iloc[j+2]), xytext=(t.Este_m.iloc[j], t.Norte_m.iloc[j]), arrowprops=dict(arrowstyle='->', color=LC[l], lw=0.8), zorder=4)
    cb = fig.colorbar(sc, ax=ax, shrink=0.8, pad=0.02, aspect=25); cb.set_label('Elevación (m s.n.m.)', fontsize=6); cb.ax.tick_params(labelsize=5.5)
    ax.set_xlabel('Este (m, GPS)'); ax.set_ylabel('Norte (m, GPS)'); ax.set_aspect('equal'); ax.grid(alpha=0.3, lw=0.4)
    ax.annotate('N', xy=(0.07, 0.95), xytext=(0.07, 0.83), xycoords='axes fraction', arrowprops=dict(arrowstyle='-|>', color='k', lw=0.8), ha='center', fontweight='bold', fontsize=6.5)
    ax.set_xlim(ax.get_xlim()[0], ax.get_xlim()[1] + 14); ax.ticklabel_format(useOffset=False, style='plain'); plt.setp(ax.get_xticklabels(), rotation=30)
    save(fig, 'p_mapa.png')


def p_qc():
    fig, axs = plt.subplots(1, 3, figsize=(TW, 2.0), gridspec_kw=dict(width_ratios=[1, 1, 1.1]))
    ax = axs[0]
    for l in range(1, 7):
        df = R[l]['df_raw']; med = []
        for e in range(41):
            s = df[(df.M == e) | (df.N == e)]; med.append(s.ip.median() if len(s) >= 5 else np.nan)
        ax.plot(range(41), med, '-o', ms=1.8, lw=0.8, color=LC[l], label=f'TKI{l}')
    ax.set_yscale('log'); ax.set_xlabel('Electrodo (0–40, ×5 m)'); ax.set_ylabel('IP aparente mediana (ms)')
    ax.axvline(28, color='r', ls=':', lw=0.8); ax.text(28.6, 12, 'e28\n(x=140 m)', color='r', fontsize=5.5, va='top')
    ax.set_ylim(0.5, 60); ax.legend(ncol=3, loc='upper left', handlelength=1.0, columnspacing=0.6, fontsize=5.5); ax.grid(alpha=0.3, lw=0.4); ax.set_title('(a) IP por electrodo de potencial', loc='left')
    ax = axs[1]
    for l in range(1, 7):
        df = R[l]['df_raw']; am = np.abs(R[l]['mis_raw']); fr = []
        for e in range(41):
            msk = ((df.M == e) | (df.N == e)).values; fr.append(am[msk].mean() if msk.sum() >= 8 else np.nan)
        ax.plot(range(41), fr, '-o', ms=1.8, lw=0.8, color=LC[l])
    ax.axvline(28, color='r', ls=':', lw=0.8); ax.set_xlabel('Electrodo (0–40, ×5 m)'); ax.set_ylabel('|desajuste| medio de ρa (%)'); ax.grid(alpha=0.3, lw=0.4)
    ax.set_title('(b) Desajuste de ρa por electrodo', loc='left')
    ax = axs[2]
    df = R[1]['df_raw']; zp = 0.17*df.L; flag = df.M.isin([25, 28]) | df.N.isin([25, 28])
    sc = ax.scatter(df.xmid[~flag], -zp[~flag], c=df.ip[~flag], s=7, marker='s', cmap='viridis', vmin=0, vmax=30)
    ax.scatter(df.xmid[flag], -zp[flag], c=df.ip[flag], s=7, marker='s', cmap='viridis', vmin=0, vmax=30, edgecolor='r', linewidths=0.6)
    ax.set_xlabel('Posición (m)'); ax.set_ylabel('Pseudoprofundidad (m)'); ax.set_xlim(0, 200)
    cb = fig.colorbar(sc, ax=ax, pad=0.02); cb.set_label('IP aparente (ms)', fontsize=6); cb.ax.tick_params(labelsize=5.5)
    ax.set_title('(c) TKI1: borde rojo = electrodo 25 ó 28', loc='left')
    fig.tight_layout(w_pad=0.8); save(fig, 'p_qc.png')


def p_iter():
    T = pd.read_csv(W + 'tabla_iteraciones.csv')
    fig, axs = plt.subplots(1, 3, figsize=(TW, 1.9))
    for l in range(1, 7):
        t = T[T.linea == l]
        axs[0].plot(t.iteracion, t.RMS, '-o', ms=2, color=LC[l], label=f'TKI{l}')
        axs[1].plot(t.iteracion, t.rho_max, '-o', ms=2, color=LC[l])
        axs[2].plot(t.iteracion, t.pct_basamento, '-o', ms=2, color=LC[l])
    for a in axs: a.axvline(SEL, color='k', ls='--', lw=0.7); a.grid(alpha=0.3, lw=0.4); a.set_xlabel('Iteración')
    axs[0].set_ylabel('RMS (%)'); axs[0].set_yscale('log'); axs[0].legend(ncol=2, handlelength=1.2, columnspacing=0.8); axs[0].set_title('(a) Error RMS', loc='left')
    axs[0].set_yticks([5, 7, 10, 15]); axs[0].set_yticklabels(['5', '7', '10', '15']); axs[0].yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    axs[1].set_ylabel('ρ máx. del modelo (Ω·m)'); axs[1].set_yscale('log'); axs[1].axhline(2000, color='gray', ls=':')
    axs[1].set_title('(b) Resistividad máxima', loc='left')
    axs[2].set_ylabel('% del área con ρ ≥ 400 Ω·m'); axs[2].set_title('(c) Proporción de basamento', loc='left')
    fig.tight_layout(w_pad=0.8); save(fig, 'p_iter.png')


def p_pseudo(line=1):
    g, fw, df = build(line, use=R[line]['keep']); env = envelope(g, df)
    d = F[line]['df']; zp = 0.17*d.L.values
    fig, axs = plt.subplots(3, 1, figsize=(CW, 3.9), sharex=True)
    for a, v, ttl in [(axs[0], d.rhoa.values, '(a) ρa medida (datos editados)'), (axs[1], F[line]['resp'], f'(b) ρa calculada (iteración {SEL})')]:
        a.scatter(d.xmid, -zp, c=np.log10(v), s=6, marker='s', cmap=RHO_CMAP, norm=RHO_NORM)
        a.set_title(ttl, loc='left'); a.set_ylabel('Pseudoprof. (m)'); a.set_ylim(-36, 0)
    a = axs[2]
    X, Z, V, zs, Dm, cs = draw_section(a, g, F[line]['rho'], env, 'rho')
    xe, ze = surf_xy(g); a.plot(np.arange(0, 200.1, 0.5), np.interp(np.arange(0, 200.1, 0.5), xe, ze), 'k-', lw=0.6)
    a.set_title(f"(c) Modelo invertido con topografía (RMS = {F[line]['rms']:.1f} %)", loc='left')
    a.set_ylabel('Elevación (m)'); a.set_xlim(0, 200); a.set_ylim(np.nanmin(Z)-1, ze.max()+3); a.set_xlabel('Distancia (m)')
    for a in axs: a.grid(alpha=0.25, lw=0.4)
    fig.tight_layout(h_pad=0.6)
    fig.subplots_adjust(bottom=0.2)
    cax = fig.add_axes([0.2, 0.045, 0.7, 0.018]); cb = fig.colorbar(plt.cm.ScalarMappable(norm=RHO_NORM, cmap=RHO_CMAP), cax=cax, orientation='horizontal', ticks=np.log10(RHO_LEVELS))
    cb.ax.set_xticklabels([str(l) for l in RHO_LEVELS], fontsize=5); cb.set_label('Ω·m', fontsize=6, labelpad=1)
    save(fig, 'p_pseudo_TKI1.png')


def p_six(kind):
    fig, axs = plt.subplots(3, 2, figsize=(TW, 5.3))
    for l, a in zip(range(1, 7), axs.ravel()):
        g, fw, df = build(l, use=R[l]['keep']); env = envelope(g, df)
        X, Z, V, zs, Dm, cs = draw_section(a, g, F[l]['rho'] if kind == 'rho' else F[l]['ip_m'], env, kind)
        Xr, Zr, Vr, _, _ = fine_section(g, F[l]['rho'], *env)
        a.contour(Xr, Zr, Vr, levels=[2.0], colors='k', linewidths=0.8); a.contour(Xr, Zr, Vr, levels=[np.log10(400)], colors='k', linewidths=0.8, linestyles='--')
        if kind == 'rho': a.contour(Xr, Zr, Vr, levels=[np.log10(30)], colors='#d000d0', linewidths=0.7)
        xe, ze = surf_xy(g); a.plot(xe, ze+0.4, 'v', color='k', ms=1.6)
        rms = f"RMS {F[l]['rms']:.1f} %" if kind == 'rho' else f"RMS {F[l]['ip_rms_abs']:.2f} ms"
        a.set_title(f'TKI{l}  (it. {SEL}, {rms})', loc='left', fontweight='bold')
        a.set_xlim(0, 200); a.grid(alpha=0.25, lw=0.4); a.set_ylim(ze.max()+3-52, ze.max()+3)
        if l % 2 == 1: a.set_ylabel('Elevación (m)')
        if l >= 5: a.set_xlabel('Distancia (m)  [TKI1–3: 0 m = Este;  TKI4–6: 0 m = Sur]' if l == 5 else 'Distancia (m)')
    fig.tight_layout(h_pad=0.5, w_pad=0.6); fig.subplots_adjust(bottom=0.12)
    cax = fig.add_axes([0.25, 0.04, 0.5, 0.014])
    if kind == 'rho':
        cb = fig.colorbar(plt.cm.ScalarMappable(norm=RHO_NORM, cmap=RHO_CMAP), cax=cax, orientation='horizontal', ticks=np.log10(RHO_LEVELS)); cb.ax.set_xticklabels([str(l) for l in RHO_LEVELS], fontsize=5.5); cb.set_label('Resistividad (Ω·m)', fontsize=6, labelpad=1)
    else:
        cb = fig.colorbar(plt.cm.ScalarMappable(norm=IP_NORM, cmap=IP_CMAP), cax=cax, orientation='horizontal', ticks=IP_LEVELS); cb.ax.set_xticklabels([str(l) for l in IP_LEVELS], fontsize=5.5); cb.set_label('Cargabilidad (ms)', fontsize=6, labelpad=1)
    save(fig, f'p_seis_{kind}.png')


def patched(modname, subs, fscale=None):
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f'{modname}.py')).read()
    for a, b in subs:
        assert a in src, (modname, a)
        src = src.replace(a, b)
    if fscale:
        src = re.sub(r'(fontsize|labelsize)=(\d+(?:\.\d+)?)', lambda m: f"{m.group(1)}={float(m.group(2))*fscale:.2f}", src)
    src = src.split("if __name__ == '__main__':")[0]
    ns = {'__name__': 'patched_' + modname}
    exec(compile(src, modname + '_patched', 'exec'), ns)
    return ns


def p_3d():
    subs = [("figsize=(16, 7.6)", "figsize=(7.16, 3.3)"), ("fig.suptitle(", "_nosup("),
            ("OUTF + ('fig12_3D_cercas_resistividad.png' if which == 'rho' else 'fig12b_3D_cercas_cargabilidad.png'), dpi=160", "PF + ('p_cercas_rho.png' if which == 'rho' else 'p_cercas_ip.png'), dpi=300"),
            ("fig.subplots_adjust(left=0.0, right=1.0, top=0.97, bottom=0.12, wspace=0.0)", "fig.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.14, wspace=0.12)"),
            ("cax = fig.add_axes([0.3, 0.07, 0.4, 0.022])", "cax = fig.add_axes([0.3, 0.06, 0.4, 0.02])"),
            ("ax.set_zlabel('Elevación (m)', fontsize=8, labelpad=2)", "ax.set_zlabel('')"), ("labelpad=2", "labelpad=-3"), ("ax.tick_params(labelsize=7, pad=0)", "ax.tick_params(labelsize=7, pad=-2); ax.tick_params(axis='z', labelsize=7, pad=1)"),
            ("s['zs'][0] + 8, f'TKI", "s['zs'][0] + 6 + 14*((line-1) % 3), f'TKI"), ("s['zs'][0] + 6, f'TKI", "s['zs'][0] + 6 + 14*((line-1) % 3), f'TKI"),
            ("zoom=1.12", "zoom=1.08"), ("style3d(ax, view)\n", "style3d(ax, view); ax.set_zticklabels([]) if k == 1 else None\n"), ("figsize=(7.16, 3.3)", "figsize=(7.16, 3.0)")]
    ns = patched('fig3d', subs, fscale=0.72)
    ns['PF'] = PF; ns['_nosup'] = lambda *a, **k: None
    ns['fig_fence']()


def p_3d_rest():
    subs = [("figsize=(15, 9.3)", "figsize=(7.16, 4.7)"), ("fig.suptitle(", "_nosup("),
            ("OUTF + ('fig13_cortes_profundidad_resistividad.png' if which == 'rho' else 'fig13b_cortes_profundidad_cargabilidad.png'), dpi=150", "PF + ('p_cortes_rho.png' if which == 'rho' else 'p_cortes_ip.png'), dpi=300"),
            ("f'Profundidad {d} m bajo la superficie'", "f'Profundidad {d} m'"),
            ("ax.set_xlabel('Este RSO (m)', fontsize=8)", "ax.set_xlabel('Este (m)', fontsize=8)"), ("ax.set_ylabel('Norte RSO (m)', fontsize=8)", "ax.set_ylabel('Norte (m)', fontsize=8)"),
            ("fig.subplots_adjust(top=0.93, bottom=0.11, hspace=0.12, wspace=0.05)", "fig.subplots_adjust(top=0.98, bottom=0.12, hspace=0.18, wspace=0.05)"),
            ("cax = fig.add_axes([0.3, 0.035, 0.4, 0.018])", "cax = fig.add_axes([0.3, 0.03, 0.4, 0.016])"),
            ("fig = plt.figure(figsize=(16, 7.6))\n    meshes", "fig = plt.figure(figsize=(7.16, 3.3))\n    meshes"),
            ("fig.subplots_adjust(left=0.0, right=1.0, top=0.97, bottom=0.1, wspace=0.0)", "fig.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.09, wspace=0.12)"),
            ("ax.set_zlabel('Elevación (m)', fontsize=8, labelpad=2)", "ax.set_zlabel('')"), ("labelpad=2", "labelpad=-3"), ("ax.tick_params(labelsize=7, pad=0)", "ax.tick_params(labelsize=7, pad=-2); ax.tick_params(axis='z', labelsize=7, pad=1)"),
            ("s['zs'][0] + 8, f'TKI", "s['zs'][0] + 6 + 14*((line-1) % 3), f'TKI"), ("s['zs'][0] + 6, f'TKI", "s['zs'][0] + 6 + 14*((line-1) % 3), f'TKI"),
            ("zoom=1.12", "zoom=1.08"), ("style3d(ax, view)\n", "style3d(ax, view); ax.set_zticklabels([]) if k == 1 else None\n"), ("fig.savefig(OUTF + 'fig14_3D_isosuperficies.png', dpi=160", "fig.savefig(PF + 'p_iso.png', dpi=300"),
            ("fig, axs = plt.subplots(1, 2, figsize=(14, 6.4), sharex=True, sharey=True)", "fig, axs = plt.subplots(1, 2, figsize=(7.16, 3.3), sharex=True, sharey=True)"),
            ("label='Espesor de la capa blanda ρ < 100 Ω·m (m)', fraction=0.04, pad=0.02)", "label='Espesor ρ < 100 Ω·m (m)', fraction=0.04, pad=0.02)"),
            ("label='Profundidad al techo del basamento ρ ≥ 400 Ω·m (m)', fraction=0.04, pad=0.02)", "label='Profundidad al techo de ρ ≥ 400 Ω·m (m)', fraction=0.04, pad=0.02)"),
            ("'Espesor de la capa blanda / residuos (hasta ρ = 100 Ω·m)'", "'(a) Espesor de la capa blanda'"),
            ("'Profundidad al basamento (blanco: no se alcanza ρ ≥ 400 Ω·m)'", "'(b) Profundidad al basamento'"),
            ("ax.set_aspect('equal'); ax.set_xlabel('Este RSO (m)'); ax.tick_params(labelsize=8)", "ax.set_aspect('equal'); ax.set_xlabel('Este (m)', fontsize=8); ax.tick_params(labelsize=8)"),
            ("axs[0].set_ylabel('Norte RSO (m)')", "axs[0].set_ylabel('Norte (m)', fontsize=8)"),
            ("fig.savefig(OUTF + 'fig15_mapas_espesor_basamento.png', dpi=150", "fig.savefig(PF + 'p_espesor.png', dpi=300"),
            ("ax.set_aspect('equal'); ax.set_xlabel('Este (m)', fontsize=8)", "ax.set_aspect('equal'); ax.set_xlim(Eg[0], Eg[-1] + 16); ax.set_xlabel('Este (m)', fontsize=8)"),
            ("ax.set_title(f'Profundidad {d} m'", "ax.set_xlim(Eg[0], Eg[-1] + 16); ax.set_title(f'Profundidad {d} m'")]
    ns = patched('fig3d', subs, fscale=0.72)
    ns['PF'] = PF; ns['_nosup'] = lambda *a, **k: None
    out, th, bd, bottom, inside, poly = ns['volume_metrics']()
    ns['fig_slices'](); ns['fig_iso'](); ns['fig_thickness'](th, bd, inside, poly)


def p_ip_chem():
    subs = [("fig, axs = plt.subplots(2, 4, figsize=(16, 7.6))", "fig, axs = plt.subplots(2, 4, figsize=(7.16, 3.4))"),
            ("fig.suptitle(", "_nosup("), ("OUTF + 'fig17_resistividad_vs_cargabilidad.png', dpi=140", "PF + 'p_rho_ip.png', dpi=300"),
            ("ax.set_title(f'TKI{l}   r = {r:.2f}   (pendiente {k:.2f} ms/década)', fontsize=9.5)", "ax.set_title(f'TKI{l}  r = {r:.2f}', fontsize=6.5)"),
            ("ax.set_title('Cargabilidad media por clase de resistividad', fontsize=9.5)", "ax.set_title('IP media por clase', fontsize=6.5)"),
            ("ax.set_title(f'Las 6 líneas juntas: r = {rr:.2f}', fontsize=9.5)", "ax.set_title(f'Seis líneas: r = {rr:.2f}', fontsize=6.5)"),
            ("ax.set_xticklabels([c[0] for c in CL], fontsize=8)", "ax.set_xticklabels(['Blanda', 'Consol.', 'Basam.'], fontsize=5.5)"),
            ("ax.set_ylabel('Cargabilidad media (ms)'); ax.legend(fontsize=7, ncol=3)", "ax.set_ylabel('IP media (ms)'); ax.legend(fontsize=4.5, ncol=3, handlelength=0.8, columnspacing=0.5)"),
            ("ax.set_xlabel('Resistividad (Ω·m)')\n        if l in (1, 4)", "ax.set_xlabel('ρ (Ω·m)')\n        if l in (1, 4)"),
            ("fig.tight_layout(rect=(0, 0, 1, 0.96))", "fig.tight_layout(pad=0.4, w_pad=0.5, h_pad=0.6)"),
            ("gridsize=22", "gridsize=14"),
            ("fig, axs = plt.subplots(1, 3, figsize=(17, 5.6), gridspec_kw=dict(width_ratios=[1.15, 1.15, 0.8]))", "fig, axs = plt.subplots(1, 3, figsize=(7.16, 2.3), gridspec_kw=dict(width_ratios=[1.15, 1.15, 0.8]))"),
            ("OUTF + 'fig18_quimica_suelo_agua.png', dpi=140", "PF + 'p_quimica.png', dpi=300"),
            ("rotation=60, fontsize=8, ha='right')", "rotation=60, fontsize=5.5, ha='right')"),
            ("ax.set_title(ttl, fontsize=10); ax.legend(fontsize=8)", "ax.set_title(ttl, fontsize=6.5); ax.legend(fontsize=5.5, handlelength=1)"),
            ("ax.legend(fontsize=7, loc='upper right'); ax.set_ylim(3, 3000)", "ax.legend(fontsize=4.6, loc='upper right', handlelength=1); ax.set_ylim(3, 6000)"),
            ("ax.set_title('Estimación de orden de magnitud', fontsize=10)", "ax.set_title('(c) Estimación de orden de magnitud', fontsize=6.5)"),
            ("label='ρ de la formación saturada (Archie, φ 0.35–0.5, m 1.3–2)'", "label='ρ formación saturada (Archie)'"),
            ("label=f'ρ observada en capa blanda (P10–P90: {obs[\"p10\"]:.0f}–{obs[\"p90\"]:.0f} Ω·m)'", "label=f'ρ observada, capa blanda (P10–P90: {obs[\"p10\"]:.0f}–{obs[\"p90\"]:.0f})'"),
            ("label='ρ del agua (de cationes mayoritarios)'", "label='ρ del agua (cationes)'"),
            ("fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig(", "fig.tight_layout(pad=0.4, w_pad=0.6); fig.savefig("),
            ("ax.grid(axis='y', alpha=0.3, which='both')", "ax.grid(axis='y', alpha=0.3, which='major', lw=0.4); ax.set_ylim(top=ax.get_ylim()[1]*60)"),
            ("ax.legend(fontsize=5.5, handlelength=1)", "ax.legend(fontsize=5.5, handlelength=1, ncol=3, loc='upper right')"),
            ("'Suelo (KS-1 a KS-3)'", "'(a) Suelo (KS-1 a KS-3)'"), ("'Agua (KW1 a KW3)'", "'(b) Agua (KW1 a KW3)'"),
            ("ax.legend(fontsize=4.5, ncol=3, handlelength=0.8, columnspacing=0.5)", "ax.set_ylim(0, 3.9); ax.legend(fontsize=4.5, ncol=3, handlelength=0.8, columnspacing=0.5)")]
    ns = patched('fig_ip_chem', subs)
    ns['PF'] = PF; ns['_nosup'] = lambda *a, **k: None
    ns['fig_scatter'](ns['pooled']()); ns['chem']()


if __name__ == '__main__':
    what = sys.argv[1:] or ['fotos', 'mapa', 'qc', 'iter', 'pseudo', 'six', '3d', '3d2', 'ipchem']
    if 'fotos' in what: p_fotos()
    if 'mapa' in what: p_mapa()
    if 'qc' in what: p_qc()
    if 'iter' in what: p_iter()
    if 'pseudo' in what: p_pseudo()
    if 'six' in what: p_six('rho'); p_six('ip')
    if '3d' in what: p_3d()
    if '3d2' in what: p_3d_rest()
    if 'ipchem' in what: p_ip_chem()
    print('ok', what)
