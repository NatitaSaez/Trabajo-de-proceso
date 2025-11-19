"""Carga y validación de configuración v2 (YAML) para el simulador 0D."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

import yaml


def _as_list(value: Any) -> List[float]:
    if value is None:
        return []
    if isinstance(value, (int, float)):
        return [float(value)]
    if isinstance(value, (list, tuple)):
        return [float(v) for v in value]
    raise TypeError(f"No se puede interpretar {value!r} como lista numérica.")


def _maybe_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _normalize_kinetic_model(value: Any) -> str:
    """Normaliza la etiqueta del modelo cinético para aceptar alias (underscore, BV, etc.)."""

    if value is None:
        return "tafel"
    normalized = str(value).strip().lower()
    normalized = normalized.replace("_", "-").replace(" ", "-")
    if normalized in {"butler-volmer", "butler", "volmer", "b-v", "bv"}:
        return "butler-volmer"
    return normalized


@dataclass
class OperatingGrid:
    """Rangos de operación para los barridos de j y T."""

    temperatures: List[float]
    j_min: float
    j_max: float
    n_points: int
    use_concentration_losses: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "OperatingGrid":
        temps = _as_list(data.get("T_list")) or _as_list(data.get("T"))
        if not temps:
            raise ValueError("Debes especificar al menos una temperatura en operating_conditions.T_list")
        return cls(
            temperatures=temps,
            j_min=float(data["j_min"]),
            j_max=float(data["j_max"]),
            n_points=int(data.get("n_points", 50)),
            use_concentration_losses=bool(data.get("use_concentration_losses", False)),
        )


@dataclass
class ThermoSettings:
    """Parámetros termodinámicos para V_rev."""

    V_ref: float = 1.23
    delta_h_ref: Optional[float] = None
    delta_s_ref: Optional[float] = None
    T_ref: float = 298.15
    electrons: int = 2
    use_nernst: bool = False
    pressure_h2: float = 1.0
    pressure_o2: float = 1.0
    activity_h2o: float = 1.0

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ThermoSettings":
        return cls(
            V_ref=float(data.get("V_ref", 1.23)),
            delta_h_ref=data.get("delta_h_ref"),
            delta_s_ref=data.get("delta_s_ref"),
            T_ref=float(data.get("T_ref", 298.15)),
            electrons=int(data.get("n", data.get("electrons", 2))),
            use_nernst=bool(data.get("use_nernst", False)),
            pressure_h2=float(data.get("p_h2", data.get("pressure_h2", 1.0))),
            pressure_o2=float(data.get("p_o2", data.get("pressure_o2", 1.0))),
            activity_h2o=float(data.get("activity_h2o", 1.0)),
        )


@dataclass
class ElectrodeKineticsV2:
    """Definición cinética por electrodo (Tafel/BV)."""

    name: str
    kinetic_model: str = "tafel"
    n: int = 2
    alpha: Optional[float] = 0.5  # usado en Tafel o simétrico BV
    alpha_a: Optional[float] = None
    alpha_c: Optional[float] = None
    j0_ref: float = 1e-3
    Ea: Optional[float] = None
    T_ref: float = 298.15

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ElectrodeKineticsV2":
        return cls(
            name=str(data.get("name", "electrode")),
            kinetic_model=_normalize_kinetic_model(data.get("kinetic_model", "tafel")),
            n=int(data.get("n", 2)),
            alpha=_maybe_float(data.get("alpha", 0.5)),
            alpha_a=_maybe_float(data.get("alpha_a")),
            alpha_c=_maybe_float(data.get("alpha_c")),
            j0_ref=float(data.get("j0_ref", 1e-3)),
            Ea=_maybe_float(data.get("Ea")),
            T_ref=float(data.get("T_ref", 298.15)),
        )

    def validate(self) -> None:
        if self.kinetic_model not in {"tafel", "butler-volmer", "bv"}:
            raise ValueError(f"Kinetic model inválido: {self.kinetic_model}")
        if self.kinetic_model in {"butler-volmer", "bv"}:
            if self.alpha_a is None or self.alpha_c is None:
                raise ValueError(
                    f"Debes especificar alpha_a y alpha_c para Butler-Volmer en {self.name}"
                )


@dataclass
class OhmicLayer:
    """Una capa resistiva (membrana, electrolito, separador)."""

    name: str
    delta: float  # cm
    kappa_ref: float  # S/cm
    Ea_kappa: Optional[float] = None  # J/mol
    T_ref: float = 298.15

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "OhmicLayer":
        return cls(
            name=str(data.get("name", "layer")),
            delta=float(data["delta"]),
            kappa_ref=float(data["kappa_ref"]),
            Ea_kappa=data.get("Ea_kappa"),
            T_ref=float(data.get("T_ref", 298.15)),
        )


@dataclass
class OhmicConfig:
    """Colección de capas + resistencia extra (contactos)."""

    layers: List[OhmicLayer] = field(default_factory=list)
    extra_resistance: float = 0.0  # Ohm.cm2 para contactos, colectores, etc.

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "OhmicConfig":
        layers_data = data.get("components") or data.get("layers") or []
        layers = [OhmicLayer.from_dict(item) for item in layers_data]
        return cls(layers=layers, extra_resistance=float(data.get("extra_resistance", 0.0)))


@dataclass
class MassTransferConfig:
    """Parámetros para pérdidas por concentración."""

    enabled: bool = False
    j_lim: Optional[float] = None  # A/cm2 (directo)
    Ea_jlim: Optional[float] = None
    D_eff: Optional[float] = None  # cm2/s
    C_bulk: Optional[float] = None  # mol/cm3
    delta_dif: Optional[float] = None  # cm
    T_ref: float = 298.15

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MassTransferConfig":
        return cls(
            enabled=bool(data.get("enabled", False)),
            j_lim=_maybe_float(data.get("j_lim")),
            Ea_jlim=_maybe_float(data.get("Ea_jlim")),
            D_eff=_maybe_float(data.get("D_eff")),
            C_bulk=_maybe_float(data.get("C_bulk")),
            delta_dif=_maybe_float(data.get("delta_dif")),
            T_ref=float(data.get("T_ref", 298.15)),
        )


@dataclass
class SimulationConfigV2:
    """Config completa leída desde YAML."""

    project_name: str
    operating: OperatingGrid
    thermo: ThermoSettings
    electrode_A: ElectrodeKineticsV2
    electrode_B: Optional[ElectrodeKineticsV2] = None
    ohmic: OhmicConfig = field(default_factory=OhmicConfig)
    mass_transfer: MassTransferConfig = field(default_factory=MassTransferConfig)
    units: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SimulationConfigV2":
        op = OperatingGrid.from_dict(data["operating_conditions"])
        thermo = ThermoSettings.from_dict(data.get("thermo", {}))
        electrode_A = ElectrodeKineticsV2.from_dict(data["electrode_A"])
        electrode_A.validate()
        electrode_B = None
        if "electrode_B" in data and data["electrode_B"]:
            electrode_B = ElectrodeKineticsV2.from_dict(data["electrode_B"])
            electrode_B.validate()
        return cls(
            project_name=str(data.get("project_name", "pem_h_cell")),
            operating=op,
            thermo=thermo,
            electrode_A=electrode_A,
            electrode_B=electrode_B,
            ohmic=OhmicConfig.from_dict(data.get("ohmic", {})),
            mass_transfer=MassTransferConfig.from_dict(data.get("mass_transfer", {})),
            units=data.get("units", {}),
        )


def load_config(path: str | Path) -> SimulationConfigV2:
    """Lee un archivo YAML y devuelve la configuración v2 validada."""

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict):
        raise ValueError("El YAML debe definir un objeto de configuración en la raíz.")
    return SimulationConfigV2.from_dict(raw)
