import os, re

def w(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"✅ Reescrito: {path}")

# 1. ACTUALIZAR INITDB.SQL DE MANERA PERMANENTE
initdb_path = "postgres_init/initdb.sql"
if os.path.exists(initdb_path):
    with open(initdb_path, "r", encoding="utf-8") as f:
        content = f.read()
    if "eventos_auditoria" not in content.lower():
        with open(initdb_path, "a", encoding="utf-8") as f:
            f.write("\n\nCREATE TABLE IF NOT EXISTS Eventos_Auditoria (\n")
            f.write("    id SERIAL PRIMARY KEY,\n")
            f.write("    actor VARCHAR(255),\n")
            f.write("    action VARCHAR(255),\n")
            f.write("    target VARCHAR(255),\n")
            f.write("    severity VARCHAR(50) DEFAULT 'info',\n")
            f.write("    fecha_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n")
            f.write(");\n")
        print("✅ initdb.sql actualizado para futuros despliegues.")

# 2. LIMPIEZA DE TEXTOS EN FRONTEND
for root, dirs, files in os.walk("frontend"):
    for file in files:
        if file.endswith((".tsx", ".ts", ".jsx", ".js")):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                modified = False
                
                # Quitar texto de mocks
                if "o mocks según NEXT_PUBLIC_DATA_MODE" in content:
                    content = content.replace("o mocks según NEXT_PUBLIC_DATA_MODE", "")
                    modified = True
                
                # Hacer clickeable el nombre/URL del footer
                if "https://www.victorfigueroa.cl" in content and "<a href" not in content:
                    content = content.replace(
                        "https://www.victorfigueroa.cl", 
                        "<a href='https://www.victorfigueroa.cl' target='_blank' rel='noopener noreferrer' className='text-brand-cyan hover:underline font-bold transition-all'>Victor Figueroa</a>"
                    )
                    modified = True

                if modified:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"✅ Textos y Links pulidos en: {path}")
            except Exception as e:
                pass

# 3. FIX FRONTEND: Formulario con Auto-Generación de URL de GitHub
w("frontend/features/projects/ProjectForm.tsx", [
    "\"use client\";",
    "import { useState, useEffect } from 'react';",
    "import { useRouter } from 'next/navigation';",
    "import { Button } from '@/components/ui/Button';",
    "import { SectionHeader } from '@/components/ui/SectionHeader';",
    "import { projectsRepository } from '@/services/repositories';",
    "export function ProjectForm() {",
    "  const router = useRouter();",
    "  const defaultOwner = process.env.NEXT_PUBLIC_GITHUB_DEFAULT_OWNER || 'LTVitoto';",
    "  const [form, setForm] = useState({ titulo: '', responsable: '', descripcion: '', github_url: '', anio: new Date().getFullYear(), rol_gemini: 'Experto Infra, FullStack', rol_chatgpt: 'Experto Backend y Datos', rol_claude: 'Experto Frontend y UX', estado: 'privado' });",
    "  ",
    "  // Auto-Generación del GitHub URL",
    "  useEffect(() => {",
    "    const slug = form.titulo.toLowerCase().trim().replace(/[\s\W-]+/g, '-');",
    "    setForm(prev => ({...prev, github_url: slug ? `https://github.com/${defaultOwner}/${slug}.git` : ''}));",
    "  }, [form.titulo]);",
    "  ",
    "  const submit = async (e: any) => {",
    "    e.preventDefault();",
    "    const p = await projectsRepository.create(form);",
    "    if(p && p.id) router.push(`/projects/${p.id}`);",
    "  };",
    "  return (",
    "    <form onSubmit={submit} className='max-w-2xl space-y-6'>",
    "      <SectionHeader title='Crear proyecto' description='Registra una iniciativa. El Workspace y Repositorio se crearán automáticamente en GitHub.' />",
    "      <div className='p-6 bg-white rounded-3xl shadow-sm border space-y-4'>",
    "        <h3 className='font-black text-brand-navy'>Datos base</h3>",
    "        <div><label className='block text-xs font-bold text-brand-muted uppercase mb-1'>Título</label><input className='w-full border rounded-xl p-3 text-sm' value={form.titulo} onChange={e => setForm({...form, titulo: e.target.value})} required /></div>",
    "        <div><label className='block text-xs font-bold text-brand-muted uppercase mb-1'>Responsable</label><input className='w-full border rounded-xl p-3 text-sm' value={form.responsable} onChange={e => setForm({...form, responsable: e.target.value})} required /></div>",
    "        <div><label className='block text-xs font-bold text-brand-muted uppercase mb-1'>Descripción</label><textarea className='w-full border rounded-xl p-3 text-sm min-h-[100px]' value={form.descripcion} onChange={e => setForm({...form, descripcion: e.target.value})} required /></div>",
    "        <div className='grid grid-cols-2 gap-4'>",
    "          <div><label className='block text-xs font-bold text-brand-muted uppercase mb-1'>GitHub URL (Auto)</label><input className='w-full border rounded-xl p-3 text-sm bg-brand-soft text-brand-muted font-mono' value={form.github_url} readOnly /></div>",
    "          <div>",
    "            <label className='block text-xs font-bold text-brand-muted uppercase mb-1'>Privacidad GitOps</label>",
    "            <select className='w-full border rounded-xl p-3 text-sm' value={form.estado} onChange={e => setForm({...form, estado: e.target.value})}>",
    "              <option value='privado'>Privado</option>",
    "              <option value='publico'>Público</option>",
    "            </select>",
    "          </div>",
    "        </div>",
    "        <h3 className='font-black text-brand-navy mt-6'>Roles Multi-Agente</h3>",
    "        <div><label className='block text-xs font-bold text-brand-muted uppercase mb-1'>Rol Gemini</label><input className='w-full border rounded-xl p-3 text-sm' value={form.rol_gemini} onChange={e => setForm({...form, rol_gemini: e.target.value})} /></div>",
    "        <div><label className='block text-xs font-bold text-brand-muted uppercase mb-1'>Rol ChatGPT</label><input className='w-full border rounded-xl p-3 text-sm' value={form.rol_chatgpt} onChange={e => setForm({...form, rol_chatgpt: e.target.value})} /></div>",
    "        <div><label className='block text-xs font-bold text-brand-muted uppercase mb-1'>Rol Claude</label><input className='w-full border rounded-xl p-3 text-sm' value={form.rol_claude} onChange={e => setForm({...form, rol_claude: e.target.value})} /></div>",
    "        <Button type='submit' className='w-full mt-4'>Crear Proyecto y Repositorio</Button>",
    "      </div>",
    "    </form>",
    "  );",
    "}"
])

# 4. FIX BACKEND PROJECTS: Creación de Repo en POST, Eliminación de Repo en DELETE, Auditoría Total
w("backend/app/routers/projects.py", [
    "import os, subprocess, base64, mimetypes, shutil, httpx",
    "from uuid import UUID",
    "from pathlib import Path",
    "from fastapi import APIRouter, Depends, HTTPException",
    "from sqlalchemy import select",
    "from sqlalchemy.ext.asyncio import AsyncSession",
    "from pydantic import BaseModel",
    "from app.database import get_db",
    "from app.config import get_settings",
    "from app.schemas import ProyectoCreate, ProyectoOut",
    "from app.services.slug import slugify",
    "from app.models.audit import EventoAuditoria",
    "router = APIRouter()",
    "settings = get_settings()",
    "class ReadmeUpdate(BaseModel): content: str",
    "class FileUpdate(BaseModel): content: str",
    "@router.get('', response_model=list[ProyectoOut])",
    "async def list_projects(db: AsyncSession = Depends(get_db)):",
    "    from app.models import Proyecto",
    "    res = await db.execute(select(Proyecto).order_by(Proyecto.fecha_creacion.desc()))",
    "    return list(res.scalars().all())",
    "@router.post('', response_model=ProyectoOut)",
    "async def create_project(payload: ProyectoCreate, db: AsyncSession = Depends(get_db)):",
    "    from app.models import Proyecto",
    "    slug = payload.nombre_slug or slugify(payload.titulo)",
    "    data = payload.model_dump()",
    "    valid_keys = Proyecto.__table__.columns.keys()",
    "    filtered_data = {k: v for k, v in data.items() if k in valid_keys and k != 'nombre_slug'}",
    "    obj = Proyecto(**filtered_data, nombre_slug=slug)",
    "    db.add(obj)",
    "    db.add(EventoAuditoria(actor='Sistema', action='Proyecto Registrado en DB', target=slug, severity='success'))",
    "    await db.commit()",
    "    await db.refresh(obj)",
    "    try:",
    "        ws = settings.base_projects_dir / obj.nombre_slug",
    "        ws.mkdir(parents=True, exist_ok=True)",
    "        with open(ws / 'README.md', 'w', encoding='utf-8') as f: ",
    "            f.write('# ' + obj.titulo + '\\n\\n' + obj.descripcion)",
    "        tk = settings.github_personal_access_token",
    "        if tk and obj.github_url:",
    "            is_private = obj.estado != 'publico'",
    "            async with httpx.AsyncClient() as client:",
    "                headers = {'Authorization': f'token {tk}', 'Accept': 'application/vnd.github.v3+json'}",
    "                r = await client.post('https://api.github.com/user/repos', headers=headers, json={'name': slug, 'private': is_private, 'description': obj.descripcion})",
    "            subprocess.run(['git', 'init'], cwd=str(ws))",
    "            subprocess.run(['git', 'add', '.'], cwd=str(ws))",
    "            subprocess.run(['git', 'config', 'user.email', 'bot@nodara.local'], cwd=str(ws))",
    "            subprocess.run(['git', 'config', 'user.name', 'Nodara Bot'], cwd=str(ws))",
    "            subprocess.run(['git', 'commit', '-m', 'Commit Inicial'], cwd=str(ws))",
    "            auth = obj.github_url.replace('https://', f'https://{tk}@')",
    "            subprocess.run(['git', 'branch', '-M', 'main'], cwd=str(ws))",
    "            subprocess.run(['git', 'remote', 'add', 'origin', auth], cwd=str(ws))",
    "            subprocess.run(['git', 'push', '-u', 'origin', 'main'], cwd=str(ws))",
    "            db.add(EventoAuditoria(actor='GitOps', action='Workspace y Repo Creado', target=slug, severity='success'))",
    "            await db.commit()",
    "    except Exception as e:",
    "        db.add(EventoAuditoria(actor='Sistema', action=f'Error GitOps: {str(e)}', target=slug, severity='danger'))",
    "        await db.commit()",
    "    return obj",
    "@router.delete('/{project_id}')",
    "async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):",
    "    from app.models import Proyecto",
    "    obj = await db.get(Proyecto, UUID(project_id))",
    "    if not obj: raise HTTPException(404)",
    "    slug = obj.nombre_slug",
    "    tk = settings.github_personal_access_token",
    "    if tk and obj.github_url:",
    "        parts = obj.github_url.replace('.git', '').split('/')",
    "        if len(parts) >= 5:",
    "            owner, repo = parts[3], parts[4]",
    "            async with httpx.AsyncClient() as client:",
    "                headers = {'Authorization': f'token {tk}', 'Accept': 'application/vnd.github.v3+json'}",
    "                r = await client.delete(f'https://api.github.com/repos/{owner}/{repo}', headers=headers)",
    "                if r.status_code in [204, 404]:",
    "                    db.add(EventoAuditoria(actor='GitOps', action='Repo GitHub Eliminado', target=repo, severity='warning'))",
    "    ws = settings.base_projects_dir / slug",
    "    if ws.exists(): shutil.rmtree(ws, ignore_errors=True)",
    "    db.add(EventoAuditoria(actor='Sistema', action='Proyecto y Workspace Destruido', target=slug, severity='danger'))",
    "    await db.delete(obj)",
    "    await db.commit()",
    "    return {'status': 'ok'}",
    "@router.get('/{project_id}/readme')",
    "async def get_readme(project_id: str, db: AsyncSession = Depends(get_db)):",
    "    from app.models import Proyecto",
    "    p = await db.get(Proyecto, UUID(project_id))",
    "    path = settings.base_projects_dir / p.nombre_slug / 'README.md'",
    "    if path.exists():",
    "        with open(path, 'r', encoding='utf-8') as f: return {'content': f.read()}",
    "    return {'content': 'Sin README.'}",
    "@router.patch('/{project_id}/readme')",
    "async def update_readme(project_id: str, payload: ReadmeUpdate, db: AsyncSession = Depends(get_db)):",
    "    from app.models import Proyecto",
    "    p = await db.get(Proyecto, UUID(project_id))",
    "    ws = settings.base_projects_dir / p.nombre_slug",
    "    with open(ws / 'README.md', 'w', encoding='utf-8') as f: f.write(payload.content)",
    "    return {'status': 'ok'}",
    "@router.get('/{project_id}/workspace/file')",
    "async def read_file(project_id: str, file_path: str, db: AsyncSession = Depends(get_db)):",
    "    from app.models import Proyecto",
    "    p = await db.get(Proyecto, UUID(project_id))",
    "    fp = Path(file_path)",
    "    if not fp.is_file():",
    "        fp = settings.base_projects_dir / p.nombre_slug / file_path.lstrip('./').lstrip('/')",
    "    if not fp.is_file(): return {'content': 'Archivo no existe.', 'is_image': False}",
    "    mime_type, _ = mimetypes.guess_type(str(fp))",
    "    if mime_type and mime_type.startswith('image/'):",
    "        with open(fp, 'rb') as f:",
    "            b64 = base64.b64encode(f.read()).decode('utf-8')",
    "            return {'content': f'data:{mime_type};base64,{b64}', 'is_image': True}",
    "    with open(fp, 'r', encoding='utf-8', errors='replace') as f: ",
    "        return {'content': f.read(), 'is_image': False}",
    "@router.put('/{project_id}/workspace/file')",
    "async def update_file(project_id: str, file_path: str, payload: FileUpdate, db: AsyncSession = Depends(get_db)):",
    "    from app.models import Proyecto",
    "    p = await db.get(Proyecto, UUID(project_id))",
    "    fp = Path(file_path)",
    "    if not fp.is_file(): fp = settings.base_projects_dir / p.nombre_slug / file_path.lstrip('./').lstrip('/')",
    "    if not fp.is_file(): raise HTTPException(404, 'Archivo no encontrado')",
    "    with open(fp, 'w', encoding='utf-8') as f: f.write(payload.content)",
    "    db.add(EventoAuditoria(actor='User', action='Archivo Editado', target=fp.name, severity='info'))",
    "    await db.commit()",
    "    return {'status': 'ok'}",
    "@router.delete('/{project_id}/workspace/file')",
    "async def delete_file(project_id: str, file_path: str, db: AsyncSession = Depends(get_db)):",
    "    from app.models import Proyecto",
    "    p = await db.get(Proyecto, UUID(project_id))",
    "    fp = Path(file_path)",
    "    if not fp.is_file(): fp = settings.base_projects_dir / p.nombre_slug / file_path.lstrip('./').lstrip('/')",
    "    if not fp.is_file(): raise HTTPException(404, 'Archivo no encontrado')",
    "    os.remove(fp)",
    "    db.add(EventoAuditoria(actor='User', action='Archivo Eliminado', target=fp.name, severity='warning'))",
    "    await db.commit()",
    "    return {'status': 'ok'}",
    "@router.get('/{project_id}/workspace/tree')",
    "async def get_tree(project_id: str, db: AsyncSession = Depends(get_db)):",
    "    from app.models import Proyecto",
    "    p = await db.get(Proyecto, UUID(project_id))",
    "    b = settings.base_projects_dir / p.nombre_slug",
    "    if not b.exists(): return []",
    "    def bt(path):",
    "        n = os.path.basename(path)",
    "        if os.path.isdir(path):",
    "            return {'id': path, 'name': n, 'type': 'folder', 'path': path, 'children': [bt(os.path.join(path, x)) for x in os.listdir(path) if not x.startswith('.git')]}",
    "        return {'id': path, 'name': n, 'type': 'file', 'path': path}",
    "    return [bt(os.path.join(b, x)) for x in os.listdir(b) if not x.startswith('.git')]",
    "@router.get('/{project_id}/messages')",
    "async def get_msgs(project_id: str, db: AsyncSession = Depends(get_db)):",
    "    from app.models.history_models import MensajeHistorial",
    "    try:",
    "        r = await db.execute(select(MensajeHistorial).where(MensajeHistorial.proyecto_id == UUID(project_id)).order_by(MensajeHistorial.fecha_envio.asc()))",
    "        return list(r.scalars().all())",
    "    except: return []",
    "@router.get('/{project_id}', response_model=ProyectoOut)",
    "async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):",
    "    from app.models import Proyecto",
    "    obj = await db.get(Proyecto, UUID(project_id))",
    "    if not obj: raise HTTPException(404)",
    "    return obj",
    "@router.patch('/{project_id}', response_model=ProyectoOut)",
    "async def update_project(project_id: str, payload: dict, db: AsyncSession = Depends(get_db)):",
    "    from app.models import Proyecto",
    "    obj = await db.get(Proyecto, UUID(project_id))",
    "    valid_keys = Proyecto.__table__.columns.keys()",
    "    for k, v in payload.items():",
    "        if k in valid_keys: setattr(obj, k, v)",
    "    db.add(EventoAuditoria(actor='User', action='Proyecto Actualizado', target=obj.nombre_slug, severity='info'))",
    "    await db.commit()",
    "    await db.refresh(obj)",
    "    return obj"
])

print("✅ Operación de Pulido y Orquestación Finalizada.")
