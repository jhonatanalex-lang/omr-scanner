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
                correct_count INTEGER,
                incorrect_count INTEGER,
                blank_count INTEGER,
                final_score REAL,
                status TEXT
            )
        """)
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

    def reconcile_and_grade(self, answer_key, score_correct=1.0, score_incorrect=-0.25):
        """
        Realiza el JOIN relacional entre Identificación y Respuestas,
        calcula la nota y detecta fichas huérfanas.
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Consulta de conciliación FULL OUTER (simulada en SQLite vía LEFT + UNION)
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
                correct, incorrect, blank, score = 0, 0, 0, 0.0
            elif not answers_json:
                status = "ORPHAN_IDENTIFICATION (Falta ficha de respuestas)"
                correct, incorrect, blank, score = 0, 0, 0, 0.0
            else:
                status = "MATCHED (Calificada)"
                answers = json.loads(answers_json)
                correct, incorrect, blank = 0, 0, 0
                
                for q_key, correct_val in answer_key.items():
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
                (sheet_code, student_id, correct_count, incorrect_count, blank_count, final_score, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (sheet_code, student_id or "UNKNOWN", correct, incorrect, blank, score, status))
            
            results.append({
                "sheet_code": sheet_code,
                "student_id": student_id or "DESCONOCIDO",
                "status": status,
                "score": score,
                "correct": correct,
                "incorrect": incorrect,
                "blank": blank
            })
            
        conn.commit()
        conn.close()
        return results

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
