# 📦 Instalación de Node.js para GradingApp

## 🎯 Objetivo
Instalar Node.js usando NVM (Node Version Manager) para poder ejecutar el frontend React y probar el sistema completo.

## 🔄 Pasos de Instalación

### **1. Node.js Portable (Sin permisos de administrador)**
- Ir a: https://nodejs.org/en/download/
- Descargar **"Windows Binary (.zip)"** - NO el instalador .msi
- Extraer el archivo ZIP en una carpeta de usuario (ejemplo: `C:\Users\victor.valenzuela\nodejs`)

### **2. Configurar Node.js Portable**
```powershell
# 1. Crear carpeta para Node.js en tu directorio de usuario:
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\nodejs"

# 2. Extraer el ZIP descargado en esa carpeta
# (hacer esto manualmente desde el explorador de archivos)

# 3. Agregar Node.js al PATH de la sesión actual:
$env:PATH += ";$env:USERPROFILE\nodejs"

# 4. Verificar instalación:
& "$env:USERPROFILE\nodejs\node.exe" --version
& "$env:USERPROFILE\nodejs\npm.cmd" --version
```

### **3. Alternativa: Node.js desde ZIP directo**
```powershell
# Si quiere mantenerlo en la carpeta del proyecto:
cd "C:\Users\victor.valenzuela\OneDrive - ARAUCO\Victor.valenzuela\Documentos\GradingApp"

# Crear carpeta tools
New-Item -ItemType Directory -Force -Path "tools\nodejs"

# Extraer Node.js ZIP en tools\nodejs
# Usar directamente desde ahí:
.\tools\nodejs\node.exe --version
.\tools\nodejs\npm.cmd --version
```

### **4. Configurar el Proyecto Frontend (Node.js Portable)**
```powershell
# Navegar al directorio del frontend
cd "c:\Users\victor.valenzuela\OneDrive - ARAUCO\Victor.valenzuela\Documentos\GradingApp\frontend"

# Opción 1: Si Node.js está en el directorio de usuario
$env:PATH += ";$env:USERPROFILE\nodejs"
npm install
npm run dev

# Opción 2: Si Node.js está en tools del proyecto
cd ..
.\tools\nodejs\npm.cmd install --prefix frontend
.\tools\nodejs\npm.cmd run dev --prefix frontend

# Opción 3: Crear scripts de conveniencia (recomendado)
# Ver sección de scripts más abajo
```

## 🚀 Comandos para Iniciar el Sistema Completo

### **Terminal 1 - Backend:**
```powershell
cd "c:\Users\victor.valenzuela\OneDrive - ARAUCO\Victor.valenzuela\Documentos\GradingApp\backend"

# Activar entorno virtual
.venv\Scripts\activate

# Iniciar servidor (opción simple mientras se resuelve FastAPI)
python simple_server.py
```

### **Terminal 2 - Frontend (Node.js Portable):**
```powershell
cd "c:\Users\victor.valenzuela\OneDrive - ARAUCO\Victor.valenzuela\Documentos\GradingApp\frontend"

# Opción 1: Node.js en directorio usuario
$env:PATH += ";$env:USERPROFILE\nodejs"
npm run dev

# Opción 2: Node.js en tools del proyecto  
cd ..
.\tools\nodejs\npm.cmd run dev --prefix frontend

# Opción 3: Usar script de conveniencia
.\start-frontend.bat
```

## 🛠️ Scripts de Conveniencia (Recomendado)

Crear estos archivos .bat en la raíz del proyecto para facilitar el uso:

### **start-backend.bat**
```batch
@echo off
cd backend
call .venv\Scripts\activate
python simple_server.py
```

### **start-frontend.bat**
```batch
@echo off
cd frontend
set PATH=%USERPROFILE%\nodejs;%PATH%
npm run dev
```

### **install-frontend.bat**
```batch
@echo off
cd frontend
set PATH=%USERPROFILE%\nodejs;%PATH%
npm install
```

## 🌐 URLs de Acceso
- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs

## 📱 Pruebas a Realizar

### **1. Navegación:**
- ✅ Dashboard inicial
- ✅ Nueva Inspección (4 pasos)
- ✅ Lista de Inspecciones
- ✅ Detalle de Inspección

### **2. Funcionalidad Móvil:**
- ✅ Abrir herramientas de desarrollador (F12)
- ✅ Cambiar a vista móvil/tablet
- ✅ Probar navegación touch
- ✅ Verificar responsividad

### **3. Flujo de Inspección:**
- ✅ Crear nueva inspección paso a paso
- ✅ Verificar cálculos automáticos
- ✅ Guardar y ver en lista
- ✅ Abrir detalle completo

## ⚠️ Solución de Problemas

### **Error: 'nvm' no se reconoce**
```powershell
# 1. Cerrar todas las terminales
# 2. Abrir nueva terminal como Administrador
# 3. Verificar variables de entorno:
echo $env:NVM_HOME
echo $env:NVM_SYMLINK

# 4. Si están vacías, reinstalar nvm-windows
```

### **Error: 'npm' no se reconoce**
```powershell
# Verificar que Node.js esté activo:
nvm current

# Activar una versión específica:
nvm use 20.10.0

# Reiniciar terminal si es necesario
```

### **Error: Python no encontrado**
```powershell
# Verificar entorno virtual:
.venv\Scripts\activate

# O usar Python directamente:
python --version
```

### **Puerto ya en uso:**
```powershell
# Para frontend (cambiar puerto):
npm run dev -- --port 3000

# Para backend:
# Cambiar puerto en simple_server.py (línea con port=8000)
```

## 🎉 Resultado Esperado

Una vez completada la instalación, tendrás:
- **✅ Sistema completo funcionando**
- **📱 Interfaz móvil optimizada**
- **🔄 Formulario de 4 pasos**
- **📊 Dashboard con estadísticas**
- **🗄️ Conexión con Supabase**

El sistema estará listo para **uso en producción** en tablets y dispositivos móviles para inspecciones de terreno.

---

**🚀 Una vez instalado Node.js, el frontend moderno estará completamente operativo!**