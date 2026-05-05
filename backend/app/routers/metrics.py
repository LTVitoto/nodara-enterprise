from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
router = APIRouter()
@router.get('')
async def get_metrics(db: AsyncSession = Depends(get_db)):
    from app.models import Proyecto
    total = await db.execute(select(func.count(Proyecto.id)))
    act = await db.execute(select(func.count(Proyecto.id)).where(Proyecto.estado == 'activo'))
    inact = await db.execute(select(func.count(Proyecto.id)).where(Proyecto.estado != 'activo'))
    return [
        {'label': 'Proyectos Totales', 'value': str(total.scalar() or 0), 'tone': 'info', 'trend': 'global'},
        {'label': 'Proyectos Activos', 'value': str(act.scalar() or 0), 'tone': 'success', 'trend': 'en curso'},
        {'label': 'Proyectos Inactivos', 'value': str(inact.scalar() or 0), 'tone': 'warning', 'trend': 'pausados'}
    ]
