import subprocess
from uuid import UUID
from fastapi import APIRouter, Depends
from app.database import get_db
from app.config import get_settings
from app.models import Proyecto
router = APIRouter()
settings = get_settings()
async def get_cwd(project_id, db):
    p = await db.get(Proyecto, UUID(project_id))
    path = settings.base_projects_dir / p.nombre_slug
    path.mkdir(parents=True, exist_ok=True)
    return str(path)
@router.post('/{project_id}/status')
async def git_status(project_id: str, db=Depends(get_db)):
    cwd = await get_cwd(project_id, db)
    subprocess.run(['git', 'init'], cwd=cwd)
    res = subprocess.run(['git', 'status'], cwd=cwd, capture_output=True, text=True)
    return {'output': res.stdout or res.stderr}
@router.post('/{project_id}/add')
async def git_add(project_id: str, db=Depends(get_db)):
    cwd = await get_cwd(project_id, db)
    res = subprocess.run(['git', 'add', '.'], cwd=cwd, capture_output=True, text=True)
    return {'output': 'Archivos agregados.\n' + (res.stdout or res.stderr)}
@router.post('/{project_id}/commit')
async def git_commit(project_id: str, db=Depends(get_db)):
    cwd = await get_cwd(project_id, db)
    subprocess.run(['git', 'config', 'user.email', 'bot@nodara.local'], cwd=cwd)
    subprocess.run(['git', 'config', 'user.name', 'Nodara Bot'], cwd=cwd)
    res = subprocess.run(['git', 'commit', '-m', 'Commit Nodara'], cwd=cwd, capture_output=True, text=True)
    return {'output': res.stdout or res.stderr}
@router.post('/{project_id}/push')
async def git_push(project_id: str, db=Depends(get_db)):
    cwd = await get_cwd(project_id, db)
    p = await db.get(Proyecto, UUID(project_id))
    if p.github_url and settings.github_personal_access_token:
        tk = settings.github_personal_access_token
        auth = p.github_url.replace('https://', f'https://{tk}@')
        subprocess.run(['git', 'branch', '-M', 'main'], cwd=cwd)
        res = subprocess.run(['git', 'push', auth, 'main'], cwd=cwd, capture_output=True, text=True)
        return {'output': res.stdout or res.stderr}
    return {'output': 'Error: GitOps sin configurar.'}
