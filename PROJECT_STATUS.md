# Proyecto OMR - Calificación de Fichas Desglosables Oficiales (Versión 30/70)

## 📌 Resumen del Proyecto y Contexto
Sistema integral de grado de producción para el diseño, generación masiva serializada, escaneo, lectura, calificación y conciliación de **hojas OMR (Optical Mark Recognition)** en exámenes masivos. Cuenta con soporte oficial para fichas de 80 preguntas en proporción 30% / 70%, selección de tema (P, Q, R, S, T, U), DNI de 8 dígitos y códigos de barras Code128 con zona de silencio de seguridad fiduciaria.

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

## 🖨️ Generación Masiva Serializada (`generate_batch_sheets.py`)
- Permite generar un único PDF multipágina listo para enviar a la imprenta con N hojas correlativas (ej: 100, 300 o 500 exámenes).
- Cada página recibe su código único correlativo (`OMR-2026-0001`, `OMR-2026-0002`, etc.) impreso en código de barras en ambas mitades desglosables.

---

## 🧩 Calificación Multitema Automática (P, Q, R, S, T, U)
- El motor clasificador detecta automáticamente qué tema rellenó el postulante.
- Si el alumno marcó `R`, el sistema evalúa sus respuestas contra la clave del Tema `R`.
- Administrador gráfico integrado en la App para ver y editar las claves de cada uno de los 6 temas de forma independiente.
- Las actas de notas en Excel y SQLite registran la columna `Tema` para auditoría transparente.

---

## 💻 Aplicación de Escritorio Interactiva (`app_gui.py`)
La aplicación cuenta ahora con dos pestañas de trabajo:
1. **📊 Calificar Exámenes:**
   - Botón *"⚙️ Administrar Claves Multitema..."* con editor visual para los 6 temas.
   - Puntuación por acierto y penalidad configurable.
   - Procesamiento en lote de PDFs con barra de progreso.
   - Tabla interactiva con columna `Tema` y exportación a Excel (.xlsx).
2. **🖨️ Generar Hojas para Imprenta:**
   - Interfaz visual para ingresar prefijo, correlativo inicial y cantidad de hojas a generar.
   - Barra de progreso interactiva y guardado del PDF para imprenta.

Ejecutable mediante:
```cmd
cd /d "D:\COPIAR ZIPLANE"
python app_gui.py
```
