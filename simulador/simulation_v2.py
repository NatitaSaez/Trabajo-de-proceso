"""Simulador 0D v2 con soporte de YAML, doble electrodo y trazabilidad básica."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Dict, Iterable, List, Sequence, Tuple

from .config_v2 import (
    ElectrodeKineticsV2,
    MassTransferConfig,
    OhmicConfig,
    OhmicLayer,
    SimulationConfigV2,
    ThermoSettings,
)
from .constants import CONSTANTS, PhysicalConstants
from .detail import EquationStep
from .electrochemistry import arrhenius


@dataclass
class PointResultV2:
    """Resultado por punto y electrodo, con contribuciones y pasos."""

    electrode: str
    current_density: float
    temperature: float
    V_rev: float
    eta_act: float
    eta_ohm: float
    eta_conc: float
    V_cell: float
    model_act: str
    j0_T: float
    r_total: float
    j_lim: float | None
    steps: List[EquationStep]

    def to_row(self) -> Dict[str, float]:
        return {
            "electrode": self.electrode,
            "j": self.current_density,
            "T": self.temperature,
            "V_rev": self.V_rev,
            "eta_act": self.eta_act,
            "eta_ohm": self.eta_ohm,
            "eta_conc": self.eta_conc,
            "V_cell": self.V_cell,
            "model_act": self.model_act,
            "j0_T": self.j0_T,
            "r_total": self.r_total,
            "j_lim": self.j_lim if self.j_lim is not None else float("nan"),
        }


def _reversible_potential(
    thermo: ThermoSettings, temperature: float, constants: PhysicalConstants
) -> Tuple[float, List[EquationStep]]:
    steps: List[EquationStep] = []
    n = thermo.electrons
    V_base: float
    if thermo.delta_h_ref is not None and thermo.delta_s_ref is not None:
        delta_g = thermo.delta_h_ref - temperature * thermo.delta_s_ref
        V_base = -delta_g / (n * constants.faraday)
        steps.append(
            EquationStep(
                name="Potencial reversible (ΔG)",
                expression="V_rev = -ΔG/(nF) con ΔG = ΔH - T·ΔS",
                values={
                    "ΔH_ref": thermo.delta_h_ref,
                    "ΔS_ref": thermo.delta_s_ref,
                    "T": temperature,
                    "n": n,
                    "F": constants.faraday,
                    "ΔG": delta_g,
                },
                result=V_base,
            )
        )
    else:
        slope = (thermo.delta_s_ref or 0.0) / (n * constants.faraday)
        V_base = thermo.V_ref + slope * (temperature - thermo.T_ref)
        steps.append(
            EquationStep(
                name="Potencial reversible (aprox. lineal)",
                expression="V_rev = V_ref + (ΔS/(nF))·(T - T_ref)",
                values={
                    "V_ref": thermo.V_ref,
                    "ΔS_ref": thermo.delta_s_ref or 0.0,
                    "n": n,
                    "F": constants.faraday,
                    "T": temperature,
                    "T_ref": thermo.T_ref,
                    "slope": slope,
                },
                result=V_base,
            )
        )

    if thermo.use_nernst:
        quotient = (
            thermo.pressure_h2
            * math.sqrt(max(thermo.pressure_o2, 1e-12))
            / max(thermo.activity_h2o, 1e-12)
        )
        nernst_term = constants.gas_constant * temperature / (n * constants.faraday) * math.log(quotient)
        V_base += nernst_term
        steps.append(
            EquationStep(
                name="Término de Nernst",
                expression="(RT/(nF))·ln(Q)",
                values={
                    "R": constants.gas_constant,
                    "T": temperature,
                    "n": n,
                    "F": constants.faraday,
                    "Q": quotient,
                    "ln(Q)": math.log(quotient),
                },
                result=nernst_term,
            )
        )

    return V_base, steps


def _j0_temperature(
    kinetics: ElectrodeKineticsV2, temperature: float, constants: PhysicalConstants
) -> Tuple[float, EquationStep]:
    j0_t = arrhenius(kinetics.j0_ref, kinetics.Ea, temperature, kinetics.T_ref, constants)
    step = EquationStep(
        name=f"j0(T) {kinetics.name}",
        expression="j0 = j0_ref * exp(-Ea/R * (1/T - 1/Tref))",
        values={
            "j0_ref": kinetics.j0_ref,
            "Ea": kinetics.Ea or 0.0,
            "R": constants.gas_constant,
            "T": temperature,
            "T_ref": kinetics.T_ref,
        },
        result=j0_t,
    )
    return j0_t, step


def _eta_tafel(
    current_density: float,
    kinetics: ElectrodeKineticsV2,
    j0: float,
    temperature: float,
    constants: PhysicalConstants,
) -> Tuple[float, EquationStep]:
    prefactor = constants.gas_constant * temperature / (kinetics.alpha * kinetics.n * constants.faraday)
    eta = prefactor * math.log(current_density / j0)
    step = EquationStep(
        name=f"η_act Tafel {kinetics.name}",
        expression="η = (RT/(α·nF))·ln(j/j0)",
        values={
            "R": constants.gas_constant,
            "T": temperature,
            "alpha": kinetics.alpha,
            "n": kinetics.n,
            "F": constants.faraday,
            "j": current_density,
            "j0": j0,
            "prefactor": prefactor,
        },
        result=eta,
    )
    return eta, step


def _eta_butler_volmer(
    current_density: float,
    kinetics: ElectrodeKineticsV2,
    j0: float,
    temperature: float,
    constants: PhysicalConstants,
) -> Tuple[float, EquationStep]:
    alpha_a = kinetics.alpha_a or kinetics.alpha or 0.5
    alpha_c = kinetics.alpha_c or kinetics.alpha or 0.5
    beta_a = alpha_a * kinetics.n * constants.faraday / (constants.gas_constant * temperature)
    beta_c = alpha_c * kinetics.n * constants.faraday / (constants.gas_constant * temperature)

    eta: float
    if abs(alpha_a - alpha_c) < 1e-9:
        # Simétrico -> solución analítica con asinh
        eta = math.asinh(current_density / (2 * j0)) / beta_a
    else:
        # Resolver numéricamente con búsqueda de raíces simple
        def residual(eta_guess: float) -> float:
            return j0 * (math.exp(beta_a * eta_guess) - math.exp(-beta_c * eta_guess)) - current_density

        # Intervalo amplio; si no encierra raíz, ampliar suavemente
        lower, upper = -2.0, 2.0
        res_l, res_u = residual(lower), residual(upper)
        attempts = 0
        while res_l * res_u > 0 and attempts < 6:
            lower *= 1.5
            upper *= 1.5
            res_l, res_u = residual(lower), residual(upper)
            attempts += 1
        # Bisección simple
        for _ in range(80):
            mid = 0.5 * (lower + upper)
            res_m = residual(mid)
            if res_l * res_m <= 0:
                upper, res_u = mid, res_m
            else:
                lower, res_l = mid, res_m
        eta = 0.5 * (lower + upper)

    step = EquationStep(
        name=f"η_act BV {kinetics.name}",
        expression="j = j0[exp(α_a nFη/RT) - exp(-α_c nFη/RT)]",
        values={
            "alpha_a": alpha_a,
            "alpha_c": alpha_c,
            "n": kinetics.n,
            "F": constants.faraday,
            "R": constants.gas_constant,
            "T": temperature,
            "beta_a": beta_a,
            "beta_c": beta_c,
            "j": current_density,
            "j0": j0,
            "eta": eta,
        },
        result=eta,
    )
    return eta, step


def _eta_activation(
    current_density: float,
    kinetics: ElectrodeKineticsV2,
    temperature: float,
    constants: PhysicalConstants,
) -> Tuple[float, List[EquationStep], float]:
    steps: List[EquationStep] = []
    j0_t, j0_step = _j0_temperature(kinetics, temperature, constants)
    steps.append(j0_step)
    if j0_t <= 0:
        raise ValueError(f"j0(T) inválido para {kinetics.name}: {j0_t}")

    model = kinetics.kinetic_model
    if model in {"tafel"}:
        eta, eta_step = _eta_tafel(current_density, kinetics, j0_t, temperature, constants)
    else:
        eta, eta_step = _eta_butler_volmer(current_density, kinetics, j0_t, temperature, constants)
    steps.append(eta_step)
    return eta, steps, j0_t


def _eta_ohmic(
    current_density: float,
    ohmic: OhmicConfig,
    temperature: float,
    constants: PhysicalConstants,
) -> Tuple[float, List[EquationStep], float]:
    steps: List[EquationStep] = []
    r_total = ohmic.extra_resistance
    for layer in ohmic.layers:
        kappa_t = arrhenius(layer.kappa_ref, layer.Ea_kappa, temperature, layer.T_ref, constants)
        r_layer = layer.delta / kappa_t
        r_total += r_layer
        steps.append(
            EquationStep(
                name=f"R capa {layer.name}",
                expression="R = delta / kappa(T)",
                values={
                    "delta": layer.delta,
                    "kappa_ref": layer.kappa_ref,
                    "Ea_kappa": layer.Ea_kappa or 0.0,
                    "T": temperature,
                    "T_ref": layer.T_ref,
                    "kappa(T)": kappa_t,
                },
                result=r_layer,
            )
        )

    eta_ohm = current_density * r_total
    steps.append(
        EquationStep(
            name="Perdida ohmica total",
            expression="η_ohm = j · R_total",
            values={"j": current_density, "R_total": r_total},
            result=eta_ohm,
        )
    )
    return eta_ohm, steps, r_total


def _eta_concentration(
    current_density: float,
    mass: MassTransferConfig,
    temperature: float,
    electrons: int,
    constants: PhysicalConstants,
) -> Tuple[float, List[EquationStep], float | None]:
    steps: List[EquationStep] = []
    if not mass.enabled:
        steps.append(
            EquationStep(
                name="Pérdida por concentración",
                expression="Desactivada (η_conc = 0)",
                values={},
                result=0.0,
            )
        )
        return 0.0, steps, None

    if mass.j_lim is not None:
        j_lim = arrhenius(mass.j_lim, mass.Ea_jlim, temperature, mass.T_ref, constants)
        steps.append(
            EquationStep(
                name="j_lim (Arrhenius)",
                expression="j_lim = j_lim_ref * exp(-Ea/R * (1/T - 1/Tref))",
                values={
                    "j_lim_ref": mass.j_lim,
                    "Ea": mass.Ea_jlim or 0.0,
                    "R": constants.gas_constant,
                    "T": temperature,
                    "T_ref": mass.T_ref,
                },
                result=j_lim,
            )
        )
    else:
        if None in (mass.D_eff, mass.C_bulk, mass.delta_dif):
            raise ValueError("Faltan parámetros para calcular j_lim (requiere D_eff, C_bulk, delta_dif).")
        j_lim = electrons * constants.faraday * mass.D_eff * mass.C_bulk / mass.delta_dif
        steps.append(
            EquationStep(
                name="j_lim (difusión)",
                expression="j_lim = nF D_eff C_bulk / delta_dif",
                values={
                    "n": electrons,
                    "F": constants.faraday,
                    "D_eff": mass.D_eff,
                    "C_bulk": mass.C_bulk,
                    "delta_dif": mass.delta_dif,
                },
                result=j_lim,
            )
        )

    if current_density >= j_lim:
        raise ValueError(f"La densidad de corriente {current_density} supera j_lim {j_lim}.")

    prefactor = constants.gas_constant * temperature / (electrons * constants.faraday)
    eta_conc = -prefactor * math.log(1 - current_density / j_lim)
    steps.append(
        EquationStep(
            name="η_conc",
            expression="η = -(RT/(nF))·ln(1 - j/j_lim)",
            values={
                "R": constants.gas_constant,
                "T": temperature,
                "n": electrons,
                "F": constants.faraday,
                "j": current_density,
                "j_lim": j_lim,
                "prefactor": prefactor,
            },
            result=eta_conc,
        )
    )
    return eta_conc, steps, j_lim


def evaluate_point_v2(
    current_density: float,
    temperature: float,
    electrode: ElectrodeKineticsV2,
    config: SimulationConfigV2,
    constants: PhysicalConstants = CONSTANTS,
) -> PointResultV2:
    """Evalúa un punto (j, T) para un electrodo dado y devuelve contribuciones y pasos."""

    steps: List[EquationStep] = []
    V_rev, thermo_steps = _reversible_potential(config.thermo, temperature, constants)
    steps.extend(thermo_steps)

    eta_act, act_steps, j0_t = _eta_activation(current_density, electrode, temperature, constants)
    steps.extend(act_steps)

    eta_ohm, ohm_steps, r_total = _eta_ohmic(current_density, config.ohmic, temperature, constants)
    steps.extend(ohm_steps)

    mass_cfg = config.mass_transfer
    if config.operating.use_concentration_losses and not mass_cfg.enabled:
        mass_cfg = replace(mass_cfg, enabled=True)
    eta_conc, conc_steps, j_lim = _eta_concentration(
        current_density,
        mass_cfg,
        temperature,
        electrons=electrode.n,
        constants=constants,
    )
    steps.extend(conc_steps)

    V_cell = V_rev + eta_act + eta_ohm + eta_conc
    steps.append(
        EquationStep(
            name="V_cell",
            expression="V = V_rev + η_act + η_ohm + η_conc",
            values={
                "V_rev": V_rev,
                "eta_act": eta_act,
                "eta_ohm": eta_ohm,
                "eta_conc": eta_conc,
            },
            result=V_cell,
        )
    )

    return PointResultV2(
        electrode=electrode.name,
        current_density=current_density,
        temperature=temperature,
        V_rev=V_rev,
        eta_act=eta_act,
        eta_ohm=eta_ohm,
        eta_conc=eta_conc,
        V_cell=V_cell,
        model_act=electrode.kinetic_model,
        j0_T=j0_t,
        r_total=r_total,
        j_lim=j_lim,
        steps=steps,
    )


def polarization_curve_v2(
    currents: Sequence[float],
    temperatures: Iterable[float],
    electrode: ElectrodeKineticsV2,
    config: SimulationConfigV2,
    constants: PhysicalConstants = CONSTANTS,
) -> List[PointResultV2]:
    """Genera curva de polarización para una lista de j y T para un electrodo."""

    results: List[PointResultV2] = []
    for T in temperatures:
        for j in currents:
            results.append(evaluate_point_v2(j, T, electrode, config, constants))
    return results


def run_simulation_v2(
    config: SimulationConfigV2,
    constants: PhysicalConstants = CONSTANTS,
) -> Dict[str, List[PointResultV2]]:
    """Ejecuta la simulación para electrodo A y (opcional) B."""

    j_values = [
        config.operating.j_min
        + i * (config.operating.j_max - config.operating.j_min) / max(config.operating.n_points - 1, 1)
        for i in range(config.operating.n_points)
    ]
    temps = config.operating.temperatures

    out: Dict[str, List[PointResultV2]] = {
        "A": polarization_curve_v2(j_values, temps, config.electrode_A, config, constants)
    }
    if config.electrode_B:
        out["B"] = polarization_curve_v2(j_values, temps, config.electrode_B, config, constants)
    return out
