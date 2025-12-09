# 🪵 GradingApp - Sistema de Clasificación de Madera

[![Backend](https://img.shields.io/badge/Backend-FastAPI-green)](https://fastapi.tiangolo.com/)
[![Frontend](https://img.shields.io/badge/Frontend-React-blue)](https://reactjs.org/)
[![Database](https://img.shields.io/badge/Database-Supabase-purple)](https://supabase.io/)
[![Mobile](https://img.shields.io/badge/Mobile-Optimized-orange)]()

Sistema moderno de inspección y gradeo de madera desarrollado para reemplazar procesos manuales con Excel. **Optimizado para uso en tablets y dispositivos móviles en terreno**.

## 🎯 Características Principales

- 📱 **Mobile-First**: Diseño optimizado para tablets 7"-12" (uso en terreno)
- 🔄 **Wizard de 4 pasos**: Proceso guiado completo de inspección
- 📊 **Distribución por grados**: Clasificación A, B, C, D y rechazos
- 🔍 **Tipificación de defectos**: Catalogación detallada de defectos
- 📈 **Cálculos automáticos**: Porcentajes y estadísticas en tiempo real
- ☁️ **Base de datos en la nube**: Supabase PostgreSQL
- 🔒 **Seguro para empresas**: HTTPS, sin puertos especiales
- ⚡ **API REST completa**: CRUD completo con validación

## 📁 Estructura del Proyecto

```
grading-app/
├── backend/              # API FastAPI
│   ├── main.py          # Punto de entrada
│   ├── database.py      # Configuración de base de datos
│   ├── models.py        # Modelos SQLAlchemy
│   ├── schemas.py       # Esquemas Pydantic
│   ├── routers/         # Rutas de la API
│   │   └── inspecciones.py
│   ├── requirements.txt # Dependencias Python
│   └── .env            # Variables de entorno
├── frontend/            # Aplicación React
│   ├── src/
│   │   ├── App.jsx     # Componente principal
│   │   ├── main.jsx    # Punto de entrada
│   │   └── components/
│   │       └── NuevaInspeccion.jsx
│   ├── package.json    # Dependencias Node.js
│   └── vite.config.js  # Configuración Vite
└── README.md           # Este archivo
```

## 🛠️ Instalación y Configuración

### Prerequisitos

- **Python 3.8+**
- **Node.js 18+**
- **PostgreSQL** (o cuenta Supabase)

### 1. Backend (FastAPI)

```bash
# Navegar al directorio backend
cd backend

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
# Editar .env con tus credenciales de Supabase
```

**Configurar `.env`:**
```env
DATABASE_URL=postgresql://postgres:TU_PASSWORD@db.TU_PROYECTO.supabase.co:5432/postgres
```

### 2. Frontend (React)

```bash
# Navegar al directorio frontend
cd frontend

# Instalar dependencias
npm install
```

## 🚀 Ejecución

### Backend
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en: `http://localhost:8000`
- Documentación: `http://localhost:8000/docs`

### Frontend
```bash
cd frontend
npm run dev
```

La aplicación web estará disponible en: `http://localhost:3000`

## 📊 Modelo de Datos

### Inspección
- **id**: Identificador único
- **numero_rollo**: Número del rollo inspeccionado
- **grado**: Calificación (A, B, C, D, RECHAZO)
- **inspector**: Nombre del inspector
- **largo, ancho, espesor**: Dimensiones (mm)
- **observaciones**: Comentarios adicionales
- **fecha_creacion**: Timestamp automático
- **fecha_actualizacion**: Timestamp de última modificación

## 🌐 API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/v1/inspecciones` | Crear inspección |
| `GET` | `/api/v1/inspecciones` | Listar inspecciones |
| `GET` | `/api/v1/inspecciones/{id}` | Obtener inspección |
| `PUT` | `/api/v1/inspecciones/{id}` | Actualizar inspección |
| `DELETE` | `/api/v1/inspecciones/{id}` | Eliminar inspección |
| `GET` | `/api/v1/inspecciones/rollo/{numero}` | Buscar por rollo |

## 🧪 Testing

### Backend
```bash
cd backend
python -m pytest
```

### Frontend
```bash
cd frontend
npm run test
```

## 📦 Deployment

### Backend (Railway/Heroku)
1. Crear `Procfile`:
   ```
   web: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

2. Agregar variables de entorno en la plataforma

### Frontend (Vercel/Netlify)
1. Build automático desde repositorio
2. Configurar variables de entorno para la API

## 🔧 Tecnologías Utilizadas

### Backend
- **FastAPI** - Framework web moderno
- **SQLAlchemy** - ORM
- **Pydantic** - Validación de datos
- **PostgreSQL** - Base de datos
- **Uvicorn** - Servidor ASGI

### Frontend
- **React 18** - Librería UI
- **Vite** - Build tool
- **CSS3** - Estilos modernos
- **Fetch API** - Cliente HTTP

## 📝 Licencia

Este proyecto está bajo la licencia MIT.

## 👥 Contribuir

1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📞 Soporte

Para soporte o consultas, crear un issue en el repositorio.