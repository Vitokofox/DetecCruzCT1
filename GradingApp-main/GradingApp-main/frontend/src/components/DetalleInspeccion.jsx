import React, { useState, useEffect } from 'react'
import { ArrowLeft, Calendar, User, Package, BarChart3, AlertTriangle } from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

const API_URL = 'http://127.0.0.1:8000/api/v1'

import { useNavigate } from 'react-router-dom'

function DetalleInspeccion({ inspeccion }) {
  const navigate = useNavigate()
  const onVolver = () => navigate('/inspecciones')

  const [distribucionGrado, setDistribucionGrado] = useState([])
  const [defectos, setDefectos] = useState([])
  const [totales, setTotales] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!inspeccion) {
      // Si se recarga la página en detalle, no tenemos la inspección en props.
      // Aquí deberíamos cargarla por ID desde la URL, pero por ahora volvemos a la lista.
      // TODO: Implementar carga individual por ID desde URL params
      navigate('/inspecciones')
    } else {
      cargarDatosCompletos()
    }
  }, [inspeccion, navigate])

  const cargarDatosCompletos = async () => {
    try {
      setLoading(true)

      // Cargar distribución de grado
      const distribResponse = await fetch(`${API_URL}/distribucion-grado?inspeccion_id=${inspeccion.id}`)
      if (distribResponse.ok) {
        const distribData = await distribResponse.json()
        setDistribucionGrado(distribData)
      }

      // Cargar defectos
      const defectosResponse = await fetch(`${API_URL}/tipificacion-defectos?inspeccion_id=${inspeccion.id}`)
      if (defectosResponse.ok) {
        const defectosData = await defectosResponse.json()
        setDefectos(defectosData)
      }

      // Cargar totales
      const totalesResponse = await fetch(`${API_URL}/totales?inspeccion_id=${inspeccion.id}`)
      if (totalesResponse.ok) {
        const totalesData = await totalesResponse.json()
        if (totalesData.length > 0) {
          setTotales(totalesData[0])
        }
      }

    } catch (error) {
      console.error('Error al cargar datos completos:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatearFecha = (fecha) => {
    if (!fecha) return 'Sin fecha'
    try {
      return format(new Date(fecha), 'dd/MM/yyyy HH:mm', { locale: es })
    } catch {
      return 'Fecha inválida'
    }
  }

  if (!inspeccion) {
    return (
      <div className="error-state">
        <p>No se encontró la inspección</p>
        <button onClick={onVolver} className="btn-back">Volver</button>
      </div>
    )
  }

  return (
    <div className="detalle-inspeccion">
      <div className="header-section">
        <button onClick={onVolver} className="btn-back">
          <ArrowLeft size={20} />
          Volver
        </button>
        <h2>📄 Detalle de Inspección</h2>
      </div>

      {loading ? (
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Cargando datos completos...</p>
        </div>
      ) : (
        <div className="detalle-content">
          {/* Información General */}
          <section className="seccion-detalle">
            <h3>
              <Package size={20} />
              Información General
            </h3>

            <div className="info-grid">
              <div className="info-item">
                <label>Lote:</label>
                <span>{inspeccion.lote || 'Sin especificar'}</span>
              </div>

              <div className="info-item">
                <label>Área:</label>
                <span>{inspeccion.area || 'Sin especificar'}</span>
              </div>

              <div className="info-item">
                <label>Producto:</label>
                <span>{inspeccion.producto || 'Sin especificar'}</span>
              </div>

              <div className="info-item">
                <label>Mercado:</label>
                <span>{inspeccion.mercado || 'Sin especificar'}</span>
              </div>

              <div className="info-item">
                <label>Terminación:</label>
                <span>{inspeccion.terminacion || 'Sin especificar'}</span>
              </div>

              <div className="info-item">
                <label>Turno:</label>
                <span>{inspeccion.turno || 'Sin especificar'}</span>
              </div>

              <div className="info-item">
                <label>Jornada:</label>
                <span>{inspeccion.jornada || 'Sin especificar'}</span>
              </div>

              <div className="info-item">
                <label>Máquina:</label>
                <span>{inspeccion.maquina || 'Sin especificar'}</span>
              </div>

              <div className="info-item">
                <label>Origen:</label>
                <span>{inspeccion.origen || 'Sin especificar'}</span>
              </div>
            </div>
          </section>

          {/* Fechas y Personal */}
          <section className="seccion-detalle">
            <h3>
              <Calendar size={20} />
              Fechas y Personal
            </h3>

            <div className="info-grid">
              <div className="info-item">
                <label>Fecha de Inspección:</label>
                <span>{formatearFecha(inspeccion.fecha_inspeccion)}</span>
              </div>

              <div className="info-item">
                <label>Fecha de Producción:</label>
                <span>{formatearFecha(inspeccion.fecha_produccion)}</span>
              </div>

              <div className="info-item">
                <label>Supervisor:</label>
                <span>{inspeccion.supervisor || 'Sin asignar'}</span>
              </div>

              <div className="info-item">
                <label>Responsable:</label>
                <span>{inspeccion.responsable || 'Sin asignar'}</span>
              </div>
            </div>
          </section>

          {/* Dimensiones y Cantidades */}
          <section className="seccion-detalle">
            <h3>
              <BarChart3 size={20} />
              Dimensiones y Cantidades
            </h3>

            <div className="info-grid">
              <div className="info-item">
                <label>Piezas Inspeccionadas:</label>
                <span className="cantidad-destacada">
                  {inspeccion.pzas_inspeccionadas || 0}
                </span>
              </div>

              <div className="info-item">
                <label>Escuadría:</label>
                <span>{inspeccion.escuadria || 'Sin especificar'}</span>
              </div>

              <div className="info-item">
                <label>Espesor:</label>
                <span>{inspeccion.espesor ? `${inspeccion.espesor} mm` : 'Sin especificar'}</span>
              </div>

              <div className="info-item">
                <label>Ancho:</label>
                <span>{inspeccion.ancho ? `${inspeccion.ancho} mm` : 'Sin especificar'}</span>
              </div>

              <div className="info-item">
                <label>Largo:</label>
                <span>{inspeccion.largo ? `${inspeccion.largo} mm` : 'Sin especificar'}</span>
              </div>
            </div>

            {inspeccion.largo && inspeccion.ancho && inspeccion.espesor && (
              <div className="dimensiones-completas">
                📏 Dimensiones completas: {inspeccion.largo} × {inspeccion.ancho} × {inspeccion.espesor} mm
              </div>
            )}
          </section>

          {/* Distribución por Grado */}
          {distribucionGrado.length > 0 && (
            <section className="seccion-detalle">
              <h3>
                <BarChart3 size={20} />
                Distribución por Grado
              </h3>

              <div className="distribucion-grados">
                {distribucionGrado.map((item, index) => (
                  <div key={index} className="grado-item">
                    <div className={`grado-label grado-${item.grado?.toLowerCase()}`}>
                      {item.grado}
                    </div>
                    <div className="grado-datos">
                      <span className="cantidad">{item.cant_piezas || 0} piezas</span>
                      <span className="porcentaje">{item.porcentaje || 0}%</span>
                    </div>
                    <div className="barra-progreso">
                      <div
                        className="progreso"
                        style={{ width: `${item.porcentaje || 0}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Defectos */}
          {defectos.length > 0 && (
            <section className="seccion-detalle">
              <h3>
                <AlertTriangle size={20} />
                Tipificación de Defectos
              </h3>

              <div className="defectos-lista">
                {defectos.map((defecto, index) => (
                  <div key={index} className="defecto-item">
                    <div className="defecto-nombre">
                      {defecto.defecto}
                    </div>
                    <div className="defecto-datos">
                      <span className="cantidad">{defecto.cant_piezas || 0} piezas</span>
                      <span className="porcentaje">{defecto.porcentaje || 0}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Totales */}
          {totales && (
            <section className="seccion-detalle">
              <h3>
                <BarChart3 size={20} />
                Totales
              </h3>

              <div className="totales-grid">
                <div className="total-item positivo">
                  <label>En Grado:</label>
                  <div className="total-valor">
                    <span className="cantidad">{totales.en_grado || 0}</span>
                    <span className="porcentaje">({totales.porc_en_grado || 0}%)</span>
                  </div>
                </div>

                <div className="total-item negativo">
                  <label>Rechazo:</label>
                  <div className="total-valor">
                    <span className="cantidad">{totales.rechazo || 0}</span>
                    <span className="porcentaje">({totales.porc_rechazo || 0}%)</span>
                  </div>
                </div>
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  )
}

export default DetalleInspeccion