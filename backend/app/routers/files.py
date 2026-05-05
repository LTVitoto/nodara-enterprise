import os
from uuid import UUID
import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.schemas import ArchivoTemporalOut
from app.services.filesystem_guard import safe_join

router = APIRouter()
settings = get_settings()

@router.get("/{proyecto_id}")
async def list_files(proyecto_id: str, db: AsyncSession = Depends(get_db)):
    from app.models import ArchivoTemporal
    try:
        p_id = UUID(proyecto_id)
        result = await db.execute(select(ArchivoTemporal).where(ArchivoTemporal.proyecto_id == p_id).order_by(ArchivoTemporal.fecha_creacion.desc()))
        return list(result.scalars().all())
    except Exception:
        return []

@router.post("/{proyecto_id}/upload", response_model=ArchivoTemporalOut)
async def upload_file(proyecto_id: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    from app.models import ArchivoTemporal, Proyecto
    p_id = UUID(proyecto_id)
    proyecto = await db.get(Proyecto, p_id)
    if not proyecto: raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    workspace = settings.base_projects_dir / proyecto.nombre_slug / "_uploads"
    workspace.mkdir(parents=True, exist_ok=True)
    target = safe_join(workspace, os.path.basename(file.filename or "archivo.bin"))

    size = 0
    async with aiofiles.open(target, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            await out.write(chunk)

    obj = ArchivoTemporal(
        proyecto_id=p_id, nombre_archivo=file.filename,
        contenido_codigo="Archivo binario guardado en disco", version=1,
        ruta_archivo=str(target), mime_type=file.content_type, size_bytes=size,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj
