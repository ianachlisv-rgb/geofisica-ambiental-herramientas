"""Mapas 2D de radiometría (RS-125): DR total, K, U y Th. Lee Radiometria_datos.xlsx (hoja Radiometría)."""
import os, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pyproj import Transformer
from scipy.interpolate import RBFInterpolator
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
XLS = os.path.join(HERE, 'datos', 'Radiometria_datos.xlsx')   # tu libro de datos (ver README)
OUT = os.path.join(HERE, 'salida') + os.sep
os.makedirs(OUT, exist_ok=True)
c = pd.read_csv(OUT+'coordenadas_corregidas.csv')   # lo genera corregir_coordenadas.py
c = c.rename(columns={'Est.':'Est'})
E0, N0 = c.E_orig.min()-10, c.N_orig.min()-10   # mismo origen que corregir_coordenadas.py
c['x'] = c.E_corr-E0; c['y'] = c.N_corr-N0
df = c[c.Linea!='fuera'].sort_values('Est').reset_index(drop=True)      # mallado
ext = c[c.Linea=='fuera'].sort_values('Est').reset_index(drop=True)     # puntos fuera del mallado
df = df.rename(columns={'Est':'Est.'}); ext = ext.rename(columns={'Est':'Est.'})
x, y = df.x.values, df.y.values
xe, ye = ext.x.values, ext.y.values
gx = np.arange(-1, max(x.max(),xe.max())+8, 0.25); gy = np.arange(-1, max(y.max(),ye.max())+8, 0.25)
GX, GY = np.meshgrid(gx, gy)
tree = cKDTree(np.c_[x,y]); d,_ = tree.query(np.c_[GX.ravel(),GY.ravel()]); mask = (d.reshape(GX.shape) > 3.5)   # >3.5 m (un paso del mallado) del dato más cercano

def interp(v):
    rbf = RBFInterpolator(np.c_[x,y], v, kernel='thin_plate_spline', smoothing=4.0)
    z = rbf(np.c_[GX.ravel(),GY.ravel()]).reshape(GX.shape)
    z = np.clip(z, v.min(), v.max()); z[mask] = np.nan; return z

vars_ = [('DR','Tasa de dosis total (DR)','nSv/h','jet'),('K','Potasio (K)','%','jet'),
         ('U','Uranio equivalente (eU)','ppm','jet'),('Th','Torio equivalente (eTh)','ppm','jet')]
plt.rcParams.update({'font.size':9,'font.family':'DejaVu Sans'})

def panel(ax, key, title, unit, cmap, cb=True):
    z = interp(df[key].values)
    im = ax.contourf(GX, GY, z, levels=np.linspace(min(df[key].min(),ext[key].min()), df[key].max(), 16), cmap=cmap)
    ax.scatter(x, y, c='k', s=7, zorder=3)
    for L,gr in df.groupby('Linea'): ax.plot(gr.x, gr.y, 'k-', lw=0.4, alpha=0.5, zorder=2)
    dn = ext.y.mean()-y.max()
    ins = ax.inset_axes([0.2,0.77,0.6,0.17])
    ins.scatter(xe, ye, c=ext[key].values, cmap=cmap, vmin=im.levels[0], vmax=im.levels[-1], s=45, edgecolor='k', zorder=3)
    for e,xi,yi in zip(ext['Est.'],xe,ye): ins.annotate(str(int(e)),(xi,yi),xytext=(4,3),textcoords='offset points',fontsize=6)
    ins.margins(0.35); ins.set_aspect('equal',adjustable='datalim'); ins.set_xticks([]); ins.set_yticks([])
    ins.set_title(f'Afloramiento, Est. 11-14 (≈{dn:.0f} m al N)',fontsize=6.5,pad=2)
    for e,xi,yi in zip(df['Est.'],x,y):
        if int(e)%5==0: ax.annotate(f'{int(e)}',(xi,yi),xytext=(3,3),textcoords='offset points',fontsize=6)
    ax.set_aspect('equal'); ax.set_ylim(y.min()-6, y.max()+22); ax.set_xlim(x.min()-6, x.max()+6); ax.set_title(f'{title}', fontsize=10)
    ax.set_xlabel('Este local (m)'); ax.set_ylabel('Norte local (m)')
    c = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.03); c.set_label(f'{unit}'); tk=np.linspace(im.levels[0],im.levels[-1],6); c.set_ticks(tk); c.ax.set_yticklabels([f'{t:.2f}'.rstrip('0').rstrip('.') for t in tk])
    return z

# --- mapas individuales
for key,title,unit,cmap in vars_:
    fig, ax = plt.subplots(figsize=(4.2,5.6)); panel(ax,key,f'{title} ({unit})',unit,cmap)
    ax.text(0.02,0.015,'● punto de medición (número cada 5)',transform=ax.transAxes,fontsize=6.5)
    fig.tight_layout(); fig.savefig(OUT+f'mapa_{key}.png', dpi=250); plt.close(fig)

# --- panel 2x2
fig, axs = plt.subplots(1,4, figsize=(15,5.6))
for ax,(key,title,unit,cmap) in zip(axs,vars_): panel(ax,key,f'{title} ({unit})',unit,cmap)
fig.suptitle('Radiometría terrestre, RS-125 Super-SPEC · 60 s por punto · UTM 14N (WGS84) · origen local: 585789 E, 2085851 N · coordenadas ajustadas a mallado de 3.5 m', fontsize=11)
fig.tight_layout(); fig.savefig(OUT+'mapas_radiometria_panel.png', dpi=220); plt.close(fig)

# --- razones
df['eU/eTh'] = df.U/df.Th.replace(0,np.nan); df['K/eTh'] = df.K/df.Th.replace(0,np.nan)
fig, axs = plt.subplots(1,2, figsize=(8.5,6))
for ax,(k,t) in zip(axs,[('eU/eTh','Razón eU/eTh'),('K/eTh','Razón K/eTh (%/ppm)')]):
    v = df[k].values; z = interp(np.nan_to_num(v, nan=np.nanmedian(v)))
    im = ax.contourf(GX,GY,z,levels=15,cmap='viridis'); ax.scatter(x,y,c='k',s=6); ax.set_aspect('equal'); ax.set_title(t)
    ax.set_xlabel('Este local (m)'); ax.set_ylabel('Norte local (m)'); plt.colorbar(im,ax=ax,shrink=0.8)
fig.tight_layout(); fig.savefig(OUT+'mapas_razones.png', dpi=220); plt.close(fig)
print(df[['DR','K','U','Th']].describe().round(2)); print('extensión E,N (m):', x.max(), y.max())

# --- antes / después de la corrección
fig, ax = plt.subplots(figsize=(5.2,6.2))
ax.plot(c.E_orig-E0, c.N_orig-N0, 'o', c='tab:red', ms=4, label='GPS del teléfono')
for _,r in c[c.Linea!='fuera'].iterrows():
    ax.plot([r.E_orig-E0, r.E_corr-E0],[r.N_orig-N0, r.N_corr-N0],'-',c='0.6',lw=0.6)
ax.plot(df.x, df.y, 's', c='k', ms=3.5, label='corregida (mallado 3.5 m)')
for L,gr in df.groupby('Linea'):
    ax.plot(gr.x, gr.y, 'k-', lw=0.5); ax.annotate(L,(gr.x.iloc[0],gr.y.iloc[0]),xytext=(-8,-10),textcoords='offset points',fontsize=8,weight='bold')
ax.set_aspect('equal'); ax.set_ylim(y.min()-6, y.max()+22); ax.set_xlim(x.min()-6, x.max()+6)
ax.set_xlabel('Este local (m)'); ax.set_ylabel('Norte local (m)'); ax.legend(loc='upper left',fontsize=7)
ax.set_title('Corrección de coordenadas: líneas A–E', fontsize=10); ax.grid(alpha=.25)
fig.tight_layout(); fig.savefig(OUT+'correccion_coordenadas.png', dpi=220); plt.close(fig)

# --- afloramiento vs mallado
fig, axs = plt.subplots(1,5, figsize=(14,4.6), gridspec_kw={'width_ratios':[1.5,1,1,1,1]})
a0=axs[0]; a0.plot(x,y,'k.',ms=4,label='mallado (40 puntos)')
a0.scatter(xe,ye,c='tab:red',s=40,edgecolor='k',label='afloramiento (Est. 11-14)',zorder=3)
for e,xi,yi in zip(ext['Est.'],xe,ye): a0.annotate(str(int(e)),(xi,yi),xytext=(4,3),textcoords='offset points',fontsize=7)
a0.set_aspect('equal'); a0.set_xlabel('Este local (m)'); a0.set_ylabel('Norte local (m)'); a0.legend(fontsize=7,loc='upper center',bbox_to_anchor=(0.5,-0.14)); a0.set_title('Ubicación',fontsize=10); a0.grid(alpha=.25)
rng=np.random.default_rng(1)
for ax,(key,title,unit,_) in zip(axs[1:],vars_):
    ax.boxplot(df[key].values, positions=[0], widths=0.5, showfliers=False)
    ax.scatter(rng.normal(0,0.05,len(df)), df[key], s=8, c='0.5', zorder=3)
    ax.scatter(np.full(len(ext),1), ext[key], c='tab:red', s=40, edgecolor='k', zorder=4)
    for e,v in zip(ext['Est.'],ext[key]): ax.annotate(str(int(e)),(1,v),xytext=(7,-2),textcoords='offset points',fontsize=7)
    ax.set_xticks([0,1]); ax.set_xticklabels(['Mallado\n(n=40)','Afloramiento\n(n=4)']); ax.set_xlim(-0.6,1.6)
    ax.set_title(f'{title.split("(")[0].strip()} ({unit})',fontsize=9); ax.grid(alpha=.25,axis='y')
fig.suptitle('Afloramiento (Est. 11-14) frente al mallado', fontsize=11); fig.tight_layout(); fig.savefig(OUT+'afloramiento_vs_mallado.png', dpi=220); plt.close(fig)
print('mallado:', df[['DR','K','U','Th']].mean().round(2).to_dict()); print('afloramiento:', ext[['DR','K','U','Th']].mean().round(2).to_dict())
