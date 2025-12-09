@echo off
echo 📦 Configurando Node.js Portable para GradingApp
echo.
echo 1. Descargue Node.js desde: https://nodejs.org/en/download/
echo 2. Seleccione "Windows Binary (.zip)" - NO el instalador .msi
echo 3. Extraiga el ZIP en: %USERPROFILE%\nodejs
echo 4. Ejecute este script nuevamente para verificar
echo.
set PATH=%USERPROFILE%\nodejs;%PATH%
echo Verificando instalación...
if exist "%USERPROFILE%\nodejs\node.exe" (
    echo ✅ Node.js encontrado en %USERPROFILE%\nodejs
    "%USERPROFILE%\nodejs\node.exe" --version
    "%USERPROFILE%\nodejs\npm.cmd" --version
    echo.
    echo 🎉 Node.js está listo! Puede ejecutar start-frontend.bat
) else (
    echo ❌ Node.js no encontrado en %USERPROFILE%\nodejs
    echo Por favor siga las instrucciones arriba
)
pause