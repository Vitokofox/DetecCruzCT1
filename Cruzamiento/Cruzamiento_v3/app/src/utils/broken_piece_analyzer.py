import cv2
from datetime import datetime

class FragmentInfo:
    def __init__(self, id, bbox, center, width_mm, length_mm, confidence, timestamp, camera_id, area_px):
        self.id = id
        self.bbox = bbox  # (x1, y1, x2, y2)
        self.center = center
        self.width_mm = width_mm
        self.length_mm = length_mm
        self.confidence = confidence
        self.timestamp = timestamp if isinstance(timestamp, datetime) else datetime.now()
        self.camera_id = camera_id
        self.area_px = area_px

class BrokenPieceAnalyzer:
    def __init__(self, config):
        self.config = config
        # Aquí podrías cargar parámetros, modelos, etc.


    def analyze(self, detections):
        # Lógica de análisis de piezas quebradas (stub)
        # Retorna un dict con resultados
        return {
            'broken_pieces_detected': False,
            'details': []
        }

    def analyze_detections(self, detections, camera_id):
        # Implementación básica para evitar el error de atributo
        # Puedes mejorar la lógica según el modelo y las clases
        broken_pieces = [d for d in detections if d.get('label', '').lower() == 'quebrada']
        result = {
            'broken_pieces_detected': bool(broken_pieces),
            'fragment_count': len(broken_pieces),
            'details': broken_pieces,
            'analysis_method': 'label_filter',
            'confidence_score': max([d.get('confidence', 0.0) for d in broken_pieces], default=0.0),
            'camera_id': camera_id
        }
        return result

def create_broken_piece_visualizer():
    def visualizer(frame, broken_analysis, fragments):
        # Dibuja los fragmentos sobre el frame
        for frag in fragments:
            x1, y1, x2, y2 = frag.bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, f"ID:{frag.id}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
        if broken_analysis.get('broken_pieces_detected', False):
            cv2.putText(frame, "PIEZAS QUEBRADAS DETECTADAS", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,255), 3)
        return frame
    return visualizer
