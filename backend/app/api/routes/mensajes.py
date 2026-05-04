from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.message_service import *

router = APIRouter(prefix="/mensajes", tags=["Mensajes"])


@router.post("/")
async def crear(data: dict, db: AsyncSession = Depends(get_db)):
    return await crear_mensaje(db, data)