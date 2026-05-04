from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class UsuarioConfigOut(BaseModel):
    id: int
    derivar_en_problemas: bool
    auto_aprobar_ejecucion: bool
    saldo_virtual_openai: float
    saldo_virtual_anthropic: float
    saldo_virtual_gemini: float
    has_api_key_openai: bool = False
    has_api_key_anthropic: bool = False
    has_api_key_gemini: bool = False

    class Config:
        from_attributes = True


class UsuarioConfigUpdate(BaseModel):
    derivar_en_problemas: Optional[bool] = None
    auto_aprobar_ejecucion: Optional[bool] = None
    api_key_openai: Optional[str] = None
    api_key_anthropic: Optional[str] = None
    api_key_gemini: Optional[str] = None


class ProyectoCreate(BaseModel):
    nombre_slug: Optional[str] = Field(default=None, max_length=100)
    titulo: str = Field(min_length=1, max_length=150)
    anio: int = Field(default_factory=lambda: datetime.now().year)
    descripcion: Optional[str] = None
    tecnologias: dict[str, Any] = Field(default_factory=dict)
    microservicios: dict[str, Any] = Field(default_factory=dict)
    instrucciones_deploy: Optional[str] = None
    github_url: Optional[str] = None
    rol_gemini: Optional[str] = None
    rol_chatgpt: Optional[str] = None
    rol_claude: Optional[str] = None
    estado: str = "activo"

    @field_validator("nombre_slug")
    @classmethod
    def normalize_slug(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return value.strip().lower().replace(" ", "_")


class ProyectoUpdate(BaseModel):
    titulo: Optional[str] = Field(default=None, max_length=150)
    anio: Optional[int] = None
    descripcion: Optional[str] = None
    tecnologias: Optional[dict[str, Any]] = None
    microservicios: Optional[dict[str, Any]] = None
    instrucciones_deploy: Optional[str] = None
    github_url: Optional[str] = None
    rol_gemini: Optional[str] = None
    rol_chatgpt: Optional[str] = None
    rol_claude: Optional[str] = None
    estado: Optional[str] = None


class ProyectoOut(BaseModel):
    id: UUID
    nombre_slug: str
    titulo: str
    anio: int
    descripcion: Optional[str]
    tecnologias: dict[str, Any]
    microservicios: dict[str, Any]
    instrucciones_deploy: Optional[str]
    github_url: Optional[str]
    rol_gemini: Optional[str]
    rol_chatgpt: Optional[str]
    rol_claude: Optional[str]
    estado: str
    fecha_creacion: datetime

    class Config:
        from_attributes = True


class ArchivoTemporalOut(BaseModel):
    id: int
    proyecto_id: UUID
    nombre_archivo: str
    contenido_codigo: str
    version: int
    fecha_creacion: datetime
    ruta_archivo: Optional[str]
    mime_type: Optional[str]
    size_bytes: Optional[int]

    class Config:
        from_attributes = True


class ApprovalOut(BaseModel):
    id: int
    proyecto_id: UUID
    usuario_config_id: int
    agente: str
    tool_name: str
    arguments_json: dict[str, Any]
    status: str
    result_json: Optional[dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class ChatMessageIn(BaseModel):
    message: str = Field(min_length=1)
    correlation_id: Optional[str] = None
