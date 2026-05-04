from fastapi import APIRouter
router = APIRouter()

@router.get("/events")
async def get_audit_events():
    # Retorno estricto para la tabla de auditoría
    return []
