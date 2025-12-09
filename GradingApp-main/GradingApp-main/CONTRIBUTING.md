# 🤝 Contribuyendo a GradingApp

¡Gracias por tu interés en contribuir al proyecto GradingApp! 🪵

## 🚀 Cómo Empezar

### 1. Configurar el Entorno de Desarrollo
```bash
# Clonar el repositorio
git clone https://github.com/TU_USUARIO/GradingApp.git
cd GradingApp

# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env  # Configurar variables

# Frontend  
cd ../frontend
npm install
```

### 2. Ejecutar el Proyecto
```bash
# Terminal 1 - Backend
cd backend
python simple_server.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## 📋 Tipos de Contribuciones

### ✨ Nuevas Características
- Mejoras en la interfaz móvil
- Nuevos tipos de defectos
- Reportes adicionales
- Integración con otros sistemas

### 🐛 Corrección de Bugs
- Problemas de responsividad
- Errores en cálculos
- Problemas de conexión

### 📚 Documentación
- Mejorar guías de usuario
- Actualizar documentación técnica
- Agregar ejemplos de uso

## 🔄 Proceso de Contribución

### 1. Fork y Branch
```bash
# Hacer fork del repositorio
# Crear rama para tu feature
git checkout -b feature/nueva-funcionalidad
```

### 2. Desarrollar y Probar
- Escribir código siguiendo las convenciones
- Agregar tests si aplica
- Probar en dispositivos móviles
- Verificar que el backend funcione

### 3. Commit y Push
```bash
# Commits descriptivos
git add .
git commit -m "✨ feat: agregar funcionalidad X"
git push origin feature/nueva-funcionalidad
```

### 4. Pull Request
- Crear PR con descripción detallada
- Referenciar issues relacionados
- Incluir capturas de pantalla si es UI

## 📝 Convenciones de Código

### Python (Backend)
- Seguir PEP 8
- Type hints donde sea posible
- Docstrings para funciones complejas
- Tests para nuevas funcionalidades

### JavaScript/React (Frontend)
- Usar ES6+ features
- Componentes funcionales con hooks
- PropTypes para validación
- CSS modules o styled-components

### Commits
```bash
✨ feat: nueva funcionalidad
🐛 fix: corrección de bug
📚 docs: actualización documentación
🎨 style: cambios de diseño
♻️ refactor: refactorización
⚡ perf: mejora de performance
🧪 test: agregar tests
```

## 🧪 Testing

### Backend
```bash
pytest tests/
```

### Frontend
```bash
npm test
npm run test:e2e
```

### Móvil
- Probar en Chrome DevTools (responsive)
- Verificar en tablets reales 7"-12"
- Probar gestos touch
- Validar orientación portrait/landscape

## 📱 Consideraciones Móviles

### UI/UX
- Botones mínimo 44px (touch target)
- Formularios optimizados para teclado móvil
- Loading states para conexiones lentas
- Offline mode considerations

### Performance
- Imágenes optimizadas
- Lazy loading
- Minimizar peticiones API
- Cacheo inteligente

## 🔍 Review Process

### Criterios de Revisión
- ✅ Funcionalidad correcta
- ✅ Código legible y mantenible
- ✅ Tests pasando
- ✅ Responsive design
- ✅ Performance adecuado
- ✅ Sin breaking changes

### Timeframe
- Reviews iniciales: 1-2 días hábiles
- Revisiones de follow-up: 24-48 horas
- Merge después de aprobación

## 🆘 Obtener Ayuda

### Documentación
- [docs/ESTADO_ACTUAL.md](docs/ESTADO_ACTUAL.md) - Estado del proyecto
- [docs/INSTRUCCIONES_NODEJS.md](docs/INSTRUCCIONES_NODEJS.md) - Setup Node.js
- [README.md](README.md) - Documentación principal

### Comunicación
- GitHub Issues para bugs y features
- GitHub Discussions para preguntas generales
- Email del maintainer para temas urgentes

## 🏆 Reconocimientos

Todos los contributores serán reconocidos en:
- README.md del proyecto
- Release notes
- Wall of fame en la documentación

---

**¡Gracias por ayudar a mejorar GradingApp! 🪵✨**