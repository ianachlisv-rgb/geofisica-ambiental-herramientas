from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import ScatterChart, Reference, Series
from openpyxl.utils import get_column_letter as L

F = 'Arial'
f_norm = Font(name=F, size=10); f_b = Font(name=F, size=10, bold=True)
f_in = Font(name=F, size=10, color='0000FF'); f_h = Font(name=F, size=12, bold=True, color='FFFFFF')
f_t = Font(name=F, size=14, bold=True); f_note = Font(name=F, size=9, italic=True, color='595959')
fill_in = PatternFill('solid', fgColor='FFF2CC'); fill_h = PatternFill('solid', fgColor='1F4E79')
fill_res = PatternFill('solid', fgColor='F8CBAD'); fill_sub = PatternFill('solid', fgColor='DDEBF7')
thin = Side(style='thin', color='BFBFBF'); box = Border(left=thin, right=thin, top=thin, bottom=thin)
ctr = Alignment(horizontal='center', vertical='center')
COLS = [L(c) for c in range(2, 13)]   # B..L = nodos 0..10
NIT = 1000

wb = Workbook()
ws = wb.active; ws.title = 'Modelo'
it = wb.create_sheet('Iteraciones'); dr = wb.create_sheet('Directo'); nt = wb.create_sheet('Notas')

def put(sh, ref, v, font=f_norm, fmt=None, fill=None, al=None, border=True):
    c = sh[ref]; c.value = v; c.font = font
    if fmt: c.number_format = fmt
    if fill: c.fill = fill
    if al: c.alignment = al
    if border: c.border = box
    return c
def header(sh, row, text, last='L'):
    for col in range(1, ord(last) - 64 + 1):
        sh.cell(row=row, column=col).fill = fill_h
    c = sh.cell(row=row, column=1, value=text); c.font = f_h

# ---------------- Modelo
ws['A1'] = 'Conducción de calor 1D por diferencias finitas:  −(k·T′)′ = H'; ws['A1'].font = f_t
ws['A2'] = 'Celdas amarillas con texto azul = datos que puedes cambiar. Todo lo demás se calcula solo. Ejemplo cargado: el de la clase (H y k de las capturas, T(0)=0, T(L)=25).'
ws['A2'].font = f_note
header(ws, 4, 'PARÁMETROS')
params = [
 (5, 'Longitud de la barra L', 1, '0.00', True, 'L = 1 en la clase'),
 (6, 'Valor inicial en los nodos interiores', 0, '0.00', True, 'Punto de partida del método iterativo (en la clase parte de 0)'),
 (7, 'Paso h = L / 10', '=B5/10', '0.000', False, 'Siempre 10 intervalos (11 nodos, de 0 a 10): es el diseño de la hoja'),
 (8, 'Temperatura en x = 0', 0, '0.00', True, 'Condición de frontera izquierda (dato de la clase)'),
 (9, 'Temperatura en x = L', 25, '0.00', True, 'Condición de frontera derecha (dato de la clase)'),
 (10, 'Método iterativo (1 = Jacobi, 2 = Gauss-Seidel)', 2, '0', True, 'Gauss-Seidel converge en la mitad de iteraciones'),
 (11, 'Tolerancia (máx |ΔT| entre iteraciones)', 1e-6, '0.0E+00', True, 'Criterio para decir que ya convergió'),
 (13, 'Iteración que se muestra como T iterativo', 81, '0', True, 'De 0 a 1000. Con 81 se reproduce la captura de la clase; con 1000 ya está convergido'),
 (12, 'Iteraciones necesarias', f'=IF(COUNT(Iteraciones!N6:N{5+NIT})=0,"no converge en {NIT}",MIN(Iteraciones!N6:N{5+NIT}))', '0', False, f'Cuántas iteraciones hacen falta para cumplir la tolerancia (se calculan hasta {NIT})'),
]
for r, lab, v, fmt, inp, note in params:
    put(ws, f'A{r}', lab, f_norm)
    put(ws, f'B{r}', v, f_in if inp else f_norm, fmt, fill_in if inp else None, ctr)
    ws[f'C{r}'] = note; ws[f'C{r}'].font = f_note

header(ws, 14, 'DATOS DEL MODELO')
put(ws, 'A15', 'Nodo i', f_b, fill=fill_sub)
put(ws, 'A16', 'x (m)', f_norm)
put(ws, 'A17', 'H  (fuente de calor)', f_norm)
put(ws, 'A18', 'k  (conductividad)', f_norm)
put(ws, 'A19', 'k cara oeste (media armónica)', f_norm)
put(ws, 'A20', 'k cara este (media armónica)', f_norm)
Hs = [0, 500, 500, 0, 200, 0, 100, 100, 0, 400, 0]
for i, c in enumerate(COLS):
    put(ws, f'{c}15', i, f_b, '0', fill_sub, ctr)
    put(ws, f'{c}16', f'={c}15*$B$7', f_norm, '0.0', None, ctr)
    put(ws, f'{c}17', Hs[i], f_in, '0', fill_in, ctr)
    put(ws, f'{c}18', 2, f_in, '0.00', fill_in, ctr)
    if 0 < i < 10:
        p, n = COLS[i-1], COLS[i+1]
        put(ws, f'{c}19', f'=2*{p}18*{c}18/({p}18+{c}18)', f_norm, '0.00', None, ctr)
        put(ws, f'{c}20', f'=2*{c}18*{n}18/({c}18+{n}18)', f_norm, '0.00', None, ctr)
    else:
        put(ws, f'{c}19', None); put(ws, f'{c}20', None)
ws['M17'] = 'H en los extremos no se usa (ahí T es dato).'; ws['M17'].font = f_note

header(ws, 22, 'RESULTADOS')
labs = {23: 'T inicial (iteración 0)', 24: 'T directo (resuelve el sistema)', 25: 'T iterativo (iteración elegida en B13)',
        26: 'Diferencia directo − iterativo', 27: 'Residuo de la ecuación (directo)', 28: 'T de la captura de la clase', 29: 'Diferencia iterativo − captura'}
for r, t in labs.items(): put(ws, f'A{r}', t, f_b if r in (24, 25) else f_norm)
cap = [0, 7.896746, 13.2941134, 16.1922944, 19.091385, 20.991385, 22.892208, 24.293696, 25.195644, 26.097822, 25]
for i, c in enumerate(COLS):
    put(ws, f'{c}23', '=$B$8' if i == 0 else ('=$B$9' if i == 10 else '=$B$6'), f_norm, '0.0000', None, ctr)
    put(ws, f'{c}24', f'=Directo!{c}12', f_b, '0.0000', fill_res, ctr)
    put(ws, f'{c}25', f'=INDEX(Iteraciones!{c}$5:{c}${5+NIT},$B$13+1)', f_b, '0.0000', fill_res, ctr)
    put(ws, f'{c}26', f'={c}24-{c}25', f_norm, '0.0E+00', None, ctr)
    if 0 < i < 10:
        p, n = COLS[i-1], COLS[i+1]
        put(ws, f'{c}27', f'={c}19*({p}24-{c}24)+{c}20*({n}24-{c}24)+{c}17*$B$7^2', f_norm, '0.0E+00', None, ctr)
    else:
        put(ws, f'{c}27', None)
    put(ws, f'{c}28', cap[i], f_in, '0.000000', None, ctr)
    put(ws, f'{c}29', f'={c}25-{c}28', f_norm, '0.0E+00', None, ctr)
ws['M28'] = 'Transcrita de la captura de pantalla; coincide con Gauss-Seidel desde 0 tras 81 iteraciones (diferencia ≈ 1e-6).'; ws['M28'].font = f_note
ws['M27'] = 'Debe ser ≈ 0: comprueba que T cumple la ecuación en cada nodo.'; ws['M27'].font = f_note

ws.column_dimensions['A'].width = 42
for c in COLS: ws.column_dimensions[c].width = 12
ws.column_dimensions['M'].width = 60
ws.freeze_panes = 'B4'

ch = ScatterChart(); ch.style = 2; ch.roundedCorners = False
ch.title = 'Distribución de temperatura en la barra'; ch.title.overlay = False
ch.x_axis.title = 'Barra, x (m)'; ch.y_axis.title = 'Temperatura'
ch.x_axis.title.overlay = False; ch.y_axis.title.overlay = False
ch.x_axis.delete = False; ch.y_axis.delete = False
ch.x_axis.scaling.min = 0; ch.x_axis.scaling.max = 1
ch.legend.position = 'b'; ch.legend.overlay = False
ch.height = 9; ch.width = 18
xs = Reference(ws, min_col=2, max_col=12, min_row=16)
for row, name, dash, sym in [(24, 'T directo', None, 'circle'), (25, 'T iterativo', 'dash', 'none')]:
    s = Series(Reference(ws, min_col=2, max_col=12, min_row=row), xs, title=name)
    s.marker.symbol = sym
    if dash: s.graphicalProperties.line.dashStyle = dash
    s.smooth = False
    ch.series.append(s)
ws.add_chart(ch, 'A32')

# ---------------- Iteraciones
it['A1'] = 'Método iterativo: cada fila es una iteración'; it['A1'].font = f_t
it['A2'] = ('Nodo interior:  T_i = ( kO·T_(i−1) + kE·T_(i+1) + H_i·h² ) / ( kO + kE ).  Jacobi usa solo valores de la fila anterior; '
            'Gauss-Seidel usa el vecino izquierdo ya actualizado de la misma fila.')
it['A2'].font = f_note
put(it, 'A4', 'Iteración', f_b, fill=fill_sub, al=ctr)
for i, c in enumerate(COLS): put(it, f'{c}4', f'Nodo {i}', f_b, fill=fill_sub, al=ctr)
put(it, 'M4', 'Máx |ΔT|', f_b, fill=fill_sub, al=ctr); put(it, 'N4', 'Cumple tol.', f_b, fill=fill_sub, al=ctr)

LAST = 5 + NIT
for r in range(5, LAST + 1):
    k = r - 5
    put(it, f'A{r}', k, f_norm, '0', None, ctr)
    for i, c in enumerate(COLS):
        if k == 0:
            f = f'=Modelo!{c}23'
        elif i == 0:
            f = '=Modelo!$B$8'
        elif i == 10:
            f = '=Modelo!$B$9'
        else:
            p, n = COLS[i-1], COLS[i+1]
            f = (f'=(Modelo!{c}$19*IF(Modelo!$B$10=1,{p}{r-1},{p}{r})+Modelo!{c}$20*{n}{r-1}'
                 f'+Modelo!{c}$17*Modelo!$B$7^2)/(Modelo!{c}$19+Modelo!{c}$20)')
        put(it, f'{c}{r}', f, f_norm, '0.000000', None, ctr)
    if k > 0:
        terms = ','.join(f'ABS({c}{r}-{c}{r-1})' for c in COLS[1:10])
        put(it, f'M{r}', f'=MAX({terms})', f_norm, '0.0E+00', None, ctr)
        put(it, f'N{r}', f'=IF(M{r}<Modelo!$B$11,A{r},"")', f_norm, '0', None, ctr)
    else:
        put(it, f'M{r}', None); put(it, f'N{r}', None)
it.column_dimensions['A'].width = 11
for c in COLS: it.column_dimensions[c].width = 11
it.column_dimensions['M'].width = 12; it.column_dimensions['N'].width = 12
it.freeze_panes = 'B5'

# ---------------- Directo (algoritmo de Thomas)
dr['A1'] = 'Solución directa del sistema tridiagonal (algoritmo de Thomas)'; dr['A1'].font = f_t
dr['A2'] = 'Ecuación en cada nodo interior:  a_i·T_(i−1) + b_i·T_i + c_i·T_(i+1) = d_i,  con a = kO/h², c = kE/h², b = −(kO+kE)/h², d = −H_i.  En los extremos: T = dato.'
dr['A2'].font = f_note
rows = {4: 'Nodo i', 5: 'a  (diagonal inferior)', 6: 'b  (diagonal principal)', 7: 'c  (diagonal superior)', 8: 'd  (lado derecho)',
        9: "pivote  m = b − a·c'(anterior)", 10: "c'  = c / m", 11: "d'  = (d − a·d'(anterior)) / m", 12: 'T  (sustitución hacia atrás)'}
for r, t in rows.items(): put(dr, f'A{r}', t, f_b if r in (4, 12) else f_norm, fill=fill_sub if r == 4 else None)
for i, c in enumerate(COLS):
    put(dr, f'{c}4', f'=Modelo!{c}15', f_b, '0', fill_sub, ctr)
    if 0 < i < 10:
        put(dr, f'{c}5', f'=Modelo!{c}19/Modelo!$B$7^2', f_norm, '0.0000', None, ctr)
        put(dr, f'{c}6', f'=-(Modelo!{c}19+Modelo!{c}20)/Modelo!$B$7^2', f_norm, '0.0000', None, ctr)
        put(dr, f'{c}7', f'=Modelo!{c}20/Modelo!$B$7^2', f_norm, '0.0000', None, ctr)
        put(dr, f'{c}8', f'=-Modelo!{c}17', f_norm, '0.0000', None, ctr)
    else:
        put(dr, f'{c}5', 0, f_norm, '0.0000', None, ctr)
        put(dr, f'{c}6', 1, f_norm, '0.0000', None, ctr)
        put(dr, f'{c}7', 0, f_norm, '0.0000', None, ctr)
        put(dr, f'{c}8', '=Modelo!$B$8' if i == 0 else '=Modelo!$B$9', f_norm, '0.0000', None, ctr)
    if i == 0:
        put(dr, f'{c}9', f'={c}6', f_norm, '0.0000', None, ctr)
        put(dr, f'{c}10', f'={c}7/{c}9', f_norm, '0.0000', None, ctr)
        put(dr, f'{c}11', f'={c}8/{c}9', f_norm, '0.0000', None, ctr)
    else:
        p = COLS[i-1]
        put(dr, f'{c}9', f'={c}6-{c}5*{p}10', f_norm, '0.0000', None, ctr)
        put(dr, f'{c}10', f'={c}7/{c}9', f_norm, '0.0000', None, ctr)
        put(dr, f'{c}11', f'=({c}8-{c}5*{p}11)/{c}9', f_norm, '0.0000', None, ctr)
    if i == 10:
        put(dr, f'{c}12', f'={c}11', f_b, '0.0000', fill_res, ctr)
    else:
        n = COLS[i+1]
        put(dr, f'{c}12', f'={c}11-{c}10*{n}12', f_b, '0.0000', fill_res, ctr)
dr.column_dimensions['A'].width = 38
for c in COLS: dr.column_dimensions[c].width = 11

# ---------------- Notas
notas = [
 ('Cómo usar este libro', True),
 ('1. Hoja "Modelo": cambia solo las celdas amarillas (L, temperaturas de frontera, método, H y k por nodo).', False),
 ('2. Las hojas "Iteraciones" y "Directo" se recalculan solas. La gráfica compara las dos soluciones.', False),
 ('3. Si te dan otro problema: pon sus H y k en las filas 17 y 18 y sus temperaturas en B8 y B9. Si te piden más o menos nodos, hay que ampliar las columnas (ver abajo).', False),
 ('', False),
 ('Qué resuelve', True),
 ('Conducción de calor estacionaria 1D con fuente:  −d/dx( k dT/dx ) = H(x).  Es una ecuación de Poisson 1D con conductividad variable.', False),
 ('Se divide la barra en N intervalos de tamaño h y se aproxima en cada nodo interior i:', False),
 ('   kO·(T_(i−1) − T_i) + kE·(T_(i+1) − T_i) = −H_i·h²', False),
 ('con kO y kE = conductividad en las caras oeste y este del nodo. Con k constante se reduce a  T_(i−1) − 2·T_i + T_(i+1) = −H_i·h²/k.', False),
 ('Despejando T_i sale la fórmula iterativa de la hoja "Iteraciones".', False),
 ('', False),
 ('Supuestos', True),
 ('• Las conductividades de las caras se calculan con media armónica (estándar cuando k cambia entre nodos). Con k = 2 en todos los nodos da exactamente k = 2.', False),
 ('• H se toma como valor puntual en cada nodo; en x = 0 y x = L la temperatura es dato, así que H ahí no se usa.', False),
 ('• La fila "T de la captura" está transcrita de una captura de pantalla de la clase (no es un dato oficial) y solo sirve para comprobar el ejemplo.', False),
 ('• No conozco las unidades de H, k y T en la clase; la hoja trabaja con los números tal cual.', False),
 ('• Se calculan 1000 iteraciones como máximo. En B13 eliges cuál se muestra como T iterativo. Con Gauss-Seidel desde 0, la iteración 81 reproduce la captura de la clase; esa solución aún no está convergida y por eso difiere ≈ 0.009 de la solución directa.', False),
 ('', False),
 ('Comprobaciones incluidas', True),
 ('• "Diferencia directo − iterativo" debe ser casi 0 cuando el método iterativo ya convergió (sube B13 a 1000 para verlo).', False),
 ('• "Residuo de la ecuación" debe ser casi 0 en todos los nodos interiores.', False),
 ('', False),
 ('Para cambiar el número de nodos', True),
 ('Hay que añadir columnas de nodo en "Modelo", "Directo" e "Iteraciones" y cambiar el 10 de h = L/10 y los rangos de la gráfica. Es mucho más cómodo mantener 10 intervalos mientras no te pidan otra cosa.', False),
]
for i, (t, b) in enumerate(notas, start=1):
    c = nt.cell(row=i, column=1, value=t); c.font = f_b if b else f_norm
    c.alignment = Alignment(wrap_text=True, vertical='top')
nt.column_dimensions['A'].width = 130
wb.save('Diferencias_finitas_calor_1D.xlsx')
print('guardado')
