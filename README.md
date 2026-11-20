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

## Qué no se incluye
Los datos de campo y de clase, las fotos y los informes completos no están en este repositorio. Cada carpeta explica
qué archivos de entrada necesita y con qué formato.

## Advertencias
- El código de ERT/IP es una implementación propia: sus resultados **no son numéricamente idénticos** a los de programas comerciales como Res2DInv.
- Revisa los parámetros (umbrales, factores de regularización, diseño del levantamiento) antes de usarlos con tus datos.
- El ejemplo sintético usa valores supuestos de la literatura; no representa ningún sitio real.

## Licencia
MIT (ver [`LICENSE`](LICENSE)). Si lo usas en un trabajo, cita este repositorio.
