"""Nucleo de simulacion para una celda H de electrolisis.

Este paquete agrupa utilidades para:

* Calcular el voltaje ideal y los sobrepotenciales (activacion, ohmico y
  concentracion) descritos en ``definicion final de ecuaciones.md``.
* Evaluar el paisaje energetico de los intermedios O*/OH*/O2* a partir de
  datos DFT, siguiendo la metodologia del documento ``requerimientos.md``.
* Explorar el desempeno de catalizadores mediante funciones de mas alto nivel.
"""

from . import constants, data, detail, electrochemistry, models, orr, simulation

__all__ = [
    "constants",
    "data",
    "detail",
    "electrochemistry",
    "models",
    "orr",
    "simulation",
]
