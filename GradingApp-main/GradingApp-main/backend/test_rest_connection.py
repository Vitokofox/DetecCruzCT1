"""
Script para probar la conexión REST a Supabase
Esta alternativa funciona a través de HTTPS (puerto 443) que suele estar permitido en redes corporativas
"""
import asyncio
import sys
import os

# Agregar el directorio actual al path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase_rest import rest_client

async def test_rest_connection():
    print("🌐 Probando conexión REST a Supabase...")
    print(f"📡 URL: {os.getenv('SUPABASE_URL')}")
    
    try:
        success, message = await rest_client.test_connection()
        print(message)
        
        if success:
            print("\n✅ ¡Perfecto! Supabase REST API está funcionando")
            print("🚀 Puedes usar la aplicación normalmente")
            
            # Probar crear una tabla si no existe
            try:
                # Intentar obtener datos (esto creará la tabla si no existe en algunos casos)
                data = rest_client.get_inspecciones(limit=1)
                print(f"📊 Tabla 'inspecciones' accesible - {len(data)} registros")
            except Exception as e:
                print(f"⚠️  Tabla 'inspecciones' podría necesitar ser creada: {e}")
                print("💡 Puedes crearla desde el panel de Supabase o SQL Editor")
        else:
            print("\n❌ No se pudo conectar via REST API")
            print("🔧 Posibles soluciones:")
            print("   • Verifica SUPABASE_URL y SUPABASE_ANON_KEY en .env")
            print("   • Revisa si el proyecto de Supabase está activo")
            print("   • Consulta con IT sobre políticas de proxy/firewall")
            
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    asyncio.run(test_rest_connection())