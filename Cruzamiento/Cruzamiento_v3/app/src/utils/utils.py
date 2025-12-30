"""
Utilidades y constantes del sistema de detección de cruzamiento.

Este módulo contiene funciones de utilidad, constantes del sistema,
y funciones auxiliares que son utilizadas en múltiples módulos.
"""

import os
import sys
import ctypes
import ctypes
from datetime import datetime
import cv2
import numpy as np


# ==================== CONSTANTES DEL SISTEMA ====================

# Identificador único de la aplicación para Windows
MYAPPID = 'ct1.cruzamiento.gui.2025'

# Constantes de Windows para mantener pantalla encendida
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

# Configuración de video
DEFAULT_TARGET_FPS = 30.0
DEFAULT_VIDEO_WIDTH = 320
DEFAULT_VIDEO_HEIGHT = 180

# Colores para detecciones (BGR)
COLORS = {
    'operador': (0, 0, 255),      # Rojo
    'cruzamiento': (0, 0, 255),   # Rojo
    'cruzymont': (0, 165, 255),   # Naranja
    'montada': (0, 255, 255),     # Amarillo
    'pieza': (0, 255, 0),         # Verde
    'pieza_quebrada': (0, 0, 128), # Rojo oscuro
    'default': (255, 0, 255),     # Magenta
    'roi': (255, 255, 0),         # Amarillo
    'inactive': (100, 100, 100)   # Gris
}


# ==================== UTILIDADES DE SISTEMA ====================

def setup_windows_app_id():
    """Configura el ID de aplicación para Windows."""
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(MYAPPID)
    except Exception as e:
        print(f"⚠️ No se pudo configurar el ID de aplicación Windows: {e}")


def mantener_pantalla_encendida():
    """Evita que la pantalla se apague durante el funcionamiento."""
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        )
    except Exception as e:
        print(f"⚠️ No se pudo mantener la pantalla encendida: {e}")


def permitir_suspension_normal():
    """Permite que el sistema entre en suspensión normalmente."""
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    except Exception as e:
        print(f"⚠️ No se pudo restaurar el comportamiento de suspensión: {e}")


# ==================== UTILIDADES DE ARCHIVOS ====================

def ruta_relativa(ruta_archivo: str) -> str:
    """
    Obtiene la ruta relativa de un archivo considerando si la app está empaquetada.
    
    Args:
        ruta_archivo: Ruta relativa del archivo
        
    Returns:
        Ruta absoluta del archivo
    """
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, ruta_archivo)


def crear_directorios_trabajo():
    """
    Crea los directorios de trabajo necesarios para la aplicación.
    
    Returns:
        Dict con las rutas de los directorios creados
    """
    base_dir = os.getcwd()
    directorios = {
        'grabaciones': os.path.join(base_dir, "grabaciones"),
        'detecciones': os.path.join(base_dir, "detecciones"),
        'logs': os.path.join(base_dir, "logs")
    }
    
    for nombre, ruta in directorios.items():
        try:
            os.makedirs(ruta, exist_ok=True)
            print(f"📁 Directorio {nombre}: {ruta}")
        except Exception as e:
            print(f"❌ Error creando directorio {nombre}: {e}")
    
    return directorios


# ==================== UTILIDADES DE TIEMPO ====================

def now_str() -> str:
    """
    Obtiene un timestamp formateado para nombres de archivo.
    
    Returns:
        String con formato YYYYMMDD_HHMMSS
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def timestamp_log() -> str:
    """
    Obtiene un timestamp formateado para logs.
    
    Returns:
        String con formato YYYY-MM-DD HH:MM:SS
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ==================== UTILIDADES DE VALIDACIÓN ====================

def validar_ip(ip: str) -> bool:
    """
    Valida si una string es una dirección IP válida.
    
    Args:
        ip: String a validar
        
    Returns:
        True si es una IP válida, False en caso contrario
    """
    try:
        partes = ip.split('.')
        if len(partes) != 4:
            return False
        for parte in partes:
            num = int(parte)
            if not 0 <= num <= 255:
                return False
        return True
    except ValueError:
        return False


def validar_puerto(puerto: int) -> bool:
    """
    Valida si un número es un puerto válido.
    
    Args:
        puerto: Número de puerto a validar
        
    Returns:
        True si es un puerto válido, False en caso contrario
    """
    return 1 <= puerto <= 65535


def validar_archivo_video(ruta: str) -> bool:
    """
    Valida si un archivo es un video válido.
    
    Args:
        ruta: Ruta del archivo a validar
        
    Returns:
        True si es un archivo de video válido, False en caso contrario
    """
    if not os.path.isfile(ruta):
        return False
    
    extensiones_validas = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.m4v'}
    _, ext = os.path.splitext(ruta.lower())
    return ext in extensiones_validas


def validar_modelo_yolo(ruta: str) -> bool:
    """
    Valida si un archivo es un modelo YOLO válido.
    
    Args:
        ruta: Ruta del archivo a validar
        
    Returns:
        True si es un modelo YOLO válido, False en caso contrario
    """
    if not os.path.isfile(ruta):
        return False
    
    extensiones_validas = {'.pt', '.pth'}
    _, ext = os.path.splitext(ruta.lower())
    return ext in extensiones_validas


# ==================== UTILIDADES DE MEDICIÓN ====================

def pixel_to_real_units(pixels: float, escala_px_por_mm: float, units: str = "mm") -> float:
    """
    Convierte píxeles a unidades reales.
    
    Args:
        pixels: Valor en píxeles
        escala_px_por_mm: Factor de escala (píxeles por mm)
        units: Unidades de salida ("mm", "cm", "m")
        
    Returns:
        Valor convertido en las unidades especificadas
    """
    if escala_px_por_mm <= 0:
        return pixels  # Fallback si no hay escala configurada
    
    mm = pixels / escala_px_por_mm
    
    if units == "cm":
        return mm / 10.0
    elif units == "m":
        return mm / 1000.0
    else:  # mm por defecto
        return mm


def format_measurement(value: float, units: str = "mm") -> str:
    """
    Formatea una medida con las unidades especificadas.
    
    Args:
        value: Valor numérico
        units: Unidades ("mm", "cm", "m")
        
    Returns:
        String formateado con el valor y unidades
    """
    if value < 1.0:
        return f"{value:.2f}{units}"
    else:
        return f"{value:.1f}{units}"


def suggest_scale_calibration(pixel_length: float, reference_length_mm: float = 4000.0) -> float:
    """
    Sugiere una escala de calibración basada en un largo de referencia.
    
    Args:
        pixel_length: Largo en píxeles de un objeto de referencia
        reference_length_mm: Largo real del objeto de referencia en mm
        
    Returns:
        Escala sugerida en píxeles por mm
    """
    if pixel_length <= 0 or reference_length_mm <= 0:
        return 1.0
    
    escala_sugerida = pixel_length / reference_length_mm
    
    # print(f"📏 Calibración sugerida:")
    # print(f"   Objeto detectado: {pixel_length:.1f} px")
    # print(f"   Largo referencial: {reference_length_mm} mm")
    # print(f"   Escala sugerida: {escala_sugerida:.4f} px/mm")
    
    return escala_sugerida


# ==================== UTILIDADES DE ROI ====================

def calcular_roi_coords(cam_id: int, w: int, h: int, scale: float, offset_x: float):
    """
    Calcula las coordenadas del ROI para una cámara.
    
    Args:
        cam_id: ID de la cámara
        w: Ancho de la imagen
        h: Alto de la imagen
        scale: Escala del ROI (0.1 a 0.9)
        offset_x: Desplazamiento horizontal (-0.45 a 0.45)
        
    Returns:
        Tupla (x1, y1, x2, y2) con las coordenadas del ROI
    """
    # Asegurar que los valores estén en rango válido
    s = max(0.10, min(0.90, float(scale)))
    off = max(-0.45, min(0.45, float(offset_x)))

    rw = int(s * w)
    cx = int((w / 2) + off * w)
    x1 = max(0, min(max(0, cx - rw // 2), w - rw))
    x2 = min(w - 1, x1 + rw)
    y1, y2 = 0, h - 1
    
    return x1, y1, x2, y2


def punto_en_roi(x: int, y: int, roi_coords) -> bool:
    """
    Verifica si un punto está dentro del ROI.
    
    Args:
        x: Coordenada X del punto
        y: Coordenada Y del punto
        roi_coords: Tupla (x1, y1, x2, y2) O lista de puntos [[x,y],...]
        
    Returns:
        True si el punto está dentro del ROI, False en caso contrario
    """
    if isinstance(roi_coords, list) and len(roi_coords) >= 3:
        # Polígono arbitrario
        pts = np.array(roi_coords, np.int32)
        pts = pts.reshape((-1, 1, 2))
        # pointPolygonTest devuelve > 0 si está dentro, 0 en borde, < 0 fuera
        return cv2.pointPolygonTest(pts, (float(x), float(y)), False) >= 0
    else:
        # Rectángulo simple
        x1, y1, x2, y2 = roi_coords
        return x1 <= x <= x2 and y1 <= y <= y2


# ==================== UTILIDADES DE COLORES ====================

def get_detection_color(class_name: str, inside_roi: bool = True, is_broken: bool = False):
    """
    Obtiene el color para una detección basado en la clase.
    
    Args:
        class_name: Nombre de la clase detectada
        inside_roi: Si la detección está dentro del ROI
        is_broken: Si es una pieza quebrada
        
    Returns:
        Tupla (B, G, R) con el color BGR
    """
    if is_broken:
        return COLORS['pieza_quebrada']
    
    if not inside_roi:
        return COLORS['inactive']
    
    class_name = class_name.lower()
    
    if class_name == "operador":
        return COLORS['operador']
    elif class_name == "cruzymont":
        return COLORS['cruzymont']
    elif class_name.startswith("cruz"):
        return COLORS['cruzamiento']
    elif class_name.startswith("monta"):
        return COLORS['montada']
    elif class_name == "pieza":
        return COLORS['pieza']
    else:
        return COLORS['default']


# ==================== UTILIDADES DE LOGGING ====================

def log_detection(cam_id: int, class_name: str, confidence: float, 
                  measurements: dict = None, file_path: str = None):
    """
    Registra una detección en el archivo de log.
    
    Args:
        cam_id: ID de la cámara
        class_name: Nombre de la clase detectada
        confidence: Nivel de confianza
        measurements: Dict con mediciones (opcional)
        file_path: Ruta del archivo de log (opcional)
    """
    try:
        if file_path is None:
            log_dir = os.path.join(os.getcwd(), "logs")
            os.makedirs(log_dir, exist_ok=True)
            file_path = os.path.join(log_dir, f"detecciones_{datetime.now().strftime('%Y-%m-%d')}.csv")
        
        # Crear header si el archivo no existe
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                header = "timestamp,camera,class,confidence"
                if measurements:
                    header += ",width,height,area,units"
                f.write(header + "\n")
        
        # Escribir registro
        with open(file_path, 'a', encoding='utf-8') as f:
            line = f"{timestamp_log()},{cam_id},{class_name},{confidence:.3f}"
            if measurements:
                line += f",{measurements.get('width', 0):.2f},{measurements.get('height', 0):.2f},{measurements.get('area', 0):.2f},{measurements.get('units', 'px')}"
            f.write(line + "\n")
            
    except Exception as e:
        print(f"❌ Error escribiendo log de detección: {e}")


# ==================== UTILIDADES DE CONFIGURACIÓN TORCH ====================

def setup_torch_for_yolo():
    """
    Configura PyTorch para cargar modelos YOLO correctamente.
    
    Aplica un monkey patch para forzar weights_only=False en torch.load
    lo cual es necesario para la compatibilidad con modelos YOLO en PyTorch 2.6+
    """
    try:
        import torch
        
        # Solo aplicar el patch si no se ha aplicado antes
        if not hasattr(torch, '_original_load'):
            torch._original_load = torch.load
            
            def safe_load(*args, **kwargs):
                # Forzar weights_only=False para compatibilidad con modelos YOLO
                kwargs['weights_only'] = False
                return torch._original_load(*args, **kwargs)
            
            torch.load = safe_load
            print("✅ PyTorch configurado para cargar modelos YOLO (weights_only=False)")
        else:
            print("✅ PyTorch ya configurado para modelos YOLO")
            
    except ImportError:
        print("⚠️ PyTorch no disponible - configuración omitida")
    except Exception as e:
        print(f"⚠️ Error configurando PyTorch: {e}")


# ==================== UTILIDADES DE BÚSQUEDA DE MODELOS ====================

def find_yolo_models(base_paths=None, model_patterns=None):
    """
    Busca modelos YOLO disponibles en múltiples ubicaciones.
    
    Args:
        base_paths: Lista de rutas base donde buscar (opcional)
        model_patterns: Lista de patrones de nombres de modelo (opcional)
        
    Returns:
        Lista de tuplas (ruta_completa, nombre_descriptivo)
    """
    if base_paths is None:
        # Detectar si estamos en un ejecutable PyInstaller
        if getattr(sys, 'frozen', False):
            # Rutas para ejecutable PyInstaller
            executable_dir = os.path.dirname(sys.executable)
            base_paths = [
                'models/',  # Carpeta models en el ejecutable
                os.path.join(executable_dir, 'models/'),  # Junto al ejecutable
                os.path.join(executable_dir, '_internal', 'models/'),  # Dentro del ejecutable
                os.path.join(sys._MEIPASS, 'models/') if hasattr(sys, '_MEIPASS') else '',  # Temp PyInstaller
            ]
        else:
            # Rutas para desarrollo normal
            base_paths = [
                '',  # Directorio actual
                'models/',  # Carpeta models relativa
                os.path.join(os.path.dirname(__file__), 'models/'),  # Carpeta models junto al script
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models/'),  # Ruta absoluta
                'app/models/',  # Desde raíz del proyecto
            ]
    
    if model_patterns is None:
        model_patterns = [
            ('best_Cruzamiento_v3.pt', 'YOLO Custom v3'),
            ('best_CruzamientoY11n.pt', 'YOLO11n Custom'),
            ('best_CruzaminetoY11s.pt', 'YOLO11s Custom'), 
            ('best_CruzamientoY11m.pt', 'YOLO11m Custom'),
            ('best_dect_piezas_seg.pt', 'YOLO Segmentation'),
            ('yolo11n.pt', 'YOLO11n Base'),
            ('yolo11s.pt', 'YOLO11s Base')
        ]
    
    models_found = []
    
    for model_file, model_desc in model_patterns:
        for base_path in base_paths:
            full_path = os.path.join(base_path, model_file) if base_path else model_file
            
            if os.path.exists(full_path) and os.path.isfile(full_path):
                file_size = os.path.getsize(full_path) / (1024 * 1024)  # MB
                desc_with_info = f"{model_desc} ({file_size:.1f}MB)"
                models_found.append((full_path, desc_with_info))
                print(f"📋 Modelo encontrado: {desc_with_info} -> {full_path}")
    
    return models_found


# ==================== UTILIDADES DIVERSAS ====================

def safe_float(value, default=0.0):
    """
    Convierte un valor a float de manera segura.
    
    Args:
        value: Valor a convertir
        default: Valor por defecto si la conversión falla
        
    Returns:
        Valor convertido a float o el valor por defecto
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """
    Convierte un valor a int de manera segura.
    
    Args:
        value: Valor a convertir
        default: Valor por defecto si la conversión falla
        
    Returns:
        Valor convertido a int o el valor por defecto
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def clamp(value, min_val, max_val):
    """
    Limita un valor entre un mínimo y máximo.
    
    Args:
        value: Valor a limitar
        min_val: Valor mínimo
        max_val: Valor máximo
        
    Returns:
        Valor limitado entre min_val y max_val
    """
    return max(min_val, min(max_val, value))