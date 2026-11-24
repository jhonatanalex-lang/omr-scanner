"""
Aplicación de Escritorio OMR (Desktop GUI) - Versión Completa
Pestañas:
  1. Calificador de Lotes:
     - Selección de clave y pesos.
     - Carga de PDF escaneado con barra de progreso.
     - Tabla interactiva de resultados y conciliación.
     - Exportación a Excel.
  2. Generador Masivo para Impresión:
     - Configuración de prefijo (ej: OMR-2026).
     - Número de inicio (ej: 1).
     - Cantidad de hojas a imprimir (ej: 100, 300, 500).
     - Generación instantánea de PDF multipágina listo para imprenta.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import json
import cv2
import numpy as np
from batch_processor import OMRBatchProcessor
from generate_batch_sheets import generate_mass_omr_sheets

class OMRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OMR Grader Suite - Calificador de Fichas Oficiales (30/70)")
        self.root.geometry("860x650")
        self.root.minsize(750, 550)
        
        self.processor = OMRBatchProcessor(db_path="omr_production.db")
        self.load_sample_key() # Cargar claves multitema por defecto al iniciar
        self.setup_ui()

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        # Header banner
        header = tk.Frame(self.root, bg="#1F4E79", height=65)
        header.pack(fill=tk.X, side=tk.TOP)
        header_title = tk.Label(
            header, text="Sistema de Calificación OMR (80 Preguntas)", 
            fg="white", bg="#1F4E79", font=("Segoe UI", 15, "bold")
        )
        header_title.pack(anchor="w", padx=20, pady=(10, 2))
        header_sub = tk.Label(
            header, text="Fichas Desglosables 30/70 • Código de Barras Code128 • SQLite • Excel", 
            fg="#D9E1F2", bg="#1F4E79", font=("Segoe UI", 9)
        )
        header_sub.pack(anchor="w", padx=20, pady=(0, 10))

        # Notebook (Pestañas)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Calificación
        tab_grade = ttk.Frame(notebook, padding=12)
        notebook.add(tab_grade, text=" 📊 Calificar Exámenes ")

        # Tab 2: Generador Masivo
        tab_generate = ttk.Frame(notebook, padding=15)
        notebook.add(tab_generate, text=" 🖨️ Generar Hojas para Imprenta ")

        self._setup_grading_tab(tab_grade)
        self._setup_generator_tab(tab_generate)

    def _setup_grading_tab(self, parent):
        # Panel 1: Configuración de Clave
        cfg_frame = ttk.LabelFrame(parent, text=" 1. Clave de Respuestas y Puntuación ", padding=10)
        cfg_frame.pack(fill=tk.X, pady=(0, 10))

        row1 = ttk.Frame(cfg_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="Correcta:").pack(side=tk.LEFT, padx=(0, 2))
        self.correct_score_var = tk.StringVar(value="5.0")
        ttk.Entry(row1, textvariable=self.correct_score_var, width=5).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(row1, text="Incorrecta:").pack(side=tk.LEFT, padx=(0, 2))
        self.incorrect_score_var = tk.StringVar(value="0.0")
        ttk.Entry(row1, textvariable=self.incorrect_score_var, width=5).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(row1, text="En Blanco:").pack(side=tk.LEFT, padx=(0, 2))
        self.blank_score_var = tk.StringVar(value="1.0")
        ttk.Entry(row1, textvariable=self.blank_score_var, width=5).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(row1, text="Doble Marca:").pack(side=tk.LEFT, padx=(0, 2))
        self.multiple_score_var = tk.StringVar(value="0.0")
        ttk.Entry(row1, textvariable=self.multiple_score_var, width=5).pack(side=tk.LEFT, padx=(0, 15))

        self.key_status_var = tk.StringVar(value="Claves: P, Q, R, S, T, U (Escala 0 - 20)")
        ttk.Button(row1, text="⚙️ Administrar Claves...", command=self.open_multitheme_dialog).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(row1, textvariable=self.key_status_var, font=("Segoe UI", 8, "italic"), foreground="#1F4E79").pack(side=tk.LEFT)

        # Panel 2: Archivo Escaneado
        batch_frame = ttk.LabelFrame(parent, text=" 2. Ingesta de Fichas Escaneadas (PDF o Imágenes) ", padding=10)
        batch_frame.pack(fill=tk.X, pady=(0, 10))

        row2 = ttk.Frame(batch_frame)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="Archivo PDF:").pack(side=tk.LEFT, padx=(0, 5))
        self.file_path_var = tk.StringVar(value="")
        ttk.Entry(row2, textvariable=self.file_path_var, width=45).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        ttk.Button(row2, text="Examinar...", command=self.browse_pdf).pack(side=tk.LEFT, padx=(0, 5))
        self.process_btn = ttk.Button(row2, text="▶ Calificar Lote", command=self.start_processing)
        self.process_btn.pack(side=tk.LEFT)

        self.progress_bar = ttk.Progressbar(batch_frame, mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=(8, 0))
        self.status_lbl = ttk.Label(batch_frame, text="Listo para procesar.")
        self.status_lbl.pack(anchor="w", pady=(4, 0))

        # Panel 3: Resultados
        results_frame = ttk.LabelFrame(parent, text=" 3. Resultados Consolidados ", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("pos", "code", "dni", "theme", "correct", "incorrect", "blank", "multiple", "raw", "score", "status")
        self.tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=7)
        self.tree.heading("pos", text="#")
        self.tree.heading("code", text="Código Hoja")
        self.tree.heading("dni", text="DNI / Estudiante")
        self.tree.heading("theme", text="Tema")
        self.tree.heading("correct", text="Buenas (+5)")
        self.tree.heading("incorrect", text="Malas (0)")
        self.tree.heading("blank", text="Blancas (+1)")
        self.tree.heading("multiple", text="Dobles (0)")
        self.tree.heading("raw", text="Ptos Brutos")
        self.tree.heading("score", text="Nota (0-20)")
        self.tree.heading("status", text="Estado Conciliación")

        self.tree.column("pos", width=35, anchor="center")
        self.tree.column("code", width=105, anchor="center")
        self.tree.column("dni", width=105, anchor="center")
        self.tree.column("theme", width=50, anchor="center")
        self.tree.column("correct", width=75, anchor="center")
        self.tree.column("incorrect", width=65, anchor="center")
        self.tree.column("blank", width=75, anchor="center")
        self.tree.column("multiple", width=70, anchor="center")
        self.tree.column("raw", width=80, anchor="center")
        self.tree.column("score", width=85, anchor="center")
        self.tree.column("status", width=150, anchor="center")

        tree_scroll = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Evento doble clic para Auditoría Visual
        self.tree.bind("<Double-1>", self.open_visual_auditor)

        footer = ttk.Frame(parent)
        footer.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(footer, text="📥 Exportar Resultados a Excel (.xlsx)", command=self.export_excel).pack(side=tk.RIGHT)

    def _setup_generator_tab(self, parent):
        box = ttk.LabelFrame(parent, text=" Configuración de Serialización Masiva para Impresión ", padding=20)
        box.pack(fill=tk.BOTH, expand=True)

        info = ttk.Label(
            box, 
            text="Esta herramienta genera un único archivo PDF listo para enviar a la imprenta o fotocopiadora.\n"
                 "Cada página A4 tendrá su código correlativo único y sus dos códigos de barras Code128 correspondientes.",
            font=("Segoe UI", 9)
        )
        info.pack(anchor="w", pady=(0, 20))

        grid = ttk.Frame(box)
        grid.pack(fill=tk.X, pady=5)

        ttk.Label(grid, text="Prefijo del Examen:").grid(row=0, column=0, sticky="w", pady=6)
        self.prefix_var = tk.StringVar(value="OMR-2026")
        ttk.Entry(grid, textvariable=self.prefix_var, width=15).grid(row=0, column=1, sticky="w", padx=10, pady=6)

        ttk.Label(grid, text="Número Inicial:").grid(row=1, column=0, sticky="w", pady=6)
        self.start_num_var = tk.StringVar(value="1")
        ttk.Entry(grid, textvariable=self.start_num_var, width=15).grid(row=1, column=1, sticky="w", padx=10, pady=6)

        ttk.Label(grid, text="Cantidad de Hojas a Imprimir:").grid(row=2, column=0, sticky="w", pady=6)
        self.qty_var = tk.StringVar(value="100")
        ttk.Entry(grid, textvariable=self.qty_var, width=15).grid(row=2, column=1, sticky="w", padx=10, pady=6)

        self.gen_progress = ttk.Progressbar(box, mode="determinate")
        self.gen_progress.pack(fill=tk.X, pady=(20, 5))
        self.gen_status_lbl = ttk.Label(box, text="Listo para generar.")
        self.gen_status_lbl.pack(anchor="w", pady=(0, 15))

        btn_row = ttk.Frame(box)
        btn_row.pack(fill=tk.X)
        self.generate_btn = ttk.Button(btn_row, text="📄 Generar Lote PDF para Impresión", command=self.start_mass_generation)
        self.generate_btn.pack(side=tk.LEFT)

    def load_sample_key(self):
        # Generar claves multitema automáticas para P, Q, R, S, T, U
        opts = ['A', 'B', 'C', 'D', 'E']
        self.multitheme_keys = {}
        for idx, t in enumerate(['P', 'Q', 'R', 'S', 'T', 'U']):
            # Desplazar cíclicamente para que cada tema tenga una clave diferente
            self.multitheme_keys[t] = {
                f"Q{i:02d}": opts[(i - 1 + idx) % 5] for i in range(1, 81)
            }
        self.teacher_key = self.multitheme_keys

    def open_multitheme_dialog(self):
        if not hasattr(self, "multitheme_keys"):
            self.load_sample_key()

        dialog = tk.Toplevel(self.root)
        dialog.title("Administrador de Claves Multitema (P, Q, R, S, T, U)")
        dialog.geometry("520x420")
        dialog.transient(self.root)
        dialog.grab_set()

        top_info = ttk.Label(
            dialog, 
            text="Selecciona el Tema y edita la clave de respuestas.\n"
                 "El motor OMR evaluará a cada estudiante según el tema que haya marcado.",
            font=("Segoe UI", 9)
        )
        top_info.pack(padx=15, pady=10, anchor="w")

        selector_frame = ttk.Frame(dialog)
        selector_frame.pack(fill=tk.X, padx=15, pady=5)

        ttk.Label(selector_frame, text="Tema a configurar:").pack(side=tk.LEFT, padx=(0, 10))
        theme_combo = ttk.Combobox(selector_frame, values=['P', 'Q', 'R', 'S', 'T', 'U'], state="readonly", width=6)
        theme_combo.set('P')
        theme_combo.pack(side=tk.LEFT)

        text_frame = ttk.Frame(dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        txt_keys = tk.Text(text_frame, wrap="none", font=("Consolas", 10))
        txt_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=txt_keys.yview)
        txt_keys.configure(yscrollcommand=txt_scroll.set)
        txt_keys.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        txt_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        def display_theme_keys(event=None):
            t = theme_combo.get()
            k_dict = self.multitheme_keys.get(t, {})
            lines = [f"{q}={opt}" for q, opt in sorted(k_dict.items())]
            txt_keys.delete("1.0", tk.END)
            txt_keys.insert(tk.END, "\n".join(lines))

        theme_combo.bind("<<ComboboxSelected>>", display_theme_keys)
        display_theme_keys()

        def save_current_theme():
            t = theme_combo.get()
            content = txt_keys.get("1.0", tk.END).strip().splitlines()
            new_dict = {}
            for line in content:
                if "=" in line:
                    q, opt = line.split("=", 1)
                    q = q.strip().upper()
                    opt = opt.strip().upper()
                    if opt in ['A', 'B', 'C', 'D', 'E']:
                        new_dict[q] = opt
            if len(new_dict) > 0:
                self.multitheme_keys[t] = new_dict
                self.teacher_key = self.multitheme_keys
                messagebox.showinfo("Guardado", f"Clave para Tema {t} guardada exitosamente ({len(new_dict)} preguntas).", parent=dialog)

        btn_row = ttk.Frame(dialog)
        btn_row.pack(fill=tk.X, padx=15, pady=(0, 15))
        ttk.Button(btn_row, text="💾 Guardar Cambios para este Tema", command=save_current_theme).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Cerrar", command=dialog.destroy).pack(side=tk.RIGHT)

    def browse_pdf(self):
        filename = filedialog.askopenfilename(
            title="Seleccionar PDF Escaneado",
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
        self.status_lbl.config(text="Procesando fichas con OpenCV y SQLite...")
        self.progress_bar["value"] = 30
        
        threading.Thread(target=self._process_worker, args=(file_path,), daemon=True).start()

    def _process_worker(self, file_path):
        try:
            def update_progress(cur, total):
                pct = int((cur / total) * 70)
                self.root.after(0, lambda: self.progress_bar.configure(value=pct))
                self.root.after(0, lambda: self.status_lbl.configure(text=f"Escaneando y leyendo página {cur} de {total}..."))
                
            # 1. Procesar el archivo PDF escaneado (leer códigos de barra, DNI y burbujas)
            self.processor.process_scanned_pdf(file_path, progress_callback=update_progress)
            
            # 2. Conciliar y Calificar contra las claves
            self.root.after(0, lambda: self.status_lbl.configure(text="Conciliando identificaciones y calificando..."))
            self.root.after(0, lambda: self.progress_bar.configure(value=85))
            
            results = self.processor.reconcile_and_grade(
                self.teacher_key, 
                score_correct=float(self.correct_score_var.get()),
                score_incorrect=float(self.incorrect_score_var.get()),
                score_blank=float(self.blank_score_var.get()),
                score_multiple=float(self.multiple_score_var.get())
            )
            # Actualizar interfaz de forma directa y segura
            self.root.after(0, lambda res=results: self._update_table(res))
        except Exception as err:
            err_msg = str(err)
            self.root.after(0, lambda: messagebox.showerror("Error al Calificar", err_msg))
        finally:
            self.root.after(0, lambda: self.process_btn.config(state=tk.NORMAL))

    def _update_table(self, results):
        self.progress_bar["value"] = 100
        self.status_lbl.config(text=f"Finalizado. {len(results)} registros procesados.")
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for idx, r in enumerate(results, start=1):
            self.tree.insert("", tk.END, values=(
                idx, r["sheet_code"], r["student_id"], r.get("theme", "N/A"),
                r["correct"], r["incorrect"], r["blank"], r.get("multiple", 0),
                f"{r.get('raw_score', 0):.1f}", f"{r['final_score']:.2f}", r["status"]
            ))

    def open_visual_auditor(self, event=None):
        selected_item = self.tree.focus()
        if not selected_item:
            return
            
        values = self.tree.item(selected_item, "values")
        if not values:
            return
            
        sheet_code = values[1]
        student_id = values[2]
        theme = values[3]
        score = values[7]
        
        # Abrir ventana de auditoría visual
        win = tk.Toplevel(self.root)
        win.title(f"Auditor Visual OMR - Ficha: {sheet_code} (DNI: {student_id})")
        win.geometry("900x700")
        win.minsize(750, 550)
        
        top_bar = tk.Frame(win, bg="#1F4E79", height=40)
        top_bar.pack(fill=tk.X, side=tk.TOP)
        
        info_txt = f"Hoja: {sheet_code}  |  DNI: {student_id}  |  Tema: {theme}  |  Nota: {score} pts"
        tk.Label(top_bar, text=info_txt, fg="white", bg="#1F4E79", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=15, pady=8)
        
        # Leyenda de Colores
        leg_frame = ttk.Frame(win, padding=6)
        leg_frame.pack(fill=tk.X)
        ttk.Label(leg_frame, text="Leyenda: ", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Label(leg_frame, text="● Opción Correcta Marcada", foreground="green", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=8)
        ttk.Label(leg_frame, text="● Opción Incorrecta Marcada", foreground="red", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=8)
        ttk.Label(leg_frame, text="● Respuesta Correcta No Marcada", foreground="#0070C0", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=8)
        ttk.Label(leg_frame, text="● Doble Marca / Dudosa", foreground="orange", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=8)

        # Canvas con Scroll para ver la hoja auditada
        canvas_frame = ttk.Frame(win)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        cv = tk.Canvas(canvas_frame, bg="#EAEAEA")
        v_bar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=cv.yview)
        h_bar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=cv.xview)
        cv.configure(xscrollcommand=h_bar.set, yscrollcommand=v_bar.set)
        
        v_bar.pack(side=tk.RIGHT, fill=tk.Y)
        h_bar.pack(side=tk.BOTTOM, fill=tk.X)
        cv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Generar o cargar imagen de auditoría sobre la hoja real del alumno
        try:
            import sqlite3
            from PIL import Image, ImageTk
            conn = sqlite3.connect(self.processor.db_path)
            cur = conn.cursor()
            cur.execute("SELECT answers_json, aligned_image_path FROM answer_sheets WHERE sheet_code = ?", (sheet_code,))
            row = cur.fetchone()
            conn.close()
            
            if row and row[0]:
                st_answers = json.loads(row[0])
            else:
                st_answers = {}
                
            real_img_path = row[1] if row and len(row) > 1 and row[1] else None
            
            # Obtener la clave respectiva según el tema del alumno
            t_key = self.teacher_key.get(theme) if isinstance(self.teacher_key, dict) and theme in self.teacher_key else self.teacher_key
            if isinstance(t_key, dict) and any(k in ["P", "Q", "R", "S", "T", "U"] for k in t_key.keys()):
                t_key = t_key.get("P", {})
                
            engine = self.processor.engine
            
            if real_img_path and os.path.exists(real_img_path):
                # Usar la imagen escaneada REAL del alumno
                base_img = cv2.imread(real_img_path)
            else:
                # Si no tiene imagen escaneada, usar fondo blanco neutro
                base_img = np.ones((1500, 1500, 3), dtype=np.uint8) * 255
                
            # Generar overlay dinámico con las respuestas reales de este examen
            audit_overlay = engine.generate_audit_overlay(base_img, st_answers, t_key)
            
            # Guardar temporal para visualización
            os.makedirs("temp_preview", exist_ok=True)
            temp_overlay_path = os.path.join("temp_preview", f"audit_{sheet_code}.png")
            cv2.imwrite(temp_overlay_path, audit_overlay)
                
            pil_img = Image.open(temp_overlay_path)
            # Escalar a tamaño de visualización ergonómico
            disp_w = 800
            disp_h = int((disp_w / pil_img.width) * pil_img.height)
            pil_resized = pil_img.resize((disp_w, disp_h), Image.Resampling.LANCZOS)
            
            tk_img = ImageTk.PhotoImage(pil_resized)
            cv.image_ref = tk_img
            cv.create_image(15, 15, anchor="nw", image=tk_img)
            cv.config(scrollregion=(0, 0, disp_w + 30, disp_h + 30))
        except Exception as err:
            cv.create_text(200, 100, text=f"No se pudo cargar la vista de imagen:\n{str(err)}", fill="red", font=("Segoe UI", 10))

    def export_excel(self):
        try:
            path = self.processor.export_to_excel("resultados_examen.xlsx")
            messagebox.showinfo("Exportación Exitosa", f"Archivo generado:\n{os.path.abspath(path)}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def start_mass_generation(self):
        try:
            prefix = self.prefix_var.get().strip()
            start_num = int(self.start_num_var.get())
            qty = int(self.qty_var.get())
        except ValueError:
            messagebox.showerror("Datos inválidos", "Número inicial y cantidad deben ser números enteros.")
            return

        save_path = filedialog.asksaveasfilename(
            title="Guardar PDF de Lote",
            defaultextension=".pdf",
            initialfile=f"lote_impresion_{qty}_fichas.pdf",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if not save_path:
            return

        self.generate_btn.config(state=tk.DISABLED)
        self.gen_status_lbl.config(text=f"Generando {qty} páginas vectoriales en PDF...")
        self.gen_progress["value"] = 0

        def _worker():
            try:
                def prog(cur, total):
                    pct = int((cur / total) * 100)
                    self.root.after(0, lambda: self.gen_progress.configure(value=pct))
                    self.root.after(0, lambda: self.gen_status_lbl.configure(text=f"Generando página {cur} de {total}..."))

                generate_mass_omr_sheets(
                    output_pdf=save_path,
                    prefix=prefix,
                    start_num=start_num,
                    quantity=qty,
                    progress_callback=prog
                )
                self.root.after(0, lambda: messagebox.showinfo(
                    "Lote Generado con Éxito", 
                    f"Se ha generado el archivo PDF con {qty} páginas correlativas:\n{os.path.abspath(save_path)}"
                ))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, lambda: self.generate_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.gen_status_lbl.config(text="Listo."))

        threading.Thread(target=_worker, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = OMRApp(root)
    root.mainloop()
