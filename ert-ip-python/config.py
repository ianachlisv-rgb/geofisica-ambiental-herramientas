"""Rutas del proyecto. Todo es relativo a la carpeta donde esta este archivo.
entrada/  -> TOMOGRAFIA1..6.dat, topografia_TKI1..6.csv, water.xlsx, soil.xlsx, photos_sheet.png
work/     -> resultados intermedios (.pkl, .json, .csv)
salida/   -> figuras/, datos/, modelos/, figuras_informe/
"""
import os
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
ENTRADA = os.path.join(BASE, 'entrada') + os.sep
W = os.path.join(BASE, 'work') + os.sep
OUT = os.path.join(BASE, 'salida') + os.sep
HDIR = OUT
OUTF = os.path.join(BASE, 'salida', 'figuras') + os.sep
PF = os.path.join(BASE, 'salida', 'figuras_informe') + os.sep
for _d in (W, OUT, OUTF, PF):
    os.makedirs(_d, exist_ok=True)


def load_topo():
    """dict {linea: DataFrame[electrodo_x_m, Este_m, Norte_m, elevacion_m, nota]} desde los CSV de entrada/"""
    return {i: pd.read_csv(ENTRADA + f'topografia_TKI{i}.csv') for i in range(1, 7)}
