"""Dataclasses para describir el estado y parametros del simulador."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from .constants import CONSTANTS, PhysicalConstants


@dataclass
class OperatingConditions:
    """Condiciones termodinamicas y quimicas de la celda."""

    temperature: float  # K
    pressure_total: float = 1.0  # bar
    pressure_h2: float = 1.0  # bar
    pressure_o2: float = 1.0  # bar
    activity_h2o: float = 1.0
    pH: float = 0.0


@dataclass
class ThermoModel:
    """Modelo termodinamico para el potencial reversible."""

    delta_h_ref: float = 285_830.0  # J/mol
    delta_s_ref: float = 163.0  # J/(mol.K)
    reference_temperature: float = 298.15  # K
    reference_potential: float = 1.23  # V @ 298 K
    electrons: int = 2

    def standard_potential(
        self,
        temperature: float,
        constants: PhysicalConstants = CONSTANTS,
    ) -> float:
        """Calcula V deg(T) = -DeltaG deg(T)/(nF)."""

        delta_g = self.delta_h_ref - temperature * self.delta_s_ref
        return delta_g / (self.electrons * constants.faraday)


@dataclass
class ElectrodeKinetics:
    """Parametros cineticos (Tafel/Arrhenius) para cada electrodo."""

    i0_ref: float  # A/cm2
    activation_energy: Optional[float]  # J/mol
    alpha: float
    electrons: int = 2
    reference_temperature: float = 298.15  # K
    name: str = "electrode"


@dataclass
class OhmicModel:
    """Modelo simplificado de perdidas ohmicas."""

    conductivity_ref: float  # S/cm
    activation_energy: Optional[float]  # J/mol
    membrane_thickness_cm: float  # cm
    contact_resistance: float  # Ohm.cm2
    electrolyte_resistance: float  # Ohm.cm2
    reference_temperature: float = 298.15  # K


@dataclass
class MassTransportModel:
    """Parametros asociados a la corriente limite."""

    limit_current_ref: float  # A/cm2
    activation_energy: Optional[float]  # J/mol
    reference_temperature: float = 298.15  # K


@dataclass
class IntermediateData:
    """Datos DFT por intermedio."""

    delta_e: float  # eV
    delta_zpe: float = 0.0  # eV
    delta_s: float = 0.0  # eV/K
    electrons: int = 0
    protons: int = 0


@dataclass
class Catalyst:
    """Parametros que describen un catalizador metalico."""

    name: str
    d_e_o: float  # eV
    d_e_oh: float  # eV
    delta_g1_u0: float  # eV @ U0
    delta_g2_u0: float  # eV @ U0
    dissociation_barrier: float  # eV
    intermediates: Dict[str, IntermediateData] = field(default_factory=dict)
    associative_linear_coeff: Optional[float] = None
    associative_intercept: Optional[float] = None


@dataclass
class ElectrolyzerConfig:
    """Agrupa todos los submodelos necesarios para simular la celda."""

    thermo: ThermoModel
    kinetics_anode: ElectrodeKinetics
    kinetics_cathode: ElectrodeKinetics
    ohmic: OhmicModel
    mass_transport: MassTransportModel
    conditions: OperatingConditions

