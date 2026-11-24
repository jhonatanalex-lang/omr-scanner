# Proyecto OMR - Calificación de Fichas Desglosables Oficiales

## 📌 Resumen del Proyecto y Contexto
Sistema integral de grado de producción para el diseño, escaneo, lectura, calificación y conciliación de **hojas OMR (Optical Mark Recognition)** en exámenes masivos. Cuenta con soporte oficial para fichas de 80 preguntas, selección de tema/tipo de prueba (P, Q, R, S, T, U), DNI de 8 dígitos, casillas de datos manuscritos y código de barras Code128 de enlace unívoco.

---

## 🎯 Especificaciones Oficiales de la Ficha (`omr_sheet_master.pdf`)

### 1. Sección de Identificación (Mitad Izquierda):
- **Placeholder de Logotipo Institucional:** Cuadrante superior reservado para el logo oficial de la institución.
- **Campos Manuscritos:** Casillas delimitadas independientes para:
  - Apellido Paterno
  - Apellido Materno
  - Nombres
- **Código de Estudiante / DNI:** Matriz numérica OMR de 8 columnas por 10 filas (0 al 9) con casillas superiores para escribir el número.
- **Espacio de Firma:** Recuadro delimitado para la firma del postulante (sin huella dactilar para evitar manchas accidentales en las burbujas).
- **Código de Barras Code128:** Serializado y decodificable automáticamente con `pyzbar`.
- **4 Marcadores Fiduciarios:** Cuadrados negros sólidos de $7.5 \times 7.5 \text{ mm}$ en las 4 esquinas.

### 2. Sección de Respuestas (Mitad Derecha):
- **Tema / Tipo de Examen:** 6 burbujas para opciones **P, Q, R, S, T, U**.
- **80 Preguntas con 5 Alternativas (A, B, C, D, E):**
  - Distribución optimizada en **4 columnas de 20 preguntas** cada una.
  - Columna 1: Preguntas 01 al 20
  - Columna 2: Preguntas 21 al 40
  - Columna 3: Preguntas 41 al 60
  - Columna 4: Preguntas 61 al 80
- **Código de Barras Code128:** Enlace idéntico al de la sección de identificación.
- **4 Marcadores Fiduciarios:** Cuadrados negros sólidos de $7.5 \times 7.5 \text{ mm}$ en las 4 esquinas.

---

## 🧪 Pruebas y Métricas de Rendimiento Verificadas
Ejecutadas mediante `test_pipeline.py` simulando escaneo real a 300 DPI y corte físico:
- **Lectura de Código de Barras:** Identificación y Respuestas decodificadas al 100% (`OMR-2026-0001`).
- **DNI Estudiante:** `46291035` decodificado al **100%**.
- **Tema de Examen:** `Q` detectado al **100%**.
- **Preguntas:** **80 de 80 preguntas reconocidas con exactitud (100.0%)**.
- **Conciliación en Base de Datos:** Registrada y calificada exitosamente en `omr_results.db`.
- **Exportación Excel:** Reporte generado en `resultados_80_preguntas.xlsx`.

---

## 💻 Aplicación de Escritorio (`app_gui.py`)
Ejecutable mediante:
```cmd
cd /d "D:\COPIAR ZIPLANE"
python app_gui.py
```
Permite cargar la clave de 80 preguntas, procesar el lote escaneado y exportar el acta de notas a Excel.
