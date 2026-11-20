"""Descarga los limites estatales/municipales y ciudades que usa figuras.py (fuentes abiertas, ver README)."""
import os, urllib.request
DATOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'datos'); os.makedirs(DATOS, exist_ok=True)
URLS = {
 'mun_puebla.json': 'https://raw.githubusercontent.com/angelnmara/geojson/master/mexicoHigh.json',            # estados de Mexico
 'puebla_mun.json': 'https://raw.githubusercontent.com/PhantomInsights/mexico-geojson/main/2020/states/Puebla.json',  # municipios de Puebla
 'pop.geojson': 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_populated_places_simple.geojson',  # ciudades
}
for n, u in URLS.items():
    d = os.path.join(DATOS, n)
    if not os.path.exists(d):
        print('descargando', n); urllib.request.urlretrieve(u, d)
print('listo')
