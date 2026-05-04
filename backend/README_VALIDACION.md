# Validación Backend Orquestador Multi-Agente

## 1. Levantar stack

Desde la raíz `/orquestador-multi-agente`:

```bash
docker compose down
docker compose up -d --build
```

## 2. Logs

```bash
docker logs -f orquestador_backend
```

Esperado:

```text
Application startup complete.
```

## 3. Health

```bash
curl -i http://localhost:8000/health
```

Esperado:

```json
{"status":"ok"}
```

## 4. Tablas

```bash
docker exec -it orquestador_db psql -U arquitecto -d orquestador_db -c "\dt"
```

Esperado:

```text
archivos_temporales
mensajes_historial
proyectos
tool_calls_pendientes
usuarios_config
```

## 5. Crear proyecto

```bash
curl -s -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Demo Orquestador Enterprise",
    "anio": 2026,
    "descripcion": "Validación Sprint 1",
    "tecnologias": {"backend": "FastAPI", "db": "PostgreSQL"},
    "microservicios": {"backend": true, "frontend": true}
  }'
```

Guarda el `id` UUID retornado.

## 6. WebSocket mock

Reemplaza `<PROJECT_UUID>` por el ID del proyecto:

```bash
docker exec -i orquestador_backend python - <<'PY'
import asyncio, json, websockets

PROJECT_UUID = "<PROJECT_UUID>"

async def main():
    async with websockets.connect(f"ws://localhost:8000/ws/chat/{PROJECT_UUID}?usuario_config_id=1") as ws:
        await ws.send(json.dumps({
            "message": "Alineación: cada agente debe reportar su responsabilidad.",
            "correlation_id": "alineacion-mock-001"
        }))
        while True:
            msg = await ws.recv()
            print(msg)
            if '"orchestration_end"' in msg:
                break

asyncio.run(main())
PY
```

## 7. Human-in-the-Loop

Deja aprobación manual:

```bash
curl -s -X PATCH http://localhost:8000/api/config/1 \
  -H "Content-Type: application/json" \
  -d '{"auto_aprobar_ejecucion": false}'
```

Pide una escritura por WebSocket:

```bash
docker exec -i orquestador_backend python - <<'PY'
import asyncio, json, websockets

PROJECT_UUID = "<PROJECT_UUID>"

async def main():
    async with websockets.connect(f"ws://localhost:8000/ws/chat/{PROJECT_UUID}?usuario_config_id=1") as ws:
        await ws.send(json.dumps({
            "message": "ChatGPT: crea un archivo README_TEST.md con una validación del backend.",
            "correlation_id": "hil-001"
        }))
        while True:
            msg = await ws.recv()
            print(msg)
            if '"human_approval_required"' in msg or '"orchestration_end"' in msg:
                break

asyncio.run(main())
PY
```

Lista aprobaciones:

```bash
curl -s http://localhost:8000/api/approvals
```

Aprueba:

```bash
curl -s -X POST http://localhost:8000/api/approvals/1/approve
```
