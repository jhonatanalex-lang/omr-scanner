# Proyecto OMR - Calificación de Fichas Desglosables (Identificación y Respuestas)

## 📌 Resumen del Proyecto y Contexto
Sistema completo de escaneo, lectura y calificación de **hojas OMR (Optical Mark Recognition)** para exámenes masivos, utilizando procesamiento de visión por computadora (OpenCV y Machine Learning) y conciliación relacional mediante base de datos SQLite.

---

## 🎯 Arquitectura Implementada y Funcional (Estado Actual)

### 1. Generador Paramétrico de Fichas Vectoriales (`generate_omr_sheet.py`)
- Produce **`omr_sheet_master.pdf`** en formato A4 apaisado milimétricamente exacto mediante `reportlab`.
- **Línea de Trepado Central:** Permite el desglose físico entre la sección de Identificación (izquierda) y la sección de Respuestas (derecha).
- **8 Marcadores Fiduciarios:** Cuadrados negros sólidos de $8 \times 8 \text{ mm}$ en las 4 esquinas de cada mitad independiente.
- **Exportación Paramétrica:** Genera automáticamente **`template_coords.json`** con las coordenadas `(u, v)` normalizadas relativas al centroide de los marcadores fiduciarios.

### 2. Motor de Visión por Computadora (`omr_core.py`)
- **Detección Fiduciaria Robusta:** Localiza mediante contornos convexos de ratio de aspecto 1.0 los 4 marcadores extremos de cualquier mitad escaneada.
- **Corrección de Perspectiva Cuadrangular (`align_quad` / `cv2.warpPerspective`):** Elimina cualquier inclinación, ángulo de escaneo o deformación de la hoja a una resolución ortogonal fija.
- **Algoritmo de Decisión de Burbujas:** Detección por densidad relativa de píxeles y umbral diferencial de contraste, inmune a bordes de círculos impresos o borrones de lápiz.

### 3. Procesador por Lotes y Conciliación (`batch_processor.py`)
- Rasterización de páginas PDF de alta velocidad con `PyMuPDF` (`fitz`).
- **Base de Datos SQLite (`omr_results.db`):**
  - Tabla `identification_sheets`: Registra el `sheet_code` correlativo y el `student_id` (DNI).
  - Tabla `answer_sheets`: Registra el `sheet_code` correlativo y las respuestas en formato JSON.
  - Tabla `graded_results`: Conciliación relacional `JOIN` por `sheet_code`, calificación contra la clave del profesor y detección automática de fichas huérfanas.

### 4. Prueba Integral de Extremo a Extremo (`test_pipeline.py`)
- ✅ Rasterización a 300 DPI (3508x2481 px).
- ✅ Simulación de llenado de DNI y 40 preguntas.
- ✅ Simulación de desglose físico (corte de imagen en 2 partes).
- ✅ Detección fiduciaria de las 4 esquinas por mitad.
- ✅ **Precisión obtenida: 100% en DNI ('74839201') y 100% en las 40 preguntas (40/40)**.
- ✅ Conciliación exitosa y calificación en SQLite.

---

## 🚀 Próximos Pasos (Hoja de Ruta)
1. **Interfaz de Usuario de Escritorio (Desktop GUI):**
   - Panel visual en PySide6 / PyQt para seleccionar un archivo PDF escaneado con cientos de páginas.
   - Vista previa con auditoría visual (resaltado en verde/rojo de burbujas leídas).
   - Exportación de notas a Excel (XLSX).
2. **Generación con Código de Barras / QR:**
   - Integrar generación dinámica de códigos de barras (Code128) con serialización automática para exámenes masivos.
3. **Versión Móvil (Fase Futura):**
   - Interfaz de cámara con *viewfinder* en vivo que detecte los 4 cuadros verdes antes de disparar.

---

## 💡 Instrucción para Antigravity en otra máquina
Si clonas este repositorio en la computadora de tu trabajo, simplemente di:
> *"He clonado este repositorio. Lee `PROJECT_STATUS.md` y continuemos con la Interfaz de Escritorio o la exportación a Excel."*
