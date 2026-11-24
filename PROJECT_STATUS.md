# Proyecto OMR - Calificación de Fichas Desglosables Oficiales (Suite Completa)

## 📌 Resumen del Proyecto y Contexto
Sistema integral de grado de producción para el diseño, generación masiva serializada, escaneo, lectura, calificación, conciliación y auditoría visual de **hojas OMR (Optical Mark Recognition)** en exámenes masivos. Cuenta con soporte oficial para fichas de 80 preguntas en proporción 30% / 70%, selección de tema (P, Q, R, S, T, U), DNI de 8 dígitos, códigos de barras Code128 con zona de silencio de seguridad fiduciaria y auditor visual interactivo.

---

## 🎯 Pipeline de Procesamiento por Lotes (`process_scanned_pdf`)
- **Ingesta de PDFs Multipágina:** El sistema abre el archivo PDF seleccionado, rasteriza cada página a 300 DPI y evalúa:
  - Detección automática de si la página es la hoja completa A4 o mitades desglosadas.
  - Decodificación del código de barras Code128 en cada mitad (`pyzbar`).
  - Detección de los 4 marcadores de esquina fiduciarios y corrección de perspectiva cuadrangular.
  - Extracción y registro del DNI en `identification_sheets`.
  - Extracción y registro del Tema y las 80 respuestas en `answer_sheets`.
  - Conciliación relacional `JOIN` y calificación contra la clave del tema correspondiente.

---

## 🧪 Validación con Ficha Real del Usuario (`CPO-2027-0030`)
- **Código de Barras:** `CPO-2027-0030` leído exitosamente al 100%.
- **DNI:** `01111111` reconocido al 100%.
- **Tema:** `SIN_TEMA` (identificado correctamente, el alumno no marcó tema).
- **Conciliación:** Estado `MATCHED (Calificada)`.

---

## 💻 Aplicación de Escritorio Interactiva (`app_gui.py`)
Ejecutable mediante:
```cmd
cd /d "D:\COPIAR ZIPLANE"
python app_gui.py
```
Permite seleccionar el PDF escaneado, ver el avance en la barra de progreso, visualizar las notas en la tabla y exportar el acta en Excel (.xlsx).
