

---

## **1\. Ecuaciones del Modelo y Dependencia Térmica**

### **1.1. Voltaje Ideal (Vid​)**

Corresponde al potencial reversible de Nernst .

Vid​(T,p)=V∘(T)+2FRT​ln(aH2​O​pH2​​⋅pO2​0.5​​)

* **Dependencia de Temperatura (T):**  
  * **Término Nernst:** El término nFRT​ es directamente proporcional a la temperatura (T en Kelvin).  
  * **Potencial Estándar (V∘(T)):** El potencial estándar en sí depende de la temperatura, basado en la energía libre de Gibbs: V∘(T)=−nFΔG∘(T)​.  
  * **Cálculo de ΔG∘(T):** Se puede calcular para cualquier T (si T es Top​) usando la T de referencia (T\_ref \= 298.15 K) y asumiendo ΔH∘ y ΔS∘ constantes (o usando polinomios termodinámicos):  
     ΔG∘(Top​)=ΔH∘(Tref​)−Top​⋅ΔS∘(Tref​)  
  * **Valor a 25°C (298.15 K):** Vid​≈1.23 V (usando LHV, como indica tu proyecto).  
  * 

### **1.2. Sobrepotencial de Activación (ηact​)**

Pérdidas cinéticas en el ánodo (OER) y cátodo (HER), modeladas con la ecuación de Tafel . Se suman ambas contribuciones.

ηact​(i,T)=ηact,an​(i,T)+ηact,cat​(i,T)  
ηact,k​(i,T)=αk​nk​FRT​ln(i0,k​(T)i​)

*(Donde k \= `an` o `cat`)*

* **Dependencia de Temperatura (T):**  
  * **Pendiente de Tafel:** El término αnFRT​ (que forma el parámetro 'b' de Tafel) es directamente proporcional a T.  
  * **Corriente de Intercambio (i0​(T)):** Es el parámetro cinético clave y **depende fuertemente de la temperatura** según la ecuación de Arrhenius:  
  * i0,k​(Top​)=i0,k,ref​⋅exp\[R−Ea,k​​(Top​1​−Tref​1​)\]

### **1.3. Sobrepotencial Óhmico (ηohm​)**

Pérdidas por resistencia (electrolito, membrana, contactos) . Se modela con la Ley de Ohm.

ηohm​(i,T)=i⋅Rohmic​(T)

* **Dependencia de Temperatura (T):**  
  * **Resistencia (Rohmic​):** La resistencia iónica (del electrolito y la membrana PEM) disminuye al aumentar la temperatura. Se modela a través de la conductividad (κ), que sigue una ley de Arrhenius:  
  * κ(Top​)=κref​⋅exp\[R−Ea,κ​​(Top​1​−Tref​1​)\]  
  * La resistencia se calcula como Rohmic​(T)=κ(T)tmem​​+Rcontact​+Relectrolito​.

### **1.4. Sobrepotencial de Concentración (ηconc​)**

Pérdidas por transporte de masa (bloqueo por burbujas, difusión de reactivos) . Se modela con un término de corriente límite (iL​) .

ηconc​(i,T)=nFRT​ln(iL​−iiL​​)

(Nota: Tu documento muestra c⋅ln(…). Ese factor c está relacionado con nFRT​)

* **Dependencia de Temperatura (T):**  
  * El término nFRT​ es directamente proporcional a T.  
  * La corriente límite (iL​) también depende de T, ya que la difusión de gases/iones (D) aumenta con la temperatura (a menudo modelado con una relación tipo Arrhenius o Stokes-Einstein).

---

## **2\. Organización de Parámetros**

A continuación, se clasifican los parámetros necesarios para tu código, basados en las listas de tu proyecto .

### **Tabla 1: Constantes Físicas**

| Parámetro | Símbolo | Valor (Ejemplo) | Fuente |
| :---- | :---- | :---- | :---- |
| Constante de Faraday | F | 96485 C/mol |  |
| Constante de los Gases | R | 8.314 J/(mol K) |  |

### **Tabla 2: Variables de Simulación**

| Parámetro | Símbolo | Descripción | Fuente |
| :---- | :---- | :---- | :---- |
| **Variable de Entrada** | i | Densidad de corriente (barrido, p.ej., 0 a 4 A/cm²) |  |
| **Variable de Salida** | Vcelda​ | Voltaje total de la celda (V) |  |

### **Tabla 3: Parámetros Fijos (Condiciones Operativas y Geometría)**

| Parámetro | Símbolo | Valor (Ejemplo) | Fuente |
| :---- | :---- | :---- | :---- |
| Temperatura de Operación | Top​ | 298.15 K (25°C) o 353.15 K (80°C) |  |
| Temperatura de Referencia | Tref​ | 298.15 K (25°C) |  |
| Presión (Total) | p | 1.01325 bar (o 1 bar) |  |
| Presión Parcial H2​ | pH2​​ | 1 bar (asumido) |  |
| Presión Parcial O2​ | pO2​​ | 1 bar (asumido) |  |
| Actividad del Agua | aH2​O​ | 1 (para electrolito líquido) |  |
| Electrones (Global) | n | 2 mol e- / mol H2​O |  |
| Espesor de Membrana | tmem​ | (Valor específico, p.ej., 50 µm) |  |

### **Tabla 4: Parámetros Clave del Modelo (Ajustables)**

Estos son los valores que definirán la forma de tu curva de polarización. Debes ajustarlos para que coincidan con tus datos de validación (Figura 4f1 ).

| Parámetro | Símbolo | Descripción | Dependencia de T |
| :---- | :---- | :---- | :---- |
| **Termodinámicos** |  |  |  |
| Potencial Estándar (Ref) | V∘(Tref​) | 1.23 V (a 25°C) | (Se usa para calcular V∘(Top​)) |
| Entalpía de Reacción | ΔH∘ | (Valor std., p.ej., 285.8 kJ/mol) | (Se usa para calcular V∘(Top​)) |
| Entropía de Reacción | ΔS∘ | (Valor std., p.ej., 0.163 kJ/mol·K) | (Se usa para calcular V∘(Top​)) |
| **Cinéticos (Activación)** |  |  |  |
| i0​ Ánodo (Ref) | i0,an,ref​ | (Valor de ajuste, p.ej., 10−9 A/cm2) | Define i0,an​ en Tref​ |
| i0​ Cátodo (Ref) | i0,cat,ref​ | (Valor de ajuste, p.ej., 10−3 A/cm2) | Define i0,cat​ en Tref​ |
| Energía Activ. (OER) | Ea,an​ | (Valor de ajuste, p.ej., 40-70 kJ/mol) | **Controla Δi0​ con T** |
| Energía Activ. (HER) | Ea,cat​ | (Valor de ajuste, p.ej., 20-40 kJ/mol) | **Controla Δi0​ con T** |
| Coef. Transf. Ánodo | αan​ | (Valor de ajuste, p.ej., 0.5) | (Generalmente asumido indep. de T) |
| Coef. Transf. Cátodo | αcat​ | (Valor de ajuste, p.ej., 0.5) | (Generalmente asumido indep. de T) |
| **Óhmicos** |  |  |  |
| Conductividad (Ref) | κref​ | (Valor de ajuste, p.ej., 0.1 S/cm) | Define κ en Tref​ |
| Energía Activ. (Cond.) | Ea,κ​ | (Valor de ajuste, p.ej., 10-20 kJ/mol) | **Controla Δκ con T** |
| Resistencia Contacto | Rcontact​ | (Valor de ajuste, Ω⋅cm2) | (Generalmente asumido indep. de T) |
| **Transporte (Concentración)** |  |  |  |
| Corriente Límite | iL​ | (Valor de ajuste, p.ej., \> 4 A/cm²) | (Depende de T, puede requerir Ea​ propio) |

