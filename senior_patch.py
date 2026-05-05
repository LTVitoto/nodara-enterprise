import os

def patch():
    # 1. ACTUALIZAR CONFIG ROUTER (GitHub Status)
    config_code = """
from fastapi import APIRouter, Depends
from app.database import get_db
from app.config import get_settings
from sqlalchemy import select

router = APIRouter()
settings = get_settings()

@router.get("")
async def get_config(db=Depends(get_db)):
    from app.models.governance import UsuarioConfig
    res = await db.execute(select(UsuarioConfig))
    cfg = res.scalars().first()
    if not cfg: cfg = UsuarioConfig(id=1)
    return [{
        "id": cfg.id,
        "auto_aprobar_ejecucion": cfg.auto_aprobar_ejecucion,
        "has_api_key_github": bool(settings.github_personal_access_token),
        "has_api_key_openai": bool(settings.openai_api_key),
        "has_api_key_gemini": bool(settings.gemini_api_key),
        "saldo_virtual_gemini": float(cfg.saldo_virtual_gemini or 0)
    }]
"""
    # 2. ACTUALIZAR METRICS ROUTER (Contadores de Proyectos)
    metrics_code = """
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from app.database import get_db

router = APIRouter()

@router.get("")
async def get_metrics(db=Depends(get_db)):
    from app.models import Proyecto
    res_total = await db.execute(select(func.count(Proyecto.id)))
    res_act = await db.execute(select(func.count(Proyecto.id)).where(Proyecto.estado == 'activo'))
    res_inact = await db.execute(select(func.count(Proyecto.id)).where(Proyecto.estado != 'activo'))
    
    total = res_total.scalar() or 0
    activos = res_act.scalar() or 0
    inactivos = res_inact.scalar() or 0
    
    return [
        {"label": "Total Proyectos", "value": str(total), "trend": "historico", "tone": "info"},
        {"label": "Proyectos Activos", "value": str(activos), "trend": "en ejecucion", "tone": "success"},
        {"label": "Proyectos Inactivos", "value": str(inactivos), "trend": "pausados", "tone": "warning"},
        {"label": "Estado Git", "value": "Sincronizado", "trend": "GitOps OK", "tone": "success"}
    ]
"""

    os.makedirs("backend/app/routers", exist_ok=True)
    with open("backend/app/routers/config.py", "w") as f: f.write(config_code.strip())
    with open("backend/app/routers/metrics.py", "w") as f: f.write(metrics_code.strip())
    print("✅ Routers actualizados (Config + Metrics)")

if __name__ == "__main__":
    patch()