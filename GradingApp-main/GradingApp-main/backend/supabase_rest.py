"""
Cliente alternativo para Supabase usando REST API
Útil cuando la conexión directa a PostgreSQL está bloqueada por firewalls
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import httpx

load_dotenv()

class SupabaseRESTClient:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
            
        self.supabase: Client = create_client(url, key)
        self.table_name = "inspecciones"
    
    async def test_connection(self):
        """Probar conexión a Supabase REST API"""
        try:
            # Intenta obtener datos de la tabla (incluso si está vacía)
            response = self.supabase.table(self.table_name).select("*").limit(1).execute()
            return True, f"✅ Conexión REST OK - {len(response.data)} registros encontrados"
        except Exception as e:
            return False, f"❌ Error REST: {e}"
    
    def create_inspeccion(self, data: dict):
        """Crear nueva inspección"""
        try:
            response = self.supabase.table(self.table_name).insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Error creating inspection: {e}")
    
    def get_inspecciones(self, limit: int = 100, offset: int = 0):
        """Obtener lista de inspecciones"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .order("fecha_creacion", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()
            return response.data
        except Exception as e:
            raise Exception(f"Error fetching inspections: {e}")
    
    def get_inspeccion_by_id(self, inspeccion_id: int):
        """Obtener inspección por ID"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("id", inspeccion_id)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Error fetching inspection: {e}")
    
    def update_inspeccion(self, inspeccion_id: int, data: dict):
        """Actualizar inspección"""
        try:
            response = self.supabase.table(self.table_name)\
                .update(data)\
                .eq("id", inspeccion_id)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Error updating inspection: {e}")
    
    def delete_inspeccion(self, inspeccion_id: int):
        """Eliminar inspección"""
        try:
            response = self.supabase.table(self.table_name)\
                .delete()\
                .eq("id", inspeccion_id)\
                .execute()
            return True
        except Exception as e:
            raise Exception(f"Error deleting inspection: {e}")

# Instancia global
rest_client = SupabaseRESTClient()