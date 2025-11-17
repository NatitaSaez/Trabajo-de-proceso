Voy a suponer que:

* Vas a usar un modelo 0D con:

  * termodinámica global del agua,
  * 2 electrodos (HER y OER, ambos Ni-foam como en Lee),
  * pérdidas óhmicas sumadas en serie,
  * y una opción sencilla de pérdidas por concentración vía (j_\text{lim}).
* Las unidades de (j) en el simulador se mantienen en A/cm², como en tu YAML.

Primero la tabla de qué datos necesitas (y dónde van en el YAML). Luego te doy un YAML completo ya adaptado a “Ni-HER / Ni-OER tipo Lee”.

---

## 1. Tabla de datos necesarios para el simulador 0D

| Bloque                   | Clave YAML                                      | Símbolo                          | Qué es / por qué se usa                                                       | Unidad  | Comentario / Fuente aproximada (Lee/Olguín)             |
| ------------------------ | ----------------------------------------------- | -------------------------------- | ----------------------------------------------------------------------------- | ------- | ------------------------------------------------------- |
| Proyecto / unidades      | `project_name`                                  | –                                | Nombre del caso de simulación                                                 | –       | Solo organizativo                                       |
|                          | `units.j`                                       | –                                | Unidad de densidad de corriente usada internamente                            | A/cm²   | En tu caso A/cm²                                        |
|                          | `units.T`                                       | –                                | Unidad de temperatura                                                         | K       |                                                         |
| Condiciones de operación | `operating_conditions.T_list`                   | (T)                              | Lista de temperaturas de simulación                                           | K       | p.ej. [298, 353]                                        |
|                          | `operating_conditions.j_min`                    | (j_\text{min})                   | Corriente mínima de la curva                                                  | A/cm²   |                                                         |
|                          | `operating_conditions.j_max`                    | (j_\text{max})                   | Corriente máxima de la curva                                                  | A/cm²   | Debe cubrir el rango del paper (~1–2 A/cm²)             |
|                          | `operating_conditions.n_points`                 | –                                | Nº de puntos en la curva                                                      | –       |                                                         |
|                          | `operating_conditions.use_concentration_losses` | –                                | Activar/desactivar (\eta_\text{conc})                                         | bool    |                                                         |
| Termodinámica            | `thermo.V_ref`                                  | (V_\text{rev}(T_\text{ref}))     | Potencial reversible a (T_\text{ref}) (aprox. 1.23 V a 298 K)                 | V       | Datos estándar agua; lo que ya tienes                   |
|                          | `thermo.delta_s_ref`                            | (\Delta S^\circ)                 | Entropía estándar reacción global (para dependencia con T)                    | J/mol·K | ~163 J/mol·K agua                                       |
|                          | `thermo.T_ref`                                  | (T_\text{ref})                   | Temp. ref. para V_ref y correcciones                                          | K       | 298.15                                                  |
|                          | `thermo.n`                                      | (n)                              | Nº de e⁻ por mol (HER/OER global)                                             | –       | 2                                                       |
|                          | `thermo.use_nernst`                             | –                                | Si corriges por presiones parciales                                           | bool    | Para 0D simple: false                                   |
|                          | `thermo.p_h2`, `thermo.p_o2`                    | (p_{H_2},p_{O_2})                | Presiones parciales si usas Nernst                                            | bar     | 1 bar típico                                            |
|                          | `thermo.activity_h2o`                           | (a_{H_2O})                       | Actividad del agua (≈1 en primera aproximación)                               | –       |                                                         |
| Electrodos cinética      | `electrode_A.name`                              | –                                | Nombre electrocatalizador 1 (HER)                                             | –       | p.ej. “Ni-HER (Lee 2022)”                               |
| (HER)                    | `electrode_A.kinetic_model`                     | –                                | Modelo cinético: `"tafel"` o `"butler-volmer"`                                | –       | Para 0D: Tafel                                          |
|                          | `electrode_A.n`                                 | (n)                              | Nº e⁻ en HER                                                                  | –       | 2                                                       |
|                          | `electrode_A.alpha`                             | (\alpha_\text{HER})              | Coeficiente de transferencia efectivo HER                                     | –       | Lee reporta (\alpha_a,\alpha_c); aquí usas uno efectivo |
|                          | `electrode_A.j0_ref`                            | (j_{0,\text{HER}}(T_\text{ref})) | Densidad de corriente de intercambio HER a (T_\text{ref})                     | A/cm²   | Desde Lee (23.4 A/m² ≈ 2.34e-3 A/cm²)                   |
|                          | `electrode_A.Ea`                                | (E_{a,\text{HER}})               | Energía de activación HER                                                     | J/mol   | ~4.0×10⁴ J/mol Lee                                      |
|                          | `electrode_A.T_ref`                             | (T_\text{ref,HER})               | Temp. a la que se midió (j_0)                                                 | K       | 353.15 K (80 °C en Lee)                                 |
| Electrodos cinética      | `electrode_B.name`                              | –                                | Nombre electrocatalizador 2 (OER)                                             | –       | p.ej. “Ni-OER (Lee 2022)”                               |
| (OER)                    | `electrode_B.kinetic_model`                     | –                                | Modelo cinético OER                                                           | –       | `"tafel"` simple                                        |
|                          | `electrode_B.n`                                 | (n)                              | Nº e⁻ en OER                                                                  | –       | 2                                                       |
|                          | `electrode_B.alpha` **o** `alpha_a/alpha_c`     | (\alpha_\text{OER})              | Coeficiente de transferencia efectivo OER                                     | –       | Lee da (\alpha_a,\alpha_c)                              |
|                          | `electrode_B.j0_ref`                            | (j_{0,\text{OER}}(T_\text{ref})) | Densidad de intercambio OER a (T_\text{ref})                                  | A/cm²   | ~9.3 A/m² ≈ 9.3e-4 A/cm² en Lee                         |
|                          | `electrode_B.Ea`                                | (E_{a,\text{OER}})               | Energía de activación OER                                                     | J/mol   | ~4.6×10⁴ J/mol                                          |
|                          | `electrode_B.T_ref`                             | (T_\text{ref,OER})               | Temp. ref OER                                                                 | K       | ~343.15 (70 °C) si sigues el paper                      |
| Ohmico (IR)              | `ohmic.components[i].name`                      | –                                | Nombre del componente (membrana, electrolito, electr. etc.)                   | –       | Para identificar                                        |
|                          | `ohmic.components[i].delta`                     | (\delta_i)                       | Espesor del componente i                                                      | m       | Lee: ~0.7 mm electrodos, 0.46 mm Zirfon                 |
|                          | `ohmic.components[i].kappa_ref`                 | (\kappa_{i}(T_\text{ref}))       | Conductividad efectiva a (T_\text{ref})                                       | S/m     | KOH, Zirfon, Ni, SS según tabla                         |
|                          | `ohmic.components[i].Ea_kappa`                  | (E_{\kappa,i})                   | Energía activación conductividad (si usas Arrhenius)                          | J/mol   | Puedes usar valores empíricos/literatura                |
|                          | `ohmic.components[i].T_ref`                     | (T_\text{ref})                   | Temp. ref para (\kappa_i)                                                     | K       | 298.15 o 353.15                                         |
|                          | `ohmic.extra_resistance`                        | (R_\text{extra})                 | Resistencias parásitas (contactos, cables) en Ω·cm² o Ω·m² (según conversión) | Ω·cm²   | Ajuste fino contra la curva experimental                |
| Transferencia de masa    | `mass_transfer.enabled`                         | –                                | Activar modelo de (\eta_\text{conc})                                          | bool    |                                                         |
|                          | `mass_transfer.j_lim`                           | (j_\text{lim,ref})               | Corriente límite a (T_\text{ref})                                             | A/cm²   | Ajustada a cola de la curva del paper                   |
|                          | `mass_transfer.Ea_jlim`                         | (E_{a,j_\text{lim}})             | Dependencia de (j_\text{lim}) con T (opcional)                                | J/mol   | Opcional; se puede fijar 0 al comienzo                  |

Con esto tienes un “mapa” de qué necesitas realmente del paper:

* De Lee: básicamente (i_0), (E_a), (\alpha), espesores, conductividades, porosidades, T de operación.
* De Olguín: estructura de resistencias en serie, posibles dependencias de (\kappa(T)) y propiedades del electrolito.

---

## 2. YAML ejemplo adaptado a Ni-foam (Lee 2022)

Te dejo ahora un YAML coherente con esa tabla, usando valores razonables y unidades A/cm² (he convertido (i_0) de A/m² a A/cm² dividiendo por 10⁴). Ajusta números finos cuando calibres con la curva experimental.

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

Notas rápidas para que lo uses:

* Lo esencial que viene “del paper” y sí deberías respetar:

  * (j_0) de HER y OER en A/m² → convertido a A/cm².
  * (E_a) para cada reacción.
  * Espesores de electrodos y separador.
* Lo que es más bien **ajustable** en tu simulador:

  * (\alpha) efectivos (puedes empezar con 0.8 y 1.1 y luego ajustar).
  * Conductividades del electrolito y Zirfon (si no tienes valores exactos, úsalos como parámetros de ajuste).
  * `extra_resistance` y `j_lim`.


