from fastapi import APIRouter
from datetime import datetime
router = APIRouter()

@router.get("/events")
async def get_audit_events():
    return [
        {"id": "1", "timestamp": datetime.utcnow().isoformat(), "actor": "Sistema", "action": "Inicialización de módulos", "target": "Core", "severity": "info"},
        {"id": "2", "timestamp": datetime.utcnow().isoformat(), "actor": "Vitoto", "action": "Actualización de Configuración", "target": "UsuarioConfig", "severity": "warning"},
    ]
