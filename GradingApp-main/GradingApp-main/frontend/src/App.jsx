import React, { useState, useEffect } from 'react'
import './App.css'
import NuevaInspeccion from './components/NuevaInspeccion'
import ListaInspecciones from './components/ListaInspecciones'
import DetalleInspeccion from './components/DetalleInspeccion'
import { Menu, Plus, List, Home } from 'lucide-react'
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom'

const API_URL = 'http://127.0.0.1:8000/api/v1'

function App() {
  const [inspecciones, setInspecciones] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [inspeccionSeleccionada, setInspeccionSeleccionada] = useState(null)

  const navigate = useNavigate()
  const location = useLocation()

  // Cargar inspecciones al iniciar
  useEffect(() => {
    fetchInspecciones()
  }, [])

  const fetchInspecciones = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_URL}/inspecciones`)
      if (!response.ok) {
        throw new Error('Error al cargar inspecciones')
      }
      const result = await response.json()
      if (result.success) {
        setInspecciones(result.data)
      } else {
        throw new Error(result.error || 'Error al cargar datos')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleInspeccionCreada = () => {
    fetchInspecciones()
    navigate('/inspecciones')
  }

  const verDetalle = (inspeccion) => {
    setInspeccionSeleccionada(inspeccion)
    navigate(`/inspecciones/${inspeccion.id}`)
  }

  if (loading) return (
    <div className="loading-screen">
      <div className="loading-spinner"></div>
      <p>Cargando inspecciones...</p>
    </div>
  )

  if (error) return (
    <div className="error-screen">
      <p>❌ Error: {error}</p>
      <button onClick={fetchInspecciones} className="retry-btn">Reintentar</button>
    </div>
  )

  const HomeView = () => (
    <div className="home-dashboard">
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Inspecciones</h3>
          <p className="stat-number">{inspecciones.length}</p>
        </div>
        <div className="stat-card">
          <h3>Última Inspección</h3>
          <p className="stat-text">
            {inspecciones.length > 0
              ? new Date(inspecciones[0].fecha_inspeccion || inspecciones[0].created_at).toLocaleDateString('es-CL')
              : 'Sin registros'
            }
          </p>
        </div>
      </div>

      <div className="action-buttons">
        <button
          className="action-btn primary"
          onClick={() => navigate('/nueva')}
        >
          <Plus size={24} />
          Nueva Inspección
        </button>

        <button
          className="action-btn secondary"
          onClick={() => navigate('/inspecciones')}
          disabled={inspecciones.length === 0}
        >
          <List size={24} />
          Ver Inspecciones ({inspecciones.length})
        </button>
      </div>
    </div>
  )

  return (
    <div className="App">
      <header className="app-header">
        <div className="header-content">
          <button
            className="nav-btn"
            onClick={() => navigate('/')}
            disabled={location.pathname === '/'}
          >
            <Home size={20} />
          </button>
          <h1>🪵 Grading App</h1>
          <div className="header-actions">
            <span className="connection-status online">●</span>
          </div>
        </div>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<HomeView />} />
          <Route path="/nueva" element={<NuevaInspeccion onInspeccionCreada={handleInspeccionCreada} onCancelar={() => navigate('/')} />} />
          <Route path="/inspecciones" element={<ListaInspecciones inspecciones={inspecciones} onVerDetalle={verDetalle} onVolver={() => navigate('/')} />} />
          <Route path="/inspecciones/:id" element={<DetalleInspeccion inspeccion={inspeccionSeleccionada} onVolver={() => navigate('/inspecciones')} />} />
        </Routes>
      </main>

      <div className="app-footer">
        <p>Sistema de Inspección de Madera v1.0</p>
      </div>
    </div>
  );
}

export default App