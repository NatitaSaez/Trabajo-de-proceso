# Especificación de parámetros para simulador 0D de curva de polarización (celda H, Ni-foam, Lee 2022 / Olguín 2025)

## 1. Tabla de datos necesarios para el simulador 0D

| Bloque                  | Clave YAML                                | Símbolo                | Qué es / por qué se usa                                                                 | Unidad         | Comentario / Fuente aproximada (Lee/Olguín)                |
|-------------------------|-------------------------------------------|------------------------|-----------------------------------------------------------------------------------------|----------------|------------------------------------------------------------|
| Proyecto / unidades     | `project_name`                           | –                      | Nombre del caso de simulación                                                          | –              | Solo organizativo                                           |
|                         | `units.j`                                | –                      | Unidad de densidad de corriente usada internamente                                     | A/cm²          | En tu caso A/cm²                                            |
|                         | `units.T`                                | –                      | Unidad de temperatura                                                                  | K              |                                                            |
| Condiciones de operación| `operating_conditions.T_list`            | T                      | Lista de temperaturas de simulación                                                    | K              | p.ej. [298, 353]                                            |
|                         | `operating_conditions.j_min`             | j_min                  | Corriente mínima de la curva                                                           | A/cm²          |                                                            |
|                         | `operating_conditions.j_max`             | j_max                  | Corriente máxima de la curva                                                           | A/cm²          | Debe cubrir el rango del paper (~1–2 A/cm²)                |
|                         | `operating_conditions.n_points`          | –                      | Nº de puntos en la curva                                                               | –              |                                                            |
|                         | `operating_conditions.use_concentration_losses` | –               | Activar/desactivar pérdidas de concentración                                           | bool           |                                                            |
| Termodinámica           | `thermo.V_ref`                           | V_rev(T_ref)           | Potencial reversible a T_ref (aprox. 1.23 V a 298 K)                                   | V              | Datos estándar agua; lo que ya tienes                       |
|                         | `thermo.delta_s_ref`                     | ΔS°                    | Entropía estándar reacción global (para dependencia con T)                             | J/mol·K        | ~163 J/mol·K agua                                          |
|                         | `thermo.T_ref`                           | T_ref                  | Temp. ref. para V_ref y correcciones                                                   | K              | 298.15                                                      |
|                         | `thermo.n`                               | n                      | Nº de e⁻ por mol (HER/OER global)                                                      | –              | 2                                                           |
|                         | `thermo.use_nernst`                      | –                      | Si corriges por presiones parciales                                                    | bool           | Para 0D simple: false                                       |
|                         | `thermo.p_h2`, `thermo.p_o2`             | p_H2, p_O2             | Presiones parciales si usas Nernst                                                     | bar            | 1 bar típico                                                |
|                         | `thermo.activity_h2o`                    | a_H2O                  | Actividad del agua (≈1 en primera aproximación)                                        | –              |                                                            |
| Electrodos cinética (HER)| `electrode_A.name`                      | –                      | Nombre electrocatalizador 1 (HER)                                                      | –              | p.ej. “Ni-HER (Lee 2022)”                                   |
|                         | `electrode_A.kinetic_model`              | –                      | Modelo cinético: "tafel" o "butler-volmer"                                         | –              | Para 0D: Tafel                                              |
|                         | `electrode_A.n`                          | n                      | Nº e⁻ en HER                                                                           | –              | 2                                                           |
|                         | `electrode_A.alpha`                      | alpha_HER              | Coeficiente de transferencia efectivo HER                                              | –              | Lee reporta alpha_a,alpha_c; aquí usas uno efectivo         |
|                         | `electrode_A.j0_ref`                     | j0_HER(T_ref)          | Densidad de corriente de intercambio HER a T_ref                                       | A/cm²          | Desde Lee (23.4 A/m² ≈ 2.34e-3 A/cm²)                      |
|                         | `electrode_A.Ea`                         | Ea_HER                 | Energía de activación HER                                                              | J/mol          | ~4.0×10⁴ J/mol Lee                                         |
|                         | `electrode_A.T_ref`                      | T_ref_HER              | Temp. a la que se midió j0                                                             | K              | 353.15 K (80 °C en Lee)                                    |
| Electrodos cinética (OER)| `electrode_B.name`                      | –                      | Nombre electrocatalizador 2 (OER)                                                      | –              | p.ej. “Ni-OER (Lee 2022)”                                   |
|                         | `electrode_B.kinetic_model`              | –                      | Modelo cinético OER                                                                    | –              | "tafel" simple                                            |
|                         | `electrode_B.n`                          | n                      | Nº e⁻ en OER                                                                           | –              | 2                                                           |
|                         | `electrode_B.alpha`                      | alpha_OER              | Coeficiente de transferencia efectivo OER                                              | –              | Lee da alpha_a,alpha_c                                      |
|                         | `electrode_B.j0_ref`                     | j0_OER(T_ref)          | Densidad de intercambio OER a T_ref                                                    | A/cm²          | ~9.3 A/m² ≈ 9.3e-4 A/cm² en Lee                            |
|                         | `electrode_B.Ea`                         | Ea_OER                 | Energía de activación OER                                                              | J/mol          | ~4.6×10⁴ J/mol                                              |
|                         | `electrode_B.T_ref`                      | T_ref_OER              | Temp. ref OER                                                                          | K              | ~343.15 (70 °C) si sigues el paper                         |
| Ohmico (IR)             | `ohmic.components[i].name`               | –                      | Nombre del componente (membrana, electrolito, electr. etc.)                            | –              | Para identificar                                            |
|                         | `ohmic.components[i].delta`              | δ_i                    | Espesor del componente i                                                              | m              | Lee: ~0.7 mm electrodos, 0.46 mm Zirfon                     |
|                         | `ohmic.components[i].kappa_ref`          | kappa_i(T_ref)         | Conductividad efectiva a T_ref                                                         | S/m            | KOH, Zirfon, Ni, SS según tabla                             |
|                         | `ohmic.components[i].Ea_kappa`           | Ea_kappa_i             | Energía activación conductividad (si usas Arrhenius)                                  | J/mol          | Puedes usar valores empíricos/literatura                    |
|                         | `ohmic.components[i].T_ref`              | T_ref                  | Temp. ref para kappa_i                                                                | K              | 298.15 o 353.15                                             |
|                         | `ohmic.extra_resistance`                 | R_extra                | Resistencias parásitas (contactos, cables) en Ω·cm² o Ω·m² (según conversión)         | Ω·cm²          | Ajuste fino contra la curva experimental                    |
| Transferencia de masa   | `mass_transfer.enabled`                  | –                      | Activar modelo de pérdidas de concentración                                           | bool           |                                                            |
|                         | `mass_transfer.j_lim`                    | j_lim_ref              | Corriente límite a T_ref                                                               | A/cm²          | Ajustada a cola de la curva del paper                       |
|                         | `mass_transfer.Ea_jlim`                  | Ea_jlim                | Dependencia de j_lim con T (opcional)                                                 | J/mol          | Opcional; se puede fijar 0 al comienzo                      |

---

## 2. YAML ejemplo adaptado a Ni-foam (Lee 2022)

```yaml
project_name: "celda_h_ni_lee2022"
units:
  j: "A/cm2"
  T: "K"

operating_conditions:
  T_list: [298.15, 353.15]   # 25 °C y 80 °C
  j_min: 0.01                # A/cm2
  j_max: 1.5                 # A/cm2 (rango típico en el paper)
  n_points: 60
  use_concentration_losses: true

thermo:
  V_ref: 1.23                # V_rev a 25 °C aprox.
  delta_s_ref: 163.0         # J/mol/K (agua)
  T_ref: 298.15
  n: 2
  use_nernst: false
  p_h2: 1.0                  # bar
  p_o2: 1.0                  # bar
  activity_h2o: 1.0

electrode_A:
  # Cátodo: HER en Ni foam (Lee 2022)
  name: "Ni-HER-Lee2022"
  kinetic_model: "tafel"
  n: 2
  alpha: 0.8                 # efectivo (Lee reporta alpha_a/alpha_c; aquí lo simplificas)
  j0_ref: 0.00234            # A/cm2  (23.4 A/m2 / 1e4)
  Ea: 40000                  # J/mol (~4.0e4, desde Lee)
  T_ref: 353.15              # K, 80 °C (temp. de los datos HER en el paper)

electrode_B:
  # Ánodo: OER en Ni foam (Lee 2022)
  name: "Ni-OER-Lee2022"
  kinetic_model: "tafel"
  n: 2
  alpha: 1.1                 # efectivo para OER (approx desde alpha_a/alpha_c de Lee)
  j0_ref: 0.00093            # A/cm2 (9.3 A/m2 / 1e4)
  Ea: 46156                  # J/mol (4.6156e4 aprox, desde Lee)
  T_ref: 343.15              # K, ~70 °C (temp de referencia en el paper para OER)

ohmic:
  components:
    - name: "electrodo_negativo_Ni"
      delta: 0.0007          # m (0.70 mm)
      kappa_ref: 1.43e7      # S/m (conductividad eléctrica Ni)
      Ea_kappa: 0            # J/mol (puedes empezar sin dependencia con T)
      T_ref: 298.15

    - name: "electrodo_positivo_Ni"
      delta: 0.0007          # m
      kappa_ref: 1.43e7      # S/m
      Ea_kappa: 0
      T_ref: 298.15

    - name: "separador_Zirfon"
      delta: 0.00046         # m (0.46 mm)
      kappa_ref: 5.0         # S/m (ejemplo; ajustar según datos del paper/datasheet)
      Ea_kappa: 15000        # J/mol (ejemplo para dependencia iónica)
      T_ref: 298.15

    - name: "electrolito_KOH_30wt"
      delta: 0.002           # m (gap libre entre electrodos; ajustable según celda H)
      kappa_ref: 600.0       # S/m (orden de magnitud KOH 30 wt% a ~80 °C)
      Ea_kappa: 12000        # J/mol
      T_ref: 353.15

  extra_resistance: 0.02     # ohm*cm2 (contactos, colectores, etc; ajustar como parámetro libre)

mass_transfer:
  enabled: true
  j_lim: 2.0                 # A/cm2 (corriente límite efectiva; ajustar con cola de la curva)
  Ea_jlim: 0                 # J/mol (puedes dejar 0 inicialmente)
```

