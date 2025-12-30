"""
Configuración del sistema de detección de cruzamiento.

Este módulo contiene la clase CamConfig que maneja toda la configuración
del sistema incluyendo cámaras, modelo IA, ROI, medición y PLC.
"""

import os
import json
from dataclasses import dataclass, asdict
from typing import ClassVar
import sys

# Centralizar el archivo de configuración en la carpeta del proyecto
# Detectar si estamos corriendo compilado (frozen) o como script
if getattr(sys, 'frozen', False):
    # Si es un ejecutable (PyInstaller), el archivo está junto al .exe
    base_dir = os.path.dirname(sys.executable)
else:
    # Si es script, estamos en src/config.py, así que subimos un nivel a app/
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_FILE = os.path.join(base_dir, "config_camera.json")


@dataclass
class CamConfig:
    """
    Configuración completa del sistema de detección.
    
    Incluye configuración para:
    - Múltiples fuentes de video (IP, webcam, archivo)
    - Modelo de IA YOLO
    - Regiones de interés (ROI)
    - Sistema de medición
    - Comunicación PLC Modbus
    - Alertas visuales
    """
    
    # === CONFIGURACIÓN DE CÁMARAS ===
    # Tipos de fuente: "ip", "webcam", "archivo"
    cam1_tipo: str = "ip"
    cam2_tipo: str = "ip"
    cam1_conexion: str = "http"  # "http" o "rtsp"
    cam2_conexion: str = "http"  # "http" o "rtsp"
    
    # Para fuentes IP
    cam_ip: str = "192.168.1.64"
    cam2_ip: str = "192.168.1.65"
    cam_user: str = "admin"
    cam_pass: str = "Vision2025"
    http_port: int = 80
    cam_port: int = 554  # Puerto para RTSP/HTTP
    connection_type: str = "RTSP"  # "RTSP" o "HTTP"
    channel: str = "101"
    
    # Para webcam (índices 0, 1, 2, etc.)
    cam1_webcam_idx: int = 0
    cam2_webcam_idx: int = 1
    
    # Para archivos de video
    cam1_archivo: str = ""
    cam2_archivo: str = ""
    
    # === CONFIGURACIÓN DEL MODELO IA ===
    model_path: str = r"app/models/best_Cruzamiento_v3.pt"
    min_confidence: float = 0.70

    # === UMBRAL DE DETECCIÓN PARA ACTIVAR PLC ===
    umbral_movimiento: int = 5
    
    # === CONFIGURACIÓN ROI ===
    roi_scale: float = 0.40  # Retrocompatibilidad
    roi_posicion: bool = False  # Retrocompatibilidad
    roi_scale_1: float = 0.40
    roi_scale_2: float = 0.40
    roi_offset_x_1: float = 0.0
    roi_offset_x_2: float = 0.0
    roi_points_cam1: list = None  # Lista de puntos [x, y] para polígono arbitrario
    
    # === CONFIGURACIÓN PLC ===
    plc_enabled: bool = False
    plc_ip: str = "192.168.10.50"
    plc_port: int = 502
    plc_unit_id: int = 1
    plc_write_mode: str = "register"
    
    # Direcciones PLC (ordenadas por funcionalidad)
    plc_reg_addr_1: int = 22001          # Cruzamiento cam1
    plc_reg_addr_2: int = 22002          # Cruzamiento cam2 / CruzyMnt
    plc_reg_addr_3: int = 22003          # Montada
    plc_reg_addr_operador: int = 22004   # Operador
    plc_reg_addr_pieza_quebrada: int = 22005  # Pieza quebrada
    plc_reg_addr_alaveo: int = 22006     # Alaveo
    plc_reg_addr_pieza: int = 22007      # Pieza (Nueva detección estándar)
    
    # Configuración de pulsos PLC
    plc_reg_pulse_value: int = 1
    plc_pulse_ms: int = 300
    plc_cooldown_s: float = 1.0
    plc_reenganche_param: int = 10 
    
    # Seguridad Operador
    operator_safety_frames: int = 30 # Frames sin operador necesarios para reenganche
    
    # Clases que activan PLC (retrocompatibilidad)
    plc_trigger_class: str = "Cruzamiento"
    plc_trigger_class_2: str = "CruzyMnt"
    plc_trigger_class_3: str = "Operador"
    
    # === ACTIVACIÓN INDIVIDUAL POR CLASE ===
    # (Ordenadas por dirección PLC para facilidad de mantenimiento)
    plc_enable_cruzamiento: bool = True      # 22001
    plc_enable_cruzymnt: bool = True         # 22002  
    plc_enable_montada: bool = False         # 22003
    plc_enable_operador: bool = True         # 22004
    alertar_pieza_quebrada: bool = True      # 22005
    plc_enable_alaveo: bool = False          # 22006
    plc_enable_pieza: bool = False           # 22007
    
    # === ALERTAS VISUALES ===
    operador_alert_enabled: bool = True
    operador_alert_color: str = "#FF0000"  # Rojo brillante
    operador_alert_blink: bool = True
    
    # === CONFIGURACIÓN DE MEDICIÓN ===
    medicion_enabled: bool = True
    medicion_units: str = "mm"  # "mm", "cm", "m"
    
    # Factor de escala: píxeles por unidad real
    escala_px_por_mm_cam1: float = 1.0  # píxeles por mm para cámara 1
    escala_px_por_mm_cam2: float = 1.0  # píxeles por mm para cámara 2
    
    mostrar_medidas_overlay: bool = True
    log_mediciones: bool = True
    
    # === CONFIGURACIÓN DE PIEZAS QUEBRADAS ===
    detectar_piezas_quebradas: bool = True
    largo_minimo_pieza_mm: float = 50.0  # Largo mínimo en mm para considerar pieza válida
    min_fragmentos_quebrada: int = 2  # Mínimo de fragmentos para considerar quebrada
    
    # === CONFIGURACIÓN DE GRABACIÓN AUTOMÁTICA ===
    auto_recording_enabled: bool = False  # Habilitar grabación automática al detectar
    auto_record_duration_s: float = 10.0  # Duración de grabación en segundos
    save_detection_images: bool = True    # Guardar imágenes de detecciones
    
    # === CONFIGURACIÓN DE TRACKING (ByteTrack - Seguimiento Persistente) ===
    # ByteTrack configurado para seguimiento continuo desde detección hasta salida
    tracking_frame_rate: int = 30         # FPS del video para ByteTrack
    tracking_track_thresh: float = 0.3    # Umbral más bajo para detectar piezas temprano
    tracking_high_thresh: float = 0.5     # Umbral para detecciones de alta confianza (reducido)
    tracking_match_thresh: float = 0.7    # Umbral IoU para matching (más permisivo)
    tracking_track_buffer: int = 60       # Más frames para mantener tracks perdidos temporalmente

    # === CONFIGURACIÓN DE TRACKING SIMPLE EN ROI ===
    # Sistema simple de seguimiento solo para piezas dentro del ROI
    simple_tracking_enabled: bool = True          # Habilitar tracking simple
    simple_tracking_max_distance: float = 200.0   # Distancia máxima en píxeles para matching (aumentado de 100)
    simple_tracking_max_missing: int = 5          # Frames máximos sin detección antes de eliminar
    simple_tracking_roi_only: bool = True         # Solo trackear piezas en ROI
    simple_tracking_show_trajectory: bool = False # Mostrar trayectoria de movimiento
    simple_tracking_continuous: bool = True       # Tracking continuo cross-camera (cámara 1 → cámara 2)
    simple_tracking_transfer_timeout: int = 10    # Frames máximos para esperar transfer entre cámaras

    @classmethod
    def load(cls, path: str = CONFIG_FILE) -> 'CamConfig':
        """
        Carga la configuración desde un archivo JSON.
        
        Args:
            path: Ruta del archivo de configuración
            
        Returns:
            Instancia de CamConfig con la configuración cargada
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Valores por defecto para retrocompatibilidad
            cls._apply_defaults(data)
            
            # Filtrar llaves que no existen en el dataclass para evitar errores
            from dataclasses import fields
            valid_keys = {f.name for f in fields(cls)}
            filtered_data = {k: v for k, v in data.items() if k in valid_keys}
            
            return cls(**filtered_data)
        except Exception as e:
            print(f"⚠️ Error cargando configuración desde {path}: {e}")
            # print("📋 Usando configuración por defecto") # Removed to avoid confusion if we catch it earlier
            # Only return default if it truly failed
            return cls()

    @classmethod
    def _apply_defaults(cls, data: dict) -> None:
        """Aplica valores por defecto para campos faltantes."""
        defaults = {
            # Cámaras
            "cam2_ip": "192.168.1.65",
            "cam1_tipo": "ip",
            "cam2_tipo": "ip",
            "cam1_webcam_idx": 0,
            "cam2_webcam_idx": 1,
            "cam1_archivo": "",
            "cam2_archivo": "",
            
            # ROI
            "roi_scale_1": data.get("roi_scale", 0.40),
            "roi_scale_2": data.get("roi_scale", 0.40),
            "roi_offset_x_1": 0.0,
            "roi_offset_x_1": 0.0,
            "roi_offset_x_2": 0.0,
            "roi_points_cam1": [],
            
            # PLC - Direcciones ordenadas
            "plc_reg_addr_1": 22001,    # Cruzamiento
            "plc_reg_addr_2": 22002,    # CruzyMnt
            "plc_reg_addr_3": 22003,    # Montada
            "plc_reg_addr_operador": 22004,    # Operador
            "plc_reg_addr_pieza_quebrada": 22005,  # Pieza Quebrada
            "plc_reg_addr_alaveo": 22006,      # Alaveo
            
            # PLC - Activación por clase (ordenadas por dirección PLC)
            "plc_enable_cruzamiento": True,     # 22001
            "plc_enable_cruzymnt": True,        # 22002
            "plc_enable_montada": False,        # 22003
            "plc_enable_operador": True,        # 22004
            "alertar_pieza_quebrada": True,     # 22005
            "plc_enable_alaveo": False,         # 22006
            
            # Alertas
            "operador_alert_enabled": True,
            "operador_alert_color": "#FF0000",
            "operador_alert_blink": True,
            
            # Medición
            "medicion_enabled": True,
            "medicion_units": "mm",
            "escala_px_por_mm_cam1": 1.0,
            "escala_px_por_mm_cam2": 1.0,
            "mostrar_medidas_overlay": True,
            "log_mediciones": True,
            
            # Piezas quebradas
            "detectar_piezas_quebradas": True,
            "largo_minimo_pieza_mm": 50.0,
            "min_fragmentos_quebrada": 2,

            # Umbral de detección para activar PLC
            "umbral_movimiento": 5,
            
            # Grabación automática
            "auto_recording_enabled": False,
            "auto_record_duration_s": 10.0,
            "save_detection_images": True,
            
            # ByteTrack (seguimiento persistente)
            "tracking_frame_rate": 30,
            "tracking_track_thresh": 0.3,
            "tracking_high_thresh": 0.5,
            "tracking_match_thresh": 0.7,
            "tracking_track_buffer": 60,
            
            # Tracking simple en ROI
            "simple_tracking_enabled": True,
            "simple_tracking_max_distance": 200.0,
            "simple_tracking_max_missing": 5,
            "simple_tracking_roi_only": True,
            "simple_tracking_show_trajectory": False,
            "simple_tracking_continuous": True,
            "simple_tracking_transfer_timeout": 10,
        }
        
        for key, default_value in defaults.items():
            data.setdefault(key, default_value)

    def save(self, path: str = CONFIG_FILE) -> None:
        """
        Guarda la configuración en un archivo JSON.
        
        Args:
            path: Ruta donde guardar el archivo de configuración
        """
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, ensure_ascii=False, indent=2)
            print(f"✅ Configuración guardada en: {path}")
        except Exception as e:
            print(f"❌ Error guardando configuración en {path}: {e}")

    def get_camera_source(self, cam_id: int) -> tuple:
        """
        Obtiene la configuración de fuente para una cámara específica.
        
        Args:
            cam_id: ID de la cámara (1 o 2)
            
        Returns:
            Tupla (tipo, configuración) donde:
            - tipo: "ip", "webcam", "archivo"
            - configuración: dict con los parámetros específicos
        """
        if cam_id == 1:
            tipo = self.cam1_tipo
            if tipo == "ip":
                config = {
                    "ip": self.cam_ip,
                    "user": self.cam_user,
                    "pass": self.cam_pass,
                    "port": self.http_port,
                    "rtsp_port": self.cam_port,
                    "channel": self.channel
                }
            elif tipo == "webcam":
                config = {"index": self.cam1_webcam_idx}
            else:  # archivo
                config = {"path": self.cam1_archivo}
        else:  # cam_id == 2
            tipo = self.cam2_tipo
            if tipo == "ip":
                config = {
                    "ip": self.cam2_ip,
                    "user": self.cam_user,
                    "pass": self.cam_pass,
                    "port": self.http_port,
                    "rtsp_port": self.cam_port,
                    "channel": self.channel
                }
            elif tipo == "webcam":
                config = {"index": self.cam2_webcam_idx}
            else:  # archivo
                config = {"path": self.cam2_archivo}
                
        return tipo, config

    def get_roi_config(self, cam_id: int) -> dict:
        """
        Obtiene la configuración ROI para una cámara específica.
        
        Args:
            cam_id: ID de la cámara (1 o 2)
            
        Returns:
            Dict con scale y offset_x para la cámara
        """
        if cam_id == 1:
            return {
                "scale": self.roi_scale_1,
                "offset_x": self.roi_offset_x_1
            }
        else:
            return {
                "scale": self.roi_scale_2,
                "offset_x": self.roi_offset_x_2
            }
    
    def get_camera_config(self, cam_id: int) -> dict:
        """
        Obtiene la configuración completa para una cámara específica.
        
        Args:
            cam_id: ID de la cámara (1 o 2)
            
        Returns:
            Dict con toda la configuración de la cámara
        """
        tipo, config = self.get_camera_source(cam_id)
        
        # Agregar información adicional según el tipo
        if tipo == "ip":
            if cam_id == 1:
                config.update({
                    'tipo': 'ip',
                    'ip': self.cam_ip,
                    'puerto': self.http_port,
                    'usuario': self.cam_user,
                    'password': self.cam_pass,
                    'channel': self.channel
                })
            else:
                config.update({
                    'tipo': 'ip', 
                    'ip': self.cam2_ip,
                    'puerto': self.http_port,
                    'usuario': self.cam_user,
                    'password': self.cam_pass,
                    'channel': self.channel
                })
        elif tipo == "webcam":
            config.update({
                'tipo': 'webcam',
                'index': config.get('index', 0)
            })
        elif tipo == "archivo":
            config.update({
                'tipo': 'archivo'
            })
        
        return config

    def get_plc_config_for_class(self, class_name: str) -> dict:
        """
        Obtiene la configuración PLC para una clase específica.
        
        Args:
            class_name: Nombre de la clase de detección
            
        Returns:
            Dict con enabled, address y otros parámetros
        """
        class_name = class_name.lower().strip()
        
        config = {
            "enabled": False,
            "address": None,
            "pulse_ms": self.plc_pulse_ms,
            "pulse_value": self.plc_reg_pulse_value,
            "cooldown_s": self.plc_cooldown_s
        }
        
        if class_name == "operador":
            config.update({
                "enabled": self.plc_enable_operador,
                "address": self.plc_reg_addr_operador
            })
        elif class_name == "cruzymont":
            config.update({
                "enabled": self.plc_enable_cruzymnt,
                "address": self.plc_reg_addr_2
            })
        elif class_name.startswith("cruz"):  # cruzamiento, cruzamiento_xxx, etc.
            config.update({
                "enabled": self.plc_enable_cruzamiento,
                "address": self.plc_reg_addr_1
            })
        elif class_name.startswith("monta"):  # montacargas, montada, etc.
            config.update({
                "enabled": self.plc_enable_montada,
                "address": self.plc_reg_addr_3
            })
        elif class_name == "alaveo":
            config.update({
                "enabled": self.plc_enable_alaveo,
                "address": self.plc_reg_addr_alaveo
            })
        elif class_name in ["quebrada", "pieza_quebrada", "broken"]:
            config.update({
                "enabled": self.alertar_pieza_quebrada,
                "address": self.plc_reg_addr_pieza_quebrada
            })
        elif class_name == "pieza":
            config.update({
                "enabled": self.plc_enable_pieza,
                "address": self.plc_reg_addr_pieza
            })
            
        return config

    def validate(self) -> list:
        """
        Valida la configuración y retorna una lista de errores encontrados.
        
        Returns:
            Lista de strings con errores encontrados (vacía si no hay errores)
        """
        errors = []
        
        # Validar IPs
        if self.cam1_tipo == "ip" and not self.cam_ip:
            errors.append("IP de cámara 1 es requerida")
        if self.cam2_tipo == "ip" and not self.cam2_ip:
            errors.append("IP de cámara 2 es requerida")
            
        # Validar archivos
        if self.cam1_tipo == "archivo" and not os.path.isfile(self.cam1_archivo):
            errors.append(f"Archivo de cámara 1 no existe: {self.cam1_archivo}")
        if self.cam2_tipo == "archivo" and not os.path.isfile(self.cam2_archivo):
            errors.append(f"Archivo de cámara 2 no existe: {self.cam2_archivo}")
            
        # Validar modelo
        if not os.path.isfile(self.model_path):
            errors.append(f"Archivo de modelo no existe: {self.model_path}")
            
        # Validar rangos
        if not 0.01 <= self.min_confidence <= 1.0:
            errors.append("Confianza mínima debe estar entre 0.01 y 1.0")
        if not 0.10 <= self.roi_scale_1 <= 0.90:
            errors.append("Escala ROI cámara 1 debe estar entre 0.10 y 0.90")
        if not 0.10 <= self.roi_scale_2 <= 0.90:
            errors.append("Escala ROI cámara 2 debe estar entre 0.10 y 0.90")
            
        return errors

    def __str__(self) -> str:
        """Representación string de la configuración."""
        return (
            f"CamConfig("
            f"C1={self.cam1_tipo}:{self.cam_ip if self.cam1_tipo == 'ip' else 'local'}, "
            f"C2={self.cam2_tipo}:{self.cam2_ip if self.cam2_tipo == 'ip' else 'local'}, "
            f"Model={os.path.basename(self.model_path)}, "
            f"PLC={'ON' if self.plc_enabled else 'OFF'})"
        )