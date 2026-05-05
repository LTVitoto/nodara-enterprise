import os
import subprocess
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.config import get_settings
from app.schemas import ProyectoCreate, ProyectoOut, ProyectoUpdate
from app.services.slug import slugify

router = APIRouter()
settings = get_settings()

@router.get("", response_model=list[ProyectoOut])
async def list_projects(db: AsyncSession = Depends(get_db)):
    from app.models import Proyecto
    result = await db.execute(select(Proyecto).order_by(Proyecto.fecha_creacion.desc()))
    return list(result.scalars().all())

@router.post("", response_model=ProyectoOut)
async def create_project(payload: ProyectoCreate, db: AsyncSession = Depends(get_db)):
    from app.models import Proyecto
    slug = payload.nombre_slug or slugify(payload.titulo)
    obj = Proyecto(**payload.model_dump(exclude={"nombre_slug"}), nombre_slug=slug)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)

    # 🔥 FIX: Auto-crear carpeta física para evitar que Workspace diga "vacía"
    workspace = settings.base_projects_dir / obj.nombre_slug
    workspace.mkdir(parents=True, exist_ok=True)
    
    # 🔥 GITOPS AUTOMATIZADO: Si hay URL, inicializa y pushea
    if obj.github_url and settings.github_personal_access_token:
        try:
            with open(workspace / "README.md", "w") as f:
                f.write(f"# {obj.titulo}\n\n{obj.descripcion}")
            subprocess.run(["git", "init"], cwd=str(workspace))
            subprocess.run(["git", "add", "."], cwd=str(workspace))
            subprocess.run(["git", "commit", "-m", "Proyecto desde Nodara : Inicializacion"], cwd=str(workspace))
            subprocess.run(["git", "branch", "-M", "main"], cwd=str(workspace))
            # Inyectar Token en URL para Push
            auth_url = obj.github_url.replace("https://", f"https://{settings.github_personal_access_token}@")
            subprocess.run(["git", "remote", "add", "origin", auth_url], cwd=str(workspace))
            subprocess.run(["git", "push", "-u", "origin", "main"], cwd=str(workspace))
        except Exception as e:
            print(f"Error GitOps: {e}")

    return obj

@router.get("/{project_id}", response_model=ProyectoOut)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    from app.models import Proyecto
    obj = await db.get(Proyecto, UUID(project_id))
    if not obj: raise HTTPException(status_code=404)
    return obj

@router.patch("/{project_id}", response_model=ProyectoOut)
async def update_project(project_id: str, payload: ProyectoUpdate, db: AsyncSession = Depends(get_db)):
    from app.models import Proyecto
    obj = await db.get(Proyecto, UUID(project_id))
    for key, value in payload.model_dump(exclude_unset=True).items(): setattr(obj, key, value)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.delete("/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    from app.models import Proyecto
    obj = await db.get(Proyecto, UUID(project_id))
    if obj:
        await db.delete(obj)
        await db.commit()
    return {"status": "ok"}

@router.get('/{project_id}/messages')
async def get_project_messages(project_id: str, db: AsyncSession = Depends(get_db)):
    from app.models.history_models import MensajeHistorial
    try:
        result = await db.execute(select(MensajeHistorial).where(MensajeHistorial.proyecto_id == UUID(project_id)).order_by(MensajeHistorial.fecha_envio.asc()))
        mensajes = result.scalars().all()
        return [{"id": str(m.id), "proyecto_id": str(m.proyecto_id), "remitente": m.remitente, "destinatario": m.destinatario, "contenido": m.contenido, "tokens_consumidos": m.tokens_consumidos or 0, "costo_estimado": float(m.costo_estimado) if m.costo_estimado else 0.0, "incluir_en_contexto": m.incluir_en_contexto, "fecha_envio": m.fecha_envio.isoformat() if m.fecha_envio else ""} for m in mensajes]
    except Exception: return []

@router.get('/{project_id}/workspace/tree')
async def get_workspace_tree(project_id: str, db: AsyncSession = Depends(get_db)):
    from app.models import Proyecto
    try:
        proyecto = await db.get(Proyecto, UUID(project_id))
        base_dir = settings.base_projects_dir / proyecto.nombre_slug
        base_dir.mkdir(parents=True, exist_ok=True) # Fuerza la creacion si no existia
        def build_tree(path):
            name = os.path.basename(path)
            if os.path.isdir(path): return {"id": path, "name": name, "type": "folder", "path": path, "children": [build_tree(os.path.join(path, x)) for x in os.listdir(path) if not x.startswith(".git")]}
            return {"id": path, "name": name, "type": "file", "path": path}
        return [build_tree(os.path.join(base_dir, x)) for x in os.listdir(base_dir) if not x.startswith(".git")]
    except Exception: return []
