# Frontend Orquestador Multi-Agente

Frontend enterprise para la plataforma **Orquestador Multi-Agente** de Victor Figueroa — Arquitecto de Soluciones.

## Branding oficial

El frontend usa el logo real `public/LogoVF.png` y una paleta derivada de la identidad VF:

- Brand Navy `#17104A`
- Brand Deep Navy `#100A36`
- Brand Cyan `#00BFF3`
- Brand Bright Cyan `#10D7FF`
- Soft Background `#F5F7FB`
- Soft Lilac `#ECEAF7`
- Border Soft `#D7D9E3`

## Stack

- Next.js App Router
- React
- TypeScript
- Tailwind CSS
- API services desacoplados
- WebSocket client
- Mocks por Sprint 2-4
- Modo `hybrid` para Sprint 1 real con fallback mock

## Variables de entorno

Copia `.env.example` como `.env.local` o usa las variables del contenedor Docker:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000
NEXT_PUBLIC_DATA_MODE=hybrid
NEXT_PUBLIC_ENABLED_SPRINTS=1,2,3,4
NEXT_PUBLIC_DEFAULT_USER_CONFIG_ID=1
```

## Ejecución local

```bash
npm install
npm run dev
```

Con Docker Compose del proyecto principal, basta con reemplazar el contenido de la carpeta `frontend/` y ejecutar:

```bash
docker compose up -d --build frontend
```

## Módulos implementados

### Sprint 1 — Backend real

- Dashboard
- Configuración
- Proyectos
- Crear proyecto
- Detalle proyecto
- Chat WebSocket
- Aprobaciones Human-in-the-Loop
- Upload de archivos

Endpoints usados:

- `GET /health`
- `GET /api/config`
- `GET /api/config/{usuario_config_id}`
- `PATCH /api/config/{usuario_config_id}`
- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/{proyecto_id}`
- `POST /api/files/{proyecto_id}/upload`
- `GET /api/approvals`
- `POST /api/approvals/{approval_id}/approve`
- `POST /api/approvals/{approval_id}/reject`
- `WS /ws/chat/{proyecto_id}?usuario_config_id=1`

### Sprint 2 — Diseñado con mocks

- Historial de mensajes
- Gestión de contexto
- Gestión avanzada de archivos
- Catálogo de tools
- Dry-run preparado

### Sprint 3 — Diseñado con mocks

- Gestión de agentes
- Roles
- Métricas
- Costos
- Workspace / file explorer

### Sprint 4 — Diseñado con mocks

- Integración GitHub
- Commits / push conceptual
- Auditoría enterprise
- Trazabilidad de acciones IA

## Modo de datos

`NEXT_PUBLIC_DATA_MODE` controla la estrategia:

- `real`: usa solo backend real.
- `mock`: usa solo mocks.
- `hybrid`: intenta backend real y cae a mocks si el endpoint aún no existe.

Recomendado para este sprint:

```env
NEXT_PUBLIC_DATA_MODE=hybrid
```

## Estructura

```text
app/          rutas Next.js App Router
components/   shell, branding, UI primitives
features/     vistas por dominio
lib/          env, format, flags, helpers
services/     API client, repositorios, WebSocket
mocks/        datos mock para Sprint 2-4
types/        tipos de dominio y WebSocket
public/       LogoVF.png
```

## Criterio de integración

1. Backend debe responder `GET /health`.
2. `GET /api/config` debe devolver al menos `usuarios_config.id=1`.
3. `GET /api/projects` puede devolver `[]` si no hay proyectos.
4. Crear un proyecto desde `/projects/new`.
5. Abrir `/chat/{uuid}` y validar WebSocket o fallback mock.
6. Validar `/approvals` con lista real o mock.
