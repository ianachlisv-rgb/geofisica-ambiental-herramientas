# Mapas de radiometría (RS-125) en Python

Dos scripts para pasar de las lecturas del espectrómetro a mapas 2D de **tasa de dosis (DR)**, **K (%)**, **eU (ppm)** y **eTh (ppm)**.

| Script | Qué hace |
|---|---|
| `crear_datos_utm.py` | Convierte lat/lon (WGS84) a UTM y arma `datos/datos_utm.csv` |
| `corregir_coordenadas.py` | Ajusta las coordenadas del GPS del teléfono a un mallado regular de líneas paralelas |
| `mapas_radiometria.py` | Interpola (thin-plate spline) y dibuja los mapas, razones K/U/Th y la figura de corrección |

## Datos de entrada
Crea la carpeta `datos/` con `radiometria.csv` y las columnas `Est., lat, lon, DR, K, U, Th`
(una fila por estación). Luego:

```
pip install numpy pandas scipy matplotlib pyproj
python crear_datos_utm.py
python corregir_coordenadas.py
python mapas_radiometria.py
```
Los resultados salen en `salida/`.

## Importante: adapta esto a tu levantamiento
`corregir_coordenadas.py` tiene escrito el diseño del levantamiento original: cinco líneas
(`LINEAS`), el sentido de caminata en serpentina (`DIR`), las estaciones fuera del mallado (`EXT`) y
una separación de 3.5 m. Cámbialos por los tuyos. Si tus puntos no forman un mallado regular,
omite ese paso y usa tus coordenadas directamente.

Los datos del levantamiento original no se incluyen.
