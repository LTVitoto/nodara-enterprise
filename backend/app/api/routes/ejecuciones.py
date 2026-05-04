from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.ejecucion_service import *

router = APIRouter(prefix="/ejecuciones", tags=["Ejecuciones"])


@router.post("/")
async def crear(data: dict, db: AsyncSession = Depends(get_db)):
    return await crear_ejecucion(
        db,
        data["proyecto_id"],
        data["correlation_id"]
    )