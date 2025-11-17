### Plan de trabajo para cumplir requerimientos v2 con trazabilidad y GUI

#### A. Núcleo de simulación 0D
- Configuración YAML: definir esquema (`operating_conditions`, `electrode_A/B`, `ohmic.components`, `mass_transfer`) y parser (pyyaml). Validar unidades básicas.
- Modelos cinéticos conmutables: implementar Tafel y Butler-Volmer, seleccionables por electrodo (`kinetic_model`). Asegurar dependencia Arrhenius de `j0(T)` y soportar `alpha_a/alpha_c` en BV.
- Potencial reversible: soportar opción termodinámica (ΔG/ΔS) y Nernst con presiones parciales. Exponer bandera para elegir.
- Pérdidas óhmicas: sumar capas en serie; cada capa con `delta`, `kappa_ref`, `Ea_kappa` (o coef lineal). Añadir cálculo de `kappa(T)`.
- Pérdidas de concentración: módulo opcional con `j_lim` o `D_eff`, `C_bulk`, `delta_dif`. Aplicar η_conc solo si habilitado.
- Doble electrodo: permitir definir A/B; calcular η_act por electrodo y sumarlas cuando corresponda.
- Barridos: generar malla de `j` y `T`; permitir lista de T o valor único.
- Resultados tabulares: devolver dataframe con columnas mínimas `electrode`, `j`, `T`, `V_rev`, `eta_act`, `eta_ohm`, `eta_conc`, `V_cell`, `model_act` (tafel/bv), `j0_T`, `kappa_eff`.

#### B. Trazabilidad (detail)
- Mantener `PointDetail/EquationStep` o equivalente: por punto incluir ecuación usada, parámetros sustituidos, resultado numérico y etiqueta de electrodo.
- Registrar modelo usado (Tafel/BV), parámetros (`alpha`, `j0_ref`, `Ea`, `T_ref`), y valores de Arrhenius (j0_T).
- Log de ohm: capas con `delta`, `kappa_ref`, `Ea_kappa`, `kappa_T`, `R_layer`.
- Log de concentración: si activo, registrar `j_lim`, `D_eff`, `C_bulk`, `delta_dif` y η_conc aplicada.
- Barridos de T: cada paso debe guardar T usada y si proviene de lista o valor fijo.
- Comparación experimental: estructuras con `j_exp`, `V_exp_interp`, `V_sim`, `error`, métricas agregadas (RMSE, MAE).
- Exportar trazabilidad: capacidad de volcar a CSV/JSON; mantener tabla detallada en GUI.

#### C. CLI
- Comandos: `simulate` (uno o dos electrodos), `compare-electrodes`, `validate-exp`.
- Entradas: `--config config.yml`, `--with-experimental exp_data.csv`, banderas `--no-conc`, `--model tafeln|bv`.
- Salidas: CSV de resultados, PNG de curvas (matplotlib), opcional JSON con trazabilidad resumida.
- Manejo de errores: validar campos requeridos en YAML y reportar faltantes.

#### D. GUI (Dash)
- Inputs: selector global de archivo/config; sliders/rangos de `j_min/j_max/n_points`; lista de T; toggle concentración; selector modelo cinético por electrodo (Tafel/BV); campos duplicados de `j0_ref`, `Ea`, `alpha`, `T_ref` para A/B.
- Ohm: tabla editable de capas (delta, kappa_ref, Ea_kappa); cálculo en tiempo real de R_total.
- Concentración: toggle y campos `j_lim` directo o {D_eff, C_bulk, delta_dif}.
- Datos experimentales: cargador CSV; overlay en gráfica; cálculo y despliegue de errores.
- Salidas: gráfica con curvas A/B y exp; curva ΔV(j); tarjetas con V_rev, η_act, η_ohm, η_conc; tabla detallada de trazabilidad por punto; botones de exportar CSV/PNG.
- Etiquetas: mostrar modelo cinético activo y si concentración está habilitada.

#### E. Datos de ejemplo
- Crear `examples/config.yml` con dos electrodos y masa opcional.
- Crear `examples/exp_data.csv` con columnas `j_exp`, `V_exp`.
- Script corto en README para correr CLI sobre los ejemplos.

#### F. Pruebas y validación
- Unitarias: cálculo de V_rev (term/Nernst), j0(T) Arrhenius, η_act Tafel/BV, η_ohm con multilayer, η_conc con j_lim.
- Integración: generación de curva V–j para A/B; comparación produce ΔV coherente; validación contra CSV calcula RMSE esperado.
- GUI smoke test: carga de config, toggle concentración, selección de modelos, carga de CSV exp, export de tabla.

#### G. Documentación
- Actualizar `README.md` con stack v2, uso de CLI y GUI, y ejemplos.
- Limpiar codificación a UTF-8 en todos los md.
- Añadir sección de trazabilidad: explicar columnas/JSON y cómo exportar.
