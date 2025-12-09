import React, { useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1/inspecciones";

export default function PruebaEnvioInspeccion() {
  const [form, setForm] = useState({
    fecha_inspeccion: "2025-11-30",
    fecha_produccion: "2025-11-29",
    area: "Corte",
    supervisor: "Juan Pérez",
    responsable: "Ana Gómez",
    lote: "L12345",
    mercado: "Nacional",
    producto: "Tablón",
    terminacion: "A",
    turno: "Noche",
    jornada: "2",
    pzas_inspeccionadas: 100,
    escuadria: "2x4",
    espesor: 2.5,
    ancho: 4.0,
    largo: 8.0,
    maquina: "M1",
    origen: "Planta Norte",
    fecha_creacion: "2025-11-30T10:00:00"
  });
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setResultado(null);
    setError(null);
    try {
      // Convertir campos numéricos
      const payload = {
        ...form,
        pzas_inspeccionadas: parseInt(form.pzas_inspeccionadas) || null,
        espesor: parseFloat(form.espesor) || null,
        ancho: parseFloat(form.ancho) || null,
        largo: parseFloat(form.largo) || null
      };
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        setResultado(data.data);
      } else {
        setError(data.error || "Error desconocido");
      }
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: "2rem auto", padding: 20, border: "1px solid #ccc", borderRadius: 8 }}>
      <h2>Prueba de envío de inspección</h2>
      <form onSubmit={handleSubmit}>
        {Object.keys(form).map((key) => (
          <div key={key} style={{ marginBottom: 12 }}>
            <label style={{ fontWeight: "bold" }}>{key}:</label>
            <input
              type="text"
              name={key}
              value={form[key]}
              onChange={handleChange}
              style={{ width: "100%", padding: 6 }}
            />
          </div>
        ))}
        <button type="submit" style={{ padding: "8px 16px", fontWeight: "bold" }}>Enviar</button>
      </form>
      {resultado && (
        <div style={{ marginTop: 20, color: "green" }}>
          <strong>Enviado correctamente:</strong>
          <pre>{JSON.stringify(resultado, null, 2)}</pre>
        </div>
      )}
      {error && (
        <div style={{ marginTop: 20, color: "red" }}>
          <strong>Error:</strong> {error}
        </div>
      )}
    </div>
  );
}
