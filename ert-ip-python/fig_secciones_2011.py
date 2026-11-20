"""Seccion KPG04 del estudio de 2011 (imagen recortada de su informe) junto a una linea TKI dibujada con la misma
escala de colores que la leyenda de esa figura (17 colores; limites leidos de la leyenda e interpolados en log)."""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from PIL import Image
from config import ENTRADA, OUT, PF

plt.rcParams.update({'font.size': 6.5, 'axes.titlesize': 7, 'axes.labelsize': 6.5, 'xtick.labelsize': 6, 'ytick.labelsize': 6, 'axes.linewidth': 0.6})
# colores de las 17 casillas de la leyenda de KPG04 (RGB) y limites entre casillas
COL = [(4,4,72),(1,5,101),(11,11,148),(8,15,149),(13,89,164),(23,171,169),(13,129,89),(19,169,20),(14,87,12),
       (97,135,19),(176,178,25),(124,95,12),(160,101,14),(156,14,18),(141,6,11),(67,16,44),(68,4,65)]
LAB = [0.03, 5.75, 12.5, 27.2, 59.0, 128, 279, 606]            # rotulos de la leyenda (limites 1|2, 3|4, ..., 15|16)
E = [LAB[0], np.sqrt(LAB[0]*LAB[1]), LAB[1]]                    # 0.03 | 0.415 | 5.75
for a, b in zip(LAB[1:-1], LAB[2:]): E += [np.sqrt(a*b), b]
E += [LAB[-1]*1.47]                                              # ultimo limite
edges = np.array(E); print(len(edges), 'limites ->', len(COL), 'casillas'); assert len(edges) == len(COL) - 1
cmap = ListedColormap(np.array(COL) / 255.0); norm = BoundaryNorm(np.r_[1e-3, edges, 1e5], cmap.N)

LINE = 2
d = pd.read_csv(OUT + f'datos/modelo2D_fino_XYZ_TKI{LINE}.csv')
fig = plt.figure(figsize=(7.16, 4.6))
ax0 = fig.add_axes([0.0, 0.52, 1.0, 0.46]); ax0.imshow(Image.open(ENTRADA + 'umor2011_KPG04.png')); ax0.axis('off')
ax0.text(0.0, 1.0, '(a) KPG04, estudio de 2011 (Umor y Arifin)', transform=ax0.transAxes, fontsize=7, va='bottom')
ax = fig.add_axes([0.085, 0.14, 0.90, 0.28])
cs = ax.tricontourf(d.x_m, d.elevacion_m, d.resistividad_ohm_m, levels=np.r_[1e-3, edges, 1e5], cmap=cmap, norm=norm)
ax.tricontour(d.x_m, d.elevacion_m, d.resistividad_ohm_m, levels=[27.2], colors='k', linewidths=0.6, linestyles=':')
ax.set_aspect('equal'); ax.set_xlabel('Distancia x (m)'); ax.set_ylabel('Elevación (m)')
ax.set_title(f'(b) TKI{LINE} (este trabajo), misma escala de colores. Línea punteada: 27 Ω·m', loc='left')
cax = fig.add_axes([0.25, 0.04, 0.5, 0.025])
cb = matplotlib.colorbar.ColorbarBase(cax, cmap=cmap, norm=BoundaryNorm(np.arange(len(COL) + 1), cmap.N), orientation='horizontal', ticks=np.arange(len(COL)) + 1.0)
bl = [0.03, 0.4, 5.75, 8.5, 12.5, 18.4, 27.2, 40, 59, 87, 128, 189, 279, 411, 606, 890]
cb.set_ticks(np.arange(1, 17)); cb.set_ticklabels([f'{v:g}' for v in bl]); cb.ax.tick_params(labelsize=4.8, length=1.5)
cb.set_label('Resistividad (Ω·m), límites aproximados', fontsize=5.8)
fig.savefig(PF + 'p_secc2011.png', dpi=300, bbox_inches='tight', pad_inches=0.02); print('ok')
d1 = d.resistividad_ohm_m; print('TKI', LINE, 'celdas < 27.2:', round((d1 < 27.2).mean()*100, 1), '%')
