# Decisiones Arquitectónicas Sprint 1

## A. Modelo canónico

Contrato oficial e inmutable del Sprint 1:

- `usuarios_config`
- `proyectos`
- `mensajes_historial`
- `archivos_temporales`
- `tool_calls_pendientes`

## B. UUID en proyectos

`proyectos.id` es `UUID` y se genera desde Python con `uuid.uuid4()`.
Todas las llaves foráneas hacia proyecto usan `UUID`:

- `mensajes_historial.proyecto_id`
- `archivos_temporales.proyecto_id`
- `tool_calls_pendientes.proyecto_id`

## C. Human-in-the-Loop

`tool_calls_pendientes` es la tabla oficial para pausar herramientas de escritura.

Estados oficiales:

- `pending`
- `approved`
- `rejected`
- `executed`
- `failed`

## D. Archivos temporales híbridos

Enfoque enterprise:

- Snippets, HTML pequeño, código y texto: `contenido_codigo` en PostgreSQL.
- Excel, ZIP, PDF, imágenes, HTML pesado y binarios: filesystem bajo `BASE_PROJECTS_DIR`.

Columnas agregadas de forma idempotente al startup:

- `ruta_archivo text nullable`
- `mime_type varchar(120) nullable`
- `size_bytes integer nullable`

## E. USE_MOCK_APIS

`USE_MOCK_APIS=True` por defecto.

El backend puede validar REST, WebSocket, streaming, tool calling y Human-in-the-Loop sin consumir APIs reales.

## F. Contrato endpoints

REST:

- `GET /health`
- `GET /api/config`
- `GET /api/config/{id}`
- `PATCH /api/config/{id}`
- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/{id}`
- `PATCH /api/projects/{id}`
- `POST /api/files/{proyecto_id}/upload`
- `GET /api/approvals`
- `GET /api/approvals/{id}`
- `POST /api/approvals/{id}/approve`
- `POST /api/approvals/{id}/reject`

WebSocket:

- `/ws/chat/{proyecto_id}?usuario_config_id=1`

## G. Router lógico

Prefijos oficiales:

- `Gemini:`
- `ChatGPT:`
- `Claude:`
- `Alineación:` / `Alineacion:`

Orden de alineación:

1. Gemini
2. ChatGPT
3. Claude

## H. Seguridad de ejecución

Lectura sin aprobación:

- `leer_archivo`
- `analizar_estructura_tabular`
- `analizar_estructura_web`

Escritura con aprobación si `auto_aprobar_ejecucion=false`:

- `crear_estructura_directorios`
- `modificar_archivo`
