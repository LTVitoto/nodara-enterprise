import type {
  AgentDefinition,
  Approval,
  AuditEvent,
  ChatMessage,
  MetricCard,
  Proyecto,
  ToolDefinition,
  UploadedFile,
  UsuarioConfig,
  WorkspaceNode
} from "@/types/domain";

export const mockConfig: UsuarioConfig = {
  id: 1,
  derivar_en_problemas: true,
  auto_aprobar_ejecucion: true,
  saldo_virtual_openai: 0,
  saldo_virtual_anthropic: 0,
  saldo_virtual_gemini: 0,
  has_api_key_openai: false,
  has_api_key_anthropic: false,
  has_api_key_gemini: false
};

export const mockProjects: Proyecto[] = [
  {
    id: "5a7c9d4b-9b98-4b7a-b787-5a8e7a13f101",
    nombre_slug: "orquestador-demo",
    titulo: "Orquestador Multi-Agente Demo",
    anio: 2026,
    descripcion: "Proyecto de referencia para validar Gemini, ChatGPT y Claude en un flujo enterprise de generación y control.",
    tecnologias: { backend: "FastAPI", frontend: "Next.js", database: "PostgreSQL", websocket: true },
    microservicios: { db: "orquestador_db", backend: "orquestador_backend", frontend: "orquestador_frontend" },
    instrucciones_deploy: "docker compose up -d --build",
    github_url: null,
    rol_gemini: "Arquitecto Cloud e Infraestructura",
    rol_chatgpt: "Arquitecto Backend y Datos",
    rol_claude: "Arquitecto Frontend y UX",
    estado: "activo",
    fecha_creacion: new Date().toISOString()
  }
];

export const mockApprovals: Approval[] = [
  {
    id: 101,
    proyecto_id: mockProjects[0].id,
    usuario_config_id: 1,
    agente: "chatgpt",
    tool_name: "modificar_archivo",
    arguments_json: { path: "backend/app/models.py", action: "patch_uuid_fk" },
    status: "pending",
    created_at: new Date().toISOString()
  }
];

export const mockMessages: ChatMessage[] = [
  {
    id: "m-001",
    proyecto_id: mockProjects[0].id,
    remitente: "Vitoto",
    destinatario: "ChatGPT",
    contenido: "ChatGPT: valida los endpoints Sprint 1 y prepara el contrato para frontend.",
    tokens_consumidos: 248,
    costo_estimado: 0.0042,
    incluir_en_contexto: true,
    fecha_envio: new Date().toISOString()
  },
  {
    id: "m-002",
    proyecto_id: mockProjects[0].id,
    remitente: "ChatGPT",
    destinatario: "Vitoto",
    contenido: "Backend operativo: health OK, config OK, projects vacío esperado, approvals vacío esperado.",
    tokens_consumidos: 612,
    costo_estimado: 0.0118,
    incluir_en_contexto: true,
    fecha_envio: new Date().toISOString()
  }
];

export const mockFiles: UploadedFile[] = [
  {
    id: 1,
    proyecto_id: mockProjects[0].id,
    nombre_archivo: "contrato-endpoints-sprint1.md",
    contenido_codigo: "# Contrato oficial Sprint 1",
    ruta_archivo: null,
    mime_type: "text/markdown",
    size_bytes: 1842,
    version: 1,
    fecha_creacion: new Date().toISOString()
  }
];

export const mockTools: ToolDefinition[] = [
  { name: "leer_archivo", description: "Lee archivos del workspace sin modificar estado.", requires_approval: false, sprint: 2, category: "Lectura" },
  { name: "analizar_estructura_tabular", description: "Analiza Excel/CSV con pandas y devuelve metadata compacta.", requires_approval: false, sprint: 2, category: "Análisis" },
  { name: "crear_estructura_directorios", description: "Crea carpetas y estructura base de proyecto.", requires_approval: true, sprint: 1, category: "Escritura" },
  { name: "modificar_archivo", description: "Crea o modifica archivos dentro del workspace controlado.", requires_approval: true, sprint: 1, category: "Escritura" }
];

export const mockAgents: AgentDefinition[] = [
  { name: "gemini", label: "Gemini", role: "Infraestructura y DevOps", responsibility: "Docker, red, variables, despliegue, observabilidad", status: "active", sprint: 1 },
  { name: "chatgpt", label: "ChatGPT", role: "Backend y Datos", responsibility: "FastAPI, PostgreSQL, WebSocket, modelo de dominio", status: "active", sprint: 1 },
  { name: "claude", label: "Claude", role: "Frontend y UI/UX", responsibility: "Next.js, diseño enterprise, experiencia multi-agente", status: "mock", sprint: 1 }
];

export const mockMetrics: MetricCard[] = [
  { label: "Solicitudes WebSocket", value: "38", trend: "+12% día", tone: "info" },
  { label: "Tool calls pendientes", value: "1", trend: "requiere aprobación", tone: "warning" },
  { label: "Costo estimado", value: "US$ 0.0160", trend: "modo mock activo", tone: "success" },
  { label: "Sprints modelados", value: "4", trend: "roadmap completo", tone: "info" }
];

export const mockWorkspace: WorkspaceNode[] = [
  {
    id: "folder-backend",
    name: "backend",
    type: "folder",
    path: "/backend",
    children: [
      { id: "app-main", name: "main.py", type: "file", path: "/backend/app/main.py" },
      { id: "app-models", name: "models.py", type: "file", path: "/backend/app/models.py" }
    ]
  },
  {
    id: "folder-frontend",
    name: "frontend",
    type: "folder",
    path: "/frontend",
    children: [
      { id: "app-page", name: "page.tsx", type: "file", path: "/frontend/app/page.tsx" },
      { id: "components", name: "components", type: "folder", path: "/frontend/components" }
    ]
  }
];

export const mockAuditEvents: AuditEvent[] = [
  { id: "a-001", timestamp: new Date().toISOString(), actor: "Vitoto", action: "Validó healthcheck", target: "GET /health", severity: "success" },
  { id: "a-002", timestamp: new Date().toISOString(), actor: "ChatGPT", action: "Corrigió modelo UUID", target: "tool_calls_pendientes.proyecto_id", severity: "info" },
  { id: "a-003", timestamp: new Date().toISOString(), actor: "Gemini", action: "Confirmó contrato canónico", target: "5 tablas Sprint 1", severity: "success" }
];
