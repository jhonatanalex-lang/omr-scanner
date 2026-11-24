"""
Generador paramétrico de Fichas OMR Oficiales Desglosables:
Especificaciones Oficiales:
  - Formato: A4 Apaisado (Landscape), desglosable en 2 mitades.
  - Mitad Izquierda (Identificación):
      * Placeholder para Logotipo institucional.
      * Campos manuscritos: Apellido Paterno, Apellido Materno, Nombres, Firma.
      * Código de Estudiante / DNI: Matriz de 8 columnas x 10 filas (0 al 9).
      * Código de barras Code128 de enlace unívoco.
      * 4 Marcadores fiduciarios en las esquinas.
  - Mitad Derecha (Respuestas):
      * Tipo / Tema de Examen: P, Q, R, S, T, U (6 burbujas).
      * 80 Preguntas con 5 alternativas (A, B, C, D, E), distribuidas en 4 columnas de 20 preguntas.
      * Código de barras Code128 de enlace idéntico.
      * 4 Marcadores fiduciarios en las esquinas.
  - Salida:
      * omr_sheet_master.pdf
      * template_coords.json (Mapa exacto normalizado al centroide de marcadores)
"""

import json
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128

MM = 72.0 / 25.4
PAGE_WIDTH, PAGE_HEIGHT = landscape(A4) # 297mm x 210mm (~841.89 x ~595.28 pt)

MARKER_SIZE = 7.5 * MM    # Cuadrados negros de 7.5mm x 7.5mm
BUBBLE_R = 1.9 * MM       # Radio de burbuja (~3.8mm de diámetro, óptimo para 80 preguntas)

def draw_fiducial_markers(c, x_min, y_min, x_max, y_max, size):
    """Dibuja 4 marcadores fiduciarios cuadrados sólidos en las esquinas."""
    c.setFillColor(colors.black)
    c.rect(x_min, y_min, size, size, fill=1, stroke=0)
    c.rect(x_max - size, y_min, size, size, fill=1, stroke=0)
    c.rect(x_min, y_max - size, size, size, fill=1, stroke=0)
    c.rect(x_max - size, y_max - size, size, size, fill=1, stroke=0)

def generate_omr_sheet(output_pdf="omr_sheet_master.pdf", output_json="template_coords.json", sheet_code="OMR-2026-0001"):
    c = canvas.Canvas(output_pdf, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    
    cut_x = PAGE_WIDTH / 2.0 # Línea central de corte (148.5 mm)
    
    # Línea central punteada de desglose
    c.setDash(3, 3)
    c.setStrokeColor(colors.gray)
    c.setLineWidth(0.7)
    c.line(cut_x, 10 * MM, cut_x, PAGE_HEIGHT - 10 * MM)
    c.setDash()
    
    c.setFont("Helvetica", 6.5)
    c.setFillColor(colors.gray)
    c.drawCentredString(cut_x, 6 * MM, "CORTE O DESGLOSE AQUÍ (LÍNEA DIVISORIA)")
    
    # =========================================================================
    # SECCIÓN 1: IDENTIFICACIÓN (MITAD IZQUIERDA)
    # Rango: [10mm, 10mm] a [cut_x - 5mm, PAGE_HEIGHT - 10mm]
    # Ancho sección: 133.5 mm, Alto: 190 mm
    # =========================================================================
    left_x_min = 10 * MM
    left_x_max = cut_x - 5 * MM
    left_y_min = 10 * MM
    left_y_max = PAGE_HEIGHT - 10 * MM
    
    draw_fiducial_markers(c, left_x_min, left_y_min, left_x_max, left_y_max, MARKER_SIZE)
    
    # Centros de referencia de marcadores para coordenadas relativas (0.0 a 1.0)
    id_ref_x0 = left_x_min + MARKER_SIZE / 2.0
    id_ref_y0 = left_y_min + MARKER_SIZE / 2.0
    id_ref_w = (left_x_max - MARKER_SIZE / 2.0) - id_ref_x0
    id_ref_h = (left_y_max - MARKER_SIZE / 2.0) - id_ref_y0
    
    # Placeholder de Logo Institucional
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.8)
    c.setFillColor(colors.whitesmoke)
    c.rect(left_x_min + 10 * MM, left_y_max - 18 * MM, 26 * MM, 14 * MM, fill=1, stroke=1)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(left_x_min + 23 * MM, left_y_max - 11.5 * MM, "[ LOGO ]")
    
    # Título y Código de barras de enlace
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(left_x_min + 39 * MM, left_y_max - 8 * MM, "FICHA DE IDENTIFICACIÓN")
    c.setFont("Helvetica", 7)
    c.drawString(left_x_min + 39 * MM, left_y_max - 12 * MM, "Rellene con lápiz 2B dentro del círculo")
    
    # Código de Barras Code128 en Identificación
    c.setFont("Helvetica-Bold", 7.5)
    c.drawRightString(left_x_max - 10 * MM, left_y_max - 5.5 * MM, f"CÓDIGO: {sheet_code}")
    barcode_id = code128.Code128(sheet_code, barHeight=6 * MM, barWidth=0.9, quiet=1)
    barcode_id.drawOn(c, left_x_max - 56 * MM, left_y_max - 14 * MM)
    
    # Bloque de Casillas de Nombres Manuscritos
    box_start_y = left_y_max - 23 * MM
    full_w = (left_x_max - left_x_min) - 20 * MM
    c.setLineWidth(0.7)
    c.setStrokeColor(colors.black)
    
    # Apellido Paterno
    c.setFont("Helvetica-Bold", 7)
    c.drawString(left_x_min + 10 * MM, box_start_y, "APELLIDO PATERNO:")
    c.rect(left_x_min + 10 * MM, box_start_y - 7.5 * MM, full_w, 6.5 * MM)
    
    # Apellido Materno
    c.drawString(left_x_min + 10 * MM, box_start_y - 10.5 * MM, "APELLIDO MATERNO:")
    c.rect(left_x_min + 10 * MM, box_start_y - 18 * MM, full_w, 6.5 * MM)
    
    # Nombres
    c.drawString(left_x_min + 10 * MM, box_start_y - 21 * MM, "NOMBRES:")
    c.rect(left_x_min + 10 * MM, box_start_y - 28.5 * MM, full_w, 6.5 * MM)
    
    # Matriz OMR de DNI / CÓDIGO (8 dígitos, 0 al 9)
    dni_base_x = left_x_min + 12 * MM
    dni_base_y = box_start_y - 35 * MM
    col_w = 7.5 * MM
    row_h = 6.2 * MM
    
    c.setFont("Helvetica-Bold", 8)
    c.drawString(dni_base_x, dni_base_y + 4 * MM, "CÓDIGO DE ESTUDIANTE / DNI")
    
    dni_bubbles = []
    c.setFont("Helvetica-Bold", 7)
    for col in range(8): # 8 dígitos
        cx = dni_base_x + col * col_w
        # Casilla superior para escribir el dígito a mano
        c.rect(cx - 2.8 * MM, dni_base_y - 2 * MM, 5.6 * MM, 5.2 * MM)
        
        for val in range(10): # 0 al 9
            cy = (dni_base_y - 8 * MM) - (val * row_h)
            c.circle(cx, cy, BUBBLE_R, stroke=1, fill=0)
            c.drawCentredString(cx, cy - 2.2, str(val))
            
            u = (cx - id_ref_x0) / id_ref_w
            v = (cy - id_ref_y0) / id_ref_h
            dni_bubbles.append({
                "digit_index": col,
                "value": val,
                "norm_x": round(u, 5),
                "norm_y": round(v, 5)
            })
            
    # Espacio para Firma del Postulante (al lado derecho de la matriz DNI)
    sign_x = dni_base_x + 8 * col_w + 5 * MM
    sign_w = (left_x_max - 10 * MM) - sign_x
    sign_h = 32 * MM
    sign_y = (dni_base_y - 8 * MM) - (9 * row_h)
    
    c.rect(sign_x, sign_y, sign_w, sign_h)
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(sign_x + sign_w / 2.0, sign_y + 4 * MM, "FIRMA DEL POSTULANTE")
    c.setDash(2, 2)
    c.line(sign_x + 3 * MM, sign_y + 9 * MM, sign_x + sign_w - 3 * MM, sign_y + 9 * MM)
    c.setDash()
    
    # =========================================================================
    # SECCIÓN 2: RESPUESTAS (MITAD DERECHA)
    # Rango: [cut_x + 5mm, 10mm] a [PAGE_WIDTH - 10mm, PAGE_HEIGHT - 10mm]
    # Ancho sección: 133.5 mm, Alto: 190 mm
    # =========================================================================
    right_x_min = cut_x + 5 * MM
    right_x_max = PAGE_WIDTH - 10 * MM
    right_y_min = 10 * MM
    right_y_max = PAGE_HEIGHT - 10 * MM
    
    draw_fiducial_markers(c, right_x_min, right_y_min, right_x_max, right_y_max, MARKER_SIZE)
    
    ans_ref_x0 = right_x_min + MARKER_SIZE / 2.0
    ans_ref_y0 = right_y_min + MARKER_SIZE / 2.0
    ans_ref_w = (right_x_max - MARKER_SIZE / 2.0) - ans_ref_x0
    ans_ref_h = (right_y_max - MARKER_SIZE / 2.0) - ans_ref_y0
    
    # Encabezado Respuestas
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(right_x_min + 10 * MM, right_y_max - 8 * MM, "HOJA DE RESPUESTAS")
    
    # Código de barras en Respuestas
    c.setFont("Helvetica-Bold", 7.5)
    c.drawRightString(right_x_max - 10 * MM, right_y_max - 5.5 * MM, f"CÓDIGO: {sheet_code}")
    barcode_ans = code128.Code128(sheet_code, barHeight=6 * MM, barWidth=0.9, quiet=1)
    barcode_ans.drawOn(c, right_x_max - 56 * MM, right_y_max - 14 * MM)
    
    # Bloque de TEMA / TIPO DE EXAMEN (P, Q, R, S, T, U)
    theme_y = right_y_max - 21 * MM
    theme_x = right_x_min + 10 * MM
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(theme_x, theme_y + 1 * MM, "TEMA:")
    
    themes = ['P', 'Q', 'R', 'S', 'T', 'U']
    theme_bubbles = []
    for t_idx, t_char in enumerate(themes):
        bx = theme_x + 14 * MM + t_idx * 5.8 * MM
        by = theme_y + 2 * MM
        c.circle(bx, by, BUBBLE_R, stroke=1, fill=0)
        c.drawCentredString(bx, by - 2.2, t_char)
        
        u = (bx - ans_ref_x0) / ans_ref_w
        v = (by - ans_ref_y0) / ans_ref_h
        theme_bubbles.append({
            "theme": t_char,
            "norm_x": round(u, 5),
            "norm_y": round(v, 5)
        })
        
    # Bloque de 80 Preguntas: 4 columnas de 20 preguntas
    options = ['A', 'B', 'C', 'D', 'E']
    opt_spacing = 4.2 * MM
    row_height = 5.8 * MM
    col_width = 28.5 * MM
    ans_start_y = right_y_max - 31 * MM
    ans_start_x = right_x_min + 9 * MM
    
    ans_bubbles = []
    
    for col_idx in range(4): # 4 columnas (0 a 3)
        col_x = ans_start_x + col_idx * col_width
        
        # Cabecera de columna (número de preguntas de la columna)
        c.setFont("Helvetica-Bold", 6.5)
        q_start = col_idx * 20 + 1
        q_end = col_idx * 20 + 20
        c.drawString(col_x, ans_start_y + 4 * MM, f"P.{q_start:02d}-{q_end:02d}")
        
        c.setFont("Helvetica-Bold", 6.5)
        for i in range(20): # 20 filas por columna
            q_num = col_idx * 20 + (i + 1)
            row_y = ans_start_y - (i * row_height)
            
            # Número de pregunta
            c.drawRightString(col_x + 4.5 * MM, row_y - 2.2, f"{q_num:02d}")
            
            # Opciones A, B, C, D, E
            for opt_idx, opt_char in enumerate(options):
                bx = col_x + 7.5 * MM + opt_idx * opt_spacing
                by = row_y
                c.circle(bx, by, BUBBLE_R, stroke=1, fill=0)
                c.drawCentredString(bx, by - 2.2, opt_char)
                
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
    print(f"✅ Ficha OMR Oficial de 80 Preguntas generada: {output_pdf}")
    
    # Exportación del archivo de mapeo JSON
    template_data = {
        "sheet_code": sheet_code,
        "format": "A4_landscape_80q",
        "bubble_radius_mm": 1.9,
        "marker_size_mm": 7.5,
        "sections": {
            "identification": {
                "num_digits": 8,
                "fields": ["apellido_paterno", "apellido_materno", "nombres", "firma"],
                "bubbles": dni_bubbles
            },
            "answers": {
                "total_questions": 80,
                "options": options,
                "theme_options": themes,
                "theme_bubbles": theme_bubbles,
                "bubbles": ans_bubbles
            }
        }
    }
    
    with open(output_json, "w", encoding="utf-8") as jf:
        json.dump(template_data, jf, indent=2)
    print(f"✅ Coordenadas oficiales exportadas: {output_json}")

if __name__ == "__main__":
    generate_omr_sheet()
