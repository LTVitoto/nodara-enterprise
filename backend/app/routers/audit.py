from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.audit import EventoAuditoria
router = APIRouter()
@router.get('/events')
async def get_audit(db: AsyncSession = Depends(get_db)):
    try:
        res = await db.execute(select(EventoAuditoria).order_by(EventoAuditoria.fecha_evento.desc()))
        return list(res.scalars().all())
    except:
        return []
