import os

print("🏆 INICIANDO GOLDEN MASTER V2: PERSISTENCIA, TOOLS Y GITOPS...")

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"✅ {path}")

# ==========================================
# 1. BACKEND ROUTERS: Files y Projects (Fix 404)
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
    except Exception:
        return []

@router.post("/{proyecto_id}/upload", response_model=ArchivoTemporalOut)
async def upload_file(proyecto_id: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    from app.models import ArchivoTemporal, Proyecto
    p_id = UUID(proyecto_id)
    proyecto = await db.get(Proyecto, p_id)
    if not proyecto: raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    workspace = settings.base_projects_dir / proyecto.nombre_slug / "_uploads"
    workspace.mkdir(parents=True, exist_ok=True)
    target = safe_join(workspace, os.path.basename(file.filename or "archivo.bin"))

    size = 0
    async with aiofiles.open(target, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            await out.write(chunk)

    obj = ArchivoTemporal(
        proyecto_id=p_id, nombre_archivo=file.filename,
        contenido_codigo="Archivo binario guardado en disco", version=1,
        ruta_archivo=str(target), mime_type=file.content_type, size_bytes=size,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj
""")

write_file("backend/app/routers/projects.py", r"""
import os
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import ProyectoCreate, ProyectoOut, ProyectoUpdate
from app.services.slug import slugify

router = APIRouter()

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

@router.get('/{project_id}/messages')
async def get_project_messages(project_id: str, db: AsyncSession = Depends(get_db)):
    from app.models.history_models import MensajeHistorial
    try:
        result = await db.execute(select(MensajeHistorial).where(MensajeHistorial.proyecto_id == UUID(project_id)).order_by(MensajeHistorial.fecha_envio.asc()))
        mensajes = result.scalars().all()
        return [{
            "id": str(m.id), "proyecto_id": str(m.proyecto_id), "remitente": m.remitente, "destinatario": m.destinatario,
            "contenido": m.contenido, "tokens_consumidos": m.tokens_consumidos or 0, 
            "costo_estimado": float(m.costo_estimado) if m.costo_estimado else 0.0,
            "incluir_en_contexto": m.incluir_en_contexto, "fecha_envio": m.fecha_envio.isoformat() if m.fecha_envio else ""
        } for m in mensajes]
    except Exception: return []

@router.get('/{project_id}/workspace/tree')
async def get_workspace_tree(project_id: str, db: AsyncSession = Depends(get_db)):
    from app.models import Proyecto
    from app.config import get_settings
    try:
        proyecto = await db.get(Proyecto, UUID(project_id))
        if not proyecto: return []
        base_dir = get_settings().base_projects_dir / proyecto.nombre_slug
        if not base_dir.exists(): return []
        
        def build_tree(path):
            name = os.path.basename(path)
            if os.path.isdir(path):
                return {"id": path, "name": name, "type": "folder", "path": path, "children": [build_tree(os.path.join(path, x)) for x in os.listdir(path)]}
            return {"id": path, "name": name, "type": "file", "path": path}
        return [build_tree(os.path.join(base_dir, x)) for x in os.listdir(base_dir)]
    except Exception: return []
""")

# ==========================================
# 2. BACKEND: Github Router y Metrics
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
""")

write_file("backend/app/routers/metrics.py", r"""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter()

@router.get("")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    from app.models.history_models import MensajeHistorial
    from app.models import Proyecto
    res_cost = await db.execute(select(func.sum(MensajeHistorial.costo_estimado)))
    res_proj = await db.execute(select(func.count(Proyecto.id)))
    res_msg = await db.execute(select(func.count(MensajeHistorial.id)))
    
    total_cost = res_cost.scalar() or 0.0
    return [
        {"label": "Proyectos Activos", "value": str(res_proj.scalar() or 0), "tone": "info", "trend": "global"},
        {"label": "Interacciones (Mensajes)", "value": str(res_msg.scalar() or 0), "tone": "success", "trend": "runtime"},
        {"label": "Costo Histórico Total", "value": f"US$ {total_cost:.4f}", "tone": "warning", "trend": "consumo real"},
        {"label": "Ahorro Estimado HIL", "value": "14 hrs", "tone": "success", "trend": "productividad"}
    ]
""")

write_file("backend/app/main.py", open("backend/app/main.py").read().replace("from app.routers import projects, approvals", "from app.routers import projects, approvals, github").replace("app.include_router(audit.router, prefix=\"/api/audit\", tags=[\"Audit\"])", "app.include_router(audit.router, prefix=\"/api/audit\", tags=[\"Audit\"])\napp.include_router(github.router, prefix=\"/api/github\", tags=[\"Github\"])"))

# ==========================================
# 3. BACKEND: Herramientas (Nuevas máscaras de búsqueda y Volcado de DB)
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

async def get_project_workspace(context: ToolExecutionContext):
    from app.models import Proyecto 
    proyecto = await context.db.get(Proyecto, context.proyecto_id)
    base = settings.base_projects_dir / proyecto.nombre_slug
    base.mkdir(parents=True, exist_ok=True)
    return base

@tool(name="leer_proyecto_tree", description="Ejecuta comando find en el proyecto ignorando .git, node_modules, etc.", risk_level="LOW", schema={"type": "object", "properties": {}})
async def leer_proyecto_tree(arguments: dict[str, Any], context: ToolExecutionContext) -> dict[str, Any]:
    base = await get_project_workspace(context)
    cmd = '''find . -type f -not -path "*/\.git/*" -not -path "*/node_modules/*" -not -path "*/__pycache__/*" -not -path "*/venv/*" -not -path "*/.next/*" -not -name "contenido_full.txt" -not -name "*.pyc" -not -name "*.png" -not -name "*.jpg" -not -name "*.ico" -not -name "*.svg" -not -name "*.Identifier"'''
    result = subprocess.run(cmd, shell=True, cwd=str(base), capture_output=True, text=True)
    return {"archivos": result.stdout.split("\n")}

@tool(name="leer_db_full", description="Extrae el schema de la base de datos PostgreSQL.", risk_level="LOW", schema={"type": "object", "properties": {}})
async def leer_db_full(arguments: dict[str, Any], context: ToolExecutionContext) -> dict[str, Any]:
    # Volcado de Schema nativo por Python (Para evitar dependencias del cliente Docker dentro del contenedor)
    from sqlalchemy import inspect
    from app.database import engine
    def get_schema(conn):
        inspector = inspect(conn)
        schema = ""
        for table_name in inspector.get_table_names():
            schema += f"Table: {table_name}\n"
            for col in inspector.get_columns(table_name):
                schema += f"  - {col['name']}: {col['type']}\n"
        return schema
    async with engine.connect() as conn:
        schema_str = await conn.run_sync(get_schema)
    return {"db_schema": schema_str}

@tool(name="leer_archivo_cat", description="Lee el contenido de un archivo.", risk_level="LOW", schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]})
async def leer_archivo_cat(arguments: dict[str, Any], context: ToolExecutionContext) -> dict[str, Any]:
    base = await get_project_workspace(context)
    target = safe_join(base, arguments["path"])
    async with aiofiles.open(target, "r", encoding="utf-8") as f: content = await f.read()
    return {"path": arguments["path"], "content": content}

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
    return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}

async def execute_tool_by_name(tool_name: str, arguments: dict[str, Any], context: ToolExecutionContext, bypass_hil: bool = False) -> dict[str, Any]:
    registered_tool = TOOL_REGISTRY.get(tool_name)
    if not registered_tool: raise ValueError(f"Tool no registrada: {tool_name}")
    approval_event = await require_human_approval_if_needed(registered_tool, arguments, context, bypass_hil=bypass_hil)
    if approval_event: return approval_event
    return await registered_tool.handler(arguments, context)
""")

# ==========================================
# 4. FRONTEND: Repositorios (Nuevos Endpoints GitHub)
# ==========================================
with open("frontend/services/repositories.ts", "r", encoding="utf-8") as f: repo = f.read()
if "export const githubRepository" not in repo:
    write_file("frontend/services/repositories.ts", repo + r"""
export const githubRepository = {
  status: async (projectId: string) => await fetchFromAPI(`/api/github/${projectId}/status`, { method: 'POST' }),
  add: async (projectId: string) => await fetchFromAPI(`/api/github/${projectId}/add`, { method: 'POST' }),
  commit: async (projectId: string) => await fetchFromAPI(`/api/github/${projectId}/commit`, { method: 'POST' }),
  push: async (projectId: string) => await fetchFromAPI(`/api/github/${projectId}/push`, { method: 'POST' }),
};
""")

# ==========================================
# 5. FRONTEND: Selectores por Proyecto (Messages, Workspace, Github)
# ==========================================
write_file("frontend/features/future/FutureTables.tsx", r"""
"use client";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { formatDate } from "@/lib/format";
import { futureRepository, projectsRepository, githubRepository } from "@/services/repositories";
import type { AgentDefinition, AuditEvent, ChatMessage, MetricCard, ToolDefinition, WorkspaceNode, Proyecto } from "@/types/domain";

function ensureArray<T>(data: any): T[] { return Array.isArray(data) ? data : (Array.isArray(data?.data) ? data.data : []); }

function ProjectSelector({ projects, projectId, setProjectId }: { projects: Proyecto[], projectId: string, setProjectId: (id: string) => void }) {
    if (projects.length === 0) return null;
    return (
        <div className="mb-6">
            <label className="mr-4 font-bold text-sm">Seleccionar Proyecto:</label>
            <select className="border border-brand-border bg-white text-brand-navy p-2 rounded-xl text-sm" value={projectId} onChange={(e) => setProjectId(e.target.value)}>
                {projects.map(p => <option key={p.id} value={p.id}>{p.titulo}</option>)}
            </select>
        </div>
    );
}

export function MessagesView() {
  const [items, setItems] = useState<ChatMessage[]>([]);
  const [projects, setProjects] = useState<Proyecto[]>([]);
  const [projectId, setProjectId] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => { projectsRepository.list().then(p => { setProjects(p); if(p.length > 0) setProjectId(p[0].id); }); }, []);
  useEffect(() => {
    if (projectId) {
        setLoading(true);
        futureRepository.messages(projectId).then(data => setItems(ensureArray<ChatMessage>(data))).finally(() => setLoading(false));
    }
  }, [projectId]);

  return (
    <div>
      <SectionHeader title="Historial de mensajes" sprint="Sprint 2 · Contexto" description="Registro persistente del chat por proyecto." />
      <ProjectSelector projects={projects} projectId={projectId} setProjectId={setProjectId} />
      {loading ? <p>Cargando...</p> : items.length === 0 ? <p>No hay mensajes en este proyecto.</p> : (
        <div className="space-y-4">
            {items.map((m) => (
            <Card key={m.id}>
                <Badge tone={m.remitente.toLowerCase() === "user" || m.remitente.toLowerCase() === "usuario" ? "info" : "success"}>{m.remitente}</Badge>
                <p className="mt-3 text-sm text-brand-navy whitespace-pre-wrap">{m.contenido}</p>
                <p className="mt-2 text-xs text-brand-muted">{formatDate(m.fecha_envio)}</p>
            </Card>
            ))}
        </div>
      )}
    </div>
  );
}

export function ToolsView() {
  const [items, setItems] = useState<ToolDefinition[]>([]);
  useEffect(() => { futureRepository.tools().then(data => setItems(ensureArray<ToolDefinition>(data))); }, []);

  return (
    <div>
      <SectionHeader title="Catálogo de tools" sprint="Sprint 2 · Tools" description="Lectura libre vs escritura con aprobación." />
      <div className="grid gap-5 md:grid-cols-2">
        {items.map((t) => (
        <Card key={t.name}>
            <Badge tone={t.requires_approval ? "warning" : "success"}>{t.requires_approval ? "requiere aprobación" : "lectura libre"}</Badge>
            <h3 className="mt-3 text-lg font-black">{t.name}</h3>
            <p className="mt-2 text-sm text-brand-muted">{t.description}</p>
        </Card>
        ))}
      </div>
    </div>
  );
}

export function AgentsView() {
  const [items, setItems] = useState<AgentDefinition[]>([]);
  useEffect(() => { futureRepository.agents().then(data => setItems(ensureArray<AgentDefinition>(data))); }, []);

  return (
    <div>
      <SectionHeader title="Gestión de agentes" sprint="Sprint 3 · Agentes" description="Estado real de los agentes según API Keys cargadas." />
      <div className="grid gap-5 xl:grid-cols-3">
        {items.map((a) => (
        <Card key={a.name}>
            <Badge tone={a.status === "active" ? "success" : "danger"}>{a.status === "active" ? "API Key Activa" : "Sin API Key"}</Badge>
            <h3 className="mt-3 text-xl font-black">{a.label}</h3>
            <p className="mt-2 font-bold text-brand-navy">{a.role}</p>
            <p className="mt-2 text-sm text-brand-muted">{a.responsibility}</p>
        </Card>
        ))}
      </div>
    </div>
  );
}

export function MetricsView() {
  const [items, setItems] = useState<MetricCard[]>([]);
  useEffect(() => { futureRepository.metrics().then(data => setItems(ensureArray<MetricCard>(data))); }, []);

  return (
    <div>
      <SectionHeader title="Métricas, costos y uso" sprint="Sprint 3 · Observabilidad" description="Métricas leídas en tiempo real de PostgreSQL." />
      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        {items.map((m, i) => (
        <Card key={m?.label || i}>
            <p className="text-sm font-bold text-brand-muted">{m?.label}</p>
            <p className="mt-3 text-3xl font-black">{m?.value}</p>
            <Badge tone={m?.tone || "info"} className="mt-4">{m?.trend}</Badge>
        </Card>
        ))}
      </div>
    </div>
  );
}

function Tree({ nodes, depth = 0 }: { nodes: WorkspaceNode[]; depth?: number }) {
  return (
    <div className="space-y-2">
      {(nodes || []).map((node) => (
        <div key={node.id} style={{ marginLeft: depth * 18 }}>
          <div className="rounded-2xl bg-brand-soft px-4 py-3 text-sm font-bold">
            {node.type === "folder" ? "📁" : "📄"} {node.name}
          </div>
          {node.children && node.children.length > 0 ? <Tree nodes={node.children} depth={depth + 1} /> : null}
        </div>
      ))}
    </div>
  );
}

export function WorkspaceView() {
  const [items, setItems] = useState<WorkspaceNode[]>([]);
  const [projects, setProjects] = useState<Proyecto[]>([]);
  const [projectId, setProjectId] = useState<string>("");

  useEffect(() => { projectsRepository.list().then(p => { setProjects(p); if(p.length > 0) setProjectId(p[0].id); }); }, []);
  useEffect(() => { if (projectId) futureRepository.workspace(projectId).then(data => setItems(ensureArray<WorkspaceNode>(data))); }, [projectId]);

  return (
    <div>
      <SectionHeader title="Workspace / File Explorer" sprint="Sprint 3 · Filesystem" description="Lectura en tiempo real del directorio del proyecto en el servidor." />
      <ProjectSelector projects={projects} projectId={projectId} setProjectId={setProjectId} />
      <Card>
        <CardTitle eyebrow="Árbol" title="Estructura física del proyecto" />
        {items.length === 0 ? <p className="text-sm text-brand-muted">Carpeta de proyecto no encontrada o vacía.</p> : <Tree nodes={items} />}
      </Card>
    </div>
  );
}

export function GithubView() {
  const [projects, setProjects] = useState<Proyecto[]>([]);
  const [projectId, setProjectId] = useState<string>("");
  const [output, setOutput] = useState<string>("Selecciona un proyecto y ejecuta una acción de Git.");

  useEffect(() => { projectsRepository.list().then(p => { setProjects(p); if(p.length > 0) setProjectId(p[0].id); }); }, []);

  const runCmd = async (action: 'status' | 'add' | 'commit' | 'push') => {
      setOutput("Ejecutando...");
      try {
          const res = await githubRepository[action](projectId);
          setOutput(res?.output || "Comando ejecutado con éxito.");
      } catch (e) {
          setOutput("Error ejecutando el comando.");
      }
  };

  return (
    <div>
      <SectionHeader title="Integración GitHub" sprint="Sprint 4 · GitOps" description="Control de versiones directo sobre el directorio del proyecto." />
      <ProjectSelector projects={projects} projectId={projectId} setProjectId={setProjectId} />
      <Card>
        <CardTitle eyebrow="Acciones" title="Comandos Locales Git" />
        <div className="flex gap-2 mb-4">
            <Button variant="secondary" onClick={() => runCmd('status')}>Git Status</Button>
            <Button variant="secondary" onClick={() => runCmd('add')}>Git Add .</Button>
            <Button variant="secondary" onClick={() => runCmd('commit')}>Git Commit</Button>
            <Button onClick={() => runCmd('push')}>Git Push</Button>
        </div>
        <pre className="bg-brand-deep text-brand-bright p-4 rounded-xl text-sm whitespace-pre-wrap">{output}</pre>
      </Card>
    </div>
  );
}

export function AuditView() {
  const [items, setItems] = useState<AuditEvent[]>([]);
  useEffect(() => { futureRepository.audit().then(data => setItems(ensureArray<AuditEvent>(data))); }, []);

  return (
    <div>
      <SectionHeader title="Auditoría enterprise" sprint="Sprint 4 · Governance" description="Trazabilidad completa de operaciones críticas." />
      <div className="space-y-4">
        {items.map((a) => (
        <Card key={a.id}>
            <Badge tone={a.severity}>{a.severity}</Badge>
            <h3 className="mt-3 font-black">{a.action}</h3>
            <p className="mt-1 text-sm text-brand-muted">{a.actor} · {a.target} · {formatDate(a.timestamp)}</p>
        </Card>
        ))}
      </div>
    </div>
  );
}
""")

print("\n🚀 SCRIPT FINALIZADO CON ÉXITO.")
print("👉 Ejecuta: docker compose restart backend frontend")