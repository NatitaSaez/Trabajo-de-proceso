# Simulador de celda H

> NÃºcleo numÃ©rico y visualizador web para estudiar la electrÃ³lisis/ORR en una celda tipo H con trazabilidad completa de ecuaciones.

## Tabla de contenidos

1. [VisiÃ³n general](#visiÃ³n-general)
2. [Arquitectura del proyecto](#arquitectura-del-proyecto)
3. [Requisitos](#requisitos)
4. [InstalaciÃ³n y ejecuciÃ³n](#instalaciÃ³n-y-ejecuciÃ³n)
5. [Uso del simulador desde Python](#uso-del-simulador-desde-python)
6. [Uso de la interfaz web](#uso-de-la-interfaz-web)
7. [Datos de referencia y supuestos](#datos-de-referencia-y-supuestos)
8. [ValidaciÃ³n y trazabilidad](#validaciÃ³n-y-trazabilidad)
9. [Diagrama de flujo](#diagrama-de-flujo)
10. [PrÃ³ximos pasos sugeridos](#prÃ³ximos-pasos-sugeridos)

## VisiÃ³n general

El repositorio implementa un modelo electroquÃ­mico completo para una celda H, con Ã©nfasis en:

- **SimulaciÃ³n termodinÃ¡mica y cinÃ©tica:** voltaje ideal de Nernst, sobrepotenciales de activaciÃ³n (Tafel), pÃ©rdidas Ã³hmicas y de concentraciÃ³n.
- **AnÃ¡lisis DFT de intermedios ORR:** cÃ¡lculo de barreras energÃ©ticas y actividades teÃ³ricas para distintos catalizadores.
- **Trazabilidad por punto:** cada evaluaciÃ³n registra la ecuaciÃ³n aplicada, los valores sustituidos y el resultado, facilitando auditorÃ­as cientÃ­ficas.
- **Interfaz web interactiva:** control de parÃ¡metros en tiempo real, grÃ¡ficos y tablas descargables.

## Arquitectura del proyecto

```
simulador_celda_H_v2/
â”œâ”€â”€ simulador/                 # NÃºcleo Python
â”‚   â”œâ”€â”€ constants.py           # Constantes fÃ­sicas
â”‚   â”œâ”€â”€ models.py              # Dataclasses de configuraciÃ³n
â”‚   â”œâ”€â”€ data.py                # Valores de referencia y catÃ¡logo de catalizadores
â”‚   â”œâ”€â”€ electrochemistry.py    # Ecuaciones (Nernst, Tafel, Ohm, transporte)
â”‚   â”œâ”€â”€ detail.py              # Registro equation-by-equation (EquationStep, PointDetail)
â”‚   â”œâ”€â”€ orr.py                 # EnergÃ­as de adsorciÃ³n y actividad catalÃ­tica
â”‚   â”œâ”€â”€ simulation.py          # API de alto nivel (ElectrolyzerSimulator, CatalystAnalyzer)
â”‚   â””â”€â”€ __init__.py
â”œâ”€â”€ interfaz_usuario/
â”‚   â”œâ”€â”€ app.py                 # App Dash con sliders, grÃ¡ficos, tablas y exportaciÃ³n CSV
â”‚   â”œâ”€â”€ assets/custom.css      # Estilos (tipografÃ­a, tooltips, layout)
â”‚   â””â”€â”€ requirements.txt       # Dependencias frontend
â”œâ”€â”€ ejemplo_simulador.py       # Script CLI de ejemplo
â”œâ”€â”€ diagrama.svg               # Esquema de arquitectura y flujo
â””â”€â”€ README.md                  # Este documento
```

## Requisitos

- Python 3.10+
- Pip actualizado (`python -m pip install --upgrade pip`)
- Entorno Windows/macOS/Linux (probado en Windows)

### Dependencias Python

```
pip install -r interfaz_usuario/requirements.txt
```

Incluye `dash`, `dash-bootstrap-components` y `plotly`. El nÃºcleo no usa librerÃ­as externas adicionales.

## InstalaciÃ³n y ejecuciÃ³n

```bash
git clone <repo>
cd simulador_celda_H_v2
pip install -r interfaz_usuario/requirements.txt

# OpciÃ³n 1: ejecutar ejemplo CLI
python ejemplo_simulador.py

# OpciÃ³n 2: lanzar la GUI
python interfaz_usuario/app.py
```

Para exponer la app a la red local:

```bash
python -c "from interfaz_usuario.app import app; app.run_server(host='0.0.0.0', port=8050, debug=False)"
```

Luego visitar `http://<IP_LOCAL>:8050/` (la misma instancia incluye la secciÃ³n de ecuaciones detalladas).

## Uso del simulador desde Python

```python
from simulador import data, detail, simulation

# ConfiguraciÃ³n por defecto (80 Â°C, parÃ¡metros de Pt)
sim = simulation.ElectrolyzerSimulator(data.DEFAULT_CONFIG)
voltage = sim.voltage(1.0)  # V celda a 1 A/cm2
print(voltage)

# Curva detallada con trazabilidad
currents = [0.2, 0.5, 1.0, 2.0]
points = detail.detailed_curve(currents, sim.config)
for point in points:
    print(point.table_row())        # resumen numÃ©rico
    for step in point.steps:        # ecuaciones detalladas
        print(step.name, step.result)
```

### AnÃ¡lisis ORR independiente

```python
from simulador import simulation, data
analyzer = simulation.CatalystAnalyzer(data.CATALYSTS["Pt"], temperature=298.15, pH=0)
activity = analyzer.activity(0.9)
barriers = analyzer.limiting_barriers(0.9)
```

## Uso de la interfaz web

1. Ajusta **Condiciones de operaciÃ³n** (temperatura K, pH) y **ConfiguraciÃ³n de corriente** (mÃ­nima, mÃ¡xima, muestras, corriente de desglose).
2. Selecciona el **Catalizador** del catÃ¡logo (Pt, Pd, Au, Ni, Ir, Rh). Los tooltips â€œâ“˜â€ describen tÃ©cnicamente cada control.
3. La secciÃ³n **Valores y grÃ¡ficos** muestra:
   - Tarjetas con: voltaje ideal, pÃ©rdidas por activaciÃ³n, ohm y concentraciÃ³n.
   - Curva de polarizaciÃ³n interactiva.
   - Actividad relativa (escala log) derivada del mÃ³dulo `orr.py`.
4. **Datos generados**: tabla resumen (descargable en CSV) y grilla con las ecuaciones evaluadas punto a punto.
5. **Detalle de ecuaciones**: selecciona un punto para ver todas las fÃ³rmulas y valores utilizados (contentidos en `detail.py`).

## Datos de referencia y supuestos

- Constantes fÃ­sicas: Faraday, R, kB, h, etc. (`constants.py`).
- TermodinÃ¡mica: Î”HÂ°, Î”SÂ°, potencial estÃ¡ndar a 298 K (data ajustable).
- CinÃ©tica: corrientes de intercambio y energÃ­as de activaciÃ³n para Ã¡nodo/cÃ¡todo (inputs Arrhenius).
- Resistencias: conductividad de membrana y resistencias de contacto/electrolito.
- Transporte: corriente lÃ­mite modelada con Arrhenius.
- CatÃ¡logo DFT: energÃ­as de adsorciÃ³n O*/OH* y barreras de disociaciÃ³n por metal (Tabla 2 del informe de requerimientos).

Todos estos parÃ¡metros pueden modificarse en `simulador/data.py` o sustituyendo `ElectrolyzerConfig` con valores experimentales.

## ValidaciÃ³n y trazabilidad

- `simulador/detail.py` produce instancias `PointDetail` con un listado `steps` de `EquationStep`. Cada paso incluye:
  - Nombre de la ecuaciÃ³n (p. ej. â€œVoltaje idealâ€, â€œSobrepotencial activaciÃ³n Ã¡nodoâ€).
  - ExpresiÃ³n simbÃ³lica (Nernst, Tafel, etc.).
  - Diccionario de valores sustituidos (temperatura, corrientes, i0, etc.).
  - Resultado numÃ©rico.
- La GUI usa esta informaciÃ³n para mostrar tanto resÃºmenes como la lista completa de ecuaciones, lo que facilita validar cada tÃ©rmino frente a la teorÃ­a.

## Diagrama de arquitectura y flujo

En `diagrama.svg` encontrarÃ¡s un esquema visual listo para insertar en presentaciones o documentos tÃ©cnicos. Resume:

1. Los mÃ³dulos principales (`constants`, `models`, `data`, `electrochemistry`, `detail`, `orr`, `simulation`) y sus dependencias.
2. El flujo de trabajo: definiciÃ³n de condiciones, construcciÃ³n de `ElectrolyzerConfig`, evaluaciÃ³n punto a punto y anÃ¡lisis ORR.
3. Las salidas disponibles (curva de polarizaciÃ³n detallada y anÃ¡lisis de actividad catalÃ­tica).

Puedes abrirlo con cualquier visor SVG o incrustarlo directamente en reportes para compartir la arquitectura del simulador con otros especialistas.

![Diagrama de arquitectura y flujo](diagrama.svg)

