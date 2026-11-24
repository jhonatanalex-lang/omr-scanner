"""
Sistema de Conciliación y Calificación por Lotes (Batch OMR Processor)
Utiliza:
  - Base de datos SQLite para persistencia relacional.
  - Conciliación de fichas de Identificación y Respuestas mediante código correlativo.
  - Calificación automatizada contra una clave de respuestas.
"""

import sqlite3
import json
import os
import fitz # PyMuPDF
import cv2
import numpy as np
from omr_core import OMREngine

class OMRBatchProcessor:
    def __init__(self, db_path="omr_results.db", template_json="template_coords.json"):
        self.db_path = db_path
        self.engine = OMREngine(template_json)
        self.init_db()

    def init_db(self):
        """Inicializa las tablas de SQLite para el enlace de fichas desglosadas."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Tabla de Identificación
        cur.execute("""
            CREATE TABLE IF NOT EXISTS identification_sheets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sheet_code TEXT UNIQUE,
                student_id TEXT,
                scan_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de Respuestas
        cur.execute("""
            CREATE TABLE IF NOT EXISTS answer_sheets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sheet_code TEXT UNIQUE,
                answers_json TEXT,
                scan_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de Calificaciones Consolidadas
        cur.execute("""
            CREATE TABLE IF NOT EXISTS graded_results (
                sheet_code TEXT PRIMARY KEY,
                student_id TEXT,
                theme TEXT,
                correct_count INTEGER,
                incorrect_count INTEGER,
                blank_count INTEGER,
                final_score REAL,
                status TEXT
            )
        """)
        # Migración automática si la tabla se creó previamente sin la columna 'theme'
        try:
            cur.execute("ALTER TABLE graded_results ADD COLUMN theme TEXT")
        except sqlite3.OperationalError:
            pass # La columna ya existe
            
        conn.commit()
        conn.close()

    def register_identification(self, sheet_code, student_id):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO identification_sheets (sheet_code, student_id)
            VALUES (?, ?)
        """, (sheet_code, student_id))
        conn.commit()
        conn.close()

    def register_answers(self, sheet_code, answers_dict):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO answer_sheets (sheet_code, answers_json)
            VALUES (?, ?)
        """, (sheet_code, json.dumps(answers_dict)))
        conn.commit()
        conn.close()

    def reconcile_and_grade(self, answer_keys, score_correct=1.0, score_incorrect=-0.25):
        """
        Realiza el JOIN relacional entre Identificación y Respuestas,
        detecta el tema del examen (P, Q, R, S, T, U) y califica contra la clave respectiva.
        answer_keys puede ser:
          - Un dict simple { "Q01": "A", ... } (clave única para todos los temas).
          - Un dict multi-tema { "P": {...}, "Q": {...}, ... }
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Consulta de conciliación FULL OUTER
        query = """
            SELECT 
                COALESCE(a.sheet_code, i.sheet_code) AS sheet_code,
                i.student_id,
                a.answers_json
            FROM answer_sheets a
            LEFT JOIN identification_sheets i ON a.sheet_code = i.sheet_code
            UNION
            SELECT 
                COALESCE(a.sheet_code, i.sheet_code) AS sheet_code,
                i.student_id,
                a.answers_json
            FROM identification_sheets i
            LEFT JOIN answer_sheets a ON i.sheet_code = a.sheet_code
        """
        cur.execute(query)
        rows = cur.fetchall()
        
        results = []
        for sheet_code, student_id, answers_json in rows:
            if not student_id:
                status = "ORPHAN_ANSWERS (Falta ficha de datos)"
                theme = "N/A"
                correct, incorrect, blank, score = 0, 0, 0, 0.0
            elif not answers_json:
                status = "ORPHAN_IDENTIFICATION (Falta ficha de respuestas)"
                theme = "N/A"
                correct, incorrect, blank, score = 0, 0, 0, 0.0
            else:
                answers = json.loads(answers_json)
                theme = answers.get("_THEME_", "SIN_TEMA")
                
                # REGLA OFICIAL: Si no marcó tema o tiene tema dudoso, pasa a OBSERVADO para arbitraje manual
                if theme in ["SIN_TEMA", "MULTIPLE_THEME"]:
                    status = f"OBSERVADO ({theme} - Falta asignar tema)"
                    correct, incorrect, blank, score = 0, 0, 0, 0.0
                else:
                    # Seleccionar la clave correspondiente según el tema
                    if isinstance(answer_keys, dict) and any(k in ["P", "Q", "R", "S", "T", "U"] for k in answer_keys.keys()):
                        target_key = answer_keys.get(theme)
                        if not target_key:
                            target_key = answer_keys.get("P") or list(answer_keys.values())[0]
                    else:
                        target_key = answer_keys
                        
                    status = "MATCHED (Calificada)"
                    correct, incorrect, blank = 0, 0, 0
                    
                    for q_key, correct_val in target_key.items():
                        if q_key.startswith("_"): # Ignorar metadatos
                            continue
                        student_val = answers.get(q_key, "BLANK")
                        if student_val == correct_val:
                            correct += 1
                        elif student_val in ["BLANK", "MULTIPLE_MARK"]:
                            blank += 1
                        else:
                            incorrect += 1
                            
                    score = max(0.0, (correct * score_correct) + (incorrect * score_incorrect))
                
            cur.execute("""
                INSERT OR REPLACE INTO graded_results 
                (sheet_code, student_id, theme, correct_count, incorrect_count, blank_count, final_score, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (sheet_code, student_id or "UNKNOWN", theme, correct, incorrect, blank, score, status))
            
            results.append({
                "sheet_code": sheet_code,
                "student_id": student_id or "DESCONOCIDO",
                "theme": theme,
                "status": status,
                "score": score,
                "correct": correct,
                "incorrect": incorrect,
                "blank": blank
            })
            
        conn.commit()
        conn.close()
        return results

    def export_to_excel(self, output_excel="resultados_examen.xlsx"):
        """Exporta los resultados consolidados a un archivo Excel (.xlsx) con formato profesional."""
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT sheet_code, student_id, theme, correct_count, incorrect_count, blank_count, final_score, status
            FROM graded_results
            ORDER BY final_score DESC
        """)
        rows = cur.fetchall()
        conn.close()
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Resultados OMR"
        
        # Estilos de cabecera
        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        center_align = Alignment(horizontal="center", vertical="center")
        thin_border = Border(
            left=Side(style='thin', color='D9D9D9'),
            right=Side(style='thin', color='D9D9D9'),
            top=Side(style='thin', color='D9D9D9'),
            bottom=Side(style='thin', color='D9D9D9')
        )
        
        headers = ["Puesto", "Código Hoja", "DNI / Estudiante", "Tema", "Correctas", "Incorrectas", "En Blanco", "Nota Final", "Estado"]
        ws.append(headers)
        
        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = center_align
            cell.border = thin_border
            
        for idx, row in enumerate(rows, start=1):
            sheet_code, student_id, theme, correct, incorrect, blank, score, status = row
            data_row = [idx, sheet_code, student_id, theme or "N/A", correct, incorrect, blank, score, status]
            ws.append(data_row)
            
            row_num = idx + 1
            for col_num in range(1, len(data_row) + 1):
                cell = ws.cell(row=row_num, column=col_num)
                cell.alignment = center_align
                cell.border = thin_border
                if col_num == 8: # Nota
                    cell.font = Font(bold=True)
                    
        # Autoajustar anchos de columna
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)
            
        wb.save(output_excel)
        print(f"✅ Resultados exportados exitosamente a: {output_excel}")
        return output_excel

    def rasterize_pdf_page(self, pdf_path, page_num=0, dpi=300):
        """Convierte una página de PDF a imagen OpenCV (numpy array)."""
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_num)
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        doc.close()
        return img

    def process_scanned_pdf(self, pdf_path, progress_callback=None):
        """
        Procesa un archivo PDF escaneado (de 1 o N páginas) que contiene fichas OMR.
        Detecta automáticamente:
          - Si la página es una ficha completa (30% Identificación + 70% Respuestas).
          - Si la página es solo una mitad desglosada (solo Identificación o solo Respuestas).
        Registra cada sección en la base de datos vinculada a su código de barras.
        """
        import pyzbar.pyzbar as pyzbar
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"Iniciando procesamiento de PDF escaneado: {pdf_path} ({total_pages} páginas)...")
        
        for page_idx in range(total_pages):
            img_bgr = self.rasterize_pdf_page(pdf_path, page_num=page_idx, dpi=300)
            h, w = img_bgr.shape[:2]
            
            # Línea estimada de corte (30% en X = 95mm sobre 297mm)
            cut_x = int((95.0 / 297.0) * w)
            left_half = img_bgr[:, :cut_x]
            right_half = img_bgr[:, cut_x:]
            
            # 1. Comprobar si es hoja completa (tiene ambos códigos o marcadores en ambos lados)
            b_left = pyzbar.decode(left_half)
            b_right = pyzbar.decode(right_half)
            
            # Procesar Mitad Izquierda (Identificación)
            code_id = b_left[0].data.decode('utf-8') if b_left else None
            m_left = self.engine.find_fiducial_markers(left_half)
            if len(m_left) == 4:
                pts_l = [(m[0], m[1]) for m in m_left]
                aligned_l, _ = self.engine.align_quad(left_half, pts_l, out_w=800, out_h=1500)
                student_id = self.engine.read_identification_section(aligned_l)
                if not code_id:
                    # Intentar leer código de barras en la imagen alineada
                    b_al = pyzbar.decode(aligned_l)
                    if b_al: code_id = b_al[0].data.decode('utf-8')
                if code_id and student_id:
                    self.register_identification(code_id, student_id)
                    print(f"   [Pág {page_idx+1}] Identificación registrada: {code_id} -> DNI: {student_id}")

            # Procesar Mitad Derecha (Respuestas)
            code_ans = b_right[0].data.decode('utf-8') if b_right else None
            m_right = self.engine.find_fiducial_markers(right_half)
            if len(m_right) == 4:
                pts_r = [(m[0], m[1]) for m in m_right]
                aligned_r, _ = self.engine.align_quad(right_half, pts_r, out_w=1500, out_h=1500)
                answers = self.engine.read_answers_section(aligned_r)
                if not code_ans:
                    b_ar = pyzbar.decode(aligned_r)
                    if b_ar: code_ans = b_ar[0].data.decode('utf-8')
                if code_ans and answers:
                    self.register_answers(code_ans, answers)
                    theme = answers.get("_THEME_", "SIN_TEMA")
                    print(f"   [Pág {page_idx+1}] Respuestas registradas: {code_ans} -> Tema: {theme}")
                    
            if progress_callback:
                progress_callback(page_idx + 1, total_pages)
                
        doc.close()
        print("✅ Procesamiento de páginas finalizado.")
