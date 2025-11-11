"""Simulacion detallada con trazabilidad de ecuaciones por punto."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List

from .constants import CONSTANTS, PhysicalConstants
from .electrochemistry import arrhenius
from .models import ElectrolyzerConfig, ElectrodeKinetics


@dataclass
class EquationStep:
    """Representa una ecuacion y los valores utilizados en un paso."""

    name: str
    expression: str
    values: Dict[str, float]
    result: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "name": self.name,
            "expression": self.expression,
            "values": self.values,
            "result": self.result,
        }


@dataclass
class PointDetail:
    """Detalle completo de un punto de la curva."""

    current_density: float
    voltage: float
    contributions: Dict[str, float]
    steps: List[EquationStep]

    def table_row(self) -> Dict[str, float]:
        row = {
            "current": self.current_density,
            "voltage": self.voltage,
        }
        row.update(self.contributions)
        return row

    def to_dict(self) -> Dict:
        return {
            "current_density": self.current_density,
            "voltage": self.voltage,
            "contributions": self.contributions,
            "steps": [step.to_dict() for step in self.steps],
        }


def _exchange_current_detail(
    kinetics: ElectrodeKinetics,
    temperature: float,
    constants: PhysicalConstants,
) -> EquationStep:
    if kinetics.activation_energy is None:
        value = kinetics.i0_ref
        expression = "i0 = i0_ref"
        values = {"i0_ref": kinetics.i0_ref}
    else:
        exponent = (-kinetics.activation_energy / constants.gas_constant) * (
            1.0 / temperature - 1.0 / kinetics.reference_temperature
        )
        value = kinetics.i0_ref * math.exp(exponent)
        expression = "i0 = i0_ref * exp(-Ea/R * (1/T - 1/Tref))"
        values = {
            "i0_ref": kinetics.i0_ref,
            "Ea": kinetics.activation_energy,
            "R": constants.gas_constant,
            "T": temperature,
            "Tref": kinetics.reference_temperature,
            "exponent": exponent,
        }
    return EquationStep(
        name=f"Corriente de intercambio {kinetics.name}",
        expression=expression,
        values=values,
        result=value,
    )


def _activation_step(
    current_density: float,
    kinetics: ElectrodeKinetics,
    temperature: float,
    constants: PhysicalConstants,
) -> List[EquationStep]:
    steps = []
    i0_step = _exchange_current_detail(kinetics, temperature, constants)
    steps.append(i0_step)
    i0 = i0_step.result
    if i0 <= 0:
        raise ValueError("La corriente de intercambio debe ser positiva.")
    prefactor = (
        constants.gas_constant
        * temperature
        / (kinetics.alpha * kinetics.electrons * constants.faraday)
    )
    eta = prefactor * math.log(current_density / i0)
    steps.append(
        EquationStep(
            name=f"Sobrepotencial activacion {kinetics.name}",
            expression="eta = (RT/(alpha*nF)) * ln(i/i0)",
            values={
                "R": constants.gas_constant,
                "T": temperature,
                "alpha": kinetics.alpha,
                "n": kinetics.electrons,
                "F": constants.faraday,
                "i": current_density,
                "i0": i0,
                "prefactor": prefactor,
            },
            result=eta,
        )
    )
    return steps


def evaluate_point(
    current_density: float,
    config: ElectrolyzerConfig,
    constants: PhysicalConstants = CONSTANTS,
) -> PointDetail:
    """Calcula un punto con trazabilidad completa."""

    if current_density <= 0:
        raise ValueError("La densidad de corriente debe ser positiva.")

    steps: List[EquationStep] = []
    conds = config.conditions
    thermo = config.thermo
    temperature = conds.temperature
    n = thermo.electrons
    R = constants.gas_constant
    F = constants.faraday

    V_std = thermo.standard_potential(temperature, constants)
    quotient = (
        conds.pressure_h2 * math.sqrt(max(conds.pressure_o2, 1e-12)) / max(conds.activity_h2o, 1e-12)
    )
    nernst_prefactor = R * temperature / (n * F)
    nernst_term = nernst_prefactor * math.log(quotient)
    V_ideal = V_std + nernst_term
    steps.append(
        EquationStep(
            name="Voltaje ideal",
            expression="V = Vstd + (RT/(nF)) * ln(Q)",
            values={
                "Vstd": V_std,
                "R": R,
                "T": temperature,
                "n": n,
                "F": F,
                "Q": quotient,
                "ln(Q)": math.log(quotient),
                "prefactor": nernst_prefactor,
            },
            result=V_ideal,
        )
    )

    activation_steps_anode = _activation_step(
        current_density, config.kinetics_anode, temperature, constants
    )
    activation_steps_cathode = _activation_step(
        current_density, config.kinetics_cathode, temperature, constants
    )
    steps.extend(activation_steps_anode)
    steps.extend(activation_steps_cathode)
    eta_act_an = activation_steps_anode[-1].result
    eta_act_cat = activation_steps_cathode[-1].result
    eta_act_total = eta_act_an + eta_act_cat
    steps.append(
        EquationStep(
            name="Sobrepotencial activacion total",
            expression="eta_act = eta_an + eta_cat",
            values={"eta_an": eta_act_an, "eta_cat": eta_act_cat},
            result=eta_act_total,
        )
    )

    conductivity = arrhenius(
        config.ohmic.conductivity_ref,
        config.ohmic.activation_energy,
        temperature,
        config.ohmic.reference_temperature,
        constants,
    )
    if conductivity <= 0:
        raise ValueError("La conductividad debe ser positiva.")
    r_membrane = config.ohmic.membrane_thickness_cm / conductivity
    r_total = r_membrane + config.ohmic.contact_resistance + config.ohmic.electrolyte_resistance
    eta_ohm = current_density * r_total
    steps.append(
        EquationStep(
            name="Perdida ohmica",
            expression="eta_ohm = i * (t_mem/kappa + R_contact + R_electrolito)",
            values={
                "i": current_density,
                "t_mem": config.ohmic.membrane_thickness_cm,
                "kappa": conductivity,
                "R_contact": config.ohmic.contact_resistance,
                "R_electrolito": config.ohmic.electrolyte_resistance,
                "R_total": r_total,
            },
            result=eta_ohm,
        )
    )

    i_lim = arrhenius(
        config.mass_transport.limit_current_ref,
        config.mass_transport.activation_energy,
        temperature,
        config.mass_transport.reference_temperature,
        constants,
    )
    if current_density >= i_lim:
        raise ValueError("La densidad de corriente supera la corriente limite.")
    conc_prefactor = R * temperature / (n * F)
    eta_conc = conc_prefactor * math.log(i_lim / (i_lim - current_density))
    steps.append(
        EquationStep(
            name="Perdida por concentracion",
            expression="eta_conc = (RT/(nF)) * ln(i_lim / (i_lim - i))",
            values={
                "R": R,
                "T": temperature,
                "n": n,
                "F": F,
                "i_lim": i_lim,
                "i": current_density,
                "prefactor": conc_prefactor,
            },
            result=eta_conc,
        )
    )

    total_voltage = V_ideal + eta_act_total + eta_ohm + eta_conc
    steps.append(
        EquationStep(
            name="Voltaje total",
            expression="V_total = V + eta_act + eta_ohm + eta_conc",
            values={
                "V": V_ideal,
                "eta_act": eta_act_total,
                "eta_ohm": eta_ohm,
                "eta_conc": eta_conc,
            },
            result=total_voltage,
        )
    )

    contributions = {
        "V_ideal": V_ideal,
        "eta_act_an": eta_act_an,
        "eta_act_cat": eta_act_cat,
        "eta_act_total": eta_act_total,
        "eta_ohm": eta_ohm,
        "eta_conc": eta_conc,
    }
    return PointDetail(
        current_density=current_density,
        voltage=total_voltage,
        contributions=contributions,
        steps=steps,
    )


def detailed_curve(
    currents: List[float],
    config: ElectrolyzerConfig,
    constants: PhysicalConstants = CONSTANTS,
) -> List[PointDetail]:
    """Evalua una lista de corrientes y regresa el detalle completo."""

    return [evaluate_point(i, config, constants) for i in currents]
