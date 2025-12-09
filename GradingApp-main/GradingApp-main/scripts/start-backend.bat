@echo off
echo 🚀 Iniciando Backend GradingApp...
cd backend
call .venv\Scripts\activate
echo ✅ Entorno virtual activado
python simple_server.py
pause