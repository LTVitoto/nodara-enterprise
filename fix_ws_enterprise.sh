#!/bin/bash
set -e

echo "🏗️ RESTAURANDO ARQUITECTURA ENTERPRISE PARA WEBSOCKETS..."

# ==========================================
# 1. ROUTER DEDICADO (El código que validaste)
# ==========================================
cat << 'EOF' > backend/app/routers/websocket_chat.py
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from uuid import UUID
import logging
from app.services.orchestrator import run_orchestrator

logger = logging.getLogger("websocket")
router = APIRouter()

@router.websocket("/ws/chat/{proyecto_id}")
async def websocket_chat(
    websocket: WebSocket,
    proyecto_id: UUID,
    usuario_config_id: int = Query(default=1),
):
    await websocket.accept()
    logger.info(f"WS Handshake aceptado | Proyecto: {proyecto_id}")
    try:
        while True:
            payload = await websocket.receive_json()
            message = payload.get("message") or payload.get("content")
            correlation_id = payload.get("correlation_id", "req-000")

            if not message:
                await websocket.send_json({"event": "error", "data": {"message": "Payload inválido"}})
                continue

            # Delegamos al Orquestador Funcional inyectando los parámetros validados
            await run_orchestrator(websocket, str(proyecto_id), usuario_config_id, payload)
            
    except WebSocketDisconnect:
        logger.info(f"WS Desconectado | Proyecto: {proyecto_id}")
    except Exception as e:
        logger.error(f"Error crítico en capa WS: {e}")
EOF

# ==========================================
# 2. ORQUESTADOR (Adaptado para recibir los nuevos parámetros)
# ==========================================
cat << 'EOF' > backend/app/services/orchestrator.py
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

async def _execute_pipeline(websocket, project_id: uuid.UUID, usuario_config_id: int, data: dict, db, ejecucion):
    prompt = data.get("message", "")
    agents = data.get("agents", ["chatgpt"])
    correlation_id = ejecucion.correlation_id

    await websocket.send_json(ws_event("orchestration_start", correlation_id, {"project_id": str(project_id), "agents": agents}))

    for agent in agents:
        try:
            provider = get_provider(agent)
        except Exception as provider_err:
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
                        
                        context = ToolExecutionContext(
                            proyecto_id=project_id, 
                            usuario_config_id=usuario_config_id, 
                            agente=agent, 
                            db=db
                        )
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

async def run_orchestrator(websocket, proyecto_id: str, usuario_config_id: int, data: dict):
    from app.models.history_models import Ejecucion 
    correlation_id = ensure_correlation_id(data.get("correlation_id"))
    
    # 🛡️ Validación estricta de UUID para prevenir crashes en Postgres
    try:
        p_id = uuid.UUID(proyecto_id)
    except ValueError:
        await websocket.send_json(ws_event("error", correlation_id, {"message": "UUID de proyecto inválido"}))
        return {"status": "error"}
    
    try:
        async with AsyncSessionLocal() as db:
            ejecucion = Ejecucion(id=uuid.uuid4(), proyecto_id=p_id, correlation_id=correlation_id, started_at=datetime.utcnow())
            db.add(ejecucion)
            await db.commit()
            await db.refresh(ejecucion)
            
            try:
                await message_service.log(
                    db=db, proyecto_id=p_id, ejecucion_id=ejecucion.id, 
                    agente="user", role="user", content=data.get("message", ""), correlation_id=correlation_id
                )
            except Exception as sql_err:
                print(f"⚠️ Warning DB: {sql_err}")
            
            result = await _execute_pipeline(websocket, p_id, usuario_config_id, data, db, ejecucion)
            
            ejecucion.finished_at = datetime.utcnow()
            await db.commit()
            await websocket.send_json(ws_event("orchestration_end", correlation_id, result))
            return result
    except Exception as e:
        await websocket.send_json(ws_event("agent_error", correlation_id, {"agent": "orchestrator", "error": f"Fallo Crítico: {str(e)}"}))
        return {"status": "error"}
EOF

# ==========================================
# 3. MAIN.PY (Limpieza total)
# ==========================================
cat << 'EOF' > backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.database import init_db
from app.routers import projects, approvals, config, health, audit, metrics, tools, agents, websocket_chat

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("orchestrator")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Inicializando Base de Datos Enterprise...")
    try:
        await init_db()
        logger.info("Base de datos sincronizada.")
    except Exception as e:
        logger.error(f"Error inicializando BD: {e}")
    yield
    logger.info("Shutdown completado.")

app = FastAPI(title="NODARA Enterprise", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 MONTAMOS TODOS LOS ROUTERS
app.include_router(health.router, tags=["Health"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(approvals.router, prefix="/api/approvals", tags=["Approvals"])
app.include_router(config.router, prefix="/api/config", tags=["Config"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["Metrics"])
app.include_router(tools.router, prefix="/api/tools", tags=["Tools"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])

# 🔥 EL ROUTER DEDICADO DE WEBSOCKETS
app.include_router(websocket_chat.router, tags=["Websockets"])
EOF

echo "✅ ARQUITECTURA LIMPIA. Reiniciando backend..."