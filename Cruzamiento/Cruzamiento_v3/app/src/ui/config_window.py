"""
Ventana de configuración del sistema de detección.

Configura:
- Cámara 1
- Modelo YOLO
- ROI
- PLC
- Medición
- Alertas
- Opciones avanzadas (grabación, tracking)
"""

import json
import os
from typing import Dict, Any
import cv2
import numpy as np

from PySide6.QtCore import Qt, Signal as pyqtSignal, QEvent
from PySide6.QtGui import QColor, QImage, QPixmap, QPainter, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QColorDialog,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QDoubleSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.config import CONFIG_FILE


class ConfigWindow(QDialog):
    """
    Ventana de configuración del sistema de detección.

    Pestañas:
    - Cámaras
    - Modelo IA
    - ROI
    - PLC
    - Medición
    - Alertas
    - Avanzado
    """

    # Señal emitida cuando se guarda la configuración
    config_changed = pyqtSignal()

    # ------------------------------------------------------------------ #
    # Init
    # ------------------------------------------------------------------ #
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("⚙️ Configuración del Sistema")
        self.setModal(True)
        self.resize(800, 650)

        # Cargar JSON de configuración
        self.config: Dict[str, Any] = self._load_json_config()

        # Tabs
        self.tab_widget = QTabWidget(self)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.tab_widget)

        # Crear pestañas
        self.create_cameras_tab()
        self.create_model_tab()
        self.create_roi_tab()
        self.create_plc_tab()
        self.create_measurement_tab()
        self.create_alerts_tab()
        self.create_advanced_tab()

        # Botones inferiores
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.save_btn = QPushButton("💾 Guardar")
        self.cancel_btn = QPushButton("Cancelar")
        self.help_btn = QPushButton("❓ Ayuda")

        self.save_btn.clicked.connect(self.save_config)
        self.cancel_btn.clicked.connect(self.reject)
        self.help_btn.clicked.connect(self.show_help)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.help_btn)

        main_layout.addLayout(btn_layout)

        # Cargar valores en widgets desde self.config
        self.load_config_values()

    # ------------------------------------------------------------------ #
    # Utilidades de carga/guardado JSON
    # ------------------------------------------------------------------ #
    def _default_config(self) -> Dict[str, Any]:
        """Valores por defecto si no existe config_camera.json."""
        return {
            "cam1_tipo": "ip",
            "cam1_conexion": "RTSP",
            "cam_ip": "",
            "cam_user": "",
            "cam_pass": "",
            "http_port": 80,
            "cam_port": 554,
            "connection_type": "RTSP",
            "channel": "101",
            "cam1_webcam_idx": 0,
            "cam1_archivo": "",
            "model_path": "",
            "min_confidence": 0.5,
            "roi_scale_1": 0.5,
            "roi_offset_x_1": 0.0,
            "plc_enabled": False,
            "plc_ip": "",
            "plc_port": 502,
            "plc_unit_id": 1,
            "umbral_movimiento": 5,
            "plc_reg_addr_1": 22001,
            "plc_reg_addr_2": 22002,
            "plc_reg_addr_3": 22003,
            "plc_reg_addr_operador": 22004,
            "plc_reg_addr_pieza_quebrada": 22005,
            "plc_reg_addr_alaveo": 22006,
            "plc_enable_cruzamiento": True,
            "plc_enable_cruzymnt": True,
            "plc_enable_montada": False,
            "plc_enable_operador": True,
            "alertar_pieza_quebrada": True,
            "plc_enable_alaveo": False,
            "plc_reg_pulse_value": 1,
            "plc_pulse_ms": 300,
            "plc_cooldown_s": 1.0,
            "medicion_enabled": True,
            "medicion_units": "mm",
            "escala_px_por_mm_cam1": 1.0,
            "mostrar_medidas_overlay": True,
            "log_mediciones": True,
            "detectar_piezas_quebradas": True,
            "largo_minimo_pieza_mm": 50.0,
            "min_fragmentos_quebrada": 2,
            "operador_alert_enabled": True,
            "operador_alert_blink": True,
            "operador_alert_color": "#FF0000",
            "auto_recording_enabled": False,
            "auto_record_duration_s": 10.0,
            "save_detection_images": True,
            "tracking_frame_rate": 30,
            "tracking_track_thresh": 0.3,
            "tracking_high_thresh": 0.5,
            "tracking_match_thresh": 0.7,
            "tracking_track_buffer": 60,
            # Param para reenganche PLC (iteraciones buenas)
            "plc_reenganche_param": 10,
        }

    def _load_json_config(self) -> Dict[str, Any]:
        """Carga config_camera.json, devolviendo un dict con valores o defaults."""
        if not os.path.exists(CONFIG_FILE):
            return self._default_config()

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"⚠️ Error cargando {CONFIG_FILE}: {e}")
            return self._default_config()

        # Mezclar con defaults para asegurar que no falte nada
        defaults = self._default_config()
        defaults.update(data)
        return defaults

    def _save_json_config(self, path: str) -> None:
        """Guarda self.config en el archivo especificado."""
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise RuntimeError(f"Error escribiendo {path}: {e}")

    def open_interactive_roi(self):
        """Abre el diálogo para definir ROI interactivamente."""
        parent = self.parent()
        if not parent or not hasattr(parent, 'camera_handler'):
            QMessageBox.warning(self, "Error", "No se puede acceder a la cámara.")
            return

        # Capturar frame (cam 1 por defecto)
        frame = parent.camera_handler.get_frame(1)
        if frame is None:
             QMessageBox.warning(self, "Error", "No se pudo capturar imagen de la cámara 1.\nVerifique que esté conectada y activa.")
             return
        
        # Obtener puntos actuales si existen
        current_points = self.config.get("roi_points_cam1", [])
        
        # Abrir diálogo
        dialog = InteractiveROIDialog(frame, current_points, self)
        if dialog.exec() == QDialog.Accepted:
            points = dialog.points
            if len(points) >= 3:
                # Guardar en config
                self.config["roi_points_cam1"] = points
                QMessageBox.information(self, "Éxito", f"ROI definido con {len(points)} puntos.\nGuarde la configuración para aplicar los cambios.")
            else:
                QMessageBox.warning(self, "Aviso", "Se requieren al menos 3 puntos para definir un ROI.")

    # ------------------------------------------------------------------ #
    # Pestaña: Cámaras
    # ------------------------------------------------------------------ #
    def create_cameras_tab(self) -> None:
        """Crea la pestaña de configuración de cámaras."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        cameras_group = QGroupBox("📹 Configuración de Cámara 1")
        cameras_layout = QFormLayout(cameras_group)

        # Tipo cámara 1
        self.cam1_tipo = QComboBox()
        self.cam1_tipo.addItems(["ip", "webcam", "archivo"])
        self.cam1_tipo.currentTextChanged.connect(self.on_cam1_type_changed)
        cameras_layout.addRow("Tipo Cámara 1:", self.cam1_tipo)

        # IP / Webcam / Archivo
        self.cam1_ip = QLineEdit()
        cameras_layout.addRow("IP Cámara 1:", self.cam1_ip)

        self.cam1_webcam_idx = QSpinBox()
        self.cam1_webcam_idx.setRange(0, 10)
        cameras_layout.addRow("Índice Webcam 1:", self.cam1_webcam_idx)

        self.cam1_archivo = QLineEdit()
        self.cam1_archivo_btn = QPushButton("📁")
        self.cam1_archivo_btn.clicked.connect(
            lambda: self.select_video_file(self.cam1_archivo)
        )
        archivo1_layout = QHBoxLayout()
        archivo1_layout.addWidget(self.cam1_archivo)
        archivo1_layout.addWidget(self.cam1_archivo_btn)
        cameras_layout.addRow("Archivo Cámara 1:", archivo1_layout)

        # Configuración común
        self.connection_type = QComboBox()
        self.connection_type.addItems(["RTSP", "HTTP"])
        self.connection_type.currentTextChanged.connect(
            self.update_connection_warning
        )
        cameras_layout.addRow("Tipo de conexión:", self.connection_type)

        self.cam_user = QLineEdit()
        cameras_layout.addRow("Usuario:", self.cam_user)

        self.cam_pass = QLineEdit()
        self.cam_pass.setEchoMode(QLineEdit.EchoMode.Password)
        cameras_layout.addRow("Contraseña:", self.cam_pass)

        self.cam_port = QSpinBox()
        self.cam_port.setRange(1, 65535)
        self.cam_port.setValue(554)
        cameras_layout.addRow("Puerto RTSP:", self.cam_port)

        self.http_port = QSpinBox()
        self.http_port.setRange(1, 65535)
        self.http_port.setValue(80)
        cameras_layout.addRow("Puerto HTTP:", self.http_port)

        self.channel = QLineEdit()
        cameras_layout.addRow("Channel (cam):", self.channel)

        self.connection_warning = QLabel()
        self.connection_warning.setStyleSheet(
            "color: orange; font-style: italic;"
        )
        cameras_layout.addRow(self.connection_warning)

        layout.addWidget(cameras_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "📹 Cámaras")

    def update_connection_warning(self, value: str) -> None:
        if value.upper() == "HTTP":
            self.connection_warning.setText(
                "⚠️ HTTP puede ser más lento que RTSP. "
                "Se recomienda RTSP para mejor rendimiento."
            )
        else:
            self.connection_warning.setText("")

    def on_cam1_type_changed(self, tipo: str) -> None:
        """Maneja el cambio de tipo de cámara 1."""
        is_ip = tipo == "ip"
        is_webcam = tipo == "webcam"
        is_file = tipo == "archivo"

        self.cam1_ip.setEnabled(is_ip)
        self.cam1_webcam_idx.setEnabled(is_webcam)
        self.cam1_archivo.setEnabled(is_file)
        self.cam1_archivo_btn.setEnabled(is_file)

    # ------------------------------------------------------------------ #
    # Pestaña: Modelo IA
    # ------------------------------------------------------------------ #
    def create_model_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        model_group = QGroupBox("🤖 Modelo de Detección")
        model_layout = QFormLayout(model_group)

        self.model_path = QLineEdit()
        self.model_path_btn = QPushButton("📁")
        self.model_path_btn.clicked.connect(self.select_model_file)
        model_path_layout = QHBoxLayout()
        model_path_layout.addWidget(self.model_path)
        model_path_layout.addWidget(self.model_path_btn)
        model_layout.addRow("Ruta modelo YOLO:", model_path_layout)

        self.min_confidence = QDoubleSpinBox()
        self.min_confidence.setRange(0.1, 1.0)
        self.min_confidence.setSingleStep(0.05)
        self.min_confidence.setDecimals(2)
        model_layout.addRow("Confianza mínima:", self.min_confidence)

        layout.addWidget(model_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "🤖 Modelo")

    # ------------------------------------------------------------------ #
    # Pestaña: ROI
    # ------------------------------------------------------------------ #
    def create_roi_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        roi1_group = QGroupBox("🔲 ROI Cámara 1")
        roi1_layout = QFormLayout(roi1_group)

        self.roi_scale_1 = QDoubleSpinBox()
        self.roi_scale_1.setRange(0.10, 0.90)
        self.roi_scale_1.setSingleStep(0.05)
        self.roi_scale_1.setDecimals(2)
        roi1_layout.addRow("Escala ROI:", self.roi_scale_1)

        self.roi_offset_x_1 = QDoubleSpinBox()
        self.roi_offset_x_1.setRange(-0.5, 0.5)
        self.roi_offset_x_1.setSingleStep(0.05)
        self.roi_offset_x_1.setDecimals(2)
        self.roi_offset_x_1.setDecimals(2)
        roi1_layout.addRow("Offset X:", self.roi_offset_x_1)

        self.btn_interactive_roi = QPushButton("🎨 Definir ROI Interactivamente")
        self.btn_interactive_roi.clicked.connect(self.open_interactive_roi)
        self.btn_interactive_roi.setStyleSheet("background-color: #3498db; color: white; padding: 5px;")
        roi1_layout.addRow("", self.btn_interactive_roi)

        layout.addWidget(roi1_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "🔲 ROI")

    # ------------------------------------------------------------------ #
    # Pestaña: PLC
    # ------------------------------------------------------------------ #
    def create_plc_tab(self) -> None:
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(tab)
        scroll.setWidgetResizable(True)

        layout = QVBoxLayout(tab)

        # Config general PLC
        plc_group = QGroupBox("🏭 Configuración PLC")
        plc_layout = QFormLayout(plc_group)

        self.plc_enabled = QCheckBox("Habilitar comunicación PLC")
        plc_layout.addRow(self.plc_enabled)

        self.plc_ip = QLineEdit()
        plc_layout.addRow("IP del PLC:", self.plc_ip)

        self.plc_port = QSpinBox()
        self.plc_port.setRange(1, 65535)
        self.plc_port.setValue(502)
        plc_layout.addRow("Puerto Modbus:", self.plc_port)

        self.plc_unit_id = QSpinBox()
        self.plc_unit_id.setRange(1, 255)
        plc_layout.addRow("Unit ID:", self.plc_unit_id)

        self.umbral_movimiento_spin = QSpinBox()
        self.umbral_movimiento_spin.setRange(1, 100)
        plc_layout.addRow(
            "Umbral de detecciones para activar PLC:", self.umbral_movimiento_spin
        )

        # Registros positivos para reenganche
        self.reenganche_spin = QSpinBox()
        self.reenganche_spin.setMinimum(1)
        self.reenganche_spin.setMaximum(100)
        self.reenganche_spin.setValue(self.config.get("plc_reenganche_param", 10))
        plc_layout.addRow("Iteraciones buenas para reenganche:", self.reenganche_spin)

        # Seguridad Operador
        self.operator_safety_frames_spin = QSpinBox()
        self.operator_safety_frames_spin.setRange(1, 900)
        self.operator_safety_frames_spin.setValue(self.config.get("operator_safety_frames", 30))
        self.operator_safety_frames_spin.setSuffix(" frames")
        plc_layout.addRow("Frames de seguridad Operador (espera):", self.operator_safety_frames_spin)

        layout.addWidget(plc_group)

        # Direcciones PLC
        addr_group = QGroupBox("📍 Direcciones de Registros")
        addr_layout = QFormLayout(addr_group)

        self.plc_reg_addr_1 = QSpinBox()
        self.plc_reg_addr_1.setRange(1, 65535)
        addr_layout.addRow("Cruzamiento:", self.plc_reg_addr_1)

        self.plc_reg_addr_2 = QSpinBox()
        self.plc_reg_addr_2.setRange(1, 65535)
        addr_layout.addRow("CruzyMnt:", self.plc_reg_addr_2)

        self.plc_reg_addr_3 = QSpinBox()
        self.plc_reg_addr_3.setRange(1, 65535)
        addr_layout.addRow("Montada:", self.plc_reg_addr_3)

        self.plc_reg_addr_operador = QSpinBox()
        self.plc_reg_addr_operador.setRange(1, 65535)
        addr_layout.addRow("Operador:", self.plc_reg_addr_operador)

        self.plc_reg_addr_pieza_quebrada = QSpinBox()
        self.plc_reg_addr_pieza_quebrada.setRange(1, 65535)
        addr_layout.addRow("Pieza Quebrada:", self.plc_reg_addr_pieza_quebrada)

        self.plc_reg_addr_alaveo = QSpinBox()
        self.plc_reg_addr_alaveo.setRange(1, 65535)
        addr_layout.addRow("Alaveo:", self.plc_reg_addr_alaveo)

        self.plc_reg_addr_pieza = QSpinBox()
        self.plc_reg_addr_pieza.setRange(1, 65535)
        addr_layout.addRow("Pieza (Estándar):", self.plc_reg_addr_pieza)

        layout.addWidget(addr_group)

        # Activación por clase
        enable_group = QGroupBox("✅ Activación por Clase")
        enable_layout = QFormLayout(enable_group)

        self.plc_enable_cruzamiento = QCheckBox("Activar para Cruzamiento")
        enable_layout.addRow(self.plc_enable_cruzamiento)

        self.plc_enable_cruzymnt = QCheckBox("Activar para CruzyMnt")
        enable_layout.addRow(self.plc_enable_cruzymnt)

        self.plc_enable_montada = QCheckBox("Activar para Montada")
        enable_layout.addRow(self.plc_enable_montada)

        self.plc_enable_operador = QCheckBox("Activar para Operador")
        enable_layout.addRow(self.plc_enable_operador)

        self.alertar_pieza_quebrada = QCheckBox("Alertar Pieza Quebrada")
        enable_layout.addRow(self.alertar_pieza_quebrada)

        self.plc_enable_alaveo = QCheckBox("Activar para Alaveo")
        enable_layout.addRow(self.plc_enable_alaveo)

        self.plc_enable_pieza = QCheckBox("Activar para Pieza")
        enable_layout.addRow(self.plc_enable_pieza)

        layout.addWidget(enable_group)

        # Config pulsos
        pulse_group = QGroupBox("⚡ Configuración de Pulsos")
        pulse_layout = QFormLayout(pulse_group)

        self.plc_reg_pulse_value = QSpinBox()
        self.plc_reg_pulse_value.setRange(0, 65535)
        pulse_layout.addRow("Valor del pulso:", self.plc_reg_pulse_value)

        self.plc_pulse_ms = QSpinBox()
        self.plc_pulse_ms.setRange(50, 5000)
        self.plc_pulse_ms.setSuffix(" ms")
        pulse_layout.addRow("Duración del pulso:", self.plc_pulse_ms)

        self.plc_cooldown_s = QDoubleSpinBox()
        self.plc_cooldown_s.setRange(0.1, 10.0)
        self.plc_cooldown_s.setSingleStep(0.1)
        self.plc_cooldown_s.setSuffix(" s")
        pulse_layout.addRow("Tiempo de enfriamiento:", self.plc_cooldown_s)

        layout.addWidget(pulse_group)

        # Botones de test
        test_group = QGroupBox("🧪 Pruebas de Conectividad y Señales")
        test_layout = QFormLayout(test_group)

        self.btn_test_connection = QPushButton("🔌 Test Conectividad PLC")
        self.btn_test_connection.clicked.connect(self.test_plc_connection)
        test_layout.addRow("", self.btn_test_connection)

        self.btn_test_signals = QPushButton("📡 Test Envío de Señales")
        self.btn_test_signals.clicked.connect(self.test_plc_signals)
        test_layout.addRow("", self.btn_test_signals)

        layout.addWidget(test_group)
        layout.addStretch()

        self.tab_widget.addTab(scroll, "🏭 PLC")

    # ------------------------------------------------------------------ #
    # Pestaña: Medición
    # ------------------------------------------------------------------ #
    def create_measurement_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # General
        general_group = QGroupBox("📏 Configuración General")
        general_layout = QFormLayout(general_group)

        self.medicion_enabled = QCheckBox("Habilitar sistema de medición")
        general_layout.addRow(self.medicion_enabled)

        self.medicion_units = QComboBox()
        self.medicion_units.addItems(["mm", "cm", "m"])
        general_layout.addRow("Unidades:", self.medicion_units)

        self.mostrar_medidas_overlay = QCheckBox("Mostrar medidas en video")
        general_layout.addRow(self.mostrar_medidas_overlay)

        self.log_mediciones = QCheckBox("Guardar log de mediciones")
        general_layout.addRow(self.log_mediciones)

        layout.addWidget(general_group)

        # Calibración
        cal_group = QGroupBox("📐 Calibración")
        cal_layout = QFormLayout(cal_group)

        self.escala_px_por_mm_cam1 = QDoubleSpinBox()
        self.escala_px_por_mm_cam1.setRange(0.01, 100.0)
        self.escala_px_por_mm_cam1.setDecimals(3)
        self.escala_px_por_mm_cam1.setSingleStep(0.1)
        cal_layout.addRow("Píxeles por mm (Cam 1):", self.escala_px_por_mm_cam1)

        layout.addWidget(cal_group)

        # Piezas quebradas
        broken_group = QGroupBox("🔧 Detección de Piezas Quebradas")
        broken_layout = QFormLayout(broken_group)

        self.detectar_piezas_quebradas = QCheckBox("Detectar piezas quebradas")
        broken_layout.addRow(self.detectar_piezas_quebradas)

        self.largo_minimo_pieza_mm = QDoubleSpinBox()
        self.largo_minimo_pieza_mm.setRange(1.0, 1000.0)
        self.largo_minimo_pieza_mm.setSuffix(" mm")
        broken_layout.addRow("Largo mínimo pieza:", self.largo_minimo_pieza_mm)

        self.min_fragmentos_quebrada = QSpinBox()
        self.min_fragmentos_quebrada.setRange(2, 10)
        broken_layout.addRow("Mín. fragmentos quebrada:", self.min_fragmentos_quebrada)

        layout.addWidget(broken_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "📏 Medición")

    # ------------------------------------------------------------------ #
    # Pestaña: Alertas
    # ------------------------------------------------------------------ #
    def create_alerts_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        alert_group = QGroupBox("🚨 Alertas de Operador")
        alert_layout = QFormLayout(alert_group)

        self.operador_alert_enabled = QCheckBox("Habilitar alertas de operador")
        alert_layout.addRow(self.operador_alert_enabled)

        self.operador_alert_blink = QCheckBox("Parpadeo de alertas")
        alert_layout.addRow(self.operador_alert_blink)

        color_layout = QHBoxLayout()
        self.operador_alert_color = QLineEdit()
        self.operador_alert_color.setReadOnly(True)
        self.color_btn = QPushButton("🎨 Seleccionar")
        self.color_btn.clicked.connect(self.select_alert_color)
        color_layout.addWidget(self.operador_alert_color)
        color_layout.addWidget(self.color_btn)
        alert_layout.addRow("Color de alerta:", color_layout)

        layout.addWidget(alert_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "🚨 Alertas")

    # ------------------------------------------------------------------ #
    # Pestaña: Avanzado
    # ------------------------------------------------------------------ #
    def create_advanced_tab(self) -> None:
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(tab)
        scroll.setWidgetResizable(True)

        layout = QVBoxLayout(tab)

        # Grabación automática
        recording_group = QGroupBox("📹 Grabación Automática")
        recording_layout = QFormLayout(recording_group)

        self.auto_recording_enabled = QCheckBox(
            "Habilitar grabación automática al detectar"
        )
        recording_layout.addRow(self.auto_recording_enabled)

        self.auto_record_duration_s = QDoubleSpinBox()
        self.auto_record_duration_s.setRange(1.0, 300.0)
        self.auto_record_duration_s.setSingleStep(1.0)
        self.auto_record_duration_s.setSuffix(" segundos")
        recording_layout.addRow("Duración de grabación:", self.auto_record_duration_s)

        self.save_detection_images = QCheckBox("Guardar imágenes de detecciones")
        recording_layout.addRow(self.save_detection_images)

        layout.addWidget(recording_group)

        # Tracking
        tracking_group = QGroupBox(
            "🎯 Seguimiento de Objetos (Tracker - Siempre Activo)"
        )
        tracking_layout = QFormLayout(tracking_group)

        info_label = QLabel(
            "El seguimiento de objetos está siempre habilitado "
            "para mejor rendimiento y robustez."
        )
        info_label.setStyleSheet(
            "color: #0066cc; font-style: italic; margin: 5px;"
        )
        tracking_layout.addRow(info_label)

        self.tracking_frame_rate = QSpinBox()
        self.tracking_frame_rate.setRange(1, 60)
        self.tracking_frame_rate.setSuffix(" FPS")
        tracking_layout.addRow("Frame rate (FPS):", self.tracking_frame_rate)

        self.tracking_track_thresh = QDoubleSpinBox()
        self.tracking_track_thresh.setRange(0.1, 1.0)
        self.tracking_track_thresh.setSingleStep(0.05)
        self.tracking_track_thresh.setDecimals(2)
        tracking_layout.addRow("Umbral de tracking:", self.tracking_track_thresh)

        self.tracking_high_thresh = QDoubleSpinBox()
        self.tracking_high_thresh.setRange(0.1, 1.0)
        self.tracking_high_thresh.setSingleStep(0.05)
        self.tracking_high_thresh.setDecimals(2)
        tracking_layout.addRow("Umbral alto de tracking:", self.tracking_high_thresh)

        self.tracking_match_thresh = QDoubleSpinBox()
        self.tracking_match_thresh.setRange(0.1, 1.0)
        self.tracking_match_thresh.setSingleStep(0.05)
        self.tracking_match_thresh.setDecimals(2)
        tracking_layout.addRow("Umbral IoU matching:", self.tracking_match_thresh)

        self.tracking_track_buffer = QSpinBox()
        self.tracking_track_buffer.setRange(10, 100)
        self.tracking_track_buffer.setSuffix(" frames")
        tracking_layout.addRow("Buffer para tracks perdidos:", self.tracking_track_buffer)

        layout.addWidget(tracking_group)
        layout.addStretch()

        self.tab_widget.addTab(scroll, "⚙️ Avanzado")

    # ------------------------------------------------------------------ #
    # Cargar valores desde self.config
    # ------------------------------------------------------------------ #
    def load_config_values(self) -> None:
        c = self.config

        # Cámara 1
        self.cam1_tipo.setCurrentText(c.get("cam1_tipo", "ip"))
        self.cam1_ip.setText(c.get("cam_ip", ""))
        self.cam1_webcam_idx.setValue(int(c.get("cam1_webcam_idx", 0)))
        self.cam1_archivo.setText(c.get("cam1_archivo", ""))

        self.cam_user.setText(c.get("cam_user", ""))
        self.cam_pass.setText(c.get("cam_pass", ""))
        self.cam_port.setValue(int(c.get("cam_port", 554)))
        self.connection_type.setCurrentText(c.get("connection_type", "RTSP"))
        self.http_port.setValue(int(c.get("http_port", 80)))
        self.channel.setText(c.get("channel", "101"))

        self.on_cam1_type_changed(self.cam1_tipo.currentText())
        self.update_connection_warning(self.connection_type.currentText())

        # Modelo
        self.model_path.setText(c.get("model_path", ""))
        self.min_confidence.setValue(float(c.get("min_confidence", 0.5)))

        # ROI
        self.roi_scale_1.setValue(float(c.get("roi_scale_1", 0.5)))
        self.roi_offset_x_1.setValue(float(c.get("roi_offset_x_1", 0.0)))

        # PLC
        self.plc_enabled.setChecked(bool(c.get("plc_enabled", False)))
        self.plc_ip.setText(c.get("plc_ip", "192.168.10.50"))
        self.plc_port.setValue(c.get("plc_port", 502))
        self.plc_unit_id.setValue(c.get("plc_unit_id", 1))
        self.umbral_movimiento_spin.setValue(c.get("umbral_movimiento", 5))
        self.reenganche_spin.setValue(c.get("plc_reenganche_param", 10))
        self.operator_safety_frames_spin.setValue(c.get("operator_safety_frames", 30))

        self.plc_reg_addr_1.setValue(int(c.get("plc_reg_addr_1", 22001)))
        self.plc_reg_addr_2.setValue(int(c.get("plc_reg_addr_2", 22002)))
        self.plc_reg_addr_3.setValue(int(c.get("plc_reg_addr_3", 22003)))
        self.plc_reg_addr_operador.setValue(
            int(c.get("plc_reg_addr_operador", 22004))
        )
        self.plc_reg_addr_pieza_quebrada.setValue(
            int(c.get("plc_reg_addr_pieza_quebrada", 22005))
        )
        self.plc_reg_addr_alaveo.setValue(int(c.get("plc_reg_addr_alaveo", 22006)))
        self.plc_reg_addr_pieza.setValue(int(c.get("plc_reg_addr_pieza", 22007)))

        self.plc_enable_cruzamiento.setChecked(
            bool(c.get("plc_enable_cruzamiento", True))
        )
        self.plc_enable_cruzymnt.setChecked(bool(c.get("plc_enable_cruzymnt", True)))
        self.plc_enable_montada.setChecked(bool(c.get("plc_enable_montada", False)))
        self.plc_enable_operador.setChecked(bool(c.get("plc_enable_operador", True)))
        self.alertar_pieza_quebrada.setChecked(
            bool(c.get("alertar_pieza_quebrada", True))
        )
        self.plc_enable_alaveo.setChecked(bool(c.get("plc_enable_alaveo", False)))
        self.plc_enable_pieza.setChecked(bool(c.get("plc_enable_pieza", False)))

        self.plc_reg_pulse_value.setValue(int(c.get("plc_reg_pulse_value", 1)))
        self.plc_pulse_ms.setValue(int(c.get("plc_pulse_ms", 300)))
        self.plc_cooldown_s.setValue(float(c.get("plc_cooldown_s", 1.0)))

        # Medición
        self.medicion_enabled.setChecked(bool(c.get("medicion_enabled", True)))
        self.medicion_units.setCurrentText(c.get("medicion_units", "mm"))
        self.escala_px_por_mm_cam1.setValue(
            float(c.get("escala_px_por_mm_cam1", 1.0))
        )
        self.mostrar_medidas_overlay.setChecked(
            bool(c.get("mostrar_medidas_overlay", True))
        )
        self.log_mediciones.setChecked(bool(c.get("log_mediciones", True)))
        self.detectar_piezas_quebradas.setChecked(
            bool(c.get("detectar_piezas_quebradas", True))
        )
        self.largo_minimo_pieza_mm.setValue(
            float(c.get("largo_minimo_pieza_mm", 50.0))
        )
        self.min_fragmentos_quebrada.setValue(int(c.get("min_fragmentos_quebrada", 2)))

        # Alertas
        self.operador_alert_enabled.setChecked(
            bool(c.get("operador_alert_enabled", True))
        )
        self.operador_alert_blink.setChecked(
            bool(c.get("operador_alert_blink", True))
        )
        color = c.get("operador_alert_color", "#FF0000")
        self.operador_alert_color.setText(color)
        self.operador_alert_color.setStyleSheet(f"background-color: {color};")

        # Avanzado
        self.auto_recording_enabled.setChecked(
            bool(c.get("auto_recording_enabled", False))
        )
        self.auto_record_duration_s.setValue(
            float(c.get("auto_record_duration_s", 10.0))
        )
        self.save_detection_images.setChecked(
            bool(c.get("save_detection_images", True))
        )

        self.tracking_frame_rate.setValue(int(c.get("tracking_frame_rate", 30)))
        self.tracking_track_thresh.setValue(
            float(c.get("tracking_track_thresh", 0.3))
        )
        self.tracking_high_thresh.setValue(float(c.get("tracking_high_thresh", 0.5)))
        self.tracking_match_thresh.setValue(
            float(c.get("tracking_match_thresh", 0.7))
        )
        self.tracking_track_buffer.setValue(
            int(c.get("tracking_track_buffer", 60))
        )

    # ------------------------------------------------------------------ #
    # Guardar configuración desde los widgets a JSON
    # ------------------------------------------------------------------ #
    def save_config(self) -> None:
        """Lee la UI, actualiza self.config y guarda el JSON."""
        c = self.config

        # Cámara 1
        c["cam1_tipo"] = self.cam1_tipo.currentText()
        c["cam_ip"] = self.cam1_ip.text().strip()
        c["cam1_webcam_idx"] = int(self.cam1_webcam_idx.value())
        c["cam1_archivo"] = self.cam1_archivo.text().strip()

        c["cam_user"] = self.cam_user.text().strip()
        c["cam_pass"] = self.cam_pass.text()
        c["cam_port"] = int(self.cam_port.value())
        c["cam_port"] = int(self.cam_port.value())
        c["connection_type"] = self.connection_type.currentText()
        # Asegurar compatibilidad con CameraHandler que espera "cam1_conexion"
        c["cam1_conexion"] = self.connection_type.currentText()
        
        c["http_port"] = int(self.http_port.value())
        c["channel"] = self.channel.text().strip()

        # Modelo
        c["model_path"] = self.model_path.text().strip()
        c["min_confidence"] = float(self.min_confidence.value())

        # ROI
        c["roi_scale_1"] = float(self.roi_scale_1.value())
        c["roi_offset_x_1"] = float(self.roi_offset_x_1.value())

        # PLC
        c["plc_enabled"] = bool(self.plc_enabled.isChecked())
        c["plc_ip"] = self.plc_ip.text().strip()
        c["plc_port"] = int(self.plc_port.value())
        c["plc_unit_id"] = self.plc_unit_id.value()
        c["umbral_movimiento"] = self.umbral_movimiento_spin.value()
        c["plc_reenganche_param"] = self.reenganche_spin.value()
        c["operator_safety_frames"] = self.operator_safety_frames_spin.value()

        c["plc_reg_addr_1"] = int(self.plc_reg_addr_1.value())
        c["plc_reg_addr_2"] = int(self.plc_reg_addr_2.value())
        c["plc_reg_addr_3"] = int(self.plc_reg_addr_3.value())
        c["plc_reg_addr_operador"] = int(self.plc_reg_addr_operador.value())
        c["plc_reg_addr_pieza_quebrada"] = int(
            self.plc_reg_addr_pieza_quebrada.value()
        )
        c["plc_reg_addr_alaveo"] = int(self.plc_reg_addr_alaveo.value())
        c["plc_reg_addr_pieza"] = int(self.plc_reg_addr_pieza.value())

        c["plc_enable_cruzamiento"] = bool(self.plc_enable_cruzamiento.isChecked())
        c["plc_enable_cruzymnt"] = bool(self.plc_enable_cruzymnt.isChecked())
        c["plc_enable_montada"] = bool(self.plc_enable_montada.isChecked())
        c["plc_enable_operador"] = bool(self.plc_enable_operador.isChecked())
        c["alertar_pieza_quebrada"] = bool(
            self.alertar_pieza_quebrada.isChecked()
        )
        c["plc_enable_alaveo"] = bool(self.plc_enable_alaveo.isChecked())
        c["plc_enable_pieza"] = bool(self.plc_enable_pieza.isChecked())

        c["plc_reg_pulse_value"] = int(self.plc_reg_pulse_value.value())
        c["plc_pulse_ms"] = int(self.plc_pulse_ms.value())
        c["plc_cooldown_s"] = float(self.plc_cooldown_s.value())

        # Medición
        c["medicion_enabled"] = bool(self.medicion_enabled.isChecked())
        c["medicion_units"] = self.medicion_units.currentText()
        c["escala_px_por_mm_cam1"] = float(self.escala_px_por_mm_cam1.value())
        c["mostrar_medidas_overlay"] = bool(
            self.mostrar_medidas_overlay.isChecked()
        )
        c["log_mediciones"] = bool(self.log_mediciones.isChecked())
        c["detectar_piezas_quebradas"] = bool(
            self.detectar_piezas_quebradas.isChecked()
        )
        c["largo_minimo_pieza_mm"] = float(
            self.largo_minimo_pieza_mm.value()
        )
        c["min_fragmentos_quebrada"] = int(
            self.min_fragmentos_quebrada.value()
        )

        # Alertas
        c["operador_alert_enabled"] = bool(
            self.operador_alert_enabled.isChecked()
        )
        c["operador_alert_blink"] = bool(self.operador_alert_blink.isChecked())
        c["operador_alert_color"] = self.operador_alert_color.text().strip() or "#FF0000"

        # Avanzado
        c["auto_recording_enabled"] = bool(
            self.auto_recording_enabled.isChecked()
        )
        c["auto_record_duration_s"] = float(
            self.auto_record_duration_s.value()
        )
        c["save_detection_images"] = bool(
            self.save_detection_images.isChecked()
        )

        c["tracking_frame_rate"] = int(self.tracking_frame_rate.value())
        c["tracking_track_thresh"] = float(
            self.tracking_track_thresh.value()
        )
        c["tracking_high_thresh"] = float(self.tracking_high_thresh.value())
        c["tracking_match_thresh"] = float(
            self.tracking_match_thresh.value()
        )
        c["tracking_track_buffer"] = int(self.tracking_track_buffer.value())

        # Guardar en disco
        # Guardar en disco
        try:
            self._save_json_config(CONFIG_FILE)
            QMessageBox.information(
                self, "Configuración", "¡Configuración guardada correctamente!"
            )
            self.config_changed.emit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo guardar la configuración:\n{e}",
            )

    # ------------------------------------------------------------------ #
    # Selectores de archivo / color
    # ------------------------------------------------------------------ #
    def select_video_file(self, line_edit: QLineEdit) -> None:
        """Selecciona un archivo de video para cámara."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo de video",
            "",
            "Videos (*.mp4 *.avi *.mov *.mkv *.wmv);;Todos los archivos (*.*)",
        )
        if file_path:
            line_edit.setText(file_path)

    def select_model_file(self) -> None:
        """Selecciona el archivo del modelo YOLO."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar modelo YOLO",
            "",
            "Modelos YOLO (*.pt *.onnx);;Todos los archivos (*.*)",
        )
        if file_path:
            self.model_path.setText(file_path)

    def select_alert_color(self) -> None:
        """Selecciona el color de alerta."""
        current_color = QColor(self.operador_alert_color.text() or "#FF0000")
        color = QColorDialog.getColor(current_color, self, "Seleccionar color de alerta")
        if color.isValid():
            self.operador_alert_color.setText(color.name())
            self.operador_alert_color.setStyleSheet(
                f"background-color: {color.name()};"
            )

    # ------------------------------------------------------------------ #
    # Ayuda
    # ------------------------------------------------------------------ #
    def show_help(self) -> None:
        """Muestra la ayuda de configuración."""
        help_text = """
<h2>🏭 Sistema de Detección de Cruzamiento</h2>
<h3>📋 Guía de Configuración</h3>

<h4>📹 <b>CÁMARAS</b></h4>
<ul>
<li><b>IP:</b> Cámara IP con RTSP/HTTP</li>
<li><b>Webcam:</b> Cámara USB (índice 0, 1, 2...)</li>
<li><b>Archivo:</b> Video grabado para pruebas</li>
</ul>

<h4>🤖 <b>MODELO IA</b></h4>
<ul>
<li>Ruta del modelo YOLO (.pt, .onnx)</li>
<li>Confianza mínima para detecciones válidas</li>
</ul>

<h4>🔲 <b>ROI</b></h4>
<ul>
<li><b>Escala:</b> tamaño horizontal del área de análisis</li>
<li><b>Offset X:</b> desplazamiento horizontal del ROI</li>
</ul>

<h4>🏭 <b>PLC</b></h4>
<ul>
<li>Comunicación Modbus TCP</li>
<li>Configurar IP, puerto, Unit ID y registros</li>
<li>Activar por tipo de detección</li>
</ul>

<h4>📏 <b>MEDICIÓN</b></h4>
<ul>
<li>Calibración (pixeles → mm)</li>
<li>Detección de piezas quebradas</li>
</ul>

<h4>🚨 <b>ALERTAS</b></h4>
<ul>
<li>Alertas visuales, color y parpadeo configurables</li>
</ul>

<h4>⚙️ <b>AVANZADO</b></h4>
<ul>
<li>Grabación automática ante detección</li>
<li>Parámetros del tracker de objetos</li>
</ul>
"""
        msg = QMessageBox(self)
        msg.setWindowTitle("❓ Ayuda de Configuración")
        msg.setTextFormat(Qt.RichText)
        msg.setText(help_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    # ------------------------------------------------------------------ #
    # Tests PLC (sin unit/slave/device_id para tu versión de pymodbus)
    # ------------------------------------------------------------------ #
    def test_plc_connection(self) -> None:
        """Prueba solo la conectividad con el PLC sin enviar pulsos."""
        try:
            from pymodbus.client import ModbusTcpClient
            import socket

            ip = self.plc_ip.text().strip()
            port = int(self.plc_port.value())
            unit = int(self.plc_unit_id.value())  # Solo informativo

            if not ip:
                QMessageBox.warning(
                    self, "Test PLC", "Por favor, ingrese la IP del PLC."
                )
                return

            # Test de socket básico
            print(f"🔍 Probando conectividad a {ip}:{port}")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            try:
                result = sock.connect_ex((ip, port))
            finally:
                sock.close()

            if result != 0:
                QMessageBox.warning(
                    self,
                    "PLC Conectividad",
                    (
                        f"❌ No se puede alcanzar {ip}:{port}\n\n"
                        "Verificar:\n"
                        f"• IP del PLC: {ip}\n"
                        f"• Puerto: {port}\n"
                        "• Conexión de red\n"
                        "• Firewall"
                    ),
                )
                return

            print(f"✅ Puerto {port} alcanzable en {ip}")

            # Conexión Modbus (tu versión NO acepta unit_id aquí)
            client = ModbusTcpClient(
                host=ip,
                port=port,
                timeout=3.0,
            )

            if client.connect():
                try:
                    # Sin unit/slave/device_id
                    response = client.read_holding_registers(0)
                    if response.isError():
                        status = (
                            "⚠️ Conectado pero error en lectura de registros "
                            f"({response})"
                        )
                        print(f"⚠️ Error al leer registro: {response}")
                    else:
                        status = (
                            "✅ Conexión Modbus exitosa y registros accesibles "
                            f"(reg0={response.registers})"
                        )
                        print(f"✅ Lectura exitosa de registro 0: {response.registers}")
                except Exception as e:
                    status = f"⚠️ Conectado pero error en test de registro: {e}"
                    print(f"⚠️ Error en test de registro: {e}")
                finally:
                    client.close()

                QMessageBox.information(
                    self,
                    "PLC Conectividad",
                    (
                        f"{status}\n\n"
                        "Configuración:\n"
                        f"• IP: {ip}\n"
                        f"• Puerto: {port}\n"
                        f"• Unit ID (referencial): {unit}"
                    ),
                )
            else:
                QMessageBox.warning(
                    self,
                    "PLC Conectividad",
                    (
                        f"❌ No se puede conectar por Modbus a {ip}:{port}\n\n"
                        "Verificar:\n"
                        "• PLC encendido y con Modbus TCP habilitado\n"
                        f"• Unit ID correcto: {unit}\n"
                        "• Configuración de red del PLC"
                    ),
                )
                print(f"❌ Fallo en conexión Modbus a {ip}:{port}")

        except ImportError:
            QMessageBox.critical(
                self,
                "PLC Conectividad",
                "❌ Librería pymodbus no instalada.\nInstalar con: pip install pymodbus",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "PLC Conectividad",
                f"❌ Error inesperado:\n{e}",
            )
            print(f"❌ Error en test de conectividad: {e}")

    def test_plc_signals(self) -> None:
        """Prueba el envío de señales al PLC."""
        try:
            from pymodbus.client import ModbusTcpClient
            import time

            ip = self.plc_ip.text().strip()
            port = int(self.plc_port.value())
            unit = int(self.plc_unit_id.value())  # Solo informativo
            pulse_ms = int(self.plc_pulse_ms.value())

            if not ip:
                QMessageBox.warning(
                    self, "Test PLC", "Por favor, ingrese la IP del PLC."
                )
                return

            client = ModbusTcpClient(
                host=ip,
                port=port,
                timeout=2.0,
            )

            if not client.connect():
                QMessageBox.warning(
                    self,
                    "Test Señales PLC",
                    (
                        "❌ No conecta a PLC.\n\n"
                        f"IP: {ip}:{port}\n"
                        "Use 'Test Conectividad PLC' para diagnóstico."
                    ),
                )
                return

            print(f"🔌 Conectado a PLC {ip}:{port} - Enviando pulsos de prueba...")

            tests_realizados = []
            val = 1

            available_tests = [
                ("Cruzamiento", self.plc_reg_addr_1, self.plc_enable_cruzamiento),
                ("CruzyMont", self.plc_reg_addr_2, self.plc_enable_cruzymnt),
                ("Montada", self.plc_reg_addr_3, self.plc_enable_montada),
                ("Operador", self.plc_reg_addr_operador, self.plc_enable_operador),
                (
                    "Pieza Quebrada",
                    self.plc_reg_addr_pieza_quebrada,
                    self.alertar_pieza_quebrada,
                ),
                ("Alaveo", self.plc_reg_addr_alaveo, self.plc_enable_alaveo),
                ("Pieza", self.plc_reg_addr_pieza, self.plc_enable_pieza),
            ]

            for signal_name, reg_widget, enable_widget in available_tests:
                if not enable_widget.isChecked():
                    tests_realizados.append(
                        f"{signal_name} - OMITIDO (deshabilitado)"
                    )
                    print(f"⏭️ {signal_name} omitido (checkbox deshabilitado)")
                    continue

                addr = int(reg_widget.value())
                try:
                    client.write_register(addr, val)
                    time.sleep(max(0.01, pulse_ms / 1000.0))
                    client.write_register(addr, 0)
                    tests_realizados.append(f"{signal_name} (reg {addr})")
                    print(f"✅ Test {signal_name} enviado a registro {addr}")
                except Exception as e:
                    tests_realizados.append(
                        f"{signal_name} (reg {addr}) - ERROR: {e}"
                    )
                    print(f"❌ Error en test {signal_name}: {e}")

            client.close()

            if tests_realizados:
                mensaje_tests = "\n".join(f"• {t}" for t in tests_realizados)
                QMessageBox.information(
                    self,
                    "Test Señales PLC Completado",
                    (
                        f"✅ Pulsos de prueba enviados:\n\n{mensaje_tests}\n\n"
                        "⚙️ Configuración utilizada:\n"
                        f"• Valor del pulso: {val}\n"
                        f"• Duración: {pulse_ms}ms\n"
                        f"• Unit ID (referencial): {unit}"
                    ),
                )
            else:
                QMessageBox.warning(
                    self,
                    "Test Señales PLC",
                    (
                        "⚠️ No se realizaron pruebas.\n\n"
                        "Motivo: Ninguna señal está habilitada.\n"
                        "Marque al menos un checkbox en la configuración PLC "
                        "antes de ejecutar el test."
                    ),
                )

        except ImportError:
            QMessageBox.critical(
                self,
                "Test Señales PLC",
                "❌ Librería pymodbus no instalada.\nInstalar con: pip install pymodbus",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Test Señales PLC",
                f"❌ Error en prueba: {e}",
            )
            print(f"❌ Error en test de señales: {e}")


class InteractiveROIDialog(QDialog):
    """Diálogo para definir ROI interactivamente sobre una imagen."""
    def __init__(self, frame, current_points=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Definir ROI Interactivamente")
        self.resize(1000, 800)
        
        # Copia del frame para dibujar
        self.original_frame = frame.copy()
        self.h, self.w = frame.shape[:2]
        self.points = list(current_points) if current_points else []
        self.max_points = 4
        
        layout = QVBoxLayout(self)
        
        # Instrucciones
        info_lbl = QLabel(
            "📍 INSTRUCCIONES:\n"
            "1. Haga clic en la imagen para marcar los 4 puntos del área de interés.\n"
            "2. Trate de marcar los puntos en orden (ej: horario).\n"
            "3. Presione 'Guardar ROI' cuando termine."
        )
        info_lbl.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(info_lbl)
        
        # Area de desplazamiento para la imagen (por si es grande)
        self.scroll = QScrollArea()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMouseTracking(False)
        self.image_label.mousePressEvent = self.on_image_click
        self.scroll.setWidget(self.image_label)
        self.scroll.setWidgetResizable(True) # Permitir que el label determine el tamaño
        layout.addWidget(self.scroll)
        
        # Botones
        btn_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("🔄 Reiniciar Puntos")
        self.reset_btn.clicked.connect(self.reset_points)
        self.reset_btn.setStyleSheet("background-color: #f39c12; color: white;")
        
        self.ok_btn = QPushButton("💾 Guardar ROI")
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setEnabled(False)
        self.ok_btn.setStyleSheet("background-color: #27ae60; color: white;")
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.update_display()
        
    def on_image_click(self, event):
        if len(self.points) >= self.max_points:
            return
        
        # Obtener coordenadas relativas al label
        x = event.pos().x()
        y = event.pos().y()
        
        # Asegurar límites por si acaso
        x = max(0, min(x, self.w - 1))
        y = max(0, min(y, self.h - 1))
        
        self.points.append([x, y])
        self.update_display()
        
        # Habilitar guardar si tenemos al menos 3 puntos (triángulo o más)
        if len(self.points) >= 3:
             self.ok_btn.setEnabled(True)

    def reset_points(self):
        self.points = []
        self.ok_btn.setEnabled(False)
        self.update_display()
        
    def update_display(self):
        # Dibujar sobre una copia del frame original
        disp_img = self.original_frame.copy()
        
        # Dibujar puntos y líneas
        pts = np.array(self.points, np.int32)
        if len(pts) > 0:
            # Dibujar puntos (círculos rojos)
            for pt in pts:
                cv2.circle(disp_img, tuple(pt), 6, (0, 0, 255), -1)
                cv2.circle(disp_img, tuple(pt), 8, (255, 255, 255), 1)
            
            # Dibujar polígono/líneas (verde)
            if len(pts) > 1:
                is_closed = (len(pts) == self.max_points)
                
                # Dibujar linea "segmentada" (Manual simple)
                color = (0, 255, 0)
                thickness = 2
                
                # Dibujar segmentos
                for i in range(len(pts) - 1):
                    self.draw_dashed_line(disp_img, tuple(pts[i]), tuple(pts[i+1]), color, thickness)
                
                if is_closed:
                    self.draw_dashed_line(disp_img, tuple(pts[-1]), tuple(pts[0]), color, thickness)
        
        # Convertir a QPixmap para mostrar en Qt
        rgb_image = cv2.cvtColor(disp_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(q_img))
        self.image_label.resize(w, h)

    def draw_dashed_line(self, img, pt1, pt2, color, thickness=1, gap=10):
        dist = np.linalg.norm(np.array(pt1) - np.array(pt2))
        dashes = int(dist / gap)
        for i in range(dashes):
            if i % 2 == 0:
                start = pt1 + (np.array(pt2) - np.array(pt1)) * (i / dashes)
                end = pt1 + (np.array(pt2) - np.array(pt1)) * ((i + 1) / dashes)
                cv2.line(img, tuple(start.astype(int)), tuple(end.astype(int)), color, thickness)
