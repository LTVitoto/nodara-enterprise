import subprocess, httpx, shutil
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
    res = subprocess.run(['git', 'commit', '-m', 'Commit Automático Nodara'], cwd=cwd, capture_output=True, text=True)
    return {'output': res.stdout or res.stderr}
@router.post('/{project_id}/push')
async def git_push(project_id: str, db=Depends(get_db)):
    from app.models.audit import EventoAuditoria
    cwd = await get_cwd(project_id, db)
    p = await db.get(Proyecto, UUID(project_id))
    tk = settings.github_personal_access_token
    if not tk or not p.github_url: return {'output': 'Error: GitOps sin configurar.'}
    slug = p.nombre_slug
    is_private = p.estado != 'publico'  # Asumimos privado por defecto a menos que el estado sea 'publico'
    async with httpx.AsyncClient() as client:
        headers = {'Authorization': f'token {tk}', 'Accept': 'application/vnd.github.v3+json'}
        r = await client.post('https://api.github.com/user/repos', headers=headers, json={'name': slug, 'private': is_private, 'description': p.descripcion})
    auth = p.github_url.replace('https://', f'https://{tk}@')
    subprocess.run(['git', 'branch', '-M', 'main'], cwd=cwd)
    res = subprocess.run(['git', 'push', auth, 'main'], cwd=cwd, capture_output=True, text=True)
    if res.returncode == 0:
        audit = EventoAuditoria(actor='Sistema', action='Git Push', target=slug, severity='success')
        db.add(audit)
        await db.commit()
    return {'output': f'Repo creado/verificado. Push:\n{res.stdout or res.stderr}'}
@router.delete('/{project_id}/repo')
async def delete_repo(project_id: str, db=Depends(get_db)):
    p = await db.get(Proyecto, UUID(project_id))
    tk = settings.github_personal_access_token
    if tk and p.github_url:
        slug = p.nombre_slug
        # Asumimos que la URL es tipo https://github.com/Usuario/Repo.git
        # Extraemos el propietario del repo
        parts = p.github_url.split('/')
        if len(parts) >= 4:
            owner = parts[3]
            async with httpx.AsyncClient() as client:
                headers = {'Authorization': f'token {tk}', 'Accept': 'application/vnd.github.v3+json'}
                await client.delete(f'https://api.github.com/repos/{owner}/{slug}', headers=headers)
    return {'status': 'ok'}
