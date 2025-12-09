import requests
import json
from datetime import datetime

API_URL = "http://127.0.0.1:8000/api/v1"

def test_create_inspeccion():
    print("🧪 Probando creación de inspección...")
    
    # Payload similar al que envía el frontend
    payload = {
        "fecha_inspeccion": datetime.now().isoformat(),
        "fecha_produccion": datetime.now().isoformat(),
        "area": "Clasificación",
        "supervisor": "Test Bot",
        "responsable": "Antigravity",
        "lote": "TEST-101",
        "mercado": "Interno",
        "producto": "Pino Radiata",
        "terminacion": "Bruto",
        "turno": "Mañana",
        "jornada": "Completa",
        "pzas_inspeccionadas": 50,
        "escuadria": "1x4",
        "espesor": 25.4,
        "ancho": 100.0,
        "largo": 900.0,
        "maquina": "Línea 1",
        "origen": "Aserradero"
    }
    
    try:
        response = requests.post(f"{API_URL}/inspecciones", json=payload)
        
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Inspección creada exitosamente!")
                print(f"🆔 ID: {data['data']['id']}")
                return data['data']['id']
            else:
                print(f"❌ Error en respuesta: {data.get('error')}")
                print(f"🔍 Full Data: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"📄 Body: {response.text}")
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

def test_cleanup(inspeccion_id):
    if not inspeccion_id:
        return
        
    print(f"\n🧹 Limpiando inspección de prueba ID: {inspeccion_id}...")
    try:
        response = requests.delete(f"{API_URL}/inspecciones/{inspeccion_id}")
        if response.status_code == 200:
            print("✅ Inspección eliminada")
        else:
            print("⚠️ No se pudo eliminar la inspección de prueba")
    except:
        pass

if __name__ == "__main__":
    inspeccion_id = test_create_inspeccion()
    # Opcional: limpiar después de probar
    # test_cleanup(inspeccion_id)
