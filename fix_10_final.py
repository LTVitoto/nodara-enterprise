import os

print("🔥 INICIANDO CORRECCIÓN FINAL (MODELO CONFIG Y PATCH)...")

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"✅ Archivo corregido: {path}")

# ==========================================
# 1. FIX: MODELO DE GOBERNANZA (Incluir saldos y llaves)
# ==========================================
write_file("backend/app/models/governance.py", r"""
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
""")

# ==========================================
# 2. FIX: ENDPOINTS DE CONFIGURACIÓN
# ==========================================
write_file("backend/app/routers/config.py", r"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter()

def _format_config(config_obj):
    """Mapea el objeto DB al formato que espera el Frontend"""
    return {
        "id": config_obj.id,
        "derivar_en_problemas": config_obj.derivar_en_problemas,
        "auto_aprobar_ejecucion": config_obj.auto_aprobar_ejecucion,
        "saldo_virtual_openai": float(config_obj.saldo_virtual_openai) if config_obj.saldo_virtual_openai else 0.0,
        "saldo_virtual_anthropic": float(config_obj.saldo_virtual_anthropic) if config_obj.saldo_virtual_anthropic else 0.0,
        "saldo_virtual_gemini": float(config_obj.saldo_virtual_gemini) if config_obj.saldo_virtual_gemini else 0.0,
        "has_api_key_openai": bool(config_obj.api_key_openai),
        "has_api_key_anthropic": bool(config_obj.api_key_anthropic),
        "has_api_key_gemini": bool(config_obj.api_key_gemini),
    }

@router.get("")
async def get_config(db: AsyncSession = Depends(get_db)):
    try:
        from app.models.governance import UsuarioConfig
        result = await db.execute(select(UsuarioConfig))
        configs = result.scalars().all()
        if not configs:
            return [{
                "id": 1,
                "derivar_en_problemas": False,
                "auto_aprobar_ejecucion": False,
                "saldo_virtual_openai": 0.0,
                "saldo_virtual_anthropic": 0.0,
                "saldo_virtual_gemini": 0.0,
                "has_api_key_openai": False,
                "has_api_key_anthropic": False,
                "has_api_key_gemini": False,
            }]
        
        return [_format_config(c) for c in configs]
    except Exception as e:
        return [{
            "id": 1,
            "derivar_en_problemas": False,
            "auto_aprobar_ejecucion": False,
            "saldo_virtual_openai": 0.0,
            "saldo_virtual_anthropic": 0.0,
            "saldo_virtual_gemini": 0.0,
            "has_api_key_openai": False,
            "has_api_key_anthropic": False,
            "has_api_key_gemini": False,
            "error": str(e)
        }]

@router.patch("/{config_id}")
async def update_config(config_id: int, payload: dict, db: AsyncSession = Depends(get_db)):
    from app.models.governance import UsuarioConfig
    config_obj = await db.get(UsuarioConfig, config_id)
    if not config_obj:
        # Si no existe, lo creamos para evitar fallos (idempotente)
        config_obj = UsuarioConfig(id=config_id)
        db.add(config_obj)

    for key, value in payload.items():
        if hasattr(config_obj, key):
            setattr(config_obj, key, value)
            
    await db.commit()
    await db.refresh(config_obj)
    
    return _format_config(config_obj)
""")

print("\n🚀 LISTO. Reinicia tu contenedor Backend para aplicar los cambios a la Base de Datos.")