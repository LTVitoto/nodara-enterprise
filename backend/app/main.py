from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db
from app.routers import projects, approvals, config, health, audit, metrics, tools, agents, websocket_chat, files, github
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
app.include_router(health.router, tags=['Health'])
app.include_router(projects.router, prefix='/api/projects', tags=['Projects'])
app.include_router(approvals.router, prefix='/api/approvals', tags=['Approvals'])
app.include_router(config.router, prefix='/api/config', tags=['Config'])
app.include_router(audit.router, prefix='/api/audit', tags=['Audit'])
app.include_router(metrics.router, prefix='/api/metrics', tags=['Metrics'])
app.include_router(tools.router, prefix='/api/tools', tags=['Tools'])
app.include_router(agents.router, prefix='/api/agents', tags=['Agents'])
app.include_router(files.router, prefix='/api/files', tags=['Files'])
app.include_router(github.router, prefix='/api/github', tags=['Github'])
app.include_router(websocket_chat.router, tags=['Websockets'])
