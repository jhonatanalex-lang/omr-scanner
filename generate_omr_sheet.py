"""
Generador Paramétrico Oficial - Ficha OMR UNSAAC (30/70 con Tiras Ópticas y Franjas)
Institución: Universidad Nacional de San Antonio Abad del Cusco (UNSAAC)
Color Institucional: Carmesí / Guinda UNSAAC (#7A1C24 / #8A1C24)
"""

import json
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas

MM = 72.0 / 25.4
PAGE_WIDTH, PAGE_HEIGHT = landscape(A4) # 297mm x 210mm (~841.89 x ~595.28 pt)

MARKER_SIZE = 7.5 * MM    # Cuadrados negros fiduciarios de 7.5mm x 7.5mm
BUBBLE_R = 2.05 * MM      # Radio de burbuja de respuestas (~4.1mm de diámetro)
SYNC_BIT_R = 1.6 * MM     # Radio de los bits de sincronización (~3.2mm de diámetro)

# Paleta Institucional UNSAAC
COLOR_UNSAAC_WINE = colors.HexColor("#7A1C24")      # Guinda institucional oscuro
COLOR_UNSAAC_MEDIUM = colors.HexColor("#8C222B")    # Guinda medio
COLOR_UNSAAC_TINT = colors.HexColor("#F9F1F1")      # Fondo franja par
COLOR_UNSAAC_BORDER = colors.HexColor("#E8D4D6")    # Bordes suaves
COLOR_WARN_RED = colors.HexColor("#CC0000")         # Rojo de advertencia
COLOR_TEXT_DARK = colors.HexColor("#1A1A1A")        # Texto negro nítido

def draw_fiducial_markers(c, x_min, y_min, x_max, y_max, size):
    """Dibuja los 4 marcadores de esquina fiduciarios aislados."""
    c.setFillColor(colors.black)
    c.rect(x_min, y_min, size, size, fill=1, stroke=0)
    c.rect(x_max - size, y_min, size, size, fill=1, stroke=0)
    c.rect(x_min, y_max - size, size, size, fill=1, stroke=0)
    c.rect(x_max - size, y_max - size, size, size, fill=1, stroke=0)

def draw_sync_strip(c, center_x, start_y, bit_spacing, num_bits, bit_val_int, sheet_code=""):
    """
    Dibuja la columna vertical de 16 bits ópticos gemelos en el horizonte de desglose.
    """
    strip_h = (num_bits - 1) * bit_spacing + 8 * MM
    strip_w = 6.0 * MM
    
    # Recuadro exterior protector en color institucional
    c.setStrokeColor(COLOR_UNSAAC_MEDIUM)
    c.setLineWidth(0.6)
    c.roundRect(center_x - strip_w / 2.0, start_y - (num_bits - 1) * bit_spacing - 4 * MM, strip_w, strip_h, 3 * MM, stroke=1, fill=0)
    
    # Texto vertical de advertencia y código correlativo
    c.saveState()
    mid_y = start_y - ((num_bits - 1) * bit_spacing) / 2.0
    c.translate(center_x - 3.8 * MM, mid_y)
    c.rotate(90)
    
    # Parte inferior: "NO ESCRIBA EN ESTA AREA" en rojo
    c.setFont("Helvetica-Bold", 4.5)
    c.setFillColor(COLOR_WARN_RED)
    c.drawCentredString(-24 * MM, 0, "NO ESCRIBA EN ESTA AREA")
    
    # Parte superior: "CÓDIGO: {sheet_code}" en negro
    if sheet_code:
        c.setFont("Helvetica-Bold", 5.5)
        c.setFillColor(colors.black)
        c.drawCentredString(24 * MM, 0, f"CÓDIGO: {sheet_code}")
        
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

def draw_mark_examples(c, x, y, compact=False):
    """Dibuja los ejemplos de marca correcta e incorrecta."""
    c.setFont("Helvetica-Bold", 5)
    c.setFillColor(colors.black)
    c.drawString(x, y, "CORRECTO:")
    # Burbuja rellena
    c.circle(x + 16 * MM, y + 1.2 * MM, 1.4 * MM, stroke=1, fill=1)
    
    c.drawString(x + 22 * MM, y, "INCORRECTO:")
    c.circle(x + 38 * MM, y + 1.2 * MM, 1.4 * MM, stroke=1, fill=0)
    c.setLineWidth(0.6)
    # Check
    c.line(x + 37 * MM, y + 1.2 * MM, x + 38 * MM, y + 0.3 * MM)
    c.line(x + 38 * MM, y + 0.3 * MM, x + 39.5 * MM, y + 2.2 * MM)
    
    c.circle(x + 43 * MM, y + 1.2 * MM, 1.4 * MM, stroke=1, fill=0)
    # Aspa (X)
    c.line(x + 42 * MM, y + 0.2 * MM, x + 44 * MM, y + 2.2 * MM)
    c.line(x + 42 * MM, y + 2.2 * MM, x + 44 * MM, y + 0.2 * MM)
    
    c.circle(x + 48 * MM, y + 1.2 * MM, 1.4 * MM, stroke=1, fill=0)
    # Punto chico
    c.circle(x + 48 * MM, y + 1.2 * MM, 0.5 * MM, stroke=1, fill=1)

def generate_omr_sheet(
    output_pdf="omr_sheet_master.pdf", 
    output_json="template_coords.json", 
    sheet_code="OMR-2026-0030",
    sheet_id_number=30,
    logo_path="unsaac_logo.png"
):
    c = canvas.Canvas(output_pdf, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    
    cut_x = 95.0 * MM # Línea de corte / desglose en X = 95mm
    
    # Línea central punteada de desglose
    c.setDash(3, 3)
    c.setStrokeColor(colors.HexColor("#B0B0B0"))
    c.setLineWidth(0.6)
    c.line(cut_x, 8 * MM, cut_x, PAGE_HEIGHT - 8 * MM)
    c.setDash()
    
    c.setFont("Helvetica-Bold", 5)
    c.setFillColor(colors.HexColor("#888888"))
    c.drawCentredString(cut_x, 4.5 * MM, "LÍNEA DE DESGLOSE / CORTE")
    
    # Marcador fiduciario central superior e inferior sobre la línea de corte
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
    
    id_center_x = (left_x_min + left_x_max - 6 * MM) / 2.0
    
    # 1.1 Escudo UNSAAC y Título
    has_logo = os.path.exists(logo_path)
    if has_logo:
        logo_w = 9.5 * MM
        logo_h = 9.5 * MM
        c.drawImage(logo_path, id_center_x - (logo_w / 2.0), left_y_max - 10.5 * MM, width=logo_w, height=logo_h, mask='auto')
        
    c.setFillColor(COLOR_UNSAAC_WINE)
    c.setFont("Helvetica-Bold", 6.2)
    c.drawCentredString(id_center_x, left_y_max - 13.2 * MM, "UNIVERSIDAD NACIONAL DE")
    c.drawCentredString(id_center_x, left_y_max - 16.0 * MM, "SAN ANTONIO ABAD DEL CUSCO")
    
    # 1.2 Banner HOJA DE IDENTIFICACIÓN
    box_w = (left_x_max - left_x_min) - 22 * MM
    box_x = left_x_min + 9 * MM
    banner_y = left_y_max - 21.5 * MM
    
    c.setFillColor(COLOR_UNSAAC_TINT)
    c.setStrokeColor(COLOR_UNSAAC_WINE)
    c.setLineWidth(0.7)
    c.roundRect(box_x, banner_y, box_w, 4.5 * MM, 1.5 * MM, fill=1, stroke=1)
    
    c.setFillColor(COLOR_UNSAAC_WINE)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(box_x + box_w / 2.0, banner_y + 1.2 * MM, "HOJA DE IDENTIFICACIÓN")
    
    # 1.3 Bloque Manuscrito de Datos Personales (Casillas amplias y ergonómicas)
    cur_y = banner_y - 3.5 * MM
    c.setLineWidth(0.65)
    c.setStrokeColor(COLOR_UNSAAC_MEDIUM)
    
    field_h = 7.5 * MM
    corner_r = 1.5 * MM
    
    # Apellido Paterno
    c.setFont("Helvetica-Bold", 5.8)
    c.setFillColor(COLOR_UNSAAC_WINE)
    c.drawString(box_x + 1.2 * MM, cur_y, "APELLIDO PATERNO:")
    cur_y -= (field_h + 1.0 * MM)
    c.roundRect(box_x, cur_y, box_w, field_h, corner_r, stroke=1, fill=0)
    
    # Apellido Materno
    cur_y -= 3.2 * MM
    c.drawString(box_x + 1.2 * MM, cur_y, "APELLIDO MATERNO:")
    cur_y -= (field_h + 1.0 * MM)
    c.roundRect(box_x, cur_y, box_w, field_h, corner_r, stroke=1, fill=0)
    
    # Nombres
    cur_y -= 3.2 * MM
    c.drawString(box_x + 1.2 * MM, cur_y, "NOMBRES:")
    cur_y -= (field_h + 1.0 * MM)
    c.roundRect(box_x, cur_y, box_w, field_h, corner_r, stroke=1, fill=0)
    
    # 1.4 Matriz DNI (8 dígitos)
    cur_y -= 5.0 * MM
    dni_header_h = 4.5 * MM
    c.setFillColor(COLOR_UNSAAC_TINT)
    c.setStrokeColor(COLOR_UNSAAC_WINE)
    c.roundRect(box_x, cur_y, box_w, dni_header_h, 1.2 * MM, fill=1, stroke=1)
    c.setFillColor(COLOR_UNSAAC_WINE)
    c.setFont("Helvetica-Bold", 6.8)
    c.drawCentredString(box_x + box_w / 2.0, cur_y + 1.2 * MM, "NÚMERO DE DNI")
    
    col_w = 7.0 * MM
    row_h = 5.8 * MM
    write_box_w = 6.0 * MM
    write_box_h = 5.8 * MM
    write_box_y = cur_y - 6.5 * MM
    box_center_x = box_x + box_w / 2.0
    
    c.setStrokeColor(COLOR_UNSAAC_MEDIUM)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 6.2)
    
    dni_bubbles = []
    for col in range(8):
        cx = box_center_x + (col - 3.5) * col_w
        # Casilla superior centrada para escribir el dígito
        c.roundRect(cx - write_box_w / 2.0, write_box_y, write_box_w, write_box_h, 1.0 * MM, stroke=1, fill=0)
        
        # 10 Burbujas verticales del 0 al 9
        for val in range(10):
            cy = (write_box_y - 4.8 * MM) - (val * row_h)
            c.circle(cx, cy, 1.95 * MM, stroke=1, fill=0)
            c.drawCentredString(cx, cy - 1.9, str(val))
            
            u = (cx - id_ref_x0) / id_ref_w
            v = (cy - id_ref_y0) / id_ref_h
            dni_bubbles.append({
                "digit_index": col,
                "value": val,
                "norm_x": round(u, 5),
                "norm_y": round(v, 5)
            })
            
    # 1.5 Recuadro de Instrucciones (Identificación)
    inst_y = (write_box_y - 4.8 * MM) - (9.5 * row_h) - 4.5 * MM
    inst_h = 20.0 * MM
    
    c.setStrokeColor(COLOR_UNSAAC_BORDER)
    c.setFillColor(COLOR_UNSAAC_TINT)
    c.roundRect(box_x, inst_y - inst_h, box_w, inst_h, 1.5 * MM, fill=1, stroke=1)
    
    # Barra de título Instrucciones
    c.setFillColor(COLOR_UNSAAC_WINE)
    c.roundRect(box_x, inst_y - 4.2 * MM, box_w, 4.2 * MM, 1.2 * MM, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 5.5)
    c.drawCentredString(box_x + box_w / 2.0, inst_y - 3.0 * MM, "INSTRUCCIONES")
    
    c.setFillColor(COLOR_TEXT_DARK)
    c.setFont("Helvetica", 4.3)
    inst_text_1 = "Escriba los ocho dígitos de su DNI en las casillas correspondientes"
    inst_text_2 = "y rellene en cada columna el círculo del dígito registrado."
    inst_text_3 = "Llene con lápiz 2B de forma nítida. Evite borrones o enmendaduras."
    c.drawString(box_x + 1.8 * MM, inst_y - 7.0 * MM, inst_text_1)
    c.drawString(box_x + 1.8 * MM, inst_y - 9.4 * MM, inst_text_2)
    c.drawString(box_x + 1.8 * MM, inst_y - 11.8 * MM, inst_text_3)
    
    draw_mark_examples(c, box_x + 1.8 * MM, inst_y - 17.0 * MM, compact=True)
    
    # 1.6 Firma del Postulante (Espacio amplio aprovechando la parte inferior)
    sign_box_y = inst_y - inst_h - 4.5 * MM
    sign_box_h = 22.0 * MM
    c.setStrokeColor(COLOR_UNSAAC_MEDIUM)
    c.setLineWidth(0.65)
    c.roundRect(box_x, sign_box_y - sign_box_h, box_w, sign_box_h, 1.5 * MM, stroke=1, fill=0)
    c.setDash(2, 2)
    c.setStrokeColor(colors.gray)
    c.line(box_x + 5 * MM, sign_box_y - sign_box_h + 6.5 * MM, box_x + box_w - 5 * MM, sign_box_y - sign_box_h + 6.5 * MM)
    c.setDash()
    c.setFont("Helvetica-Bold", 5.0)
    c.setFillColor(COLOR_TEXT_DARK)
    c.drawCentredString(box_x + box_w / 2.0, sign_box_y - sign_box_h + 2.8 * MM, "FIRMA DEL POSTULANTE (dentro del cuadro)")
    
    # 1.7 Tira Binaria Óptica en Identificación
    NUM_SYNC_BITS = 16
    SYNC_SPACING = 6.2 * MM
    SYNC_START_Y = PAGE_HEIGHT - 38 * MM
    left_sync_x = cut_x - 8 * MM
    left_bits = draw_sync_strip(c, left_sync_x, SYNC_START_Y, SYNC_SPACING, NUM_SYNC_BITS, sheet_id_number, sheet_code=sheet_code)
    
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
    
    # 2.1 Tira Binaria en Respuestas (simétrica gemela)
    right_sync_x = cut_x + 8 * MM
    right_bits = draw_sync_strip(c, right_sync_x, SYNC_START_Y, SYNC_SPACING, NUM_SYNC_BITS, sheet_id_number, sheet_code=sheet_code)
    
    right_sync_coords = []
    for rb in right_bits:
        u = (rb["x"] - ans_ref_x0) / ans_ref_w
        v = (rb["y"] - ans_ref_y0) / ans_ref_h
        right_sync_coords.append({"bit_index": rb["bit_index"], "norm_x": round(u, 5), "norm_y": round(v, 5)})
        
    ans_center_x = (right_x_min + 14 * MM + right_x_max) / 2.0
    
    # 2.2 Escudo UNSAAC y Encabezado Respuestas
    if has_logo:
        logo_w = 9.5 * MM
        logo_h = 9.5 * MM
        c.drawImage(logo_path, ans_center_x - (logo_w / 2.0), right_y_max - 10.5 * MM, width=logo_w, height=logo_h, mask='auto')
        
    c.setFillColor(COLOR_UNSAAC_WINE)
    c.setFont("Helvetica-Bold", 8.0)
    c.drawCentredString(ans_center_x, right_y_max - 13.5 * MM, "UNIVERSIDAD NACIONAL DE SAN ANTONIO ABAD DEL CUSCO")
    c.setFont("Helvetica-Bold", 6.2)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawCentredString(ans_center_x, right_y_max - 16.5 * MM, "HOJA ÓPTICA DE EVALUACIÓN ACADÉMICA")
    
    # 2.3 Badges de Título y Tema
    subhead_y = right_y_max - 23.5 * MM
    ans_start_x = right_x_min + 14 * MM
    ans_content_w = (right_x_max - ans_start_x) - 2 * MM
    
    # Badge "HOJA DE RESPUESTAS"
    badge_w = 60 * MM
    c.setFillColor(COLOR_UNSAAC_TINT)
    c.setStrokeColor(COLOR_UNSAAC_WINE)
    c.roundRect(ans_start_x, subhead_y, badge_w, 5.0 * MM, 1.5 * MM, fill=1, stroke=1)
    c.setFillColor(COLOR_UNSAAC_WINE)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(ans_start_x + badge_w / 2.0, subhead_y + 1.4 * MM, "HOJA DE RESPUESTAS")
    
    # Selector de TEMA (P, Q, R, S, T, U)
    theme_box_w = 85 * MM
    theme_box_x = ans_start_x + ans_content_w - theme_box_w
    c.setFillColor(COLOR_UNSAAC_TINT)
    c.setStrokeColor(COLOR_UNSAAC_WINE)
    c.roundRect(theme_box_x, subhead_y, theme_box_w, 5.0 * MM, 1.5 * MM, fill=1, stroke=1)
    
    c.setFillColor(COLOR_UNSAAC_WINE)
    c.setFont("Helvetica-Bold", 6.5)
    c.drawString(theme_box_x + 2 * MM, subhead_y + 1.5 * MM, "TIPO DE TEMA:")
    
    themes = ['P', 'Q', 'R', 'S', 'T', 'U']
    theme_bubbles = []
    c.setFont("Helvetica-Bold", 6.5)
    for t_idx, t_char in enumerate(themes):
        bx = theme_box_x + 23 * MM + t_idx * 10 * MM
        by = subhead_y + 2.5 * MM
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.white)
        c.circle(bx, by, 1.85 * MM, stroke=1, fill=1)
        c.setFillColor(colors.black)
        c.drawCentredString(bx, by - 1.8, t_char)
        
        u = (bx - ans_ref_x0) / ans_ref_w
        v = (by - ans_ref_y0) / ans_ref_h
        theme_bubbles.append({
            "theme": t_char,
            "norm_x": round(u, 5),
            "norm_y": round(v, 5)
        })
        
    # 2.4 Matriz de 80 Preguntas en 4 Columnas con FRANJAS ALTERNADAS
    options = ['A', 'B', 'C', 'D', 'E']
    opt_spacing = 5.2 * MM
    row_height = 6.6 * MM
    col_width = 41.5 * MM
    col_gap = 2.5 * MM
    ans_start_y = subhead_y - 8.5 * MM
    
    ans_bubbles = []
    for col_idx in range(4):
        col_x = ans_start_x + col_idx * (col_width + col_gap)
        q_start = col_idx * 20 + 1
        q_end = col_idx * 20 + 20
        
        # Cabecera de Columna
        c.setFillColor(COLOR_UNSAAC_WINE)
        c.setFont("Helvetica-Bold", 6.8)
        c.drawCentredString(col_x + col_width / 2.0, ans_start_y + 3.0 * MM, f"PREGUNTAS {q_start:02d} - {q_end:02d}")
        
        c.setStrokeColor(COLOR_UNSAAC_MEDIUM)
        c.setLineWidth(0.6)
        c.line(col_x + 1 * MM, ans_start_y + 1.5 * MM, col_x + col_width - 1 * MM, ans_start_y + 1.5 * MM)
        
        # 20 Filas con Franjas Alternadas
        for i in range(20):
            q_num = col_idx * 20 + (i + 1)
            row_y = ans_start_y - 2.5 * MM - (i * row_height)
            
            # Dibujar la FRANJA HORIZONTAL (Zebra Striping)
            franja_h = 5.6 * MM
            franja_y = row_y - 2.8 * MM
            
            if i % 2 == 0:
                # Fila par: Franja sombreada suave (tinte institucional muy tenue)
                c.setFillColor(COLOR_UNSAAC_TINT)
                c.setStrokeColor(COLOR_UNSAAC_BORDER)
                c.setLineWidth(0.3)
                c.roundRect(col_x, franja_y, col_width, franja_h, 1.2 * MM, fill=1, stroke=1)
            else:
                # Fila impar: Fondo blanco con borde sutil
                c.setFillColor(colors.white)
                c.setStrokeColor(colors.HexColor("#EDEDED"))
                c.setLineWidth(0.3)
                c.roundRect(col_x, franja_y, col_width, franja_h, 1.2 * MM, fill=1, stroke=1)
                
            # Número de pregunta
            c.setFont("Helvetica-Bold", 6.2)
            c.setFillColor(COLOR_UNSAAC_WINE)
            c.drawRightString(col_x + 7.5 * MM, row_y - 1.8, f"{q_num:02d}.")
            
            # Burbujas A, B, C, D, E
            c.setFont("Helvetica-Bold", 6.5)
            for opt_idx, opt_char in enumerate(options):
                bx = col_x + 12.0 * MM + opt_idx * opt_spacing
                by = row_y
                c.setStrokeColor(colors.black)
                c.setLineWidth(0.5)
                c.setFillColor(colors.white)
                c.circle(bx, by, BUBBLE_R, stroke=1, fill=1)
                c.setFillColor(colors.black)
                c.drawCentredString(bx, by - 1.8, opt_char)
                
                u = (bx - ans_ref_x0) / ans_ref_w
                v = (by - ans_ref_y0) / ans_ref_h
                ans_bubbles.append({
                    "question": q_num,
                    "option": opt_char,
                    "norm_x": round(u, 5),
                    "norm_y": round(v, 5)
                })
                
    # 2.5 Banner Inferior de Instrucciones y Recomendaciones
    foot_y = ans_start_y - 2.5 * MM - (20 * row_height) - 1.5 * MM
    foot_h = 16.0 * MM
    
    c.setStrokeColor(COLOR_UNSAAC_BORDER)
    c.setFillColor(COLOR_UNSAAC_TINT)
    c.roundRect(ans_start_x, foot_y - foot_h, ans_content_w, foot_h, 1.5 * MM, fill=1, stroke=1)
    
    # Encabezado Instrucciones
    c.setFillColor(COLOR_UNSAAC_WINE)
    c.roundRect(ans_start_x, foot_y - 3.8 * MM, 40 * MM, 3.8 * MM, 1.0 * MM, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 5.5)
    c.drawCentredString(ans_start_x + 20 * MM, foot_y - 2.8 * MM, "INSTRUCCIONES")
    
    # Textos instructivos oficiales (como en omr modelo.png)
    c.setFillColor(COLOR_TEXT_DARK)
    c.setFont("Helvetica", 4.3)
    rule_x = ans_start_x + 2 * MM
    c.drawString(rule_x, foot_y - 6.2 * MM, "1. Rellene el círculo completamente una vez que esté seguro de su respuesta y sólo uno por cada pregunta.")
    c.drawString(rule_x, foot_y - 8.6 * MM, "2. En caso de error, limpie el borrador, borre con cuidado y rellene la opción que considere correcta.")
    c.drawString(rule_x, foot_y - 11.0 * MM, "3. No doble ni arrugue la hoja por ningún motivo.  4. No use tinta ni bolígrafo.  5. Evite humedecer la hoja.")
    c.drawString(rule_x, foot_y - 13.4 * MM, "6. Verifique que el Tipo de Tema marcado coincida exactamente con el cuadernillo de preguntas entregado.")
    
    # Lado derecho del banner inferior: USE SOLO LAPIZ 2B y Ejemplos
    ex_x = ans_start_x + ans_content_w - 55 * MM
    c.setFont("Helvetica-Bold", 5.2)
    c.setFillColor(COLOR_UNSAAC_WINE)
    c.drawString(ex_x, foot_y - 5.5 * MM, "USE SÓLO LÁPIZ 2B")
    draw_mark_examples(c, ex_x, foot_y - 11.5 * MM, compact=False)

    c.showPage()
    c.save()
    print(f"✅ Ficha OMR Oficial UNSAAC generada: {output_pdf}")
    
    template_data = {
        "sheet_code": sheet_code,
        "sheet_id_number": sheet_id_number,
        "format": "A4_landscape_80q_30_70_unsaac",
        "bubble_radius_mm": 2.05,
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
    print(f"✅ Coordenadas maestras actualizadas: {output_json}")

if __name__ == "__main__":
    generate_omr_sheet(sheet_code="OMR-2026-0030", sheet_id_number=30)
