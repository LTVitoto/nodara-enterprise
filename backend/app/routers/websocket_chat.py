from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.services.orchestrator import MultiAgentOrchestrator
from app.services.ws_events import ws_error

router = APIRouter()
settings = get_settings()


@router.websocket("/ws/chat/{proyecto_id}")
async def websocket_chat(
    websocket: WebSocket,
    proyecto_id: UUID,
    usuario_config_id: int = Query(default=1),
):
    await websocket.accept()
    orchestrator = MultiAgentOrchestrator()

    try:
        while True:
            payload = await websocket.receive_json()
            message = payload.get("message") or payload.get("content")
            correlation_id = payload.get("correlation_id")

            if not message:
                await websocket.send_json(ws_error("Payload inválido. Debe incluir 'message'.", correlation_id))
                continue

            async with AsyncSessionLocal() as db:
                await orchestrator.handle_architect_message(
                    websocket=websocket,
                    db=db,
                    proyecto_id=proyecto_id,
                    usuario_config_id=usuario_config_id,
                    message=message,
                    correlation_id=correlation_id,
                )
    except WebSocketDisconnect:
        return
    except Exception as exc:
        try:
            await websocket.send_json(ws_error(str(exc)))
        except Exception:
            return
