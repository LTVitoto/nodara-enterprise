import subprocess
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.config import get_settings
from app.models import Proyecto

router = APIRouter()
settings = get_settings()

async def get_cwd(project_id: str, db: AsyncSession):
    p = await db.get(Proyecto, UUID(project_id))
    path = settings.base_projects_dir / p.nombre_slug
    path.mkdir(parents=True, exist_ok=True)
    return str(path)

@router.post("/{project_id}/status")
async def git_status(project_id: str, db: AsyncSession = Depends(get_db)):
    cwd = await get_cwd(project_id, db)
    # Inicializa el repo si no existe
    subprocess.run(["git", "init"], cwd=cwd, capture_output=True)
    res = subprocess.run(["git", "status"], cwd=cwd, capture_output=True, text=True)
    return {"output": res.stdout or res.stderr}

@router.post("/{project_id}/add")
async def git_add(project_id: str, db: AsyncSession = Depends(get_db)):
    cwd = await get_cwd(project_id, db)
    res = subprocess.run(["git", "add", "."], cwd=cwd, capture_output=True, text=True)
    return {"output": "Archivos agregados al staging.\n" + (res.stdout or res.stderr)}

@router.post("/{project_id}/commit")
async def git_commit(project_id: str, db: AsyncSession = Depends(get_db)):
    cwd = await get_cwd(project_id, db)
    res = subprocess.run(["git", "commit", "-m", "Version via Nodara, Websocket OK"], cwd=cwd, capture_output=True, text=True)
    return {"output": res.stdout or res.stderr}

@router.post("/{project_id}/push")
async def git_push(project_id: str, db: AsyncSession = Depends(get_db)):
    cwd = await get_cwd(project_id, db)
    # Aquí se usarían las credenciales de la DB en un escenario productivo total
    res = subprocess.run(["git", "push"], cwd=cwd, capture_output=True, text=True)
    out = res.stdout or res.stderr
    if not out: out = "Error: Upstream no configurado o repositorio sin origin."
    return {"output": out}
