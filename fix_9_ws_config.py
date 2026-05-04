import os

print("🔥 INICIANDO CORRECCIÓN CRÍTICA DE WEBSOCKETS Y CONFIG...")

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"✅ Archivo corregido: {path}")

# ==========================================
# 1. FIX: ENDPOINT PATCH CONFIG (Faltante)
# ==========================================
write_file("backend/app/routers/config.py", r"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter()

@router.get("")
async def get_config(db: AsyncSession = Depends(get_db)):
    try:
        from app.models.governance import UsuarioConfig
        result = await db.execute(select(UsuarioConfig))
        configs = result.scalars().all()
        if not configs:
            return [{"id": 1, "auto_aprobar_ejecucion": False}]
        return configs
    except Exception as e:
        print(f"Error en BD Config: {e}")
        return [{"id": 1, "auto_aprobar_ejecucion": False, "error": str(e)}]

@router.patch("/{config_id}")
async def update_config(config_id: int, payload: dict, db: AsyncSession = Depends(get_db)):
    try:
        from app.models.governance import UsuarioConfig
        config_obj = await db.get(UsuarioConfig, config_id)
        if not config_obj:
            raise HTTPException(status_code=404, detail="Config no encontrada")
        
        for key, value in payload.items():
            if hasattr(config_obj, key):
                setattr(config_obj, key, value)
                
        await db.commit()
        await db.refresh(config_obj)
        return config_obj
    except Exception as e:
        print(f"Error actualizando config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
""")

# ==========================================
# 2. FIX: ORCHESTRATOR Y WS (Captura de Errores y Feedback de IA)
# ==========================================
write_file("backend/app/services/orchestrator.py", r"""
import uuid
from datetime import datetime
from app.database import AsyncSessionLocal
from app.core.tracing import ensure_correlation_id
from app.services.providers import get_provider, normalize_provider_error
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
        try:
            provider = get_provider(agent)
        except Exception as provider_err:
            # Captura de error de API KEY faltante sin botar el WS
            await websocket.send_json(ws_event("agent_error", correlation_id, {"agent": agent, "error": str(provider_err)}))
            continue
            
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
    from app.models.history_models import Ejecucion 
    correlation_id = ensure_correlation_id(data.get("correlation_id"))
    
    try:
        async with AsyncSessionLocal() as db:
            ejecucion = Ejecucion(id=uuid.uuid4(), proyecto_id=project_id, correlation_id=correlation_id, started_at=datetime.utcnow())
            db.add(ejecucion)
            await db.commit()
            await db.refresh(ejecucion)
            
            # 🔥 Guardado Seguro del primer mensaje (sin crashear si fallan columnas)
            try:
                await message_service.log(db=db, proyecto_id=project_id, ejecucion_id=ejecucion.id, agente="user", role="user", content=data.get("message", ""), correlation_id=correlation_id)
            except Exception as sql_err:
                print(f"⚠️ Warning: No se pudo guardar en DB (Ignorando para no tumbar WS): {sql_err}")
            
            result = await _execute_pipeline(websocket, project_id, data, db, ejecucion)
            
            ejecucion.finished_at = datetime.utcnow()
            await db.commit()
            await websocket.send_json(ws_event("orchestration_end", correlation_id, result))
            return result
    except Exception as e:
        # Blindaje maestro del WS
        await websocket.send_json(ws_event("agent_error", correlation_id, {"agent": "orchestrator", "error": f"Fallo Crítico: {str(e)}"}))
        return {"status": "error"}

__all__ = ["run_orchestrator"]
""")

print("\n🚀 LISTO. Reinicia tu contenedor Backend.")