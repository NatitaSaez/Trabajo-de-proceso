### Diferencias clave entre v1 y v2

- **Dominio y alcance**: `requerimientos.md` se centra en ORR y actividad catalítica vía DFT para pilas de combustible; `requerimientosv2.md` redefine a un simulador 0D de celda H/electrolizador con foco en curvas V–j, sin DFT ni volcanes, y añade comparación entre dos electrodos y validación con datos experimentales.
- **Modelo electroquímico**: v1 lista ecuaciones de Nernst, Tafel, pérdidas ohm y concentración, pero ligadas a ORR; `definicion_final_de_ecuaciones_v2.md` y la sección 3 de `requerimientosv2.md` precisan el stack V_rev + eta_act + eta_ohm + eta_conc para electrolizador (HER/OER) y permiten elegir Tafel o Butler-Volmer, incluir o excluir concentración.
- **Parámetros y configuración**: v1 asume parámetros embebidos; v2 exige archivo de configuración (YAML sugerido) con bloques `electrode_A/B`, componentes ohmicos, rangos de j/T y banderas de concentración, más inputs de datos experimentales para validación.
- **Flujos y criterios**: v2 define flujos de CLI (simulación simple, comparación de electrodos, validación con `exp_data.csv`) y criterios de aceptación (error < umbral, modularidad para nuevos modelos), ausentes en v1.
- **Librerías y estructura**: v2 prescribe libs (`numpy`, `scipy`, `pandas`, `matplotlib`, `pyyaml`, CLI con argparse/typer/click) y sugiere dataframes/tablas para resultados; v1 no fija stack ni formato de resultados.

### Qué hacer para cumplir v2 (núcleo)

- Implementar un kernel 0D configurable con lectura de YAML (operating_conditions, electrode_A/B, ohmic, mass_transfer).
- Soportar modelos cinéticos seleccionables: Tafel por defecto, Butler-Volmer opcional, con Arrhenius para j0 y conductividades.
- Calcular V_rev con opción termodinámica o Nernst según entrada de presiones; sumar pérdidas ohmicas (serie de capas) y opcionalmente concentración (j_lim).
- Generar curvas V–j para uno o dos electrodos, barridos en T; devolver tabla con j, T, V_cell, eta_act, eta_ohm, eta_conc y guardar CSV/gráficos (matplotlib).
- Incorporar modo de validación: leer `exp_data.csv`, interpolar, calcular error vs simulación y reportar métricas.

### Qué hacer para cumplir v2 (GUI)

- Añadir selector de modelo cinético (`tafel`/`butler-volmer`), check de pérdidas por concentración y entrada de j_lim o parámetros de masa.
- Permitir definir dos electrodos: campos duplicados de j0_ref, Ea, alpha, modelo; mostrar curvas superpuestas y ΔV(j).
- Entradas para rangos de j y T (lista de T o slider), y para componentes ohmicos (lista editable de capas con delta, kappa_ref, Ea_kappa).
- Carga de datos experimentales (CSV) y overlay en la gráfica, con cálculo de error y tabla resumida.
- Botones para exportar CSV de simulación y descarga de figura; mantener tabla detallada de contribuciones (eta_act/ohm/conc) por punto.

### Sugerencia de pasos inmediatos

1) Normalizar codificación UTF-8 de los md y aplicar un nombre/camino final para el archivo de configuración (ej. `config.yml`).  
2) Extender el núcleo Python para lectura de YAML, doble electrodo y conmutación Tafel/BV + concentración.  
3) Actualizar CLI según flujos RF (simulación, comparación, validación).  
4) Refactorizar la app Dash para los nuevos inputs (dos electrodos, modelos, concentración, rangos de T) y salidas (curvas comparadas, error vs experimento).  
5) Añadir tests unitarios mínimos de cálculo V–j y una muestra de `config.yml` + `exp_data.csv` en `examples/`.
