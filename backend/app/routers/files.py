import os
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy import select
from app.database import get_db
from app.config import get_settings
from app.models import ArchivoTemporal, Proyecto
router = APIRouter()
settings = get_settings()
@router.get('/{project_id}')
async def list_files(project_id: str, db=Depends(get_db)):
    res = await db.execute(select(ArchivoTemporal).where(ArchivoTemporal.proyecto_id == UUID(project_id)))
    return list(res.scalars().all())
@router.post('/{project_id}/upload')
async def upload_file(project_id: str, file: UploadFile = File(...), db=Depends(get_db)):
    p = await db.get(Proyecto, UUID(project_id))
    ws = settings.base_projects_dir / p.nombre_slug / '_uploads'
    ws.mkdir(parents=True, exist_ok=True)
    target = ws / file.filename
    content = await file.read()
    with open(target, 'wb') as f: f.write(content)
    obj = ArchivoTemporal(proyecto_id=UUID(project_id), nombre_archivo=file.filename, contenido_codigo='Binario', ruta_archivo=str(target), mime_type=file.content_type, size_bytes=len(content))
    db.add(obj)
    await db.commit()
    return obj
