from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.proyecto_service import *

router = APIRouter(prefix="/proyectos", tags=["Proyectos"])


@router.post("/")
async def crear(data: dict, db: AsyncSession = Depends(get_db)):
    return await crear_proyecto(db, data)


@router.get("/")
async def listar(db: AsyncSession = Depends(get_db)):
    return await listar_proyectos(db)