"""
Monitor diagnóstico de comunicación Modbus TCP con PLC.

- Lee periódicamente los registros %MW10203 y %MW10204.
- Muestra todos los frames Modbus enviados/recibidos en consola (logging DEBUG).
- Permite escritura manual a registros mediante comandos (opcional, comentado).
- Maneja excepciones y cierra conexión correctamente.
"""

import logging
import time
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s"
)
logging.getLogger("pymodbus").setLevel(logging.DEBUG)

PLC_IP = "192.168.10.50"
PLC_PORT = 502
PLC_UNIT_ID = 1

REG_SHORT = 10203
REG_LONG = 10204
REGS_EXTRA = [
    22001,  # plc_reg_addr_1
    22003,  # plc_reg_addr_2
    22003,  # plc_reg_addr_3
    22004,  # plc_reg_addr_operador
    22005,  # plc_reg_addr_pieza_quebrada
    22006,  # plc_reg_addr_alaveo
]
READ_INTERVAL = 1.0  # segundos


def read_register(client, address):
    """Lee un registro Modbus y retorna su valor o None si hay error."""
    try:
        response = client.read_holding_registers(address)
        if response.isError():
            logging.error(f"Error leyendo registro {address}: {response}")
            return None
        value = response.registers[0]
        print(f"📥 Reg {address} = {value}")
        return value
    except Exception as e:
        logging.error(f"Excepción leyendo registro {address}: {e}")
        return None


def write_register(client, address, value):
    """Escribe un valor en un registro Modbus."""
    try:
        response = client.write_register(address, value, unit=PLC_UNIT_ID)
        if response.isError():
            logging.error(f"Error escribiendo registro {address}: {response}")
            return False
        logging.info(f"Registro {address} escrito con valor {value}")
        return True
    except Exception as e:
        logging.error(f"Excepción escribiendo registro {address}: {e}")
        return False


def main():
    print("Monitor Modbus TCP - PLC diagnóstico")
    print(f"Conectando a PLC {PLC_IP}:{PLC_PORT} (Unit ID: {PLC_UNIT_ID})...")
    client = ModbusTcpClient(host=PLC_IP, port=PLC_PORT, timeout=1.0)
    try:
        if not client.connect():
            logging.error("No se pudo conectar al PLC.")
            return
        logging.info("Conexión establecida.")
        # Modo interactivo (opcional)
        # import threading
        # def input_thread():
        #     while True:
        #         cmd = input()
        #         if cmd.startswith("w "):
        #             try:
        #                 _, addr, val = cmd.split()
        #                 addr = int(addr)
        #                 val = int(val)
        #                 write_register(client, addr, val)
        #             except Exception as e:
        #                 print(f"Comando inválido: {e}")
        # threading.Thread(target=input_thread, daemon=True).start()
        while True:
            read_register(client, REG_SHORT)
            read_register(client, REG_LONG)
            for reg in REGS_EXTRA:
                read_register(client, reg)
            time.sleep(READ_INTERVAL)
    except KeyboardInterrupt:
        print("\n⏹️ Monitor detenido por el usuario (CTRL+C)")
    except Exception as e:
        logging.error(f"Error inesperado: {e}")
    finally:
        client.close()
        logging.info("Conexión cerrada correctamente.")


if __name__ == "__main__":
    main()
