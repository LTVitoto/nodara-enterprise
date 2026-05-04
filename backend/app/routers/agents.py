from fastapi import APIRouter
router = APIRouter()

@router.get("")
async def list_agents():
    return [{"id": "chatgpt", "name": "ChatGPT Fullstack", "status": "active"}]
