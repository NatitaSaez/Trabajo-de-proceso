"""Funciones para evaluar el modelo DFT de los intermedios O*/OH*."""

from __future__ import annotations

import math
from typing import Dict

from .constants import CONSTANTS, PhysicalConstants
from .models import Catalyst

WATER_REFERENCE_ENERGY = 2.46  # eV, calibrado con Pt @ U0
ASSOCIATIVE_DEFAULT_SLOPE = 0.65  # eV/eV
ASSOCIATIVE_DEFAULT_INTERCEPT = 0.25  # eV
ASSOCIATIVE_OPTIMAL_BINDING = 1.6  # eV


def _thermal_energy_ev(
    temperature: float, constants: PhysicalConstants = CONSTANTS
) -> float:
    return constants.boltzmann * temperature * constants.joule_to_ev


def calcular_energia_libre(
    catalyst: Catalyst,
    intermediate: str,
    potential: float,
    pH: float,
    temperature: float,
    constants: PhysicalConstants = CONSTANTS,
) -> float:
    """Aplica los 6 pasos descritos en la seccion 2.2 del informe."""

    if intermediate not in catalyst.intermediates:
        raise KeyError(f"No hay datos para el intermedio {intermediate} en {catalyst.name}.")

    data = catalyst.intermediates[intermediate]
    delta_g = data.delta_e + data.delta_zpe - temperature * data.delta_s
    delta_g += data.electrons * potential  # efecto del potencial (e*U)
    delta_g += data.protons * _thermal_energy_ev(temperature, constants) * math.log(10) * pH
    return delta_g


def _scale_barrier(
    barrier_at_u0: float, potential: float, reference_potential: float = 1.23
) -> float:
    """Ajusta barreras linealmente con el potencial (1 e- por paso)."""

    return barrier_at_u0 + (potential - reference_potential)


def evaluar_mecanismo_disociativo(
    catalyst: Catalyst,
    potential: float,
    temperature: float,
    pH: float,
    reference_potential: float = 1.23,
    constants: PhysicalConstants = CONSTANTS,
) -> Dict[str, float]:
    """Calcula DeltaG1 y DeltaG2 para la via disociativa."""

    if catalyst.intermediates:
        g_o = calcular_energia_libre(catalyst, "O*", potential, pH, temperature, constants)
        g_oh = calcular_energia_libre(catalyst, "OH*", potential, pH, temperature, constants)
        delta_g1 = g_oh - g_o
        delta_g2 = WATER_REFERENCE_ENERGY - g_oh
    else:
        delta_g1 = _scale_barrier(catalyst.delta_g1_u0, potential, reference_potential)
        delta_g2 = _scale_barrier(catalyst.delta_g2_u0, potential, reference_potential)

    limiting = max(delta_g1, delta_g2)
    return {"delta_g1": delta_g1, "delta_g2": delta_g2, "limiting": limiting}


def evaluar_mecanismo_asociativo(
    catalyst: Catalyst,
    potential: float,
    reference_potential: float = 1.23,
) -> Dict[str, float]:
    """Modelo lineal para la via asociativa (Figura 8)."""

    slope = (
        catalyst.associative_linear_coeff
        if catalyst.associative_linear_coeff is not None
        else ASSOCIATIVE_DEFAULT_SLOPE
    )
    intercept = (
        catalyst.associative_intercept
        if catalyst.associative_intercept is not None
        else ASSOCIATIVE_DEFAULT_INTERCEPT
    )
    delta_binding = abs(catalyst.d_e_o - ASSOCIATIVE_OPTIMAL_BINDING)
    barrier = intercept + slope * delta_binding + (potential - reference_potential)
    return {"barrier": barrier}


def determinar_via_dominante(
    catalyst: Catalyst,
    potential: float,
    temperature: float,
    pH: float,
) -> Dict[str, float | str]:
    """Compara las barreras de disociacion, via disociativa y asociativa."""

    dis = evaluar_mecanismo_disociativo(catalyst, potential, temperature, pH)
    assoc = evaluar_mecanismo_asociativo(catalyst, potential)

    candidates = {
        "mecanismo disociativo": dis["limiting"],
        "mecanismo asociativo": assoc["barrier"],
        "disociacion O2": catalyst.dissociation_barrier,
    }
    dominant = min(candidates.items(), key=lambda item: item[1])
    return {
        "via_dominante": dominant[0],
        "barrera": dominant[1],
        "detalle_disociativo": dis,
        "detalle_asociativo": assoc,
    }


def calcular_actividad(
    catalyst: Catalyst,
    potential: float,
    temperature: float,
    pH: float,
    constants: PhysicalConstants = CONSTANTS,
) -> float:
    """Implementa la medida A proporcional a exp(-DeltaG*/kT)."""

    decision = determinar_via_dominante(catalyst, potential, temperature, pH)
    barrier = decision["barrera"]
    kT = _thermal_energy_ev(temperature, constants)
    if kT <= 0:
        raise ValueError("Temperatura invalida.")
    return math.exp(-barrier / kT)

