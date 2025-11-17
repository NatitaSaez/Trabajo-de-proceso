### Verificación de ecuaciones y variables vs. `simulador_celda_h_0D_config.md`

Este documento valida que el núcleo v2 (código Python) implementa las ecuaciones y claves YAML descritas en `simulador_celda_h_0D_config.md`, e indica las desviaciones observadas.

---

#### Potencial reversible (`V_rev`)
- **Código**: `simulador/simulation_v2.py:57-125` (`_reversible_potential`).
- **Claves YAML usadas**: `thermo.V_ref`, `thermo.delta_s_ref`, `thermo.delta_h_ref`, `thermo.T_ref`, `thermo.n`, `thermo.use_nernst`, `thermo.p_h2`, `thermo.p_o2`, `thermo.activity_h2o`.
- **Ecuación aplicada**:
  - Si hay ΔH y ΔS: `V_rev = -(ΔH - T·ΔS)/(nF)`.
  - Si solo hay ΔS: `V_rev = V_ref + (ΔS/(nF))·(T - T_ref)`.
  - Si `use_nernst`: añade `(RT/(nF))·ln(p_H2·sqrt(p_O2)/a_H2O)`.
- **Desviaciones**: Se prioriza el uso de ΔH+ΔS cuando están ambos; el doc menciona la forma lineal con ΔS como aproximación, consistente.

#### Cinética (Tafel / Butler-Volmer) y Arrhenius de `j0`
- **Código**: `simulador/simulation_v2.py:235-254` (`_eta_activation`, `_eta_tafel`, `_eta_butler_volmer`).
- **Claves YAML**: `electrode_A/B.kinetic_model`, `j0_ref`, `Ea`, `alpha`, `alpha_a`, `alpha_c`, `n`, `T_ref`.
- **Ecuaciones**:
  - Arrhenius: `j0(T) = j0_ref * exp(-Ea/R * (1/T - 1/Tref))`.
  - Tafel: `η = (RT/(α n F))·ln(j/j0)`.
  - BV: resuelve `j = j0[exp(α_a nFη/RT) - exp(-α_c nFη/RT)]` (usa asinh si simétrico).
- **Desviaciones**: Ninguna relevante; se exige `alpha_a/alpha_c` cuando se elige BV.

#### Pérdidas óhmicas (capas en serie)
- **Código**: `simulador/simulation_v2.py:256-295` (`_eta_ohmic`).
- **Claves YAML**: `ohmic.components[].delta`, `kappa_ref`, `Ea_kappa`, `T_ref`, y `ohmic.extra_resistance`.
- **Ecuación**: `η_ohm = j * Σ (δ_i / κ_i(T)) + j * R_extra`, con `κ_i(T)` vía Arrhenius.
- **Desviaciones**: Ninguna; coincide con capa en serie esperada.

#### Pérdidas de concentración
- **Código**: `simulador/simulation_v2.py:296-350` (`_eta_concentration`).
- **Claves YAML**: `mass_transfer.enabled`, `j_lim`, `Ea_jlim`, `D_eff`, `C_bulk`, `delta_dif`, `T_ref`; `operating.use_concentration_losses` fuerza `enabled`.
- **Ecuaciones**:
  - Si `j_lim` provisto: `j_lim(T)` por Arrhenius.
  - Si no: `j_lim = nF D_eff C_bulk / delta_dif`.
  - `η_conc = -(RT/(nF)) · ln(1 - j/j_lim)`.
- **Desviaciones**: Ninguna; incluye opción de desactivar.

#### Curva completa
- **Código**: `simulador/simulation_v2.py:400-452` (`evaluate_point_v2`).
- **Ecuación**: `V_cell = V_rev + η_act + η_ohm + η_conc` por punto (j, T).
- **Trazabilidad**: Cada punto guarda `steps` (`EquationStep`) con `name`, `expression`, `values`, `result`.

#### Mapeo de claves YAML
- **Estructuras**: Definidas en `simulador/config_v2.py:29-213` (`OperatingGrid`, `ThermoSettings`, `ElectrodeKineticsV2`, `OhmicLayer/Config`, `MassTransferConfig`, `SimulationConfigV2`, `load_config`).
- **Cobertura**: Todas las claves del doc (`operating_conditions`, `thermo`, `electrode_A/B`, `ohmic`, `mass_transfer`, `units`) están presentes. No se usan claves adicionales.

#### Desviaciones menores o consideraciones
- El doc menciona «potencial estandar a 298 K (como V_ref=1.23)»; el código permite ΔH/ΔS si se proveen, con prioridad sobre la forma lineal.
- En BV, si `alpha_a` y `alpha_c` no están, se exige definirlos (no se asume 0.5 salvo en Tafel/simétrico).
- Conductividad: modelo Arrhenius; no hay forma alternativa (lineal) en el código.
- Para concentración, si `use_concentration_losses` está en `operating_conditions`, se fuerza `enabled` aunque `mass_transfer.enabled` sea false.

#### Conclusión
El núcleo v2 implementa las ecuaciones descritas en `simulador_celda_h_0D_config.md` (V_rev con ΔS/ΔH/Nernst, Tafel/BV con Arrhenius de j0, óhmicas por capas, concentración con j_lim o difusión) y usa las mismas claves YAML. No se detectan desviaciones funcionales; solo se resalta la prioridad de ΔH+ΔS si están presentes y la obligatoriedad de `alpha_a/alpha_c` para modelo Butler-Volmer.
