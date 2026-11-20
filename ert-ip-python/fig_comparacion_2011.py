"""Comparacion con el reporte de 2011 (Umor y Arifin, relleno de Taman Nanyang/Wahyu/Delima, Kepong).
(a) distribucion de resistividad de los modelos TKI frente a los umbrales que uso ese reporte;
(b) RMS de las inversiones de ambos estudios.
Cifras del reporte de 2011 leidas de sus figuras 8 a 12 (RMS) y de su seccion 9 (umbrales)."""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from config import OUT, PF

plt.rcParams.update({'font.size': 6.5, 'axes.titlesize': 7, 'axes.labelsize': 6.5, 'xtick.labelsize': 6, 'ytick.labelsize': 6,
                     'legend.fontsize': 5.8, 'axes.linewidth': 0.6, 'xtick.major.width': 0.5, 'ytick.major.width': 0.5})

RMS_KPG = [10.6, 9.0, 10.2, 6.3, 6.1]          # reporte 2011, KPG01..KPG05
RMS_TKI = [6.9, 6.9, 5.4, 6.4, 5.9, 7.4]       # este trabajo, TKI1..TKI6

r = np.concatenate([pd.read_csv(OUT + f'datos/modelo2D_fino_XYZ_TKI{l}.csv').resistividad_ohm_m.values for l in range(1, 7)])
print('celdas', len(r), 'min', r.min().round(2), 'mediana', np.median(r).round(1), '<10:', (r < 10).mean() * 100, '<30:', (r < 30).mean() * 100)

fig, axs = plt.subplots(1, 2, figsize=(7.16, 2.5), gridspec_kw=dict(width_ratios=[1.55, 1]))
ax = axs[0]
bins = np.logspace(np.log10(0.03), np.log10(2500), 70)
ax.axvspan(0.03, 1, color='#9ecae1', alpha=0.55, lw=0)
ax.axvspan(1, 10, color='#c6dbef', alpha=0.55, lw=0)
ax.axvspan(10, 2500, color='#f0f0f0', alpha=0.8, lw=0)
h, _ = np.histogram(r, bins=bins)
ax.stairs(h / h.sum() * 100, bins, fill=True, color='#d95f02', alpha=0.85, lw=0.5, ec='k')
ymax = h.max() / h.sum() * 100 * 1.12
ax.set_xscale('log'); ax.set_xlim(0.03, 2500); ax.set_ylim(0, ymax)
ax.set_xlabel('Resistividad (Ω·m)'); ax.set_ylabel('Celdas de los modelos TKI (%)')
ax.text(0.17, ymax*0.93, 'lixiviado\n(< 1 Ω·m)', ha='center', va='top', fontsize=5.8)
ax.text(3.2, ymax*0.93, 'cubierta\nhúmeda\n(1–10)', ha='center', va='top', fontsize=5.8)
ax.text(600, ymax*0.93, 'cubierta seca\n(> 10 Ω·m)', ha='center', va='top', fontsize=5.8)
ax.axvline(r.min(), color='k', ls=':', lw=0.8)
ax.axvline(27.2, color='#7a0177', ls='--', lw=0.8)
ax.text(75, ymax*0.66, 'unos 27 Ω·m: límite de las zonas\n«lixiviado» de KPG04 (leyenda)', fontsize=5.5, color='#7a0177', va='center', ha='left')
ax.annotate(f'mínimo TKI\n{r.min():.1f} Ω·m', xy=(r.min(), ymax*0.55), xytext=(1.6, ymax*0.55), fontsize=5.8, va='center',
            arrowprops=dict(arrowstyle='-|>', lw=0.6, color='k'))
ax.set_title('(a) TKI frente a los umbrales del texto de 2011', loc='left')
ax.grid(alpha=0.3, lw=0.4, which='major')

ax = axs[1]
x1 = np.arange(5); x2 = np.arange(6) + 6.0
ax.bar(x1, RMS_KPG, color='#9e9e9e', ec='k', lw=0.4, label='2011 (Wenner, KPG01–05)')
ax.bar(x2, RMS_TKI, color='#1b9e77', ec='k', lw=0.4, label='Este trabajo (W–S, TKI1–6)')
for xx, v in zip(np.r_[x1, x2], RMS_KPG + RMS_TKI):
    ax.text(xx, v + 0.2, f'{v:.1f}', ha='center', fontsize=5.3)
ax.set_xticks(np.r_[x1, x2]); ax.set_xticklabels([f'{i}' for i in range(1, 6)] + [f'{i}' for i in range(1, 7)])
ax.set_xlabel('Número de línea'); ax.set_ylabel('RMS (%)'); ax.set_ylim(0, 13.5)
ax.legend(loc='upper right', handlelength=1.0, frameon=False)
ax.set_title('(b) Ajuste de las inversiones', loc='left')
ax.grid(alpha=0.3, lw=0.4, axis='y')

fig.tight_layout(pad=0.4, w_pad=1.0)
os.makedirs(PF, exist_ok=True)
fig.savefig(PF + 'p_comp2011.png', dpi=300, bbox_inches='tight', pad_inches=0.02)
print('ok', PF + 'p_comp2011.png')
