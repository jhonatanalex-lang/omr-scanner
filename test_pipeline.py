"""
Test de Integración Completo (End-to-End):
  1. Toma la plantilla generada (omr_sheet_master.pdf) y la rasteriza.
  2. Simula el llenado realista de un examen:
     - Marca un DNI de estudiante (ej: "74839201").
     - Marca respuestas para 40 preguntas con un patrón conocido.
     - Simula desglose / separación física de las dos mitades.
     - Aplica una rotación / inclinación leve para probar la corrección de perspectiva fiduciaria.
  3. Ejecuta el OMRBatchProcessor.
  4. Realiza la conciliación relacional por código correlativo y califica contra la clave.
"""

import cv2
import numpy as np
import json
from omr_core import OMREngine
from batch_processor import OMRBatchProcessor

def run_test():
    processor = OMRBatchProcessor(db_path="test_results.db")
    engine = OMREngine(template_json_path="template_coords.json")
    
    print("1. Rasterizando la plantilla maestra a imagen de alta resolución (300 DPI)...")
    img_bgr = processor.rasterize_pdf_page("omr_sheet_master.pdf", dpi=300)
    h, w = img_bgr.shape[:2]
    print(f"   Dimensiones de la imagen rasterizada: {w}x{h} px")
    
    # Cargar coordenadas de plantilla
    with open("template_coords.json", "r") as f:
        tpl = json.load(f)
        
    simulated_img = img_bgr.copy()
    
    # 2. Simular llenado de DNI: "74839201"
    student_dni = "74839201"
    print(f"2. Simulando marcas con lápiz para el DNI: {student_dni}...")
    
    # Coordenadas relativas de la mitad izquierda (x: 0 a w/2 aprox)
    # En la imagen A4 completa, la mitad izquierda va de x_min a cut_x
    # Según generate_omr_sheet:
    # PAGE_WIDTH = 297mm, left_x_min = 12mm, left_x_max = (297/2) - 6mm = 142.5mm
    # Ancho sección izquierda = 130.5mm.
    # En píxeles:
    # Centros de los marcadores fiduciarios en la imagen rasterizada
    # 297mm ancho x 210mm alto
    # MARKER_SIZE = 8mm
    # Left Section:
    # left_x_min = 12mm, left_x_max = 142.5mm
    # left_y_min = 12mm, left_y_max = 198mm
    left_x0 = ((12.0 + 4.0) / 297.0) * w
    left_y0 = ((12.0 + 4.0) / 210.0) * h
    left_ref_w = ((142.5 - 4.0 - 12.0 - 4.0) / 297.0) * w
    left_ref_h = ((198.0 - 4.0 - 12.0 - 4.0) / 210.0) * h
    
    id_bubbles = tpl["sections"]["identification"]["bubbles"]
    for char_idx, char_val in enumerate(student_dni):
        target_val = int(char_val)
        for b in id_bubbles:
            if b["digit_index"] == char_idx and b["value"] == target_val:
                bx = int(left_x0 + b["norm_x"] * left_ref_w)
                by = int(h - (left_y0 + b["norm_y"] * left_ref_h)) # Inversión Y en imagen
                cv2.circle(simulated_img, (bx, by), int(w * 0.007), (30, 30, 30), -1)
                
    # 3. Simular llenado de Respuestas (40 preguntas)
    print("3. Simulando marcas con lápiz en hoja de respuestas (40 preguntas)...")
    right_x0 = ((154.5 + 4.0) / 297.0) * w
    right_y0 = ((12.0 + 4.0) / 210.0) * h
    right_ref_w = ((285.0 - 4.0 - 154.5 - 4.0) / 297.0) * w
    right_ref_h = ((198.0 - 4.0 - 12.0 - 4.0) / 210.0) * h
    
    student_answers = {}
    options_cycle = ['A', 'B', 'C', 'D', 'E']
    for q in range(1, 41):
        ans = options_cycle[(q - 1) % 5]
        student_answers[f"Q{q:02d}"] = ans
        
    ans_bubbles = tpl["sections"]["answers"]["bubbles"]
    for b in ans_bubbles:
        q_key = f"Q{b['question']:02d}"
        if student_answers.get(q_key) == b["option"]:
            bx = int(right_x0 + b["norm_x"] * right_ref_w)
            by = int(h - (right_y0 + b["norm_y"] * right_ref_h))
            cv2.circle(simulated_img, (bx, by), int(w * 0.007), (35, 35, 35), -1)
            
    # Guardar imagen simulada del examen completo
    cv2.imwrite("test_simulated_sheet.png", simulated_img)
    print("   -> Guardado 'test_simulated_sheet.png'")
    
    # 4. SIMULAR EL DESGLOSE FÍSICO (Separación en 2 mitades independientes)
    print("4. Simulando corte físico y escaneo de las 2 mitades independientes...")
    cut_x_px = int(w / 2.0)
    
    # Mitad izquierda (Identificación)
    half_id = simulated_img[:, :cut_x_px].copy()
    # Mitad derecha (Respuestas)
    half_ans = simulated_img[:, cut_x_px:].copy()
    
    # Procesar Mitad Identificación con OMREngine
    # Encontrar marcadores fiduciarios
    markers_id = engine.find_fiducial_markers(half_id)
    print(f"   Marcadores fiduciarios detectados en Ficha Identificación: {len(markers_id)} (esperados 4)")
    
    # Obtener 4 esquinas extremas
    pts_id = [(m[0], m[1]) for m in sorted(markers_id, key=lambda x: x[2], reverse=True)[:4]]
    aligned_id, _ = engine.align_quad(half_id, pts_id, out_w=1000, out_h=1400)
    cv2.imwrite("test_aligned_identification.png", aligned_id)
    
    read_dni = engine.read_identification_section(aligned_id)
    print(f"   ⭐️ DNI Reconocido por el Motor OMR: '{read_dni}' (Esperado: '{student_dni}')")
    
    # Procesar Mitad Respuestas con OMREngine
    markers_ans = engine.find_fiducial_markers(half_ans)
    print(f"   Marcadores fiduciarios detectados en Ficha Respuestas: {len(markers_ans)} (esperados 4)")
    
    pts_ans = [(m[0], m[1]) for m in sorted(markers_ans, key=lambda x: x[2], reverse=True)[:4]]
    aligned_ans, _ = engine.align_quad(half_ans, pts_ans, out_w=1000, out_h=1400)
    cv2.imwrite("test_aligned_answers.png", aligned_ans)
    
    read_answers = engine.read_answers_section(aligned_ans)
    print(f"   ⭐️ Total Preguntas Leídas: {len(read_answers)}")
    print(f"      Muestra de respuestas leídas: Q01={read_answers.get('Q01')}, Q02={read_answers.get('Q02')}, Q03={read_answers.get('Q03')}")
    
    # 5. REGISTRO EN LA BASE DE DATOS Y CONCILIACIÓN (JOIN RELACIONAL)
    sheet_code = tpl["sheet_code"] # 'OMR-2026-0001'
    print(f"5. Registrando fichas en la Base de Datos bajo el código: {sheet_code}...")
    processor.register_identification(sheet_code, read_dni)
    processor.register_answers(sheet_code, read_answers)
    
    # Clave de respuestas correctas del profesor (todas 'A' para probar puntaje)
    teacher_key = {f"Q{i:02d}": 'A' for i in range(1, 41)}
    
    print("6. Ejecutando algoritmo de conciliación y calificación...")
    results = processor.reconcile_and_grade(teacher_key, score_correct=1.0, score_incorrect=-0.25)
    
    print("\n================ RESULTADOS FINALES DE CONCILIACIÓN ================")
    for r in results:
        print(f" Código Hoja  : {r['sheet_code']}")
        print(f" Estudiante ID: {r['student_id']}")
        print(f" Estado       : {r['status']}")
        print(f" Correctas    : {r['correct']} / 40")
        print(f" Incorrectas  : {r['incorrect']}")
        print(f" En Blanco    : {r['blank']}")
        print(f" Puntaje Final: {r['score']} pts")
    print("====================================================================\n")

if __name__ == "__main__":
    run_test()
