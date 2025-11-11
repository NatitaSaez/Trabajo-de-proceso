"""Interfaces de alto nivel para el simulador."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence

from . import electrochemistry, orr
from .constants import CONSTANTS, PhysicalConstants
from .models import Catalyst, ElectrolyzerConfig


@dataclass
class ElectrolyzerSimulator:
    """Calcula voltajes de celda y desgloses de sobrepotenciales."""

    config: ElectrolyzerConfig
    constants: PhysicalConstants = CONSTANTS

    def voltage(self, current_density: float) -> float:
        return electrochemistry.cell_voltage(current_density, self.config, self.constants)

    def voltage_breakdown(self, current_density: float) -> Dict[str, float]:
        conds = self.config.conditions
        V_ideal = electrochemistry.nernst_potential(conds, self.config.thermo, self.constants)
        eta_act = electrochemistry.activation_overpotential(
            current_density,
            self.config.kinetics_anode,
            self.config.kinetics_cathode,
            conds.temperature,
            self.constants,
        )
        eta_ohm = electrochemistry.ohmic_overpotential(
            current_density, self.config.ohmic, conds.temperature, self.constants
        )
        eta_conc = electrochemistry.concentration_overpotential(
            current_density,
            self.config.mass_transport,
            conds.temperature,
            self.config.thermo.electrons,
            self.constants,
        )
        return {
            "V_ideal": V_ideal,
            "eta_activacion": eta_act,
            "eta_ohmico": eta_ohm,
            "eta_concentracion": eta_conc,
            "V_total": V_ideal + eta_act + eta_ohm + eta_conc,
        }

    def polarization_curve(self, currents: Sequence[float]) -> List[float]:
        return electrochemistry.polarization_curve(currents, self.config, self.constants)


@dataclass
class CatalystAnalyzer:
    """Envuelve las utilidades de energia libre y actividad."""

    catalyst: Catalyst
    temperature: float = 298.15
    pH: float = 0.0
    constants: PhysicalConstants = CONSTANTS

    def free_energy(self, potential: float, intermediate: str) -> float:
        return orr.calcular_energia_libre(
            self.catalyst, intermediate, potential, self.pH, self.temperature, self.constants
        )

    def limiting_barriers(self, potential: float) -> Dict[str, float | str]:
        return orr.determinar_via_dominante(
            self.catalyst, potential, self.temperature, self.pH
        )

    def activity(self, potential: float) -> float:
        return orr.calcular_actividad(
            self.catalyst, potential, self.temperature, self.pH, self.constants
        )

    def activity_profile(self, potentials: Iterable[float]) -> List[float]:
        return [self.activity(U) for U in potentials]

