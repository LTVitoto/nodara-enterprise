import os

print("🔥 BLINDANDO ENDPOINT DE CONFIGURACIÓN Y VALIDACIÓN DE API KEYS...")

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"✅ Archivo corregido: {path}")

write_file("backend/app/routers/config.py", r"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.config import get_settings

router = APIRouter()
settings = get_settings()

# 🔥 FIX 1: Modelo Pydantic estricto para evitar Error 500 y Crash de FastAPI
class ConfigUpdate(BaseModel):
    auto_aprobar_ejecucion: Optional[bool] = None

# 🔥 FIX 2: Detector de placeholders en el .env
def _is_real_key(key: str) -> bool:
    if not key:
        return False
    # Si la llave contiene el texto placeholder, la marcamos como "No cargada"
    if "tu_llave" in key.lower():
        return False
    return True

def _format_config(config_obj):
    """Mapea el objeto DB al formato que espera el Frontend"""
    return {
        "id": config_obj.id,
        "derivar_en_problemas": config_obj.derivar_en_problemas,
        "auto_aprobar_ejecucion": config_obj.auto_aprobar_ejecucion,
        "saldo_virtual_openai": float(config_obj.saldo_virtual_openai) if config_obj.saldo_virtual_openai is not None else 0.0,
        "saldo_virtual_anthropic": float(config_obj.saldo_virtual_anthropic) if config_obj.saldo_virtual_anthropic is not None else 0.0,
        "saldo_virtual_gemini": float(config_obj.saldo_virtual_gemini) if config_obj.saldo_virtual_gemini is not None else 0.0,
        # Validamos contra la BD o contra el .env asegurando que no sean placeholders
        "has_api_key_openai": bool(config_obj.api_key_openai) or _is_real_key(settings.openai_api_key),
        "has_api_key_anthropic": bool(config_obj.api_key_anthropic) or _is_real_key(settings.anthropic_api_key),
        "has_api_key_gemini": bool(config_obj.api_key_gemini) or _is_real_key(settings.gemini_api_key),
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
                "has_api_key_openai": _is_real_key(settings.openai_api_key),
                "has_api_key_anthropic": _is_real_key(settings.anthropic_api_key),
                "has_api_key_gemini": _is_real_key(settings.gemini_api_key),
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
            "has_api_key_openai": _is_real_key(settings.openai_api_key),
            "has_api_key_anthropic": _is_real_key(settings.anthropic_api_key),
            "has_api_key_gemini": _is_real_key(settings.gemini_api_key),
            "error": str(e)
        }]

@router.patch("/{config_id}")
async def update_config(config_id: int, payload: ConfigUpdate, db: AsyncSession = Depends(get_db)):
    from app.models.governance import UsuarioConfig
    
    config_obj = await db.get(UsuarioConfig, config_id)
    if not config_obj:
        config_obj = UsuarioConfig(id=config_id)
        db.add(config_obj)

    # Actualización segura a través de Pydantic
    if payload.auto_aprobar_ejecucion is not None:
        config_obj.auto_aprobar_ejecucion = payload.auto_aprobar_ejecucion
            
    await db.commit()
    await db.refresh(config_obj)
    
    return _format_config(config_obj)
""")

print("🚀 SCRIPT FINALIZADO. REINICIA EL CONTENEDOR BACKEND.")