> **Nota:** los datos de entrada (`entrada/`: archivos `.dat`, topografía y tablas químicas) no se incluyen: pertenecen a un conjunto de datos público publicado (Data in Brief) y a material de clase. Para usar el código con tus datos, crea `entrada/` con el mismo formato (ver `parse_dat.py` y `ert_tools.py`). El módulo `ejemplo_relleno_sintetico/` corre sin datos externos.

CODIGO PYTHON - ERT/IP Taman Kepong Indah (TKI1 a TKI6)
Ian A. Sandoval-Valderrabano - Facultad de Ingenieria, BUAP
=========================================================================

QUE ES
------
Pipeline completo, escrito por mi, que reemplaza a Res2DInv/Voxler en este trabajo:
  - modelado directo 2.5D por elementos finitos con topografia
  - inversion de resistividad Gauss-Newton con suavidad (tipo Occam / Res2DInv)
  - inversion lineal de cargabilidad (IP)
  - modelo 3D (interpolacion IDW), volumenes y figuras.
Los resultados NO son numericamente identicos a Res2DInv (la formulacion es parecida,
la implementacion no). Hay que decirlo en el informe.

REQUISITOS
----------
Python 3.10+ con:  numpy  scipy  pandas  matplotlib  scikit-image  pillow  openpyxl
(opcional, solo para ocr_topo.py: python-docx  pytesseract + tesseract instalado)
  pip install numpy scipy pandas matplotlib scikit-image pillow openpyxl

ESTRUCTURA
----------
  Coordenadas: las tablas GPS (Este ~405 000 m, Norte ~357 300 m) estan en la cuadricula RSO de Malasia
               peninsular (Kertau RSO / GDM2000 Peninsula RSO), NO en UTM; el datum exacto no esta confirmado.
config.py        rutas (todo relativo a esta carpeta)
entrada/         TOMOGRAFIA1..6.dat, topografia_TKI1..6.csv, water.xlsx, soil.xlsx, photos_sheet.png
work/            resultados intermedios (se crea sola)
salida/          figuras/, datos/, modelos/, figuras_informe/ (se crean solas)

ORDEN DE EJECUCION  (cd a esta carpeta; python archivo.py)
------------------------------------------------------------
PUNTO 1 - topografia
  parse_dat.py       lee los .dat (formato Res2DInv, arreglo 7, 41 electrodos).
  ert_tools.py       arma A, M, N, B y el factor geometrico por medicion; carga la topografia
                     de entrada/topografia_TKI*.csv (este, norte, elevacion de cada electrodo).
  ocr_topo.py        (opcional) saca esas tablas del .docx de GPS por OCR; los CSV ya estan revisados.

PUNTO 2 - procesamiento
  1) pipeline.py     edicion de datos + inversion de 10 iteraciones por linea  -> work/dc_results2.pkl
                     - corre una inversion previa con los datos crudos
                     - marca electrodos defectuosos: IP > 10 ms en >60 % de sus datos
                       o |desajuste| > 20 % en >= 50 % (salieron el 28 en todas las lineas,
                       el 25 en TKI1 y el 7 en TKI3)
                     - quita atipicos con |desajuste| > max(25 %, 3 sigma robusto)
                     - inversion final: lam0=20, factor 0.7, minimo 2, error 3 %, 10 iteraciones
  2) analysis.py     tabla por iteracion (RMS, rho max, % de area por clase) -> work/tabla_iteraciones.csv
                     y sugiere la iteracion con criterios explicitos (cambio de RMS < 5 %,
                     rho max <= 2500, p95 estable, rho max >= 95 % de rhoa max). Sugiere la 4 en las seis lineas.
  3) final_models.py ITERACION ELEGIDA: SEL = 4 (linea 4 del archivo; es la decision a defender).
                     Tambien hace la inversion lineal de IP con la relacion de Seigel,
                     y su edicion robusta (a repetir 3 veces)           -> work/final.pkl

PUNTO 3 - zonas con escala comun
  zones.py           clases del articulo (<100, 100-400, >400 ohm.m), nucleo <30 ohm.m,
                     profundidades, areas, posiciones x y tamanos       -> work/zone_metrics.json
  plotlib.py         escalas comunes de color (rho 5-4000 ohm.m, IP 0-6 ms), perfiles de seccion
  figs_sections.py   figura de seccion por linea
  make_figures.py    figuras 1-11 (mapa, topografia, QC, iteraciones, pseudosecciones, 6 modelos)

PUNTO 4 - 3D
  model3d.py         secciones georreferenciadas -> malla 5x5x1 m (IDW anisotropo, radios 45 m y 2 m)
                     en PROFUNDIDAD bajo la superficie (las cotas GPS de lineas que se cruzan
                     difieren hasta 14 m)                              -> work/model3d.pkl
  export_data.py     escribe salida/datos/*.csv (modelos 2D, 3D, bitacoras), los .dat con topografia
                     (salida/datos/res2dinv/) y el .vtk (salida/modelos/) para ParaView;
                     la tabla modelo3D_malla_XYZ.csv se puede importar en Voxler
  fig3d.py           diagrama de cercas, cortes horizontales, isosuperficies, mapas de espesor,
                     volumenes y consistencia en cruces

ADELANTO (puntos 5 y 6)
  fig_ip_chem.py     IP vs resistividad (correlacion), quimica de suelo/agua, estimacion de rho del agua
                     (CE ~ 100 x suma de cationes en meq/L, Archie)
  paper_figs.py      versiones de las figuras a tamano de articulo IEEE -> salida/figuras_informe/

TIEMPO: pipeline.py tarda unos 3 minutos; el resto menos de 10 minutos en total.

PARAMETROS QUE PUEDES CAMBIAR PARA QUE EL TRABAJO SEA TUYO
----------------------------------------------------------
  pipeline.py    umbrales de edicion (10 ms, 60 %, 20 %, 25 %, 3 sigma), lam0, lam_fac, niter
  final_models.py   SEL (iteracion elegida), IP_REL, IP_ABS, IP_LAM
  analysis.py    criterios de seleccion de iteracion
  zones.py       umbrales de clase (100, 400, 30 ohm.m)
  model3d.py     radios IDW, tamano de celda
Si cambias algo, vuelve a correr desde ese paso en adelante y revisa las cifras del informe.

  fig_comparacion_2011.py / fig_secciones_2011.py   comparacion con el reporte de 2011 (histograma, RMS y seccion KPG04 junto a TKI2; usa entrada/umor2011_KPG04.png)
