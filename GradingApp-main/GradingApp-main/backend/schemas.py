from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

# Schemas para Inspecciones
class InspeccionBase(BaseModel):
    fecha_inspeccion: Optional[datetime] = None
    fecha_produccion: Optional[datetime] = None
    area: Optional[str] = None
    supervisor: Optional[str] = None
    responsable: Optional[str] = None
    lote: Optional[str] = None
    mercado: Optional[str] = None
    producto: Optional[str] = None
    terminacion: Optional[str] = None
    turno: Optional[str] = None
    jornada: Optional[str] = None
    pzas_inspeccionadas: Optional[int] = None
    escuadria: Optional[str] = None
    espesor: Optional[Decimal] = None
    ancho: Optional[Decimal] = None
    largo: Optional[Decimal] = None
    maquina: Optional[str] = None
    origen: Optional[str] = None

class InspeccionCreate(InspeccionBase):
    pass

class InspeccionUpdate(BaseModel):
    fecha_inspeccion: Optional[datetime] = None
    fecha_produccion: Optional[datetime] = None
    area: Optional[str] = None
    supervisor: Optional[str] = None
    responsable: Optional[str] = None
    lote: Optional[str] = None
    mercado: Optional[str] = None
    producto: Optional[str] = None
    terminacion: Optional[str] = None
    turno: Optional[str] = None
    jornada: Optional[str] = None
    pzas_inspeccionadas: Optional[int] = None
    escuadria: Optional[str] = None
    espesor: Optional[Decimal] = None
    ancho: Optional[Decimal] = None
    largo: Optional[Decimal] = None
    maquina: Optional[str] = None
    origen: Optional[str] = None

class InspeccionResponse(InspeccionBase):
    id: int
    


# Schemas para Distribución de Grado
class DistribucionGradoBase(BaseModel):
    inspeccion_id: Optional[int] = None
    grado: Optional[str] = None
    cant_piezas: Optional[int] = None
    porcentaje: Optional[Decimal] = None

class DistribucionGradoCreate(DistribucionGradoBase):
    pass

class DistribucionGradoResponse(DistribucionGradoBase):
    id: int
    


# Schemas para Tipificación de Defectos
class TipificacionDefectosBase(BaseModel):
    inspeccion_id: Optional[int] = None
    defecto: Optional[str] = None
    cant_piezas: Optional[int] = None
    porcentaje: Optional[Decimal] = None

class TipificacionDefectosCreate(TipificacionDefectosBase):
    pass

class TipificacionDefectosResponse(TipificacionDefectosBase):
    id: int
    


# Schemas para Totales
class TotalesBase(BaseModel):
    inspeccion_id: Optional[int] = None
    en_grado: Optional[int] = None
    rechazo: Optional[int] = None
    porc_en_grado: Optional[Decimal] = None
    porc_rechazo: Optional[Decimal] = None

class TotalesCreate(TotalesBase):
    pass

class TotalesResponse(TotalesBase):
    id: int
    


# Schema completo para una inspección con todos sus datos relacionados
class InspeccionCompleta(InspeccionResponse):
    distribucion_grado: List[DistribucionGradoResponse] = []
    tipificacion_defectos: List[TipificacionDefectosResponse] = []
    totales: Optional[TotalesResponse] = None