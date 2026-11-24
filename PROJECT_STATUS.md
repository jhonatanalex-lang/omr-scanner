# Proyecto OMR - Calificación de Fichas Desglosables Oficiales (Suite Completa)

## 📌 Resumen del Proyecto y Contexto
Sistema integral de grado de producción para el diseño, generación masiva serializada, escaneo, lectura, calificación, conciliación y auditoría visual de **hojas OMR (Optical Mark Recognition)** en exámenes masivos. Cuenta con soporte oficial para fichas de 80 preguntas en proporción 30% / 70%, selección de tema (P, Q, R, S, T, U), DNI de 8 dígitos, códigos de barras Code128 con zona de silencio de seguridad fiduciaria y auditor visual interactivo.

---

## 🎯 Calibración de Umbral para Distinguir Grafito vs. Tipografía Impresa
- **El problema de la letra 'B':** En la tipografía impresa, la letra `B` tiene dos bucles cerrados y un trazo vertical grueso que ocupan un ~29% de píxeles negros incluso estando completamente vacía, mientras que letras más delgadas como la `C` tienen ~23%.
- **Solución de Precisión:**
  - El umbral mínimo de activación se calibró a **0.48 de llenado con una diferencia mínima de 0.15** frente a la segunda opción.
  - Las preguntas vacías (como la 68 a la 80) ahora se clasifican limpiamente como `BLANK` (En Blanco) con 100% de fiabilidad.
  - Una pregunta en blanco solo muestra el círculo **azul** en la opción correcta según la clave del docente, sin anillos naranjas ni falsos rojos.

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
Permite calificar lotes, ver desgloses analíticos y abrir el auditor visual en alta resolución con doble clic.
