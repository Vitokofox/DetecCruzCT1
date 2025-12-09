import React, { useState } from 'react'
import { ArrowLeft, Save, Plus, Minus } from 'lucide-react'

const API_URL = 'http://127.0.0.1:8000/api/v1'

const GRADOS_DISPONIBLES = ['A', 'B', 'C', 'D', 'RECHAZO']
const DEFECTOS_COMUNES = [
  'Nudos', 'Grietas', 'Deformaciones', 'Manchas',
  'Pudriciones', 'Perforaciones', 'Otros'
]
const AREAS = ['Aserrío', 'Secado', 'Elaboración', 'Clasificación']
const TURNOS = ['Mañana', 'Tarde', 'Noche']

import { useNavigate } from 'react-router-dom'

function NuevaInspeccion({ onInspeccionCreada }) {
  const navigate = useNavigate()
  const onCancelar = () => navigate('/')

  const [inspeccionData, setInspeccionData] = useState({
    fecha_inspeccion: new Date().toISOString().slice(0, 16),
    fecha_produccion: new Date().toISOString().slice(0, 16),
    area: 'Clasificación',
    supervisor: '',
    responsable: '',
    lote: '',
    mercado: '',
    producto: '',
    terminacion: '',
    turno: 'Mañana',
    jornada: 'Regular',
    pzas_inspeccionadas: '',
    escuadria: '',
    espesor: '',
    ancho: '',
    largo: '',
    maquina: '',
    origen: ''
  })

  const [distribucionGrado, setDistribucionGrado] = useState([
    { grado: 'A', cant_piezas: '', porcentaje: 0 },
    { grado: 'B', cant_piezas: '', porcentaje: 0 },
    { grado: 'C', cant_piezas: '', porcentaje: 0 },
    { grado: 'D', cant_piezas: '', porcentaje: 0 },
    { grado: 'RECHAZO', cant_piezas: '', porcentaje: 0 }
  ])

  const [defectos, setDefectos] = useState([{ defecto: '', cant_piezas: '', porcentaje: 0 }])

  const [totales, setTotales] = useState({
    en_grado: '',
    rechazo: '',
    porc_en_grado: 0,
    porc_rechazo: 0
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [mensaje, setMensaje] = useState('')
  const [paso, setPaso] = useState(1) // 1: Inspección, 2: Distribución, 3: Defectos, 4: Totales

  const calcularPorcentajes = () => {
    const totalInspeccionadas = parseInt(inspeccionData.pzas_inspeccionadas) || 0

    // Calcular porcentajes de distribución de grado
    const nuevaDistribucion = distribucionGrado.map(item => {
      const cantidad = parseInt(item.cant_piezas) || 0
      const porcentaje = totalInspeccionadas > 0 ? (cantidad / totalInspeccionadas * 100).toFixed(1) : 0
      return { ...item, porcentaje: parseFloat(porcentaje) }
    })
    setDistribucionGrado(nuevaDistribucion)

    // Calcular porcentajes de defectos
    const nuevosDefectos = defectos.map(item => {
      const cantidad = parseInt(item.cant_piezas) || 0
      const porcentaje = totalInspeccionadas > 0 ? (cantidad / totalInspeccionadas * 100).toFixed(1) : 0
      return { ...item, porcentaje: parseFloat(porcentaje) }
    })
    setDefectos(nuevosDefectos)

    // Calcular totales
    const enGrado = parseInt(totales.en_grado) || 0
    const rechazo = parseInt(totales.rechazo) || 0
    const porcEnGrado = totalInspeccionadas > 0 ? (enGrado / totalInspeccionadas * 100).toFixed(1) : 0
    const porcRechazo = totalInspeccionadas > 0 ? (rechazo / totalInspeccionadas * 100).toFixed(1) : 0

    setTotales({
      ...totales,
      porc_en_grado: parseFloat(porcEnGrado),
      porc_rechazo: parseFloat(porcRechazo)
    })
  }

  const agregarDefecto = () => {
    setDefectos([...defectos, { defecto: '', cant_piezas: '', porcentaje: 0 }])
  }

  const eliminarDefecto = (index) => {
    if (defectos.length > 1) {
      const nuevosDefectos = defectos.filter((_, i) => i !== index)
      setDefectos(nuevosDefectos)
    }
  }

  const handleInspeccionChange = (e) => {
    const { name, value } = e.target
    setInspeccionData(prev => ({ ...prev, [name]: value }))
  }

  const handleDistribucionChange = (index, field, value) => {
    const nuevaDistribucion = [...distribucionGrado]
    nuevaDistribucion[index][field] = value
    setDistribucionGrado(nuevaDistribucion)
  }

  const handleDefectoChange = (index, field, value) => {
    const nuevosDefectos = [...defectos]
    nuevosDefectos[index][field] = value
    setDefectos(nuevosDefectos)
  }

  const handleTotalesChange = (field, value) => {
    setTotales(prev => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async () => {
    setIsSubmitting(true)
    setMensaje('')

    try {
      // 1. Crear inspección principal
      const inspeccionPayload = {
        ...inspeccionData,
        fecha_inspeccion: typeof inspeccionData.fecha_inspeccion === 'string' ? inspeccionData.fecha_inspeccion : new Date(inspeccionData.fecha_inspeccion).toISOString(),
        fecha_produccion: typeof inspeccionData.fecha_produccion === 'string' ? inspeccionData.fecha_produccion : new Date(inspeccionData.fecha_produccion).toISOString(),
        pzas_inspeccionadas: parseInt(inspeccionData.pzas_inspeccionadas) || null,
        espesor: parseFloat(inspeccionData.espesor) || null,
        ancho: parseFloat(inspeccionData.ancho) || null,
        largo: parseFloat(inspeccionData.largo) || null
      }

      const inspeccionResponse = await fetch(`${API_URL}/inspecciones`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(inspeccionPayload)
      })

      if (!inspeccionResponse.ok) {
        throw new Error('Error al crear la inspección')
      }

      const inspeccionCreada = await inspeccionResponse.json()
      const inspeccionId = inspeccionCreada.id

      // 2. Crear distribución de grado
      for (const dist of distribucionGrado) {
        if (dist.cant_piezas) {
          await fetch(`${API_URL}/distribucion-grado`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              inspeccion_id: inspeccionId,
              grado: dist.grado,
              cant_piezas: parseInt(dist.cant_piezas),
              porcentaje: dist.porcentaje
            })
          })
        }
      }

      // 3. Crear tipificación de defectos
      for (const defecto of defectos) {
        if (defecto.defecto && defecto.cant_piezas) {
          await fetch(`${API_URL}/tipificacion-defectos`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              inspeccion_id: inspeccionId,
              defecto: defecto.defecto,
              cant_piezas: parseInt(defecto.cant_piezas),
              porcentaje: defecto.porcentaje
            })
          })
        }
      }

      // 4. Crear totales
      if (totales.en_grado || totales.rechazo) {
        await fetch(`${API_URL}/totales`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            inspeccion_id: inspeccionId,
            en_grado: parseInt(totales.en_grado) || null,
            rechazo: parseInt(totales.rechazo) || null,
            porc_en_grado: totales.porc_en_grado,
            porc_rechazo: totales.porc_rechazo
          })
        })
      }

      setMensaje('✅ Inspección completa creada exitosamente')
      setTimeout(() => {
        onInspeccionCreada && onInspeccionCreada()
      }, 1500)

    } catch (error) {
      setMensaje(`❌ Error: ${error.message}`)
    } finally {
      setIsSubmitting(false)
    }
  }

  const renderPaso1 = () => (
    <div className="paso-container">
      <h3>📋 Datos de la Inspección</h3>

      <div className="form-grid">
        <div className="form-group">
          <label>Fecha de Inspección</label>
          <input
            type="datetime-local"
            name="fecha_inspeccion"
            value={inspeccionData.fecha_inspeccion}
            onChange={handleInspeccionChange}
          />
        </div>

        <div className="form-group">
          <label>Fecha de Producción</label>
          <input
            type="datetime-local"
            name="fecha_produccion"
            value={inspeccionData.fecha_produccion}
            onChange={handleInspeccionChange}
          />
        </div>

        <div className="form-group">
          <label>Área</label>
          <select name="area" value={inspeccionData.area} onChange={handleInspeccionChange}>
            {AREAS.map(area => (
              <option key={area} value={area}>{area}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Supervisor</label>
          <input
            type="text"
            name="supervisor"
            value={inspeccionData.supervisor}
            onChange={handleInspeccionChange}
            placeholder="Nombre del supervisor"
          />
        </div>

        <div className="form-group">
          <label>Responsable</label>
          <input
            type="text"
            name="responsable"
            value={inspeccionData.responsable}
            onChange={handleInspeccionChange}
            placeholder="Responsable de la inspección"
          />
        </div>

        <div className="form-group">
          <label>Lote</label>
          <input
            type="text"
            name="lote"
            value={inspeccionData.lote}
            onChange={handleInspeccionChange}
            placeholder="Número de lote"
          />
        </div>

        <div className="form-group">
          <label>Mercado</label>
          <input
            type="text"
            name="mercado"
            value={inspeccionData.mercado}
            onChange={handleInspeccionChange}
            placeholder="Mercado destino"
          />
        </div>

        <div className="form-group">
          <label>Producto</label>
          <input
            type="text"
            name="producto"
            value={inspeccionData.producto}
            onChange={handleInspeccionChange}
            placeholder="Tipo de producto"
          />
        </div>

        <div className="form-group">
          <label>Terminación</label>
          <input
            type="text"
            name="terminacion"
            value={inspeccionData.terminacion}
            onChange={handleInspeccionChange}
            placeholder="Tipo de terminación"
          />
        </div>

        <div className="form-group">
          <label>Turno</label>
          <select name="turno" value={inspeccionData.turno} onChange={handleInspeccionChange}>
            {TURNOS.map(turno => (
              <option key={turno} value={turno}>{turno}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Jornada</label>
          <input
            type="text"
            name="jornada"
            value={inspeccionData.jornada}
            onChange={handleInspeccionChange}
            placeholder="Tipo de jornada"
          />
        </div>

        <div className="form-group">
          <label>Piezas Inspeccionadas</label>
          <input
            type="number"
            name="pzas_inspeccionadas"
            value={inspeccionData.pzas_inspeccionadas}
            onChange={handleInspeccionChange}
            placeholder="Cantidad total"
          />
        </div>

        <div className="form-group">
          <label>Escuadría</label>
          <input
            type="text"
            name="escuadria"
            value={inspeccionData.escuadria}
            onChange={handleInspeccionChange}
            placeholder="Ej: 2x4"
          />
        </div>

        <div className="form-group">
          <label>Espesor (mm)</label>
          <input
            type="number"
            name="espesor"
            step="0.1"
            value={inspeccionData.espesor}
            onChange={handleInspeccionChange}
            placeholder="Espesor en mm"
          />
        </div>

        <div className="form-group">
          <label>Ancho (mm)</label>
          <input
            type="number"
            name="ancho"
            step="0.1"
            value={inspeccionData.ancho}
            onChange={handleInspeccionChange}
            placeholder="Ancho en mm"
          />
        </div>

        <div className="form-group">
          <label>Largo (mm)</label>
          <input
            type="number"
            name="largo"
            step="0.1"
            value={inspeccionData.largo}
            onChange={handleInspeccionChange}
            placeholder="Largo en mm"
          />
        </div>

        <div className="form-group">
          <label>Máquina</label>
          <input
            type="text"
            name="maquina"
            value={inspeccionData.maquina}
            onChange={handleInspeccionChange}
            placeholder="ID o nombre de máquina"
          />
        </div>

        <div className="form-group">
          <label>Origen</label>
          <input
            type="text"
            name="origen"
            value={inspeccionData.origen}
            onChange={handleInspeccionChange}
            placeholder="Origen del material"
          />
        </div>
      </div>
    </div>
  )

  const renderPaso2 = () => (
    <div className="paso-container">
      <h3>📊 Distribución por Grado</h3>
      <div className="distribucion-grid">
        {distribucionGrado.map((item, index) => (
          <div key={item.grado} className="grado-row">
            <label className={`grado-label grado-${item.grado.toLowerCase()}`}>
              {item.grado}
            </label>
            <input
              type="number"
              placeholder="Cantidad"
              value={item.cant_piezas}
              onChange={(e) => handleDistribucionChange(index, 'cant_piezas', e.target.value)}
            />
            <span className="porcentaje">{item.porcentaje}%</span>
          </div>
        ))}
      </div>
      <button
        type="button"
        onClick={calcularPorcentajes}
        className="calc-btn"
      >
        Calcular Porcentajes
      </button>
    </div>
  )

  const renderPaso3 = () => (
    <div className="paso-container">
      <h3>🔍 Tipificación de Defectos</h3>
      {defectos.map((defecto, index) => (
        <div key={index} className="defecto-row">
          <select
            value={defecto.defecto}
            onChange={(e) => handleDefectoChange(index, 'defecto', e.target.value)}
          >
            <option value="">Seleccionar defecto...</option>
            {DEFECTOS_COMUNES.map(def => (
              <option key={def} value={def}>{def}</option>
            ))}
          </select>
          <input
            type="number"
            placeholder="Cantidad"
            value={defecto.cant_piezas}
            onChange={(e) => handleDefectoChange(index, 'cant_piezas', e.target.value)}
          />
          <span className="porcentaje">{defecto.porcentaje}%</span>
          <button
            type="button"
            onClick={() => eliminarDefecto(index)}
            className="btn-eliminar"
            disabled={defectos.length === 1}
          >
            <Minus size={16} />
          </button>
        </div>
      ))}
      <div className="defectos-actions">
        <button type="button" onClick={agregarDefecto} className="btn-agregar">
          <Plus size={16} /> Agregar Defecto
        </button>
        <button type="button" onClick={calcularPorcentajes} className="calc-btn">
          Calcular Porcentajes
        </button>
      </div>
    </div>
  )

  const renderPaso4 = () => (
    <div className="paso-container">
      <h3>📈 Totales</h3>
      <div className="totales-grid">
        <div className="form-group">
          <label>En Grado</label>
          <input
            type="number"
            value={totales.en_grado}
            onChange={(e) => handleTotalesChange('en_grado', e.target.value)}
            placeholder="Cantidad en grado"
          />
          <span className="porcentaje">{totales.porc_en_grado}%</span>
        </div>

        <div className="form-group">
          <label>Rechazo</label>
          <input
            type="number"
            value={totales.rechazo}
            onChange={(e) => handleTotalesChange('rechazo', e.target.value)}
            placeholder="Cantidad rechazada"
          />
          <span className="porcentaje">{totales.porc_rechazo}%</span>
        </div>
      </div>
      <button type="button" onClick={calcularPorcentajes} className="calc-btn">
        Calcular Porcentajes
      </button>
    </div>
  )

  return (
    <div className="nueva-inspeccion">
      <div className="header-section">
        <button onClick={onCancelar} className="btn-back">
          <ArrowLeft size={20} />
          Volver
        </button>
        <h2>➕ Nueva Inspección</h2>
      </div>

      <div className="pasos-indicator">
        {[1, 2, 3, 4].map(num => (
          <div
            key={num}
            className={`paso-indicator ${paso >= num ? 'active' : ''}`}
            onClick={() => setPaso(num)}
          >
            {num}
          </div>
        ))}
      </div>

      <div className="form-container">
        {paso === 1 && renderPaso1()}
        {paso === 2 && renderPaso2()}
        {paso === 3 && renderPaso3()}
        {paso === 4 && renderPaso4()}
      </div>

      <div className="navigation-buttons">
        {paso > 1 && (
          <button
            onClick={() => setPaso(paso - 1)}
            className="btn-prev"
          >
            Anterior
          </button>
        )}

        {paso < 4 ? (
          <button
            onClick={() => setPaso(paso + 1)}
            className="btn-next"
          >
            Siguiente
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            className="btn-submit"
            disabled={isSubmitting}
          >
            <Save size={20} />
            {isSubmitting ? 'Guardando...' : 'Guardar Inspección'}
          </button>
        )}
      </div>

      {mensaje && (
        <div className={`mensaje ${mensaje.includes('❌') ? 'error' : 'success'}`}>
          {mensaje}
        </div>
      )}
    </div>
  )
}

export default NuevaInspeccion