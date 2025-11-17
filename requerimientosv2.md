---
### 1. Propósito del software

Desarrollar un simulador electroquímico 0D en Python para un electrolizador tipo H que:

* Genere curvas de polarización (V)–(j) en función de:

  * densidad de corriente,
  * temperatura,
  * parámetros cinéticos (Tafel/Butler–Volmer),
  * resistencias óhmicas,
  * opcionalmente, pérdidas de concentración.
* Permita comparar:

  * hasta **dos electrodos de trabajo** (por ejemplo, dos materiales catalíticos distintos),
  * resultados simulados vs. datos experimentales obtenidos de papers (curvas (V)–(j) digitalizadas).
* Soporte análisis estacionario (curvas de polarización) y, en una segunda etapa, análisis transitorio simple en función del tiempo.

---

### 2. Alcance

* Modelo 0D (celda concentrada, sin resolución espacial).
* Electrolizador tipo H (dos semiceldas, un electrodo de trabajo y uno contraelectrodo).
* Medio alcalino o ácido definido por el usuario (la ec. general es la misma, cambian parámetros).
* En esta primera versión:

  * Enfoque principal en régimen estacionario: cálculo de (V_\text{cell}(j,T)).
  * Tiempo usado para “campañas” de simulación (escenarios), no para resolver PDE acopladas.
* No se modelan explícitamente:

  * flujo bifásico de gas/líquido,
  * transporte convectivo detallado,
  * envejecimiento/degradación de materiales (podrá añadirse como factor empírico en el futuro).

---

### 3. Modelo matemático a implementar (resumen de ecuaciones)

#### 3.1. Ecuación global de la celda

[
V_\text{cell}(j,T) = V_\text{rev}(T) + \eta_\text{act}(j,T) + \eta_\text{ohm}(j,T) + \eta_\text{conc}(j,T)
]

Con opción de:

* Versión básica: (\eta_\text{conc} = 0).
* Versión extendida: (\eta_\text{conc} \neq 0) usando modelo de corriente límite.

#### 3.2. Potencial reversible (V_\text{rev}(T))

1. Opción termodinámica global:

[
\Delta G(T) = \Delta H(T) - T,\Delta S(T)
]
[
V_\text{rev}(T) = -\frac{\Delta G(T)}{nF}
]

Aproximación lineal:

[
V_\text{rev}(T) \approx V_\text{rev}(T_0) + \frac{\Delta S^\circ}{nF}(T-T_0)
]

2. Opción Nernst (si se especifican presiones parciales):

[
V_\text{rev}(T) = V_\text{rev}^\circ(T) + \frac{RT}{nF}\ln Q
]

#### 3.3. Sobretensión de activación

**Modo Tafel (por defecto):**

[
\eta_\text{act}(j,T) = \frac{RT}{\alpha nF}\ln\left(\frac{|j|}{j_0(T)}\right)
]

Con:

[
j_0(T) = j_{0,\text{ref}}\exp\left[-\frac{E_a}{R}\left(\frac{1}{T} - \frac{1}{T_\text{ref}}\right)\right]
]

**Modo Butler–Volmer (opcional):**

[
j = j_0(T)\left[
\exp\left(\frac{\alpha_a nF\eta}{RT}\right) -
\exp\left(-\frac{\alpha_c nF\eta}{RT}\right)
\right]
]

La implementación debe permitir elegir, por configuración:

* `"kinetic_model": "tafel"` o `"butler-volmer"`.

#### 3.4. Sobretensión óhmica

[
\eta_\text{ohm}(j,T) = j , R_\text{areal}(T)
]

[
R_\text{areal}(T) = \sum_i \frac{\delta_i}{\kappa_{i,\text{eff}}(T)}
]

Con dependencia de conductividad:

[
\kappa_{i,\text{eff}}(T)
= \kappa_{i,\text{ref}}
\exp\left[-\frac{E_{\kappa,i}}{R}\left(\frac{1}{T}-\frac{1}{T_\text{ref}}\right)\right]
]

#### 3.5. Sobretensión de concentración (opcional)

[
j_\text{lim} = \frac{nF D_\text{eff} C_\text{bulk}}{\delta_\text{dif}}
]

[
\eta_\text{conc}(j,T)
= -\frac{RT}{nF}\ln\left(1-\frac{j}{j_\text{lim}}\right)
]

---

### 4. Requerimientos funcionales

#### RF1. Definición de parámetros de celda y electrodos

El simulador debe permitir definir (vía archivo de configuración o entrada de usuario):

* Parámetros globales:

  * Área activa (A) [cm² o m²].
  * Tipo de celda (etiqueta, p. ej. `"H-cell"`).
  * Temperatura de referencia (T_\text{ref}).
* Por electrodo (hasta 2 electrodos de trabajo):

  * Nombre/material (ej. `"Ni"`, `"Cu"`, `"NiFeOx"`).
  * Modelo cinético (`"tafel"` / `"butler-volmer"`).
  * (j_{0,\text{ref}}), (E_a), (\alpha).
  * Parámetros opcionales de Butler–Volmer ((\alpha_a), (\alpha_c)).
* Componentes óhmicos:

  * Espesores (\delta_i).
  * (\kappa_{i,\text{ref}}), (E_{\kappa,i}) o coeficientes empíricos.
* Parámetros de concentración (si se usan):

  * (D_\text{eff}), (C_\text{bulk}), (\delta_\text{dif}).

#### RF2. Definición de condiciones de operación

* Rango de densidad de corriente:

  * `j_min`, `j_max`, `n_points`.
* Rango de temperatura:

  * una temperatura fija o un conjunto ([T_1, T_2, ..., T_n]).
* Opciones de operación:

  * inclusión/exclusión de (\eta_\text{conc}),
  * inclusión de dos electrodos (sumar (\eta_\text{act,cat}) y (\eta_\text{act,án})).

#### RF3. Cálculo de curva de polarización para un electrodo

Para cada electrodo definido:

* Calcular, para cada (j) y (T):

  1. (V_\text{rev}(T)).
  2. (\eta_\text{act}(j,T)).
  3. (\eta_\text{ohm}(j,T)).
  4. (Opcional) (\eta_\text{conc}(j,T)).
  5. (V_\text{cell}(j,T)).

* Guardar resultados en una estructura de datos (tabla) con columnas mínimas:

  * `j`, `T`, `V_cell`, `eta_act`, `eta_ohm`, `eta_conc`.

#### RF4. Comparación de dos electrodos de trabajo

* Debe ser posible definir dos conjuntos de parámetros cinéticos:

  * `electrode_A`, `electrode_B`.
* El simulador debe generar:

  * Una curva (V)–(j) para cada electrodo,
  * Una figura con ambas curvas superpuestas,
  * Opcionalmente, diferencias (\Delta V(j) = V_B(j) - V_A(j)).

#### RF5. Barrido en temperatura

* Debe permitir fijar un vector de temperaturas, por ejemplo:

  * `T_list = [298, 313, 333] K`.
* Para cada (T), generar una curva (V)–(j).
* El resultado debe incluir:

  * Gráficos (V)–(j) coloreados por temperatura,
  * Tablas diferenciadas por temperatura.

#### RF6. Modo transitorio simple (opcional, etapa 2)

Sin resolver PDE, se requiere la infraestructura para:

* Definir un perfil de operación en el tiempo:

  * Ejemplo: `j(t)` como escalón, rampa o lista de pares `(t, j)`.
* Calcular la respuesta en términos de:

  * (V_\text{cell}(t)) usando el estado estacionario instantáneo.
* Dejar preparado el modelo para incorporar en el futuro:

  * equilibrio térmico simple (ecuación de energía global),
  * ajuste de (T(t)) por disipación y refrigeración.

#### RF7. Importación de datos experimentales

* Formato de entrada recomendado: CSV con columnas:

  * `j_exp`, `V_exp`, (opcional) `T_exp`.
* El simulador debe:

  * Leer el archivo,
  * Interpolar o emparejar puntos simulados y experimentales en función de (j),
  * Calcular métricas de error:

    * RMSE, MAE, error relativo medio.
* Debe ser capaz de generar un gráfico:

  * Simulación vs. experimento en la misma curva,
  * Leyenda clara.

#### RF8. Exportación de resultados

* Los resultados deben poder exportarse en:

  * CSV (tablas de resultados),
  * PNG/PDF (figuras de curvas de polarización).
* Nombres de archivo generados sistemáticamente a partir de:

  * nombre del proyecto,
  * nombre del electrodo,
  * fecha/hora o etiqueta de escenario.

#### RF9. Interfaz de usuario

* Fase 1: interfaz de línea de comandos (CLI):

  * Argumentos básicos:

    * `--config` (ruta a archivo YAML/JSON),
    * `--output-dir`,
    * `--compare-electrodes`,
    * `--with-experimental DATA.csv`.
* Fase 2: posibilidad de una GUI simple (por ejemplo, con `streamlit` o `Tkinter`), no obligatorio en la primera versión pero contemplado en el diseño modular.

---

### 5. Requerimientos no funcionales

* Lenguaje: Python 3.10+.
* Estilo de código:

  * PEP8,
  * docstrings claros,
  * tipado estático con `typing`.
* Reproducibilidad:

  * versión del código controlada (git),
  * archivo de requisitos (`requirements.txt` o `pyproject.toml`).
* Rendimiento:

  * El cálculo para un conjunto típico (p. ej. 3 temperaturas, 200 puntos de (j)) debe ejecutarse en menos de 1 s en un PC estándar.
* Portabilidad:

  * Debe funcionar en Windows, Linux y WSL sin cambios de código, sólo creando un entorno virtual.

---

### 6. Arquitectura de software propuesta

#### 6.1. Estructura de módulos

Propuesta mínima:

* `pem_sim/`

  * `__init__.py`
  * `config.py`
  * `models.py`
  * `kinetics.py`
  * `ohmic.py`
  * `mass_transfer.py`
  * `simulation.py`
  * `io.py`
  * `plotting.py`
  * `cli.py`
  * `validation.py`
  * `examples/` (scripts y configuraciones de ejemplo).

#### 6.2. Elementos clave

* `config.py`

  * Lectura y validación de archivos YAML/JSON de configuración.

* `models.py`

  * Clases de datos:

    * `ElectrodeParameters`,
    * `OhmicParameters`,
    * `MassTransferParameters`,
    * `OperatingConditions`.

* `kinetics.py`

  * Funciones:

    * `eta_tafel(j, T, params)`,
    * `eta_butler_volmer(j, T, params)`,
    * `j0_T(T, params)`.

* `ohmic.py`

  * `ohmic_overpotential(j, T, ohmic_params)`.

* `mass_transfer.py`

  * `eta_concentration(j, T, mt_params)` (opcional).

* `simulation.py`

  * `compute_polarization_curve(electrode_params, ohmic_params, mt_params, op_conditions)`.
  * `compute_polarization_comparison(electrode_A, electrode_B, ...)`.

* `io.py`

  * Carga de datos experimentales (CSV).
  * Exportación de resultados (CSV).

* `plotting.py`

  * Generación de gráficos (V)–(j) y comparaciones.

* `validation.py`

  * Cálculo de errores RMSE, etc.

* `cli.py`

  * Entrada principal de línea de comandos.

---

### 7. Flujos principales de uso

#### Flujo 1: Simulación de un electrodo

1. Usuario prepara archivo de configuración (`config.yml`) con:

   * parámetros del electrodo,
   * parámetros óhmicos,
   * condiciones de operación.
2. Ejecuta:

   * `python -m pem_sim.cli --config config.yml`.
3. El sistema:

   * lee la configuración,
   * recorre (j) y (T),
   * calcula (V_\text{cell}(j,T)),
   * guarda resultados (CSV) y gráfico.

#### Flujo 2: Comparación de dos electrodos

1. El usuario define en la configuración:

   * `electrode_A`, `electrode_B`.
2. Ejecuta:

   * `python -m pem_sim.cli --config config.yml --compare-electrodes`.
3. El sistema:

   * genera curvas para A y B,
   * produce gráfico comparativo y tabla con (\Delta V(j)).

#### Flujo 3: Validación con datos experimentales

1. El usuario dispone de un archivo `exp_data.csv` con columnas `j_exp`, `V_exp`.
2. Ejecuta:

   * `python -m pem_sim.cli --config config.yml --with-experimental exp_data.csv`.
3. El sistema:

   * simula la curva,
   * interpola para los mismos `j`,
   * calcula errores,
   * genera gráfico simulación vs. experimento.

---

### 8. Librerías de Python requeridas

* Núcleo numérico:

  * `numpy`
  * `scipy` (si se requiere resolver ecuaciones implícitas para Butler–Volmer)
* Gestión de datos:

  * `pandas` (para tablas y CSV)
* Gráficos:

  * `matplotlib`
* Configuración:

  * `pyyaml` (si se usa YAML)
* CLI:

  * `argparse` (estándar) o `typer` / `click` (más amigables)
* Validación de datos (opcional):

  * `pydantic` o `dataclasses`.

---

### 9. Datos de entrada esperados

#### 9.1. Ejemplo de estructura de configuración (YAML)

```yaml
project_name: "pem_h_cell"
units:
  j: "A/cm2"
  T: "K"

operating_conditions:
  T_list: [298, 313, 333]
  j_min: 0.01
  j_max: 1.0
  n_points: 100
  use_concentration_losses: false

electrode_A:
  name: "Ni-HER"
  kinetic_model: "tafel"
  n: 2
  alpha: 0.5
  j0_ref: 0.01   # A/cm2
  Ea: 40000      # J/mol
  T_ref: 298

ohmic:
  components:
    - name: "electrolyte"
      delta: 0.01       # cm
      kappa_ref: 0.5    # S/cm
      Ea_kappa: 15000   # J/mol
      T_ref: 298
    - name: "separator"
      delta: 0.005
      kappa_ref: 0.1
      Ea_kappa: 20000
      T_ref: 298

mass_transfer:
  enabled: false
```

---

### 10. Criterios de aceptación

* El código compila y se ejecuta sin errores en un entorno virtual estándar.
* Para parámetros tomados de un paper de referencia, el simulador reproduce la forma de la curva de polarización con un error medio en voltaje menor a un umbral definido (por ejemplo, < 50 mV en el rango operativo).
* El usuario puede:

  * cambiar fácilmente parámetros en el archivo de configuración,
  * agregar nuevos electrodos (nuevas entradas), sin modificar el código fuente.
* La estructura modular permite:

  * sustituir fácilmente el modelo cinético,
  * añadir nuevos términos (por ejemplo, degradación, calentamiento) en versiones futuras.

---

