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
