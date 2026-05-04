from __future__ import annotations

import asyncio
import json
import os
from uuid import UUID

import httpx
import websockets

API = os.getenv("API", "http://localhost:8000")
WS = os.getenv("WS", "ws://localhost:8000")


async def main() -> None:
    async with httpx.AsyncClient(timeout=20) as client:
        health = await client.get(f"{API}/health")
        print("health", health.status_code, health.text)

        project_payload = {
            "titulo": "Smoke Test Orquestador",
            "anio": 2026,
            "descripcion": "Smoke test automático",
            "tecnologias": {"backend": "FastAPI"},
            "microservicios": {"backend": True},
        }
        project = await client.post(f"{API}/api/projects", json=project_payload)
        print("project", project.status_code, project.text)
        project.raise_for_status()
        project_id = UUID(project.json()["id"])

    async with websockets.connect(f"{WS}/ws/chat/{project_id}?usuario_config_id=1") as ws:
        await ws.send(json.dumps({"message": "ChatGPT: responde OK smoke test", "correlation_id": "smoke-001"}))
        while True:
            msg = await ws.recv()
            print("ws", msg)
            if '"orchestration_end"' in msg:
                break


if __name__ == "__main__":
    asyncio.run(main())
