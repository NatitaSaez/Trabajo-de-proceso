"""Aplicación Dash v2 para el simulador 0D (celda H)."""

from __future__ import annotations

import base64
import io
import json
import pathlib
import sys
from typing import Dict, List, Tuple

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Dash, Input, Output, State, dash_table, dcc, html

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulador.config_v2 import (  # noqa: E402
    ElectrodeKineticsV2,
    MassTransferConfig,
    OhmicConfig,
    OhmicLayer,
    OperatingGrid,
    SimulationConfigV2,
    ThermoSettings,
    load_config,
)
from simulador.simulation_v2 import PointResultV2, run_simulation_v2  # noqa: E402


# --- Utilidades -------------------------------------------------------------------------------

def parse_temperatures(text: str) -> List[float]:
    parts = [p.strip() for p in text.split(",") if p.strip()]
    temps: List[float] = []
    for p in parts:
        try:
            temps.append(float(p))
        except ValueError:
            raise ValueError(f"No se pudo interpretar la temperatura '{p}'")
    if not temps:
        raise ValueError("Debes ingresar al menos una temperatura separada por comas, ej: 298, 333")
    return temps


def _build_config_from_inputs(values: Dict) -> SimulationConfigV2:
    op = OperatingGrid(
        temperatures=parse_temperatures(values["temps"]),
        j_min=float(values["j_min"]),
        j_max=float(values["j_max"]),
        n_points=int(values["n_points"]),
        use_concentration_losses=values["use_conc"],
    )
    thermo = ThermoSettings(
        V_ref=float(values["V_ref"]),
        delta_s_ref=float(values["delta_s_ref"]),
        T_ref=float(values["T_ref"]),
        electrons=int(values["n_e"]),
        use_nernst=bool(values["use_nernst"]),
        pressure_h2=float(values["p_h2"]),
        pressure_o2=float(values["p_o2"]),
        activity_h2o=float(values["a_h2o"]),
    )
    electrode_a = ElectrodeKineticsV2(
        name=values["name_a"],
        kinetic_model=values["model_a"],
        n=int(values["n_e"]),
        alpha=float(values["alpha_a"]) if values["alpha_a"] is not None else None,
        alpha_a=float(values["alpha_a_a"]) if values["alpha_a_a"] is not None else None,
        alpha_c=float(values["alpha_c_a"]) if values["alpha_c_a"] is not None else None,
        j0_ref=float(values["j0_a"]),
        Ea=float(values["Ea_a"]) if values["Ea_a"] is not None else None,
        T_ref=float(values["T_ref"]),
    )
    electrode_a.validate()

    electrode_b = None
    if values["enable_b"]:
        electrode_b = ElectrodeKineticsV2(
            name=values["name_b"],
            kinetic_model=values["model_b"],
            n=int(values["n_e"]),
            alpha=float(values["alpha_b"]) if values["alpha_b"] is not None else None,
            alpha_a=float(values["alpha_a_b"]) if values["alpha_a_b"] is not None else None,
            alpha_c=float(values["alpha_c_b"]) if values["alpha_c_b"] is not None else None,
            j0_ref=float(values["j0_b"]),
            Ea=float(values["Ea_b"]) if values["Ea_b"] is not None else None,
            T_ref=float(values["T_ref"]),
        )
        electrode_b.validate()

    layers = []
    for row in values["ohm_layers"]:
        try:
            layers.append(
                OhmicLayer(
                    name=row.get("name", "layer"),
                    delta=float(row.get("delta", 0.0)),
                    kappa_ref=float(row.get("kappa_ref", 0.0)),
                    Ea_kappa=float(row["Ea_kappa"]) if row.get("Ea_kappa") not in (None, "") else None,
                    T_ref=float(row.get("T_ref", values["T_ref"])),
                )
            )
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Capa ohmica inválida: {row}") from exc
    ohmic = OhmicConfig(layers=layers, extra_resistance=float(values["R_extra"]))

    mass = MassTransferConfig(
        enabled=bool(values["use_conc"]),
        j_lim=float(values["j_lim"]) if values["j_lim"] is not None else None,
        Ea_jlim=float(values["Ea_jlim"]) if values["Ea_jlim"] is not None else None,
        D_eff=float(values["D_eff"]) if values["D_eff"] is not None else None,
        C_bulk=float(values["C_bulk"]) if values["C_bulk"] is not None else None,
        delta_dif=float(values["delta_dif"]) if values["delta_dif"] is not None else None,
        T_ref=float(values["T_ref"]),
    )

    return SimulationConfigV2(
        project_name="celda_H_v2",
        operating=op,
        thermo=thermo,
        electrode_A=electrode_a,
        electrode_B=electrode_b,
        ohmic=ohmic,
        mass_transfer=mass,
    )


def _point_to_row(p: PointResultV2) -> Dict:
    return {
        "electrode": p.electrode,
        "T": p.temperature,
        "j": p.current_density,
        "V_cell": p.V_cell,
        "V_rev": p.V_rev,
        "eta_act": p.eta_act,
        "eta_ohm": p.eta_ohm,
        "eta_conc": p.eta_conc,
        "r_total": p.r_total,
        "model": p.model_act,
    }


DEFAULT_OHMIC_LAYERS = [
    {"name": "membrana", "delta": 0.005, "kappa_ref": 0.1, "Ea_kappa": 15000, "T_ref": 298.15},
    {"name": "electrolito", "delta": 0.01, "kappa_ref": 0.5, "Ea_kappa": 15000, "T_ref": 298.15},
]

# --- Defaults from config.yml -----------------------------------------------------------------

def _load_defaults():
    cfg_path = PROJECT_ROOT / "examples" / "config.yml"
    try:
        cfg = load_config(cfg_path)
    except Exception:
        return {}

    def _electrode_defaults(electrode: ElectrodeKineticsV2 | None, prefix: str) -> Dict[str, object]:
        if electrode is None:
            return {}
        return {
            f"name_{prefix}": electrode.name,
            f"model_{prefix}": electrode.kinetic_model,
            f"j0_{prefix}": electrode.j0_ref,
            f"Ea_{prefix}": electrode.Ea,
            f"alpha_{prefix}": electrode.alpha,
            f"alpha_a_{prefix}": electrode.alpha_a,
            f"alpha_c_{prefix}": electrode.alpha_c,
        }

    ohm_layers = [
        {"name": l.name, "delta": l.delta, "kappa_ref": l.kappa_ref, "Ea_kappa": l.Ea_kappa, "T_ref": l.T_ref}
        for l in cfg.ohmic.layers
    ] or DEFAULT_OHMIC_LAYERS

    temps_list = cfg.operating.temperatures
    temps_default = min(temps_list) if temps_list else ""

    return {
        # Si hay lista/rango de T en config, usar el menor valor como default en la UI.
        "temps": str(temps_default),
        "j_min": cfg.operating.j_min,
        "j_max": cfg.operating.j_max,
        "n_points": cfg.operating.n_points,
        "use_conc": cfg.operating.use_concentration_losses,
        "V_ref": cfg.thermo.V_ref,
        "delta_s_ref": cfg.thermo.delta_s_ref,
        "T_ref": cfg.thermo.T_ref,
        "n_e": cfg.thermo.electrons,
        "use_nernst": cfg.thermo.use_nernst,
        "p_h2": cfg.thermo.pressure_h2,
        "p_o2": cfg.thermo.pressure_o2,
        "a_h2o": cfg.thermo.activity_h2o,
        "R_extra": cfg.ohmic.extra_resistance,
        "ohm_layers": ohm_layers,
        "j_lim": cfg.mass_transfer.j_lim,
        "Ea_jlim": cfg.mass_transfer.Ea_jlim,
        "D_eff": cfg.mass_transfer.D_eff,
        "C_bulk": cfg.mass_transfer.C_bulk,
        "delta_dif": cfg.mass_transfer.delta_dif,
        **_electrode_defaults(cfg.electrode_A, "a"),
        **_electrode_defaults(cfg.electrode_B, "b"),
    }


DEFAULT_CFG_VALUES = _load_defaults()

def _d(key: str, fallback):
    return DEFAULT_CFG_VALUES.get(key, fallback)

COMMON_STYLES = [dbc.themes.FLATLY]
app: Dash = dash.Dash(
    __name__,
    title="Simulador Celda H - v2",
    external_stylesheets=COMMON_STYLES,
    suppress_callback_exceptions=True,
)


def build_number_input(id_, label, value, step, min_=None):
    return dbc.Col([dbc.Label(label), dbc.Input(id=id_, type="number", value=value, step=step, min=min_)], md=4)


# --- Layout -----------------------------------------------------------------------------------

operating_controls = dbc.Card(
    [
        dbc.CardHeader("Condiciones de operación"),
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label("Temperaturas (K, separadas por coma)"),
                                dbc.Input(id="temp-list", value=_d("temps", "298, 333"), type="text"),
                            ],
                            md=6,
                        ),
                        build_number_input("j-min", "j mín (A/cm²)", _d("j_min", 0.01), 0.01, 0),
                        build_number_input("j-max", "j máx (A/cm²)", _d("j_max", 1.0), 0.05, 0),
                        build_number_input("n-points", "Puntos", _d("n_points", 60), 1, 2),
                    ],
                    className="gy-2",
                ),
                html.Hr(),
                dbc.Row(
                    [
                        build_number_input("V-ref", "V_ref (V)", _d("V_ref", 1.23), 0.01, 0),
                        build_number_input("delta-s", "ΔS° (J/mol.K)", _d("delta_s_ref", 163.0), 1, None),
                        build_number_input("T-ref", "T_ref (K)", _d("T_ref", 298.15), 1, 200),
                        build_number_input("n-electrons", "n e-", _d("n_e", 2), 1, 1),
                    ],
                    className="gy-2",
                ),
                dbc.Row(
                    [
                        build_number_input("p-h2", "p_H2 (bar)", _d("p_h2", 1.0), 0.1, 0),
                        build_number_input("p-o2", "p_O2 (bar)", _d("p_o2", 1.0), 0.1, 0),
                        build_number_input("a-h2o", "a_H2O", _d("a_h2o", 1.0), 0.1, 0),
                        dbc.Col(
                            dbc.Checklist(
                                options=[{"label": "Usar Nernst", "value": "nernst"}],
                                value=["nernst"] if _d("use_nernst", False) else [],
                                id="use-nernst",
                                switch=True,
                            ),
                            md=3,
                        ),
                    ],
                    className="gy-2",
                ),
            ]
        ),
    ]
)


def electrode_card(prefix: str, title: str, enable_toggle: bool = False) -> dbc.Card:
    header_children = [title]
    if enable_toggle:
        header_children.append(
            dbc.Checklist(options=[{"label": "Activar electrodo B", "value": "enable"}], value=[], id="enable-b")
        )
    return dbc.Card(
        [
            dbc.CardHeader(header_children),
            dbc.CardBody(
                [
                    dbc.Row(
                    [
                        dbc.Col([dbc.Label("Nombre"), dbc.Input(id=f"name-{prefix}", value=_d(f"name_{prefix}", title), type="text")], md=4),
                        dbc.Col(
                            [
                                dbc.Label("Modelo cinético"),
                                dcc.Dropdown(
                                    id=f"model-{prefix}",
                                        options=[
                                        {"label": "Tafel", "value": "tafel"},
                                        {"label": "Butler-Volmer", "value": "butler-volmer"},
                                    ],
                                    value=_d(f"model_{prefix}", "tafel"),
                                    clearable=False,
                                ),
                            ],
                            md=4,
                        ),
                            dbc.Col(
                                [
                                    dbc.Label("j0_ref (A/cm²)"),
                                    dbc.Input(id=f"j0-{prefix}", type="number", value=_d(f"j0_{prefix}", 0.01), step=0.001, min=0),
                                ],
                                md=4,
                            ),
                    ],
                    className="gy-2",
                ),
                dbc.Row(
                    [
                        build_number_input(f"Ea-{prefix}", "Ea (J/mol)", _d(f"Ea_{prefix}", 40000), 1000, 0),
                        build_number_input(f"alpha-{prefix}", "alpha (Tafel/BV sim.)", _d(f"alpha_{prefix}", None), 0.05, 0),
                        build_number_input(f"alpha-a-{prefix}", "alpha_a (BV)", _d(f"alpha_a_{prefix}", None), 0.05, 0),
                        build_number_input(f"alpha-c-{prefix}", "alpha_c (BV)", _d(f"alpha_c_{prefix}", None), 0.05, 0),
                    ],
                    className="gy-2",
                ),
            ]
        ),
        ]
    )


ohmic_table = dash_table.DataTable(
    id="ohm-layers",
    columns=[
        {"name": "name", "id": "name", "type": "text"},
        {"name": "delta (cm)", "id": "delta", "type": "numeric"},
        {"name": "kappa_ref (S/cm)", "id": "kappa_ref", "type": "numeric"},
        {"name": "Ea_kappa (J/mol)", "id": "Ea_kappa", "type": "numeric"},
        {"name": "T_ref (K)", "id": "T_ref", "type": "numeric"},
    ],
    editable=True,
    row_deletable=True,
    data=_d("ohm_layers", DEFAULT_OHMIC_LAYERS),
    style_table={"overflowX": "auto"},
    style_cell={"padding": "4px"},
)

ohmic_card = dbc.Card(
    [
        dbc.CardHeader("Pérdidas óhmicas"),
        dbc.CardBody(
            [
                dbc.Button("Agregar capa", id="add-layer", color="secondary", size="sm", className="mb-2"),
                ohmic_table,
                dbc.Row(
                    [
                        build_number_input("R-extra", "Resistencia extra (Ω·cm²)", _d("R_extra", 0.02), 0.01, 0),
                    ],
                    className="gy-2 mt-2",
                ),
            ]
        ),
    ]
)

mass_card = dbc.Card(
    [
        dbc.CardHeader("Pérdidas por concentración"),
        dbc.CardBody(
            [
                dbc.Checklist(options=[{"label": "Incluir η_conc", "value": "conc"}], value=[], id="use-conc", switch=True),
                dbc.Row(
                    [
                        build_number_input("j-lim", "j_lim (A/cm²)", _d("j_lim", None), 0.1, 0),
                        build_number_input("Ea-jlim", "Ea j_lim (J/mol)", _d("Ea_jlim", None), 1000, 0),
                        build_number_input("D-eff", "D_eff (cm²/s)", _d("D_eff", None), 0.0001, 0),
                        build_number_input("C-bulk", "C_bulk (mol/cm³)", _d("C_bulk", None), 0.0001, 0),
                        build_number_input("delta-dif", "delta_dif (cm)", _d("delta_dif", None), 0.001, 0),
                    ],
                    className="gy-2",
                ),
            ]
        ),
    ]
)

layout_results = dbc.Row(
    [
        dbc.Col(dbc.Card([dbc.CardHeader("Curvas simuladas"), dbc.CardBody([dcc.Graph(id="curve-fig")])]), md=8),
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader("Curva ΔV (B - A)"),
                    dbc.CardBody([dcc.Graph(id="delta-fig")]),
                ]
            ),
            md=4,
        ),
    ],
    className="gy-3",
)

table_results = dbc.Card(
    [
        dbc.CardHeader("Tabla de resultados"),
        dbc.CardBody(
            [
                dash_table.DataTable(
                    id="results-table",
                    columns=[
                        {"name": "electrode", "id": "electrode"},
                        {"name": "T (K)", "id": "T"},
                        {"name": "j (A/cm²)", "id": "j"},
                        {"name": "V_cell (V)", "id": "V_cell"},
                        {"name": "V_rev (V)", "id": "V_rev"},
                        {"name": "eta_act", "id": "eta_act"},
                        {"name": "eta_ohm", "id": "eta_ohm"},
                        {"name": "eta_conc", "id": "eta_conc"},
                        {"name": "r_total", "id": "r_total"},
                        {"name": "modelo", "id": "model"},
                    ],
                    style_table={"overflowX": "auto"},
                    sort_action="native",
                    row_selectable="single",
                    page_size=10,
                ),
                html.Div(id="error-msg", className="text-danger mt-2"),
            ]
        ),
    ],
    className="my-3",
)

detail_card = dbc.Card(
    [
        dbc.CardHeader("Trazabilidad del punto seleccionado"),
        dbc.CardBody(
            [
                html.Div(id="detail-header", className="mb-2"),
                dash_table.DataTable(
                    id="steps-table",
                    columns=[
                        {"name": "Paso", "id": "name"},
                        {"name": "Expresión", "id": "expression"},
                        {"name": "Resultado", "id": "result"},
                        {"name": "Valores", "id": "values"},
                    ],
                    style_table={"overflowX": "auto"},
                    style_cell={"whiteSpace": "pre-line"},
                ),
                html.Pre(id="step-values", className="mt-3 bg-light p-2 border"),
            ]
        ),
    ]
)

upload_card = dbc.Card(
    [
        dbc.CardHeader("Datos experimentales (CSV j_exp, V_exp)"),
        dbc.CardBody(
            [
                dcc.Upload(
                    id="upload-exp",
                    children=html.Div(["Arrastra o selecciona un CSV"]),
                    style={
                        "width": "100%",
                        "height": "60px",
                        "lineHeight": "60px",
                        "borderWidth": "1px",
                        "borderStyle": "dashed",
                        "borderRadius": "3px",
                        "textAlign": "center",
                    },
                ),
                html.Div(id="upload-status", className="text-muted mt-2"),
            ]
        ),
    ]
)

app.layout = dbc.Container(
    [
        html.H2("Simulador de celda H - v2"),
        dbc.Row([dbc.Col(operating_controls, md=12)], className="gy-3"),
        dbc.Row(
            [dbc.Col(electrode_card("a", "Electrodo A"), md=6), dbc.Col(electrode_card("b", "Electrodo B", enable_toggle=True), md=6)],
            className="gy-3",
        ),
        dbc.Row([dbc.Col(ohmic_card, md=7), dbc.Col(mass_card, md=5)], className="gy-3"),
        dbc.Row(
            [
                dbc.Col(upload_card, md=6),
                dbc.Col(dbc.Button("Simular", id="run-btn", color="primary", className="mt-4"), md=2),
            ],
            className="gy-3",
        ),
        html.Hr(),
        layout_results,
        table_results,
        detail_card,
        dcc.Store(id="store-results"),
        dcc.Store(id="store-exp"),
    ],
    fluid=True,
)


# --- Callbacks --------------------------------------------------------------------------------

@app.callback(
    Output("ohm-layers", "data"),
    Input("add-layer", "n_clicks"),
    State("ohm-layers", "data"),
    prevent_initial_call=True,
)
def add_layer(n_clicks, rows):
    rows = rows or []
    rows.append({"name": f"capa_{len(rows)+1}", "delta": 0.001, "kappa_ref": 0.1, "Ea_kappa": None, "T_ref": 298.15})
    return rows


def _parse_upload(contents: str, filename: str) -> Tuple[pd.DataFrame, str]:
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
    # Normalizar encabezados para aceptar variantes comunes
    normalized = {col.strip().lower(): col for col in df.columns}
    j_col = None
    v_col = None
    for key in ("j_exp", "current_density_a_m2", "current_density_a_cm2", "j"):
        if key in normalized:
            j_col = normalized[key]
            break
    for key in ("v_exp", "voltage_v", "voltage", "v"):
        if key in normalized:
            v_col = normalized[key]
            break
    if j_col is None or v_col is None:
        raise ValueError("El CSV debe tener columnas j_exp,V_exp (o equivalentes: current_density..., voltage_V).")
    df = df.rename(columns={j_col: "j_exp", v_col: "V_exp"})
    return df[["j_exp", "V_exp"]], f"{filename}: {len(df)} filas cargadas"


@app.callback(
    Output("upload-status", "children"),
    Output("store-exp", "data"),
    Input("upload-exp", "contents"),
    State("upload-exp", "filename"),
    prevent_initial_call=True,
)
def handle_upload(contents, filename):
    try:
        df, msg = _parse_upload(contents, filename)
    except Exception as exc:  # noqa: BLE001
        return f"Error al leer CSV: {exc}", None
    return msg, df.to_dict("records")


@app.callback(
    Output("store-results", "data"),
    Output("error-msg", "children"),
    Input("run-btn", "n_clicks"),
    State("temp-list", "value"),
    State("j-min", "value"),
    State("j-max", "value"),
    State("n-points", "value"),
    State("V-ref", "value"),
    State("delta-s", "value"),
    State("T-ref", "value"),
    State("n-electrons", "value"),
    State("use-nernst", "value"),
    State("p-h2", "value"),
    State("p-o2", "value"),
    State("a-h2o", "value"),
    State("name-a", "value"),
    State("model-a", "value"),
    State("j0-a", "value"),
    State("Ea-a", "value"),
    State("alpha-a", "value"),
    State("alpha-a-a", "value"),
    State("alpha-c-a", "value"),
    State("name-b", "value"),
    State("model-b", "value"),
    State("j0-b", "value"),
    State("Ea-b", "value"),
    State("alpha-b", "value"),
    State("alpha-a-b", "value"),
    State("alpha-c-b", "value"),
    State("enable-b", "value"),
    State("ohm-layers", "data"),
    State("R-extra", "value"),
    State("use-conc", "value"),
    State("j-lim", "value"),
    State("Ea-jlim", "value"),
    State("D-eff", "value"),
    State("C-bulk", "value"),
    State("delta-dif", "value"),
    prevent_initial_call=True,
)
def run_simulation(
    _click,
    temp_list,
    j_min,
    j_max,
    n_points,
    V_ref,
    delta_s,
    T_ref,
    n_e,
    use_nernst,
    p_h2,
    p_o2,
    a_h2o,
    name_a,
    model_a,
    j0_a,
    Ea_a,
    alpha_a,
    alpha_a_a,
    alpha_c_a,
    name_b,
    model_b,
    j0_b,
    Ea_b,
    alpha_b,
    alpha_a_b,
    alpha_c_b,
    enable_b,
    ohm_layers,
    R_extra,
    use_conc,
    j_lim,
    Ea_jlim,
    D_eff,
    C_bulk,
    delta_dif,
):
    values = {
        "temps": temp_list,
        "j_min": j_min,
        "j_max": j_max,
        "n_points": n_points,
        "V_ref": V_ref,
        "delta_s_ref": delta_s,
        "T_ref": T_ref,
        "n_e": n_e,
        "use_nernst": "nernst" in (use_nernst or []),
        "p_h2": p_h2,
        "p_o2": p_o2,
        "a_h2o": a_h2o,
        "name_a": name_a,
        "model_a": model_a,
        "j0_a": j0_a,
        "Ea_a": Ea_a,
        "alpha_a": alpha_a,
        "alpha_a_a": alpha_a_a,
        "alpha_c_a": alpha_c_a,
        "name_b": name_b,
        "model_b": model_b,
        "j0_b": j0_b,
        "Ea_b": Ea_b,
        "alpha_b": alpha_b,
        "alpha_a_b": alpha_a_b,
        "alpha_c_b": alpha_c_b,
        "enable_b": "enable" in (enable_b or []),
        "ohm_layers": ohm_layers or [],
        "R_extra": R_extra,
        "use_conc": "conc" in (use_conc or []),
        "j_lim": j_lim,
        "Ea_jlim": Ea_jlim,
        "D_eff": D_eff,
        "C_bulk": C_bulk,
        "delta_dif": delta_dif,
    }
    try:
        cfg = _build_config_from_inputs(values)
        results = run_simulation_v2(cfg)
    except Exception as exc:  # noqa: BLE001
        return None, f"Error: {exc}"

    rows = []
    for label, points in results.items():
        for p in points:
            row = _point_to_row(p)
            row["label"] = label
            row["steps"] = [s.to_dict() for s in p.steps]
            row["j_lim"] = p.j_lim
            rows.append(row)
    return rows, ""


@app.callback(
    Output("curve-fig", "figure"),
    Output("delta-fig", "figure"),
    Input("store-results", "data"),
    Input("store-exp", "data"),
)
def update_figures(data, exp_data):
    if not data:
        return {"data": [], "layout": {"template": "plotly_white"}}, _blank_delta()
    df = pd.DataFrame(data)
    fig = {"data": [], "layout": {"template": "plotly_white", "xaxis": {"title": "j (A/cm²)"}, "yaxis": {"title": "V_cell (V)"}}}
    for (label, T), grp in df.groupby(["label", "T"]):
        grp_sorted = grp.sort_values("j")
        fig["data"].append(
            {"x": grp_sorted["j"], "y": grp_sorted["V_cell"], "mode": "lines+markers", "name": f"{label} @ {T}K"}
        )

    if exp_data:
        exp_df = pd.DataFrame(exp_data)
        fig["data"].append({"x": exp_df["j_exp"], "y": exp_df["V_exp"], "mode": "markers", "name": "Exp", "marker": {"color": "black"}})

    delta_fig = _blank_delta()
    if {"A", "B"}.issubset(set(df["label"].unique())):
        delta_lines = []
        for T in df["T"].unique():
            a = df[(df["label"] == "A") & (df["T"] == T)].sort_values("j")
            b = df[(df["label"] == "B") & (df["T"] == T)].sort_values("j")
            if len(a) and len(b) and len(a) == len(b):
                delta = b["V_cell"].values - a["V_cell"].values
                delta_lines.append({"x": a["j"], "y": delta, "mode": "lines+markers", "name": f"ΔV @ {T}K"})
        if delta_lines:
            delta_fig = {"data": delta_lines, "layout": {"template": "plotly_white", "xaxis": {"title": "j"}, "yaxis": {"title": "ΔV (B-A)"}}}

    return fig, delta_fig


def _blank_delta():
    return {"data": [], "layout": {"template": "plotly_white", "xaxis": {"title": "j"}, "yaxis": {"title": "ΔV (B-A)"}}}


@app.callback(
    Output("results-table", "data"),
    Input("store-results", "data"),
)
def update_table(data):
    return data or []


@app.callback(
    Output("detail-header", "children"),
    Output("steps-table", "data"),
    Output("step-values", "children"),
    Input("results-table", "selected_rows"),
    State("results-table", "data"),
    State("store-results", "data"),
)
def update_detail(selected_rows, table_data, store_data):
    if not store_data or selected_rows is None or not table_data:
        return "Selecciona una fila para ver las ecuaciones.", [], ""
    idx = selected_rows[0]
    selected = table_data[idx]
    point = next(
        (p for p in store_data if p["electrode"] == selected["electrode"] and p["T"] == selected["T"] and p["j"] == selected["j"]),
        None,
    )
    if not point:
        return "No se encontró el punto seleccionado.", [], ""
    steps_raw = point.get("steps", [])
    steps_table = [
        {
            "name": s["name"],
            "expression": s["expression"],
            "result": f"{s['result']:.6g}",
            "values": "\n".join(f"{k}: {v}" for k, v in s.get("values", {}).items()),
        }
        for s in steps_raw
    ]
    detail_payload = {
        "V_rev": selected["V_rev"],
        "eta_act": selected["eta_act"],
        "eta_ohm": selected["eta_ohm"],
        "eta_conc": selected["eta_conc"],
        "r_total": selected["r_total"],
        "modelo": selected["model"],
        "j_lim": point.get("j_lim"),
        "pasos": [{s["name"]: s.get("values", {})} for s in steps_raw],
    }
    values_text = json.dumps(detail_payload, indent=2)
    return f"{selected['electrode']} @ {selected['T']}K, j={selected['j']} A/cm²", steps_table, values_text


def _blank_figure(x_title: str, y_title: str, message: str) -> dict:
    return {
        "data": [],
        "layout": {
            "xaxis": {"title": x_title},
            "yaxis": {"title": y_title},
            "template": "plotly_white",
            "margin": {"l": 50, "r": 10, "t": 10, "b": 40},
            "annotations": [
                {
                    "text": message,
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"color": "#888"},
                }
            ],
        },
    }


if __name__ == "__main__":
    app.run_server(debug=False)
