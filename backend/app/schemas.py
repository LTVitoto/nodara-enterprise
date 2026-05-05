from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

class ProyectoCreate(BaseModel):
    nombre_slug: Optional[str] = None
    titulo: str
    anio: int = 2026
    descripcion: Optional[str] = None
    tecnologias: dict[str, Any] = {}
    microservicios: dict[str, Any] = {}
    instrucciones_deploy: Optional[str] = None
    github_url: Optional[str] = None
    rol_gemini: Optional[str] = "Experto en Infraestructura"
    rol_chatgpt: Optional[str] = "Experto en Backend"
    rol_claude: Optional[str] = "Experto en Frontend"
    estado: str = "activo"
    responsable: str = "Vitoto"

class ProyectoUpdate(BaseModel):
    titulo: Optional[str] = None
    estado: Optional[str] = None
    responsable: Optional[str] = None

class ProyectoOut(ProyectoCreate):
    id: UUID
    fecha_creacion: datetime
    class Config: from_attributes = True

class ArchivoTemporalOut(BaseModel):
    id: int
    proyecto_id: UUID
    nombre_archivo: str
    ruta_archivo: Optional[str]
    size_bytes: Optional[int]
    class Config: from_attributes = True

class ApprovalOut(BaseModel):
    id: int
    proyecto_id: UUID
    usuario_config_id: int
    agente: str
    tool_name: str
    arguments_json: dict[str, Any]
    status: str
    class Config: from_attributes = True
