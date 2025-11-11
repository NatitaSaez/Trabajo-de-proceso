"""Parametros de ejemplo y catalogos rapidos."""

from __future__ import annotations

from .models import (
    Catalyst,
    ElectrolyzerConfig,
    ElectrodeKinetics,
    IntermediateData,
    MassTransportModel,
    OhmicModel,
    OperatingConditions,
    ThermoModel,
)

# --- Condiciones y modelos por defecto --------------------------------------------------------

DEFAULT_CONDITIONS = OperatingConditions(
    temperature=353.15,  # 80  degC
    pressure_total=1.0,
    pressure_h2=1.0,
    pressure_o2=1.0,
    activity_h2o=1.0,
    pH=0.0,
)

DEFAULT_THERMO = ThermoModel()

KINETICS_ANODE = ElectrodeKinetics(
    i0_ref=1e-9,
    activation_energy=65_000.0,
    alpha=0.5,
    electrons=2,
    name="anodo",
)

KINETICS_CATHODE = ElectrodeKinetics(
    i0_ref=1e-3,
    activation_energy=35_000.0,
    alpha=0.5,
    electrons=2,
    name="catodo",
)

OHMIC_MODEL = OhmicModel(
    conductivity_ref=0.1,
    activation_energy=15_000.0,
    membrane_thickness_cm=0.005,  # 50 um
    contact_resistance=0.02,
    electrolyte_resistance=0.05,
)

MASS_TRANSPORT = MassTransportModel(
    limit_current_ref=5.0,
    activation_energy=12_000.0,
)

DEFAULT_CONFIG = ElectrolyzerConfig(
    thermo=DEFAULT_THERMO,
    kinetics_anode=KINETICS_ANODE,
    kinetics_cathode=KINETICS_CATHODE,
    ohmic=OHMIC_MODEL,
    mass_transport=MASS_TRANSPORT,
    conditions=DEFAULT_CONDITIONS,
)

# --- Catalogo de catalizadores (Tabla 2 del informe) -----------------------------------------

_PT_INTERMEDIATES = {
    "O*": IntermediateData(delta_e=1.57, delta_zpe=0.05, delta_s=1.34e-4, electrons=0, protons=0),
    "OH*": IntermediateData(delta_e=1.05, delta_zpe=0.35, delta_s=2.0e-3, electrons=1, protons=1),
}

CATALYSTS = {
    "Pt": Catalyst(
        name="Pt",
        d_e_o=1.57,
        d_e_oh=1.05,
        delta_g1_u0=0.45,
        delta_g2_u0=0.43,
        dissociation_barrier=0.0,
        intermediates=_PT_INTERMEDIATES,
    ),
    "Pd": Catalyst(
        name="Pd",
        d_e_o=1.53,
        d_e_oh=0.92,
        delta_g1_u0=0.36,
        delta_g2_u0=0.56,
        dissociation_barrier=0.15,
    ),
    "Au": Catalyst(
        name="Au",
        d_e_o=2.75,
        d_e_oh=1.49,
        delta_g1_u0=-0.29,
        delta_g2_u0=-0.01,
        dissociation_barrier=2.06,
    ),
    "Ni": Catalyst(
        name="Ni",
        d_e_o=0.34,
        d_e_oh=0.13,
        delta_g1_u0=0.76,
        delta_g2_u0=1.35,
        dissociation_barrier=0.40,
    ),
    "Ir": Catalyst(
        name="Ir",
        d_e_o=1.0,
        d_e_oh=0.63,
        delta_g1_u0=0.60,
        delta_g2_u0=0.85,
        dissociation_barrier=0.20,
    ),
    "Rh": Catalyst(
        name="Rh",
        d_e_o=0.44,
        d_e_oh=0.34,
        delta_g1_u0=0.87,
        delta_g2_u0=1.14,
        dissociation_barrier=0.50,
    ),
}

