"""Aplicacion web (v1 y v2) para el simulador de celda H."""

from __future__ import annotations

import pathlib
import sys
import csv
import io
from dataclasses import replace
from typing import List, Tuple

import dash
import dash_bootstrap_components as dbc
import flask
import numpy as np
from dash import Dash, Input, Output, State, dash_table, dcc, html

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulador import data, detail, simulation


def _build_config(temperature: float, pH: float) -> simulation.ElectrolyzerSimulator:
    """Crea un simulador con las condiciones indicadas (temperatura en Kelvin)."""

    conditions = replace(data.DEFAULT_CONFIG.conditions, temperature=temperature, pH=pH)
    config = replace(data.DEFAULT_CONFIG, conditions=conditions)
    return simulation.ElectrolyzerSimulator(config)


def _polarization(
    sim: simulation.ElectrolyzerSimulator,
    current_range: Tuple[float, float],
    num_points: int,
) -> Tuple[np.ndarray, List[float]]:
    currents = np.linspace(current_range[0], current_range[1], num_points)
    voltages = np.array(sim.polarization_curve(currents))
    return currents, voltages.tolist()


def _activity_profile(
    catalyst_name: str, temperature: float, pH: float, potentials: np.ndarray
) -> List[float]:
    analyzer = simulation.CatalystAnalyzer(
        catalyst=data.CATALYSTS[catalyst_name], temperature=temperature, pH=pH
    )
    return analyzer.activity_profile(potentials.tolist())


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


def _validate_currents(current_min: float | None, current_max: float | None, focus_current: float | None) -> str | None:
    if current_min is None or current_max is None or focus_current is None:
        return "Completa los valores de corriente para generar la simulacion."
    if current_min <= 0 or current_max <= 0:
        return "Las corrientes deben ser mayores que cero."
    if current_min >= current_max:
        return "La corriente minima debe ser menor que la maxima."
    if focus_current <= 0:
        return "La corriente de referencia debe ser mayor que cero."
    return None


FIELD_DESCRIPTIONS = {
    "temperature": "Temperatura de operacion de la celda en Kelvin; afecta el potencial ideal, la cinetica y el transporte ionico.",
    "ph": "pH del electrolito. Ajusta la energia libre de protones utilizada en los calculos termodinamicos.",
    "current_min": "Limite inferior del barrido de densidad de corriente para la curva de polarizacion.",
    "current_max": "Limite superior del barrido de densidad de corriente para la curva de polarizacion.",
    "samples": "Numero de puntos discretos utilizados para trazar la curva entre las corrientes minima y maxima.",
    "focus_current": "Punto especifico de densidad de corriente usado para desglosar los sobrepotenciales.",
    "catalyst": "Conjunto de parametros DFT (energias de adsorcion y barreras) asociados al catalizador seleccionado.",
}


def label_with_info(text: str, tooltip_id: str, field_key: str) -> html.Div:
    return html.Div(
        [
            html.Span(text),
            html.Span("ⓘ", id=tooltip_id, className="info-icon", tabIndex=0),
            dbc.Tooltip(FIELD_DESCRIPTIONS[field_key], target=tooltip_id, placement="top"),
        ],
        className="label-with-info",
    )


def _component_id(prefix: str | None, suffix: str) -> str:
    if prefix:
        return f"{prefix}-{suffix}"
    return suffix


CATALYST_OPTIONS = [
    {"label": data.CATALYSTS[name].name, "value": name} for name in data.CATALYSTS
]

COMMON_STYLES = [dbc.themes.SANDSTONE]
server = flask.Flask(__name__)

app: Dash = dash.Dash(
    __name__,
    title="Simulador Celda H",
    external_stylesheets=COMMON_STYLES,
    suppress_callback_exceptions=True,
    server=server,
)


def _cards_section(prefix: str | None) -> dbc.Row:
    cards = [
        dbc.Col(
            dbc.Card([dbc.CardHeader("Voltaje ideal"), html.H3(id=_component_id(prefix, "card-videal"))]),
            md=3,
        ),
        dbc.Col(
            dbc.Card([dbc.CardHeader("Perdida activacion"), html.H3(id=_component_id(prefix, "card-eta-act"))]),
            md=3,
        ),
        dbc.Col(
            dbc.Card([dbc.CardHeader("Perdida ohmica"), html.H3(id=_component_id(prefix, "card-eta-ohm"))]),
            md=3,
        ),
        dbc.Col(
            dbc.Card(
                [dbc.CardHeader("Perdida concentracion"), html.H3(id=_component_id(prefix, "card-eta-conc"))]
            ),
            md=3,
        ),
    ]
    return dbc.Row(cards, className="gy-3")


def _graphs_section(prefix: str | None) -> dbc.Row:
    return dbc.Row(
        [
            dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Curva de polarizacion"),
                                dcc.Graph(id=_component_id(prefix, "polarization-graph")),
                            ]
                        ),
                        md=7,
                    ),
            dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Actividad catalitica"),
                                dcc.Graph(id=_component_id(prefix, "activity-graph")),
                            ]
                        ),
                        md=5,
            ),
        ],
        className="gy-3",
    )


def _hero_section() -> dbc.Container:
    return dbc.Container(
        [
            html.H1("Simulador de celda H 0D", className="display-5"),
            html.P(
                "Esta version muestra la curva, una tabla de resultados y el detalle de las ecuaciones evaluadas "
                "en cada punto.",
                className="lead",
            ),
        ],
        className="py-4",
    )


def _control_panel() -> dbc.Card:
    return dbc.Card(
        dbc.CardBody(
            [
                html.H5("Condiciones de operacion", className="card-title"),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                label_with_info("Temperatura (K)", "temperature-info", "temperature"),
                                dcc.Slider(
                                    id="temperature-slider",
                                    min=313,
                                    max=373,
                                    step=1,
                                    value=353,
                                    marks=None,
                                    tooltip={"placement": "bottom"},
                                ),
                                html.Div(id="temperature-display", className="slider-value"),
                            ],
                            md=6,
                        ),
                        dbc.Col(
                            [
                                label_with_info("pH", "ph-info", "ph"),
                                dcc.Slider(
                                    id="ph-slider",
                                    min=0,
                                    max=14,
                                    step=0.1,
                                    value=0.0,
                                    marks={0: "0", 7: "7", 14: "14"},
                                    tooltip={"placement": "bottom"},
                                ),
                                html.Div(id="ph-display", className="slider-value"),
                            ],
                            md=6,
                        ),
                    ],
                    className="gy-3",
                ),
                html.Hr(),
                html.H5("Configuracion de corriente"),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                label_with_info(
                                    "Corriente minima (A/cm^2)",
                                    "current-min-info",
                                    "current_min",
                                ),
                                dbc.Input(id="current-min", type="number", value=0.2, step=0.1, min=0.01),
                            ],
                            md=4,
                        ),
                        dbc.Col(
                            [
                                label_with_info(
                                    "Corriente maxima (A/cm^2)",
                                    "current-max-info",
                                    "current_max",
                                ),
                                dbc.Input(id="current-max", type="number", value=2.0, step=0.1, min=0.2),
                            ],
                            md=4,
                        ),
                        dbc.Col(
                            [
                                label_with_info("Muestras en curva", "samples-info", "samples"),
                                dcc.Slider(
                                    id="samples-slider",
                                    min=5,
                                    max=40,
                                    step=1,
                                    value=20,
                                    marks={i: str(i) for i in range(5, 41, 5)},
                                    tooltip={"placement": "bottom"},
                                ),
                                html.Div(id="samples-display", className="slider-value"),
                            ],
                            md=4,
                        ),
                    ],
                    className="gy-3",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                label_with_info(
                                    "Corriente para desglose (A/cm^2)",
                                    "focus-current-info",
                                    "focus_current",
                                ),
                                dbc.Input(id="focus-current", type="number", value=1.0, step=0.1, min=0.1),
                            ],
                            md=6,
                        ),
                        dbc.Col(
                            [
                                label_with_info("Catalizador", "catalyst-info", "catalyst"),
                                dcc.Dropdown(
                                    id="catalyst-dropdown",
                                    options=CATALYST_OPTIONS,
                                    value="Pt",
                                    clearable=False,
                                ),
                            ],
                            md=6,
                        ),
                    ],
                    className="gy-3",
                ),
            ]
        ),
        className="shadow-sm",
    )


def _table_section() -> dbc.Card:
    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(html.Span("Tabla de resultados"), md=8),
                        dbc.Col(
                            dbc.Button(
                                "Descargar CSV",
                                id="download-btn",
                                color="primary",
                                size="sm",
                                className="float-end",
                            ),
                            md=4,
                        ),
                    ],
                    align="center",
                )
            ),
            dash_table.DataTable(
                id="results-table",
                columns=[
                    {"name": "i (A/cm^2)", "id": "current"},
                    {"name": "V total (V)", "id": "voltage"},
                    {"name": "V ideal (V)", "id": "V_ideal"},
                    {"name": "eta_act total (V)", "id": "eta_act_total"},
                    {"name": "eta_act anodo (V)", "id": "eta_act_an"},
                    {"name": "eta_act catodo (V)", "id": "eta_act_cat"},
                    {"name": "eta_ohm (V)", "id": "eta_ohm"},
                    {"name": "eta_conc (V)", "id": "eta_conc"},
                ],
                data=[],
                style_table={"maxHeight": "320px", "overflowY": "auto"},
                style_cell={"textAlign": "center"},
                row_selectable="single",
                selected_rows=[],
            ),
        ]
    )


def _points_grid_section() -> dbc.Card:
    return dbc.Card(
        [
            dbc.CardHeader("Grilla completa de puntos y ecuaciones"),
            dash_table.DataTable(
                id="points-grid",
                columns=[
                    {"name": "i (A/cm^2)", "id": "current"},
                    {"name": "V total (V)", "id": "voltage"},
                    {"name": "Ecuaciones evaluadas", "id": "equations"},
                ],
                data=[],
                style_table={"maxHeight": "320px", "overflowY": "auto"},
                style_cell={"whiteSpace": "pre-line", "textAlign": "left"},
            ),
        ]
    )


def _detail_section() -> dbc.Card:
    return dbc.Card(
        [
            dbc.CardHeader("Detalle de ecuaciones"),
            dbc.CardBody(
                [
                    html.Div(id="selected-point"),
                    dash_table.DataTable(
                        id="equation-steps-table",
                        columns=[
                            {"name": "Paso", "id": "name"},
                            {"name": "Expresion", "id": "expression"},
                            {"name": "Resultado", "id": "result"},
                        ],
                        data=[],
                        style_table={"maxHeight": "260px", "overflowY": "auto"},
                        style_cell={"textAlign": "left", "whiteSpace": "normal"},
                    ),
                    html.Div(id="equation-detail", className="mt-3"),
                ]
            ),
        ]
    )


app.layout = dbc.Container(
    [
        _hero_section(),
        html.H2("Condiciones de operacion", className="mt-4"),
        _control_panel(),
        html.Hr(),
        html.H2("Valores y graficos", className="mt-4"),
        html.Div(id="alert-placeholder"),
        _cards_section(None),
        html.Div(className="my-3"),
        _graphs_section(None),
        html.Hr(),
        html.H2("Datos generados", className="mt-4"),
        html.H5("Tabla de resultados", className="mt-2"),
        dbc.Row(
            [
                dbc.Col(_table_section(), md=5),
                dbc.Col(_points_grid_section(), md=7),
            ],
            className="gy-4",
        ),
        html.Hr(),
        html.H2("Detalle de ecuaciones", className="mt-4"),
        _detail_section(),
        dcc.Download(id="download-table"),
        dcc.Store(id="detail-store"),
    ],
    fluid=True,
    className="pb-4",
)


# ---------------------------------------------------------------------------------------------
# Callbacks V1


@app.callback(Output("temperature-display", "children"), Input("temperature-slider", "value"))
def update_temperature_display(value: float) -> str:
    return f"{value:.1f} K"


@app.callback(Output("ph-display", "children"), Input("ph-slider", "value"))
def update_ph_display(value: float) -> str:
    return f"pH {value:.1f}"


@app.callback(Output("samples-display", "children"), Input("samples-slider", "value"))
def update_samples_display(value: int) -> str:
    return f"{value} puntos"


@app.callback(
    [
        Output("polarization-graph", "figure"),
        Output("activity-graph", "figure"),
        Output("card-videal", "children"),
        Output("card-eta-act", "children"),
        Output("card-eta-ohm", "children"),
        Output("card-eta-conc", "children"),
        Output("results-table", "data"),
        Output("points-grid", "data"),
        Output("results-table", "selected_rows"),
        Output("detail-store", "data"),
        Output("alert-placeholder", "children"),
    ],
    [
        Input("temperature-slider", "value"),
        Input("ph-slider", "value"),
        Input("current-min", "value"),
        Input("current-max", "value"),
        Input("samples-slider", "value"),
        Input("focus-current", "value"),
        Input("catalyst-dropdown", "value"),
    ],
)
def update_outputs(
    temperature: float,
    pH: float,
    current_min: float,
    current_max: float,
    samples: int,
    focus_current: float,
    catalyst: str,
):
    error = _validate_currents(current_min, current_max, focus_current)
    if error:
        alert = dbc.Alert(error, color="danger", dismissable=True)
        placeholder_fig = _blank_figure("Corriente (A/cm^2)", "Voltaje (V)", "Ajusta los valores para simular.")
        placeholder_act = _blank_figure("Potencial (V vs SHE)", "Actividad relativa", "Ajusta los valores para simular.")
        return (
            placeholder_fig,
            placeholder_act,
            "--",
            "--",
            "--",
            "--",
            [],
            [],
            [],
            [],
            alert,
        )

    sim = _build_config(temperature, pH)
    currents = np.linspace(current_min, current_max, samples)
    details = detail.detailed_curve(currents.tolist(), sim.config)
    voltages = [point.voltage for point in details]
    table_rows_raw = [point.table_row() for point in details]
    table_rows = [
        {
            "current": f"{row['current']:.3f}",
            "voltage": f"{row['voltage']:.3f}",
            "V_ideal": f"{row['V_ideal']:.3f}",
            "eta_act_total": f"{row['eta_act_total']:.3f}",
            "eta_act_an": f"{row['eta_act_an']:.3f}",
            "eta_act_cat": f"{row['eta_act_cat']:.3f}",
            "eta_ohm": f"{row['eta_ohm']:.3f}",
            "eta_conc": f"{row['eta_conc']:.3f}",
        }
        for row in table_rows_raw
    ]
    store_data = [point.to_dict() for point in details]
    points_grid = []
    for point in store_data:
        equations_text = "\n".join(
            f"{idx+1}. {step['name']} -> {step['expression']} = {step['result']:.4f}"
            for idx, step in enumerate(point["steps"])
        )
        points_grid.append(
            {
                "current": f"{point['current_density']:.3f}",
                "voltage": f"{point['voltage']:.3f}",
                "equations": equations_text,
            }
        )

    breakdown = sim.voltage_breakdown(focus_current)
    cards = (
        f"{breakdown['V_ideal']:.3f} V",
        f"{breakdown['eta_activacion']:.3f} V",
        f"{breakdown['eta_ohmico']:.3f} V",
        f"{breakdown['eta_concentracion']:.3f} V",
    )

    customdata = [
        [
            row["V_ideal"],
            row["eta_act_total"],
            row["eta_ohm"],
            row["eta_conc"],
        ]
        for row in table_rows_raw
    ]
    pol_fig = {
        "data": [
            {
                "x": currents.tolist(),
                "y": voltages,
                "mode": "lines+markers",
                "name": "V celda",
                "line": {"color": "#1F7A8C", "width": 3},
                "customdata": customdata,
                "hovertemplate": (
                    "i = %{x:.3f} A/cm^2<br>"
                    "V = %{y:.3f} V<br>"
                    "V ideal = %{customdata[0]:.3f} V<br>"
                    "eta_act = %{customdata[1]:.3f} V<br>"
                    "eta_ohm = %{customdata[2]:.3f} V<br>"
                    "eta_conc = %{customdata[3]:.3f} V<br>"
                    "<extra></extra>"
                ),
            }
        ],
        "layout": {
            "xaxis": {"title": "Corriente (A/cm^2)"},
            "yaxis": {"title": "Voltaje (V)"},
            "template": "plotly_white",
            "margin": {"l": 40, "r": 10, "t": 10, "b": 40},
        },
    }

    potentials = np.linspace(0.6, 1.3, 60)
    activities = _activity_profile(catalyst, temperature, pH, potentials)
    act_fig = {
        "data": [
            {
                "x": potentials.tolist(),
                "y": activities,
                "mode": "lines",
                "line": {"color": "#FFBF69", "width": 3},
                "fill": "tozeroy",
            }
        ],
        "layout": {
            "xaxis": {"title": "Potencial (V vs SHE)"},
            "yaxis": {"title": "Actividad relativa", "type": "log", "rangemode": "tozero"},
            "template": "plotly_white",
            "margin": {"l": 50, "r": 10, "t": 10, "b": 40},
        },
    }

    selected_rows = [0] if table_rows else []

    return (
        pol_fig,
        act_fig,
        *cards,
        table_rows,
        points_grid,
        selected_rows,
        store_data,
        None,
    )


@app.callback(
    Output("selected-point", "children"),
    Output("equation-steps-table", "data"),
    Output("equation-detail", "children"),
    Input("detail-store", "data"),
    Input("results-table", "selected_rows"),
)
def update_equation_detail(store_data, selected_rows):
    if not store_data:
        message = "Selecciona un punto en la tabla para visualizar las ecuaciones evaluadas."
        return message, [], message
    idx = 0
    if selected_rows:
        idx = min(selected_rows[0], len(store_data) - 1)
    detail_point = store_data[idx]
    steps = detail_point["steps"]
    contrib = detail_point["contributions"]
    summary_cards = [
        html.H5(f"Detalle para i = {detail_point['current_density']:.3f} A/cm^2", className="mb-3"),
        dbc.Row(
            [
                dbc.Col(dbc.Card([dbc.CardHeader("V ideal"), html.H4(f"{contrib['V_ideal']:.3f} V")]), md=3),
                dbc.Col(
                    dbc.Card([dbc.CardHeader("eta_act total"), html.H4(f"{contrib['eta_act_total']:.3f} V")]), md=3
                ),
                dbc.Col(dbc.Card([dbc.CardHeader("eta_ohm"), html.H4(f"{contrib['eta_ohm']:.3f} V")]), md=3),
                dbc.Col(dbc.Card([dbc.CardHeader("eta_conc"), html.H4(f"{contrib['eta_conc']:.3f} V")]), md=3),
            ],
            className="gy-2 mb-3",
        ),
    ]
    steps_table = [
        {"name": step["name"], "expression": step["expression"], "result": f"{step['result']:.6f}"} for step in steps
    ]

    accordion_items = []
    for i, step in enumerate(steps):
        values_list = html.Ul([html.Li(f"{k} = {v:.6g}") for k, v in step["values"].items()])
        accordion_items.append(
            dbc.AccordionItem(
                [
                    html.P(step["expression"], className="text-muted"),
                    values_list,
                    html.P(f"Resultado: {step['result']:.6f}"),
                ],
                title=f"{step['name']}",
                item_id=str(i),
            )
        )
    accordion = dbc.Accordion(accordion_items, always_open=False, flush=True)
    return summary_cards, steps_table, accordion


@app.callback(
    Output("download-table", "data"),
    Input("download-btn", "n_clicks"),
    State("detail-store", "data"),
    prevent_initial_call=True,
)
def download_table(n_clicks, store_data):
    if not n_clicks or not store_data:
        raise dash.exceptions.PreventUpdate
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "current_density",
            "voltage",
            "V_ideal",
            "eta_act_total",
            "eta_act_an",
            "eta_act_cat",
            "eta_ohm",
            "eta_conc",
        ]
    )
    for point in store_data:
        contrib = point["contributions"]
        writer.writerow(
            [
                f"{point['current_density']:.6f}",
                f"{point['voltage']:.6f}",
                f"{contrib['V_ideal']:.6f}",
                f"{contrib['eta_act_total']:.6f}",
                f"{contrib['eta_act_an']:.6f}",
                f"{contrib['eta_act_cat']:.6f}",
                f"{contrib['eta_ohm']:.6f}",
                f"{contrib['eta_conc']:.6f}",
            ]
        )
    return {"content": buffer.getvalue(), "filename": "curva_detallada.csv"}


if __name__ == "__main__":
    app.run_server(debug=True)
