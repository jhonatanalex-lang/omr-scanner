# Proyecto OMR - Calificación de Fichas Desglosables (Identificación y Respuestas)

## 📌 Resumen del Proyecto y Contexto
Este proyecto tiene como objetivo desarrollar un sistema completo de escaneo, lectura y calificación de **hojas OMR (Optical Mark Recognition)** para exámenes masivos, utilizando procesamiento de visión por computadora (OpenCV y Machine Learning).

### 🎯 Características Principales
1. **Ficha OMR Dividida en 2 Partes Desglosables:**
   - **Mitad Izquierda (Identificación):** Datos del postulante, DNI / Código de estudiante en burbujas, aula y código correlativo/de barras.
   - **Mitad Derecha (Respuestas):** Opciones de respuestas (A, B, C, D, E) y el mismo código correlativo/de barras para calificación ciega anónima.
2. **Método de Captura Híbrido:**
   - Captura en vivo mediante cámara de teléfono celular (con visor de encuadre en pantalla).
   - Procesamiento en bloque/lotes (*batch*) desde escáner de escritorio (ADF / cama plana) en archivos PDF o imágenes.
3. **Módulo de Emparejamiento (Conciliación):**
   - El sistema procesa de forma independiente las fichas de identificación y las de respuestas.
   - Ambas mitades se unen automáticamente mediante el código interno / correlativo (impreso en código de barras o QR en ambas mitades).

---

## 🔍 Hallazgos de Ingeniería Inversa (Análisis de ZipGrade APK)
Se realizó la inspección de la arquitectura interna de `zipgrade.apk` para extraer las mejores prácticas de visión por computadora:

1. **Núcleo de Visión en C++ (`libmixed_sample.so`):**
   - La lógica no corre en Java/Kotlin, sino en C++ con OpenCV compilado bajo la clase `SheetReader`.
   - **Detección Fiduciaria:** Localiza 4 marcadores de esquina cuadrados (`calculateFiducialTargets`, `calculateFiducialPoints`, `FindContours`).
   - **Perspectiva:** Aplica matriz de homografía (`matTransformToFiducials`, `homographyTransform`) para aplanar y corregir la inclinación de la hoja.
   - **Clasificación de Burbujas por Machine Learning:**
     - En lugar de simples umbrales fijos que fallan con sombras o lápices claros, usa modelos **SVM (Support Vector Machine)** con kernel RBF creados con `libsvm`:
       - `svmsingle.model` (clasificación de burbuja única).
       - `svmcombo.model` (clasificación combinada).
       - `svmglare.model` (detección y compensación de reflejos/brillos de flash o luz).

---

## 📐 Regla Crítica de Diseño para Fichas Desglosables
Al cortar la hoja física en dos partes independientes:
- **Cada mitad debe contar obligatoriamente con sus propios 4 marcadores fiduciarios en las esquinas** (8 marcadores en total en la hoja sin cortar). Si solo hubiera 4 en la hoja completa, al desglosarla se perderían 2 esquinas por mitad y la cámara no podría aplicar la corrección de perspectiva.
- **Código de Enlace:** Un código de barras (Code128) o código QR pre-impreso idéntico en ambas secciones.

---

## 🚀 Próximos Pasos Técnicos a Realizar
1. **Generador de la Plantilla Maestra en PDF:**
   - Script (ej. Python con ReportLab) para generar el formato vectorial exacto (en milímetros) de la hoja desglosable.
   - Exportación de las coordenadas exactas de las burbujas (`template.json`).
2. **Motor de Visión OMR (Python + OpenCV):**
   - Detección de los 4 marcadores de esquina.
   - Corrección de perspectiva cuadrangular (`warpPerspective`).
   - Lectura del código de barras / QR de enlace.
   - Extracción de intensidades y detección de marcas en las burbujas.
3. **Módulo de Conciliación y Calificación:**
   - Base de datos local (SQLite) para registrar fichas de identificación y fichas de respuestas.
   - Comparación contra clave de respuestas y emisión de reportes.

---

## 💡 Instrucción para Antigravity en otra máquina
Si abres este proyecto en otra computadora con Antigravity, puedes iniciar diciendo:
> *"He clonado/copiado este repositorio. Lee el archivo `PROJECT_STATUS.md` para entender el estado del proyecto y continuemos implementando el Paso 1 (Generador de plantilla OMR)."*
