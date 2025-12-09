
from fastapi import APIRouter, HTTPException
from typing import List
from schemas import InspeccionCreate, InspeccionUpdate, InspeccionResponse
from datetime import datetime, date
from supabase_rest import rest_client

router = APIRouter()

# ============= INSPECCIONES =============

@router.post("/inspecciones")
def crear_inspeccion(inspeccion: InspeccionCreate):
    """Crear una nueva inspección"""
    try:
        # Validación de datos
        data = inspeccion.model_dump(mode='json', exclude_unset=True)
        result = rest_client.create_inspeccion(data)
        # Serializar todos los campos tipo date y datetime
        if result:
            for key, value in result.items():
                if isinstance(value, (datetime, date)):
                    result[key] = value.isoformat()
        return {"success": True, "data": result, "error": None}
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}

@router.get("/inspecciones")
def obtener_inspecciones(skip: int = 0, limit: int = 100):
    """Obtener lista de inspecciones"""
    try:
        result = rest_client.get_inspecciones(limit=limit, offset=skip)
        return {"success": True, "data": result, "error": None}
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}

@router.get("/inspecciones/{inspeccion_id}")
def obtener_inspeccion(inspeccion_id: int):
    """Obtener una inspección específica por ID"""
    try:
        result = rest_client.get_inspeccion_by_id(inspeccion_id)
        if not result:
            return {"success": False, "data": None, "error": "Inspección no encontrada"}
        return {"success": True, "data": result, "error": None}
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}

@router.put("/inspecciones/{inspeccion_id}")
def actualizar_inspeccion(inspeccion_id: int, inspeccion_update: InspeccionUpdate):
    """Actualizar una inspección existente"""
    try:
        data = inspeccion_update.model_dump(mode='json', exclude_unset=True)
        result = rest_client.update_inspeccion(inspeccion_id, data)
        if not result:
            return {"success": False, "data": None, "error": "Inspección no encontrada"}
        return {"success": True, "data": result, "error": None}
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}

@router.delete("/inspecciones/{inspeccion_id}")
def eliminar_inspeccion(inspeccion_id: int):
    """Eliminar una inspección"""
    try:
        result = rest_client.delete_inspeccion(inspeccion_id)
        if not result:
            return {"success": False, "data": None, "error": "Inspección no encontrada"}
        return {"success": True, "data": {"message": "Inspección eliminada correctamente"}, "error": None}
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}


# ============= DISTRIBUCIÓN GRADO =============
# Endpoints eliminados. Si se requiere integración con Supabase REST, crear endpoints equivalentes usando rest_client.

# ============= TIPIFICACIÓN DEFECTOS =============
# Endpoints eliminados. Si se requiere integración con Supabase REST, crear endpoints equivalentes usando rest_client.

# ============= TOTALES =============

## Endpoints de totales y búsquedas eliminados. Si se requiere integración con Supabase REST, crear endpoints equivalentes usando rest_client.
    """Obtener inspecciones por producto"""
    inspecciones = db.query(Inspeccion).filter(Inspeccion.producto == producto).all()
    return inspecciones

## Endpoint de búsqueda por supervisor eliminado. Si se requiere integración con Supabase REST, crear endpoint equivalente usando rest_client.