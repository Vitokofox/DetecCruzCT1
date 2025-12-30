"""
Ventana de historial de detecciones.

Esta ventana muestra un historial detallado de todas las detecciones
realizadas por el sistema, incluyendo información de tracking, miniaturas,
mediciones y estadísticas.
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QPushButton, QScrollArea, QWidget, QFrame,
    QComboBox, QCheckBox, QSpinBox, QGroupBox, QSplitter,
    QTextEdit, QProgressBar, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer, Signal as pyqtSignal
from PySide6.QtGui import QPixmap, QFont, QPalette, QColor
import cv2
import numpy as np


class DetectionHistoryWindow(QDialog):
    """
    Ventana para mostrar el historial de detecciones con filtering y estadísticas.
    """
    
    def __init__(self, detection_handler, parent=None):
        super().__init__(parent)
        self.detection_handler = detection_handler
        
        self.setWindowTitle("📊 Historial de Detecciones")
        self.setModal(False)
        self.resize(1200, 800)
        
        self.setup_ui()
        self.setup_timer()
        self.load_detection_history()
        
    def get_saved_detections(self):
        """Obtiene las detecciones guardadas de la carpeta detecciones."""
        detections = []
        detecciones_dir = os.path.join(os.getcwd(), "detecciones")
        
        # Si estamos en un ejecutable, buscar en dist/detecciones
        if hasattr(sys, 'frozen'):
            exe_dir = os.path.dirname(sys.executable)
            detecciones_dir = os.path.join(exe_dir, "detecciones")
        
        if not os.path.exists(detecciones_dir):
            return detections
        
        # Buscar archivos de imagen
        for filename in os.listdir(detecciones_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                filepath = os.path.join(detecciones_dir, filename)
                
                # Buscar archivo de metadata correspondiente
                metadata_filename = filename.replace('.jpg', '_metadata.json')
                metadata_filepath = os.path.join(detecciones_dir, metadata_filename)
                
                # Extraer información del nombre del archivo
                # Formato: deteccion_cam1_20251021_090005.jpg
                parts = filename.replace('.jpg', '').split('_')
                
                if len(parts) >= 4:
                    try:
                        cam_id = parts[1].replace('cam', '')
                        date_str = parts[2]
                        time_str = parts[3]
                        
                        # Leer metadata si existe
                        label = 'Detección guardada'
                        confidence = 0.95
                        num_detections = 1
                        
                        if os.path.exists(metadata_filepath):
                            try:
                                import json
                                with open(metadata_filepath, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                                    label = metadata.get('main_class', 'Detección')
                                    confidence = metadata.get('main_confidence', 0.95)
                                    num_detections = metadata.get('num_detections', 1)
                            except Exception as e:
                                print(f"⚠️ Error leyendo metadata de {metadata_filename}: {e}")
                        
                        # Crear objeto de detección
                        detection_info = {
                            'id': len(detections) + 1,
                            'image_path': filepath,
                            'filename': filename,
                            'camera_id': int(cam_id),
                            'date': date_str,
                            'time': time_str,
                            'timestamp': f"{date_str}_{time_str}",
                            'label': label,
                            'confidence': confidence,
                            'num_detections': num_detections
                        }
                        detections.append(detection_info)
                    except (ValueError, IndexError):
                        continue
        
        # Ordenar por timestamp más reciente primero
        detections.sort(key=lambda x: x['timestamp'], reverse=True)
        return detections
        
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        
        # Panel de controles
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        
        # Filtros
        filter_group = QGroupBox("🔍 Filtros")
        filter_layout = QHBoxLayout(filter_group)
        
        filter_layout.addWidget(QLabel("Cámara:"))
        self.camera_filter = QComboBox()
        self.camera_filter.addItems(["Todas", "Cámara 1", "Cámara 2"])
        self.camera_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.camera_filter)
        
        filter_layout.addWidget(QLabel("Clase:"))
        self.class_filter = QComboBox()
        self.class_filter.addItem("Todas")
        self.class_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.class_filter)
        
        self.tracked_only = QCheckBox("Solo con tracking")
        self.tracked_only.stateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.tracked_only)
        
        self.broken_only = QCheckBox("Solo piezas quebradas")
        self.broken_only.stateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.broken_only)
        
        controls_layout.addWidget(filter_group)
        
        # Controles de actualización
        update_group = QGroupBox("🔄 Actualización")
        update_layout = QHBoxLayout(update_group)
        
        self.auto_refresh = QCheckBox("Auto-actualizar")
        self.auto_refresh.setChecked(True)
        self.auto_refresh.stateChanged.connect(self.toggle_auto_refresh)
        update_layout.addWidget(self.auto_refresh)
        
        self.refresh_btn = QPushButton("🔄 Actualizar Ahora")
        self.refresh_btn.clicked.connect(self.load_detection_history)
        update_layout.addWidget(self.refresh_btn)
        
        self.clear_btn = QPushButton("🗑️ Limpiar Historial")
        self.clear_btn.clicked.connect(self.clear_history)
        update_layout.addWidget(self.clear_btn)
        
        controls_layout.addWidget(update_group)
        
        controls_layout.addStretch()
        layout.addWidget(controls_frame)
        
        # Crear pestañas
        self.tab_widget = QTabWidget()
        
        # Pestaña de lista de detecciones
        self.create_detections_tab()
        
        # Pestaña de estadísticas
        self.create_statistics_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Botones de acción
        button_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("📤 Exportar Datos")
        self.export_btn.clicked.connect(self.export_data)
        button_layout.addWidget(self.export_btn)
        
        button_layout.addStretch()
        
        self.close_btn = QPushButton("❌ Cerrar")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
    def create_detections_tab(self):
        """Crea la pestaña de lista de detecciones."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Crear tabla de detecciones
        self.detections_table = QTableWidget()
        self.detections_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.detections_table.setAlternatingRowColors(True)
        
        # Configurar columnas - AGREGAR COLUMNA DE MINIATURA
        headers = [
            "📷", "ID", "Clase", "Tiempo", "Confianza", "Cámara", "Archivo"
        ]
        self.detections_table.setColumnCount(len(headers))
        self.detections_table.setHorizontalHeaderLabels(headers)
        
        # Configurar header con miniatura
        header = self.detections_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)        # Miniatura
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # ID
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Clase
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Tiempo
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # Confianza
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)        # Cámara
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)  # Archivo
        self.detections_table.setColumnWidth(0, 80)  # Miniatura
        self.detections_table.setColumnWidth(5, 60)  # Cámara
        
        # Set row height for thumbnails
        self.detections_table.verticalHeader().setDefaultSectionSize(70)
        
        layout.addWidget(self.detections_table)
        self.tab_widget.addTab(tab, "📋 Detecciones")
        
    def create_statistics_tab(self):
        """Crea la pestaña de estadísticas."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Scroll area para estadísticas
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Estadísticas generales
        general_group = QGroupBox("📊 Estadísticas Generales")
        general_layout = QGridLayout(general_group)
        
        self.total_detections_label = QLabel("0")
        self.total_detections_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2196F3;")
        general_layout.addWidget(QLabel("Total de detecciones:"), 0, 0)
        general_layout.addWidget(self.total_detections_label, 0, 1)
        
        self.tracked_objects_label = QLabel("0")
        self.tracked_objects_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        general_layout.addWidget(QLabel("Objetos trackeados:"), 1, 0)
        general_layout.addWidget(self.tracked_objects_label, 1, 1)
        
        self.broken_pieces_label = QLabel("0")
        self.broken_pieces_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #FF5722;")
        general_layout.addWidget(QLabel("Piezas quebradas:"), 2, 0)
        general_layout.addWidget(self.broken_pieces_label, 2, 1)
        
        scroll_layout.addWidget(general_group)
        
        # Estadísticas por cámara
        cam_group = QGroupBox("📹 Por Cámara")
        cam_layout = QGridLayout(cam_group)
        
        self.cam1_stats = QLabel("Cámara 1: 0 detecciones")
        self.cam2_stats = QLabel("Cámara 2: 0 detecciones")
        cam_layout.addWidget(self.cam1_stats, 0, 0)
        cam_layout.addWidget(self.cam2_stats, 1, 0)
        
        scroll_layout.addWidget(cam_group)
        
        # Estadísticas por clase
        class_group = QGroupBox("🏷️ Por Clase")
        class_layout = QVBoxLayout(class_group)
        
        self.class_stats_widget = QWidget()
        self.class_stats_layout = QVBoxLayout(self.class_stats_widget)
        class_layout.addWidget(self.class_stats_widget)
        
        scroll_layout.addWidget(class_group)
        
        # Estadísticas de tracking
        tracking_group = QGroupBox("🎯 Tracking")
        tracking_layout = QGridLayout(tracking_group)
        
        self.active_tracks_cam1 = QLabel("Activos Cam1: 0")
        self.active_tracks_cam2 = QLabel("Activos Cam2: 0")
        self.total_tracks = QLabel("Total tracks: 0")
        
        tracking_layout.addWidget(self.active_tracks_cam1, 0, 0)
        tracking_layout.addWidget(self.active_tracks_cam2, 0, 1)
        tracking_layout.addWidget(self.total_tracks, 1, 0, 1, 2)
        
        scroll_layout.addWidget(tracking_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        self.tab_widget.addTab(tab, "📊 Estadísticas")
        
    def setup_timer(self):
        """Configura el timer para auto-actualización."""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.load_detection_history)
        self.update_timer.start(5000)  # Actualizar cada 5 segundos
        
    def toggle_auto_refresh(self, state):
        """Activa/desactiva la auto-actualización."""
        if state == Qt.Checked:
            self.update_timer.start(5000)
        else:
            self.update_timer.stop()
            
    def load_detection_history(self):
        """Carga el historial de detecciones y consolida por ID único."""
        try:
            # Obtener historial de ambas cámaras
            history_cam1 = self.detection_handler.detection_history.get(1, [])
            history_cam2 = self.detection_handler.detection_history.get(2, [])
            
            # Crear diccionario consolidado por track_id
            consolidated_pieces = {}
            
            # Procesar detecciones de cámara 1
            for detection in history_cam1:
                track_id = detection.get('track_id', -1)
                label = detection.get('label', '').lower()
                
                # Filtrar solo piezas (excluir operador)
                if track_id != -1 and label == 'pieza':
                    if track_id not in consolidated_pieces:
                        # Obtener medidas corregidas (largo/ancho)
                        measurements = detection.get('measurements') or detection.get('initial_size')
                        processed_measurements = {}
                        if measurements:
                            # Priorizar campos específicos de largo/ancho
                            largo = measurements.get('largo', measurements.get('height', measurements.get('height_real', 0)))
                            ancho = measurements.get('ancho', measurements.get('width', measurements.get('width_real', 0)))
                            processed_measurements = {
                                'largo': largo,
                                'ancho': ancho,
                                'area': measurements.get('area', measurements.get('area_real', 0))
                            }
                        
                        consolidated_pieces[track_id] = {
                            'track_id': track_id,
                            'label': detection.get('label', 'Pieza'),
                            'measurements': processed_measurements,
                            'plc_triggered': detection.get('plc_triggered', False),
                            'cam1': 1,  # Detectado en cámara 1
                            'cam2': 0,  # No detectado en cámara 2 (por ahora)
                            'first_detection_time': detection.get('first_detection_time', detection.get('timestamp'))
                        }
                    else:
                        # Ya existe, solo marcar que también está en cam1
                        consolidated_pieces[track_id]['cam1'] = 1
            
            # Procesar detecciones de cámara 2
            for detection in history_cam2:
                track_id = detection.get('track_id', -1)
                label = detection.get('label', '').lower()
                
                # Filtrar solo piezas (excluir operador)
                if track_id != -1 and label == 'pieza':
                    if track_id not in consolidated_pieces:
                        # Obtener medidas corregidas (largo/ancho)
                        measurements = detection.get('measurements') or detection.get('initial_size')
                        processed_measurements = {}
                        if measurements:
                            # Priorizar campos específicos de largo/ancho
                            largo = measurements.get('largo', measurements.get('height', measurements.get('height_real', 0)))
                            ancho = measurements.get('ancho', measurements.get('width', measurements.get('width_real', 0)))
                            processed_measurements = {
                                'largo': largo,
                                'ancho': ancho,
                                'area': measurements.get('area', measurements.get('area_real', 0))
                            }
                        
                        consolidated_pieces[track_id] = {
                            'track_id': track_id,
                            'label': detection.get('label', 'Pieza'),
                            'measurements': processed_measurements,
                            'plc_triggered': detection.get('plc_triggered', False),
                            'cam1': 0,  # No detectado en cámara 1
                            'cam2': 1,  # Detectado en cámara 2
                            'first_detection_time': detection.get('first_detection_time', detection.get('timestamp'))
                        }
                    else:
                        # Ya existe, marcar que también está en cam2
                        consolidated_pieces[track_id]['cam2'] = 1
                        # Actualizar PLC si fue disparado en cualquier cámara
                        if detection.get('plc_triggered', False):
                            consolidated_pieces[track_id]['plc_triggered'] = True
            
            # Convertir a lista y ordenar por track_id
            self.all_detections = list(consolidated_pieces.values())
            self.all_detections.sort(key=lambda x: x.get('track_id', 0))
            
            self.populate_class_filter()
            self.apply_filters()
            self.update_statistics()
            
        except Exception as e:
            print(f"Error cargando historial: {e}")
            
    def populate_class_filter(self):
        """Popula el filtro de clases con las clases detectadas."""
        current_text = self.class_filter.currentText()
        self.class_filter.clear()
        self.class_filter.addItem("Todas")
        
        # Obtener todas las clases únicas
        classes = set()
        for detection in getattr(self, 'all_detections', []):
            classes.add(detection.get('label', 'Desconocida'))
            
        for class_name in sorted(classes):
            self.class_filter.addItem(class_name)
            
        # Restaurar selección si existe
        index = self.class_filter.findText(current_text)
        if index >= 0:
            self.class_filter.setCurrentIndex(index)
            
    def apply_filters(self):
        """Aplica los filtros seleccionados a las detecciones consolidadas."""
        if not hasattr(self, 'all_detections'):
            return
            
        filtered_detections = []
        
        camera_filter = self.camera_filter.currentText()
        class_filter = self.class_filter.currentText()
        tracked_only = self.tracked_only.isChecked()
        broken_only = self.broken_only.isChecked()
        
        for detection in self.all_detections:
            # Filtro de cámara
            if camera_filter != "Todas":
                if camera_filter == "Cámara 1" and detection.get('cam1', 0) == 0:
                    continue
                elif camera_filter == "Cámara 2" and detection.get('cam2', 0) == 0:
                    continue
                    
            # Filtro de clase
            if class_filter != "Todas":
                if detection.get('label') != class_filter:
                    continue
                    
            # Filtro de tracking (siempre tienen tracking en este formato)
            if tracked_only:
                if detection.get('track_id', -1) == -1:
                    continue
                    
            # Filtro de piezas quebradas (simplificado)
            if broken_only:
                # En el nuevo formato no tenemos información de piezas quebradas
                # Se puede agregar más tarde si es necesario
                continue
                    
            filtered_detections.append(detection)
            
        self.populate_table(filtered_detections)
        
    def populate_table(self, detections: List[Dict]):
        """Popula la tabla con las detecciones guardadas con miniaturas."""
        # Obtener detecciones guardadas de archivos
        saved_detections = self.get_saved_detections()
        
        self.detections_table.setRowCount(len(saved_detections))
        
        for row, detection in enumerate(saved_detections):
            # Columna 0: Miniatura
            thumbnail_label = QLabel()
            thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumbnail_label.setFixedSize(70, 60)
            
            # Cargar imagen y crear miniatura
            image_path = detection.get('image_path')
            if image_path and os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # Escalar a miniatura manteniendo proporción
                    scaled_pixmap = pixmap.scaled(65, 55, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    thumbnail_label.setPixmap(scaled_pixmap)
                else:
                    thumbnail_label.setText("📷")
            else:
                thumbnail_label.setText("❌")
            
            self.detections_table.setCellWidget(row, 0, thumbnail_label)
            
            # Columna 1: ID
            detection_id = detection.get('id', row + 1)
            id_item = QTableWidgetItem(str(detection_id))
            id_item.setBackground(QColor("#E3F2FD"))
            self.detections_table.setItem(row, 1, id_item)
            
            # Columna 2: Clase
            label = detection.get('label', 'Detección')
            self.detections_table.setItem(row, 2, QTableWidgetItem(label))
            
            # Columna 3: Tiempo
            date_str = detection.get('date', 'N/A')
            time_str = detection.get('time', 'N/A')
            if date_str != 'N/A' and time_str != 'N/A':
                # Formatear fecha y hora
                try:
                    date_formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    time_formatted = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
                    datetime_str = f"{date_formatted} {time_formatted}"
                except:
                    datetime_str = f"{date_str} {time_str}"
            else:
                datetime_str = "N/A"
            self.detections_table.setItem(row, 3, QTableWidgetItem(datetime_str))
            
            # Columna 4: Confianza
            confidence = detection.get('confidence', 0.0)
            confidence_str = f"{confidence:.1%}"
            self.detections_table.setItem(row, 4, QTableWidgetItem(confidence_str))
            
            # Columna 5: Cámara
            camera_id = detection.get('camera_id', 0)
            camera_str = f"Cam {camera_id}"
            self.detections_table.setItem(row, 5, QTableWidgetItem(camera_str))
            
            # Columna 6: Archivo
            filename = detection.get('filename', 'N/A')
            self.detections_table.setItem(row, 6, QTableWidgetItem(filename))
            
    def update_statistics(self):
        """Actualiza las estadísticas mostradas."""
        if not hasattr(self, 'all_detections'):
            return
            
        total_detections = len(self.all_detections)
        self.total_detections_label.setText(str(total_detections))
        
        # Contar objetos trackeados
        tracked_count = sum(1 for d in self.all_detections if d.get('track_id', -1) != -1)
        self.tracked_objects_label.setText(str(tracked_count))
        
        # Contar piezas quebradas
        broken_count = sum(1 for d in self.all_detections if d.get('is_broken', False))
        self.broken_pieces_label.setText(str(broken_count))
        
        # Estadísticas por cámara
        cam1_count = sum(1 for d in self.all_detections if d.get('camera') == 1)
        cam2_count = sum(1 for d in self.all_detections if d.get('camera') == 2)
        
        self.cam1_stats.setText(f"Cámara 1: {cam1_count} detecciones")
        self.cam2_stats.setText(f"Cámara 2: {cam2_count} detecciones")
        
        # Estadísticas por clase
        self.update_class_statistics()
        
        # Estadísticas de tracking
        self.update_tracking_statistics()
        
    def update_class_statistics(self):
        """Actualiza las estadísticas por clase."""
        # Limpiar estadísticas anteriores
        for i in reversed(range(self.class_stats_layout.count())):
            self.class_stats_layout.itemAt(i).widget().setParent(None)
            
        # Contar por clase
        class_counts = {}
        for detection in getattr(self, 'all_detections', []):
            label = detection.get('label', 'Desconocida')
            class_counts[label] = class_counts.get(label, 0) + 1
            
        # Crear labels para cada clase
        for class_name, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(self.all_detections)) * 100 if self.all_detections else 0
            label = QLabel(f"{class_name}: {count} ({percentage:.1f}%)")
            label.setStyleSheet("padding: 2px; margin: 1px;")
            self.class_stats_layout.addWidget(label)
            
    def update_tracking_statistics(self):
        """Actualiza las estadísticas de tracking."""
        try:
            # Obtener estadísticas de tracking del detection handler
            track_summary_cam1 = self.detection_handler.get_tracking_summary(1)
            track_summary_cam2 = self.detection_handler.get_tracking_summary(2)
            
            active_cam1 = track_summary_cam1.get('active_tracks', 0)
            active_cam2 = track_summary_cam2.get('active_tracks', 0)
            total_cam1 = track_summary_cam1.get('total_tracks', 0)
            total_cam2 = track_summary_cam2.get('total_tracks', 0)
            
            self.active_tracks_cam1.setText(f"Activos Cam1: {active_cam1}")
            self.active_tracks_cam2.setText(f"Activos Cam2: {active_cam2}")
            self.total_tracks.setText(f"Total tracks: {total_cam1 + total_cam2}")
            
        except Exception as e:
            print(f"Error actualizando estadísticas de tracking: {e}")
            
    def clear_history(self):
        """Limpia el historial de detecciones."""
        try:
            # Limpiar historial en el detection handler
            self.detection_handler.detection_history[1].clear()
            self.detection_handler.detection_history[2].clear()
            
            # Resetear tracking
            self.detection_handler.reset_tracking()
            
            # Actualizar vista
            self.load_detection_history()
            
            print("✅ Historial de detecciones limpiado")
            
        except Exception as e:
            print(f"❌ Error limpiando historial: {e}")
            
    def export_data(self):
        """Exporta los datos de detección a un archivo."""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"detecciones_export_{timestamp}.csv"
            
            # TODO: Implementar exportación a CSV
            print(f"📤 Funcionalidad de exportación pendiente - {filename}")
            
        except Exception as e:
            print(f"❌ Error exportando datos: {e}")
            
    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana."""
        self.update_timer.stop()
        event.accept()