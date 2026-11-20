import sys, json
from figs_sections import *
import pandas as pd
from matplotlib.lines import Line2D

F, R = load_all()
M = {int(k): v for k, v in json.load(open(W+'zone_metrics.json')).items()}
TOP = load_topo()
plt.rcParams.update({'font.size': 9, 'axes.titlesize': 10})
LC = {1: '#1b9e77', 2: '#d95f02', 3: '#7570b3', 4: '#e7298a', 5: '#66a61e', 6: '#e6ab02'}

# ------------------------------------------------------------ Fig 01: map + topography
def fig_mapa():
    fig, ax = plt.subplots(figsize=(7.5, 7))
    for l in range(1, 7):
        t = TOP[l]
        sc = ax.scatter(t.Este_m, t.Norte_m, c=t.elevacion_m, cmap='terrain', vmin=78, vmax=102, s=18, zorder=3, edgecolor='none')
        ax.plot(t.Este_m, t.Norte_m, '-', color=LC[l], lw=1.6, zorder=2)
        ax.annotate(f'TKI {l}\n0 m', (t.Este_m.iloc[0], t.Norte_m.iloc[0]), xytext=((6, -14) if l==5 else (6, -4 if l > 3 else 4)), textcoords='offset points', fontsize=8, color=LC[l], fontweight='bold')
        ax.annotate('200 m', (t.Este_m.iloc[-1], t.Norte_m.iloc[-1]), xytext=(2 if l <= 3 else 4, 6), textcoords='offset points', fontsize=7, color=LC[l])
        j = 20
        ax.annotate('', xy=(t.Este_m.iloc[j+2], t.Norte_m.iloc[j+2]), xytext=(t.Este_m.iloc[j], t.Norte_m.iloc[j]), arrowprops=dict(arrowstyle='->', color=LC[l], lw=1.2), zorder=4)
    cb = fig.colorbar(sc, ax=ax, shrink=0.7); cb.set_label('Elevación del electrodo (m s.n.m.)')
    ax.set_xlabel('Este (m, GPS)'); ax.set_ylabel('Norte (m, GPS)'); ax.set_aspect('equal'); ax.grid(alpha=0.3)
    ax.set_title('Ubicación de las 6 líneas de tomografía (coordenadas GPS de cada electrodo)', loc='left', fontweight='bold', fontsize=10)
    ax.annotate('N', xy=(0.94, 0.95), xytext=(0.94, 0.86), xycoords='axes fraction', arrowprops=dict(arrowstyle='-|>', color='k'), ha='center', fontweight='bold')
    ax.ticklabel_format(useOffset=False, style='plain'); plt.setp(ax.get_xticklabels(), rotation=30)
    fig.savefig(OUTF+'fig01_mapa_lineas.png', dpi=170, bbox_inches='tight'); plt.close(fig)

def fig_topo():
    fig, axs = plt.subplots(2, 3, figsize=(12, 5.2), sharex=True)
    for l, ax in zip(range(1, 7), axs.ravel()):
        t = TOP[l]
        ax.step(t.electrodo_x_m, t.elevacion_m, where='mid', color=LC[l], lw=1.6)
        ax.plot(t.electrodo_x_m, t.elevacion_m, 'o', color=LC[l], ms=3)
        ax.set_title(f'TKI {l}  (Δz = {t.elevacion_m.max()-t.elevacion_m.min():.0f} m)', loc='left', fontweight='bold')
        ax.set_ylim(78, 103); ax.grid(alpha=0.3)
        if l in (1, 4): ax.set_ylabel('Elevación (m s.n.m.)')
        if l > 3: ax.set_xlabel('Distancia (m)')
    fig.suptitle('Topografía introducida en cada línea (elevación GPS de los 41 electrodos, mismo eje vertical)', x=0.01, ha='left', fontweight='bold')
    fig.tight_layout(); fig.savefig(OUTF+'fig02_topografia.png', dpi=170, bbox_inches='tight'); plt.close(fig)

# ------------------------------------------------------------ Fig 03: electrode QC
def fig_qc():
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.2))
    ax = axs[0]
    for l in range(1, 7):
        df = R[l]['df_raw']; med = []
        for e in range(41):
            s = df[(df.M == e) | (df.N == e)]
            med.append(s.ip.median() if len(s) >= 5 else np.nan)
        ax.plot(range(41), med, '-o', ms=3, lw=1.2, color=LC[l], label=f'TKI {l}')
    ax.set_yscale('log'); ax.set_xlabel('Número de electrodo (0–40; ×5 m)'); ax.set_ylabel('IP aparente mediana (ms)\n(electrodo como electrodo de potencial)')
    ax.axvline(28, color='r', ls=':', lw=1); ax.text(28.3, ax.get_ylim()[1]*0.5, 'electrodo 28\n(x = 140 m)', color='r', fontsize=8, va='top')
    ax.legend(fontsize=7, ncol=2, loc='lower left'); ax.grid(alpha=0.3); ax.set_title('(a) IP aparente por electrodo de potencial', loc='left', fontweight='bold')
    ax = axs[1]
    for l in range(1, 7):
        df = R[l]['df_raw']; am = np.abs(R[l]['mis_raw']); fr = []
        for e in range(41):
            msk = ((df.M == e) | (df.N == e)).values
            fr.append(am[msk].mean() if msk.sum() >= 8 else np.nan)
        ax.plot(range(41), fr, '-o', ms=3, lw=1.2, color=LC[l])
    ax.axvline(28, color='r', ls=':', lw=1); ax.set_xlabel('Número de electrodo (0–40; ×5 m)'); ax.set_ylabel('|desajuste| medio de ρa (%)'); ax.grid(alpha=0.3)
    ax.set_title('(b) Desajuste de resistividad por electrodo de potencial', loc='left', fontweight='bold')
    ax = axs[2]
    df = R[1]['df_raw']; zp = 0.17*df.L; flag = df.M.isin([25, 28]) | df.N.isin([25, 28])
    sc = ax.scatter(df.xmid[~flag], -zp[~flag], c=df.ip[~flag], s=26, marker='s', cmap='viridis', vmin=0, vmax=30)
    ax.scatter(df.xmid[flag], -zp[flag], c=df.ip[flag], s=26, marker='s', cmap='viridis', vmin=0, vmax=30, edgecolor='r', linewidths=1.2)
    ax.set_xlabel('Posición del punto de datos (m)'); ax.set_ylabel('Pseudoprofundidad (m)'); ax.set_xlim(0, 200)
    cb = fig.colorbar(sc, ax=ax); cb.set_label('IP aparente (ms)')
    ax.set_title('(c) TKI 1: pseudosección de IP (borde rojo = datos con electrodo 25 ó 28)', loc='left', fontweight='bold', fontsize=8.5)
    fig.tight_layout(); fig.savefig(OUTF+'fig03_control_calidad_electrodos.png', dpi=170, bbox_inches='tight'); plt.close(fig)

# ------------------------------------------------------------ Fig 04: iteration analysis
def fig_iter():
    T = pd.read_csv(W+'tabla_iteraciones.csv')
    fig, axs = plt.subplots(1, 3, figsize=(14, 4))
    for l in range(1, 7):
        t = T[T.linea == l]
        axs[0].plot(t.iteracion, t.RMS, '-o', ms=3.5, color=LC[l], label=f'TKI {l}')
        axs[1].plot(t.iteracion, t.rho_max, '-o', ms=3.5, color=LC[l])
        axs[2].plot(t.iteracion, t.pct_basamento, '-o', ms=3.5, color=LC[l])
    for a in axs: a.axvline(SEL, color='k', ls='--', lw=1); a.grid(alpha=0.3); a.set_xlabel('Iteración')
    axs[0].set_ylabel('RMS (%)'); axs[0].set_yscale('log'); axs[0].legend(fontsize=8)
    axs[0].set_title('(a) Error RMS', loc='left', fontweight='bold')
    axs[1].set_ylabel('ρ máxima dentro de la zona cubierta (Ω·m)'); axs[1].set_yscale('log'); axs[1].axhline(2000, color='gray', ls=':'); axs[1].text(1.1, 2150, 'límite del artículo (2000 Ω·m)', fontsize=7, color='gray')
    axs[1].set_title('(b) Resistividad máxima del modelo', loc='left', fontweight='bold')
    axs[2].set_ylabel('% del área con ρ ≥ 400 Ω·m'); axs[2].set_title('(c) Proporción de "basamento"', loc='left', fontweight='bold')
    fig.tight_layout(); fig.savefig(OUTF+'fig04_analisis_iteraciones.png', dpi=170, bbox_inches='tight'); plt.close(fig)

def fig_iter_compare(line, its=(2, 4, 7, 10)):
    g, fw, df = build(line, use=R[line]['keep']); env = envelope(g, df)
    fig, axs = plt.subplots(len(its), 1, figsize=(10.5, 2.9*len(its)), sharex=True)
    xe, ze = surf_xy(g)
    for a, it in zip(axs, its):
        h = R[line]['hist'][it]
        X, Z, V, zs, Dm, cs = draw_section(a, g, np.exp(h['m']), env, 'rho')
        a.contour(X, Z, V, levels=[2.0], colors='k', linewidths=1.2); a.contour(X, Z, V, levels=[np.log10(400)], colors='k', linewidths=1.2, linestyles='--')
        a.set_title(f"Iteración {it}  —  RMS = {h['rms']:.1f} %   ρ máx = {np.exp(h['m'])[R[line]['inside']].max():.0f} Ω·m" + ('   ← elegida' if it == SEL else ''), loc='left', fontsize=9, fontweight='bold')
        a.set_aspect(2.0); a.set_ylabel('Elev. (m)'); a.set_xlim(0, 200); a.grid(alpha=0.25)
        a.set_ylim(np.nanmin(Z)-1, ze.max()+3)
    axs[-1].set_xlabel('Distancia (m)')
    fig.suptitle(f'TKI {line}: efecto del número de iteraciones sobre el modelo (misma escala de color; línea continua = 100 Ω·m, discontinua = 400 Ω·m)', x=0.01, ha='left', fontsize=9.5, fontweight='bold')
    fig.tight_layout(rect=(0, 0, 0.9, 0.97))
    cax = fig.add_axes([0.92, 0.25, 0.015, 0.5]); cb = fig.colorbar(plt.cm.ScalarMappable(norm=RHO_NORM, cmap=RHO_CMAP), cax=cax, ticks=np.log10(RHO_LEVELS)); cb.ax.set_yticklabels([str(l) for l in RHO_LEVELS], fontsize=7)
    fig.savefig(OUTF+f'fig05_iteraciones_TKI{line}.png', dpi=150, bbox_inches='tight'); plt.close(fig)

# ------------------------------------------------------------ Fig 06: Res2DInv-like 3 panels
def fig_res2dinv(line):
    g, fw, df = build(line, use=R[line]['keep']); env = envelope(g, df)
    d = F[line]['df']; zp = 0.17*d.L.values
    fig, axs = plt.subplots(3, 1, figsize=(10.5, 9.2), sharex=True)
    lv = np.log10(RHO_LEVELS)
    for a, v, ttl in [(axs[0], d.rhoa.values, 'Pseudosección de resistividad aparente MEDIDA (datos editados)'), (axs[1], F[line]['resp'], f"Pseudosección de resistividad aparente CALCULADA (iteración {SEL})")]:
        sc = a.scatter(d.xmid, -zp, c=np.log10(v), s=34, marker='s', cmap=RHO_CMAP, norm=RHO_NORM)
        a.set_title(ttl, loc='left', fontweight='bold', fontsize=9); a.set_ylabel('Pseudoprofundidad (m)'); a.set_ylim(-36, 0)
    a = axs[2]
    X, Z, V, zs, Dm, cs = draw_section(a, g, F[line]['rho'], env, 'rho')
    xe, ze = surf_xy(g); a.plot(np.arange(0, 200.1, 0.5), np.interp(np.arange(0, 200.1, 0.5), xe, ze), 'k-', lw=1)
    a.set_title(f"Modelo invertido de resistividad con topografía — RMS = {F[line]['rms']:.1f} %", loc='left', fontweight='bold', fontsize=9)
    a.set_ylabel('Elevación (m s.n.m.)'); a.set_xlim(0, 200); a.set_ylim(np.nanmin(Z)-1, ze.max()+3); a.set_xlabel('Distancia (m)')
    for a in axs: a.grid(alpha=0.25)
    fig.tight_layout(rect=(0, 0, 0.9, 1))
    cax = fig.add_axes([0.92, 0.3, 0.015, 0.4]); cb = fig.colorbar(plt.cm.ScalarMappable(norm=RHO_NORM, cmap=RHO_CMAP), cax=cax, ticks=lv); cb.ax.set_yticklabels([str(l) for l in RHO_LEVELS], fontsize=7); cb.set_label('Ω·m', fontsize=8)
    fig.suptitle(f'TKI {line}', x=0.01, ha='left', fontweight='bold', fontsize=11, y=1.0)
    fig.savefig(OUTF+f'fig06_pseudoseccion_modelo_TKI{line}.png', dpi=150, bbox_inches='tight'); plt.close(fig)

# ------------------------------------------------------------ Fig 07-11: sections
def fig_secciones():
    for l in range(1, 7):
        section_figure(l, F, R, M[l], OUTF+f'fig07_resistividad_TKI{l}.png')
        section_figure(l, F, R, M[l], OUTF+f'fig11_resistividad_IP_TKI{l}.png', with_ip=True)

def fig_6lines(kind):
    fig, axs = plt.subplots(6, 1, figsize=(10.5, 17.5), sharex=True)
    for l, a in zip(range(1, 7), axs):
        g, fw, df = build(l, use=R[l]['keep']); env = envelope(g, df)
        X, Z, V, zs, Dm, cs = draw_section(a, g, F[l]['rho'] if kind == 'rho' else F[l]['ip_m'], env, kind)
        Xr, Zr, Vr, _, _ = fine_section(g, F[l]['rho'], *env)
        a.contour(Xr, Zr, Vr, levels=[2.0], colors='k', linewidths=1.2); a.contour(Xr, Zr, Vr, levels=[np.log10(400)], colors='k', linewidths=1.2, linestyles='--')
        xe, ze = surf_xy(g); a.plot(xe, ze+0.3, 'v', color='k', ms=2.5)
        rms = f"RMS = {F[l]['rms']:.1f} %" if kind == 'rho' else f"RMS = {F[l]['ip_rms_abs']:.2f} ms"
        a.set_title(f'TKI {l}   (iteración {SEL}, {rms})', loc='left', fontweight='bold', fontsize=9)
        a.set_aspect(2.0); a.set_xlim(0, 200); a.grid(alpha=0.25); a.set_ylabel('Elev. (m)')
        a.set_ylim(np.nanmin(Z)-1, ze.max()+3)
    axs[-1].set_xlabel('Distancia (m)  [TKI 1–3: 0 m = extremo Este;  TKI 4–6: 0 m = extremo Sur]')
    fig.tight_layout(rect=(0, 0, 0.9, 1))
    cax = fig.add_axes([0.92, 0.35, 0.015, 0.3])
    if kind == 'rho':
        cb = fig.colorbar(plt.cm.ScalarMappable(norm=RHO_NORM, cmap=RHO_CMAP), cax=cax, ticks=np.log10(RHO_LEVELS)); cb.ax.set_yticklabels([str(l) for l in RHO_LEVELS], fontsize=7); cb.set_label('Resistividad (Ω·m)')
    else:
        cb = fig.colorbar(plt.cm.ScalarMappable(norm=IP_NORM, cmap=IP_CMAP), cax=cax, ticks=IP_LEVELS); cb.ax.set_yticklabels([str(l) for l in IP_LEVELS], fontsize=7); cb.set_label('Cargabilidad (ms)')
    fig.savefig(OUTF+('fig08_resistividad_6lineas.png' if kind == 'rho' else 'fig10_cargabilidad_6lineas.png'), dpi=130, bbox_inches='tight'); plt.close(fig)

if __name__ == '__main__':
    which = sys.argv[1:] or ['mapa', 'topo', 'qc', 'iter', 'cmp', 'r2d', 'sec', 'six']
    if 'mapa' in which: fig_mapa()
    if 'topo' in which: fig_topo()
    if 'qc' in which: fig_qc()
    if 'iter' in which: fig_iter()
    if 'cmp' in which:
        for l in range(1, 7): fig_iter_compare(l)
    if 'r2d' in which:
        for l in range(1, 7): fig_res2dinv(l)
    if 'sec' in which: fig_secciones()
    if 'six' in which: fig_6lines('rho'); fig_6lines('ip')
    print('ok', which)
