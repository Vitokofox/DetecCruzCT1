"""
Manejador de detecciones YOLO y mediciones.

Este módulo se encarga de:
- Cargar y ejecutar modelos YOLO
- Procesar detecciones y aplicar filtros ROI
- Realizar mediciones de piezas
- Detectar piezas quebradas con análisis avanzado
- Integración con PLC para alertas
"""

import os
import sys
import time
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import cv2
import numpy as np

from src.utils.utils import (
    pixel_to_real_units, 
    format_measurement, 
    suggest_scale_calibration,
    calcular_roi_coords,
    punto_en_roi,
    get_detection_color,
    log_detection,
    setup_torch_for_yolo,
    find_yolo_models,
    now_str
)
# Tracking completamente eliminado - sistema simplificado
from src.utils.broken_piece_analyzer import BrokenPieceAnalyzer, create_broken_piece_visualizer

# Importar handler robusto de YOLO
from src.services.yolo_handler import YOLOModelHandler

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
    print("✅ PyTorch configurado para cargar modelos YOLO (weights_only=False)")
except ImportError as e:
    YOLO_AVAILABLE = False
    print("⚠️ Ultralytics YOLO no está disponible")
    print(f"   Error de importación: {e}")
    # En ejecutables PyInstaller, esto es común pero puede funcionar igual
    if getattr(sys, 'frozen', False):
        print("   📦 Ejecutando desde ejecutable - intentando carga directa...")
        try:
            # Intento de importación alternativa para ejecutables
            import torch
            print("   ✅ PyTorch disponible en ejecutable")
            YOLO_AVAILABLE = True
        except ImportError:
            print("   ❌ PyTorch tampoco disponible")


class DetectionHandler:
    """
    Manejador principal de detecciones YOLO con medición y alertas.
    """
    
    def __init__(self, config, plc_service=None):
        """
        Inicializa el manejador de detecciones.
        
        Args:
            config: Instancia de CamConfig
            plc_service: Instancia de PLCService (opcional)
        """
        self.config = config
        self.plc_service = plc_service
        self.model: Optional['YOLO'] = None
        self.detecting = False
        
        # Handler robusto de YOLO
        self.yolo_handler = YOLOModelHandler()
        
        # Callbacks para eventos
        self.status_callback = None
        self.alert_callback = None
        
        # Historial de detecciones por cámara
        self.detection_history: Dict[int, List[Dict]] = {1: []}
        # Inicializar estado de movimiento de línea
        self.linea_en_movimiento: Dict[int, bool] = {1: False}
        self.movimiento_umbral_px = 10  # Umbral de desplazamiento en píxeles para considerar movimiento
        self.max_history_size = 10
        
        # Sistema de grabación de primera detección
        self.primera_guardada = {1: False}
        self.save_dir = os.path.join(os.getcwd(), "detecciones")
        os.makedirs(self.save_dir, exist_ok=True)
        
        # Sistema de conteo simplificado SIN tracking
        print("📊 Sistema de conteo directo inicializado (SIN tracking)")
        
        # Analizador avanzado de piezas quebradas
        self.broken_piece_analyzer = BrokenPieceAnalyzer(config)
        self.broken_piece_visualizer = create_broken_piece_visualizer()
        print("🔧 Analizador de piezas quebradas inicializado")
    
    def clear_detection_history(self):
        """
        Limpia el historial de detecciones.
        Útil para resetear el contador durante pruebas o al inicio de producción.
        """
        self.detection_history = {1: []}
        self.primera_guardada = {1: False}
        print("🧹 Historial de detecciones limpiado - Contador reiniciado")
    
    def get_detection_stats(self):
        """
        Obtiene estadísticas detalladas del contador de detecciones.
        
        Returns:
            Dict con estadísticas completas
        """
        stats = {
            'total_cam1': len(self.detection_history.get(1, [])),
            'total_general': len(self.detection_history.get(1, [])),  # Solo Cam1 cuenta
            'by_class': {},
            'broken_count': 0,
            'with_tracking': 0
        }
        
        # Analizar detecciones de Cam1 (las que cuentan)
        for detection in self.detection_history.get(1, []):
            label = detection.get('label', 'Desconocido')
            clean_label = label.split('_')[0] if '_' in label else label
            clean_label = clean_label.title()
            
            # No contar operador
            if 'Operador' not in clean_label.lower():
                stats['by_class'][clean_label] = stats['by_class'].get(clean_label, 0) + 1
            
            # Contar quebradas y con tracking
            if detection.get('is_broken', False):
                stats['broken_count'] += 1
            
            if detection.get('track_id', -1) != -1:
                stats['with_tracking'] += 1
        
        return stats
    
    def set_status_callback(self, callback):
        """Establece callback para actualizaciones de estado del modelo."""
        self.status_callback = callback
    
    def set_alert_callback(self, callback):
        """Establece callback para alertas de operador."""
        self.alert_callback = callback
    
    def _update_status(self, message: str):
        """Actualiza el estado del modelo."""
        if self.status_callback:
            self.status_callback(message)
        else:
            print(f"🧠 Modelo: {message}")
    
    def load_model(self, model_path: str = None) -> bool:
        """
        Carga un modelo YOLO usando el handler robusto.
        
        Args:
            model_path: Ruta específica del modelo (opcional)
            
        Returns:
            True si el modelo se cargó correctamente
        """
        try:
            self._update_status("Cargando modelo YOLO...")
            # Usar el handler robusto para cargar el modelo, pasando la ruta desde la config si no se especifica
            if model_path is None:
                model_path = getattr(self.config, 'model_path', None)
            success, message = self.yolo_handler.load_model(model_path)
            if success:
                self.model = self.yolo_handler.model
                if self.model:
                    if hasattr(self.model, 'names'):
                        num_classes = len(self.model.names)
                        class_names = list(self.model.names.values())
                        self._update_status(f"OK - Modelo cargado ({num_classes} clases)")
                        print(f"🚀 Modelo YOLO cargado exitosamente:")
                        print(f"   🎯 Clases: {num_classes} - {class_names}")
                    else:
                        self._update_status("OK - Modelo cargado")
                        print(f"🚀 Modelo YOLO cargado exitosamente")
                    return True
                else:
                    self._update_status("ERROR - Handler no devolvió modelo")
                    return False
            else:
                self._update_status(f"ERROR - {message}")
                print(f"❌ Error cargando modelo: {message}")
                return False
        except Exception as e:
            self._update_status(f"ERROR - Excepción: {str(e)}")
            print(f"💥 Error en load_model: {e}")
            return False
    
    def start_detection(self):
        """Inicia el sistema de detección."""
        if self.model is None:
            print("⚠️ No hay modelo cargado para iniciar detección")
            return False
        
        self.detecting = True
        self.primera_guardada = {1: False, 2: False}
        print("🤖 Detección iniciada")
        return True
    
    def stop_detection(self):
        """Detiene el sistema de detección."""
        self.detecting = False
        self.primera_guardada = {1: False, 2: False}
        print("🤖 Detección detenida")
    
    def is_detecting(self) -> bool:
        """Verifica si la detección está activa."""
        return self.detecting and self.model is not None
    
    def process_frame(self, frame: np.ndarray, cam_id: int, 
                     draw_annotations: bool = True) -> Tuple[np.ndarray, Dict]:
        """
        Procesa un frame y ejecuta detecciones.
        
        Args:
            frame: Frame BGR a procesar
            cam_id: ID de la cámara (1 o 2)
            draw_annotations: Si dibujar las anotaciones
            
        Returns:
            Tupla (frame_anotado, info_detecciones)
        """
        h, w = frame.shape[:2]
        
        # Calcular ROI
        roi_config = self.config.get_roi_config(cam_id)
        
        # Verificar si hay puntos de ROI definidos (polígono)
        roi_points = getattr(self.config, f"roi_points_cam{cam_id}", [])
        roi_polygon = None
        
        if roi_points and len(roi_points) >= 3:
            try:
                # Polígono arbitrario
                pts = np.array(roi_points, np.int32)
                # Calcular bounding rect para el recorte
                x_min = int(np.min(pts[:, 0]))
                y_min = int(np.min(pts[:, 1]))
                x_max = int(np.max(pts[:, 0]))
                y_max = int(np.max(pts[:, 1]))
                
                # Asegurar límites
                x_min = max(0, x_min)
                y_min = max(0, y_min)
                x_max = min(w, x_max)
                y_max = min(h, y_max)
                
                roi_coords = (x_min, y_min, x_max, y_max)
                roi_polygon = roi_points # Lista de puntos [x,y]
                
            except Exception as e:
                print(f"Error ROI Points: {e}")
                roi_coords = calcular_roi_coords(cam_id, w, h, roi_config['scale'], roi_config['offset_x'])
        else:
            # ROI Rectangular vertical (Legacy)
            roi_coords = calcular_roi_coords(cam_id, w, h, roi_config['scale'], roi_config['offset_x'])
        
        # Información de resultado
        result_info = {
            'num_detections': 0,
            'plc_triggered': False,
            'operator_detected': False,
            'broken_pieces': 0,
            'detections': []
        }
        
        # Dibujar ROI
        if draw_annotations:
            if roi_polygon:
                # Dibujar polígono
                pts = np.array(roi_polygon, np.int32)
                pts = pts.reshape((-1, 1, 2))
                cv2.polylines(frame, [pts], True, (255, 255, 0), 2)
            else:
                # Dibujar rectángulo simple
                cv2.rectangle(frame, (roi_coords[0], roi_coords[1]), 
                             (roi_coords[2], roi_coords[3]), (255, 255, 0), 2)
        
        # Ejecutar detección si está activa
        if self.is_detecting():
            try:
                # Recortar frame al ROI para reducir falsos positivos y acelerar la inferencia
                x1_roi, y1_roi, x2_roi, y2_roi = roi_coords
                roi_frame = frame[y1_roi:y2_roi, x1_roi:x2_roi].copy()
                results = self.model(
                    roi_frame,
                    verbose=False,
                    conf=getattr(self.config, 'min_confidence', 0.5)
                )
                if results and len(results) > 0:
                    result_info = self._process_detections(
                        frame, results[0], cam_id, roi_coords, draw_annotations, roi_polygon=roi_polygon
                    )
                    
                    # Guardar imagen limpia SOLO para clases específicas (excepto pieza y operador)
                    if result_info.get('detections'):
                        # Filtrar detecciones para grabación (excluir pieza y operador)
                        detections_to_save = [
                            d for d in result_info['detections'] 
                            if d.get('label', '').lower() not in ['pieza', 'operador']
                        ]
                        
                        if detections_to_save:
                            # Hacer una copia del frame limpio (sin anotaciones) para guardar
                            clean_frame = frame.copy()
                            
                            # Crear info de detecciones para guardar
                            save_info = result_info.copy()
                            save_info['detections'] = detections_to_save
                            
                            # Guardar primera detección (imagen limpia) - solo clases específicas
                            self._save_first_detection(clean_frame, cam_id, detections_to_save)
                            
                            # Guardar detección con timestamp (imagen limpia) - solo clases específicas
                            self._save_detection_image(clean_frame, cam_id, save_info)

                    # --- Lógica de desplazamiento de piezas para detectar movimiento de línea ---
                    piezas_roi = [
                        d for d in result_info.get('detections', [])
                        if d.get('label', '').lower() == 'Pieza' and d.get('inside_roi', False)
                    ]
                    # Guardar historial de piezas (solo centro)
                    if piezas_roi:
                        centros_actuales = [d['center'] for d in piezas_roi]
                        self.detection_history[cam_id].append(
                            {'centros': centros_actuales, 'timestamp': datetime.now()}
                        )
                        # Mantener historial acotado
                        if len(self.detection_history[cam_id]) > self.max_history_size:
                            self.detection_history[cam_id] = self.detection_history[cam_id][-self.max_history_size:]
                        # Comparar con frame anterior para detectar movimiento
                        if len(self.detection_history[cam_id]) >= 2:
                            prev = self.detection_history[cam_id][-2]['centros']
                            curr = self.detection_history[cam_id][-1]['centros']
                            movimiento = False
                            for c1 in prev:
                                for c2 in curr:
                                    dist = ((c2[0]-c1[0])**2 + (c2[1]-c1[1])**2)**0.5
                                    if dist > self.movimiento_umbral_px:
                                        movimiento = True
                                        break
                                if movimiento:
                                    break
                            self.linea_en_movimiento[cam_id] = movimiento
                        else:
                            self.linea_en_movimiento[cam_id] = False
                    else:
                        self.linea_en_movimiento[cam_id] = False
                    result_info['linea_en_movimiento'] = self.linea_en_movimiento[cam_id]
                        
            except Exception as e:
                print(f"❌ Error en detección: {e}")
        
        # Dibujar detecciones DESPUÉS del tracking
        if draw_annotations and result_info.get('detections'):
            for detection in result_info['detections']:
                self._draw_detection(frame, detection, cam_id)
        
        # === VISUALIZACIÓN AVANZADA DE PIEZAS QUEBRADAS ===
        if (draw_annotations and 
            result_info.get('broken_analysis', {}).get('broken_pieces_detected', False)):
            
            broken_analysis = result_info['broken_analysis']
            
            # Extraer fragmentos de las detecciones para visualización
            piece_detections = [
                d for d in result_info.get('detections', [])
                if d.get('label', '').lower() == 'pieza' and d.get('inside_roi', False)
            ]
            
            if piece_detections:
                # Convertir a FragmentInfo para visualización
                from broken_piece_analyzer import FragmentInfo
                fragments = []
                
                for i, detection in enumerate(piece_detections):
                    bbox = detection.get('bbox', (0, 0, 0, 0))
                    measurements = detection.get('measurements', {})
                    fragment = FragmentInfo(
                        id=i,
                        bbox=bbox,
                        center=detection.get('center', (0, 0)),
                        width_mm=measurements.get('ancho', 0.0),
                        length_mm=measurements.get('largo', 0.0),
                        confidence=detection.get('confidence', 0.0),
                        timestamp=detection.get('timestamp', datetime.now()),
                        camera_id=cam_id,
                        area_px=(bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                    )
                    fragments.append(fragment)
                
                # Aplicar visualización avanzada
                frame = self.broken_piece_visualizer(frame, broken_analysis, fragments)
        
        return frame, result_info
    
    def _save_first_detection(self, frame: np.ndarray, cam_id: int, detections: List[Dict]):
        """
        Guarda la imagen de la primera detección de la sesión.
        """
        if self.primera_guardada.get(cam_id, False):
            return
            
        try:
            timestamp = now_str()
            filename = f"primera_deteccion_c{cam_id}_{timestamp}.jpg"
            filepath = os.path.join(self.save_dir, filename)
            
            # Dibujar recuadros simples
            draw_frame = frame.copy()
            for d in detections:
                 x1, y1, x2, y2 = d['bbox']
                 cv2.rectangle(draw_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                 cv2.putText(draw_frame, d['label'], (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)

            cv2.imwrite(filepath, draw_frame)
            print(f"📸 Primera detección guardada: {filename}")
            self.primera_guardada[cam_id] = True
            
        except Exception as e:
            print(f"❌ Error guardando primera detección: {e}")

    def _save_detection_image(self, frame: np.ndarray, cam_id: int, info: Dict):
        """
        Guarda imagen de detección si está configurado para hacerlo.
        """
        if not getattr(self.config, 'save_detection_images', False):
            return

        # Limitar frecuencia de guardado (opcional, por ahora guardamos si hay detecciones relevantes)
        try:
            timestamp = now_str()
            # Usar la clase más relevante para el nombre del archivo
            main_label = "unknown"
            if info.get('detections'):
                 main_label = info['detections'][0]['label']
            
            filename = f"det_c{cam_id}_{main_label}_{timestamp}.jpg"
            filepath = os.path.join(self.save_dir, filename)
            
            # Dibujar recuadros
            draw_frame = frame.copy()
            for d in info.get('detections', []):
                 x1, y1, x2, y2 = d['bbox']
                 cv2.rectangle(draw_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                 
            cv2.imwrite(filepath, draw_frame)
            
        except Exception as e:
            print(f"❌ Error guardando imagen de detección: {e}") 
    
    def process_frame_optimized(self, frame: np.ndarray, cam_id: int) -> Tuple[None, Dict]:
        """
        Procesa un frame OPTIMIZADO para latencia baja - SIN crear frame de visualización.
        
        Args:
            frame: Frame BGR a procesar
            cam_id: ID de la cámara (1 o 2)
            
        Returns:
            Tupla (None, info_detecciones)
        """
        if not self.detecting or self.model is None:
            return None, {
                'detections': 0,
                'plc_triggered': False,
                'operator_detected': False,
                'broken_pieces': 0,
                'detection_list': []
            }
        
        h, w = frame.shape[:2]
        
        # Calcular ROI (más rápido sin visualización)
        roi_config = self.config.get_roi_config(cam_id)
        roi_coords = calcular_roi_coords(cam_id, w, h, roi_config['scale'], roi_config['offset_x'])
        
        # Información de resultado optimizada
        result_info = {
            'detections': 0,
            'plc_triggered': False,
            'operator_detected': False,
            'broken_pieces': 0,
            'detection_list': []
        }
        
        try:
            # Ejecutar detección YOLO solo sobre el ROI para minimizar latencia
            x1_roi, y1_roi, x2_roi, y2_roi = roi_coords
            roi_frame = frame[y1_roi:y2_roi, x1_roi:x2_roi].copy()
            result = self.model(
                roi_frame,
                verbose=False,
                conf=getattr(self.config, 'min_confidence', 0.5)
            )[0]
            
            if result.boxes is None:
                return None, result_info
            
            # Procesar detecciones SOLO para lógica, sin dibujos
            names = self.model.names
            
            for box in result.boxes:
                # Extraer información básica (coordenadas relativas al ROI -> ajustar al frame completo)
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                x1 += x1_roi
                x2 += x1_roi
                y1 += y1_roi
                y2 += y1_roi
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                
                # Obtener nombre de clase y aplicar umbral específico
                label = names.get(cls, str(cls)) if isinstance(names, dict) else names[cls]
                min_conf = self._get_min_conf_for_label(label)
                if conf < min_conf:
                    continue
                
                # Calcular centro (más rápido)
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                
                # Verificar ROI (operador en todo el frame)
                if label.lower() == "operador":
                    inside_roi = True
                    result_info['operator_detected'] = True
                else:
                    inside_roi = punto_en_roi(cx, cy, roi_coords)
                
                # Solo contar detecciones dentro del ROI
                if not inside_roi and label.lower() != "operador":
                    continue
                
                result_info['detections'] += 1
                
                # Agregar a la lista de detecciones
                detection_data = {
                    'label': label,
                    'confidence': conf,
                    'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                    'cx': cx, 'cy': cy,
                    'inside_roi': inside_roi
                }
                result_info['detection_list'].append(detection_data)
                
                # Detección rápida de piezas quebradas (solo cámara 1)
                if cam_id == 1 and label.lower() != "operador":
                    # Análisis básico sin visualización
                    width_px, height_px = x2 - x1, y2 - y1
                    aspect_ratio = width_px / max(height_px, 1)
                    
                    # Criterios básicos para pieza quebrada
                    if (aspect_ratio > 3.0 or aspect_ratio < 0.3 or 
                        width_px < 20 or height_px < 20):
                        result_info['broken_pieces'] += 1
                        detection_data['is_broken'] = True
                    else:
                        detection_data['is_broken'] = False
                
                # Log simplificado para debugging
                if self.config.verbose_mode:
                    print(f"Detección optimizada - Cam{cam_id}: {label} (conf: {conf:.2f})")
            
            # Trigger PLC si hay detecciones válidas
            if result_info['detections'] > 0:
                result_info['plc_triggered'] = True
                
                # Agregar al historial simplificado
                if cam_id not in self.detection_history:
                    self.detection_history[cam_id] = []
                
                # Mantener historial limitado (últimas 100 detecciones)
                if len(self.detection_history[cam_id]) > 100:
                    self.detection_history[cam_id] = self.detection_history[cam_id][-50:]
                
                # Agregar detecciones al historial
                for detection in result_info['detection_list']:
                    self.detection_history[cam_id].append({
                        'timestamp': time.time(),
                        'label': detection['label'],
                        'confidence': detection['confidence'],
                        'cam_id': cam_id
                    })
        
        except Exception as e:
            print(f"❌ Error en proceso optimizado: {e}")
        
        return None, result_info
    
    def _process_detections(self, frame: np.ndarray, result,
                           cam_id: int,
                           roi_coords: Tuple[int, int, int, int],
                           draw_annotations: bool,
                           roi_polygon: list = None) -> Dict:
        """Procesa las detecciones de YOLO."""
        info = {
            'num_detections': 0,
            'plc_triggered': False,
            'operator_detected': False,
            'broken_pieces': 0,
            'detections': []
        }
        
        if result.boxes is None:
            return info
        
        names = self.model.names
        detection_list = []
        
        for box in result.boxes:
            # Extraer información de la detección (coordenadas relativas al ROI -> ajustar al frame completo)
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            # Ajustar al frame completo usando las coordenadas del ROI
            x_offset, y_offset, _, _ = roi_coords
            x1 += x_offset
            x2 += x_offset
            y1 += y_offset
            y2 += y_offset
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            
            # Obtener nombre de clase y aplicar umbral específico
            label = names.get(cls, str(cls)) if isinstance(names, dict) else names[cls]
            min_conf = self._get_min_conf_for_label(label)
            if conf < min_conf:
                continue
            
            # Calcular centro y dimensiones
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            width_px, height_px = x2 - x1, y2 - y1
            
            # Verificar si está en ROI (operador se detecta en todo el frame)
            if label.lower() == "operador":
                inside_roi = True
                info['operator_detected'] = True
            else:
                inside_roi = punto_en_roi(cx, cy, roi_polygon if roi_polygon else roi_coords)
            
            # Solo procesar detecciones dentro del ROI (excepto operador)
            if not inside_roi and label.lower() != "operador":
                continue
            
            info['num_detections'] += 1
            
            # Procesar mediciones solo en cámara 1
            if cam_id == 1:
                measurements = self._process_measurements(
                    label, width_px, height_px, cam_id, inside_roi
                )
                
                # Detectar piezas quebradas solo en cámara 1
                is_broken = self._check_broken_piece(label, measurements, inside_roi)
                if is_broken:
                    info['broken_pieces'] += 1
            else:
                # Cámara 2: Sin mediciones
                measurements = {}
                is_broken = False
            
            # Crear información de detección
            detection_data = {
                'label': label,
                'confidence': conf,
                'bbox': (x1, y1, x2, y2),
                'center': (cx, cy),
                'inside_roi': inside_roi,
                'measurements': measurements,
                'is_broken': is_broken,
                'timestamp': datetime.now()
            }
            
            detection_list.append(detection_data)
            info['detections'].append(detection_data)
            
            # NO dibujar aquí - se dibuja después del tracking
            
        # ========================================
        # DETECCIÓN DIRECTA + TRACKING PARALELO
        # ========================================
        # 1. Procesar detecciones normalmente
        # 2. Aplicar tracking simple como post-procesamiento
        
        # Procesar detecciones directamente (sin tracking)
        if detection_list:
            info['detections'] = detection_list
            info['num_detections'] = len(detection_list)
            
            # Procesar cada detección para análisis adicional
            for detection in detection_list:
                # Verificar si está en ROI para PLC y alertas
                label = detection.get('label', '')
                bbox = detection.get('bbox')
                
                if bbox:
                    x1, y1, x2, y2 = bbox
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    if label.lower() == "operador":
                        inside_roi = True
                        info['operator_detected'] = True
                    else:
                        inside_roi = punto_en_roi(cx, cy, roi_coords)
                    detection['inside_roi'] = inside_roi
                    detection['track_id'] = -1  # Sin tracking por defecto
                    # Solo procesar para PLC si está dentro del ROI y es cámara 1
                    if inside_roi and cam_id == 1 and self._should_trigger_plc(label):
                        self._trigger_plc(label, cam_id)
                        info['plc_triggered'] = True
                    # Activar PLC solo si el modelo detecta explícitamente la clase 'quebrada'
                    if label.lower() == "quebrada" and inside_roi and cam_id == 1:
                        detection['is_broken'] = True
                        info['broken_pieces'] += 1
                        if self._should_trigger_plc("quebrada"):
                            self._trigger_plc("quebrada", cam_id)
                            info['plc_triggered_broken'] = True
            
            # === SISTEMA SIMPLIFICADO: SIN TRACKING ===
            # Las detecciones ya están procesadas, no necesitamos tracking
            
            # === ANÁLISIS AVANZADO DE PIEZAS QUEBRADAS ===
            # Solo en cámara 1
            if self.config.detectar_piezas_quebradas and cam_id == 1:
                broken_analysis = self.broken_piece_analyzer.analyze_detections(
                    info['detections'], cam_id
                )
                
                if broken_analysis.get('broken_pieces_detected', False):
                    print(f"🔧 ANÁLISIS AVANZADO: Pieza quebrada detectada en Cam{cam_id}")
                    print(f"   Método: {broken_analysis.get('analysis_method', 'unknown')}")
                    print(f"   Confianza: {broken_analysis.get('confidence_score', 0.0):.2f}")
                    # Actualizar contador con análisis avanzado
                    info['broken_pieces'] = broken_analysis.get('fragment_count', info['broken_pieces'])
                    info['broken_analysis'] = broken_analysis
                    # Activar PLC para pieza quebrada si está configurado
                    if (self.config.alertar_pieza_quebrada and 
                        self.plc_service and 
                        self.config.plc_enabled):
                        try:
                            self.plc_service.pulse(
                                "register",
                                self.config.plc_reg_addr_pieza_quebrada,
                                self.config.plc_pulse_ms,
                                self.config.plc_reg_pulse_value,
                                cam_id,
                                class_name="pieza_quebrada"
                            )
                            print(
                                f"🔧 PLC activado para pieza quebrada "
                                f"(registro {self.config.plc_reg_addr_pieza_quebrada})"
                            )
                        except Exception as e:
                            print(f"❌ Error activando PLC para pieza quebrada: {e}")
        
        # === CONTEO DIRECTO Y SIMPLIFICADO ===
        # SOLO contar detecciones de cámara 1 (excluir operador)
        if cam_id == 1:
            # Obtener TODAS las detecciones válidas para conteo (EXCEPTO operador)
            countable_objects = [
                detection for detection in info['detections']
                if detection.get('inside_roi', False)
                and 'operador' not in detection.get('label', '').lower()
            ]
            
            # print(f"🔍 Cam1: {len(countable_objects)} objetos válidos detectados")
            
            if countable_objects:
                # Sistema simplificado: contar CADA detección válida
                new_detections = []
                
                for obj in countable_objects:
                    # Crear entrada simple sin tracking
                    detection_entry = {
                        'label': obj.get('label', 'Unknown'),
                        'bbox': obj.get('bbox', [0, 0, 0, 0]),
                        'confidence': obj.get('confidence', 0.0),
                        'timestamp': datetime.now(),
                        'camera_id': cam_id,
                        'inside_roi': obj.get('inside_roi', False),
                        'is_broken': obj.get('is_broken', False),
                        'measurements': obj.get('measurements', {}),
                        'detection_method': 'direct_simple'
                    }
                    # Verificar si no es un duplicado muy reciente (mismo frame)
                    is_duplicate = False
                    bbox = obj.get('bbox', [0, 0, 0, 0])
                    cx = (bbox[0] + bbox[2]) // 2
                    cy = (bbox[1] + bbox[3]) // 2
                    # Verificar contra las últimas 3 detecciones para evitar duplicados
                    for recent in self.detection_history.get(cam_id, [])[-3:]:
                        recent_bbox = recent.get('bbox', [0, 0, 0, 0])
                        recent_cx = (recent_bbox[0] + recent_bbox[2]) // 2
                        recent_cy = (recent_bbox[1] + recent_bbox[3]) // 2
                        # Si está muy cerca y es la misma clase, es probable duplicado
                        distance = ((cx - recent_cx)**2 + (cy - recent_cy)**2)**0.5
                        same_label = recent.get('label') == obj.get('label')
                        time_diff = (datetime.now() - recent.get('timestamp', datetime.now())).total_seconds()
                        if distance < 30 and same_label and time_diff < 1.0:
                            is_duplicate = True
                            break
                    if not is_duplicate:
                        new_detections.append(detection_entry)
                
                if new_detections:
                    # Agregar directamente al historial
                    if cam_id not in self.detection_history:
                        self.detection_history[cam_id] = []
                    self.detection_history[cam_id].extend(new_detections)
                    # print(f"📊 CONTADO: {len(new_detections)} objetos NUEVOS en Cam1")
                    # for obj in new_detections:
                    #     label = obj.get('label', 'Unknown')
                    #     print(f"   ✅ {label.title()} agregado al contador")
                    # print(f"📊 TOTAL en historial Cam1: {len(self.detection_history[cam_id])}")
        else:
            pass # print(f"📋 Cam{cam_id}: Detecciones no cuentan para historial (solo Cam1)")
        
        return info
    
    # Método _add_simple_tracking eliminado - Sistema simplificado SIN tracking
    
    def _process_measurements(self, label: str, width_px: float, height_px: float,
                            cam_id: int, inside_roi: bool) -> Optional[Dict]:
        """Procesa las mediciones de una detección."""
        if not self.config.medicion_enabled or not inside_roi:
            return None
        
        # Obtener escala para la cámara
        if cam_id == 1:
            scale = self.config.escala_px_por_mm_cam1
        else:
            scale = self.config.escala_px_por_mm_cam2
        
        # Convertir a unidades reales
        width_real = pixel_to_real_units(width_px, scale, self.config.medicion_units)
        height_real = pixel_to_real_units(height_px, scale, self.config.medicion_units)
        area_real = width_real * height_real
        
        measurements = {
            'width_px': width_px,
            'height_px': height_px,
            'width_real': width_real,
            'height_real': height_real,
            'area_real': area_real,
            'units': self.config.medicion_units
        }
        
        # Para piezas, calcular largo y ancho
        if label.lower() == "pieza":
            # Determinar largo como la dimensión mayor que se acerque a 4000mm
            largo_ref = 4000.0 if self.config.medicion_units == "mm" else \
                       400.0 if self.config.medicion_units == "cm" else 4.0
            
            diff1 = abs(width_real - largo_ref)
            diff2 = abs(height_real - largo_ref)
            
            if diff1 < diff2:
                largo, ancho = width_real, height_real
            else:
                largo, ancho = height_real, width_real
            
            measurements.update({
                'largo': largo,
                'ancho': ancho
            })
            
            # Sugerir calibración si las dimensiones están muy fuera de rango
            max_diff_allowed = largo_ref * 0.5
            if min(diff1, diff2) > max_diff_allowed:
                pixel_length_max = max(width_px, height_px)
                suggest_scale_calibration(pixel_length_max, largo_ref)
        
        # Log de mediciones
        if self.config.log_mediciones:
            log_detection(cam_id, label, 0.0, measurements)  # confidence se pasará después
        
        return measurements
    
    def _check_broken_piece(self, label: str, measurements: Optional[Dict],
                           inside_roi: bool) -> bool:
        """
        Verifica si una pieza está quebrada (método básico de respaldo).
        
        Este método proporciona detección básica basada en dimensiones.
        El análisis avanzado se ejecuta posteriormente en _process_detections.
        """
        if (not self.config.detectar_piezas_quebradas or 
            label.lower() != "pieza" or 
            not measurements or 
            not inside_roi):
            return False
        
        largo = measurements.get('largo', 0)
        
        # Convertir largo mínimo a las unidades actuales
        largo_min = self.config.largo_minimo_pieza_mm
        if self.config.medicion_units == "cm":
            largo_min = largo_min / 10.0
        elif self.config.medicion_units == "m":
            largo_min = largo_min / 1000.0
        
        if largo < largo_min:
            print(
                f"⚠️ PIEZA QUEBRADA (básica): "
                f"{largo:.1f}{self.config.medicion_units} < {largo_min:.1f}{self.config.medicion_units}"
            )
            return True
        
        return False
    
    def _get_min_conf_for_label(self, label: str) -> float:
        """
        Devuelve el umbral mínimo de confianza para una clase dada.
        Permite afinar la sensibilidad por tipo de objeto.
        """
        base = getattr(self.config, 'min_confidence', 0.5)
        name = label.lower()
        # Podemos relajar un poco el umbral para operador para no perderlo
        if name == 'Operador':
            return max(0.2, base * 0.6)
        # Otras clases usan el umbral global
        return base
    
    def _should_trigger_plc(self, label: str) -> bool:
        """Determina si una clase debe activar el PLC."""
        if not self.config.plc_enabled:
            return False
        
        plc_config = self.config.get_plc_config_for_class(label)
        return plc_config['enabled']
    
    def _trigger_plc(self, label: str, cam_id: int):
        """Activa el PLC para una detección."""
        if not self.plc_service:
            return
        
        plc_config = self.config.get_plc_config_for_class(label)
        if not plc_config['enabled'] or plc_config['address'] is None:
            return
        
        success = self.plc_service.pulse(
            "register",
            plc_config['address'],
            plc_config['pulse_ms'],
            plc_config['pulse_value'],
            cam_id,
            label
        )
        
        if success:
            print(f"🔌 PLC activado: {label} cam{cam_id} -> addr:{plc_config['address']}")
    
    def _handle_operator_alert(self, operator_detected: bool):
        """Maneja las alertas de operador."""
        if self.alert_callback:
            self.alert_callback(operator_detected)
    
    def _draw_detection(self, frame: np.ndarray, detection: Dict, cam_id: int):
        """Dibuja una detección en el frame - Rectángulo con nombre de clase."""
        label = detection['label']
        x1, y1, x2, y2 = detection['bbox']
        inside_roi = detection['inside_roi']
        confidence = detection.get('confidence', 0.0)
        
        # Obtener color basado en la clase
        color = get_detection_color(label, inside_roi, False)
        
        # Dibujar rectángulo de detección
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # Preparar texto con clase y confianza
        class_text = f"{label.title()}"
        confidence_text = f"{confidence:.2f}"
        
        # Fondo para el texto (mejor legibilidad)
        text_size = cv2.getTextSize(class_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        conf_size = cv2.getTextSize(confidence_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        
        # Calcular posición del texto
        text_x = x1
        text_y = max(15, y1 - 5)
        
        # Dibujar fondo para el texto de clase
        cv2.rectangle(
            frame,
            (text_x, text_y - text_size[1] - 5),
            (text_x + max(text_size[0], conf_size[0]) + 10, text_y + 5),
            color,
            -1
        )
        
        # Dibujar texto de clase en blanco
        cv2.putText(
            frame,
            class_text,
            (text_x + 5, text_y - 3),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )
        
        # Dibujar confianza debajo (solo si está en ROI)
        if inside_roi:
            cv2.putText(
                frame,
                confidence_text,
                (text_x + 5, text_y + conf_size[1] + 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
        
        # Mostrar indicador de ROI
        if not inside_roi:
            # Dibujar rectángulo punteado para objetos fuera del ROI
            cv2.rectangle(frame, (x1, y1), (x2, y2), (128, 128, 128), 1)
            cv2.putText(
                frame,
                "FUERA ROI",
                (x1, y2 + 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (128, 128, 128),
                1
            )
    
    def _draw_dashed_rectangle(self, img: np.ndarray, pt1: Tuple[int, int], 
                              pt2: Tuple[int, int], color: Tuple[int, int, int], 
                              thickness: int = 2, dash_length: int = 10):
        """Dibuja un rectángulo con líneas segmentadas."""
        x1, y1 = pt1
        x2, y2 = pt2
        
        # Líneas del rectángulo
        lines = [
            ((x1, y1), (x2, y1)),  # superior
            ((x2, y1), (x2, y2)),  # derecha
            ((x2, y2), (x1, y2)),  # inferior
            ((x1, y2), (x1, y1))   # izquierda
        ]
        
        for line in lines:
            pt_start, pt_end = line
            length = int(((pt_end[0] - pt_start[0]) ** 2 + (pt_end[1] - pt_start[1]) ** 2) ** 0.5)
            for i in range(0, length, dash_length * 2):
                start = (
                    int(pt_start[0] + (pt_end[0] - pt_start[0]) * (i / length)),
                    int(pt_start[1] + (pt_end[1] - pt_start[1]) * (i / length))
                )
                end = (
                    int(pt_start[0] + (pt_end[0] - pt_start[0]) * ((i + dash_length) / length)),
                    int(pt_start[1] + (pt_end[1] - pt_start[1]) * ((i + dash_length) / length))
                )
                cv2.line(img, start, end, color, thickness)
