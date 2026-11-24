# Proyecto OMR - Calificación de Fichas Desglosables Oficiales (Suite Completa)

## 📌 Resumen del Proyecto y Contexto
Sistema integral de grado de producción para el diseño, generación masiva serializada, escaneo, lectura, calificación, conciliación y auditoría visual de **hojas OMR (Optical Mark Recognition)** en exámenes masivos. Cuenta con soporte oficial para fichas de 80 preguntas en proporción 30% / 70%, selección de tema (P, Q, R, S, T, U), DNI de 8 dígitos, códigos de barras Code128 con zona de silencio de seguridad fiduciaria y auditor visual interactivo.

---

## ⚖️ Sistema de Puntuación Institucional y Escala Vigesimal (0 a 20)

### 1. Tratamiento de Dobles Marcas y Preguntas:
- **Respuesta Correcta:** **+5.0 puntos**.
- **Respuesta Incorrecta:** **0.0 puntos**.
- **Pregunta en Blanco:** **+1.0 punto**.
- **Doble Marca / Múltiple:** Si el postulante rellena más de una opción en la misma pregunta, el sistema la detecta como `MULTIPLE_MARK`, la invalida y le asigna **0.0 puntos** (no bonifica como blanca ni suma acierto).

### 2. Conversión Matemática a Nota Vigesimal (0 al 20):
- **Puntaje Bruto Máximo Posible:** $80 \text{ preguntas} \times 5\text{ pts} = 400.0\text{ puntos}$.
- **Fórmula de Conversión:**
  $$\text{Nota Final (0 - 20)} = \left( \frac{\text{Puntaje Bruto Obtenido}}{400.0} \right) \times 20.0$$
  *(Ejemplo: 300 puntos brutos equivalen exactamente a una nota de 15.00 sobre 20).*

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

## 🔍 Auditor Visual Interactivo Docente (`app_gui.py`)
- **Doble clic en la tabla:** Abre inmediatamente la ventana de auditoría visual con la foto escaneada real del estudiante.
- **Resaltado por Colores sobre la imagen real:**
  - 🟢 **Verde:** Opción marcada correcta.
  - 🔴 **Rojo:** Opción marcada incorrecta.
  - 🔵 **Azul:** La respuesta que era correcta.
  - 🟠 **Naranja:** Marcas dobles o tachones detectados para arbitraje manual del docente.

---

## 💻 Aplicación de Escritorio Interactiva (`app_gui.py`)
Ejecutable mediante:
```cmd
cd /d "D:\COPIAR ZIPLANE"
python app_gui.py
```
Permite calificar lotes, ver desgloses de Buenas (+5), Malas (0), Blancas (+1), Dobles (0), Puntaje Bruto y Nota (0-20), además de exportar a Excel.
