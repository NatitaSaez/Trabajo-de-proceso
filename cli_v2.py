"""CLI v2 para el simulador 0D (lectura YAML, doble electrodo, validación CSV)."""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from simulador.config_v2 import SimulationConfigV2, load_config
from simulador.simulation_v2 import PointResultV2, run_simulation_v2


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _results_to_dataframe(results: Dict[str, List[PointResultV2]]) -> pd.DataFrame:
    rows = []
    for label, points in results.items():
        for p in points:
            row = p.to_row()
            row["electrode_label"] = label
            rows.append(row)
    return pd.DataFrame(rows)


def _plot_curves(df: pd.DataFrame, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 5))
    for (label, T), group in df.groupby(["electrode_label", "T"]):
        group_sorted = group.sort_values("j")
        ax.plot(group_sorted["j"], group_sorted["V_cell"], label=f"{label} @ {T}K")
    ax.set_xlabel("j (A/cm²)")
    ax.set_ylabel("V_cell (V)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def _load_experimental(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    expected = {"j_exp", "V_exp"}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"El CSV experimental debe contener columnas {expected}, faltan: {missing}")
    return df


def _validate_against_experiment(
    sim_df: pd.DataFrame, exp_df: pd.DataFrame
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    # Usar solo primer T para la comparación básica.
    first_T = sim_df["T"].iloc[0]
    sim_single = sim_df[sim_df["T"] == first_T].sort_values("j")
    # Interpolar V_sim en los j_exp
    V_interp = np.interp(exp_df["j_exp"].values, sim_single["j"].values, sim_single["V_cell"].values)
    errors = V_interp - exp_df["V_exp"].values
    metrics = {
        "rmse": float(np.sqrt(np.mean(errors**2))),
        "mae": float(np.mean(np.abs(errors))),
        "max_err": float(np.max(np.abs(errors))),
    }
    out = exp_df.copy()
    out["V_sim"] = V_interp
    out["error_V"] = errors
    out["T_sim"] = first_T
    return out, metrics


def save_trazabilidad(points: List[PointResultV2], path: Path) -> None:
    """Volcar pasos detallados a CSV (aplanado por paso)."""

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "electrode",
                "T",
                "j",
                "step_name",
                "expression",
                "result",
                "values",
            ]
        )
        for p in points:
            for step in p.steps:
                writer.writerow(
                    [
                        p.electrode,
                        p.temperature,
                        p.current_density,
                        step.name,
                        step.expression,
                        step.result,
                        step.values,
                    ]
                )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulador 0D v2 (celda H).")
    parser.add_argument("--config", required=True, help="Ruta al archivo YAML de configuración.")
    parser.add_argument("--output-dir", default="outputs", help="Directorio destino para CSV/figuras.")
    parser.add_argument(
        "--with-experimental", dest="exp_csv", help="CSV con columnas j_exp, V_exp para validar."
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Desactivar la generación de la figura PNG con curvas simuladas.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    _ensure_dir(output_dir)

    cfg: SimulationConfigV2 = load_config(args.config)
    results = run_simulation_v2(cfg)
    df = _results_to_dataframe(results)
    df.to_csv(output_dir / "simulacion.csv", index=False)

    # CSV por electrodo
    for label, points in results.items():
        pd.DataFrame([p.to_row() for p in points]).to_csv(output_dir / f"simulacion_{label}.csv", index=False)
        save_trazabilidad(points, output_dir / f"trazabilidad_{label}.csv")

    if not args.no_plot:
        _plot_curves(df, output_dir / "curvas.png")

    if args.exp_csv:
        exp_df = _load_experimental(Path(args.exp_csv))
        exp_out, metrics = _validate_against_experiment(df, exp_df)
        exp_out.to_csv(output_dir / "validacion_vs_exp.csv", index=False)
        with open(output_dir / "validacion_metrics.txt", "w", encoding="utf-8") as f:
            for k, v in metrics.items():
                f.write(f"{k}: {v:.6f}\n")
        print(f"Validación vs experimento -> RMSE={metrics['rmse']:.4f} V, MAE={metrics['mae']:.4f} V")

    print(f"Resultados guardados en: {os.path.abspath(output_dir)}")


if __name__ == "__main__":
    main()
