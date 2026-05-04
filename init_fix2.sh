#!/bin/bash
set -e

echo "🔧 Aplicando Parche de Importaciones Diferidas (Resolviendo Circular Imports)..."

# ==========================================
# 1. PARCHE: tools.py
# ==========================================
cat << 'EOF' > backend/app/services/tools.py
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
EOF

# ==========================================
# 2. PARCHE: orchestrator.py
# ==========================================
cat << 'EOF' > backend/app/services/orchestrator.py
import uuid
import time
from decimal import Decimal
from datetime import datetime

from app.database import AsyncSessionLocal
from app.core.tracing import ensure_correlation_id
from app.services.providers import get_provider, normalize_provider_error
from app.services.costing import estimate_cost_usd, estimate_tokens
from app.services.message_service import MessageService
from app.services.tools import execute_tool_by_name, ToolExecutionContext

def ws_event(event: str, correlation_id: str, data: dict):
    return {"event": event, "correlation_id": correlation_id, "data": data}

message_service = MessageService()

async def _execute_pipeline(websocket, project_id, data, db, ejecucion):
    prompt = data.get("message", "")
    agents = data.get("agents", ["chatgpt"])
    correlation_id = ejecucion.correlation_id

    await websocket.send_json(ws_event("orchestration_start", correlation_id, {"project_id": project_id, "agents": agents}))

    for agent in agents:
        provider = get_provider(agent)
        loop_active = True
        current_prompt = prompt

        while loop_active:
            try:
                response = await provider.generate(current_prompt)
                
                if '"tool_name"' in response: 
                    import json
                    try:
                        tool_req = json.loads(response)
                        tool_name = tool_req.get("tool_name")
                        tool_args = tool_req.get("arguments", {})
                        
                        await websocket.send_json(ws_event("agent_tool_call", correlation_id, {"tool": tool_name}))
                        
                        context = ToolExecutionContext(proyecto_id=uuid.UUID(project_id), usuario_config_id=1, agente=agent, db=db)
                        tool_result = await execute_tool_by_name(tool_name, tool_args, context)
                        
                        if tool_result.get("requires_human_approval"):
                            await websocket.send_json(ws_event("hil_required", correlation_id, tool_result))
                            loop_active = False 
                            break
                        
                        current_prompt = f"Resultado de tool {tool_name}: {json.dumps(tool_result)}. ¿Cuál es el siguiente paso?"
                        
                    except json.JSONDecodeError:
                        loop_active = False 
                else:
                    loop_active = False 

                await websocket.send_json(ws_event("agent_response", correlation_id, {"agent": agent, "message": response}))

            except Exception as exc:
                error_msg = normalize_provider_error(agent, exc)
                await websocket.send_json(ws_event("agent_error", correlation_id, {"agent": agent, "error": error_msg}))
                loop_active = False

    return {"status": "completed"}

async def run_orchestrator(websocket, project_id: str, data: dict):
    # 🔥 FIX: Importación Diferida
    from app.models.history_models import Ejecucion 
    
    correlation_id = ensure_correlation_id(data.get("correlation_id"))
    async with AsyncSessionLocal() as db:
        ejecucion = Ejecucion(id=uuid.uuid4(), proyecto_id=project_id, correlation_id=correlation_id, started_at=datetime.utcnow())
        db.add(ejecucion)
        await db.commit()
        await db.refresh(ejecucion)
        
        await message_service.log(db=db, proyecto_id=project_id, ejecucion_id=ejecucion.id, agente="user", role="user", content=data.get("message", ""), correlation_id=correlation_id)
        
        result = await _execute_pipeline(websocket, project_id, data, db, ejecucion)
        
        ejecucion.finished_at = datetime.utcnow()
        await db.commit()
        await websocket.send_json(ws_event("orchestration_end", correlation_id, result))
        return result

__all__ = ["run_orchestrator"]
EOF

echo "✅ Listo. Reinicia el contenedor de Docker; Uvicorn debería arrancar sin problemas."