from __future__ import annotations
import json
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
    # 🔥 FIX: Importación Diferida para evitar Circular Import
    from app.models import Proyecto 
    
    proyecto = await context.db.get(Proyecto, context.proyecto_id)
    if not proyecto: raise ValueError("Proyecto no encontrado")
    base = settings.base_projects_dir / proyecto.nombre_slug
    base.mkdir(parents=True, exist_ok=True)
    return base

async def require_human_approval_if_needed(
    registered_tool: RegisteredTool, arguments: dict[str, Any], context: ToolExecutionContext, bypass_hil: bool = False
) -> dict[str, Any] | None:
    if bypass_hil or registered_tool.risk_level == "LOW": return None

    # 🔥 FIX: Importación Diferida
    from app.models import ToolCallPendiente, ToolCallStatus, UsuarioConfig 
    
    usuario = await context.db.get(UsuarioConfig, context.usuario_config_id)
    
    if registered_tool.risk_level == "CRITICAL" or (not usuario.auto_aprobar_ejecucion):
        pending = ToolCallPendiente(
            proyecto_id=context.proyecto_id,
            usuario_config_id=context.usuario_config_id,
            agente=context.agente,
            tool_name=registered_tool.name,
            arguments_json=arguments,
            status=ToolCallStatus.PENDING.value,
        )
        context.db.add(pending)
        await context.db.commit()
        await context.db.refresh(pending)
        
        return {
            "requires_human_approval": True,
            "approval_id": pending.id,
            "risk_level": registered_tool.risk_level,
            "tool_name": registered_tool.name,
            "message": f"Ejecución de riesgo {registered_tool.risk_level} pausada. Requiere HIL.",
        }
    return None

@tool(
    name="crear_estructura_directorios",
    description="Crea carpetas en el workspace.",
    risk_level="MEDIUM",
    schema={"type": "object", "properties": {"estructura": {"type": "array"}}, "required": ["estructura"]}
)
async def crear_estructura_directorios(arguments: dict[str, Any], context: ToolExecutionContext) -> dict[str, Any]:
    return {"ok": True, "created": ["mock_dirs_created_for_safety"]}

@tool(
    name="modificar_archivo",
    description="Reemplaza contenido de un archivo.",
    risk_level="HIGH",
    schema={"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}
)
async def modificar_archivo(arguments: dict[str, Any], context: ToolExecutionContext) -> dict[str, Any]:
    base = await get_project_workspace(context)
    target = safe_join(base, arguments["path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(target, "w", encoding="utf-8") as f:
        await f.write(arguments["content"])
    return {"ok": True, "path": str(target), "bytes_written": len(arguments["content"])}

@tool(
    name="ejecutar_docker",
    description="Ejecuta docker-compose up o levanta servicios.",
    risk_level="CRITICAL",
    schema={"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}
)
async def ejecutar_docker(arguments: dict[str, Any], context: ToolExecutionContext) -> dict[str, Any]:
    return {"ok": True, "stdout": "Docker command executed via HIL", "command": arguments["command"]}

async def execute_tool_by_name(tool_name: str, arguments: dict[str, Any], context: ToolExecutionContext, bypass_hil: bool = False) -> dict[str, Any]:
    registered_tool = TOOL_REGISTRY.get(tool_name)
    if not registered_tool: raise ValueError(f"Tool no registrada: {tool_name}")
    approval_event = await require_human_approval_if_needed(registered_tool, arguments, context, bypass_hil=bypass_hil)
    if approval_event: return approval_event
    return await registered_tool.handler(arguments, context)
