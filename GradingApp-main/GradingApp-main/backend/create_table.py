"""
Generador de SQL de referencia para la tabla 'inspecciones' en Supabase.
No ejecuta nada contra la base de datos.
Las tablas deben crearse manualmente en el panel de Supabase (SQL Editor).
"""

# SQL de referencia para crear la tabla
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS inspecciones (
    id SERIAL PRIMARY KEY,
    numero_rollo VARCHAR(50) NOT NULL,
    grado VARCHAR(10) NOT NULL,
    observaciones TEXT,
    inspector VARCHAR(100) NOT NULL,
    largo FLOAT,
    ancho FLOAT,
    espesor FLOAT,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP WITH TIME ZONE
);

-- Crear índice para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_numero_rollo ON inspecciones(numero_rollo);
CREATE INDEX IF NOT EXISTS idx_fecha_creacion ON inspecciones(fecha_creacion);

-- Agregar trigger para actualizar fecha_actualizacion
CREATE OR REPLACE FUNCTION update_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_fecha_actualizacion ON inspecciones;
CREATE TRIGGER trigger_update_fecha_actualizacion
    BEFORE UPDATE ON inspecciones
    FOR EACH ROW
    EXECUTE FUNCTION update_fecha_actualizacion();
"""

if __name__ == "__main__":
    print("📋 SQL para crear tabla de inspecciones:")
    print("="*50)
    print(CREATE_TABLE_SQL)
    print("="*50)
    print("\n🔧 Para crear la tabla:")
    print("1. Ve al panel de Supabase: https://<tu-proyecto>.supabase.co")
    print("2. Abre el 'SQL Editor'")
    print("3. Pega el SQL de arriba")
    print("4. Haz clic en 'Run'")
    print("\n💡 Una vez creada la tabla, la aplicación funcionará completamente!")

# También vamos a probar si podemos ejecutar SQL directamente
try:
    # Nota: Esto puede no funcionar con la key anónima
    # Solo referencia: para crear tablas, usa la consola de Supabase con el SQL generado.
except Exception as e:
    print(f"\n⚠️  No se puede ejecutar SQL directamente con la key anónima: {e}")
    print("📝 Usa el SQL Editor del panel de Supabase para crear la tabla")