"""Ajusta un mallado regular (5 líneas paralelas, puntos cada s m) a las coordenadas GPS del teléfono.
Las estaciones 11-14 están fuera del mallado y conservan su coordenada GPS."""
import os, numpy as np, pandas as pd
from scipy.optimize import least_squares
from pyproj import Transformer

HERE=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(HERE,'salida')+os.sep; os.makedirs(OUT,exist_ok=True)
d=pd.read_csv(os.path.join(HERE,'datos','datos_utm.csv'))   # columnas: Est., lat, lon, E, N, DR, K, U, Th
E0,N0=d.E.min()-10,d.N.min()-10
d['x']=d.E-E0; d['y']=d.N-N0
LINEAS={'A':range(1,11),'B':range(15,25),'C':range(25,31),'D':range(31,39),'E':range(39,45)}
DIR={'A':+1,'B':-1,'C':+1,'D':-1,'E':+1}               # sentido de caminata (serpentina): N, S, N, S, N
EXT=[11,12,13,14]
rows=[]
for li,(L,est) in enumerate(LINEAS.items()):
    for k,e in enumerate(est): rows.append((int(e),L,li,k))
g=pd.DataFrame(rows,columns=['Est.','Linea','li','k']).merge(d[['Est.','x','y']],on='Est.')

def modelo(p,s,dsep=None):
    Ox,Oy,th,dl=p[:4]; v0=p[4:9]
    if dsep is not None: dl=dsep
    t=np.array([np.sin(th),np.cos(th)]); n=np.array([np.cos(th),-np.sin(th)])
    v=v0[g.li.values]+np.array([DIR[l] for l in g.Linea])*g.k.values*s
    return np.c_[Ox+n[0]*g.li.values*dl+t[0]*v, Oy+n[1]*g.li.values*dl+t[1]*v]
def res(p,s,dsep=None): return (modelo(p,s,dsep)-g[['x','y']].values).ravel()
p0=np.array([10,10,np.radians(20),3.5, 0,35,3,24,3.0])
out={}
for nombre,s,libre_d in [('3.5 m en ambos ejes',3.5,False),('paso entre líneas libre',3.5,True)]:
    f=lambda p: res(p,s,None if libre_d else 3.5)
    r=least_squares(f,p0,loss='soft_l1',f_scale=2.0)
    dd=r.x[3] if libre_d else 3.5
    rr=np.hypot(*f(r.x).reshape(-1,2).T)
    out[nombre]=(r.x,dd,rr)
    print(f'{nombre}: azimut={np.degrees(r.x[2]):.1f}°, sep. líneas={dd:.2f} m, RMS={np.sqrt((rr**2).mean()):.2f} m, máx={rr.max():.1f} m')
# resultado adoptado: mallado 3.5 x 3.5 m
p,dd,rr=out['3.5 m en ambos ejes']
xy=modelo(p,3.5,3.5)
g['xc']=xy[:,0]; g['yc']=xy[:,1]; g['desp_m']=rr
# puntos externos: sin cambio
ext=d[d['Est.'].isin(EXT)][['Est.','x','y']].copy(); ext['xc']=ext.x; ext['yc']=ext.y; ext['Linea']='fuera'; ext['desp_m']=0.0
c=pd.concat([g[['Est.','Linea','x','y','xc','yc','desp_m']],ext[['Est.','Linea','x','y','xc','yc','desp_m']]]).sort_values('Est.')
c['E_orig']=c.x+E0; c['N_orig']=c.y+N0; c['E_corr']=c.xc+E0; c['N_corr']=c.yc+N0
inv=Transformer.from_crs('EPSG:32614','EPSG:4326',always_xy=True)
lo,la=inv.transform(c.E_corr.values,c.N_corr.values); c['lat_corr']=la; c['lon_corr']=lo
c=c.merge(d[['Est.','lat','lon','DR','K','U','Th']],on='Est.')
c.to_csv(OUT+'coordenadas_corregidas.csv',index=False)
print(c.sort_values('desp_m',ascending=False)[['Est.','Linea','desp_m']].head(8).to_string(index=False))
print('despl. medio',c[c.Linea!='fuera'].desp_m.mean().round(2),'m')
