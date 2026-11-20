import json, pickle, numpy as np, matplotlib
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
DATOS = os.path.join(HERE, 'datos'); FIGS = os.path.join(HERE, 'figuras')
os.makedirs(DATOS, exist_ok=True); os.makedirs(FIGS, exist_ok=True)
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.patches import Polygon as MPoly, Rectangle
from matplotlib.collections import PolyCollection
from shapely.geometry import shape
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.linewidth':0.6})
OUT=FIGS+'/'; DAT=DATOS+'/'
COAPAN=(-97.4060,18.4274)   # iglesia de Santa Maria Coapan (OLC 76C4CHGV+XJ)

def draw_geom(ax, geom, **kw):
    polys = [geom] if geom.geom_type=='Polygon' else list(geom.geoms)
    for p in polys:
        ax.add_patch(MPoly(np.array(p.exterior.coords), closed=True, **kw))

# ------------------------------------------------ Fig 1: localizacion
mx = json.load(open(DAT+'mun_puebla.json'))
pm = json.load(open(DAT+'puebla_mun.json'))
pop = json.load(open(DAT+'pop.geojson'))
cities = {f['properties']['name']:f['geometry']['coordinates'] for f in pop['features']}
fig, axs = plt.subplots(1,3, figsize=(7.2,2.9), gridspec_kw={'width_ratios':[1.05,1,1]})
ax=axs[0]
for f in mx['features']:
    g=shape(f['geometry']); st=f['id']=='MX-PUE'
    draw_geom(ax,g,fc='#c0392b' if st else '#e8e8e8',ec='#777',lw=0.3)
ax.set_xlim(-118.5,-86); ax.set_ylim(14.3,33); ax.set_aspect(1.1); ax.set_xticks([]); ax.set_yticks([])
ax.text(-104,29.5,'MÉXICO',ha='center',fontsize=8,weight='bold',color='#333')
ax.annotate('Puebla',(-98.1,19.0),(-110,16.2),arrowprops=dict(arrowstyle='-',lw=0.6),fontsize=7.5)
ax.set_title('(a)',loc='left',fontsize=8)
ax=axs[1]
for f in pm['features']:
    g=shape(f['geometry']); t=f['properties']['NOM_MUN']=='Tehuacán'
    draw_geom(ax,g,fc='#c0392b' if t else '#f2f2f2',ec='#888',lw=0.25)
for n,lab,dx,dy in [('Puebla','Puebla',0.08,0.05),('Tehuacan','Tehuacán',0.1,-0.17),('Tlaxcala',None,0,0)]:
    if lab:
        c=cities[n]; ax.plot(*c,'ko',ms=2.5); ax.text(c[0]+dx,c[1]+dy,lab,fontsize=6.5)
b=[shape(f['geometry']).bounds for f in pm['features']]
ax.set_xlim(min(x[0] for x in b)-.05,max(x[2] for x in b)+.05); ax.set_ylim(min(x[1] for x in b)-.05,max(x[3] for x in b)+.05)
ax.set_aspect(1.06); ax.set_title('(b) Estado de Puebla',loc='left',fontsize=8)
ax.set_xlabel('Longitud (°O)'); ax.set_ylabel('Latitud (°N)')
ax=axs[2]
tg=[shape(f['geometry']) for f in pm['features'] if f['properties']['NOM_MUN']=='Tehuacán'][0]
bx=tg.bounds
for f in pm['features']:
    g=shape(f['geometry'])
    if g.intersects(tg.buffer(0.02)):
        t=f['properties']['NOM_MUN']=='Tehuacán'
        draw_geom(ax,g,fc='#f4d9d5' if t else '#f2f2f2',ec='#555',lw=0.5)
        if not t:
            c=g.representative_point(); 
            if False: ax.text(c.x,c.y,f['properties']['NOM_MUN'],fontsize=4.5,ha='center',color='#666')
c=cities['Tehuacan']; ax.plot(*c,'ko',ms=3); ax.text(c[0]+0.01,c[1]+0.03,'Tehuacán',fontsize=7,ha='left')
ax.plot(*COAPAN,marker='^',color='#c0392b',ms=7,mec='k',mew=0.5); ax.text(COAPAN[0]-0.01,COAPAN[1]-0.06,'Santa María\nCoapan',fontsize=7,color='#c0392b',weight='bold',ha='right')
ax.set_xlim(bx[0]-.05,bx[2]+.05); ax.set_ylim(bx[1]-.05,bx[3]+.05); ax.set_aspect(1.06)
ax.set_xlabel('Longitud (°O)'); ax.set_title('(c) Municipio de Tehuacán',loc='left',fontsize=8)
ax.annotate('',xy=(bx[0]+0.03,bx[1]+0.17),xytext=(bx[0]+0.03,bx[1]+0.07),arrowprops=dict(arrowstyle='-|>',lw=1))
ax.text(bx[0]+0.03,bx[1]+0.18,'N',ha='center',fontsize=7,weight='bold')
for a in axs[1:]: a.tick_params(labelsize=6.5)
plt.tight_layout(); plt.savefig(OUT+'f1_localizacion.png',dpi=300); plt.close()

# ------------------------------------------------ Fig 2: diseño de adquisicion (esquematico, coordenadas locales)
fig, ax = plt.subplots(figsize=(3.45,4.6))
land = np.array([[40,40],[330,25],[375,120],[355,250],[260,300],[110,295],[25,200],[20,110]])
ax.add_patch(MPoly(land,closed=True,fc='#e9d8c4',ec='#6b4a2b',lw=1.2,label='Polígono del relleno (aprox. 8 ha)'))
# malla EM/magnetometria
for gx in range(0,401,50): ax.plot([gx,gx],[0,320],color='#bbb',lw=0.3,zorder=1)
for gy in range(0,321,40): ax.plot([0,400],[gy,gy],color='#bbb',lw=0.3,zorder=1)
# lineas ERT (E-W) 235 m, 48 electrodos cada 5 m
x0=80
for i,y in enumerate([60,100,140,180,220,260]):
    ax.plot([x0,x0+235],[y,y],color='#1f4e9c',lw=1.6,zorder=3,label='Perfiles ERT/IP L1–L6' if i==0 else None)
    ax.text(x0-6,y,f'L{i+1}',ha='right',va='center',fontsize=6.5,color='#1f4e9c')
for j,xx in enumerate([150,260]):
    ax.plot([xx,xx],[40,280],color='#c0392b',lw=1.6,zorder=3,label='Perfiles transversales T1–T2 (N–S)' if j==0 else None)
    ax.text(xx,270 if False else 283,f'T{j+1}',ha='center',fontsize=6.5,color='#c0392b',bbox=dict(fc='white',ec='none',pad=0.5))
ax.plot([40,275],[-40,-40],color='#2a7f3f',lw=1.6,zorder=3,label='Perfil de fondo R1 (fuera del sitio)')
ax.text(30,-40,'R1',ha='right',va='center',fontsize=6.5,color='#2a7f3f')
for k,(px,py) in enumerate([(45,160),(345,150),(210,45),(190,310)]):
    ax.plot(px,py,'s',color='k',ms=5,zorder=5,label='Piezómetros propuestos P1–P4' if k==0 else None)
    ax.text(px+9,py+6,f'P{k+1}',fontsize=6.5)
ax.set_xlim(-30,420); ax.set_ylim(-60,345); ax.set_aspect(1)
ax.set_xlabel('Este local (m)'); ax.set_ylabel('Norte local (m)')
ax.legend(loc='upper center',bbox_to_anchor=(0.5,-0.16),fontsize=6,frameon=False,ncol=1)
ax.annotate('',xy=(395,320),xytext=(395,285),arrowprops=dict(arrowstyle='-|>',lw=1)); ax.text(395,326,'N',ha='center',fontsize=7,weight='bold')
ax.plot([300,400],[-45,-45],'k-',lw=2); ax.text(350,-41,'100 m',ha='center',fontsize=6.5,va='bottom')
ax.text(205,-18,'Malla EM y magnetometría',fontsize=6,color='#666',ha='center')
ax.set_title('Esquema en coordenadas locales (sin georreferencia)',fontsize=7)
plt.tight_layout(); plt.savefig(OUT+'f2_diseno.png',dpi=300); plt.close()

# ------------------------------------------------ Fig 3: modelo sintetico
from ert2d import Grid
from sim_ert import truth, NEL
D=pickle.load(open(DAT+'sim_data.pkl','rb')); I=pickle.load(open(DAT+'sim_inv.pkl','rb'))
x=D['x']; q=D['q']
xm=0.5*(x[q[:,2]]+x[q[:,3]]); L=np.abs(x[q[:,1]]-x[q[:,0]]); zp=0.17*L
g=Grid(np.zeros(NEL))
rho_inv=np.exp(I['m'])
norm=LogNorm(3,300); cm='turbo'
def blocks(ax,g,vals):
    polys=[[(px,pz) for px,pz in p] for p in g.par_poly]
    pc=PolyCollection(polys,array=vals,cmap=cm,norm=norm,edgecolors='none'); ax.add_collection(pc); return pc
fig,axs=plt.subplots(3,1,figsize=(3.45,5.2),sharex=True)
# (a) verdadero
gt_x=np.linspace(0,235,236); gt_z=np.linspace(0,35,141)
Xg,Zg=np.meshgrid(gt_x,gt_z); R=truth(Xg,Zg)
pcm=axs[0].pcolormesh(Xg,-Zg,R,cmap=cm,norm=norm,shading='auto')
axs[0].set_title('(a) Modelo verdadero (sintético)',loc='left',fontsize=7.5)
# (b) pseudoseccion
sc=axs[1].scatter(xm,-zp,c=D['rhoa'],cmap=cm,norm=norm,s=7,marker='s',lw=0)
axs[1].set_title('(b) Resistividad aparente simulada (+3 % de ruido)',loc='left',fontsize=7.5)
# (c) invertido
blocks(axs[2],g,rho_inv)
axs[2].set_title(f'(c) Modelo invertido (RMS = {I["rms"][-1]:.1f} %); punteado: cuerpos reales',loc='left',fontsize=7.5)
for a in axs:
    a.set_xlim(0,235); a.set_ylim(-35,0); a.set_ylabel('Profundidad (m)')
    a.set_aspect('auto')
axs[2].set_xlabel('Distancia (m)')
# anotaciones
axs[0].text(110,-11,'residuos',ha='center',fontsize=6.5,color='k')
axs[0].text(95,-4.8,'lodos',ha='center',fontsize=5.5,color='w',va='center')
axs[0].text(172,-19,'lixiviado',ha='center',fontsize=6.5,color='w',weight='bold')
for a in (axs[2],):
    for (x0,x1,z0,z1) in [(55,165,1.5,14),(120,215,10,24),(85,105,3,7)]:
        a.add_patch(Rectangle((x0,-z1),x1-x0,z1-z0,fill=False,ec='k',lw=0.7,ls='--'))
fig.subplots_adjust(hspace=0.45)
for a in axs: a.tick_params(labelbottom=True)
cb=fig.colorbar(pcm,ax=axs,orientation='horizontal',fraction=0.04,pad=0.16,aspect=35)
cb.set_label('Resistividad (Ω·m)',fontsize=7); cb.ax.tick_params(labelsize=6.5)
plt.savefig(OUT+'f3_sintetico.png',dpi=300,bbox_inches='tight'); plt.close()
print('ok')
