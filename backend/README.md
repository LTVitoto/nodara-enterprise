# Backend Orquestador Multi-Agente Enterprise Sprint 1

Backend FastAPI alineado a las decisiones cerradas por Gemini:

- PostgreSQL async con SQLAlchemy.
- `proyectos.id` UUIDv4 generado desde Python.
- 5 tablas canónicas de Sprint 1.
- WebSocket `/ws/chat/{proyecto_id}`.
- Router lógico Gemini / ChatGPT / Claude / Alineación.
- `USE_MOCK_APIS=True` por defecto.
- Tool Calling con Human-in-the-Loop.
- Manejo híbrido de archivos temporales.

## Instalación en Docker Compose actual

Descomprime este ZIP y reemplaza la carpeta `backend/` del proyecto.

Tu `.env` raíz debe incluir:

```env
USE_MOCK_APIS=True
BASE_PROJECTS_DIR=/home/vitoto/email@victorfigueroa.cl
POSTGRES_USER=arquitecto
POSTGRES_PASSWORD=super_password_secreta_123
POSTGRES_DB=orquestador_db
POSTGRES_PORT=5432
POSTGRES_HOST=db
DATABASE_URL=postgresql+asyncpg://arquitecto:super_password_secreta_123@db:5432/orquestador_db
```

Luego:

```bash
docker compose down
docker compose up -d --build
```

Validar:

```bash
curl -i http://localhost:8000/health
```
