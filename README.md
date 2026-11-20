# Geofísica ambiental: herramientas y plantillas

Código y plantillas que usé en reportes y proyectos de geofísica ambiental, para que otras personas los reutilicen o los adapten.

**Autor:** Ian A. Sandoval-Valderrábano, Facultad de Ingeniería, Benemérita Universidad Autónoma de Puebla (BUAP).

| Carpeta | Contenido |
|---|---|
| [`ert-ip-python`](ert-ip-python) | Tomografía de resistividad eléctrica (ERT) e IP en Python: modelado directo por elementos finitos con topografía, inversión suavizada, modelo 3D y figuras |
| [`ert-ip-python/ejemplo_relleno_sintetico`](ert-ip-python/ejemplo_relleno_sintetico) | Ejemplo completo con datos sintéticos de un relleno sanitario (sin datos externos) |
| [`radiometria-mapas`](radiometria-mapas) | Mapas 2D de radiometría (DR, K, eU, eTh) a partir de lecturas de un espectrómetro y GPS de teléfono |
| [`excel-diferencias-finitas`](excel-diferencias-finitas) | Libro de Excel con diferencias finitas para conducción de calor 1D (Jacobi, Gauss-Seidel y solución directa) |
| [`plantilla-ieee-latex`](plantilla-ieee-latex) | Plantilla de informe tipo IEEE en español (compila con LaTeX sin la clase oficial; instrucciones para Overleaf) |

## Repositorios por proyecto
Cada proyecto tiene además su propio repositorio, con el artículo en PDF:

| Repositorio | Proyecto |
|---|---|
| [`ert-relleno-coapan`](https://github.com/ianachlisv-rgb/ert-relleno-coapan) | Levantamiento geofísico y simulación de ERT para el relleno sanitario de Santa María Coapan (Puebla) |
| [`ert-ip-kuala-lumpur`](https://github.com/ianachlisv-rgb/ert-ip-kuala-lumpur) | ERT e IP en un sitio de residuos de Kuala Lumpur, con inversión propia en Python |
| [`ert-dayat-ben-fellah`](https://github.com/ianachlisv-rgb/ert-dayat-ben-fellah) | Anomalías de resistividad en Dayat Ben Fellah (Argelia), con lector y pseudosecciones de datos Wenner |
| [`mapas-radiometria`](https://github.com/ianachlisv-rgb/mapas-radiometria) | Mapas de radiometría con espectrómetro RS-125, con ejemplo sintético |
| [`diferencias-finitas-calor-1d`](https://github.com/ianachlisv-rgb/diferencias-finitas-calor-1d) | Hoja de Excel de conducción de calor 1D |
| [`densidad-poblacion-tlaxcala-qgis`](https://github.com/ianachlisv-rgb/densidad-poblacion-tlaxcala-qgis) | Densidad de población de Tlaxcala con QGIS, con script en Python |

## Qué no se incluye
Los datos de campo y de clase, las fotos y los informes completos no están en este repositorio. Cada carpeta explica
qué archivos de entrada necesita y con qué formato.

## Advertencias
- El código de ERT/IP es una implementación propia: sus resultados **no son numéricamente idénticos** a los de programas comerciales como Res2DInv.
- Revisa los parámetros (umbrales, factores de regularización, diseño del levantamiento) antes de usarlos con tus datos.
- El ejemplo sintético usa valores supuestos de la literatura; no representa ningún sitio real.

## Licencia
MIT (ver [`LICENSE`](LICENSE)). Si lo usas en un trabajo, cita este repositorio.
