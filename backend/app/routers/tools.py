from fastapi import APIRouter
from app.services.tools import TOOL_REGISTRY

router = APIRouter()

@router.get("")
async def list_tools():
    return [
        {
            "name": t.name,
            "description": t.description,
            "requires_approval": t.risk_level != "LOW",
            "sprint": 1 if t.name in ["crear_estructura_directorios", "modificar_archivo"] else 2,
            "category": "Escritura" if t.risk_level != "LOW" else "Lectura"
        }
        for t in TOOL_REGISTRY.values()
    ]
