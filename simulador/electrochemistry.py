"""Calculos electroquimicos para la celda H."""

from __future__ import annotations

import math
from typing import Iterable, List, Sequence

from .constants import CONSTANTS, PhysicalConstants
from .models import (
    ElectrolyzerConfig,
    ElectrodeKinetics,
    MassTransportModel,
    OhmicModel,
    OperatingConditions,
    ThermoModel,
)


def arrhenius(
    value_ref: float,
    activation_energy: float | None,
    temperature: float,
    reference_temperature: float,
    constants: PhysicalConstants = CONSTANTS,
) -> float:
    """Aplica la relacion de Arrhenius."""

    if activation_energy is None:
        return value_ref
    factor = -activation_energy / constants.gas_constant
    exponent = factor * (1.0 / temperature - 1.0 / reference_temperature)
    return value_ref * math.exp(exponent)


def nernst_potential(
    conditions: OperatingConditions,
    thermo: ThermoModel,
    constants: PhysicalConstants = CONSTANTS,
) -> float:
    """Calcula el voltaje ideal (Nernst) descrito en la seccion 1.1."""

    V_std = thermo.standard_potential(conditions.temperature, constants=constants)
    quotient = (
        conditions.pressure_h2
        * math.sqrt(max(conditions.pressure_o2, 1e-12))
        / max(conditions.activity_h2o, 1e-12)
    )
    nernst_term = (
        constants.gas_constant
        * conditions.temperature
        / (thermo.electrons * constants.faraday)
        * math.log(quotient)
    )
    return V_std + nernst_term


def _activation_eta(
    current_density: float,
    kinetics: ElectrodeKinetics,
    temperature: float,
    constants: PhysicalConstants,
) -> float:
    if current_density <= 0.0:
        raise ValueError("La densidad de corriente debe ser positiva para perdidas de activacion.")

    i0 = arrhenius(
        kinetics.i0_ref,
        kinetics.activation_energy,
        temperature,
        kinetics.reference_temperature,
        constants,
    )
    if i0 <= 0.0:
        raise ValueError(f"i0 invalido ({i0}) para {kinetics.name}.")

    prefactor = (
        constants.gas_constant
        * temperature
        / (kinetics.alpha * kinetics.electrons * constants.faraday)
    )
    return prefactor * math.log(current_density / i0)


def activation_overpotential(
    current_density: float,
    kinetics_anode: ElectrodeKinetics,
    kinetics_cathode: ElectrodeKinetics,
    temperature: float,
    constants: PhysicalConstants = CONSTANTS,
) -> float:
    """Sobrepotencial de activacion total."""

    eta_an = _activation_eta(current_density, kinetics_anode, temperature, constants)
    eta_cat = _activation_eta(current_density, kinetics_cathode, temperature, constants)
    return eta_an + eta_cat


def ohmic_overpotential(
    current_density: float,
    ohmic: OhmicModel,
    temperature: float,
    constants: PhysicalConstants = CONSTANTS,
) -> float:
    """Perdidas ohmicas (ley de Ohm)."""

    conductivity = arrhenius(
        ohmic.conductivity_ref,
        ohmic.activation_energy,
        temperature,
        ohmic.reference_temperature,
        constants,
    )
    if conductivity <= 0:
        raise ValueError("La conductividad debe ser positiva.")

    membrane_resistance = ohmic.membrane_thickness_cm / conductivity
    total_resistance = (
        membrane_resistance + ohmic.contact_resistance + ohmic.electrolyte_resistance
    )
    return current_density * total_resistance


def concentration_overpotential(
    current_density: float,
    mass_transport: MassTransportModel,
    temperature: float,
    electrons: int = 2,
    constants: PhysicalConstants = CONSTANTS,
) -> float:
    """Sobrepotencial por transporte de masa."""

    i_lim = arrhenius(
        mass_transport.limit_current_ref,
        mass_transport.activation_energy,
        temperature,
        mass_transport.reference_temperature,
        constants,
    )
    if current_density >= i_lim:
        raise ValueError("La densidad de corriente supera la corriente limite.")

    term = (
        constants.gas_constant
        * temperature
        / (electrons * constants.faraday)
        * math.log(i_lim / (i_lim - current_density))
    )
    return term


def cell_voltage(
    current_density: float,
    config: ElectrolyzerConfig,
    constants: PhysicalConstants = CONSTANTS,
) -> float:
    """Voltaje total de la celda."""

    V_ideal = nernst_potential(config.conditions, config.thermo, constants)
    eta_act = activation_overpotential(
        current_density,
        config.kinetics_anode,
        config.kinetics_cathode,
        config.conditions.temperature,
        constants,
    )
    eta_ohm = ohmic_overpotential(
        current_density,
        config.ohmic,
        config.conditions.temperature,
        constants,
    )
    eta_conc = concentration_overpotential(
        current_density,
        config.mass_transport,
        config.conditions.temperature,
        config.thermo.electrons,
        constants,
    )
    return V_ideal + eta_act + eta_ohm + eta_conc


def polarization_curve(
    currents: Sequence[float],
    config: ElectrolyzerConfig,
    constants: PhysicalConstants = CONSTANTS,
) -> List[float]:
    """Calcula la curva de polarizacion (U vs i)."""

    return [cell_voltage(i, config, constants) for i in currents]

