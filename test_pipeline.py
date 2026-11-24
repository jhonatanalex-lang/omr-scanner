"""
Test de Integración Integral para Ficha Oficial de 80 Preguntas:
  1. Rasteriza la plantilla maestra de 80 preguntas (omr_sheet_master.pdf).
  2. Simula:
     - DNI del alumno: '46291035'
     - Tipo de Examen / Tema marcado: 'Q'
     - 80 Preguntas marcadas con un patrón conocido (A, B, C, D, E cíclico).
  3. Desglose en dos mitades independientes.
  4. Decodificación de código de barras Code128 de enlace unívoco.
  5. Calificación contra la clave del Tema 'Q'.
"""

import cv2
import numpy as np
import json
import fitz
import pyzbar.pyzbar as pyzbar
from omr_core import OMREngine
from batch_processor import OMRBatchProcessor

def run_test_80():
    processor = OMRBatchProcessor(db_path="test_results.db")
    engine = OMREngine(template_json_path="template_coords.json")
    
    print("1. Rasterizando la ficha oficial de 80 preguntas (300 DPI)...")
    img_bgr = processor.rasterize_pdf_page("omr_sheet_master.pdf", dpi=300)
    h, w = img_bgr.shape[:2]
    print(f"   Dimensiones de la imagen: {w}x{h} px")
    
    with open("template_coords.json", "r") as f:
        tpl = json.load(f)
        
    simulated_img = img_bgr.copy()
    
    # Parámetros geométricos en mm para la simulación
    # Left Section: x: [10mm, 143.5mm], y: [10mm, 200mm], Marker size: 7.5mm
    left_x0 = ((10.0 + 3.75) / 297.0) * w
    left_y0 = ((10.0 + 3.75) / 210.0) * h
    left_ref_w = ((143.5 - 3.75 - 10.0 - 3.75) / 297.0) * w
    left_ref_h = ((200.0 - 3.75 - 10.0 - 3.75) / 210.0) * h
    
    student_dni = "46291035"
    print(f"2. Simulando llenado de DNI: {student_dni}...")
    id_bubbles = tpl["sections"]["identification"]["bubbles"]
    for char_idx, char_val in enumerate(student_dni):
        target_val = int(char_val)
        for b in id_bubbles:
            if b["digit_index"] == char_idx and b["value"] == target_val:
                bx = int(left_x0 + b["norm_x"] * left_ref_w)
                by = int(h - (left_y0 + b["norm_y"] * left_ref_h))
                cv2.circle(simulated_img, (bx, by), int(w * 0.0055), (30, 30, 30), -1)
                
    # Right Section: x: [153.5mm, 287mm], y: [10mm, 200mm], Marker size: 7.5mm
    right_x0 = ((153.5 + 3.75) / 297.0) * w
    right_y0 = ((10.0 + 3.75) / 210.0) * h
    right_ref_w = ((287.0 - 3.75 - 153.5 - 3.75) / 297.0) * w
    right_ref_h = ((200.0 - 3.75 - 10.0 - 3.75) / 210.0) * h
    
    # Simular marcado de Tema: 'Q'
    chosen_theme = "Q"
    print(f"3. Simulando marcado de Tema de Examen: '{chosen_theme}'...")
    for tb in tpl["sections"]["answers"]["theme_bubbles"]:
        if tb["theme"] == chosen_theme:
            bx = int(right_x0 + tb["norm_x"] * right_ref_w)
            by = int(h - (right_y0 + tb["norm_y"] * right_ref_h))
            cv2.circle(simulated_img, (bx, by), int(w * 0.0055), (35, 35, 35), -1)
            
    # Simular 80 Preguntas
    print("4. Simulando marcado de 80 Preguntas...")
    student_answers = {}
    options_cycle = ['A', 'B', 'C', 'D', 'E']
    for q in range(1, 81):
        ans = options_cycle[(q - 1) % 5]
        student_answers[f"Q{q:02d}"] = ans
        
    for b in tpl["sections"]["answers"]["bubbles"]:
        q_key = f"Q{b['question']:02d}"
        if student_answers.get(q_key) == b["option"]:
            bx = int(right_x0 + b["norm_x"] * right_ref_w)
            by = int(h - (right_y0 + b["norm_y"] * right_ref_h))
            cv2.circle(simulated_img, (bx, by), int(w * 0.0055), (35, 35, 35), -1)
            
    cv2.imwrite("test_official_simulated.png", simulated_img)
    
    # 5. Desglose físico
    cut_x_px = int(w / 2.0)
    half_id = simulated_img[:, :cut_x_px]
    half_ans = simulated_img[:, cut_x_px:]
    
    # Lectura del código de barras en Identificación
    b_id = pyzbar.decode(half_id)
    sheet_code_id = b_id[0].data.decode('utf-8') if b_id else "UNKNOWN"
    print(f"   Código de Barras en Ficha Identificación: {sheet_code_id}")
    
    # Detección y Alineamiento Identificación
    markers_id = engine.find_fiducial_markers(half_id)
    pts_id = [(m[0], m[1]) for m in markers_id]
    aligned_id, _ = engine.align_quad(half_id, pts_id, out_w=1000, out_h=1400)
    read_dni = engine.read_identification_section(aligned_id)
    print(f"   ⭐️ DNI Reconocido: '{read_dni}' (Esperado: '{student_dni}')")
    
    # Lectura del código de barras en Respuestas
    b_ans = pyzbar.decode(half_ans)
    sheet_code_ans = b_ans[0].data.decode('utf-8') if b_ans else "UNKNOWN"
    print(f"   Código de Barras en Ficha Respuestas: {sheet_code_ans}")
    
    # Detección y Alineamiento Respuestas
    markers_ans = engine.find_fiducial_markers(half_ans)
    pts_ans = [(m[0], m[1]) for m in markers_ans]
    aligned_ans, _ = engine.align_quad(half_ans, pts_ans, out_w=1000, out_h=1400)
    read_answers = engine.read_answers_section(aligned_ans)
    
    read_theme = read_answers.get("_THEME_")
    print(f"   ⭐️ Tema de Examen Reconocido: '{read_theme}' (Esperado: '{chosen_theme}')")
    
    # Comprobar precisión de las 80 preguntas
    hits = sum(1 for q in range(1, 81) if read_answers.get(f"Q{q:02d}") == student_answers.get(f"Q{q:02d}"))
    print(f"   ⭐️ Preguntas reconocidas con exactitud: {hits} / 80 ({(hits/80)*100:.1f}%)")
    
    # Registrar en base de datos y calificar
    processor.register_identification(sheet_code_id, read_dni)
    processor.register_answers(sheet_code_ans, read_answers)
    
    # Clave del profesor para 80 preguntas
    teacher_key = {f"Q{i:02d}": ['A', 'B', 'C', 'D', 'E'][(i - 1) % 5] for i in range(1, 81)}
    results = processor.reconcile_and_grade(teacher_key, score_correct=1.0, score_incorrect=-0.25)
    
    print("\n================ RESULTADOS FINALES DE CONCILIACIÓN ================")
    for r in results:
        print(f" Código Hoja  : {r['sheet_code']}")
        print(f" Estudiante ID: {r['student_id']}")
        print(f" Estado       : {r['status']}")
        print(f" Correctas    : {r['correct']} / 80")
        print(f" Puntaje Final: {r['score']} pts")
    print("====================================================================\n")
    
    excel_path = processor.export_to_excel("resultados_80_preguntas.xlsx")
    print(f"Reporte Excel generado en: {excel_path}")

if __name__ == "__main__":
    run_test_80()
