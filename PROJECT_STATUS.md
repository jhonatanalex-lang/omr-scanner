# Proyecto OMR - Calificación de Fichas Desglosables (Identificación y Respuestas)

## 📌 Resumen del Proyecto y Contexto
Sistema integral de grado de producción para el diseño, escaneo, lectura, calificación y conciliación de **hojas OMR (Optical Mark Recognition)** en exámenes masivos. Utiliza visión por computadora con OpenCV, decodificación de códigos de barras Code128, base de datos relacional SQLite y exportación ejecutiva a Excel.

---

## 🎯 Arquitectura Completa Implementada

### 1. Generador Paramétrico con Código de Barras (`generate_omr_sheet.py`)
- **Hoja A4 Apaisada:** Maquetada matemáticamente en milímetros con `reportlab`.
- **Línea de Trepado Central:** Permite el desglose físico entre Identificación y Respuestas.
- **8 Marcadores Fiduciarios:** Cuadrados de $8 \times 8 \text{ mm}$ en las 4 esquinas de cada mitad desglosada.
- **Enlace Unívoco por Código de Barras:** Genera códigos **Code128 nativos** con zona de silencio (*quiet zone*) en ambas secciones (`OMR-2026-XXXX`). Verificado y decodificable al 100% con `pyzbar`.
- **Salida:** `omr_sheet_master.pdf` y `template_coords.json`.

### 2. Motor de Visión por Computadora (`omr_core.py`)
- **Localización Fiduciaria:** Detección de marcadores cuadrados extremos tolerante a rotaciones y sombras.
- **Corrección Proyectiva Isométrica (`align_quad`):** Homografía de 4 puntos (`cv2.warpPerspective`) a resolución ortogonal fija.
- **Lectura de Burbujas Diferencial:** Clasificador por contraste relativo inmune a ruidos de impresión o borrones de lápiz.

### 3. Procesador por Lotes y Conciliación Relacional (`batch_processor.py`)
- Rasterizado ultra-rápido de lotes PDF con `PyMuPDF` (`fitz`).
- **Base de Datos SQLite:**
  - Registra fichas de identificación y respuestas por separado.
  - Conciliación relacional `JOIN` por `sheet_code`.
  - Calificación ponderada y detección de fichas huérfanas o dobles marcas.
- **Exportación Ejecutiva a Excel (`export_to_excel`):**
  - Genera archivos `.xlsx` estilizados con formato corporativo (cabecera azul marino, bordes, alineación y cálculo de puestos).

### 4. Aplicación de Escritorio Interactiva (`app_gui.py`)
- Desarrollada en Python nativo (`Tkinter` / `ttk`).
- Permite al docente:
  - Configurar puntaje por acierto y penalidad por error.
  - Cargar clave de examen personalizada con un clic.
  - Seleccionar el archivo PDF de fichas escaneadas mediante explorador de archivos.
  - Barra de progreso y tabla interactiva de resultados en vivo.
  - Botón de exportación directa a Excel.

---

## 🧪 Pruebas y Métricas de Rendimiento
- **Detección Fiduciaria:** 4 de 4 esquinas por sección detectadas sin falsos positivos.
- **Lectura de Código de Barras:** 100% de decodificación en ambas mitades escaneadas.
- **Exactitud OMR:** **100% de precisión** (40 de 40 preguntas identificadas correctamente y DNI de 8 dígitos decodificado sin errores).
- **Exportación Excel:** Verificada con `openpyxl`.

---

## 💻 Cómo Iniciar el Sistema en Cualquier Computadora
1. **Generar la Ficha Maestra:**
   ```bash
   python generate_omr_sheet.py
   ```
2. **Ejecutar la Prueba de Integración:**
   ```bash
   python test_pipeline.py
   ```
3. **Abrir la Aplicación de Escritorio:**
   ```bash
   python app_gui.py
   ```
