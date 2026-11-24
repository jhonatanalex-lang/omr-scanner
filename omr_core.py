"""
Motor Central de Visión por Computadora para OMR (OpenCV)
Capacidades:
  1. Detecta los 4 marcadores de esquina fiduciarios de una hoja o sección escaneada.
  2. Corrige perspectiva isométrica (warpPerspective).
  3. Muestrea las burbujas basándose en template_coords.json.
  4. Extrae marcas válidas utilizando densidad relativa de píxeles y contraste local.
"""

import cv2
import numpy as np
import json
import os

class OMREngine:
    def __init__(self, template_json_path="template_coords.json", target_w=1200, target_h=1600):
        self.target_w = target_w
        self.target_h = target_h
        
        with open(template_json_path, "r", encoding="utf-8") as f:
            self.template = json.load(f)

    def order_points(self, pts):
        """
        Ordena 4 puntos en el sentido:
        [top-left, top-right, bottom-right, bottom-left]
        """
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)] # top-left tiene la suma x+y menor
        rect[2] = pts[np.argmax(s)] # bottom-right tiene la suma x+y mayor
        
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)] # top-right tiene la menor diferencia y-x
        rect[3] = pts[np.argmax(diff)] # bottom-left tiene la mayor diferencia y-x
        return rect

    def find_fiducial_markers(self, image):
        """
        Localiza los marcadores cuadrados fiduciarios sólidos en las esquinas de la imagen.
        Devuelve exactamente los 4 marcadores de las esquinas extremas.
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 25, 7
        )
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        markers = []
        img_h, img_w = gray.shape[:2]
        img_area = img_w * img_h
        
        for c in contours:
            area = cv2.contourArea(c)
            # El marcador es de 8x8mm en una hoja de ~140x210mm (~0.2% del área)
            if area < img_area * 0.0005 or area > img_area * 0.03:
                continue
                
            x, y, w, h = cv2.boundingRect(c)
            aspect_ratio = float(w) / h
            
            # Debe ser estrictamente cuadrado
            if 0.8 <= aspect_ratio <= 1.2:
                hull = cv2.convexHull(c)
                hull_area = cv2.contourArea(hull)
                if hull_area > 0 and (area / hull_area) > 0.85: # Cuadrado sólido relleno
                    M = cv2.moments(c)
                    if M["m00"] != 0:
                        cX = int(M["m10"] / M["m00"])
                        cY = int(M["m01"] / M["m00"])
                        markers.append((cX, cY, area))
                        
        if len(markers) < 4:
            return markers
            
        # Si hay más candidatos por casillas cuadradas, seleccionar los 4 más cercanos a las 4 esquinas extremas
        # Top-Left (min x+y), Top-Right (max x - y), Bottom-Right (max x+y), Bottom-Left (min x - y)
        pts = np.array([(m[0], m[1]) for m in markers])
        
        tl = pts[np.argmin(pts[:, 0] + pts[:, 1])]
        br = pts[np.argmax(pts[:, 0] + pts[:, 1])]
        tr = pts[np.argmax(pts[:, 0] - pts[:, 1])]
        bl = pts[np.argmin(pts[:, 0] - pts[:, 1])]
        
        selected = [tuple(tl), tuple(tr), tuple(br), tuple(bl)]
        return [(p[0], p[1], 1000) for p in selected]

    def align_quad(self, image, four_points, out_w=None, out_h=None):
        """
        Aplica transformación de perspectiva ortogonal dada por 4 puntos ordenados.
        """
        w = out_w or self.target_w
        h = out_h or self.target_h
        
        ordered_pts = self.order_points(np.array(four_points, dtype="float32"))
        
        dst = np.array([
            [0, 0],
            [w - 1, 0],
            [w - 1, h - 1],
            [0, h - 1]
        ], dtype="float32")
        
        M = cv2.getPerspectiveTransform(ordered_pts, dst)
        warped = cv2.warpPerspective(image, M, (w, h))
        return warped, M

    def read_answers_section(self, aligned_img):
        """
        Lee las respuestas desde una sección de respuestas alineada ortogonalmente.
        aligned_img: tamaño (self.target_w, self.target_h)
        """
        if len(aligned_img.shape) == 3:
            gray = cv2.cvtColor(aligned_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = aligned_img
            
        # Invertir para que marcas negras sean valor alto
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        answers_cfg = self.template["sections"]["answers"]
        
        # 1. Leer Tema del Examen (P, Q, R, S, T, U) si está presente
        detected_theme = "SIN_TEMA"
        if "theme_bubbles" in answers_cfg:
            theme_scores = []
            h, w = gray.shape
            r = int(w * 0.010)
            for tb in answers_cfg["theme_bubbles"]:
                px_x = int(tb["norm_x"] * w)
                px_y = int((1.0 - tb["norm_y"]) * h)
                roi = binary[max(0, px_y - r):min(h, px_y + r), max(0, px_x - r):min(w, px_x + r)]
                fill_score = cv2.countNonZero(roi) / (roi.size + 1e-5) if roi.size > 0 else 0
                theme_scores.append((tb["theme"], fill_score))
                
            theme_scores_sorted = sorted(theme_scores, key=lambda x: x[1], reverse=True)
            t_top1 = theme_scores_sorted[0]
            t_top2 = theme_scores_sorted[1]
            if t_top1[1] >= 0.18 and (t_top1[1] - t_top2[1]) >= 0.035:
                detected_theme = t_top1[0]
            elif t_top1[1] >= 0.18:
                detected_theme = "MULTIPLE_THEME"
                
        # 2. Leer Preguntas
        bubbles = answers_cfg["bubbles"]
        questions = {}
        h, w = gray.shape
        r = int(w * 0.010)
        
        for b in bubbles:
            q = b["question"]
            if q not in questions:
                questions[q] = []
                
            px_x = int(b["norm_x"] * w)
            px_y = int((1.0 - b["norm_y"]) * h)
            
            roi = binary[max(0, px_y - r):min(h, px_y + r), max(0, px_x - r):min(w, px_x + r)]
            fill_score = cv2.countNonZero(roi) / (roi.size + 1e-5) if roi.size > 0 else 0
            questions[q].append({
                "option": b["option"],
                "score": fill_score
            })
            
        results = {"_THEME_": detected_theme}
        for q, opts in sorted(questions.items()):
            opts_sorted = sorted(opts, key=lambda x: x["score"], reverse=True)
            top1 = opts_sorted[0]
            top2 = opts_sorted[1]
            
            if top1["score"] >= 0.18 and (top1["score"] - top2["score"]) >= 0.035:
                results[f"Q{q:02d}"] = top1["option"]
            elif top1["score"] >= 0.18 and (top1["score"] - top2["score"]) < 0.035:
                results[f"Q{q:02d}"] = "MULTIPLE_MARK"
            else:
                results[f"Q{q:02d}"] = "BLANK"
                
        return results
                
        return results

    def read_identification_section(self, aligned_img):
        """
        Lee el DNI / código de estudiante desde la sección de identificación alineada.
        """
        if len(aligned_img.shape) == 3:
            gray = cv2.cvtColor(aligned_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = aligned_img
            
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        id_cfg = self.template["sections"]["identification"]
        bubbles = id_cfg["bubbles"]
        
        # Agrupar por columna de dígito (0 a 7)
        digits = {i: [] for i in range(id_cfg["num_digits"])}
        h, w = gray.shape
        
        for b in bubbles:
            col = b["digit_index"]
            px_x = int(b["norm_x"] * w)
            px_y = int((1.0 - b["norm_y"]) * h)
            
            r = int(w * 0.012)
            roi = binary[max(0, px_y - r):min(h, px_y + r), max(0, px_x - r):min(w, px_x + r)]
            fill_score = cv2.countNonZero(roi) / (roi.size + 1e-5) if roi.size > 0 else 0
            
            digits[col].append({
                "value": b["value"],
                "score": fill_score
            })
            
        student_id = ""
        for col, values in sorted(digits.items()):
            values_sorted = sorted(values, key=lambda x: x["score"], reverse=True)
            top1 = values_sorted[0]
            top2 = values_sorted[1]
            
            if top1["score"] >= 0.18 and (top1["score"] - top2["score"]) >= 0.035:
                student_id += str(top1["value"])
            else:
                student_id += "?" # Dígito dudoso o vacío
                
        return student_id
