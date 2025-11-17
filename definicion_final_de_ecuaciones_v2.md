---
## 1. Ecuación global de la curva de polarización

### 1.1. Suma de contribuciones de sobrepotencial

[
V_\text{cell}(j,T) ;=; V_\text{rev}(T) ;+; \eta_\text{act}(j,T) ;+; \eta_\text{ohm}(j,T) ;+; \eta_\text{conc}(j,T)
]

Si quieres partir simple:

[
V_\text{cell}(j,T) ;\approx; V_\text{rev}(T) ;+; \eta_\text{act}(j,T) ;+; \eta_\text{ohm}(j,T)
]

**Por qué se usa**
Es la descomposición estándar de la curva de polarización: el voltaje total es el potencial reversible más las pérdidas cinéticas (activación), resistivas (óhmicas) y de transporte (concentración).

**Datos necesarios**

* Tipo de celda: área activa (A), espesores de membrana/electrolito/electrodos.
* Rango de densidad de corriente (j) que quieres simular.
* Rango de temperatura (T).

---

## 2. Potencial reversible (V_\text{rev}(T))

Para la reacción global en agua alcalina (ej. KOH):

[
\text{Cat: } 2H_2O + 2e^- \rightarrow H_2 + 2OH^-
]
[
\text{Án: } 2OH^- \rightarrow \tfrac{1}{2}O_2 + H_2O + 2e^-
]
[
\text{Global: } H_2O(l) \rightarrow H_2(g) + \tfrac{1}{2}O_2(g)
]

### 2.1. Desde energía libre de Gibbs (con entropía)

[
\Delta G(T) = \Delta H(T) - T,\Delta S(T)
]

[
V_\text{rev}(T) = -\frac{\Delta G(T)}{nF}
]

Con aproximación lineal en (T) (muy típica):

[
V_\text{rev}(T) \approx V_\text{rev}(T_0) + \frac{\Delta S^\circ}{nF},(T - T_0)
]

donde:

* (n = 2) electrones/mol (H_2)
* (F): constante de Faraday
* (\Delta S^\circ): cambio de entropía estándar de la reacción global
* (T_0): temperatura de referencia (298 K, por ejemplo)

Si quieres incluir condiciones no estándar:

[
V_\text{rev}(T) = V_\text{rev}^\circ(T) + \frac{RT}{nF}\ln Q
]

donde (Q) es el cociente de reacción (en la práctica, función de (p_{H_2}), (p_{O_2}), actividad del agua, etc.).

**Por qué se usa**
Te da el mínimo voltaje termodinámico para descomponer agua a una cierta temperatura. Es el “baseline” contra el cual se suman todas las pérdidas.

**Datos necesarios**

* (V_\text{rev}(T_0)) o (\Delta G^\circ(T_0)) de la reacción global.
* (\Delta S^\circ) o datos tabulados de (\Delta H^\circ(T)) y (\Delta S^\circ(T)).
* Temperatura (T).
* (Opcional) Presiones parciales de (H_2) y (O_2) si usas Nernst.

---

## 3. Sobretensión de activación (\eta_\text{act}) (Tafel)

Suponiendo Tafel para un solo electrodo de trabajo (catódico o anódico), con el otro electrodo “ideal” o absorbido en (V_\text{rev}).

### 3.1. Ecuación de Tafel

Para el electrodo activo:

[
\eta_\text{act}(j,T)
= \frac{RT}{\alpha,nF},\ln!\left(\frac{|j|}{j_0(T)}\right)
]

donde:

* (\eta_\text{act}): sobretensión de activación
* (\alpha): coeficiente de transferencia de carga (catódico o anódico, según reacción)
* (j_0(T)): densidad de corriente de intercambio a temperatura (T)
* (j): densidad de corriente impuesta
* (n): número de electrones (2 para HER)

Si quisieras distinguir cátodo y ánodo:

[
\eta_{\text{act,cat}}(j,T)
= \frac{RT}{\alpha_\text{cat} nF},\ln!\left(\frac{|j|}{j_{0,\text{cat}}(T)}\right)
]

[
\eta_{\text{act,án}}(j,T)
= \frac{RT}{\alpha_\text{án} nF},\ln!\left(\frac{|j|}{j_{0,\text{án}}(T)}\right)
]

y luego:

[
\eta_\text{act,tot} = \eta_{\text{act,cat}} + \eta_{\text{act,án}}
]

En tu proyecto puedes partir con:

* O bien considerar sólo el electrodo limitante (por ejemplo HER u OER, el que tenga cinética más lenta).
* O bien sumar ambas contribuciones.

### 3.2. Dependencia de (j_0) con temperatura (Arrhenius)

[
j_0(T)
= j_{0,\text{ref}},
\exp\left[
-\frac{E_a}{R}\left(\frac{1}{T} - \frac{1}{T_\text{ref}}\right)
\right]
]

**Por qué se usa**

* Tafel es la simplificación directa de Butler–Volmer en el régimen de sobrepotenciales moderados/altos (zona típica de operación de un electrolizador).
* Permite relacionar de forma simple (j) con (\eta_\text{act}) y capturar el efecto de temperatura a través de (j_0(T)) sin resolver exponentes positivos/negativos completos.

**Datos necesarios**

Por cada electrodo que modeles (HER y/o OER):

* (j_{0,\text{ref}}) a (T_\text{ref}) (del paper o ajustado desde la curva experimental).
* Energía de activación (E_a) para la reacción (del paper o de la literatura).
* Coeficiente de transferencia (\alpha) (o (\alpha_\text{cat}), (\alpha_\text{án})).
* Temperatura de referencia (T_\text{ref}) (298 K u otra).
* Temperatura de operación (T).

---

## 4. Pérdidas óhmicas (\eta_\text{ohm})

### 4.1. Relación básica

[
\eta_\text{ohm}(j,T) = j , R_\text{areal}(T)
]

donde

[
R_\text{areal}(T) = \sum_i R_{i,\text{areal}}(T)
]

y para cada componente (i) (membrana, electrolito, electrodos, contactos):

[
R_{i,\text{areal}}(T) = \frac{\delta_i}{\kappa_{i,\text{eff}}(T)}
]

* (\delta_i): espesor del componente (i) [m]
* (\kappa_{i,\text{eff}}(T)): conductividad efectiva (iónica o electrónica) [S/m]

Si quieres incluir dependencia de (\kappa) con (T):

[
\kappa_{i,\text{eff}}(T)
= \kappa_{i,\text{ref}},
\exp\left[
-\frac{E_{\kappa,i}}{R}\left(\frac{1}{T} - \frac{1}{T_\text{ref}}\right)
\right]
]

o bien una ley empírica tipo:

[
\kappa_{i,\text{eff}}(T) \approx a_i + b_i,T
]

**Por qué se usa**

Es la formulación estándar para pérdidas IR: resistencia total en serie de todos los componentes multiplicada por la densidad de corriente. En un modelo 0D no resuelves campo eléctrico interno, sólo un (R_\text{tot}) efectivo.

**Datos necesarios**

Por componente (i):

* Espesor (\delta_i) (m).
* Conductividad (\kappa_{i,\text{ref}}) (S/m) a una temperatura de referencia.
* Parámetros de la dependencia con (T) (energía de activación (E_{\kappa,i}) o coeficientes lineales (a_i, b_i)).
* (Opcional) Porosidad y factor de tortuosidad si quieres pasar de (\kappa) a (\kappa_\text{eff}).

---

## 5. Pérdidas de concentración (\eta_\text{conc}) (opcional)

Si decides incluir efectos de transporte de masa de forma simple (tipo “corriente límite”):

### 5.1. Corriente límite

[
j_\text{lim} = \frac{n F D_\text{eff} C_\text{bulk}}{\delta_\text{dif}}
]

* (D_\text{eff}): difusividad efectiva de la especie limitante (ej. (OH^-))
* (C_\text{bulk}): concentración en el volumen del electrolito
* (\delta_\text{dif}): espesor de la capa difusiva efectiva

### 5.2. Sobretensión de concentración

[
\eta_\text{conc}(j,T)
= -\frac{RT}{nF},\ln!\left(1 - \frac{j}{j_\text{lim}}\right)
]

**Por qué se usa**

Es una forma compacta de introducir el hecho de que, a altas corrientes, la especie reactante se agota en la superficie del electrodo y el potencial requerido aumenta fuertemente.

**Datos necesarios**

* Difusividad efectiva (D_\text{eff}) de la especie limitante (función de (T) y del electrolito).
* Concentración de esa especie en el volumen (C_\text{bulk}).
* Espesor de capa difusiva (\delta_\text{dif}) (se ajusta o se estima).

Si en esta primera versión quieres algo simple, puedes poner (\eta_\text{conc}=0) o sólo incluirla cuando (j) se acerca a la región alta de la curva.

---

## 6. Relación corriente–densidad, área y tiempo

Aunque tu modelo 0D de curva de polarización puede ser cuasi-estacionario (sin tiempo), es útil explicitar:

[
j = \frac{I}{A}
]

Si más adelante quieres incluir el tiempo (t) (por ejemplo, para ver degradación o cambios de temperatura):

* Balance de energía (para (T(t))).
* Balance de especies (para (C_i(t))), si incluyes transporte.

Por ahora, para la curva (V)–(j) estacionaria, basta con:

* Definir el área activa (A).
* Recorrer (j) en un rango (ej. 0–2 A/cm²).
* Para cada (j) y (T), calcular (V_\text{cell}(j,T)) con las ecuaciones anteriores.

---

## 7. Resumen compacto (qué ecuaciones y qué datos)

1. **Potencial reversible**

   * Ecuación:
     [
     V_\text{rev}(T) = -\frac{\Delta G(T)}{nF} \approx V_\text{rev}(T_0) + \frac{\Delta S^\circ}{nF}(T-T_0)
     ]
   * Datos: (\Delta G^\circ(T_0)) o (V_\text{rev}(T_0)), (\Delta S^\circ), (T).

2. **Activación (Tafel)**

   * Ecuación:
     [
     \eta_\text{act}(j,T)
     = \frac{RT}{\alpha nF}\ln\left(\frac{|j|}{j_0(T)}\right)
     ]
     [
     j_0(T) = j_{0,\text{ref}}\exp\left[-\frac{E_a}{R}\left(\frac{1}{T}-\frac{1}{T_\text{ref}}\right)\right]
     ]
   * Datos: (j_{0,\text{ref}}), (E_a), (\alpha), (T_\text{ref}), (T), (n).

3. **Óhmica (IR)**

   * Ecuación:
     [
     \eta_\text{ohm}(j,T) = j\sum_i \frac{\delta_i}{\kappa_{i,\text{eff}}(T)}
     ]
   * Datos: (\delta_i), (\kappa_{i,\text{ref}}), ley de (\kappa_{i,\text{eff}}(T)).

4. **Concentración (opcional)**

   * Ecuaciones:
     [
     j_\text{lim} = \frac{nF D_\text{eff} C_\text{bulk}}{\delta_\text{dif}}
     ]
     [
     \eta_\text{conc}(j,T)
     = -\frac{RT}{nF}\ln\left(1-\frac{j}{j_\text{lim}}\right)
     ]
   * Datos: (D_\text{eff}), (C_\text{bulk}), (\delta_\text{dif}).

5. **Curva de polarización final**

   * Ecuación:
     [
     V_\text{cell}(j,T)
     = V_\text{rev}(T) + \eta_\text{act}(j,T) + \eta_\text{ohm}(j,T) + \eta_\text{conc}(j,T)
     ]

Si quieres, en el siguiente paso puedo traducir este listado a una “especificación de código” en Python (inputs, outputs, estructura de funciones) para que quede directamente listo para implementar en tu simulador.
