"""Convierte lat/lon (WGS84) a UTM 14N (EPSG:32614) y arma datos/datos_utm.csv.
Entrada: datos/radiometria.csv con columnas  Est., lat, lon, DR, K, U, Th   (lat N, lon como negativo al oeste).
Cambia EPSG si tu zona no es la 14N (Puebla central: 32614)."""
import os, pandas as pd
from pyproj import Transformer
EPSG = 32614
HERE = os.path.dirname(os.path.abspath(__file__))
d = pd.read_csv(os.path.join(HERE, 'datos', 'radiometria.csv'))
t = Transformer.from_crs(4326, EPSG, always_xy=True)
d['E'], d['N'] = t.transform(d['lon'].values, d['lat'].values)
d = d[['Est.', 'lat', 'lon', 'E', 'N', 'DR', 'K', 'U', 'Th']]
d.to_csv(os.path.join(HERE, 'datos', 'datos_utm.csv'), index=False)
print(len(d), 'estaciones ->', os.path.join('datos', 'datos_utm.csv'))
