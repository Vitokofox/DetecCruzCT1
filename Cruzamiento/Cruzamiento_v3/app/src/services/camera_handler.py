"""
Manejador de cámaras para el sistema de detección.

Este módulo maneja la captura de video desde múltiples fuentes:
- Cámaras IP (HTTP/MJPEG)
- Webcams USB
- Archivos de video

Incluye threading para captura asíncrona y manejo de errores robusto.
"""

import os
import time
import threading
from typing import Optional, Tuple, Dict, Any
import cv2
import numpy as np
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from src.utils.utils import validar_ip, validar_puerto, validar_archivo_video


class CameraHandler:
    """
    Manejador principal de cámaras con soporte para múltiples fuentes.
    """
    
    def __init__(self, config):
        """
        Inicializa el manejador de cámaras.
        
        Args:
            config: Instancia de CamConfig con la configuración
        """
        self.config = config
        
        # Control de threads
        self.reader_running = False
        self.reader_threads: Dict[int, threading.Thread] = {}
        
        # Frames actuales por cámara
        self.last_frame1: Optional[np.ndarray] = None
        self.last_frame2: Optional[np.ndarray] = None
        
        # Locks para acceso thread-safe
        self.last_lock1 = threading.Lock()
        self.last_lock2 = threading.Lock()
        
        # Objetos de captura para webcam y archivos
        self.cap1: Optional[cv2.VideoCapture] = None
        self.cap2: Optional[cv2.VideoCapture] = None
        
        # Callbacks para estado
        self.status_callback = None
        
    def set_status_callback(self, callback):
        """
        Establece callback para actualizaciones de estado.
        
        Args:
            callback: Función que recibe (cam_id, mensaje)
        """
        self.status_callback = callback
        
    def _update_status(self, cam_id: int, message: str):
        """Actualiza el estado de una cámara."""
        if self.status_callback:
            self.status_callback(cam_id, message)
        else:
            print(f"📹 C{cam_id}: {message}")
    
    def start_cameras(self) -> bool:
        """
        Inicia la captura de ambas cámaras.
        
        Returns:
            True si al menos una cámara se inició correctamente
        """
        if self.reader_running:
            self._update_status(0, "Cámaras ya están activas")
            return True
        
        self.reader_running = True
        
        # Iniciar threads para cada cámara
        success1 = self._start_camera_thread(1)
        success2 = self._start_camera_thread(2)
        
        if success1 or success2:
            self._update_status(0, "🔄 Conectando cámaras...")
            return True
        else:
            self.reader_running = False
            self._update_status(0, "❌ No se pudo iniciar ninguna cámara")
            return False
    
    def stop_cameras(self):
        """Detiene la captura de todas las cámaras."""
        self.reader_running = False
        
        # Esperar que terminen los threads
        for cam_id, thread in self.reader_threads.items():
            if thread and thread.is_alive():
                thread.join(timeout=2.0)
                self._update_status(cam_id, "🔴 Thread detenido")
        
        self.reader_threads.clear()
        
        # Limpiar frames
        with self.last_lock1:
            self.last_frame1 = None
        with self.last_lock2:
            self.last_frame2 = None
        
        # Liberar recursos de captura
        if self.cap1:
            self.cap1.release()
            self.cap1 = None
        if self.cap2:
            self.cap2.release()
            self.cap2 = None
            
        self._update_status(0, "🔴 Cámaras detenidas")
    
    def get_frames(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Obtiene los frames actuales de ambas cámaras.
        
        Returns:
            Tupla (frame1, frame2) con copias de los frames actuales
        """
        frame1 = frame2 = None
        
        with self.last_lock1:
            if self.last_frame1 is not None:
                frame1 = self.last_frame1.copy()
                
        with self.last_lock2:
            if self.last_frame2 is not None:
                frame2 = self.last_frame2.copy()
        
        return frame1, frame2
    
    def get_frame(self, cam_id: int) -> Optional[np.ndarray]:
        """
        Obtiene el frame actual de una cámara específica.
        
        Args:
            cam_id: ID de la cámara (1 o 2)
            
        Returns:
            Copia del frame actual o None si no disponible
        """
        if cam_id == 1:
            with self.last_lock1:
                return self.last_frame1.copy() if self.last_frame1 is not None else None
        elif cam_id == 2:
            with self.last_lock2:
                return self.last_frame2.copy() if self.last_frame2 is not None else None
        else:
            return None
    
    def is_running(self) -> bool:
        """
        Verifica si el sistema de cámaras está activo.
        
        Returns:
            True si está ejecutándose, False en caso contrario
        """
        return self.reader_running
    
    def get_camera_info(self, cam_id: int) -> Dict[str, Any]:
        """
        Obtiene información sobre una cámara específica.
        
        Args:
            cam_id: ID de la cámara (1 o 2)
            
        Returns:
            Dict con información de la cámara
        """
        tipo, config = self.config.get_camera_source(cam_id)
        
        info = {
            'id': cam_id,
            'type': tipo,
            'config': config,
            'active': cam_id in self.reader_threads and 
                     self.reader_threads[cam_id].is_alive() if self.reader_threads else False,
            'has_frame': self.get_frame(cam_id) is not None
        }
        
        return info
    
    def _start_camera_thread(self, cam_id: int) -> bool:
        """
        Inicia el thread de captura para una cámara específica.
        
        Args:
            cam_id: ID de la cámara (1 o 2)
            
        Returns:
            True si el thread se inició correctamente
        """
        tipo, config = self.config.get_camera_source(cam_id)
        # Obtener tipo de conexión desde la configuración
        conexion = getattr(self.config, f"cam{cam_id}_conexion", "http")

        print(f"[DEBUG] Cámara {cam_id}: tipo={tipo}, conexion={conexion}")

        if tipo in ["none", "disabled", ""]:
            return False

        try:
            if tipo == "ip":
                if not self._validate_ip_config(config):
                    return False
                if conexion.lower() == "rtsp":
                    thread = threading.Thread(
                        target=self._reader_loop_rtsp,
                        args=(cam_id, config),
                        daemon=True
                    )
                else:
                    thread = threading.Thread(
                        target=self._reader_loop_http,
                        args=(cam_id, config),
                        daemon=True
                    )
            elif tipo == "webcam":
                if not self._validate_webcam_config(config):
                    return False
                thread = threading.Thread(
                    target=self._reader_loop_webcam, 
                    args=(cam_id, config), 
                    daemon=True
                )
            elif tipo == "archivo":
                if not self._validate_file_config(config):
                    return False
                thread = threading.Thread(
                    target=self._reader_loop_file, 
                    args=(cam_id, config), 
                    daemon=True
                )
            else:
                self._update_status(cam_id, f"❌ Tipo de cámara no soportado: {tipo}")
                return False
            
            self.reader_threads[cam_id] = thread
            thread.start()
            self._update_status(cam_id, f"🚀 Thread {tipo} iniciado")
            return True
            
        except Exception as e:
            self._update_status(cam_id, f"❌ Error iniciando thread: {e}")
            return False
    
    
    def _reader_loop_rtsp(self, cam_id: int, config: dict):
        """Loop de captura para cámaras IP vía RTSP (TCP)."""
        ip = config['ip']
        user = config['user']
        password = config['pass']
        # Priorizar rtsp_port, fallback a 554
        port = config.get('rtsp_port', 554)
        if port == 80: port = 554 # Corrección de seguridad si viene mal configurado
        
        channel = config['channel']
        
        # Construir URL RTSP
        rtsp_url = f"rtsp://{user}:{password}@{ip}:{port}/Streaming/Channels/{channel}"
        
        reconnect_delay = 1.0
        max_delay = 10.0
        fail_count = 0
        max_fails = 5 # Si falla 5 veces seguidas, caer a HTTP
        
        self._update_status(cam_id, f"🔄 Conectando RTSP ({ip}:{port})...")
        print(f"[DEBUG] RTSP URL: rtsp://{user}:***@{ip}:{port}/Streaming/Channels/{channel}")
        
        while self.reader_running:
            try:
                # Si fallamos demasiadas veces, intentar fallback a HTTP
                if fail_count >= max_fails:
                    self._update_status(cam_id, "⚠️ RTSP inestable, cambiando a HTTP/Snapshot...")
                    print(f"⚠️ Fallback activado para Cam {cam_id}")
                    self._reader_loop_http(cam_id, config)
                    return # Salir del loop RTSP si entramos a HTTP
                
                # Forzar TCP para estabilidad
                if os.name == 'nt':
                     os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
                
                cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
                
                if not cap.isOpened():
                    self._update_status(cam_id, "❌ Error abriendo RTSP")
                    fail_count += 1
                    time.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, max_delay)
                    continue
                
                self._update_status(cam_id, "🚀 RTSP Conectado (TCP)")
                fail_count = 0 # Reset contador
                reconnect_delay = 1.0
                
                # Intentar setear buffer bajo
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                while self.reader_running and cap.isOpened():
                    ret, frame = cap.read()
                    
                    if ret and frame is not None:
                        if cam_id == 1:
                            with self.last_lock1:
                                self.last_frame1 = frame
                        else:
                            with self.last_lock2:
                                self.last_frame2 = frame
                        fail_count = 0 # Éxito continuo
                    else:
                        print(f"⚠️ RTSP C{cam_id}: Frame perdido")
                        break
                
                cap.release()
                if self.reader_running:
                    self._update_status(cam_id, "🔄 Reconectando RTSP...")
                    fail_count += 1
                    time.sleep(1.0)
                    
            except Exception as e:
                self._update_status(cam_id, f"❌ Error RTSP: {e}")
                time.sleep(reconnect_delay)
                fail_count += 1

    def _validate_ip_config(self, config: dict) -> bool:
        """Valida la configuración de cámara IP."""
        ip = config.get('ip', '')
        port = config.get('port', 80)
        
        if not validar_ip(ip):
            print(f"❌ IP inválida: {ip}")
            return False
        if not validar_puerto(port):
            print(f"❌ Puerto inválido: {port}")
            return False
            
        return True
    
    def _validate_webcam_config(self, config: dict) -> bool:
        """Valida la configuración de webcam."""
        index = config.get('index', 0)
        
        if not isinstance(index, int) or index < 0:
            print(f"❌ Índice de webcam inválido: {index}")
            return False
            
        return True
    
    def _validate_file_config(self, config: dict) -> bool:
        """Valida la configuración de archivo."""
        path = config.get('path', '')
        
        if not validar_archivo_video(path):
            print(f"❌ Archivo de video inválido: {path}")
            return False
            
        return True
    
    def _reader_loop_http(self, cam_id: int, config: dict):
        """Loop de captura para cámaras IP HTTP/MJPEG."""
        ip = config['ip']
        user = config['user']
        password = config['pass']
        port = config['port']
        channel = config['channel']
        
        auth_digest = HTTPDigestAuth(user, password)
        auth_basic = HTTPBasicAuth(user, password)
        
        # URLs a probar
        host = f"{ip}:{port}"
        base = f"http://{host}/ISAPI/Streaming/channels/{channel}"
        urls_mjpeg = [
            f"{base}/httpPreview",
            f"{base}/httpPreview?auth=basic"
        ]
        urls_snapshot = [
            f"{base}/picture",
            f"{base}/picture?snapShotImageType=JPEG"
        ]
        
        backoff = 0.5
        max_backoff = 5.0
        target_fps = 15  # FPS objetivo para la captura
        frame_interval = 1.0 / target_fps
        
        while self.reader_running:
            start_time = time.time()
            connected = False
            # Intentar MJPEG primero
            for url in urls_mjpeg:
                try:
                    self._update_status(cam_id, f"🔄 Probando MJPEG: {url.split('/')[-1]}")
                    with requests.get(url, auth=auth_digest, stream=True, timeout=10) as r:
                        if r.status_code in (401, 403, 404):
                            continue
                        r.raise_for_status()
                        # Procesar stream MJPEG
                        if self._process_mjpeg_stream(cam_id, r):
                            connected = True
                            backoff = 0.5
                            break
                except requests.exceptions.RequestException as e:
                    print(f"⚠️ Error MJPEG C{cam_id}: {e}")
                    continue
            # Si MJPEG falló, intentar snapshot
            if not connected and self.reader_running:
                for url in urls_snapshot:
                    try:
                        self._update_status(cam_id, f"🔄 Usando snapshot: {url.split('/')[-1]}")
                        if self._process_snapshot_stream(cam_id, url, auth_digest):
                            connected = True
                            backoff = 0.5
                            break
                    except Exception as e:
                        print(f"⚠️ Error snapshot C{cam_id}: {e}")
                        continue
            if not connected and self.reader_running:
                self._update_status(cam_id, f"❌ Reconectando en {backoff:.1f}s...")
                time.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)
            elif connected:
                elapsed = time.time() - start_time
                sleep_time = max(0, frame_interval - elapsed)
                time.sleep(sleep_time)
    
    def _process_mjpeg_stream(self, cam_id: int, response) -> bool:
        """Procesa un stream MJPEG."""
        try:
            content_type = response.headers.get('Content-Type', '')
            boundary = None
            
            if 'boundary=' in content_type:
                boundary = content_type.split('boundary=')[-1].strip().strip('"')
                if not boundary.startswith('--'):
                    boundary = '--' + boundary
                boundary = boundary.encode('utf-8')
            
            buffer = b""
            self._update_status(cam_id, "▶️ MJPEG conectado")
            
            for chunk in response.iter_content(chunk_size=4096):
                if not self.reader_running:
                    break
                    
                if not chunk:
                    continue
                    
                buffer += chunk
                
                # Procesar con boundary si está disponible
                if boundary and boundary in buffer:
                    parts = buffer.split(boundary)
                    buffer = parts[-1]
                    
                    for part in parts[:-1]:
                        self._extract_jpeg_from_part(cam_id, part)
                    continue
                
                # Buscar JPEGs directamente en el buffer
                self._extract_jpeg_from_buffer(cam_id, buffer)
                
            return True
            
        except Exception as e:
            print(f"❌ Error procesando MJPEG C{cam_id}: {e}")
            return False
    
    def _extract_jpeg_from_part(self, cam_id: int, part: bytes):
        """Extrae JPEG de una parte del stream MJPEG."""
        header_end = part.find(b'\\r\\n\\r\\n')
        if header_end != -1:
            jpeg_bytes = part[header_end + 4:]
            if jpeg_bytes:
                self._decode_and_store_frame(cam_id, jpeg_bytes)
    
    def _extract_jpeg_from_buffer(self, cam_id: int, buffer: bytes):
        """Extrae JPEGs directamente del buffer."""
        while True:
            soi = buffer.find(b'\\xff\\xd8')  # Start of Image
            eoi = buffer.find(b'\\xff\\xd9')  # End of Image
            
            if soi != -1 and eoi != -1 and eoi > soi:
                jpeg_bytes = buffer[soi:eoi + 2]
                buffer = buffer[eoi + 2:]
                self._decode_and_store_frame(cam_id, jpeg_bytes)
            else:
                break
    
    def _process_snapshot_stream(self, cam_id: int, url: str, auth) -> bool:
        """Procesa capturas individuales (snapshot)."""
        try:
            self._update_status(cam_id, "▶️ SNAPSHOT activo")
            
            while self.reader_running:
                response = requests.get(url, auth=auth, timeout=5)
                response.raise_for_status()
                
                if response.content:
                    self._decode_and_store_frame(cam_id, response.content)
                
                time.sleep(0.08)  # ~12.5 FPS
                
            return True
            
        except Exception as e:
            print(f"❌ Error snapshot C{cam_id}: {e}")
            return False
    
    def _decode_and_store_frame(self, cam_id: int, jpeg_bytes: bytes):
        """Decodifica bytes JPEG y almacena el frame."""
        try:
            img = cv2.imdecode(np.frombuffer(jpeg_bytes, np.uint8), cv2.IMREAD_COLOR)
            if img is not None:
                if cam_id == 1:
                    with self.last_lock1:
                        self.last_frame1 = img
                else:
                    with self.last_lock2:
                        self.last_frame2 = img
        except Exception as e:
            print(f"⚠️ Error decodificando frame C{cam_id}: {e}")
    
    def _reader_loop_webcam(self, cam_id: int, config: dict):
        """Loop de captura para webcam."""
        webcam_idx = config['index']
        
        try:
            cap = cv2.VideoCapture(webcam_idx)
            
            if cam_id == 1:
                self.cap1 = cap
            else:
                self.cap2 = cap
            
            if not cap.isOpened():
                self._update_status(cam_id, f"❌ No se pudo abrir webcam {webcam_idx}")
                return
            
            # Configurar resolución si es posible
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            self._update_status(cam_id, f"▶️ Webcam {webcam_idx} iniciada")
            

            target_fps = 15  # FPS objetivo para webcam
            frame_interval = 1.0 / target_fps
            while self.reader_running:
                start_time = time.time()
                ret, frame = cap.read()
                if ret and frame is not None:
                    if cam_id == 1:
                        with self.last_lock1:
                            self.last_frame1 = frame
                    else:
                        with self.last_lock2:
                            self.last_frame2 = frame
                else:
                    time.sleep(0.03)  # Esperar si no hay frame
                elapsed = time.time() - start_time
                sleep_time = max(0, frame_interval - elapsed)
                time.sleep(sleep_time)
                    
        except Exception as e:
            self._update_status(cam_id, f"❌ Error webcam: {e}")
        finally:
            if 'cap' in locals():
                cap.release()
            if cam_id == 1:
                self.cap1 = None
            else:
                self.cap2 = None
    
    def _reader_loop_file(self, cam_id: int, config: dict):
        """Loop de captura para archivo de video."""
        video_path = config['path']
        
        try:
            cap = cv2.VideoCapture(video_path)
            
            if cam_id == 1:
                self.cap1 = cap
            else:
                self.cap2 = cap
            
            if not cap.isOpened():
                self._update_status(cam_id, f"❌ No se pudo abrir archivo {video_path}")
                return
            
            # Obtener FPS del video para sincronización
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30  # FPS por defecto
            frame_delay = 1.0 / fps
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            self._update_status(cam_id, f"▶️ Archivo iniciado (FPS: {fps:.1f}, Frames: {total_frames})")
            
            while self.reader_running:
                ret, frame = cap.read()
                if ret and frame is not None:
                    if cam_id == 1:
                        with self.last_lock1:
                            self.last_frame1 = frame
                    else:
                        with self.last_lock2:
                            self.last_frame2 = frame
                    
                    time.sleep(frame_delay)
                else:
                    # Reiniciar video al final (loop infinito)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self._update_status(cam_id, "🔄 Reiniciando video")
                    time.sleep(0.1)
                    
        except Exception as e:
            self._update_status(cam_id, f"❌ Error archivo: {e}")
        finally:
            if 'cap' in locals():
                cap.release()
            if cam_id == 1:
                self.cap1 = None
            else:
                self.cap2 = None
    
    def optimize_for_hikvision(self):
        """
        Optimizaciones específicas para cámaras Hikvision DS-2CD1653G0-IZ.
        Ajusta parámetros para menor latencia y mejor rendimiento.
        """
        print("🚀 Aplicando optimizaciones para Hikvision DS-2CD1653G0-IZ...")
        
        # Optimizaciones de configuración
        optimizations = {
            'buffer_size': 1,  # Buffer mínimo para reducir latencia
            'tcp_timeout': 5000,  # 5 segundos timeout
            'max_retries': 3,
            'frame_skip': 2,  # Saltar frames para reducir carga
        }
        
        # Aplicar configuraciones específicas para IP cameras
        if hasattr(self, 'ip_stream_configs'):
            self.ip_stream_configs = {
                **self.ip_stream_configs,
                **optimizations
            }
        else:
            self.ip_stream_configs = optimizations
        
        # Configurar URLs optimizadas para Hikvision
        self._setup_hikvision_urls()
        
        print("✅ Optimizaciones aplicadas para mejor latencia")
    
    def _setup_hikvision_urls(self):
        """Configura URLs optimizadas para cámaras Hikvision."""
        # URLs específicas para menor latencia en Hikvision
        hikvision_urls = {
            'main': '/ISAPI/Streaming/channels/101/picture',  # Stream principal
            'sub': '/ISAPI/Streaming/channels/102/picture',   # Sub-stream (menor latencia)
            'mjpeg': '/ISAPI/Streaming/channels/101/httpPreview',  # MJPEG optimizado
        }
        
        # Configurar para usar sub-stream si existe
        for cam_id in [1, 2]:
            cam_config = self.config.get_camera_config(cam_id)
            if cam_config['tipo'] == 'ip' and 'DS-2CD' in str(cam_config.get('modelo', '')):
                # Usar sub-stream para menor latencia
                base_url = f"http://{cam_config['ip']}:{cam_config['puerto']}"
                cam_config['url'] = f"{base_url}{hikvision_urls['sub']}"
                print(f"📹 Cam{cam_id}: URL optimizada para Hikvision")
    
    def set_low_latency_mode(self, enabled: bool = True):
        """
        Activa/desactiva modo de baja latencia.
        
        Args:
            enabled: Si activar el modo de baja latencia
        """
        self.low_latency_mode = enabled
        
        if enabled:
            # Reducir buffer y timeouts
            self.target_fps = 25
            self.max_frame_age = 0.1  # 100ms máximo
            print("⚡ Modo baja latencia ACTIVADO")
        else:
            # Valores normales
            self.target_fps = 15
            self.max_frame_age = 0.5
            print("🔄 Modo latencia normal")
    
    def get_frames_optimized(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Versión optimizada de get_frames para modo de baja latencia.
        Descarta frames antiguos y prioriza los más recientes.
        
        Returns:
            Tupla (frame1, frame2) con frames más recientes disponibles
        """
        frame1, frame2 = None, None
        current_time = time.time()
        
        # Frame 1 con verificación de edad
        if self.last_frame1 is not None:
            try:
                with self.last_lock1:
                    # En modo baja latencia, verificar edad del frame
                    if hasattr(self, 'low_latency_mode') and self.low_latency_mode:
                        # Tomar frame solo si es reciente
                        frame1 = self.last_frame1.copy()
                    else:
                        frame1 = self.last_frame1.copy()
            except:
                frame1 = None
        
        # Frame 2 con verificación de edad
        if self.last_frame2 is not None:
            try:
                with self.last_lock2:
                    if hasattr(self, 'low_latency_mode') and self.low_latency_mode:
                        frame2 = self.last_frame2.copy()
                    else:
                        frame2 = self.last_frame2.copy()
            except:
                frame2 = None
        
        return frame1, frame2
    
    def cleanup(self):
        """Limpieza de recursos al cerrar."""
        print("🧹 Limpiando recursos de cámaras...")
        self.stop_cameras()  # Usar el método correcto
        
        # Limpiar capturas
        for cap in [getattr(self, 'cap1', None), getattr(self, 'cap2', None)]:
            if cap:
                cap.release()
        
        # Limpiar frames
        self.last_frame1 = None
        self.last_frame2 = None
        
        print("✅ Recursos limpiados")