"""
Servicio de comunicación PLC Modbus TCP.

Compatible con pymodbus 3.6+
-----------------------------------------------------------------
• Lee registros con: client.read_holding_registers(addr)
• Escribe registros con: client.write_register(addr, value)
• Sin device_id, unit_id, ni slave (tu versión NO los acepta)
-----------------------------------------------------------------
"""

import time
import logging
from pymodbus.client import ModbusTcpClient

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("PLCService")


class PLCService:
    # ---------------------------------------------------------------
    #  Parámetro de reenganche
    # ---------------------------------------------------------------
    def set_reenganche_param(self, valor: int):
        """
        Define cuántas iteraciones consecutivas "buenas" se requieren
        antes de reconectar la señal al PLC.
        """
        if valor < 1:
            valor = 1
        self.reenganche_param = valor
        log.info(f"Parámetro de reenganche actualizado a: {self.reenganche_param}")

    def get_reenganche_param(self) -> int:
        """
        Devuelve el parámetro de reenganche (por defecto 10 si no está definido).
        """
        return getattr(self, "reenganche_param", 10)

    # ---------------------------------------------------------------
    #  Lógica de desconexión / reconexión de señal
    # ---------------------------------------------------------------
    def desconectar_senal(self):
        """
        Lógica para desconectar la señal al PLC.
        Si en cfg se define plc_reg_addr_enable, se escribe ahí un 0.
        """
        log.info("Señal al PLC desconectada por seguridad.")
        
        # Bloquear envío de señales por software
        self.signals_enabled = False

        if not self.is_connected():
            return

        enable_addr = getattr(self.cfg, "plc_reg_addr_enable", None)
        if enable_addr is not None:
            try:
                resp = self.client.write_register(enable_addr, 0)
                if resp.isError():
                    log.error(f"Error deshabilitando señal en registro {enable_addr}: {resp}")
            except Exception as e:
                log.error(f"Excepción deshabilitando señal en registro {enable_addr}: {e}")

    def reconectar_senal(self):
        """
        Lógica para reconectar la señal al PLC.
        Si en cfg se define plc_reg_addr_enable, se escribe ahí un 1.
        """
        log.info("Señal al PLC reconectada tras reenganche.")
        
        # Habilitar envío de señales
        self.signals_enabled = True

        if not self.is_connected():
            return

        enable_addr = getattr(self.cfg, "plc_reg_addr_enable", None)
        if enable_addr is not None:
            try:
                resp = self.client.write_register(enable_addr, 1)
                if resp.isError():
                    log.error(f"Error habilitando señal en registro {enable_addr}: {resp}")
            except Exception as e:
                log.error(f"Excepción habilitando señal en registro {enable_addr}: {e}")

    # ---------------------------------------------------------------
    #  INIT
    # ---------------------------------------------------------------
    def __init__(self, cfg):
        """
        cfg = CamConfig con parámetros del PLC
        """
        self.cfg = cfg
        self.client: ModbusTcpClient | None = None
        self._connected = False
        
        # Estado de aislamiento por seguridad (Operador)
        self.is_isolated = False
        
        # Estado de habilitación de señales (Controlado por cadenas/proceso)
        self.signals_enabled = False # Inicia bloqueado hasta que se confirme "100% en linea"

        # Cooldowns por clase / cámara
        self.last_pulse_time = {}

        # Parámetro de reenganche desde config (plc_reenganche_param en JSON)
        default_reenganche = getattr(cfg, "plc_reenganche_param", 10)
        try:
            default_reenganche = int(default_reenganche)
        except Exception:
            default_reenganche = 10
        self.reenganche_param = max(1, default_reenganche)

        # ===============================================
        #  MAPEOS DE REGISTROS PLC  (desde config JSON)
        # ===============================================
        self.class_address_map = {
            "Cruzamiento": cfg.plc_reg_addr_1,
            "CruzyMont": cfg.plc_reg_addr_2,
            "Montada": cfg.plc_reg_addr_3,
            "Operador": cfg.plc_reg_addr_operador,
            "Quebrada": cfg.plc_reg_addr_pieza_quebrada,
            "Alaveo": cfg.plc_reg_addr_alaveo,
            "Pieza": cfg.plc_reg_addr_pieza,
        }

    # ==========================================================
    #  CONEXIÓN
    # ==========================================================
    def connect(self) -> bool:
        """Intenta conectar con el PLC via Modbus TCP."""
        try:
            log.info(f"🔌 Intentando conectar a PLC: {self.cfg.plc_ip}:{self.cfg.plc_port}")

            self.client = ModbusTcpClient(
                host=self.cfg.plc_ip,
                port=self.cfg.plc_port,
                timeout=2.5,
            )

            if not self.client.connect():
                log.error("❌ No se pudo conectar al PLC.")
                self._connected = False
                return False

            # Lectura de prueba (registro 0 o cualquier registro válido)
            try:
                test = self.client.read_holding_registers(0)
                if test.isError():
                    log.warning("⚠️ Conectado, pero error en la lectura de prueba.")
                    self._connected = False
                else:
                    log.info("✅ PLC conectado exitosamente.")
                    self._connected = True
            except Exception as e:
                log.error(f"⚠️ Error verificando lectura Modbus: {e}")
                self._connected = False

            return self._connected

        except Exception as e:
            log.error(f"❌ Error conectando PLC: {e}")
            self._connected = False
            return False

    def is_connected(self) -> bool:
        """
        Verifica el estado lógico de conexión y el cliente Modbus.
        """
        if self.client is None:
            return False
        return bool(self._connected and getattr(self.client, "connected", True))

    def close(self):
        """Cierra la conexión con el PLC."""
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            finally:
                self.client = None
                self._connected = False

    # ==========================================================
    #  MODO DE AISLAMIENTO (SEGURIDAD)
    # ==========================================================
    def set_isolation(self, isolated: bool):
        """
        Activa o desactiva el modo de aislamiento.
        Si está aislado (True), no se enviarán pulsos al PLC 
        (excepto funciones administrativas si las hubiera).
        """
        if isolated != self.is_isolated:
            self.is_isolated = isolated
            if isolated:
                log.warning("🔒 PLC EN MODO AISLAMIENTO (Seguridad Activa). Pulsos bloqueados.")
            else:
                log.info("🔓 PLC liberado del aislamiento. Pulsos permitidos.")

    # ==========================================================
    #  LECTURA DE REGISTROS
    # ==========================================================
    def read_status_register(self, address: int) -> int:
        """
        Lee un registro holding y devuelve su valor o -1 si falla.
        """
        if not self.is_connected():
            return -1

        try:
            resp = self.client.read_holding_registers(address)
            if resp.isError():
                log.error(f"Error leyendo registro {address}: {resp}")
                return -1

            return int(resp.registers[0])

        except Exception as e:
            log.error(f"Excepción leyendo registro {address}: {e}")
            return -1

    # ==========================================================
    #  ENVÍO DE PULSOS (ESCRITURA)
    # ==========================================================
    def pulse(
        self,
        mode: str,
        addr: int,
        pulse_ms: int,
        reg_val: int | None = None,
        cam_id: int = 1,
        class_name: str = "",
    ) -> bool:

        if not self.is_connected():
            log.warning("⚠️ No conectado al PLC → no se envió pulso.")
            return False

        # Verificar si el sistema está "100% en linea" (señales habilitadas)
        if not self.signals_enabled:
            # log.debug("⚠️ Señales deshabilitadas (sistema en espera/reconexión) → pulso bloqueado.") 
            return False

        # Verificar aislamiento por seguridad
        if self.is_isolated:
            log.warning(f"🔒 PLC AISLADO: Pulso a {addr} ({class_name}) BLOQUEADO por seguridad.")
            return False

        # Default del valor del pulso
        if reg_val is None:
            reg_val = self.cfg.plc_reg_pulse_value

        cooldown_key = f"{cam_id}_{class_name.lower()}"
        now = time.time()

        # Cooldown
        last = self.last_pulse_time.get(cooldown_key, 0)
        if now - last < self.cfg.plc_cooldown_s:
            # log.debug(f"🔄 Cooldown activo para {class_name}") # Silenciado para optimización
            return False

        try:
            # ===============================
            #  ESCRIBIR PULSO
            # ===============================
            resp1 = self.client.write_register(addr, reg_val)
            if resp1.isError():
                log.error(f"❌ Error activando registro {addr}")
                return False

            time.sleep(pulse_ms / 1000.0)

            resp2 = self.client.write_register(addr, 0)
            if resp2.isError():
                log.error(f"❌ Error desactivando registro {addr}")

            # Registrar cooldown
            self.last_pulse_time[cooldown_key] = now

            log.info(f"✅ Pulso enviado: {class_name} → Registro {addr}")
            return True

        except Exception as e:
            log.error(f"❌ Error enviando pulso a {addr}: {e}")
            return False

    # ==========================================================
    #  ENVÍO AUTOMÁTICO SEGÚN CLASE DETECTADA
    # ==========================================================
    def send_detection(self, class_name: str) -> bool:
        """
        Envia al PLC la clase detectada desde YOLO.
        """
        if not self.cfg.plc_enabled:
            return False
        if not self.is_connected():
            return False

        class_name = class_name.lower()

        if class_name not in self.class_address_map:
            log.warning(f"Clase no mapeada: {class_name}")
            return False

        register = self.class_address_map[class_name]
        return self.pulse("register", register, self.cfg.plc_pulse_ms, class_name=class_name)

    # ==========================================================
    #  ESTADO GENERAL
    # ==========================================================
    def get_status(self) -> dict:
        return {
            "enabled": self.cfg.plc_enabled,
            "connected": self.is_connected(),
            "ip": self.cfg.plc_ip,
            "port": self.cfg.plc_port,
            "cooldown_s": self.cfg.plc_cooldown_s,
            "reenganche_param": self.get_reenganche_param(),
        }
