import subprocess, httpx, shutil
from uuid import UUID
from fastapi import APIRouter, Depends
from app.database import get_db
from app.config import get_settings
from app.models import Proyecto
from app.models.audit import EventoAuditoria
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
    cwd = await get_cwd(project_id, db)
    p = await db.get(Proyecto, UUID(project_id))
    tk = settings.github_personal_access_token
    if not tk or not p.github_url: return {'output': 'Error: GitOps sin configurar.'}
    repo_name = p.github_url.split('/')[-1].replace('.git', '')
    is_private = p.estado != 'publico'
    try:
        async with httpx.AsyncClient() as client:
            headers = {'Authorization': f'Bearer {tk}', 'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'Nodara-Enterprise'}
            await client.post('https://api.github.com/user/repos', headers=headers, json={'name': repo_name, 'private': is_private, 'description': p.descripcion})
    except Exception as e:
        pass # Ignoramos si ya existe o falla en push manual, intentamos el push igual
    auth = p.github_url.replace('https://', f'https://{tk}@')
    subprocess.run(['git', 'branch', '-M', 'main'], cwd=cwd)
    res = subprocess.run(['git', 'push', auth, 'main'], cwd=cwd, capture_output=True, text=True)
    if res.returncode == 0:
        db.add(EventoAuditoria(actor='Sistema', action='Git Push Manual Exitoso', target=repo_name, severity='success'))
    else:
        db.add(EventoAuditoria(actor='Sistema', action='Git Push Manual Fallido', target=repo_name, severity='danger'))
    await db.commit()
    return {'output': f'Push ejecutado:\n{res.stdout or res.stderr}'}
@router.delete('/{project_id}/repo')
async def delete_repo(project_id: str, db=Depends(get_db)):
    p = await db.get(Proyecto, UUID(project_id))
    tk = settings.github_personal_access_token
    if tk and p.github_url:
        parts = p.github_url.replace('.git', '').split('/')
        if len(parts) >= 4:
            owner, repo = parts[-2], parts[-1]
            try:
                async with httpx.AsyncClient() as client:
                    headers = {'Authorization': f'Bearer {tk}', 'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'Nodara-Enterprise'}
                    r = await client.delete(f'https://api.github.com/repos/{owner}/{repo}', headers=headers)
                    if r.status_code == 204:
                        db.add(EventoAuditoria(actor='GitOps', action='Repo Eliminado en GitHub', target=repo, severity='warning'))
                    elif r.status_code != 404:
                        error_msg = r.json().get('message', 'Error') if r.text else str(r.status_code)
                        db.add(EventoAuditoria(actor='GitOps', action=f'No se pudo borrar Github: {error_msg}', target=repo, severity='danger'))
                    await db.commit()
            except Exception as e:
                db.add(EventoAuditoria(actor='GitOps', action=f'Excepción borrando Github: {str(e)[:50]}', target=repo, severity='danger'))
                await db.commit()
    return {'status': 'ok'}
