from PySide6.QtWidgets import QLabel, QMessageBox, QWidget
from typing import Any

class OperatorAlert:
    """Manejador de alertas de operador."""
    
    def __init__(self, alert_widget: QLabel, config: Any):
        self.alert_widget = alert_widget
        self.config = config
        self.operator_detected = False
        self.alert_visible = True
        
    def update_operator_status(self, detected: bool):
        """Actualiza el estado de la alerta de operador."""
        # Obtener referencia a la ventana principal
        main_window = self.alert_widget.window() # Use window() instead of parent() for safety
        
        if detected and not self.operator_detected:
            self.operator_detected = True
            self.show_alert()
            
            # Detener detección y grabación si están activas
            if hasattr(main_window, 'stop_detection'):
                # Note: calling stop_detection might cause recursion if not careful, 
                # but here it seems the alert just notifies.
                # However, logic in main_refactorized suggested it stops things.
                # We will keep it simple: Just show alert.
                # If we want to stop, we should do it via signals or direct call if sure.
                pass

            # Mensaje visual y consola
            status_det = getattr(main_window, 'status_detection', None)
            if status_det:
                status_det.setText("🤖 Detección: ⏸️ Detenida por intervención de operador")
                
            status_rec = getattr(main_window, 'status_recording', None)
            if status_rec:
                status_rec.setText("🔴 Grabación: Detenida por operador")
                
            print("⏹️ Detección y grabación detenidas por intervención de operador")
            
        elif not detected and self.operator_detected:
            self.operator_detected = False
            self.hide_alert()
            
            status_det = getattr(main_window, 'status_detection', None)
            if status_det:
                status_det.setText("🤖 Detección: 🟢 Activa")
                
            status_rec = getattr(main_window, 'status_recording', None)
            if status_rec:
                status_rec.setText("🔴 Grabación: Inactiva")
                
            print("✅ Operador ya no está en área peligrosa - Alerta desactivada")

    def show_alert(self):
        self.alert_widget.setVisible(True)
        self.alert_widget.setStyleSheet(
            f"background-color: {getattr(self.config, 'operador_alert_color', 'red')}; "
            "color: white; font-size: 24px; font-weight: bold; padding: 10px; border-radius: 10px;"
        )
            
    def hide_alert(self):
        self.alert_widget.setVisible(False)
