export type Sprint = 1 | 2 | 3 | 4;
export type AgentName = "gemini" | "chatgpt" | "claude" | "orchestrator";
export type ApprovalStatus = "pending" | "approved" | "rejected" | "executed" | "failed";
export type DataMode = "real" | "mock" | "hybrid";

export interface UsuarioConfig {
  id: number;
  derivar_en_problemas: boolean;
  auto_aprobar_ejecucion: boolean;
  saldo_virtual_openai: number;
  saldo_virtual_anthropic: number;
  saldo_virtual_gemini: number;
  has_api_key_openai: boolean;
  has_api_key_anthropic: boolean;
  has_api_key_gemini: boolean;
}

export interface UsuarioConfigUpdate {
  derivar_en_problemas?: boolean;
  auto_aprobar_ejecucion?: boolean;
  api_key_openai?: string | null;
  api_key_anthropic?: string | null;
  api_key_gemini?: string | null;
}

export interface Proyecto {
  id: string;
  nombre_slug: string;
  titulo: string;
  anio: number;
  descripcion?: string | null;
  tecnologias: Record<string, unknown>;
  microservicios: Record<string, unknown>;
  instrucciones_deploy?: string | null;
  github_url?: string | null;
  rol_gemini?: string | null;
  rol_chatgpt?: string | null;
  rol_claude?: string | null;
  estado: string;
  responsable?: string | null;
  fecha_creacion?: string;
}

export type ProyectoCreate = Omit<Proyecto, "id" | "fecha_creacion">;

export interface Approval {
  id: number;
  proyecto_id: string;
  usuario_config_id: number;
  agente: string;
  tool_name: string;
  arguments_json: Record<string, unknown>;
  status: ApprovalStatus;
  result_json?: Record<string, unknown> | null;
  error_message?: string | null;
  created_at?: string;
  resolved_at?: string | null;
}

export interface UploadedFile {
  id: number;
  proyecto_id: string;
  nombre_archivo: string;
  contenido_codigo?: string | null;
  ruta_archivo?: string | null;
  mime_type?: string | null;
  size_bytes?: number | null;
  version: number;
  fecha_creacion?: string;
}

export interface ChatMessage {
  id: string;
  proyecto_id: string;
  remitente: string;
  destinatario: string;
  contenido: string;
  tokens_consumidos: number;
  costo_estimado: number;
  incluir_en_contexto: boolean;
  fecha_envio: string;
}

export interface ToolDefinition {
  name: string;
  description: string;
  requires_approval: boolean;
  sprint: Sprint;
  category: string;
}

export interface AgentDefinition {
  name: AgentName;
  label: string;
  role: string;
  responsibility: string;
  status: "active" | "mock" | "disabled";
  sprint: Sprint;
}

export interface MetricCard {
  label: string;
  value: string;
  trend?: string;
  tone?: "info" | "success" | "warning" | "danger";
}

export interface WorkspaceNode {
  id: string;
  name: string;
  type: "file" | "folder";
  path: string;
  children?: WorkspaceNode[];
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  target: string;
  severity: "info" | "success" | "warning" | "danger";
}
