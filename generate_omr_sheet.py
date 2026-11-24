"""
Generador paramétrico de Fichas OMR Desglosables (Identificación + Respuestas)
Produce:
  1. omr_sheet_master.pdf (Hoja A4 apaisada lista para imprimir)
  2. template_coords.json (Mapa de coordenadas normalizadas para el motor de visión)
"""

import json
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas

# Dimensiones en puntos (1 pulgada = 72 pt, 1 mm = 72 / 25.4 pt)
MM = 72.0 / 25.4
PAGE_WIDTH, PAGE_HEIGHT = landscape(A4) # 297mm x 210mm (~841.89 x ~595.28 pt)

# Parámetros de diseño
MARKER_SIZE = 8 * MM      # 8mm x 8mm para esquinas fiduciarias
BUBBLE_R = 2.4 * MM       # Radio de la burbuja (~4.8 mm de diámetro)

def draw_fiducial_markers(c, x_min, y_min, x_max, y_max, size):
    """Dibuja 4 marcadores fiduciarios cuadrados sólidos en las 4 esquinas del área dada."""
    c.setFillColor(colors.black)
    # Bottom-Left
    c.rect(x_min, y_min, size, size, fill=1, stroke=0)
    # Bottom-Right
    c.rect(x_max - size, y_min, size, size, fill=1, stroke=0)
    # Top-Left
    c.rect(x_min, y_max - size, size, size, fill=1, stroke=0)
    # Top-Right
    c.rect(x_max - size, y_max - size, size, size, fill=1, stroke=0)

def generate_omr_sheet(output_pdf="omr_sheet_master.pdf", output_json="template_coords.json", sheet_code="OMR-2026-0001"):
    c = canvas.Canvas(output_pdf, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    
    # Línea central de corte/desglose
    cut_x = PAGE_WIDTH / 2.0
    c.setDash(3, 3)
    c.setStrokeColor(colors.gray)
    c.line(cut_x, 15 * MM, cut_x, PAGE_HEIGHT - 15 * MM)
    c.setDash() # Restaurar línea sólida
    
    # Texto guía de corte
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.gray)
    c.drawCentredString(cut_x, 8 * MM, "CORTE O DESGLOSE AQUÍ (LÍNEA DIVISORIA)")
    
    # =========================================================================
    # SECCIÓN 1: MITAD IZQUIERDA (IDENTIFICACIÓN)
    # Margen: [12mm, 12mm] a [cut_x - 6mm, PAGE_HEIGHT - 12mm]
    # =========================================================================
    left_x_min = 12 * MM
    left_x_max = cut_x - 6 * MM
    left_y_min = 12 * MM
    left_y_max = PAGE_HEIGHT - 12 * MM
    
    draw_fiducial_markers(c, left_x_min, left_y_min, left_x_max, left_y_max, MARKER_SIZE)
    
    # Encabezado Identificación
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.black)
    c.drawString(left_x_min + 12 * MM, left_y_max - 7 * MM, "FICHA DE IDENTIFICACIÓN")
    c.setFont("Helvetica", 8)
    c.drawString(left_x_min + 12 * MM, left_y_max - 11 * MM, "Llene completamente los círculos con lápiz 2B")
    
    # Código de Enlace en Identificación
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(left_x_max - 12 * MM, left_y_max - 7 * MM, f"CÓDIGO: {sheet_code}")
    
    # Bloque de datos escritos
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.8)
    c.rect(left_x_min + 12 * MM, left_y_max - 28 * MM, (left_x_max - left_x_min) - 24 * MM, 14 * MM)
    c.setFont("Helvetica", 7.5)
    c.drawString(left_x_min + 14 * MM, left_y_max - 18 * MM, "APELLIDOS Y NOMBRES: _____________________________________________")
    c.drawString(left_x_min + 14 * MM, left_y_max - 24 * MM, "AULA / SEDE: _____________________    FECHA: ____ / ____ / ________")
    
    # Matriz OMR de DNI / CÓDIGO (8 dígitos, números 0 al 9)
    dni_start_x = left_x_min + 20 * MM
    dni_start_y = left_y_max - 36 * MM
    col_w = 9.5 * MM
    row_h = 7.5 * MM
    
    c.setFont("Helvetica-Bold", 9)
    c.drawString(dni_start_x, dni_start_y + 4 * MM, "CÓDIGO DE ESTUDIANTE / DNI")
    
    # Centros de los marcadores fiduciarios como origen/referencia de coordenadas (0.0 a 1.0)
    # Bottom-Left marker center: (left_x_min + MARKER_SIZE/2, left_y_min + MARKER_SIZE/2)
    # Top-Right marker center: (left_x_max - MARKER_SIZE/2, left_y_max - MARKER_SIZE/2)
    id_ref_x0 = left_x_min + MARKER_SIZE / 2.0
    id_ref_y0 = left_y_min + MARKER_SIZE / 2.0
    id_ref_w = (left_x_max - MARKER_SIZE / 2.0) - id_ref_x0
    id_ref_h = (left_y_max - MARKER_SIZE / 2.0) - id_ref_y0
    
    dni_bubbles = []
    c.setFont("Helvetica-Bold", 8)
    for col in range(8): # 8 dígitos
        cx = dni_start_x + col * col_w
        # Encabezado de casilla cuadrada para escribir el número arriba
        c.rect(cx - 3.2 * MM, dni_start_y - 2 * MM, 6.4 * MM, 6 * MM)
        
        for val in range(10): # 0 al 9
            cy = (dni_start_y - 9 * MM) - (val * row_h)
            # Dibujar burbuja
            c.circle(cx, cy, BUBBLE_R, stroke=1, fill=0)
            c.drawCentredString(cx, cy - 2.5, str(val))
            
            # Guardar posición normalizada (0.0 a 1.0) relativa a los centros de los 4 marcadores
            u = (cx - id_ref_x0) / id_ref_w
            v = (cy - id_ref_y0) / id_ref_h
            dni_bubbles.append({
                "digit_index": col,
                "value": val,
                "norm_x": round(u, 5),
                "norm_y": round(v, 5)
            })
            
    # =========================================================================
    # SECCIÓN 2: MITAD DERECHA (RESPUESTAS)
    # Margen: [cut_x + 6mm, 12mm] a [PAGE_WIDTH - 12mm, PAGE_HEIGHT - 12mm]
    # =========================================================================
    right_x_min = cut_x + 6 * MM
    right_x_max = PAGE_WIDTH - 12 * MM
    right_y_min = 12 * MM
    right_y_max = PAGE_HEIGHT - 12 * MM
    
    draw_fiducial_markers(c, right_x_min, right_y_min, right_x_max, right_y_max, MARKER_SIZE)
    
    ans_ref_x0 = right_x_min + MARKER_SIZE / 2.0
    ans_ref_y0 = right_y_min + MARKER_SIZE / 2.0
    ans_ref_w = (right_x_max - MARKER_SIZE / 2.0) - ans_ref_x0
    ans_ref_h = (right_y_max - MARKER_SIZE / 2.0) - ans_ref_y0
    
    # Encabezado Respuestas
    c.setFont("Helvetica-Bold", 12)
    c.drawString(right_x_min + 12 * MM, right_y_max - 7 * MM, "HOJA DE RESPUESTAS")
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(right_x_max - 12 * MM, right_y_max - 7 * MM, f"CÓDIGO: {sheet_code}")
    
    # Columnas de Preguntas (Ejemplo: 40 Preguntas en 2 columnas de 20)
    options = ['A', 'B', 'C', 'D', 'E']
    opt_spacing = 5.2 * MM
    ans_row_h = 6.4 * MM
    
    ans_bubbles = []
    
    for col_idx in range(2):
        col_base_x = right_x_min + 15 * MM + col_idx * 45 * MM
        col_base_y = right_y_max - 24 * MM
        
        c.setFont("Helvetica-Bold", 8)
        for i in range(20):
            q_num = col_idx * 20 + (i + 1)
            row_y = col_base_y - (i * ans_row_h)
            
            # Número de pregunta
            c.drawString(col_base_x, row_y - 2.5, f"{q_num:02d}.")
            
            # Burbujas A, B, C, D, E
            for opt_idx, opt_char in enumerate(options):
                bx = col_base_x + 7.5 * MM + opt_idx * opt_spacing
                by = row_y
                c.circle(bx, by, BUBBLE_R, stroke=1, fill=0)
                c.drawCentredString(bx, by - 2.5, opt_char)
                
                u = (bx - ans_ref_x0) / ans_ref_w
                v = (by - ans_ref_y0) / ans_ref_h
                ans_bubbles.append({
                    "question": q_num,
                    "option": opt_char,
                    "norm_x": round(u, 5),
                    "norm_y": round(v, 5)
                })

    c.showPage()
    c.save()
    print(f"✅ PDF generado exitosamente: {output_pdf}")
    
    # Guardar esquema JSON
    template_data = {
        "sheet_code": sheet_code,
        "format": "A4_landscape",
        "bubble_radius_mm": 2.4,
        "marker_size_mm": 8.0,
        "sections": {
            "identification": {
                "num_digits": 8,
                "bubbles": dni_bubbles
            },
            "answers": {
                "total_questions": 40,
                "options": options,
                "bubbles": ans_bubbles
            }
        }
    }
    
    with open(output_json, "w", encoding="utf-8") as jf:
        json.dump(template_data, jf, indent=2)
    print(f"✅ Coordenadas guardadas exitosamente: {output_json}")

if __name__ == "__main__":
    generate_omr_sheet()
