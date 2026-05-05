import os
import subprocess

print("🏆 INICIANDO FIX DEFINITIVO (GITOPS, UI, WORKSPACE, TOOLS Y 404s)...")

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"✅ {path}")

# ==========================================
# 1. DB: AÑADIR CAMPO RESPONSABLE
# ==========================================
subprocess.run(["docker", "exec", "-i", "nodara_db", "psql", "-U", "arquitecto", "-d", "orquestador_db", "-c", 
                "ALTER TABLE proyectos ADD COLUMN IF NOT EXISTS responsable VARCHAR(100) DEFAULT 'Vitoto';"])
print("✅ Columna 'responsable' inyectada en BD.")

# ==========================================
# 2. FRONTEND: LIMPIEZA DE UI (Quitar S1/S2 y DATA_MODE)
# ==========================================
app_shell_path = "frontend/components/layout/AppShell.tsx"
if os.path.exists(app_shell_path):
    with open(app_shell_path, "r", encoding="utf-8") as f: content = f.read()
    content = content.replace(
        '<span className={cn("rounded-full px-2 py-0.5 text-[10px]", active ? "bg-brand-deep/15" : "bg-white/10")}>S{item.sprint}</span>',
        ''
    )
    # Quitar los badges del header
    start = content.find('<div className="flex flex-wrap items-center gap-2">')
    if start != -1:
        end = content.find('</div>', start) + 6
        content = content[:start] + content[end:]
    write_file(app_shell_path, content)

header_path = "frontend/components/ui/SectionHeader.tsx"
if os.path.exists(header_path):
    with open(header_path, "r", encoding="utf-8") as f: content = f.read()
    content = content.replace('{sprint ? <Badge tone="info" className="mb-3">{sprint}</Badge> : null}', '')
    write_file(header_path, content)

# ==========================================
# 3. FRONTEND: DETALLE DE PROYECTO (Edición, Borrado y Responsable)
# ==========================================
write_file("frontend/features/projects/ProjectDetailView.tsx", r"""
"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AgentBadge } from "@/components/ui/AgentBadge";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { formatDate, formatCurrency } from "@/lib/format";
import { projectsRepository, futureRepository } from "@/services/repositories";
import type { Proyecto } from "@/types/domain";

export function ProjectDetailView({ projectId }: { projectId: string }) {
  const router = useRouter();
  const [project, setProject] = useState<Proyecto | null>(null);
  const [costoTotal, setCostoTotal] = useState<number>(0);

  async function loadData() {
      const p = await projectsRepository.get(projectId);
      setProject(p);
      const msgs = await futureRepository.messages(projectId);
      setCostoTotal(msgs.reduce((acc, m) => acc + (m.costo_estimado || 0), 0));
  }

  useEffect(() => { loadData(); }, [projectId]);

  async function toggleStatus() {
      if(!project) return;
      const newStatus = project.estado === 'activo' ? 'inactivo' : 'activo';
      await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/projects/${projectId}`, {
          method: 'PATCH', headers:{'Content-Type':'application/json'}, body: JSON.stringify({estado: newStatus})
      });
      loadData();
  }

  async function deleteProject() {
      if(!confirm("¿Estás seguro de eliminar este proyecto y todos sus archivos?")) return;
      await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/projects/${projectId}`, { method: 'DELETE' });
      router.push("/projects");
  }

  if (!project) return <SectionHeader title="Cargando proyecto..." description="Consultando backend..." />;

  return (
    <div>
      <SectionHeader
        title={project.titulo}
        description={project.descripcion || "Sin descripción"}
        action={
            <div className="flex gap-2">
                <Button variant="danger" onClick={deleteProject}>Eliminar</Button>
                <Button variant="secondary" onClick={toggleStatus}>{project.estado === 'activo' ? 'Desactivar' : 'Activar'}</Button>
                <Link href={`/chat/${project.id}`}><Button>Abrir Chat</Button></Link>
            </div>
        }
      />
      <div className="grid gap-6 xl:grid-cols-[1.1fr_.9fr]">
        <Card>
          <CardTitle eyebrow={project.nombre_slug} title="Contrato del proyecto" />
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl bg-brand-soft p-4"><p className="text-xs font-black text-brand-muted">Responsable</p><p className="font-black text-brand-navy">{(project as any).responsable || "Vitoto"}</p></div>
            <div className="rounded-2xl bg-brand-soft p-4"><p className="text-xs font-black text-brand-muted">Costo Incurrido</p><Badge tone="warning" className="mt-1 text-sm">{formatCurrency(costoTotal)}</Badge></div>
            <div className="rounded-2xl bg-brand-soft p-4"><p className="text-xs font-black text-brand-muted">Estado</p><Badge tone={project.estado === 'activo' ? "success" : "danger"} className="mt-1">{project.estado}</Badge></div>
            <div className="rounded-2xl bg-brand-soft p-4"><p className="text-xs font-black text-brand-muted">GitHub</p><p className="font-bold text-sm truncate">{project.github_url || "No vinculado"}</p></div>
          </div>
          <pre className="mt-5 overflow-auto rounded-3xl bg-brand-deep p-5 text-xs leading-6 text-brand-bright">{JSON.stringify({ tecnologias: project.tecnologias, microservicios: project.microservicios }, null, 2)}</pre>
        </Card>
        <Card>
          <CardTitle eyebrow="Roles" title="Sala multi-agente" />
          <div className="space-y-4">
            <div className="rounded-3xl border border-brand-border p-4"><AgentBadge agent="gemini" /><p className="mt-3 text-sm text-brand-muted">{project.rol_gemini}</p></div>
            <div className="rounded-3xl border border-brand-border p-4"><AgentBadge agent="chatgpt" /><p className="mt-3 text-sm text-brand-muted">{project.rol_chatgpt}</p></div>
            <div className="rounded-3xl border border-brand-border p-4"><AgentBadge agent="claude" /><p className="mt-3 text-sm text-brand-muted">{project.rol_claude}</p></div>
          </div>
        </Card>
      </div>
    </div>
  );
}
""")

# ==========================================
# 4. BACKEND: SCHEMAS (Responsable)
# ==========================================
write_file("backend/app/schemas.py", r"""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

class ProyectoCreate(BaseModel):
    nombre_slug: Optional[str] = None
    titulo: str
    anio: int = 2026
    descripcion: Optional[str] = None
    tecnologias: dict[str, Any] = {}
    microservicios: dict[str, Any] = {}
    instrucciones_deploy: Optional[str] = None
    github_url: Optional[str] = None
    rol_gemini: Optional[str] = "Experto en Infraestructura"
    rol_chatgpt: Optional[str] = "Experto en Backend"
    rol_claude: Optional[str] = "Experto en Frontend"
    estado: str = "activo"
    responsable: str = "Vitoto"

class ProyectoUpdate(BaseModel):
    titulo: Optional[str] = None
    estado: Optional[str] = None
    responsable: Optional[str] = None

class ProyectoOut(ProyectoCreate):
    id: UUID
    fecha_creacion: datetime
    class Config: from_attributes = True

class ArchivoTemporalOut(BaseModel):
    id: int
    proyecto_id: UUID
    nombre_archivo: str
    ruta_archivo: Optional[str]
    size_bytes: Optional[int]
    class Config: from_attributes = True

class ApprovalOut(BaseModel):
    id: int
    proyecto_id: UUID
    usuario_config_id: int
    agente: str
    tool_name: str
    arguments_json: dict[str, Any]
    status: str
    class Config: from_attributes = True
""")

# ==========================================
# 5. BACKEND ROUTER: PROJECT (Delete, GitOps Automático)
# ==========================================
write_file("backend/app/routers/projects.py", r"""
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
""")

# ==========================================
# 6. BACKEND: TOOLS (Añadiendo Docker Compose Build)
# ==========================================
write_file("backend/app/services/tools.py", r"""
from __future__ import annotations
import json, os, subprocess
from dataclasses import dataclass
from typing import Any, Awaitable, Callable
from uuid import UUID
import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.services.filesystem_guard import safe_join

settings = get_settings()

@dataclass
class ToolExecutionContext:
    proyecto_id: UUID
    usuario_config_id: int
    agente: str
    db: AsyncSession
    human_approved: bool = False

@dataclass
class RegisteredTool:
    name: str
    description: str
    risk_level: str
    schema: dict[str, Any]
    handler: Callable[[dict[str, Any], ToolExecutionContext], Awaitable[dict[str, Any]]]

TOOL_REGISTRY: dict[str, RegisteredTool] = {}

def tool(name: str, description: str, risk_level: str, schema: dict[str, Any]):
    def decorator(func: Callable[[dict[str, Any], ToolExecutionContext], Awaitable[dict[str, Any]]]):
        TOOL_REGISTRY[name] = RegisteredTool(name=name, description=description, risk_level=risk_level, schema=schema, handler=func)
        return func
    return decorator

async def get_project_workspace(context: ToolExecutionContext):
    from app.models import Proyecto 
    proyecto = await context.db.get(Proyecto, context.proyecto_id)
    base = settings.base_projects_dir / proyecto.nombre_slug
    base.mkdir(parents=True, exist_ok=True)
    return base

async def require_human_approval_if_needed(registered_tool: RegisteredTool, arguments: dict[str, Any], context: ToolExecutionContext, bypass_hil: bool = False):
    if bypass_hil or registered_tool.risk_level == "LOW": return None
    from app.models.governance import ToolCallPendiente, ToolCallStatus, UsuarioConfig 
    usuario = await context.db.get(UsuarioConfig, context.usuario_config_id)
    if registered_tool.risk_level == "CRITICAL" or (not usuario.auto_aprobar_ejecucion):
        pending = ToolCallPendiente(proyecto_id=context.proyecto_id, usuario_config_id=context.usuario_config_id, agente=context.agente, tool_name=registered_tool.name, arguments_json=arguments, status=ToolCallStatus.PENDING.value)
        context.db.add(pending)
        await context.db.commit()
        await context.db.refresh(pending)
        return {"requires_human_approval": True, "approval_id": pending.id, "risk_level": registered_tool.risk_level, "tool_name": registered_tool.name}
    return None

@tool(name="leer_proyecto_tree", description="Ejecuta comando find en el proyecto ignorando basura", risk_level="LOW", schema={"type": "object", "properties": {}})
async def leer_proyecto_tree(arguments: dict[str, Any], context: ToolExecutionContext) -> dict[str, Any]:
    base = await get_project_workspace(context)
    cmd = '''find . -type f -not -path "*/\.git/*" -not -path "*/node_modules/*" -not -path "*/__pycache__/*" -not -path "*/venv/*" -not -path "*/.next/*" -not -name "*.pyc"'''
    result = subprocess.run(cmd, shell=True, cwd=str(base), capture_output=True, text=True)
    return {"archivos": result.stdout.split("\n")}

@tool(name="leer_db_full", description="Extrae el schema de la base de datos PostgreSQL.", risk_level="LOW", schema={"type": "object", "properties": {}})
async def leer_db_full(arguments: dict[str, Any], context: ToolExecutionContext) -> dict[str, Any]:
    from sqlalchemy import inspect
    from app.database import engine
    def get_schema(conn):
        inspector = inspect(conn)
        schema = ""
        for table_name in inspector.get_table_names():
            schema += f"Table: {table_name}\n"
            for col in inspector.get_columns(table_name): schema += f"  - {col['name']}: {col['type']}\n"
        return schema
    async with engine.connect() as conn: schema_str = await conn.run_sync(get_schema)
    return {"db_schema": schema_str}

@tool(name="leer_archivo_cat", description="Lee el contenido de un archivo.", risk_level="LOW", schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]})
async def leer_archivo_cat(arguments: dict[str, Any], context: ToolExecutionContext) -> dict[str, Any]:
    base = await get_project_workspace(context)
    async with aiofiles.open(safe_join(base, arguments["path"]), "r", encoding="utf-8") as f: return {"content": await f.read()}

@tool(name="escribir_script", description="Crea o sobrescribe un archivo.", risk_level="HIGH", schema={"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]})
async def escribir_script(arguments: dict[str, Any], context: ToolExecutionContext) -> dict[str, Any]:
    base = await get_project_workspace(context)
    target = safe_join(base, arguments["path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(target, "w", encoding="utf-8") as f: await f.write(arguments["content"])
    return {"ok": True, "path": str(target)}

@tool(name="ejecutar_script_bash", description="Ejecuta un script con bash o python3.", risk_level="CRITICAL", schema={"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]})
async def ejecutar_script_bash(arguments: dict[str, Any], context: ToolExecutionContext) -> dict[str, Any]:
    base = await get_project_workspace(context)
    result = subprocess.run(arguments["command"], shell=True, cwd=str(base), capture_output=True, text=True)
    return {"stdout": result.stdout, "stderr": result.stderr}

@tool(name="reconstruir_docker", description="Reconstruye y levanta docker-compose up -d --build", risk_level="CRITICAL", schema={"type": "object", "properties": {}})
async def reconstruir_docker(arguments: dict[str, Any], context: ToolExecutionContext) -> dict[str, Any]:
    base = await get_project_workspace(context)
    result = subprocess.run("docker compose up -d --build", shell=True, cwd=str(base), capture_output=True, text=True)
    return {"stdout": result.stdout, "stderr": result.stderr}

async def execute_tool_by_name(tool_name: str, arguments: dict[str, Any], context: ToolExecutionContext, bypass_hil: bool = False) -> dict[str, Any]:
    registered_tool = TOOL_REGISTRY.get(tool_name)
    if not registered_tool: raise ValueError(f"Tool no registrada: {tool_name}")
    approval_event = await require_human_approval_if_needed(registered_tool, arguments, context, bypass_hil=bypass_hil)
    if approval_event: return approval_event
    return await registered_tool.handler(arguments, context)
""")

print("\n🚀 LISTO. REINICIA TUS CONTENEDORES (docker compose restart backend frontend)")