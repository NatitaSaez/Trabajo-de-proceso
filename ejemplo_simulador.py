"""Ejemplo rapido de uso del nucleo de simulacion."""

from simulador import data, simulation


def main() -> None:
    sim = simulation.ElectrolyzerSimulator(data.DEFAULT_CONFIG)
    currents = [0.2, 0.5, 1.0, 2.0]
    voltages = sim.polarization_curve(currents)
    print("=== Curva de polarizacion (80 degC) ===")
    for i, v in zip(currents, voltages):
        breakdown = sim.voltage_breakdown(i)
        print(f"i = {i:4.1f} A/cm^2 -> V = {v:5.3f} V (eta_act={breakdown['eta_activacion']:.3f} V)")

    analyzer = simulation.CatalystAnalyzer(data.CATALYSTS["Pt"], temperature=298.15, pH=0.0)
    potentials = [0.7, 0.8, 0.9, 1.0, 1.23]
    print("\n=== Actividad catalitica relativa (Pt) ===")
    for U, activity in zip(potentials, analyzer.activity_profile(potentials)):
        info = analyzer.limiting_barriers(U)
        print(
            f"U = {U:4.2f} V -> A = {activity:7.3e}, "
            f"via dominante: {info['via_dominante']} (DeltaG* = {info['barrera']:.2f} eV)"
        )


if __name__ == "__main__":
    main()
