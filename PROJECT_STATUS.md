# Proyecto OMR - Calificación de Fichas Desglosables Oficiales (Suite Completa con Tiras Ópticas Antifraude)

## 📌 Resumen del Proyecto y Contexto
Sistema integral de grado de producción para el diseño, generación masiva serializada, escaneo, lectura, calificación, conciliación y auditoría visual de **hojas OMR (Optical Mark Recognition)** en exámenes masivos. Cuenta con soporte oficial para fichas de 80 preguntas en proporción 30% / 70%, selección de tema (P, Q, R, S, T, U), DNI de 8 dígitos, códigos de barras Code128 y **tiras ópticas binarias gemelas antifraude** a lo largo de la línea de desglose.

---

## 🔒 Mecanismo de Seguridad Antifraude por Intercambio de Fichas (Tiras Ópticas Gemelas)

### 1. El Problema Resuelto:
Si dos postulantes coludidos intentan intercambiar bajo la mesa sus fichas de respuestas después de que el docente recogió las identificaciones, el sistema neutraliza el intento de fraude de inmediato.

### 2. La Solución Técnica Implementada:
- A lo largo de la línea de corte central ($X = 95\text{ mm}$), se dibujan **dos columnas verticales gemelas de 16 bits ópticos**:
  - Una columna en la ficha de Identificación (borde derecho).
  - Una columna idéntica en la ficha de Respuestas (borde izquierdo).
  - Texto delimitador: *"NO ESCRIBA EN ESTA ÁREA"*.
- **Codificación en bits OMR:**
  - Las burbujas con bit = 1 se pre-rellenan en negro sólido al imprimir.
  - Las burbujas con bit = 0 quedan vacías.
  - Permite codificar hasta $2^{16} = 65,535$ correlativos únicos en bits.
- **Validación Matemática en el Motor (`read_sync_strip`):**
  - El motor lee el número binario de la mitad izquierda (`num_l`).
  - El motor lee el número binario de la mitad derecha (`num_r`).
  - **Condición de Integridad:** $\text{num\_l} == \text{num\_r}$.
  - Si un estudiante intercambia su hoja con otro, sus números binarios no coincidirán y el sistema emitirá la alerta automática: **`FRAUDE (Hojas de Respuestas Intercambiadas)`**.

---

## 🎯 Especificaciones de la Ficha Oficial UNSAAC (`omr_sheet_master.pdf`)

### 1. Dimensiones y Proporción 30% / 70%:
- **Institución:** Universidad Nacional de San Antonio Abad del Cusco (UNSAAC).
- **Identidad Visual:** Escudo oficial centrado en ambas mitades, paleta carmesí / guinda institucional (`#7A1C24`) con acentos en tinte suave (`#F9F1F1`) y bordes redondeados ergonómicos.
- **Formato:** Hoja estándar **A4 Apaisada (297 mm x 210 mm)**.
- **Línea de Desglose / Corte:** Ubicada en **X = 95 mm** (deja ~32% para Identificación y ~68% para Respuestas).
- **Aislamiento Fiduciario:** 4 marcadores de esquina negros aislados en cada mitad con zona de silencio total (0% interferencia).

### 2. Sección de Identificación (Mitad Izquierda - 30%):
- **Encabezado:** Escudo oficial de la UNSAAC y título: `UNIVERSIDAD NACIONAL DE SAN ANTONIO ABAD DEL CUSCO`, seguido del banner `HOJA DE IDENTIFICACIÓN`.
- **Campos Manuscritos:** Casillas redondeadas (`roundRect`) con borde guinda institucional para Apellido Paterno, Apellido Materno y Nombres.
- **Matriz OMR de Código / DNI:** Banner `NÚMERO DE DNI`, casillas redondeadas para escritura manuscrita y 8 columnas $\times$ 10 filas (0 al 9) de burbujas.
- **Cuadro de Instrucciones y Ejemplos:** Banner guinda con recomendaciones de llenado de DNI y ejemplos gráficos (`CORRECTO ●`, `INCORRECTO ✔ ✖ ◐`).
- **Espacio de Firma:** Recuadro redondeado con línea de puntos: `FIRMA DEL POSTULANTE (dentro del cuadro)`.
- **Tira Binaria Antifraude:** 16 bits ópticos pre-rellenados y código vertical correlativo.

### 3. Sección de Respuestas (Mitad Derecha - 70%):
- **Encabezado:** Escudo oficial de la UNSAAC, títulos `UNIVERSIDAD NACIONAL DE SAN ANTONIO ABAD DEL CUSCO` y `HOJA ÓPTICA DE EVALUACIÓN ACADÉMICA`.
- **Badges:** Banner redondeado `HOJA DE RESPUESTAS` y selector de `TIPO DE TEMA` (**P, Q, R, S, T, U**).
- **80 Preguntas con Franjas Alternadas (Zebra Striping):**
  - 4 columnas de 20 preguntas (1-20, 21-40, 41-60, 61-80).
  - Cada fila cuenta con una **franja horizontal delimitadora** alternada (filas pares con tinte tenue `#F9F1F1` y filas impares en blanco) para evitar que la vista del estudiante se desplace a otra fila.
  - Opciones de respuesta `A, B, C, D, E` y numeración en negrita guinda.
- **Banner Inferior de Instrucciones Oficiales:** 6 reglas numeradas según el modelo oficial de examen y guía de `USE SÓLO LÁPIZ 2B` con ejemplos de marcado.
- **Tira Binaria Antifraude:** Idéntica y gemela a la de identificación.

---

## ⚖️ Sistema de Puntuación Institucional y Escala Vigesimal (0 a 20)
- **Buena:** +5.0 puntos.
- **Mala:** 0.0 puntos.
- **En Blanco:** +1.0 punto.
- **Doble Marca:** 0.0 puntos (anulada).
- **Escala Vigesimal:** $\text{Nota} = (\text{Puntaje Bruto} / 400.0) \times 20.0$.

---

## 💻 Aplicación de Escritorio Interactiva (`app_gui.py`)
Ejecutable mediante:
```cmd
cd /d "D:\COPIAR ZIPLANE"
python app_gui.py
```
Permite calificar lotes, generar hojas masivas para imprenta, auditar en alta resolución con doble clic y exportar actas a Excel.
