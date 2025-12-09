"""
Servidor simple para probar la API REST de Supabase
usando solo la librería http.server de Python
"""
import os
import json
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

class GradingAPIHandler(BaseHTTPRequestHandler):
    """Handler para las peticiones HTTP del API de Grading"""
    
    def _set_cors_headers(self):
        """Configurar headers CORS para permitir acceso desde el frontend"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        
    def _send_json_response(self, data, status=200):
        """Enviar respuesta JSON"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self._set_cors_headers()
        self.end_headers()
        response_json = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
    
    def _get_supabase_headers(self):
        """Headers para Supabase"""
        return {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
    
    def do_OPTIONS(self):
        """Manejar preflight CORS"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """Manejar peticiones GET"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            params = parse_qs(parsed_url.query)
            
            if path == '/':
                self._send_json_response({
                    "message": "🪵 GradingApp API funcionando",
                    "version": "1.0.0",
                    "endpoints": [
                        "/api/v1/inspecciones",
                        "/api/v1/distribucion-grado",
                        "/api/v1/tipificacion-defectos", 
                        "/api/v1/totales"
                    ]
                })
                
            elif path == '/health':
                # Test de conexión con Supabase
                try:
                    response = requests.get(
                        f"{SUPABASE_URL}/rest/v1/inspecciones?select=count&limit=1",
                        headers=self._get_supabase_headers(),
                        timeout=5
                    )
                    supabase_ok = response.status_code == 200
                except:
                    supabase_ok = False
                    
                self._send_json_response({
                    "status": "healthy" if supabase_ok else "warning",
                    "database": "connected" if supabase_ok else "disconnected",
                    "timestamp": "2025-11-21"
                })
                
            elif path == '/api/v1/inspecciones':
                # Obtener inspecciones
                try:
                    limit = params.get('limit', ['100'])[0]
                    response = requests.get(
                        f"{SUPABASE_URL}/rest/v1/inspecciones?select=*&limit={limit}&order=id.desc",
                        headers=self._get_supabase_headers()
                    )
                    
                    if response.status_code == 200:
                        self._send_json_response(response.json())
                    else:
                        self._send_json_response({
                            "error": f"Supabase error: {response.status_code}",
                            "detail": response.text
                        }, 500)
                        
                except Exception as e:
                    self._send_json_response({
                        "error": "Database connection failed",
                        "detail": str(e)
                    }, 500)
                    
            elif path.startswith('/api/v1/'):
                # Otros endpoints
                table = path.split('/')[-1].replace('-', '_')
                try:
                    response = requests.get(
                        f"{SUPABASE_URL}/rest/v1/{table}?select=*",
                        headers=self._get_supabase_headers()
                    )
                    
                    if response.status_code == 200:
                        self._send_json_response(response.json())
                    else:
                        self._send_json_response({
                            "error": f"Table '{table}' not found or accessible",
                            "status": response.status_code
                        }, 404)
                        
                except Exception as e:
                    self._send_json_response({
                        "error": "Database error",
                        "detail": str(e)
                    }, 500)
            else:
                self._send_json_response({
                    "error": "Endpoint not found",
                    "path": path
                }, 404)
                
        except Exception as e:
            self._send_json_response({
                "error": "Internal server error",
                "detail": str(e)
            }, 500)
    
    def do_POST(self):
        """Manejar peticiones POST"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            if path.startswith('/api/v1/'):
                table = path.split('/')[-1].replace('-', '_')
                
                try:
                    response = requests.post(
                        f"{SUPABASE_URL}/rest/v1/{table}",
                        headers={**self._get_supabase_headers(), "Prefer": "return=representation"},
                        json=data
                    )
                    
                    if response.status_code in [200, 201]:
                        self._send_json_response(response.json(), 201)
                    else:
                        self._send_json_response({
                            "error": f"Failed to create record in '{table}'",
                            "status": response.status_code,
                            "detail": response.text
                        }, 400)
                        
                except Exception as e:
                    self._send_json_response({
                        "error": "Database error",
                        "detail": str(e)
                    }, 500)
            else:
                self._send_json_response({
                    "error": "Invalid endpoint for POST",
                    "path": path
                }, 404)
                
        except Exception as e:
            self._send_json_response({
                "error": "Request processing error",
                "detail": str(e)
            }, 400)
    
    def log_message(self, format, *args):
        """Personalizar logging"""
        print(f"[{self.date_time_string()}] {format % args}")

def main():
    """Ejecutar el servidor"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: SUPABASE_URL y SUPABASE_ANON_KEY deben estar configuradas en .env")
        return
    
    server_address = ('127.0.0.1', 8000)
    httpd = HTTPServer(server_address, GradingAPIHandler)
    
    print("🚀 Servidor GradingApp iniciado")
    print(f"📡 URL: http://127.0.0.1:8000")
    print(f"🔗 Supabase: {SUPABASE_URL}")
    print("📋 Endpoints disponibles:")
    print("   GET  / - Info del API")
    print("   GET  /health - Estado de salud")
    print("   GET  /api/v1/inspecciones - Listar inspecciones")
    print("   POST /api/v1/inspecciones - Crear inspección")
    print("   GET  /api/v1/distribucion-grado - Distribución por grado")
    print("   GET  /api/v1/tipificacion-defectos - Defectos")
    print("   GET  /api/v1/totales - Totales")
    print("\n🔥 Presiona Ctrl+C para detener el servidor")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  Servidor detenido")
        httpd.server_close()

if __name__ == "__main__":
    main()