from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Proyecto, ArchivoTemporal
from app.models.history_models import MensajeHistorial
from app.models.audit import EventoAuditoria
router = APIRouter()
@router.get('')
async def get_metrics(db: AsyncSession = Depends(get_db)):
    try:
        t_p = await db.scalar(select(func.count(Proyecto.id)))
        t_m = await db.scalar(select(func.count(MensajeHistorial.id)))
        t_a = await db.scalar(select(func.count(ArchivoTemporal.id)))
        t_e = await db.scalar(select(func.count(EventoAuditoria.id)))
        return [
            {'label': 'Proyectos Activos', 'value': str(t_p or 0), 'trend': 'Real', 'tone': 'success'},
            {'label': 'Mensajes de IA', 'value': str(t_m or 0), 'trend': 'Real', 'tone': 'info'},
            {'label': 'Archivos Generados', 'value': str(t_a or 0), 'trend': 'Real', 'tone': 'warning'},
            {'label': 'Eventos Auditoría', 'value': str(t_e or 0), 'trend': 'Real', 'tone': 'danger'}
        ]
    except:
        return []
