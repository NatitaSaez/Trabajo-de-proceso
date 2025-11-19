import math
import unittest

from simulador.electrochemistry import arrhenius


class TestArrheniusKappa(unittest.TestCase):
    """Valida que arrhenius coincida con la expresión cerrada."""

    KAPPA_REF_ADJUSTED = 13.2  # S/m a 80 °C
    EA_KAPPA_ADJUSTED = 24500.0  # J/mol
    T_REF_C = 80.0  # °C

    @staticmethod
    def _expected_value(temp_celsius: float, kappa_ref: float, Ea: float, T_ref_c: float) -> float:
        temp_kelvin = temp_celsius + 273.15
        ref_kelvin = T_ref_c + 273.15
        exponent = -(Ea / 8.314462618) * (1.0 / temp_kelvin - 1.0 / ref_kelvin)
        return kappa_ref * math.exp(exponent)

    def _calc_kappa(self, temp_celsius: float) -> float:
        temp_kelvin = temp_celsius + 273.15
        ref_kelvin = self.T_REF_C + 273.15
        return arrhenius(
            self.KAPPA_REF_ADJUSTED,
            self.EA_KAPPA_ADJUSTED,
            temp_kelvin,
            ref_kelvin,
        )

    def test_reference_temperature(self):
        expected = self._expected_value(self.T_REF_C, self.KAPPA_REF_ADJUSTED, self.EA_KAPPA_ADJUSTED, self.T_REF_C)
        calculated = self._calc_kappa(self.T_REF_C)
        self.assertAlmostEqual(calculated, expected, delta=1e-9)

    def test_low_temperature_20c(self):
        expected = self._expected_value(20.0, self.KAPPA_REF_ADJUSTED, self.EA_KAPPA_ADJUSTED, self.T_REF_C)
        calculated = self._calc_kappa(20.0)
        self.assertAlmostEqual(calculated, expected, delta=1e-9)

    def test_intermediate_temperature_40c(self):
        expected = self._expected_value(40.0, self.KAPPA_REF_ADJUSTED, self.EA_KAPPA_ADJUSTED, self.T_REF_C)
        calculated = self._calc_kappa(40.0)
        self.assertAlmostEqual(calculated, expected, delta=1e-9)

    def test_intermediate_temperature_60c(self):
        expected = self._expected_value(60.0, self.KAPPA_REF_ADJUSTED, self.EA_KAPPA_ADJUSTED, self.T_REF_C)
        calculated = self._calc_kappa(60.0)
        self.assertAlmostEqual(calculated, expected, delta=1e-9)


if __name__ == "__main__":
    print("Ejecutando Test Unitario de Arrhenius:")
    unittest.main(argv=["first-arg-is-ignored"], exit=False)

