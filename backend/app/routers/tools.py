from fastapi import APIRouter
router = APIRouter()

@router.get("")
async def list_tools():
    return [{"name": "filesystem_guard", "description": "Control de archivos", "risk_level": "HIGH"}]
