from __future__ import annotations

import os
from pathlib import Path
from uuid import UUID

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.schemas import ArchivoTemporalOut
from app.services.filesystem_guard import safe_join

router = APIRouter()
settings = get_settings()

TEXT_MIME_PREFIXES = ("text/",)
TEXT_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".json", ".html", ".css", ".md", ".txt", ".yml", ".yaml", ".csv"}


def should_inline(filename: str, mime_type: str | None, size_bytes: int) -> bool:
    from app.models import ArchivoTemporal, Proyecto
    suffix = Path(filename).suffix.lower()
    is_text = (mime_type or "").startswith(TEXT_MIME_PREFIXES) or suffix in TEXT_EXTENSIONS
    return is_text and size_bytes <= settings.db_inline_max_bytes


@router.post("/{proyecto_id}/upload", response_model=ArchivoTemporalOut)
async def upload_file(proyecto_id: UUID, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    from app.models import ArchivoTemporal, Proyecto
    proyecto = await db.get(Proyecto, proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    workspace = settings.base_projects_dir / proyecto.nombre_slug / "_uploads"
    workspace.mkdir(parents=True, exist_ok=True)

    filename = os.path.basename(file.filename or "archivo.bin")
    target = safe_join(workspace, filename)

    size = 0
    chunks: list[bytes] = []
    async with aiofiles.open(target, "wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            chunks.append(chunk)
            await out.write(chunk)

    raw = b"".join(chunks)
    inline_content = ""
    if should_inline(filename, file.content_type, size):
        inline_content = raw.decode("utf-8", errors="replace")

    obj = ArchivoTemporal(
        proyecto_id=proyecto_id,
        nombre_archivo=filename,
        contenido_codigo=inline_content,
        version=1,
        ruta_archivo=str(target),
        mime_type=file.content_type,
        size_bytes=size,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj
