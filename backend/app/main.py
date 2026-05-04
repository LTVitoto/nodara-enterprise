from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.database import init_db
from app.routers import projects, approvals, config, health, audit, metrics, tools, agents
# Importación diferida para el orquestador
from app.services.orchestrator import run_orchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("orchestrator")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Inicializando Base de Datos Enterprise...")
    try:
        await init_db()
        logger.info("Base de datos sincronizada.")
    except Exception as e:
        logger.error(f"Error inicializando BD: {e}")
    yield
    logger.info("Shutdown completado.")

app = FastAPI(title="NODARA Enterprise", version="2.0.0", lifespan=lifespan)

# CORS TOTALMENTE PERMISIVO PARA DESARROLLO LOCAL
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(approvals.router, prefix="/api/approvals", tags=["Approvals"])
app.include_router(config.router, prefix="/api/config", tags=["Config"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["Metrics"])
app.include_router(tools.router, prefix="/api/tools", tags=["Tools"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])

@app.websocket("/ws/chat/{project_id}")
async def ws_chat(websocket: WebSocket, project_id: str):
    await websocket.accept()
    logger.info(f"WS Conectado: {project_id}")
    try:
        while True:
            data = await websocket.receive_json()
            await run_orchestrator(websocket, project_id, data)
    except WebSocketDisconnect:
        logger.info("WS Desconectado normalmente.")
    except Exception as e:
        logger.error(f"WS Error Crítico: {e}")
