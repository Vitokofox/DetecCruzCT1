@echo off
echo ===================================================
echo   Setup de Entorno - Sistema de Cruzamiento V3
echo ===================================================
echo.

REM Verificar si Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no encontrado. Por favor instala Python 3.10+ y agregalo al PATH.
    pause
    exit /b
)

echo 1. Creando entorno virtual (.venv)...
python -m venv .venv
if %errorlevel% neq 0 (
    echo [ERROR] Fallo al crear el entorno virtual.
    pause
    exit /b
)

echo.
echo 2. Activando entorno virtual...
call .venv\Scripts\activate

echo.
echo 3. Actualizando pip...
python -m pip install --upgrade pip

echo.
echo 4. Instalando dependencias desde requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Fallo instalando dependencias. Revisa tu conexion a internet.
    pause
    exit /b
)

echo.
echo ===================================================
echo   INSTALACION COMPLETADA CON EXITO!
echo ===================================================
echo.
echo Para correr la app, usa el script 'run_app.bat' o activa el entorno y ejecuta 'python oper_window.py'.
echo.
pause
