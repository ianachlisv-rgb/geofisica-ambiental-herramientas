# Ejemplo: ERT sintética de un relleno sanitario

Simula un perfil de tomografía de resistividad eléctrica (48 electrodos cada 5 m, arreglo Wenner-Schlumberger,
736 mediciones, 3 % de ruido) sobre un modelo **inventado** de relleno (residuos, lixiviado, bolsa de lodos),
lo invierte y compara con el modelo verdadero. **No son datos de campo.**

El modelo directo usa una malla más fina que la de la inversión, para no favorecer el resultado.

```
pip install numpy scipy matplotlib shapely
python sim_ert.py            # datos sintéticos      -> datos/sim_data.pkl
python inv_sim.py            # inversión             -> datos/sim_inv.pkl
python descargar_limites.py  # límites de México/Puebla (solo para figuras.py)
python figuras.py            # mapas y figura del modelo -> figuras/
```

Cambia `truth()` en `sim_ert.py` para probar otras geometrías o resistividades.
`figuras.py` también dibuja los mapas de localización y de diseño de adquisición del caso Santa María Coapan (Tehuacán, Puebla);
en esa figura el polígono del sitio es esquemático.

Límites usados: Natural Earth (dominio público), `angelnmara/geojson` y `PhantomInsights/mexico-geojson` (GitHub).
