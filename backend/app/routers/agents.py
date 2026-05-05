from fastapi import APIRouter
from app.config import get_settings

router = APIRouter()
settings = get_settings()

def _check_key(key):
    return bool(key) and "tu_llave" not in key.lower()

@router.get("")
async def list_agents():
    return [
        {"name": "gemini", "label": "Gemini", "role": "Infraestructura", "responsibility": "Docker, red, variables, despliegue", "sprint": 1, "status": "active" if _check_key(settings.gemini_api_key) else "disabled"},
        {"name": "chatgpt", "label": "ChatGPT", "role": "Backend y Datos", "responsibility": "FastAPI, PostgreSQL, WebSockets", "sprint": 1, "status": "active" if _check_key(settings.openai_api_key) else "disabled"},
        {"name": "claude", "label": "Claude", "role": "Frontend y UX", "responsibility": "Next.js, Tailwind, React", "sprint": 1, "status": "active" if _check_key(settings.anthropic_api_key) else "disabled"}
    ]
