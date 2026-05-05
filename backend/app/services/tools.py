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
