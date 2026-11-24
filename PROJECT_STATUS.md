# Proyecto OMR - Calificación de Fichas Desglosables Oficiales (Versión 30/70)

## 📌 Resumen del Proyecto y Contexto
Sistema integral de grado de producción para el diseño, escaneo, lectura, calificación y conciliación de **hojas OMR (Optical Mark Recognition)** en exámenes masivos. Cuenta con soporte oficial para fichas de 80 preguntas en proporción 30% / 70%, selección de tema (P, Q, R, S, T, U), DNI de 8 dígitos y códigos de barras Code128 con zona de silencio de seguridad fiduciaria.

---

## 🎯 Especificaciones de la Ficha Optimizada (`omr_sheet_master.pdf`)

### 1. Dimensiones y Proporción 30% / 70%:
- **Formato:** Hoja estándar **A4 Apaisada (297 mm x 210 mm)**.
- **Línea de Desglose / Corte:** Ubicada en **X = 95 mm** (deja ~32% para Identificación y ~68% para Respuestas).
- **Aislamiento Fiduciario:** Los códigos de barras Code128 se ubicaron en zonas interiores protegidas con amplio margen de separación respecto a los marcadores de esquina, garantizando detección fiduciaria con 0% de interferencia.

### 2. Sección de Identificación (Mitad Izquierda - 30%):
- **Encabezado:** Título y Código de barras Code128 centrado.
- **Campos Manuscritos:** Casillas delimitadas para Apellido Paterno, Apellido Materno y Nombres.
- **Matriz OMR de Código / DNI:** 8 columnas $\times$ 10 filas (0 al 9) con casillas superiores para escribir el número con lápiz.
- **Espacio de Firma:** Recuadro con línea de firma ubicado ergonómicamente en la parte inferior.
- **4 Marcadores Fiduciarios:** Cuadrados de $7.5 \times 7.5 \text{ mm}$ en las 4 esquinas.

### 3. Sección de Respuestas (Mitad Derecha - 70%):
- **Espacio Amplio y Cómodo:** Ocupa casi el 70% del ancho de la hoja A4.
- **Tema / Tipo de Examen:** 6 alternativas visibles (**P, Q, R, S, T, U**).
- **80 Preguntas con alternativas A, B, C, D, E:**
  - 4 columnas generosas con espacio interlineal cómodo ($7.6 \text{ mm}$ de separación por fila).
  - Burbujas de mayor diámetro ($4.2 \text{ mm}$ de diámetro) fáciles de rellenar para el estudiante.
- **Código de Barras Code128:** Idéntico al de identificación para el cruce relacional ciego.
- **4 Marcadores Fiduciarios:** Cuadrados de $7.5 \times 7.5 \text{ mm}$ en las 4 esquinas.

---

## 🧪 Pruebas y Métricas Verificadas
Ejecutadas con `test_pipeline.py` simulando escaneo real a 300 DPI y corte físico:
- **Detección Fiduciaria:** Exactamente 4 de 4 esquinas detectadas en ambas mitades (0 interferencia con el código de barras).
- **Lectura de Código de Barras:** Identificación y Respuestas decodificadas al 100% (`OMR-2026-0001`).
- **DNI Estudiante:** `72910483` decodificado al **100%**.
- **Tema de Examen:** `R` detectado al **100%**.
- **Preguntas:** **80 de 80 preguntas reconocidas con exactitud (100.0%)**.
- **Conciliación en Base de Datos:** `MATCHED` y calificada en SQLite.

---

## 💻 Aplicación de Escritorio (`app_gui.py`)
Ejecutable mediante:
```cmd
cd /d "D:\COPIAR ZIPLANE"
python app_gui.py
```
Permite cargar la clave de 80 preguntas, procesar el lote escaneado y exportar el acta de notas a Excel.
