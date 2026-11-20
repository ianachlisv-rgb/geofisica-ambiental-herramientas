import sys, json, shutil
from plotlib import *
import pandas as pd

F, R = load_all()
LINECOL = {1: '#e6194b', 2: '#f58231', 3: '#9a6324', 4: '#3cb44b', 5: '#4363d8', 6: '#911eb4'}
CL = [('Capa blanda\n(<100 Ω·m)', -9, 2.0, '#4eb3d3'), ('Capa consolidada\n(100–400)', 2.0, np.log10(400), '#fee08b'), ('Basamento\n(>400)', np.log10(400), 9, '#d73027')]


def pooled():
    rows = []
    for l in range(1, 7):
        g, fw, df = build(l, use=R[l]['keep'])
        m = R[l]['inside'].astype(bool)
        lr = np.log10(F[l]['rho'][m]); ip = F[l]['ip_m'][m]
        for a, b in zip(lr, ip): rows.append((l, a, b))
    return pd.DataFrame(rows, columns=['linea', 'logrho', 'ip'])


def fig_scatter(P):
    fig, axs = plt.subplots(2, 4, figsize=(16, 7.6))
    stats = []
    for l in range(1, 7):
        ax = axs.ravel()[l-1]; d = P[P.linea == l]
        ax.hexbin(d.logrho, d.ip, gridsize=22, cmap='Greys', mincnt=1, extent=(0.8, 3.5, 0, 5.5))
        for (nm, lo, hi, col) in CL: ax.axvspan(max(lo, 0.8), min(hi, 3.5), color=col, alpha=0.13)
        r = np.corrcoef(d.logrho, d.ip)[0, 1]
        k, b0 = np.polyfit(d.logrho, d.ip, 1); xx = np.array([d.logrho.min(), d.logrho.max()])
        ax.plot(xx, k*xx+b0, 'r-', lw=2)
        ax.set_title(f'TKI{l}   r = {r:.2f}   (pendiente {k:.2f} ms/década)', fontsize=9.5)
        ax.set_xlim(0.8, 3.5); ax.set_ylim(0, 5.5)
        ax.set_xticks([1, 2, 3]); ax.set_xticklabels(['10', '100', '1000'])
        if l > 3: ax.set_xlabel('Resistividad (Ω·m)')
        if l in (1, 4): ax.set_ylabel('Cargabilidad (ms)')
        stats.append(dict(linea=l, r=r, pendiente=k))
    # ultimo panel: medias por clase y linea
    ax = axs.ravel()[6]
    w = 0.13
    for l in range(1, 7):
        d = P[P.linea == l]; vals = []
        for (nm, lo, hi, col) in CL:
            s = d[(d.logrho >= lo) & (d.logrho < hi)].ip
            vals.append(s.mean() if len(s) > 30 else np.nan)
        ax.bar(np.arange(3) + (l-3.5)*w, vals, w, color=LINECOL[l], label=f'TKI{l}')
    ax.set_xticks(range(3)); ax.set_xticklabels([c[0] for c in CL], fontsize=8); ax.set_ylabel('Cargabilidad media (ms)'); ax.legend(fontsize=7, ncol=3)
    ax.set_title('Cargabilidad media por clase de resistividad', fontsize=9.5)
    ax = axs.ravel()[7]
    # todas las lineas: media +- sd por intervalo de resistividad
    bins = np.arange(0.9, 3.4, 0.2); c = 0.5*(bins[1:]+bins[:-1])
    mu = [P[(P.logrho >= a) & (P.logrho < b)].ip.mean() for a, b in zip(bins[:-1], bins[1:])]
    sd = [P[(P.logrho >= a) & (P.logrho < b)].ip.std() for a, b in zip(bins[:-1], bins[1:])]
    n = [((P.logrho >= a) & (P.logrho < b)).sum() for a, b in zip(bins[:-1], bins[1:])]
    mu, sd, n = map(np.array, (mu, sd, n)); ok = n > 20
    ax.errorbar(c[ok], mu[ok], sd[ok], fmt='ko-', capsize=3)
    for (nm, lo, hi, col) in CL: ax.axvspan(max(lo, 0.8), min(hi, 3.5), color=col, alpha=0.13)
    rr = np.corrcoef(P.logrho, P.ip)[0, 1]
    ax.set_title(f'Las 6 líneas juntas: r = {rr:.2f}', fontsize=9.5); ax.set_xticks([1, 2, 3]); ax.set_xticklabels(['10', '100', '1000'])
    ax.set_xlabel('Resistividad (Ω·m)'); ax.set_xlim(0.8, 3.5); ax.set_ylim(0, 5.5)
    fig.suptitle('Relación entre resistividad y cargabilidad en las celdas del modelo invertido (cada celda = un bloque del modelo dentro de la envolvente de datos)', fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(OUTF + 'fig17_resistividad_vs_cargabilidad.png', dpi=140, bbox_inches='tight'); plt.close(fig)
    stats.append(dict(linea='todas', r=rr, pendiente=np.polyfit(P.logrho, P.ip, 1)[0]))
    # medias por clase (pool)
    cls = {}
    for (nm, lo, hi, col) in CL:
        s = P[(P.logrho >= lo) & (P.logrho < hi)].ip
        cls[nm.split('\n')[0]] = dict(n=int(len(s)), media=float(s.mean()), mediana=float(s.median()), p10=float(s.quantile(0.1)), p90=float(s.quantile(0.9)))
    json.dump(dict(stats=stats, clases=cls), open(W + 'ip_stats.json', 'w'), indent=1, default=float)
    print(pd.DataFrame(stats).round(2).to_string()); print(json.dumps(cls, indent=1))


# ------------------------------------------------------------------ quimica
WATER = pd.read_excel(ENTRADA + 'water.xlsx', sheet_name='Sheet1', header=None)
SOIL = pd.read_excel(ENTRADA + 'soil.xlsx', sheet_name='Sheet2', header=None)


def load_tbl(d):
    d = d.dropna(how='all').reset_index(drop=True)
    hdr = d.iloc[0].tolist(); d = d.iloc[1:].copy(); d.columns = ['par'] + hdr[1:]
    d['par'] = d['par'].astype(str).str.strip()
    for c in d.columns[1:]: d[c] = pd.to_numeric(d[c], errors='coerce')
    return d.set_index('par')


def chem():
    w = load_tbl(WATER); s = load_tbl(SOIL)
    # ---- estimacion de la resistividad del agua porosa a partir de cationes mayoritarios (reglas empiricas: EC[uS/cm] ~ 100 x sum cationes [meq/L])
    eq = {'Sodium, Na': 22.99, 'Potassium, K': 39.10, 'Calcium, Ca': 40.08/2, 'Magnesium, Mg': 24.31/2}
    rows = []
    for col in w.columns:
        meq = sum(w.loc[k, col]/1000.0/eqw for k, eqw in eq.items())       # ug/L -> mg/L -> meq/L
        ec = 100*meq; rw = 1e4/ec
        rows.append(dict(muestra=col, cationes_meq_L=meq, EC_est_uS_cm=ec, rho_agua_ohm_m=rw))
    est = pd.DataFrame(rows)
    # Archie: rho = rho_w * phi^-m, phi 0.35-0.50, m 1.3-2.0
    est['rho_Archie_min'] = est.rho_agua_ohm_m*0.50**-1.3; est['rho_Archie_max'] = est.rho_agua_ohm_m*0.35**-2.0
    est.to_csv(W + 'estimacion_resistividad_agua.csv', index=False)
    print(est.round(2).to_string())
    # observado en la capa blanda
    P = pooled(); soft = 10**P[P.logrho < 2.0].logrho
    obs = dict(p10=float(np.percentile(soft, 10)), mediana=float(np.median(soft)), p90=float(np.percentile(soft, 90)))
    json.dump(dict(est=est.to_dict('records'), observado_capa_blanda=obs), open(W + 'quimica_estimacion.json', 'w'), indent=1, default=float)
    print('capa blanda observada', obs)

    fig, axs = plt.subplots(1, 3, figsize=(17, 5.6), gridspec_kw=dict(width_ratios=[1.15, 1.15, 0.8]))
    cols = ['#4363d8', '#f58231', '#3cb44b']
    for ax, tbl, ttl, unit in ((axs[0], s, 'Suelo (KS-1 a KS-3)', 'mg/kg (supuesto)'), (axs[1], w, 'Agua (KW1 a KW3)', 'µg/L (supuesto)')):
        t = tbl.drop(index=[i for i in tbl.index if i.startswith('pH') or i.startswith('Chemical')], errors='ignore')
        names = [i for i in t.index]; x = np.arange(len(names)); wd = 0.27
        for j, c in enumerate(t.columns):
            v = t[c].values.astype(float); v = np.where(np.isnan(v), np.nan, v)
            ax.bar(x + (j-1)*wd, np.where(v > 0, v, np.nan), wd, color=cols[j], label=c)
        ax.set_yscale('log'); ax.set_xticks(x); ax.set_xticklabels([n.split(',')[-1].strip() if ',' in n else n for n in names], rotation=60, fontsize=8, ha='right')
        ax.set_ylabel(unit); ax.set_title(ttl, fontsize=10); ax.legend(fontsize=8); ax.grid(axis='y', alpha=0.3, which='both')
    ax = axs[2]
    x = np.arange(3); ax.bar(x, est.rho_agua_ohm_m, 0.5, color='#4eb3d3', label='ρ del agua (de cationes mayoritarios)')
    for i, r in est.iterrows(): ax.plot([i, i], [r.rho_Archie_min, r.rho_Archie_max], 'k-', lw=6, solid_capstyle='butt', alpha=0.6, label='ρ de la formación saturada (Archie, φ 0.35–0.5, m 1.3–2)' if i == 0 else None)
    ax.axhspan(obs['p10'], obs['p90'], color='#d73027', alpha=0.18, label=f'ρ observada en capa blanda (P10–P90: {obs["p10"]:.0f}–{obs["p90"]:.0f} Ω·m)')
    ax.set_xticks(x); ax.set_xticklabels(est.muestra); ax.set_yscale('log'); ax.set_ylabel('Ω·m'); ax.legend(fontsize=7, loc='upper right'); ax.set_ylim(3, 3000)
    ax.set_title('Estimación de orden de magnitud', fontsize=10)
    fig.suptitle('Química de suelo y agua del sitio (escala logarítmica) y comparación con la resistividad observada', fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig(OUTF + 'fig18_quimica_suelo_agua.png', dpi=140, bbox_inches='tight'); plt.close(fig)


if __name__ == '__main__':
    shutil.copy(ENTRADA + 'photos_sheet.png', OUTF + 'fig00_fotos_sitio.png')
    what = sys.argv[1:] or ['ip', 'chem']
    if 'ip' in what: fig_scatter(pooled())
    if 'chem' in what: chem()
