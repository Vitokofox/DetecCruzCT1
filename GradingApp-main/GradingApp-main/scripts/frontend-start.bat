@echo off
echo 🚀 Iniciando Frontend GradingApp...

REM Cambiar al directorio del proyecto
cd /d "C:\Users\victor.valenzuela\OneDrive - ARAUCO\Victor.valenzuela\Documentos\GradingApp\frontend"

echo 📁 Directorio actual: %CD%

REM Verificar que Node.js esté instalado
if exist "%USERPROFILE%\nodejs\node.exe" (
    echo ✅ Node.js encontrado
    "%USERPROFILE%\nodejs\node.exe" --version
    "%USERPROFILE%\nodejs\npm.cmd" --version
    
    echo 🚀 Iniciando servidor de desarrollo...
    "%USERPROFILE%\nodejs\npm.cmd" run dev
    
) else (
    echo ❌ Node.js no encontrado en %USERPROFILE%\nodejs
    echo Por favor ejecute install-nodejs.bat primero
    pause
)