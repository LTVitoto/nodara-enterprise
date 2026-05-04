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
