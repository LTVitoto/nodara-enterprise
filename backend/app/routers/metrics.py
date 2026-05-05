from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter()

@router.get("")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    from app.models.history_models import MensajeHistorial
    from app.models import Proyecto
    res_cost = await db.execute(select(func.sum(MensajeHistorial.costo_estimado)))
    res_proj = await db.execute(select(func.count(Proyecto.id)))
    res_msg = await db.execute(select(func.count(MensajeHistorial.id)))
    
    total_cost = res_cost.scalar() or 0.0
    return [
        {"label": "Proyectos Activos", "value": str(res_proj.scalar() or 0), "tone": "info", "trend": "global"},
        {"label": "Interacciones (Mensajes)", "value": str(res_msg.scalar() or 0), "tone": "success", "trend": "runtime"},
        {"label": "Costo Histórico Total", "value": f"US$ {total_cost:.4f}", "tone": "warning", "trend": "consumo real"},
        {"label": "Ahorro Estimado HIL", "value": "14 hrs", "tone": "success", "trend": "productividad"}
    ]
