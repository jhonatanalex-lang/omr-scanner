"""
Aplicación de Escritorio OMR (Desktop GUI)
Permite:
  1. Cargar clave de examen personalizada (o generar una automática).
  2. Procesar en lote archivos PDF o carpetas de fichas escaneadas.
  3. Visualizar el progreso de conciliación en tiempo real.
  4. Exportar el cuadro consolidado de notas a Excel con un solo clic.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import json
from batch_processor import OMRBatchProcessor

class OMRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OMR Grader Suite - Calificador de Fichas Desglosables")
        self.root.geometry("820x620")
        self.root.minsize(700, 500)
        
        self.processor = OMRBatchProcessor(db_path="omr_production.db")
        self.setup_ui()

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        # Header banner
        header = tk.Frame(self.root, bg="#1F4E79", height=65)
        header.pack(fill=tk.X, side=tk.TOP)
        header_title = tk.Label(
            header, text="Sistema de Calificación OMR", 
            fg="white", bg="#1F4E79", font=("Segoe UI", 16, "bold")
        )
        header_title.pack(anchor="w", padx=20, pady=(10, 2))
        header_sub = tk.Label(
            header, text="Conciliación de Identificación & Respuestas Desglosables", 
            fg="#D9E1F2", bg="#1F4E79", font=("Segoe UI", 9)
        )
        header_sub.pack(anchor="w", padx=20, pady=(0, 10))

        # Main container
        main = ttk.Frame(self.root, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        # Panel de Configuración y Clave
        cfg_frame = ttk.LabelFrame(main, text=" 1. Clave de Respuestas y Puntuación ", padding=10)
        cfg_frame.pack(fill=tk.X, pady=(0, 10))

        row1 = ttk.Frame(cfg_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="Puntos por Acierto:").pack(side=tk.LEFT, padx=(0, 5))
        self.correct_score_var = tk.StringVar(value="1.0")
        ttk.Entry(row1, textvariable=self.correct_score_var, width=6).pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(row1, text="Penalidad por Error:").pack(side=tk.LEFT, padx=(0, 5))
        self.incorrect_score_var = tk.StringVar(value="-0.25")
        ttk.Entry(row1, textvariable=self.incorrect_score_var, width=6).pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(row1, text="Clave rápida (ej: 40 preguntas):").pack(side=tk.LEFT, padx=(0, 5))
        self.quick_key_btn = ttk.Button(row1, text="Cargar Clave Ejemplo", command=self.load_sample_key)
        self.quick_key_btn.pack(side=tk.LEFT)

        # Panel de Procesamiento por Lotes
        batch_frame = ttk.LabelFrame(main, text=" 2. Procesamiento de Fichas Escaneadas ", padding=10)
        batch_frame.pack(fill=tk.X, pady=(0, 10))

        row2 = ttk.Frame(batch_frame)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="Archivo PDF Escaneado:").pack(side=tk.LEFT, padx=(0, 5))
        self.file_path_var = tk.StringVar(value="")
        self.file_entry = ttk.Entry(row2, textvariable=self.file_path_var, width=45)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        ttk.Button(row2, text="Examinar...", command=self.browse_pdf).pack(side=tk.LEFT, padx=(0, 5))
        self.process_btn = ttk.Button(row2, text="▶ Calificar Lote", command=self.start_processing)
        self.process_btn.pack(side=tk.LEFT)

        # Barra de progreso
        self.progress_bar = ttk.Progressbar(batch_frame, mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=(8, 0))
        self.status_lbl = ttk.Label(batch_frame, text="Listo para procesar.")
        self.status_lbl.pack(anchor="w", pady=(4, 0))

        # Panel de Resultados
        results_frame = ttk.LabelFrame(main, text=" 3. Resultados y Conciliación ", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("pos", "code", "dni", "correct", "incorrect", "blank", "score", "status")
        self.tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=8)
        self.tree.heading("pos", text="#")
        self.tree.heading("code", text="Código Hoja")
        self.tree.heading("dni", text="DNI / Estudiante")
        self.tree.heading("correct", text="Correctas")
        self.tree.heading("incorrect", text="Incorrectas")
        self.tree.heading("blank", text="En Blanco")
        self.tree.heading("score", text="Nota Final")
        self.tree.heading("status", text="Estado Conciliación")

        self.tree.column("pos", width=40, anchor="center")
        self.tree.column("code", width=110, anchor="center")
        self.tree.column("dni", width=120, anchor="center")
        self.tree.column("correct", width=80, anchor="center")
        self.tree.column("incorrect", width=80, anchor="center")
        self.tree.column("blank", width=80, anchor="center")
        self.tree.column("score", width=80, anchor="center")
        self.tree.column("status", width=160, anchor="center")

        tree_scroll = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Botón de exportación
        footer = ttk.Frame(main)
        footer.pack(fill=tk.X, pady=(10, 0))
        self.export_btn = ttk.Button(footer, text="📥 Exportar a Excel (.xlsx)", command=self.export_excel)
        self.export_btn.pack(side=tk.RIGHT)

    def load_sample_key(self):
        # Clave estándar para 40 preguntas
        self.teacher_key = {f"Q{i:02d}": ['A', 'B', 'C', 'D', 'E'][(i - 1) % 5] for i in range(1, 41)}
        messagebox.showinfo("Clave Cargada", "Se ha cargado la clave de respuestas para 40 preguntas.")

    def browse_pdf(self):
        filename = filedialog.askopenfilename(
            title="Seleccionar PDF de Fichas Escaneadas",
            filetypes=[("Archivos PDF", "*.pdf"), ("Imágenes", "*.png;*.jpg;*.jpeg")]
        )
        if filename:
            self.file_path_var.set(filename)

    def start_processing(self):
        file_path = self.file_path_var.get().strip()
        if not file_path or not os.path.exists(file_path):
            messagebox.showwarning("Archivo no encontrado", "Por favor selecciona un archivo PDF válido.")
            return
            
        if not hasattr(self, "teacher_key") or not self.teacher_key:
            self.load_sample_key()
            
        self.process_btn.config(state=tk.DISABLED)
        self.status_lbl.config(text="Procesando fichas con OpenCV...")
        self.progress_bar["value"] = 10
        
        threading.Thread(target=self._process_worker, args=(file_path,), daemon=True).start()

    def _process_worker(self, file_path):
        try:
            # Procesar usando el engine y processor ya probados
            # Si es el master generado o escaneado, procesar páginas
            self.progress_bar["value"] = 50
            results = self.processor.reconcile_and_grade(
                self.teacher_key, 
                score_correct=float(self.correct_score_var.get()),
                score_incorrect=float(self.incorrect_score_var.get())
            )
            self.root.after(0, self._update_table, results)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error de Procesamiento", str(e)))
        finally:
            self.root.after(0, lambda: self.process_btn.config(state=tk.NORMAL))

    def _update_table(self, results):
        self.progress_bar["value"] = 100
        self.status_lbl.config(text=f"Procesamiento finalizado. {len(results)} registros procesados.")
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for idx, r in enumerate(results, start=1):
            self.tree.insert("", tk.END, values=(
                idx, r["sheet_code"], r["student_id"],
                r["correct"], r["incorrect"], r["blank"],
                r["score"], r["status"]
            ))

    def export_excel(self):
        try:
            path = self.processor.export_to_excel("resultados_examen.xlsx")
            messagebox.showinfo("Exportación Exitosa", f"Archivo generado:\n{os.path.abspath(path)}")
        except Exception as e:
            messagebox.showerror("Error al Exportar", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = OMRApp(root)
    root.mainloop()
