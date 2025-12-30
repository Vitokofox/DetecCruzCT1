"""
yolo_handler.py

Manejador robusto para cargar modelos YOLO (Ultralytics) en distintos entornos:
- Entorno normal (script / desarrollo)
- Ejecutable empaquetado (PyInstaller)

Objetivos:
- Evitar rutas absolutas (usar rutas relativas al proyecto / carpeta models).
- Preferir siempre el model_path configurado (por ejemplo desde CamConfig).
- Tener un único punto de carga de modelo para que el resto del sistema
  (DetectionHandler, etc.) solo use YOLOModelHandler.model.
"""

import os
import sys
import logging
from typing import Optional, Tuple, List

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except Exception as e:
    YOLO_AVAILABLE = False
    YOLO_IMPORT_ERROR = e

# utils.py debe exponer estas funciones, que ya usas en otros módulos
try:
    from src.utils.utils import setup_torch_for_yolo, find_yolo_models
except ImportError:
    # Try relative import for flexibility
    try:
        from ...utils.utils import setup_torch_for_yolo, find_yolo_models
    except ImportError:
        pass # Fallback below handle it
    # Fallback suave si no están disponibles (no debería pasar en tu proyecto)
    def setup_torch_for_yolo():
        return

    def find_yolo_models(base_dir: str) -> list:
        return []

log = logging.getLogger("YOLOModelHandler")


class YOLOModelHandler:
    """
    Encapsula la carga del modelo YOLO, manejando rutas relativas, entorno PyInstaller
    y selección automática del mejor modelo disponible cuando no se entrega uno explícito.
    """

    def __init__(self) -> None:
        self.model: Optional["YOLO"] = None
        self.model_path: Optional[str] = None

    # ------------------------------------------------------------------
    # API pública principal
    # ------------------------------------------------------------------
    def load_model(self, explicit_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Carga el modelo YOLO.

        Parameters
        ----------
        explicit_path : str | None
            Ruta recibida desde la configuración (CamConfig.model_path) u otro lugar.
            Puede ser absoluta o relativa. Si es None o no existe, se intentará
            encontrar el mejor modelo disponible en la carpeta `models/`.

        Returns
        -------
        (success, message) : (bool, str)
            success = True si el modelo se cargó correctamente.
            message = detalle del resultado o del error.
        """
        if not YOLO_AVAILABLE:
            msg = f"No se pudo importar ultralytics.YOLO: {YOLO_IMPORT_ERROR}"
            log.error(msg)
            return False, msg

        # Ajustar backend Torch si corresponde
        try:
            setup_torch_for_yolo()
        except Exception as e:
            # No es crítico para cargar el modelo; solo lo logueamos.
            log.warning(f"setup_torch_for_yolo() falló: {e}")

        base_dir = self._get_base_dir()
        models_dir = os.path.join(base_dir, "models")

        candidate_paths: List[str] = []

        # 1) Si te pasan un path explícito, lo intentamos primero
        if explicit_path:
            resolved = self._resolve_model_path(explicit_path, base_dir, models_dir)
            if resolved:
                candidate_paths.append(resolved)
            else:
                log.warning(
                    f"Ruta explícita de modelo no encontrada: {explicit_path} "
                    f"(base_dir={base_dir}, models_dir={models_dir})"
                )

        # 2) Si no hay candidato aún, buscamos automáticamente modelos en la carpeta
        if not candidate_paths:
            auto_models = find_yolo_models(models_dir) or find_yolo_models(base_dir)
            # Opcional: puedes priorizar alguno por nombre
            priority_order = [
                "best_Cruzamiento_v3.pt",
                "best_cruzamiento.pt",
                "best.pt",
            ]
            sorted_auto = self._sort_models_by_priority(auto_models, priority_order)
            candidate_paths.extend(sorted_auto)

        if not candidate_paths:
            msg = (
                "No se encontró ningún modelo YOLO.\n"
                f"- base_dir: {base_dir}\n"
                f"- models_dir: {models_dir}\n"
                "Asegúrate de que exista una carpeta 'models' con un archivo .pt."
            )
            log.error(msg)
            return False, msg

        # Intentamos cargar el primer modelo que funcione
        last_error = None
        
        # Detectar dispositivo
        try:
            import torch
            device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
            device_name = torch.cuda.get_device_name(0) if device == 'cuda:0' else 'CPU'
            log.info(f"🖥️ Dispositivo de inferencia seleccionado: {device} ({device_name})")
        except ImportError:
            device = 'cpu'
            log.warning("⚠️ Torch no importable para chequear CUDA, usando CPU")

        for path in candidate_paths:
            try:
                log.info(f"Intentando cargar modelo YOLO desde: {path}")
                model = YOLO(path)  # type: ignore[call-arg]
                
                # Mover al dispositivo (YOLO ultralytics maneja esto, pero lo forzamos para asegurar)
                model.to(device)
                
                # Si llega aquí, cargó bien
                self.model = model
                self.model_path = path

                info = self._describe_model(model)
                msg = f"Modelo YOLO cargado correctamente desde '{path}' en {device}. {info}"
                log.info(msg)
                return True, msg

            except Exception as e:
                last_error = e
                log.error(f"Error cargando modelo desde '{path}': {e}", exc_info=True)

        msg = f"No se pudo cargar ningún modelo YOLO. Último error: {last_error}"
        log.error(msg)
        return False, msg

    # ------------------------------------------------------------------
    # Métodos auxiliares
    # ------------------------------------------------------------------
    def _get_base_dir(self) -> str:
        """
        Devuelve el directorio base del proyecto, considerando:
        - Ejecución normal (usa la carpeta donde está este archivo).
        - Ejecutable PyInstaller (usa sys._MEIPASS si existe).
        """
        # PyInstaller: sys._MEIPASS apunta al directorio temporal con los recursos
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            return sys._MEIPASS  # type: ignore[attr-defined]
        # Modo desarrollo / script normal
        # Estamos en src/services/yolo_handler.py, subir 2 niveles a app/
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    def _resolve_model_path(self, path: str, base_dir: str, models_dir: str) -> Optional[str]:
        """
        Intenta resolver una ruta de modelo que puede ser:
        - Absoluta y válida
        - Relativa respecto a base_dir
        - Relativa respecto a models_dir

        Devuelve la ruta existente o None si no se encuentra.
        """
        # 1) Si ya es absoluta y existe, la usamos tal cual
        if os.path.isabs(path) and os.path.exists(path):
            return path

        # 2) Probar como relativa a base_dir
        candidate = os.path.join(base_dir, path)
        if os.path.exists(candidate):
            return candidate

        # 3) Probar como relativa a models_dir
        candidate = os.path.join(models_dir, path)
        if os.path.exists(candidate):
            return candidate

        return None

    def _sort_models_by_priority(self, models: list, priority_order: list) -> list:
        """
        Ordena una lista de rutas de modelos según una lista de prioridades por nombre.
        Los que no estén en priority_order quedan al final.
        """
        if not models:
            return []

        def priority_key(p: str) -> int:
            name = os.path.basename(p)
            if name in priority_order:
                return priority_order.index(name)
            return len(priority_order) + 1

        return sorted(models, key=priority_key)

    def _describe_model(self, model: "YOLO") -> str:
        """
        Devuelve un string corto describiendo el modelo (clases, etc.).
        """
        try:
            names = getattr(model, "names", None)
            if isinstance(names, dict):
                num_classes = len(names)
                class_list = list(names.values())
                return f"Clases: {num_classes} -> {class_list}"
            return "Modelo YOLO cargado (sin info de clases)."
        except Exception:
            return "Modelo YOLO cargado (no se pudo leer names)."
