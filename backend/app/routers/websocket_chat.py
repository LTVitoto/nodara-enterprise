import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.audit import EventoAuditoria
router = APIRouter()
@router.websocket('/ws/chat/{project_id}')
async def websocket_endpoint(websocket: WebSocket, project_id: str, db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    try:
        audit = EventoAuditoria(actor='User', action='Inicio conversación', target=str(project_id)[:8]+'...', severity='info')
        db.add(audit)
        await db.commit()
    except: pass
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data) if data.startswith('{') else {'message': data}
            msg = payload.get('message', data)
            audit_msg = EventoAuditoria(actor='User', action='Mensaje Enviado', target=str(project_id)[:8]+'...', severity='success')
            db.add(audit_msg)
            await db.commit()
            await websocket.send_text(json.dumps({'event': 'message', 'data': {'agent': 'Orquestador', 'message': f'Mensaje procesado: {msg}'}}))
    except WebSocketDisconnect:
        pass
