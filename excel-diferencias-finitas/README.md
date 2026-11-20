# Conducción de calor 1D por diferencias finitas (Excel)

Libro de Excel con fórmulas para resolver  **−(k·T′)′ = H**  en una barra con 11 nodos:

- **Modelo**: datos editables (celdas amarillas: H, k, temperaturas de frontera, método, iteración a mostrar) y la gráfica.
- **Iteraciones**: Jacobi o Gauss-Seidel, hasta 1000 iteraciones.
- **Directo**: solución exacta del sistema tridiagonal (algoritmo de Thomas) para comparar.
- **Notas**: ecuación, fórmula por nodo y supuestos.

El ejemplo cargado es el de una clase: H = 500, 500, 0, 200, 0, 100, 100, 0, 400; k = 2; T(0) = 0 y T(1) = 25.
Gauss-Seidel desde 0 con 81 iteraciones reproduce la tabla del profesor; la solución convergida difiere unos 0.009.

`generar_excel.py` (necesita `openpyxl`) regenera el libro desde cero.
