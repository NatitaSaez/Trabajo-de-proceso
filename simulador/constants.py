"""Constantes fisicas utilizadas en el simulador."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PhysicalConstants:
    """Coleccion de constantes fisicas basicas.

    Todas las magnitudes estan en unidades SI. Se agregan factores de conversion
    para trabajar en eV cuando se evaluan energias DFT.
    """

    faraday: float = 96485.33212  # C/mol
    gas_constant: float = 8.314462618  # J/(mol.K)
    boltzmann: float = 1.380649e-23  # J/K
    electron_charge: float = 1.602176634e-19  # C
    planck: float = 6.62607015e-34  # J.s

    @property
    def ev_to_joule(self) -> float:
        return self.electron_charge

    @property
    def joule_to_ev(self) -> float:
        return 1.0 / self.electron_charge


CONSTANTS = PhysicalConstants()
