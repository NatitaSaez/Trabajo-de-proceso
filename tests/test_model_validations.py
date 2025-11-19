import math
import unittest

from simulador.config_v2 import ElectrodeKineticsV2, OhmicConfig, OhmicLayer, ThermoSettings
from simulador.constants import CONSTANTS
from simulador.electrochemistry import arrhenius
from simulador.simulation_v2 import _eta_activation, _eta_ohmic, _reversible_potential


class TestElectrolyzerModel(unittest.TestCase):
    """Pruebas relacionadas con V_rev, η_ohm y η_act según el modelo 0D."""

    # Temperaturas de interés
    T_REF = 298.15  # K
    T_20C = 293.15
    T_80C = 353.15

    # Corriente objetivo (A/cm²)
    J_TARGET = 0.6188135

    # Parámetros de termodinámica
    V_REF = 1.23
    DELTA_S = 200.0  # J/mol/K
    ELECTRONS = 2

    # Parámetros de conductividad (S/cm)
    KAPPA_REF_SC = 13.2 / 100.0
    EA_KAPPA = 24500.0

    # Espesor del separador (cm) y resistencia extra (ohm·cm²)
    DELTA_SEP_CM = 0.00046 * 100.0
    R_EXTRA = 0.02

    # Cinética OER
    OER = ElectrodeKineticsV2(
        name="OER",
        kinetic_model="butler-volmer",
        n=2,
        alpha=1.14,
        alpha_a=1.14,
        alpha_c=0.86,
        j0_ref=0.00093,
        Ea=46156.0,
        T_ref=343.15,
    )

    # Cinética HER
    HER = ElectrodeKineticsV2(
        name="HER",
        kinetic_model="butler-volmer",
        n=2,
        alpha=0.78,
        alpha_a=0.78,
        alpha_c=1.22,
        j0_ref=0.00234,
        Ea=40000.0,
        T_ref=353.15,
    )

    def _solve_butler_volmer(self, j, j0, alpha_a, alpha_c, n, temperature):
        """Resuelve BV por bisección para comparar contra la implementación."""

        r_gas = CONSTANTS.gas_constant
        faraday = CONSTANTS.faraday

        def residual(eta):
            term_a = math.exp(alpha_a * n * faraday * eta / (r_gas * temperature))
            term_c = math.exp(-alpha_c * n * faraday * eta / (r_gas * temperature))
            return j0 * (term_a - term_c) - j

        lower, upper = 0.0, 0.01
        while residual(upper) < 0 and upper < 5.0:
            upper *= 2.0

        for _ in range(120):
            mid = 0.5 * (lower + upper)
            res_mid = residual(mid)
            if abs(res_mid) < 1e-10:
                return mid
            if res_mid > 0:
                upper = mid
            else:
                lower = mid
        return 0.5 * (lower + upper)

    def test_reversible_potential_linear_dependence(self):
        """Verifica que V_rev siga la dependencia lineal con ΔS."""

        thermo = ThermoSettings(
            V_ref=self.V_REF,
            delta_s_ref=self.DELTA_S,
            T_ref=self.T_REF,
            electrons=self.ELECTRONS,
        )
        v_rev, _ = _reversible_potential(thermo, self.T_20C, CONSTANTS)
        expected = self.V_REF + (self.DELTA_S / (self.ELECTRONS * CONSTANTS.faraday)) * (
            self.T_20C - self.T_REF
        )
        self.assertAlmostEqual(v_rev, expected, delta=2e-3)

    def test_kappa_arrhenius_adjustment(self):
        """Comprueba que el cálculo de κ(T) siga la expresión de Arrhenius."""

        kappa_sc = arrhenius(
            self.KAPPA_REF_SC,
            self.EA_KAPPA,
            self.T_20C,
            self.T_80C,
            CONSTANTS,
        )
        exponent = -(self.EA_KAPPA / CONSTANTS.gas_constant) * (
            1.0 / self.T_20C - 1.0 / self.T_80C
        )
        expected_sc = self.KAPPA_REF_SC * math.exp(exponent)
        self.assertAlmostEqual(kappa_sc, expected_sc, delta=1e-12)

    def test_eta_ohm_with_unit_conversion(self):
        """Valida que η_ohm use la kappa ajustada y aplique correctamente las unidades."""

        layer = OhmicLayer(
            name="zirfon",
            delta=self.DELTA_SEP_CM,
            kappa_ref=self.KAPPA_REF_SC,
            Ea_kappa=self.EA_KAPPA,
            T_ref=self.T_80C,
        )
        ohmic = OhmicConfig(layers=[layer], extra_resistance=self.R_EXTRA)
        eta_ohm, _, _ = _eta_ohmic(self.J_TARGET, ohmic, self.T_20C, CONSTANTS)

        kappa_sc = arrhenius(
            self.KAPPA_REF_SC, self.EA_KAPPA, self.T_20C, self.T_80C, CONSTANTS
        )
        r_sep = self.DELTA_SEP_CM / kappa_sc
        expected_eta = self.J_TARGET * (r_sep + self.R_EXTRA)

        self.assertAlmostEqual(eta_ohm, expected_eta, delta=2e-3)

    def test_oer_activation_matches_bv_solution(self):
        """La η_act del OER sigue la dependencia Arrhenius de j0(T) y solvencia BV."""

        j0_expected = arrhenius(
            self.OER.j0_ref, self.OER.Ea, self.T_20C, self.OER.T_ref, CONSTANTS
        )
        eta_model, _, j0_t = _eta_activation(self.J_TARGET, self.OER, self.T_20C, CONSTANTS)
        self.assertAlmostEqual(j0_t, j0_expected, delta=1e-6)

        eta_expected = self._solve_butler_volmer(
            self.J_TARGET,
            j0_expected,
            self.OER.alpha_a,
            self.OER.alpha_c,
            self.OER.n,
            self.T_20C,
        )
        self.assertAlmostEqual(eta_model, eta_expected, delta=2e-3)

    def test_her_activation_matches_bv_solution(self):
        """La η_act del HER también concuerda con la solución BV independiente."""

        j0_expected = arrhenius(
            self.HER.j0_ref, self.HER.Ea, self.T_20C, self.HER.T_ref, CONSTANTS
        )
        eta_model, _, j0_t = _eta_activation(self.J_TARGET, self.HER, self.T_20C, CONSTANTS)
        self.assertAlmostEqual(j0_t, j0_expected, delta=1e-6)

        eta_expected = self._solve_butler_volmer(
            self.J_TARGET,
            j0_expected,
            self.HER.alpha_a,
            self.HER.alpha_c,
            self.HER.n,
            self.T_20C,
        )
        self.assertAlmostEqual(eta_model, eta_expected, delta=2e-3)

    def test_total_activation_is_sum_of_electrodes(self):
        """Verifica que la suma de las η_act individuales corresponda al total."""

        eta_oer, _, _ = _eta_activation(self.J_TARGET, self.OER, self.T_20C, CONSTANTS)
        eta_her, _, _ = _eta_activation(self.J_TARGET, self.HER, self.T_20C, CONSTANTS)
        self.assertAlmostEqual(eta_oer + eta_her, 0.2381, delta=5e-3)


if __name__ == "__main__":
    print("\n--- EJECUTANDO SUITE DE TESTS PARA MODELO 0D ---\n")
    unittest.main(argv=["first-arg-is-ignored"], exit=False)
