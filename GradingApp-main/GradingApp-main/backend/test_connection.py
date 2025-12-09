
## SQLAlchemy eliminado. Este script debe probar la conexión a Supabase REST.
from supabase_rest import rest_client

def test_supabase_connection():
    try:
        # Ejemplo: obtener inspecciones (ajusta según tu tabla)
        result = rest_client.get_inspecciones(limit=1)
        print("✅ Conexión Supabase REST OK →", result)
    except Exception as e:
        print("❌ ERROR:", e)
        print("🔧 Verifica las credenciales en el archivo .env")

if __name__ == "__main__":
    test_supabase_connection()