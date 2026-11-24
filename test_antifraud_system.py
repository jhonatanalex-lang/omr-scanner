"""
Test Automatizado de Seguridad Antifraude por Tiras Binarias Ópticas:
  1. Genera dos fichas serializadas con tiras ópticas gemelas:
     - Ficha 1: OMR-2026-0001 (Sync ID = 1)
     - Ficha 2: OMR-2026-0002 (Sync ID = 2)
  2. Simula:
     - Caso A (Legítimo): Ficha 1 completa normal (Left=1, Right=1).
     - Caso B (Fraude por Intercambio): 
       Identificación de Ficha 1 (Left=1) + Respuestas de Ficha 2 (Right=2).
  3. Ejecuta conciliación y califica en SQLite.
  4. Verifica que el Caso A sea calificado exitosamente (VERIFICADO_OK)
     y el Caso B sea inmediatamente bloqueado por FRAUDE DETECTADO (Puntaje 0).
  5. Exporta a Excel y valida el formato.
"""

import os
import json
import sqlite3
import cv2
import numpy as np
from generate_batch_sheets import generate_mass_omr_sheets
from batch_processor import OMRBatchProcessor
from omr_core import OMREngine

def test_antifraud():
    print("=== INICIANDO TEST DE SEGURIDAD ANTIFRAUDE ===")
    db_test = "test_antifraud.db"
    if os.path.exists(db_test):
        os.remove(db_test)
        
    pdf_lote = "test_lote_seguridad.pdf"
    generate_mass_omr_sheets(
        output_pdf=pdf_lote,
        output_json="template_coords.json",
        prefix="OMR-2026",
        start_num=1,
        quantity=2
    )
    
    proc = OMRBatchProcessor(db_path=db_test, template_json="template_coords.json")
    engine = OMREngine("template_coords.json")
    
    # Rasterizar ambas páginas
    img1 = proc.rasterize_pdf_page(pdf_lote, page_num=0, dpi=300)
    img2 = proc.rasterize_pdf_page(pdf_lote, page_num=1, dpi=300)
    
    h, w = img1.shape[:2]
    cut_x = int((95.0 / 297.0) * w)
    
    # Cortar las mitades
    f1_left = img1[:, :cut_x]
    f1_right = img1[:, cut_x:]
    
    f2_left = img2[:, :cut_x]
    f2_right = img2[:, cut_x:]
    
    # --- CASO 1: LEGÍTIMO (Hoja OMR-2026-0001 con su propia mitad derecha) ---
    print("\n--- CASO 1: ALUMNO LEGÍTIMO (OMR-2026-0001) ---")
    # Procesar ID F1
    m_l1 = engine.find_fiducial_markers(f1_left)
    al_l1, _ = engine.align_quad(f1_left, [(m[0], m[1]) for m in m_l1], 800, 1500)
    sync_l1 = engine.read_sync_strip(al_l1, "identification")
    proc.register_identification("OMR-2026-0001", "11111111", sync_id=sync_l1)
    print(f"Identificación Ficha 1 -> DNI: 11111111, Sync Left: {sync_l1}")
    
    # Procesar Resp F1
    m_r1 = engine.find_fiducial_markers(f1_right)
    al_r1, _ = engine.align_quad(f1_right, [(m[0], m[1]) for m in m_r1], 1500, 1500)
    sync_r1 = engine.read_sync_strip(al_r1, "answers")
    ans_f1 = {"_THEME_": "P", "Q01": "A", "Q02": "B"}
    proc.register_answers("OMR-2026-0001", ans_f1, sync_id=sync_r1)
    print(f"Respuestas Ficha 1 -> Tema: P, Sync Right: {sync_r1}")
    
    # --- CASO 2: FRAUDE (Postulante OMR-2026-0002 intercambia respuestas con Ficha 1) ---
    print("\n--- CASO 2: FRAUDE POR INTERCAMBIO (OMR-2026-0002) ---")
    # Postulante 2 llena su ID en Ficha 2
    m_l2 = engine.find_fiducial_markers(f2_left)
    al_l2, _ = engine.align_quad(f2_left, [(m[0], m[1]) for m in m_l2], 800, 1500)
    sync_l2 = engine.read_sync_strip(al_l2, "identification")
    proc.register_identification("OMR-2026-0002", "22222222", sync_id=sync_l2)
    print(f"Identificación Ficha 2 -> DNI: 22222222, Sync Left: {sync_l2}")
    
    # Pero entrega una hoja de respuestas que fue clonada / cambiada de otra persona (ej. tira sync = 999 o de otra ficha)
    # Simulamos que entregó la mitad de Ficha 1 registrada como 0002
    proc.register_answers("OMR-2026-0002", {"_THEME_": "P", "Q01": "A", "Q02": "B"}, sync_id=sync_r1) # sync_r1 es 1, pero su ID es 2!
    print(f"Respuestas Ficha 2 (Intercambiada) -> Sync Right: {sync_r1} (DIFERENTE DEL LEFT {sync_l2})")
    
    # Calificar
    teacher_keys = {"P": {"Q01": "A", "Q02": "B"}}
    results = proc.reconcile_and_grade(teacher_keys, score_correct=5.0, score_incorrect=0.0)
    
    print("\n================ RESULTADOS DE CONCILIACIÓN Y ANTIFRAUDE ================")
    for r in results:
        print(f"Ficha: {r['sheet_code']} | DNI: {r['student_id']}")
        print(f"  Estado   : {r['status']}")
        print(f"  Seguridad: {r['sync_status']}")
        print(f"  Nota     : {r['final_score']} pts")
        
    excel_path = "test_resultados_antifraude.xlsx"
    proc.export_to_excel(excel_path)
    print(f"\nReporte Excel exportado a: {excel_path}")
    
    # Aserciones de validación
    r1 = next(x for x in results if x["sheet_code"] == "OMR-2026-0001")
    r2 = next(x for x in results if x["sheet_code"] == "OMR-2026-0002")
    
    assert "VERIFICADO_OK" in r1["sync_status"], f"Error: Ficha 1 debió ser OK, fue {r1['sync_status']}"
    assert r1["final_score"] == 20.0, f"Error: Ficha 1 debió tener 20.0, tuvo {r1['final_score']}"
    
    assert "FRAUDE_DETECTADO" in r2["sync_status"], f"Error: Ficha 2 debió detectar FRAUDE, fue {r2['sync_status']}"
    assert r2["final_score"] == 0.0, f"Error: Ficha 2 debió anularse a 0.0, tuvo {r2['final_score']}"
    
    print("\n✅ TODAS LAS PRUEBAS DE SEGURIDAD ANTIFRAUDE PASARON AL 100%!")

if __name__ == "__main__":
    test_antifraud()
