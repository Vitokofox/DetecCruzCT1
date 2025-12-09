@echo off
echo 📱 Iniciando Frontend GradingApp...
cd frontend
echo ✅ Usando Node.js portable desde directorio usuario
echo 🧪 Verificando Node.js...
"%USERPROFILE%\nodejs\node.exe" --version
"%USERPROFILE%\nodejs\npm.cmd" --version
echo 🚀 Iniciando servidor de desarrollo...
"%USERPROFILE%\nodejs\npm.cmd" run dev
pause