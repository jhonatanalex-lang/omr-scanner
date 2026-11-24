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

## 🎯 Especificaciones de la Ficha Optimizada (`omr_sheet_master.pdf`)

### 1. Dimensiones y Proporción 30% / 70%:
- **Formato:** Hoja estándar **A4 Apaisada (297 mm x 210 mm)**.
- **Línea de Desglose / Corte:** Ubicada en **X = 95 mm** (deja ~32% para Identificación y ~68% para Respuestas).
- **Aislamiento Fiduciario:** Códigos de barras y tiras binarias aisladas con zona de silencio para 0% de interferencia con los 4 marcadores de esquina.

### 2. Sección de Identificación (Mitad Izquierda - 30%):
- **Encabezado:** Título y Código de barras Code128.
- **Campos Manuscritos:** Casillas delimitadas para Apellido Paterno, Apellido Materno y Nombres.
- **Matriz OMR de Código / DNI:** 8 columnas $\times$ 10 filas (0 al 9) con casillas superiores para escribir el número con lápiz.
- **Espacio de Firma:** Recuadro con línea de firma ubicado ergonómicamente en la parte inferior.
- **Tira Binaria Antifraude:** 16 bits ópticos pre-rellenados.

### 3. Sección de Respuestas (Mitad Derecha - 70%):
- **Tira Binaria Antifraude:** 16 bits ópticos gemelos idénticos a los de identificación.
- **Tema / Tipo de Examen:** 6 alternativas visibles (**P, Q, R, S, T, U**).
- **80 Preguntas con alternativas A, B, C, D, E:**
  - 4 columnas generosas con espacio interlineal cómodo ($7.6 \text{ mm}$ de separación por fila).
  - Burbujas de mayor diámetro ($4.2 \text{ mm}$ de diámetro) fáciles de rellenar para el estudiante.
- **Código de Barras Code128:** Idéntico al de identificación.

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
