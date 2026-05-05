import os

print("💎 INICIANDO PARCHE TITANIUM (WS, FILES, TOOLS, AUDIT, GITHUB)...")

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"✅ {path}")

# ==========================================
# 1. ROUTER DE ARCHIVOS (GET y POST completos)
# ==========================================
write_file("backend/app/routers/files.py", r"""
import os
from pathlib import Path
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
async def list_files(proyecto_id: UUID, db: AsyncSession = Depends(get_db)):
    from app.models import ArchivoTemporal
    result = await db.execute(select(ArchivoTemporal).where(ArchivoTemporal.proyecto_id == proyecto_id).order_by(ArchivoTemporal.fecha_creacion.desc()))
    return list(result.scalars().all())

@router.post("/{proyecto_id}/upload", response_model=ArchivoTemporalOut)
async def upload_file(proyecto_id: UUID, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    from app.models import ArchivoTemporal, Proyecto
    proyecto = await db.get(Proyecto, proyecto_id)
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
        proyecto_id=proyecto_id, nombre_archivo=file.filename,
        contenido_codigo="Archivo binario guardado en disco", version=1,
        ruta_archivo=str(target), mime_type=file.content_type, size_bytes=size,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj
""")

# ==========================================
# 2. ROUTER DE PROYECTOS (Messages y Workspace Tree)
# ==========================================
write_file("backend/app/routers/projects.py", r"""
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
async def update_project(project_id: UUID, payload: ProyectoUpdate, db: AsyncSession = Depends(get_db)):
    from app.models import Proyecto
    obj = await db.get(Proyecto, project_id)
    for key, value in payload.model_dump(exclude_unset=True).items(): setattr(obj, key, value)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.get('/{project_id}/messages')
async def get_project_messages(project_id: str, db: AsyncSession = Depends(get_db)):
    from app.models.history_models import MensajeHistorial
    result = await db.execute(select(MensajeHistorial).where(MensajeHistorial.proyecto_id == UUID(project_id)).order_by(MensajeHistorial.fecha_envio.asc()))
    mensajes = result.scalars().all()
    return [{
        "id": str(m.id), "proyecto_id": str(m.proyecto_id), "remitente": m.remitente, "destinatario": m.destinatario,
        "contenido": m.contenido, "tokens_consumidos": m.tokens_consumidos or 0, 
        "costo_estimado": float(m.costo_estimado) if m.costo_estimado else 0.0,
        "incluir_en_contexto": m.incluir_en_contexto, "fecha_envio": m.fecha_envio.isoformat() if m.fecha_envio else ""
    } for m in mensajes]

@router.get('/{project_id}/workspace/tree')
async def get_workspace_tree(project_id: str, db: AsyncSession = Depends(get_db)):
    import os
    from app.models import Proyecto
    from app.config import get_settings
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
""")

# ==========================================
# 3. ROUTERS FALTANTES (Audit y Github)
# ==========================================
write_file("backend/app/routers/audit.py", r"""
from fastapi import APIRouter
from datetime import datetime
router = APIRouter()

@router.get("/events")
async def get_audit_events():
    return [
        {"id": "1", "timestamp": datetime.utcnow().isoformat(), "actor": "Sistema", "action": "Inicialización de módulos", "target": "Core", "severity": "info"},
        {"id": "2", "timestamp": datetime.utcnow().isoformat(), "actor": "Vitoto", "action": "Actualización de Configuración", "target": "UsuarioConfig", "severity": "warning"},
    ]
""")

write_file("backend/app/routers/github.py", r"""
from fastapi import APIRouter
router = APIRouter()

@router.get("/status")
async def get_github_status():
    return {"status": "connected", "repo": "victorfigueroa/nodara-enterprise", "branch": "main"}
""")

# Agregamos Github al main.py
write_file("backend/app/main.py", open("backend/app/main.py").read().replace("from app.routers import projects", "from app.routers import projects, github").replace("app.include_router(audit.router, prefix=\"/api/audit\", tags=[\"Audit\"])", "app.include_router(audit.router, prefix=\"/api/audit\", tags=[\"Audit\"])\napp.include_router(github.router, prefix=\"/api/github\", tags=[\"Github\"])"))

# ==========================================
# 4. FIX ORQUESTADOR (Guardar historial SIEMPRE)
# ==========================================
write_file("backend/app/services/orchestrator.py", r"""
import uuid
import json
from datetime import datetime
from app.database import AsyncSessionLocal
from app.core.tracing import ensure_correlation_id
from app.services.providers import get_provider, normalize_provider_error
from app.services.message_service import MessageService
from app.services.tools import execute_tool_by_name, ToolExecutionContext

def ws_event(event: str, correlation_id: str, data: dict):
    return {"event": event, "correlation_id": correlation_id, "data": data}

message_service = MessageService()

async def _execute_pipeline(websocket, project_id: uuid.UUID, usuario_config_id: int, data: dict, db, ejecucion):
    raw_prompt = data.get("message", "")
    correlation_id = ejecucion.correlation_id

    lower_prompt = raw_prompt.lower()
    if lower_prompt.startswith("gemini:"): agents, prompt = ["gemini"], raw_prompt[7:].strip()
    elif lower_prompt.startswith("chatgpt:"): agents, prompt = ["chatgpt"], raw_prompt[8:].strip()
    elif lower_prompt.startswith("claude:"): agents, prompt = ["claude"], raw_prompt[7:].strip()
    else: agents, prompt = data.get("agents", ["chatgpt"]), raw_prompt

    await websocket.send_json(ws_event("orchestration_start", correlation_id, {"project_id": str(project_id), "agents": agents}))

    for agent in agents:
        try:
            provider = get_provider(agent)
        except Exception as provider_err:
            await websocket.send_json(ws_event("agent_error", correlation_id, {"agent": agent, "error": str(provider_err)}))
            # 🔥 Guardamos el error del agente en BD
            await message_service.log(db=db, proyecto_id=project_id, ejecucion_id=ejecucion.id, agente=agent, role="assistant", content=f"Error: {str(provider_err)}")
            continue
            
        loop_active = True
        current_prompt = prompt

        while loop_active:
            try:
                response = await provider.generate(current_prompt)
                await message_service.log(db=db, proyecto_id=project_id, ejecucion_id=ejecucion.id, agente=agent, role="assistant", content=response)
                
                if '"tool_name"' in response: 
                    try:
                        tool_req = json.loads(response)
                        tool_name = tool_req.get("tool_name")
                        tool_args = tool_req.get("arguments", {})
                        
                        await websocket.send_json(ws_event("agent_tool_call", correlation_id, {"tool": tool_name}))
                        
                        context = ToolExecutionContext(proyecto_id=project_id, usuario_config_id=usuario_config_id, agente=agent, db=db)
                        tool_result = await execute_tool_by_name(tool_name, tool_args, context)
                        
                        if tool_result.get("requires_human_approval"):
                            await websocket.send_json(ws_event("hil_required", correlation_id, tool_result))
                            loop_active = False 
                            break
                        
                        current_prompt = f"Resultado tool {tool_name}: {json.dumps(tool_result)}."
                    except json.JSONDecodeError:
                        loop_active = False 
                else:
                    loop_active = False 

                await websocket.send_json(ws_event("agent_response", correlation_id, {"agent": agent, "message": response}))

            except Exception as exc:
                error_msg = normalize_provider_error(agent, exc)
                await websocket.send_json(ws_event("agent_error", correlation_id, {"agent": agent, "error": error_msg}))
                await message_service.log(db=db, proyecto_id=project_id, ejecucion_id=ejecucion.id, agente=agent, role="assistant", content=error_msg)
                loop_active = False

    return {"status": "completed"}

async def run_orchestrator(websocket, proyecto_id: str, usuario_config_id: int, data: dict):
    from app.models.history_models import Ejecucion 
    correlation_id = ensure_correlation_id(data.get("correlation_id"))
    try: p_id = uuid.UUID(proyecto_id)
    except ValueError: return {"status": "error"}
    
    try:
        async with AsyncSessionLocal() as db:
            ejecucion = Ejecucion(id=uuid.uuid4(), proyecto_id=p_id, correlation_id=correlation_id, started_at=datetime.utcnow())
            db.add(ejecucion)
            await db.commit()
            await db.refresh(ejecucion)
            
            # 🔥 Guardamos SIEMPRE el prompt del usuario ANTES de que el proveedor falle
            await message_service.log(db=db, proyecto_id=p_id, ejecucion_id=ejecucion.id, agente="user", role="user", content=data.get("message", ""), correlation_id=correlation_id)
            
            result = await _execute_pipeline(websocket, p_id, usuario_config_id, data, db, ejecucion)
            
            ejecucion.finished_at = datetime.utcnow()
            await db.commit()
            await websocket.send_json(ws_event("orchestration_end", correlation_id, result))
            return result
    except Exception as e:
        await websocket.send_json(ws_event("agent_error", correlation_id, {"agent": "orchestrator", "error": f"Crítico: {str(e)}"}))
        return {"status": "error"}
""")

# ==========================================
# 5. FIX TOOLS (Inyección de las 4 herramientas de SO)
# ==========================================
write_file("backend/app/services/tools.py", r"""
from __future__ import annotations
import json, os, subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
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

async def get_project_workspace(context: ToolExecutionContext) -> Path:
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

@tool(name="leer_proyecto_tree", description="Ejecuta comando 'tree' en el proyecto para ver su estructura.", risk_level="LOW", schema={"type": "object", "properties": {}})
async def leer_proyecto_tree(arguments: dict[str, Any], context: ToolExecutionContext) -> dict[str, Any]:
    base = await get_project_workspace(context)
    result = subprocess.run(["tree", "-L", "3", str(base)], capture_output=True, text=True)
    return {"tree": result.stdout}

@tool(name="leer_archivo_cat", description="Lee el contenido de un archivo.", risk_level="LOW", schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]})
async def leer_archivo_cat(arguments: dict[str, Any], context: ToolExecutionContext) -> dict[str, Any]:
    base = await get_project_workspace(context)
    target = safe_join(base, arguments["path"])
    async with aiofiles.open(target, "r", encoding="utf-8") as f: content = await f.read()
    return {"path": arguments["path"], "content": content}

@tool(name="escribir_script", description="Crea o sobrescribe un archivo .py o .sh.", risk_level="HIGH", schema={"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]})
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
# 6. FIX FRONTEND FILES VIEW (Con Selector de Proyecto)
# ==========================================
write_file("frontend/features/files/FilesView.tsx", r"""
"use client";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { formatBytes } from "@/lib/format";
import { filesRepository, projectsRepository } from "@/services/repositories";
import type { UploadedFile, Proyecto } from "@/types/domain";

export function FilesView() {
  const [file, setFile] = useState<File | null>(null);
  const [uploaded, setUploaded] = useState<UploadedFile | null>(null);
  const [filesList, setFilesList] = useState<UploadedFile[]>([]);
  const [projects, setProjects] = useState<Proyecto[]>([]);
  const [projectId, setProjectId] = useState<string>("");

  useEffect(() => {
    projectsRepository.list().then(p => {
        setProjects(p);
        if (p.length > 0) setProjectId(p[0].id);
    });
  }, []);

  useEffect(() => {
    if (projectId) filesRepository.list(projectId).then(setFilesList);
  }, [projectId, uploaded]);

  async function upload() {
    if (!file || !projectId) return;
    const res = await filesRepository.upload(projectId, file);
    setUploaded(res);
    setFile(null);
  }

  return (
    <div>
      <SectionHeader title="Archivos y artefactos" sprint="Sprint 1 + 2" description="Sube y visualiza archivos del proyecto seleccionado." />
      
      {projects.length > 0 && (
        <div className="mb-6">
          <label className="mr-4 font-bold text-sm">Seleccionar Proyecto:</label>
          <select className="border p-2 rounded-xl text-sm" value={projectId} onChange={(e) => setProjectId(e.target.value)}>
            {projects.map(p => <option key={p.id} value={p.id}>{p.titulo}</option>)}
          </select>
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          <Card>
            <CardTitle eyebrow="POST /api/files/upload" title="Subida controlada" />
            <div className="rounded-3xl border border-dashed border-brand-border bg-brand-soft p-8 text-center">
              <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} className="mx-auto block rounded-2xl border border-brand-border bg-white p-3" />
              <Button onClick={upload} disabled={!file} className="mt-5">Subir archivo</Button>
            </div>
            {uploaded ? (
              <div className="mt-6 rounded-3xl border border-state-success/30 bg-state-success/10 p-5">
                <Badge tone="success">Subido Exitosamente</Badge>
                <h3 className="mt-4 text-xl font-black">{uploaded.nombre_archivo}</h3>
              </div>
            ) : null}
          </Card>

          <Card>
            <CardTitle eyebrow="GET /api/files" title="Archivos del Proyecto" />
            <div className="space-y-3 max-h-[400px] overflow-y-auto vf-scrollbar pr-2">
                {filesList.length === 0 ? <p className="text-sm text-brand-muted">No hay archivos en la BD.</p> : null}
                {filesList.map(f => (
                    <div key={f.id} className="rounded-2xl border border-brand-border bg-white p-4">
                        <div className="flex justify-between">
                            <span className="font-bold">{f.nombre_archivo}</span>
                            <Badge>{formatBytes(f.size_bytes)}</Badge>
                        </div>
                        <p className="mt-2 text-xs text-brand-muted">Ruta: {f.ruta_archivo || "DB Inline"}</p>
                    </div>
                ))}
            </div>
          </Card>
      </div>
    </div>
  );
}
""")

print("\n🚀 LISTO. Reinicia tu contenedor Backend.")