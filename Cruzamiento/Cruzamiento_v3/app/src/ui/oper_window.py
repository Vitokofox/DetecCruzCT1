from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QGroupBox, QSizePolicy, QMessageBox, QApplication
)
from PySide6.QtGui import QIcon, QPixmap, QPixmap, QImage
from PySide6.QtCore import Qt, QTimer

import sys
import os
import cv2
import numpy as np
from datetime import datetime

# Importar módulos refactorizados
from src.config import CamConfig
from src.services.camera_handler import CameraHandler
from src.services.detection_handler import DetectionHandler
from src.services.plc_service import PLCService
from src.services.video_recorder import VideoRecorder, DEFAULT_TARGET_FPS
from src.ui.operator_alert import OperatorAlert

class OperWindow(QWidget):
    """
    Ventana principal de operador: contiene toda la apariencia y los widgets
    para interactuar con la aplicación.
    Versión Refactorizada.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Panel Operador - Sistema de Detección")
        self.setGeometry(120, 120, 1200, 800)
        
        # Icono (ajustar ruta si es necesario)
        # Asumiendo ejecución desde root del proyecto
        icon_path = os.path.join("assets", "icono.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # --- 1. Cargar Configuración ---
        self.cfg = CamConfig.load()
        
        # --- 2. Inicializar Componentes ---
        self.camera_handler = CameraHandler(self.cfg)
        self.plc_service = PLCService(self.cfg)
        self.detection_handler = DetectionHandler(self.cfg, self.plc_service)
        self.video_recorder = VideoRecorder()
        self.video_recorder.setup_directories(os.getcwd())
        
        # Configurar callbacks de handlers
        self.camera_handler.set_status_callback(self._update_camera_status)
        self.detection_handler.set_status_callback(self._update_model_status)
        
        # Timers
        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self._update_video_frames)
        # Estados PLC específicos de esta ventana
        self.cadena_corta_operativa = False
        self.cadena_larga_operativa = False
        self.esperando_reenganche = False
        self.contador_reenganche = 0
        self.plc_min_iter_ok = 10
        
        # Estado Seguridad Operador
        self.operator_safety_active = False # Si estamos en modo seguridad (aislamiento)
        self.operator_cooldown_counter = 0  # Contador de frames libres de operador
        self.is_operator_detected = False   # Estado en el frame actual
        
        # Últimos frames
        self.last_frame1_det = None

        # --- 3. Construir UI ---
        self._init_ui()
        
        # Inicializar alerta
        self.operator_alert = OperatorAlert(self.alert_widget, self.cfg)
        self.detection_handler.set_alert_callback(self.operator_alert.update_operator_status)
        
        # Intentar conectar PLC al inicio (opcional, igual que antes)
        if self.cfg.plc_enabled:
            self.plc_service.connect()
            
        print("🚀 OperWindow inicializada (Refactorizada)")

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Estilos (Tema Oscuro)
        self.setStyleSheet("""
            QWidget { background-color: #000000; color: #ffffff; font-size: 11pt; }
            QGroupBox { font-weight: bold; border: 1px solid #444; border-radius: 5px; margin-top: 10px; color: #ffffff; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; background-color: #000000; }
            QLabel { color: #ffffff; }
            QPushButton { padding: 8px; border-radius: 4px; background-color: #007bff; color: white; font-weight: bold; border: none; }
            QPushButton:hover { background-color: #0056b3; }
            QPushButton:pressed { background-color: #004085; }
        """)

        # 1. Header
        logo_label = QLabel()
        logo_path = os.path.join("assets", "logo-arauco.png")
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            if not logo_pixmap.isNull():
                logo_resized = logo_pixmap.scaled(
                    logo_pixmap.width() // 2, logo_pixmap.height() // 2,
                    Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
                logo_label.setPixmap(logo_resized)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        # 2. Alerta Operador (Nuevo)
        self.alert_widget = QLabel("⚠️ OPERADOR CERCA DE LA LÍNEA ⚠️")
        self.alert_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.alert_widget.setStyleSheet("color: red; font-size: 20px; font-weight: bold; background-color: yellow; padding: 5px;")
        self.alert_widget.hide()
        layout.addWidget(self.alert_widget)

        # 3. Video Area
        video_group = QGroupBox("📹 Visualización de Cámara")
        video_layout = QHBoxLayout()
        
        self.video_label1 = QLabel("Cámara 1")
        self.video_label1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_label1.setMinimumSize(400, 300)
        self.video_label1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label1.setStyleSheet("background-color: black; color: white;")
        video_layout.addWidget(self.video_label1, 3)
        
        # Panel Info Lateral
        info_panel = self._create_info_panel()
        video_layout.addWidget(info_panel, 1)
        
        video_group.setLayout(video_layout)
        layout.addWidget(video_group)

        # 4. Controles
        controls_group = QGroupBox("Controles")
        controls_layout = QHBoxLayout()
        
        self.btn_start_video = QPushButton("Iniciar Video")
        self.btn_start_detection = QPushButton("Iniciar Detección")
        self.btn_stop_detection = QPushButton("Detener Detección")
        self.btn_record_clean = QPushButton("📹 Grabar Video") # Cambiado a Video
        self.btn_stop_record = QPushButton("⏹️ Parar Grabación")
        self.btn_config = QPushButton("Configuración")
        
        # Colores específicos
        self.btn_stop_detection.setStyleSheet("background-color: #dc3545; color: white;")
        self.btn_stop_record.setStyleSheet("background-color: #dc3545; color: white;")
        
        controls_layout.addWidget(self.btn_start_video)
        controls_layout.addWidget(self.btn_start_detection)
        controls_layout.addWidget(self.btn_stop_detection)
        controls_layout.addWidget(self.btn_record_clean)
        controls_layout.addWidget(self.btn_stop_record)
        controls_layout.addWidget(self.btn_config)
        
        # Botón Monitor PLC
        self.btn_plc_monitor = QPushButton("Monitor PLC")
        self.btn_plc_monitor.setStyleSheet("background-color: #6c757d; color: white;") # Gris
        controls_layout.addWidget(self.btn_plc_monitor)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Conectar señales
        self.btn_start_video.clicked.connect(self.start_video)
        self.btn_start_detection.clicked.connect(self.start_detection)
        self.btn_stop_detection.clicked.connect(self.stop_detection)
        self.btn_record_clean.clicked.connect(lambda: self.start_recording(with_detections=False))
        self.btn_stop_record.clicked.connect(self.stop_recording)
        self.btn_config.clicked.connect(self.open_config_window)
        self.btn_plc_monitor.clicked.connect(self.launch_plc_monitor)

        # 5. Status Bar
        status_group = QGroupBox("Estado del Sistema")
        status_layout = QHBoxLayout()
        
        self.status_global = QLabel("🔴 SISTEMA DETENIDO")
        self.status_video = QLabel("📹 Video: OFF")
        self.status_model = QLabel("🧠 Modelo: OFF")
        self.status_detection = QLabel("🤖 Detección: OFF")
        self.status_recording = QLabel("🔴 Rec: OFF")
        self.status_plc = QLabel("🔌 PLC: OFF")
        
        for lbl in [self.status_global, self.status_video, self.status_model, 
                    self.status_detection, self.status_recording, self.status_plc]:
            lbl.setStyleSheet("font-weight: bold;")
            status_layout.addWidget(lbl)
            
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        self.setLayout(layout)

    def _create_info_panel(self):
        panel = QWidget()
        layout = QVBoxLayout()
        
        lbl_title = QLabel("Información Detección")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(lbl_title)
        
        self.detection_summary = QLabel("Esperando datos...")
        self.detection_summary.setWordWrap(True)
        self.detection_summary.setStyleSheet("background-color: #222; color: white; padding: 10px; border-radius: 5px; border: 1px solid #444;")
        layout.addWidget(self.detection_summary)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel

    # --- Lógica Principal ---

    def start_video(self):
        """Inicia cámaras y timer."""
        if self.camera_handler.start_cameras():
            self.main_timer.start(int(1000 / DEFAULT_TARGET_FPS))
            self.status_video.setText("📹 Video: ON")
            
            # Conectar PLC si es necesario
            if self.cfg.plc_enabled:
                self.plc_service.connect()
        else:
            QMessageBox.critical(self, "Error", "No se pudieron iniciar las cámaras.")

    def stop_video(self):
        """Detiene cámaras, timers y servicios conexos."""
        self.main_timer.stop()
        self.camera_handler.stop_cameras()
        self.stop_detection()
        self.stop_recording()
        
        # Cerrar PLC si está abierto
        if self.plc_service:
            self.plc_service.close()

        self.status_video.setText("📹 Video: OFF")
        self.status_plc.setText("🔌 PLC: OFF")
        self.status_global.setText("🔴 SISTEMA DETENIDO")
        
        # Limpiar visualización
        self.video_label1.clear()
        self.video_label1.setText("Cámara 1")

    def start_detection(self):
        """Inicia detección."""
        if self.detection_handler.load_model(): # Asegurar modelo cargado
            if self.detection_handler.start_detection():
                self.status_detection.setText("🤖 Detección: ON")
            else:
                QMessageBox.warning(self, "Error", "Falló inicio de detección.")
        else:
            QMessageBox.warning(self, "Error", "No se pudo cargar el modelo.")

    def stop_detection(self):
        self.detection_handler.stop_detection()
        self.status_detection.setText("🤖 Detección: PAUSA")

    def start_recording(self, with_detections: bool):
        # Obtener frames actuales
        frame1, frame2 = self.camera_handler.get_frames()
        if self.video_recorder.start_recording(frame1, frame2, with_detections):
             self.status_recording.setText("🔴 Rec: ON")
        else:
             QMessageBox.warning(self, "Error", "No se pudo iniciar grabación (verifique cámaras).")

    def stop_recording(self):
        self.video_recorder.stop_recording()
        self.status_recording.setText("🔴 Rec: OFF")

    def open_config_window(self):
        # Import local
        try:
            from src.ui.config_window import ConfigWindow
            self.conf_win = ConfigWindow(self)
            self.conf_win.config_changed.connect(self.on_config_changed)
            self.conf_win.show()
        except ImportError as e:
            QMessageBox.warning(self, "Error", f"Módulo de configuración no encontrado: {e}")

    def launch_plc_monitor(self):
        """
        Lanza el monitor PLC en una consola separada.
        Maneja tanto ejecución como script (python src/services/plc_monitor.py)
        como ejecución compilada (ejecutable independiente).
        """
        import subprocess
        import sys
        
        try:
            if getattr(sys, 'frozen', False):
                # Si estamos compilados, asumimos que PLC Monitor también se compiló 
                # y está en la misma carpeta (o es un subproceso del mismo exe, pero lo más fácil es otro exe)
                # Estrategia: Buscamos 'plc_monitor.exe' en la misma carpeta
                base_dir = os.path.dirname(sys.executable)
                monitor_exe = os.path.join(base_dir, "plc_monitor.exe")
                
                if os.path.exists(monitor_exe):
                    subprocess.Popen([monitor_exe], creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    # Fallback raro: ¿está dentro de este mismo exe?
                    QMessageBox.warning(self, "Error", f"No se encontró el ejecutable del monitor en: {monitor_exe}")
            else:
                # Modo script: lanzar python src/services/plc_monitor.py
                # Estamos corriendo desde root, así que referenciamos el archivo en src/services
                script_path = os.path.join("src", "services", "plc_monitor.py")
                if not os.path.exists(script_path):
                     # Try absolute path based on this file
                     base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                     script_path = os.path.join(base_dir, "services", "plc_monitor.py")

                # Windows: 'start cmd /k ...' para mantener ventana abierta
                # Usamos Popen con creationflags para abrir nueva ventana de consola limpiamente
                cmd = [sys.executable, script_path]
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error lanzando Monitor PLC: {e}")

    def on_config_changed(self):
        """
        Maneja el cambio de configuración: recarga y reinicia servicios suavemente.
        """
        print("🔄 Recargando configuración y reiniciando servicios...")
        
        # 1. Guardar estado actual
        was_video_running = self.camera_handler.is_running()
        was_detecting = self.detection_handler.is_detecting()
        
        # 2. Detener todo
        self.stop_video() # Esto detiene cámaras, grabción, detección y cierra PLC
        
        # 3. Recargar Configuración
        try:
            self.cfg = CamConfig.load()
            print("✅ Configuración recargada desde disco")
        except Exception as e:
            QMessageBox.critical(self, "Error Fatal", f"Error recargando configuración: {e}")
            return

        # 4. Actualizar referencias en Handlers
        # Camera Handler
        self.camera_handler.config = self.cfg
        
        # PLC Service - Recrear para actualizar mapas de registros
        try:
            if self.plc_service:
                self.plc_service.close()
            self.plc_service = PLCService(self.cfg)
            print("✅ PLC Service recreado con nueva configuración")
        except Exception as e:
            print(f"⚠️ Error recreando PLC Service: {e}")

        # Detection Handler
        self.detection_handler.config = self.cfg
        self.detection_handler.plc_service = self.plc_service
        
        # Re-inicializar componentes internos del DetectionHandler
        # (BrokenPieceAnalyzer se crea en __init__, necesitamos actualizarlo)
        if hasattr(self.detection_handler, 'broken_piece_analyzer'):
             from src.utils.broken_piece_analyzer import BrokenPieceAnalyzer
             self.detection_handler.broken_piece_analyzer = BrokenPieceAnalyzer(self.cfg)
             print("✅ BrokenPieceAnalyzer actualizado")

        # Alerta Operador - Recrear
        self.operator_alert = OperatorAlert(self.alert_widget, self.cfg)
        self.detection_handler.set_alert_callback(self.operator_alert.update_operator_status)
        
        # 5. Feedback al usuario
        QMessageBox.information(self, "Configuración Actualizada", 
                              "✅ Configuración aplicada correctamente.\n\n"
                              "Los servicios se han reiniciado con los nuevos parámetros.")

        # 6. Restaurar estado anterior
        if was_video_running:
            print("🔄 Reiniciando video...")
            self.start_video()
            
            if was_detecting:
                print("🔄 Reiniciando detección...")
                # Pequeño delay para dar tiempo a las cámaras
                QTimer.singleShot(500, self.start_detection)

    def _update_video_frames(self):
        """Loop principal llamado por timer."""
        # 1. Obtener frames
        frame1, frame2 = self.camera_handler.get_frames()
        
        if frame1 is None and frame2 is None:
            return

        # 2. Procesar (solo frame 1 para visualización principal, o ambos si necesario)
        # OperWindow muestra Cam1 principalmente, pero DetectionHandler puede procesar ambos.
        # Por eficiencia, si solo mostramos Cam1, procesamos Cam1 para display.
        # Pero DetectionHandler puede que quiera procesar Cam2 para logs?
        # Procesaremos Cam1 para mostrar.
        
        info = {}
        if frame1 is not None:
            # Procesar frame
            frame1_display, info = self.detection_handler.process_frame(
                frame1.copy(), 1, self.detection_handler.is_detecting()
            )
            self.last_frame1_det = frame1_display
            
            # Mostrar en GUI
            self._show_frame(self.video_label1, frame1_display)
            
            # Actualizar info panel
            self._update_info_panel(info)

        # 3. Grabar si activo
        if self.video_recorder.recording:
            # Necesitamos frame2 si existe
            # Si frame2 existe, deberíamos procesarlo también si queremos grabar con detecciones
            frame2_det = None
            if frame2 is not None and self.video_recorder.record_with_detections:
                 frame2_det, _ = self.detection_handler.process_frame(
                     frame2.copy(), 2, self.detection_handler.is_detecting()
                 )
            self.video_recorder.write_frames(frame1, frame2, self.last_frame1_det, frame2_det)

        # 3.5 Actualizar estado operador (para lógica PLC)
        self.is_operator_detected = info.get('operator_detected', False)
        
        # 4. Actualizar estado PLC
        self._update_plc_status_logic()


    def _show_frame(self, label, frame):
        """Convierte OpenCV frame a QPixmap y muestra."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        # Escalar manteniendo aspecto
        pixmap = pixmap.scaled(label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(pixmap)

    def _update_info_panel(self, info):
        if not info:
             return
        
        num = info.get('num_detections', 0)
        broken = info.get('broken_pieces', 0)
        dets = info.get('detections', [])
        
        text = f"<h3>Detecciones: {num}</h3>"
        if broken > 0:
            text += f"<p style='color:red'>Quebradas: {broken}</p>"
        
        # Listar ultimas
        if dets:
            text += "<ul>"
            for d in dets[:5]: # Mostrar max 5
                lbl = d.get('label', '?')
                conf = d.get('confidence', 0.0)
                text += f"<li>{lbl} ({conf:.2f})</li>"
            text += "</ul>"
            
        self.detection_summary.setText(text)

    # --- Lógica PLC (Preservada/Adaptada) ---
    def _update_plc_status_logic(self):
        if not self.plc_service: 
            return
            
        connected = self.plc_service.is_connected()
        self.status_plc.setText(f"🔌 PLC: {'ON' if connected else 'OFF'}")
        
        # Lógica de colores del status global
        # La lógica original leía registros 10203/10204. Modificado para solo leer 10204.
        if connected:
             # st_corta = self.plc_service.read_status_register(10203) # REMOVIDO POR SOLICITUD
             st_larga = self.plc_service.read_status_register(10204)
             
             # self.cadena_corta_operativa = (st_corta == 1) # REMOVIDO
             self.cadena_larga_operativa = (st_larga == 1)
             
             # --- Reenganche Logic ---
             # Antes: if not self.cadena_corta_operativa or not self.cadena_larga_operativa:
             if not self.cadena_larga_operativa:
                 # Cadenas NO operativas
                 if not self.esperando_reenganche:
                     # Transición a estado de espera/desconexión
                     self.plc_service.desconectar_senal()
                     self.esperando_reenganche = True
                 
                 # IMPORTANTE: Siempre reiniciar el contador si las cadenas fallan
                 # "si la cadena se detienne mientras el contador esta en curso deve reiniciarce"
                 self.contador_reenganche = 0
                     
             else:
                 # Cadenas OK
                 if self.esperando_reenganche:
                     self.contador_reenganche += 1
                     min_iter = self.plc_service.get_reenganche_param()
                     if self.contador_reenganche >= min_iter:
                         self.plc_service.reconectar_senal()
                         self.esperando_reenganche = False
                         self.contador_reenganche = 0
                 else:
                     self.contador_reenganche = 0
                     
             # --- Lógica de Seguridad Operador ---
             if self.is_operator_detected:
                 # Operador detectado: ACTIVAR AISLAMIENTO INMEDIATO
                 if not self.operator_safety_active:
                     self.plc_service.set_isolation(True)
                     self.operator_safety_active = True
                 self.operator_cooldown_counter = 0 # Reiniciar contador
                 
             elif self.operator_safety_active:
                 # Operador NO detectado pero seguía activo el aislamiento
                 self.operator_cooldown_counter += 1
                 # Chequear si cumplimos los frames de seguridad
                 safety_frames = getattr(self.cfg, 'operator_safety_frames', 30)
                 if self.operator_cooldown_counter >= safety_frames:
                     # LIBERAR AISLAMIENTO si cadenas están OK
                     # Antes: if self.cadena_corta_operativa and self.cadena_larga_operativa:
                     if self.cadena_larga_operativa:
                         self.plc_service.set_isolation(False)
                         self.operator_safety_active = False
                     else:
                         # Si cadenas fallan, seguimos aislados pero permitimos reconexion cuando arreglen cadenas
                         self.plc_service.set_isolation(False) # Dejamos que lógica cadenas maneje enable/disable
                         self.operator_safety_active = False

             # Actualizar Label Global con prioridad
             if not connected:
                 self.status_global.setText("🔴 PLC DESCONECTADO")
                 self.status_plc.setText("🔌 PLC: OFF")
             
             elif self.operator_safety_active:
                 frames_left = getattr(self.cfg, 'operator_safety_frames', 30) - self.operator_cooldown_counter
                 frames_left = max(0, frames_left)
                 self.status_global.setText(f"🟡 AISLAMIENTO SEGURIDAD: {frames_left}")
                 self.status_global.setStyleSheet("color: orange; font-weight: bold; background-color: #222;")
                 self.status_plc.setText("🔌 PLC: BLOQUEADO 🔒")
                 
             elif self.esperando_reenganche:
                 # Mostrar countdown de reenganche
                 # Antes: if self.cadena_corta_operativa and self.cadena_larga_operativa:
                 if self.cadena_larga_operativa:
                     # Cadenas OK, contando para reenganchar
                     min_iter = self.plc_service.get_reenganche_param()
                     restante = max(0, min_iter - self.contador_reenganche)
                     self.status_global.setText(f"⏳ RECONECTANDO EN: {restante}")
                     self.status_global.setStyleSheet("color: yellow; font-weight: bold; background-color: #444;")
                     self.status_plc.setText("🔌 PLC: ESPERA")
                 else:
                     # Cadenas detenidas
                     self.status_global.setText("🔴 SISTEMA ESPERA/DETENIDO")
                     self.status_global.setStyleSheet("color: red; font-weight: bold;")
                     self.status_plc.setText("🔌 PLC: PAUSA")

             # Antes: elif self.cadena_corta_operativa and self.cadena_larga_operativa:
             elif self.cadena_larga_operativa:
                 self.status_global.setText("🟢 SISTEMA CONECTADO")
                 self.status_global.setStyleSheet("color: green; font-weight: bold;")
                 self.status_plc.setText("🔌 PLC: ON")
             else:
                 # Caso fallback para cuando cadena_larga_operativa es False
                 # (Aunque debería caer en esperando_reenganche, por seguridad visual)
                 self.status_global.setText("🔴 SISTEMA DETENIDO")
                 self.status_global.setStyleSheet("color: red; font-weight: bold;")
        else:
             self.status_global.setText("🔴 PLC DESCONECTADO")
             self.status_plc.setText("🔌 PLC: OFF")

    def _update_camera_status(self, cam_id, msg):
        print(f"CamStatus {cam_id}: {msg}")

    def _update_model_status(self, msg):
        self.status_model.setText(f"🧠 {msg}")

    def closeEvent(self, event):
        """Limpieza al cerrar."""
        self.main_timer.stop()
        self.camera_handler.stop_cameras()
        self.video_recorder.stop_recording()
        if self.plc_service:
            self.plc_service.close()
        event.accept()

def run_app():
    app = QApplication(sys.argv)
    window = OperWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_app()
