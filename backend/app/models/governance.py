from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base

class ToolCallStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTED = "executed"
    REJECTED = "rejected"
    FAILED = "failed"

class UsuarioConfig(Base):
    __tablename__ = "usuario_config"
    id = Column(Integer, primary_key=True, autoincrement=True)
    derivar_en_problemas = Column(Boolean, default=False)
    auto_aprobar_ejecucion = Column(Boolean, default=False)
    saldo_virtual_openai = Column(Numeric(10, 4), default=0.0000)
    saldo_virtual_anthropic = Column(Numeric(10, 4), default=0.0000)
    saldo_virtual_gemini = Column(Numeric(10, 4), default=0.0000)
    api_key_openai = Column(String(255), nullable=True)
    api_key_anthropic = Column(String(255), nullable=True)
    api_key_gemini = Column(String(255), nullable=True)

class ToolCallPendiente(Base):
    __tablename__ = "tool_call_pendiente"
    id = Column(Integer, primary_key=True, autoincrement=True)
    proyecto_id = Column(UUID(as_uuid=True), index=True)
    usuario_config_id = Column(Integer, ForeignKey("usuario_config.id"))
    agente = Column(String, nullable=False)
    tool_name = Column(String, nullable=False)
    arguments_json = Column(JSONB, default={})
    status = Column(String, default=ToolCallStatus.PENDING.value)
    result_json = Column(JSONB, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
