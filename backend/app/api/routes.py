from fastapi import APIRouter

router = APIRouter(prefix="/api")

@router.get("/config")
def get_config():
    return {
        "app_name": "Orquestador Multi-Agente",
        "version": "1.0",
        "env": "dev"
    }

@router.get("/projects")
def get_projects():
    return [
        {"id": "1", "name": "Proyecto Demo"},
        {"id": "2", "name": "NODARA"}
    ]

@router.get("/metrics/usage")
def get_metrics():
    return {
        "total_requests": 120,
        "total_tokens": 45000,
        "total_cost_usd": 12.5
    }