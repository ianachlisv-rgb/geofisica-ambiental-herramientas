"""Exporta: .dat con topografia (formato Res2DInv, topografia tipo 1), bitacora de edicion, modelos 2D XYZ, malla 3D XYZ y VTK."""
import sys, pickle
from plotlib import *
from parse_dat import FILES
import pandas as pd

import os
for d in ('datos', 'modelos', 'datos/res2dinv'): os.makedirs(OUT + d, exist_ok=True)
F, R = load_all()
M3 = pickle.load(open(W + 'model3d.pkl', 'rb')); V = M3['vol']; L = M3['lines']
TOPO = load_topo()

# ---------------- 1) .dat con topografia (+ version editada) y bitacora de edicion
log = []
for line in range(1, 7):
    raw = open(FILES[line], 'r', errors='ignore').read().replace('\r', '').split('\n')
    hdr = raw[:9]                       # nombre, a, tipo, ndatos, xtype, ip flag, nombre IP, unidad, delay/int
    r = R[line]; df = r['df_raw']; keep = r['keep']
    t = TOPO[line]
    topo_lines = ['1', str(len(t))] + [f'{x:.1f}\t{z:.1f}' for x, z in zip(t['electrodo_x_m'], t['elevacion_m'])] + ['1']
    # --- version A: TODOS los datos originales + topografia (para repetir el procesamiento completo en Res2DInv)
    def write(path, d, name_suffix):
        h = hdr.copy(); h[0] = h[0].strip('"') ; h[0] = f'"{h[0]}{name_suffix}"'; h[3] = str(len(d))
        rows = [f'{int(x)}\t{int(a)}\t{int(n)}\t{rh:.6f}\t{ip:.6f}' for x, a, n, rh, ip in zip(d.x, d.a, d.n, d.rhoa, d.ip)]
        txt = '\n'.join(h + rows + ['0'] + topo_lines + ['0', '0', '0', '0'])
        open(path, 'w', newline='\r\n').write(txt + '\n')
    write(OUT + f'datos/res2dinv/TOMOGRAFIA{line}_topo.dat', df, '_topo')
    write(OUT + f'datos/res2dinv/TOMOGRAFIA{line}_topo_editado.dat', df[keep], '_topo_editado')
    # --- bitacora
    fl = r['flagged']
    for i, (_, row) in enumerate(df.iterrows()):
        if keep[i]: continue
        motivo = []
        bad = [e for e in fl if row.M == e or row.N == e]
        if bad: motivo.append(f'electrodo de potencial {bad[0]} con datos sistematicamente malos (IP>10 ms o desajuste>20 %)')
        else: motivo.append(f'dato atipico: |desajuste| > {r["thr"]:.0f} % tras primera inversion')
        log.append(dict(linea=f'TKI{line}', x_m=row.x, a_m=row.a, n=row.n, rhoa_ohm_m=round(row.rhoa, 2), IP_ms=round(row.ip, 2), motivo='; '.join(motivo)))
pd.DataFrame(log).to_csv(OUT + 'datos/bitacora_edicion_datos.csv', index=False)
print('bitacora', len(log))
# IP: datos eliminados solo para el modelo de cargabilidad
rows = []
for line in range(1, 7):
    f = F[line]; df = f['df']; k = f['ip_keep']
    for i in np.where(~k)[0]:
        rows.append(dict(linea=f'TKI{line}', x_m=df.x.iloc[i], a_m=df.a.iloc[i], n=df.n.iloc[i], IP_ms=round(df.ip.iloc[i], 2), motivo='atipico en cargabilidad (criterio robusto)'))
pd.DataFrame(rows).to_csv(OUT + 'datos/bitacora_edicion_IP.csv', index=False)
print('IP removed', len(rows))

# ---------------- 2) modelos 2D: bloques de la inversion y seccion fina georreferenciada
for line in range(1, 7):
    g, fw, df = build(line, use=R[line]['keep'])
    nel, nz = g.nel, g.nz
    xs = np.repeat(g.xel, nz); dpar = par_depth(g)
    zsurf = np.interp(xs, g.xel, g.Z[g.ixc0+1+2*np.arange(nel), 0])
    t = TOPO[line]
    E = np.interp(xs, t['electrodo_x_m'], t['Este_m']); N = np.interp(xs, t['electrodo_x_m'], t['Norte_m'])
    mod = pd.DataFrame(dict(x_m=xs, Este=E, Norte=N, profundidad_m=dpar, elevacion_m=zsurf-dpar, resistividad_ohm_m=F[line]['rho'], cargabilidad_ms=F[line]['ip_m']))
    mod.round(3).to_csv(OUT + f'datos/modelo2D_bloques_TKI{line}.csv', index=False)
    s = L[line]
    X, D = np.meshgrid(s['x'], s['d'], indexing='ij')
    ok = np.isfinite(s['logrho'])
    fine = pd.DataFrame(dict(x_m=X[ok], Este=np.repeat(s['E'][:, None], len(s['d']), 1)[ok], Norte=np.repeat(s['N'][:, None], len(s['d']), 1)[ok],
                             elevacion_m=s['Z'][ok], profundidad_m=D[ok], resistividad_ohm_m=10**s['logrho'][ok], cargabilidad_ms=s['ip'][ok]))
    fine.round(3).to_csv(OUT + f'datos/modelo2D_fino_XYZ_TKI{line}.csv', index=False)

# ---------------- 3) malla 3D XYZ + VTK
Eg, Ng, Dg, DEM = V['Eg'], V['Ng'], V['Dg'], V['DEM']
EE, NN, DD = np.meshgrid(Eg, Ng, Dg, indexing='ij')
ZZ = DEM[:, :, None] - DD
LR, IPv = V['logrho'], V['ip']
ok = np.isfinite(LR)
m3 = pd.DataFrame(dict(Este=EE[ok], Norte=NN[ok], Elevacion_m=ZZ[ok], Profundidad_m=DD[ok], Resistividad_ohm_m=10**LR[ok], Cargabilidad_ms=IPv[ok]))
m3.round(3).to_csv(OUT + 'datos/modelo3D_malla_XYZ.csv', index=False)
print('3D rows', len(m3))
# VTK legacy ascii (STRUCTURED_GRID) para Paraview / Voxler
nE, nN, nD = LR.shape
with open(OUT + 'modelos/modelo3D_resistividad_IP.vtk', 'w') as fo:
    fo.write('# vtk DataFile Version 3.0\nModelo 3D ERT/IP Taman Kepong Indah (interpolacion IDW, profundidad bajo la superficie)\nASCII\nDATASET STRUCTURED_GRID\n')
    fo.write(f'DIMENSIONS {nE} {nN} {nD}\nPOINTS {nE*nN*nD} float\n')
    P = np.stack([EE, NN, ZZ], -1)                  # orden VTK: x rapido -> usar transposicion
    P = np.transpose(P, (2, 1, 0, 3)).reshape(-1, 3)
    np.savetxt(fo, P, fmt='%.2f')
    fo.write(f'POINT_DATA {nE*nN*nD}\n')
    for name, arr in (('resistividad_ohm_m', np.where(ok, 10**LR, -9999.0)), ('log10_resistividad', np.where(ok, LR, -9999.0)), ('cargabilidad_ms', np.where(ok, IPv, -9999.0)), ('profundidad_m', DD)):
        fo.write(f'SCALARS {name} float 1\nLOOKUP_TABLE default\n')
        np.savetxt(fo, np.transpose(arr, (2, 1, 0)).reshape(-1), fmt='%.4g')
print('ok')
