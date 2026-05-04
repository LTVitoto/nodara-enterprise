#!/bin/bash
set -e

echo "🏛️ Inyectando el Modelo de Datos de Gobernanza (HIL)..."

# 1. Crear el nuevo archivo de modelos de gobernanza
cat << 'EOF' > backend/app/models/governance.py
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB

# Se asume que Base viene de db.base según tu árbol de directorios
from app.db.base import Base 

class ToolCallStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTED = "executed"
    REJECTED = "rejected"
    FAILED = "failed"

class UsuarioConfig(Base):
    __tablename__ = "usuario_config"
    id = Column(Integer, primary_key=True, autoincrement=True)
    auto_aprobar_ejecucion = Column(Boolean, default=False)

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
EOF

# 2. Actualizar el __init__.py para exponer los modelos al resto de la App
cat << 'EOF' > backend/app/models/__init__.py
from app.models.proyecto import Proyecto
from app.models.history_models import Ejecucion, MensajeHistorial
from app.models.governance import UsuarioConfig, ToolCallPendiente, ToolCallStatus
EOF

echo "✅ Modelos de Gobernanza creados y exportados."
echo "🔄 Por favor, reinicia tu contenedor. Al ejecutar 'await init_db()', FastAPI creará estas tablas en PostgreSQL automáticamente y Uvicorn levantará 100% sano."