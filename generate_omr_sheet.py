"""
Generador paramétrico de Fichas OMR Oficiales Desglosables (Versión 30/70 con Tiras Ópticas Binarias)
Incorpora:
  - Tiras gemelas binarias OMR flanqueando la línea de corte central (X = 95mm).
  - 16 bits ópticos pre-rellenados (burbuja negra sólida = bit 1, círculo blanco = bit 0).
  - Permite codificar hasta 65,535 correlativos únicos sin posibilidad de fraude por intercambio.
  - Al cortar, cada mitad conserva exactamente su tira binaria gemela.
"""

import json
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128

MM = 72.0 / 25.4
PAGE_WIDTH, PAGE_HEIGHT = landscape(A4) # 297mm x 210mm (~841.89 x ~595.28 pt)

MARKER_SIZE = 7.5 * MM    # Cuadrados negros fiduciarios de 7.5mm x 7.5mm
BUBBLE_R = 2.1 * MM       # Radio de burbuja de respuestas (~4.2mm de diámetro)
SYNC_BIT_R = 1.6 * MM     # Radio de los bits de sincronización (~3.2mm de diámetro)

def draw_fiducial_markers(c, x_min, y_min, x_max, y_max, size):
    """Dibuja los 4 marcadores de esquina fiduciarios aislados."""
    c.setFillColor(colors.black)
    c.rect(x_min, y_min, size, size, fill=1, stroke=0)
    c.rect(x_max - size, y_min, size, size, fill=1, stroke=0)
    c.rect(x_min, y_max - size, size, size, fill=1, stroke=0)
    c.rect(x_max - size, y_max - size, size, size, fill=1, stroke=0)

def draw_sync_strip(c, center_x, start_y, bit_spacing, num_bits, bit_val_int):
    """
    Dibuja una columna vertical de bits ópticos (16 bits).
    Las burbujas con bit=1 se rellenan en negro sólido.
    Las burbujas con bit=0 quedan vacías.
    """
    strip_h = (num_bits - 1) * bit_spacing + 8 * MM
    strip_w = 6.0 * MM
    
    # Recuadro exterior protector en color rosa/rojo suave
    c.setStrokeColor(colors.HexColor("#E06666"))
    c.setLineWidth(0.6)
    c.roundRect(center_x - strip_w / 2.0, start_y - (num_bits - 1) * bit_spacing - 4 * MM, strip_w, strip_h, 3 * MM, stroke=1, fill=0)
    
    # Texto vertical de advertencia
    c.saveState()
    c.setFont("Helvetica-Bold", 4.5)
    c.setFillColor(colors.HexColor("#CC0000"))
    c.translate(center_x - 3.8 * MM, start_y - ((num_bits - 1) * bit_spacing) / 2.0)
    c.rotate(90)
    c.drawCentredString(0, 0, "NO ESCRIBA EN ESTA AREA")
    c.restoreState()
    
    bit_bubbles = []
    for bit_idx in range(num_bits):
        cy = start_y - bit_idx * bit_spacing
        is_on = (bit_val_int >> (num_bits - 1 - bit_idx)) & 1
        
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.6)
        if is_on:
            c.setFillColor(colors.black)
            c.circle(center_x, cy, SYNC_BIT_R, stroke=1, fill=1)
        else:
            c.setFillColor(colors.white)
            c.circle(center_x, cy, SYNC_BIT_R, stroke=1, fill=0)
            
        bit_bubbles.append({
            "bit_index": bit_idx,
            "x": center_x,
            "y": cy,
            "is_on": is_on
        })
    return bit_bubbles

def generate_omr_sheet(
    output_pdf="omr_sheet_master.pdf", 
    output_json="template_coords.json", 
    sheet_code="OMR-2026-0001",
    sheet_id_number=1
):
    c = canvas.Canvas(output_pdf, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    
    cut_x = 95.0 * MM # Línea de desglose
    
    # Línea central punteada de desglose
    c.setDash(3, 3)
    c.setStrokeColor(colors.gray)
    c.setLineWidth(0.6)
    c.line(cut_x, 8 * MM, cut_x, PAGE_HEIGHT - 8 * MM)
    c.setDash()
    
    c.setFont("Helvetica", 6)
    c.setFillColor(colors.gray)
    c.drawCentredString(cut_x, 4.5 * MM, "LÍNEA DE DESGLOSE / CORTE")
    
    # Marcador fiduciario central superior e inferior sobre la línea de corte (como en la muestra)
    c.setFillColor(colors.black)
    c.rect(cut_x - 1.5 * MM, PAGE_HEIGHT - 12 * MM, 3 * MM, 3 * MM, fill=1, stroke=0)
    c.rect(cut_x - 1.5 * MM, 9 * MM, 3 * MM, 3 * MM, fill=1, stroke=0)
    
    # =========================================================================
    # SECCIÓN 1: IDENTIFICACIÓN (30%)
    # =========================================================================
    left_x_min = 8 * MM
    left_x_max = cut_x - 4 * MM
    left_y_min = 8 * MM
    left_y_max = PAGE_HEIGHT - 8 * MM
    
    draw_fiducial_markers(c, left_x_min, left_y_min, left_x_max, left_y_max, MARKER_SIZE)
    
    id_ref_x0 = left_x_min + MARKER_SIZE / 2.0
    id_ref_y0 = left_y_min + MARKER_SIZE / 2.0
    id_ref_w = (left_x_max - MARKER_SIZE / 2.0) - id_ref_x0
    id_ref_h = (left_y_max - MARKER_SIZE / 2.0) - id_ref_y0
    
    # Encabezado Identificación
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawCentredString((left_x_min + left_x_max - 5 * MM) / 2.0, left_y_max - 5.5 * MM, "FICHA DE IDENTIFICACIÓN")
    
    # Código de barras centrado
    barcode_id = code128.Code128(sheet_code, barHeight=5.5 * MM, barWidth=0.75, quiet=0)
    barcode_w = barcode_id.width
    barcode_x_id = ((left_x_min + left_x_max - 5 * MM) / 2.0) - (barcode_w / 2.0)
    barcode_id.drawOn(c, barcode_x_id, left_y_max - 13.5 * MM)
    
    c.setFont("Helvetica", 6)
    c.drawCentredString((left_x_min + left_x_max - 5 * MM) / 2.0, left_y_max - 16 * MM, f"CÓDIGO: {sheet_code}")
    
    # Bloque Manuscrito
    box_w = (left_x_max - left_x_min) - 22 * MM
    box_x = left_x_min + 9 * MM
    cur_y = left_y_max - 20 * MM
    
    c.setLineWidth(0.6)
    c.setStrokeColor(colors.black)
    
    c.setFont("Helvetica-Bold", 6.5)
    c.drawString(box_x, cur_y, "APELLIDO PATERNO:")
    cur_y -= 5.5 * MM
    c.rect(box_x, cur_y, box_w, 5.0 * MM)
    
    cur_y -= 3.5 * MM
    c.drawString(box_x, cur_y, "APELLIDO MATERNO:")
    cur_y -= 5.5 * MM
    c.rect(box_x, cur_y, box_w, 5.0 * MM)
    
    cur_y -= 3.5 * MM
    c.drawString(box_x, cur_y, "NOMBRES:")
    cur_y -= 5.5 * MM
    c.rect(box_x, cur_y, box_w, 5.0 * MM)
    
    # Matriz DNI (8 dígitos)
    dni_base_x = box_x + 1.0 * MM
    dni_base_y = cur_y - 8 * MM
    col_w = 6.8 * MM
    row_h = 6.0 * MM
    
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString((left_x_min + left_x_max - 8 * MM) / 2.0, dni_base_y + 3.5 * MM, "CÓDIGO / DNI")
    
    dni_bubbles = []
    c.setFont("Helvetica-Bold", 6.5)
    for col in range(8):
        cx = dni_base_x + col * col_w
        c.rect(cx - 2.8 * MM, dni_base_y - 2 * MM, 5.6 * MM, 5.0 * MM)
        
        for val in range(10):
            cy = (dni_base_y - 7.5 * MM) - (val * row_h)
            c.circle(cx, cy, BUBBLE_R, stroke=1, fill=0)
            c.drawCentredString(cx, cy - 2.0, str(val))
            
            u = (cx - id_ref_x0) / id_ref_w
            v = (cy - id_ref_y0) / id_ref_h
            dni_bubbles.append({
                "digit_index": col,
                "value": val,
                "norm_x": round(u, 5),
                "norm_y": round(v, 5)
            })
            
    # Firma del postulante
    sign_y = (dni_base_y - 7.5 * MM) - (9.5 * row_h) - 18 * MM
    sign_h = 16 * MM
    c.rect(box_x, sign_y, box_w, sign_h)
    c.setDash(2, 2)
    c.line(box_x + 4 * MM, sign_y + 6 * MM, box_x + box_w - 4 * MM, sign_y + 6 * MM)
    c.setDash()
    c.setFont("Helvetica", 6)
    c.drawCentredString(box_x + box_w / 2.0, sign_y + 2.5 * MM, "FIRMA DEL POSTULANTE")

    # =========================================================================
    # TIRAS ÓPTICAS BINARIAS (EN EL HORIZONTE DE DESGLOSE)
    # =========================================================================
    NUM_SYNC_BITS = 16
    SYNC_SPACING = 6.2 * MM
    SYNC_START_Y = PAGE_HEIGHT - 38 * MM
    
    # 1. Tira Binaria en Identificación (al borde derecho de la mitad izquierda)
    left_sync_x = cut_x - 8 * MM
    left_bits = draw_sync_strip(c, left_sync_x, SYNC_START_Y, SYNC_SPACING, NUM_SYNC_BITS, sheet_id_number)
    
    left_sync_coords = []
    for lb in left_bits:
        u = (lb["x"] - id_ref_x0) / id_ref_w
        v = (lb["y"] - id_ref_y0) / id_ref_h
        left_sync_coords.append({"bit_index": lb["bit_index"], "norm_x": round(u, 5), "norm_y": round(v, 5)})

    # =========================================================================
    # SECCIÓN 2: RESPUESTAS (70%)
    # =========================================================================
    right_x_min = cut_x + 4 * MM
    right_x_max = PAGE_WIDTH - 8 * MM
    right_y_min = 8 * MM
    right_y_max = PAGE_HEIGHT - 8 * MM
    
    draw_fiducial_markers(c, right_x_min, right_y_min, right_x_max, right_y_max, MARKER_SIZE)
    
    ans_ref_x0 = right_x_min + MARKER_SIZE / 2.0
    ans_ref_y0 = right_y_min + MARKER_SIZE / 2.0
    ans_ref_w = (right_x_max - MARKER_SIZE / 2.0) - ans_ref_x0
    ans_ref_h = (right_y_max - MARKER_SIZE / 2.0) - ans_ref_y0
    
    # 2. Tira Binaria en Respuestas (al borde izquierdo de la mitad derecha, simétrica gemela)
    right_sync_x = cut_x + 8 * MM
    right_bits = draw_sync_strip(c, right_sync_x, SYNC_START_Y, SYNC_SPACING, NUM_SYNC_BITS, sheet_id_number)
    
    right_sync_coords = []
    for rb in right_bits:
        u = (rb["x"] - ans_ref_x0) / ans_ref_w
        v = (rb["y"] - ans_ref_y0) / ans_ref_h
        right_sync_coords.append({"bit_index": rb["bit_index"], "norm_x": round(u, 5), "norm_y": round(v, 5)})
        
    # Encabezado Respuestas
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(right_x_min + 16 * MM, right_y_max - 6 * MM, "HOJA DE RESPUESTAS")
    
    barcode_ans = code128.Code128(sheet_code, barHeight=5.5 * MM, barWidth=0.8, quiet=0)
    barcode_ans_x = right_x_max - 52 * MM
    barcode_ans.drawOn(c, barcode_ans_x, right_y_max - 13.5 * MM)
    c.setFont("Helvetica-Bold", 6.5)
    c.drawRightString(right_x_max - 12 * MM, right_y_max - 6 * MM, f"CÓDIGO: {sheet_code}")
    
    # Tema (P, Q, R, S, T, U)
    theme_y = right_y_max - 18 * MM
    theme_x = right_x_min + 16 * MM
    c.setFont("Helvetica-Bold", 8)
    c.drawString(theme_x, theme_y + 1 * MM, "TEMA:")
    
    themes = ['P', 'Q', 'R', 'S', 'T', 'U']
    theme_bubbles = []
    c.setFont("Helvetica-Bold", 7.5)
    for t_idx, t_char in enumerate(themes):
        bx = theme_x + 16 * MM + t_idx * 7.5 * MM
        by = theme_y + 2.2 * MM
        c.circle(bx, by, BUBBLE_R, stroke=1, fill=0)
        c.drawCentredString(bx, by - 2.2, t_char)
        
        u = (bx - ans_ref_x0) / ans_ref_w
        v = (by - ans_ref_y0) / ans_ref_h
        theme_bubbles.append({
            "theme": t_char,
            "norm_x": round(u, 5),
            "norm_y": round(v, 5)
        })
        
    # 80 Preguntas en 4 columnas
    options = ['A', 'B', 'C', 'D', 'E']
    opt_spacing = 5.0 * MM
    row_height = 7.6 * MM
    col_width = 42.5 * MM
    ans_start_y = right_y_max - 28 * MM
    ans_start_x = right_x_min + 15 * MM
    
    ans_bubbles = []
    for col_idx in range(4):
        col_x = ans_start_x + col_idx * col_width
        q_start = col_idx * 20 + 1
        q_end = col_idx * 20 + 20
        
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(col_x + 2 * MM, ans_start_y + 4.5 * MM, f"PREGUNTAS {q_start:02d} - {q_end:02d}")
        
        c.setStrokeColor(colors.lightgrey)
        c.setLineWidth(0.4)
        c.line(col_x, ans_start_y + 2.5 * MM, col_x + 38 * MM, ans_start_y + 2.5 * MM)
        
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.6)
        
        for i in range(20):
            q_num = col_idx * 20 + (i + 1)
            row_y = ans_start_y - 2 * MM - (i * row_height)
            
            c.setFont("Helvetica-Bold", 7)
            c.drawRightString(col_x + 6.5 * MM, row_y - 2.2, f"{q_num:02d}")
            
            c.setFont("Helvetica-Bold", 7.5)
            for opt_idx, opt_char in enumerate(options):
                bx = col_x + 10.5 * MM + opt_idx * opt_spacing
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
    print(f"✅ Ficha OMR Oficial con Tiras Binarias Antifraude generada: {output_pdf}")
    
    template_data = {
        "sheet_code": sheet_code,
        "sheet_id_number": sheet_id_number,
        "format": "A4_landscape_80q_30_70_sync",
        "bubble_radius_mm": 2.1,
        "sync_bit_radius_mm": 1.6,
        "marker_size_mm": 7.5,
        "sections": {
            "identification": {
                "num_digits": 8,
                "fields": ["apellido_paterno", "apellido_materno", "nombres", "firma"],
                "sync_bits": left_sync_coords,
                "bubbles": dni_bubbles
            },
            "answers": {
                "total_questions": 80,
                "options": options,
                "theme_options": themes,
                "theme_bubbles": theme_bubbles,
                "sync_bits": right_sync_coords,
                "bubbles": ans_bubbles
            }
        }
    }
    
    with open(output_json, "w", encoding="utf-8") as jf:
        json.dump(template_data, jf, indent=2)
    print(f"✅ Coordenadas maestras actualizadas con tiras ópticas: {output_json}")

if __name__ == "__main__":
    generate_omr_sheet(sheet_code="OMR-2026-0030", sheet_id_number=30)
