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
