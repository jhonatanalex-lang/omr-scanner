"""
Generador Masivo Serializado de Fichas OMR Oficiales (30/70)
Permite generar un único PDF listo para imprenta/fotocopiadora con N páginas,
donde cada página contiene un correlativo único (ej: OMR-2026-0001 a OMR-2026-0500)
con su respectivo código de barras Code128 en ambas mitades desglosables.
"""

import os
import json
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128

MM = 72.0 / 25.4
PAGE_WIDTH, PAGE_HEIGHT = landscape(A4) # 297mm x 210mm (~841.89 x ~595.28 pt)

MARKER_SIZE = 7.5 * MM    # Cuadrados negros fiduciarios de 7.5mm x 7.5mm
BUBBLE_R = 2.1 * MM       # Radio de burbuja (~4.2mm de diámetro)

def draw_fiducial_markers(c, x_min, y_min, x_max, y_max, size):
    """Dibuja los 4 marcadores de esquina fiduciarios aislados."""
    c.setFillColor(colors.black)
    c.rect(x_min, y_min, size, size, fill=1, stroke=0)
    c.rect(x_max - size, y_min, size, size, fill=1, stroke=0)
    c.rect(x_min, y_max - size, size, size, fill=1, stroke=0)
    c.rect(x_max - size, y_max - size, size, size, fill=1, stroke=0)

def draw_single_omr_page(c, sheet_code, coords_cache=None):
    """Dibuja una hoja completa A4 apaisada (30% Identificación / 70% Respuestas)."""
    cut_x = 95.0 * MM
    
    # Línea central punteada de desglose
    c.setDash(3, 3)
    c.setStrokeColor(colors.gray)
    c.setLineWidth(0.6)
    c.line(cut_x, 8 * MM, cut_x, PAGE_HEIGHT - 8 * MM)
    c.setDash()
    
    c.setFont("Helvetica", 6)
    c.setFillColor(colors.gray)
    c.drawCentredString(cut_x, 4.5 * MM, "LÍNEA DE DESGLOSE / CORTE")
    
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
    c.drawCentredString((left_x_min + left_x_max) / 2.0, left_y_max - 5.5 * MM, "FICHA DE IDENTIFICACIÓN")
    
    # Código de barras centrado
    barcode_id = code128.Code128(sheet_code, barHeight=5.5 * MM, barWidth=0.75, quiet=0)
    barcode_w = barcode_id.width
    barcode_x_id = ((left_x_min + left_x_max) / 2.0) - (barcode_w / 2.0)
    barcode_id.drawOn(c, barcode_x_id, left_y_max - 13.5 * MM)
    
    c.setFont("Helvetica", 6)
    c.drawCentredString((left_x_min + left_x_max) / 2.0, left_y_max - 16 * MM, f"CÓDIGO: {sheet_code}")
    
    # Bloque Manuscrito
    box_w = (left_x_max - left_x_min) - 18 * MM
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
    dni_base_x = box_x + 1.5 * MM
    dni_base_y = cur_y - 8 * MM
    col_w = 7.6 * MM
    row_h = 6.0 * MM
    
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString((left_x_min + left_x_max) / 2.0, dni_base_y + 3.5 * MM, "CÓDIGO / DNI")
    
    dni_bubbles = []
    c.setFont("Helvetica-Bold", 6.5)
    for col in range(8):
        cx = dni_base_x + col * col_w
        c.rect(cx - 2.8 * MM, dni_base_y - 2 * MM, 5.6 * MM, 5.0 * MM)
        
        for val in range(10):
            cy = (dni_base_y - 7.5 * MM) - (val * row_h)
            c.circle(cx, cy, BUBBLE_R, stroke=1, fill=0)
            c.drawCentredString(cx, cy - 2.0, str(val))
            
            if coords_cache is not None and len(coords_cache["identification"]) < 80:
                u = (cx - id_ref_x0) / id_ref_w
                v = (cy - id_ref_y0) / id_ref_h
                coords_cache["identification"].append({
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
    
    # Encabezado Respuestas
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(right_x_min + 12 * MM, right_y_max - 6 * MM, "HOJA DE RESPUESTAS")
    
    barcode_ans = code128.Code128(sheet_code, barHeight=5.5 * MM, barWidth=0.8, quiet=0)
    barcode_ans_x = right_x_max - 52 * MM
    barcode_ans.drawOn(c, barcode_ans_x, right_y_max - 13.5 * MM)
    c.setFont("Helvetica-Bold", 6.5)
    c.drawRightString(right_x_max - 12 * MM, right_y_max - 6 * MM, f"CÓDIGO: {sheet_code}")
    
    # Tema (P, Q, R, S, T, U)
    theme_y = right_y_max - 18 * MM
    theme_x = right_x_min + 12 * MM
    c.setFont("Helvetica-Bold", 8)
    c.drawString(theme_x, theme_y + 1 * MM, "TEMA:")
    
    themes = ['P', 'Q', 'R', 'S', 'T', 'U']
    c.setFont("Helvetica-Bold", 7.5)
    for t_idx, t_char in enumerate(themes):
        bx = theme_x + 16 * MM + t_idx * 7.5 * MM
        by = theme_y + 2.2 * MM
        c.circle(bx, by, BUBBLE_R, stroke=1, fill=0)
        c.drawCentredString(bx, by - 2.2, t_char)
        
        if coords_cache is not None and len(coords_cache["themes"]) < 6:
            u = (bx - ans_ref_x0) / ans_ref_w
            v = (by - ans_ref_y0) / ans_ref_h
            coords_cache["themes"].append({
                "theme": t_char,
                "norm_x": round(u, 5),
                "norm_y": round(v, 5)
            })
            
    # 80 Preguntas en 4 columnas
    options = ['A', 'B', 'C', 'D', 'E']
    opt_spacing = 5.2 * MM
    row_height = 7.6 * MM
    col_width = 44.5 * MM
    ans_start_y = right_y_max - 28 * MM
    ans_start_x = right_x_min + 11 * MM
    
    for col_idx in range(4):
        col_x = ans_start_x + col_idx * col_width
        q_start = col_idx * 20 + 1
        q_end = col_idx * 20 + 20
        
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(col_x + 2 * MM, ans_start_y + 4.5 * MM, f"PREGUNTAS {q_start:02d} - {q_end:02d}")
        
        c.setStrokeColor(colors.lightgrey)
        c.setLineWidth(0.4)
        c.line(col_x, ans_start_y + 2.5 * MM, col_x + 39 * MM, ans_start_y + 2.5 * MM)
        
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
                
                if coords_cache is not None and len(coords_cache["answers"]) < 400:
                    u = (bx - ans_ref_x0) / ans_ref_w
                    v = (by - ans_ref_y0) / ans_ref_h
                    coords_cache["answers"].append({
                        "question": q_num,
                        "option": opt_char,
                        "norm_x": round(u, 5),
                        "norm_y": round(v, 5)
                    })

def generate_mass_omr_sheets(
    output_pdf="lote_fichas_impresion.pdf",
    output_json="template_coords.json",
    prefix="OMR-2026",
    start_num=1,
    quantity=50,
    progress_callback=None
):
    """
    Genera un archivo PDF con 'quantity' páginas numeradas correlativamente.
    Ejemplo: OMR-2026-0001 a OMR-2026-0050.
    """
    c = canvas.Canvas(output_pdf, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    coords_cache = {"identification": [], "themes": [], "answers": []}
    
    print(f"Iniciando generación de {quantity} fichas OMR serializadas ({prefix}-{start_num:04d} a {prefix}-{(start_num + quantity - 1):04d})...")
    
    for idx in range(quantity):
        current_num = start_num + idx
        sheet_code = f"{prefix}-{current_num:04d}"
        
        # En la primera página capturamos las coordenadas fijas
        cache = coords_cache if idx == 0 else None
        draw_single_omr_page(c, sheet_code, cache)
        c.showPage()
        
        if progress_callback:
            progress_callback(idx + 1, quantity)
            
    c.save()
    print(f"✅ Lote de {quantity} páginas generado exitosamente en: {output_pdf}")
    
    # Guardar / actualizar template_coords.json
    template_data = {
        "format": "A4_landscape_80q_30_70",
        "bubble_radius_mm": 2.1,
        "marker_size_mm": 7.5,
        "sections": {
            "identification": {
                "num_digits": 8,
                "fields": ["apellido_paterno", "apellido_materno", "nombres", "firma"],
                "bubbles": coords_cache["identification"]
            },
            "answers": {
                "total_questions": 80,
                "options": ['A', 'B', 'C', 'D', 'E'],
                "theme_options": ['P', 'Q', 'R', 'S', 'T', 'U'],
                "theme_bubbles": coords_cache["themes"],
                "bubbles": coords_cache["answers"]
            }
        }
    }
    with open(output_json, "w", encoding="utf-8") as jf:
        json.dump(template_data, jf, indent=2)
    print(f"✅ Coordenadas maestras actualizadas en: {output_json}")
    return output_pdf

if __name__ == "__main__":
    # Generar un lote de muestra de 10 hojas correlativas
    generate_mass_omr_sheets(quantity=10)
