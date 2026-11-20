import numpy as np, glob, os
from config import ENTRADA
FILES={i: ENTRADA + f'TOMOGRAFIA{i}.dat' for i in range(1,7)}

def read_dat(path):
    L=[l.strip() for l in open(path, encoding='latin-1').read().splitlines()]
    L=[l for l in L if l!='']
    hdr={'name':L[0].strip('"'),'a0':float(L[1]),'array':int(L[2]),'ndat':int(L[3]),
         'xtype':int(L[4]),'ip':int(L[5]),'ipname':L[6].strip('"'),'ipunit':L[7].strip('"')}
    hdr['delay'],hdr['integ']=[float(v) for v in L[8].split()]
    rows=[]
    for l in L[9:]:
        p=l.replace(',',' ').split()
        if len(p)>=5 and not all(float(v)==0 for v in p):
            rows.append([float(v) for v in p[:5]])
        elif len(p)==1 and float(p[0])==0:
            break
    a=np.array(rows)
    return hdr,a   # cols: x, a, n, rhoa, ip

if __name__=='__main__':
    for i,f in FILES.items():
        h,a=read_dat(f)
        print(i,h['name'],h['ndat'],len(a),'x:',a[:,0].min(),a[:,0].max(),'rhoa',a[:,3].min().round(1),a[:,3].max().round(1),'IP',a[:,4].min().round(2),a[:,4].max().round(2), 'neg rho',(a[:,3]<=0).sum(),'neg ip',(a[:,4]<0).sum())
        import collections
        c=collections.Counter(zip(a[:,1],a[:,2]))
        print('   (a,n):count', dict(sorted(c.items())))
        # max reach check
        L=2*a[:,1]*a[:,2]+a[:,1]
        print('   array length max',L.max(),' max end', (a[:,0]+L).max())
