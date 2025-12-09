import React, { useState } from 'react'
import { ArrowLeft, Search, Calendar, Filter, Eye } from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

import { useNavigate } from 'react-router-dom'

function ListaInspecciones({ inspecciones, onVerDetalle }) {
  const navigate = useNavigate()
  const onVolver = () => navigate('/')

  const [filtro, setFiltro] = useState('')
  const [ordenarPor, setOrdenarPor] = useState('fecha_desc')

  const inspeccionesFiltradas = inspecciones
    .filter(inspeccion => {
      const termino = filtro.toLowerCase()
      return (
        inspeccion.lote?.toLowerCase().includes(termino) ||
        inspeccion.supervisor?.toLowerCase().includes(termino) ||
        inspeccion.responsable?.toLowerCase().includes(termino) ||
        inspeccion.area?.toLowerCase().includes(termino) ||
        inspeccion.producto?.toLowerCase().includes(termino)
      )
    })
    .sort((a, b) => {
      switch (ordenarPor) {
        case 'fecha_asc':
          return new Date(a.fecha_inspeccion) - new Date(b.fecha_inspeccion)
        case 'fecha_desc':
          return new Date(b.fecha_inspeccion) - new Date(a.fecha_inspeccion)
        case 'lote':
          return (a.lote || '').localeCompare(b.lote || '')
        case 'supervisor':
          return (a.supervisor || '').localeCompare(b.supervisor || '')
        default:
          return 0
      }
    })

  const formatearFecha = (fecha) => {
    if (!fecha) return 'Sin fecha'
    try {
      return format(new Date(fecha), 'dd/MM/yyyy HH:mm', { locale: es })
    } catch {
      return 'Fecha inválida'
    }
  }

  return (
    <div className="lista-inspecciones">
      <div className="header-section">
        <button onClick={onVolver} className="btn-back">
          <ArrowLeft size={20} />
          Volver
        </button>
        <h2>📋 Inspecciones ({inspeccionesFiltradas.length})</h2>
      </div>

      <div className="controles">
        <div className="busqueda">
          <Search size={20} />
          <input
            type="text"
            placeholder="Buscar por lote, supervisor, área..."
            value={filtro}
            onChange={(e) => setFiltro(e.target.value)}
          />
        </div>

        <div className="ordenar">
          <Filter size={20} />
          <select value={ordenarPor} onChange={(e) => setOrdenarPor(e.target.value)}>
            <option value="fecha_desc">Más recientes</option>
            <option value="fecha_asc">Más antiguos</option>
            <option value="lote">Por lote</option>
            <option value="supervisor">Por supervisor</option>
          </select>
        </div>
      </div>

      {inspeccionesFiltradas.length === 0 ? (
        <div className="no-data">
          {filtro ? (
            <>
              <p>No se encontraron inspecciones que coincidan con "{filtro}"</p>
              <button onClick={() => setFiltro('')} className="btn-clear">
                Limpiar filtro
              </button>
            </>
          ) : (
            <p>No hay inspecciones registradas</p>
          )}
        </div>
      ) : (
        <div className="inspecciones-grid">
          {inspeccionesFiltradas.map((inspeccion) => (
            <div key={inspeccion.id} className="inspeccion-card">
              <div className="card-header">
                <div className="card-title">
                  <strong>Lote: {inspeccion.lote || 'Sin lote'}</strong>
                  <span className="fecha">
                    <Calendar size={14} />
                    {formatearFecha(inspeccion.fecha_inspeccion)}
                  </span>
                </div>
                <button
                  onClick={() => onVerDetalle(inspeccion)}
                  className="btn-ver"
                >
                  <Eye size={16} />
                </button>
              </div>

              <div className="card-content">
                <div className="info-row">
                  <span className="label">Área:</span>
                  <span className="value">{inspeccion.area || '-'}</span>
                </div>

                <div className="info-row">
                  <span className="label">Supervisor:</span>
                  <span className="value">{inspeccion.supervisor || '-'}</span>
                </div>

                <div className="info-row">
                  <span className="label">Responsable:</span>
                  <span className="value">{inspeccion.responsable || '-'}</span>
                </div>

                <div className="info-row">
                  <span className="label">Producto:</span>
                  <span className="value">{inspeccion.producto || '-'}</span>
                </div>

                <div className="info-row">
                  <span className="label">Piezas:</span>
                  <span className="value piezas">{inspeccion.pzas_inspeccionadas || 0}</span>
                </div>

                {inspeccion.escuadria && (
                  <div className="info-row">
                    <span className="label">Escuadría:</span>
                    <span className="value">{inspeccion.escuadria}</span>
                  </div>
                )}

                <div className="dimensiones">
                  {inspeccion.largo && inspeccion.ancho && inspeccion.espesor && (
                    <span className="dimensiones-text">
                      📏 {inspeccion.largo} × {inspeccion.ancho} × {inspeccion.espesor} mm
                    </span>
                  )}
                </div>
              </div>

              <div className="card-footer">
                <span className="turno">{inspeccion.turno || 'Sin turno'}</span>
                <span className="mercado">{inspeccion.mercado || 'Sin mercado'}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default ListaInspecciones