import os, subprocess, base64, mimetypes
from uuid import UUID
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.config import get_settings
from app.schemas import ProyectoCreate, ProyectoOut
from app.services.slug import slugify
router = APIRouter()
settings = get_settings()
class ReadmeUpdate(BaseModel): content: str
@router.get('', response_model=list[ProyectoOut])
async def list_projects(db: AsyncSession = Depends(get_db)):
    from app.models import Proyecto
    res = await db.execute(select(Proyecto).order_by(Proyecto.fecha_creacion.desc()))
    return list(res.scalars().all())
@router.post('', response_model=ProyectoOut)
async def create_project(payload: ProyectoCreate, db: AsyncSession = Depends(get_db)):
    from app.models import Proyecto
    slug = payload.nombre_slug or slugify(payload.titulo)
    data = payload.model_dump()
    valid_keys = Proyecto.__table__.columns.keys()
    
    # 🎯 FIX DEFINITIVO: Evitamos explícitamente el duplicate keyword argument
    filtered_data = {k: v for k, v in data.items() if k in valid_keys and k != 'nombre_slug'}
    
    obj = Proyecto(**filtered_data, nombre_slug=slug)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    try:
        ws = settings.base_projects_dir / obj.nombre_slug
        ws.mkdir(parents=True, exist_ok=True)
        with open(ws / 'README.md', 'w', encoding='utf-8') as f: 
            f.write('# ' + obj.titulo + '\n\n' + obj.descripcion)
    except: pass
    return obj
@router.get('/{project_id}/readme')
async def get_readme(project_id: str, db: AsyncSession = Depends(get_db)):
    from app.models import Proyecto
    p = await db.get(Proyecto, UUID(project_id))
    path = settings.base_projects_dir / p.nombre_slug / 'README.md'
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f: return {'content': f.read()}
    return {'content': 'Sin README.'}
@router.patch('/{project_id}/readme')
async def update_readme(project_id: str, payload: ReadmeUpdate, db: AsyncSession = Depends(get_db)):
    from app.models import Proyecto
    p = await db.get(Proyecto, UUID(project_id))
    ws = settings.base_projects_dir / p.nombre_slug
    with open(ws / 'README.md', 'w', encoding='utf-8') as f: f.write(payload.content)
    return {'status': 'ok'}
@router.get('/{project_id}/workspace/file')
async def read_file(project_id: str, file_path: str, db: AsyncSession = Depends(get_db)):
    from app.models import Proyecto
    p = await db.get(Proyecto, UUID(project_id))
    fp = Path(file_path)
    if not fp.is_file():
        fp = settings.base_projects_dir / p.nombre_slug / file_path.lstrip('./').lstrip('/')
    if not fp.is_file(): return {'content': 'Archivo no leible o no existe.', 'is_image': False}
    mime_type, _ = mimetypes.guess_type(str(fp))
    if mime_type and mime_type.startswith('image/'):
        with open(fp, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
            return {'content': f'data:{mime_type};base64,{b64}', 'is_image': True}
    with open(fp, 'r', encoding='utf-8', errors='replace') as f: 
        return {'content': f.read(), 'is_image': False}
@router.get('/{project_id}/workspace/tree')
async def get_tree(project_id: str, db: AsyncSession = Depends(get_db)):
    from app.models import Proyecto
    p = await db.get(Proyecto, UUID(project_id))
    b = settings.base_projects_dir / p.nombre_slug
    if not b.exists(): return []
    def bt(path):
        n = os.path.basename(path)
        if os.path.isdir(path):
            return {'id': path, 'name': n, 'type': 'folder', 'path': path, 'children': [bt(os.path.join(path, x)) for x in os.listdir(path) if not x.startswith('.git')]}
        return {'id': path, 'name': n, 'type': 'file', 'path': path}
    return [bt(os.path.join(b, x)) for x in os.listdir(b) if not x.startswith('.git')]
@router.get('/{project_id}/messages')
async def get_msgs(project_id: str, db: AsyncSession = Depends(get_db)):
    from app.models.history_models import MensajeHistorial
    try:
        r = await db.execute(select(MensajeHistorial).where(MensajeHistorial.proyecto_id == UUID(project_id)).order_by(MensajeHistorial.fecha_envio.asc()))
        return list(r.scalars().all())
    except: return []
@router.get('/{project_id}', response_model=ProyectoOut)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    from app.models import Proyecto
    obj = await db.get(Proyecto, UUID(project_id))
    if not obj: raise HTTPException(404)
    return obj
@router.patch('/{project_id}', response_model=ProyectoOut)
async def update_project(project_id: str, payload: dict, db: AsyncSession = Depends(get_db)):
    from app.models import Proyecto
    obj = await db.get(Proyecto, UUID(project_id))
    valid_keys = Proyecto.__table__.columns.keys()
    for k, v in payload.items():
        if k in valid_keys: setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj
