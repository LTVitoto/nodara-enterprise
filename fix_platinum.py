import os

print("💎 INICIANDO PARCHE PLATINUM (PERMISOS 777, GITOPS Y FORMULARIOS)...")

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"✅ {path}")

# ==========================================
# 1. FIX MODELO BACKEND (Para evitar el 500 al crear proyectos)
# ==========================================
write_file("backend/app/models/proyecto.py", r"""
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from app.database import Base

class Proyecto(Base):
    __tablename__ = "proyectos"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_slug = Column(String(100), unique=True, nullable=False)
    titulo = Column(String(150), nullable=False)
    anio = Column(Integer, nullable=False)
    descripcion = Column(Text)
    tecnologias = Column(JSONB, default=[])
    microservicios = Column(JSONB, default=[])
    instrucciones_deploy = Column(Text)
    github_url = Column(String(255))
    rol_gemini = Column(Text, nullable=False)
    rol_chatgpt = Column(Text, nullable=False)
    rol_claude = Column(Text, nullable=False)
    estado = Column(String(20), default="Activo")
    responsable = Column(String(100), default="Vitoto") # 🔥 FIX CRÍTICO
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
""")

# ==========================================
# 2. FIX ROUTER PROYECTOS (chmod 777 y GitOps Automático)
# ==========================================
write_file("backend/app/routers/projects.py", r"""
import os
import subprocess
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
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

    # 🔥 CARPETA CON CHMOD 777
    workspace = settings.base_projects_dir / obj.nombre_slug
    workspace.mkdir(parents=True, exist_ok=True)
    subprocess.run(["chmod", "-R", "777", str(workspace)])
    
    # 🔥 GITOPS AUTOMATIZADO
    if obj.github_url and settings.github_personal_access_token:
        try:
            # Bypass de seguridad de Git para carpetas root:root
            subprocess.run(["git", "config", "--global", "--add", "safe.directory", "*"])
            
            with open(workspace / "README.md", "w") as f:
                f.write(f"# {obj.titulo}\n\n{obj.descripcion}")
                
            subprocess.run(["git", "init"], cwd=str(workspace))
            subprocess.run(["git", "add", "."], cwd=str(workspace))
            subprocess.run(["git", "commit", "-m", "Proyecto desde Nodara : Inicializacion"], cwd=str(workspace))
            subprocess.run(["git", "branch", "-M", "main"], cwd=str(workspace))
            
            auth_url = obj.github_url.replace("https://", f"https://{settings.github_personal_access_token}@")
            subprocess.run(["git", "remote", "add", "origin", auth_url], cwd=str(workspace))
            subprocess.run(["git", "push", "-u", "origin", "main"], cwd=str(workspace))
            
            # Re-aplicar 777 tras crear el directorio .git
            subprocess.run(["chmod", "-R", "777", str(workspace)])
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
        base_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["chmod", "-R", "777", str(base_dir)])
        
        def build_tree(path):
            name = os.path.basename(path)
            if os.path.isdir(path): return {"id": path, "name": name, "type": "folder", "path": path, "children": [build_tree(os.path.join(path, x)) for x in os.listdir(path) if not x.startswith(".git")]}
            return {"id": path, "name": name, "type": "file", "path": path}
        return [build_tree(os.path.join(base_dir, x)) for x in os.listdir(base_dir) if not x.startswith(".git")]
    except Exception: return []
""")

# ==========================================
# 3. FIX ROUTER GITHUB (Evitando el error de Dubious Ownership)
# ==========================================
write_file("backend/app/routers/github.py", r"""
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
    
    # 🔥 SOLUCIÓN CRÍTICA PARA PERMISOS DE GITOPS
    subprocess.run(["chmod", "-R", "777", str(path)])
    subprocess.run(["git", "config", "--global", "--add", "safe.directory", "*"])
    
    return str(path)

@router.post("/{project_id}/status")
async def git_status(project_id: str, db: AsyncSession = Depends(get_db)):
    cwd = await get_cwd(project_id, db)
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
    res = subprocess.run(["git", "push"], cwd=cwd, capture_output=True, text=True)
    out = res.stdout or res.stderr
    if not out: out = "Error: Upstream no configurado o repositorio sin origin."
    return {"output": out}
""")

# ==========================================
# 4. FIX FRONTEND: AÑADIR RESPONSABLE AL FORMULARIO
# ==========================================
write_file("frontend/features/projects/ProjectForm.tsx", r"""
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { projectsRepository } from "@/services/repositories";
import type { ProyectoCreate } from "@/types/domain";

const defaultProject: ProyectoCreate = {
  nombre_slug: "orquestador-demo",
  titulo: "Orquestador Multi-Agente Demo",
  anio: 2026,
  descripcion: "Proyecto enterprise.",
  tecnologias: { backend: "FastAPI", frontend: "Next.js" },
  microservicios: { db: "orquestador_db" },
  instrucciones_deploy: "docker compose up -d",
  github_url: null,
  rol_gemini: "Experto Infra",
  rol_chatgpt: "Experto Backend",
  rol_claude: "Experto Frontend",
  estado: "activo",
  responsable: "Vitoto"
};

export function ProjectForm() {
  const router = useRouter();
  const [payload, setPayload] = useState<ProyectoCreate>(defaultProject);
  const [saving, setSaving] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
        const created = await projectsRepository.create(payload);
        router.push(`/projects/${created.id}`);
    } catch(e) {
        console.error("Error creando proyecto", e);
        setSaving(false);
    }
  }

  function set<K extends keyof ProyectoCreate>(key: K, value: ProyectoCreate[K]) {
    setPayload((prev) => ({ ...prev, [key]: value }));
  }

  return (
    <div>
      <SectionHeader title="Crear proyecto" description="Formulario alineado a la BD y WSL." />
      <Card>
        <CardTitle eyebrow="Payload oficial" title="Datos base del proyecto" />
        <form onSubmit={submit} className="grid gap-5">
          <div className="grid gap-5 md:grid-cols-2">
            <label className="grid gap-2 text-sm font-bold">Slug<input className="rounded-2xl border border-brand-border p-3" value={payload.nombre_slug} onChange={(e) => set("nombre_slug", e.target.value)} /></label>
            <label className="grid gap-2 text-sm font-bold">Título<input className="rounded-2xl border border-brand-border p-3" value={payload.titulo} onChange={(e) => set("titulo", e.target.value)} /></label>
          </div>
          <div className="grid gap-5 md:grid-cols-2">
            <label className="grid gap-2 text-sm font-bold">Responsable<input className="rounded-2xl border border-brand-border p-3 bg-brand-soft" value={payload.responsable} onChange={(e) => set("responsable", e.target.value)} /></label>
            <label className="grid gap-2 text-sm font-bold">GitHub URL<input className="rounded-2xl border border-brand-border p-3" value={payload.github_url || ""} onChange={(e) => set("github_url", e.target.value || null)} placeholder="https://github.com/.../repo.git"/></label>
          </div>
          <label className="grid gap-2 text-sm font-bold">Descripción<textarea className="min-h-28 rounded-2xl border border-brand-border p-3" value={payload.descripcion || ""} onChange={(e) => set("descripcion", e.target.value)} /></label>
          <div className="grid gap-5 md:grid-cols-3">
            <label className="grid gap-2 text-sm font-bold">Rol Gemini<textarea className="min-h-24 rounded-2xl border border-brand-border p-3" value={payload.rol_gemini || ""} onChange={(e) => set("rol_gemini", e.target.value)} /></label>
            <label className="grid gap-2 text-sm font-bold">Rol ChatGPT<textarea className="min-h-24 rounded-2xl border border-brand-border p-3" value={payload.rol_chatgpt || ""} onChange={(e) => set("rol_chatgpt", e.target.value)} /></label>
            <label className="grid gap-2 text-sm font-bold">Rol Claude<textarea className="min-h-24 rounded-2xl border border-brand-border p-3" value={payload.rol_claude || ""} onChange={(e) => set("rol_claude", e.target.value)} /></label>
          </div>
          <Button disabled={saving} className="justify-self-start">{saving ? "Creando..." : "Crear proyecto"}</Button>
        </form>
      </Card>
    </div>
  );
}
""")

# ==========================================
# 5. FIX ROUTER FILES (Garantizar 200 OK y no 404)
# ==========================================
write_file("backend/app/routers/files.py", r"""
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
    except Exception as e:
        print(f"Error GET files: {e}")
        return []

@router.post("/{proyecto_id}/upload", response_model=ArchivoTemporalOut)
async def upload_file(proyecto_id: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    from app.models import ArchivoTemporal, Proyecto
    p_id = UUID(proyecto_id)
    proyecto = await db.get(Proyecto, p_id)
    if not proyecto: raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    workspace = settings.base_projects_dir / proyecto.nombre_slug / "_uploads"
    workspace.mkdir(parents=True, exist_ok=True)
    subprocess.run(["chmod", "-R", "777", str(settings.base_projects_dir / proyecto.nombre_slug)])
    
    target = safe_join(workspace, os.path.basename(file.filename or "archivo.bin"))
    size = 0
    async with aiofiles.open(target, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            await out.write(chunk)

    obj = ArchivoTemporal(proyecto_id=p_id, nombre_archivo=file.filename, contenido_codigo="Binario guardado", version=1, ruta_archivo=str(target), mime_type=file.content_type, size_bytes=size)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj
""")

print("\n🚀 LISTO. Reinicia Backend y Frontend.")