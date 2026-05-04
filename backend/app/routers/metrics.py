from fastapi import APIRouter
router = APIRouter()

@router.get("")
async def get_metrics():
    return [
        {"label": "Proyectos", "value": "Activo", "tone": "info", "trend": "global"},
        {"label": "Agentes", "value": "Operativos", "tone": "success", "trend": "runtime"}
    ]
