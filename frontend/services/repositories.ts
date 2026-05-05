import type { AgentDefinition, Approval, AuditEvent, ChatMessage, MetricCard, Proyecto, ProyectoCreate, ToolDefinition, UploadedFile, UsuarioConfig, WorkspaceNode } from "@/types/domain";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function normalizeArray<T>(data: any): T[] {
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.items)) return data.items;
  if (data && Array.isArray(data.data)) return data.data;
  return [];
}

// 🔥 FIX CRÍTICO: 'function' en lugar de 'def'
async function fetchFromAPI(endpoint: string, options?: RequestInit) {
  try {
    const res = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...options?.headers }
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (error) {
    console.error(`API Error en ${endpoint}:`, error);
    return null; 
  }
}

export const configRepository = {
  list: async (): Promise<UsuarioConfig[]> => normalizeArray(await fetchFromAPI('/api/config')),
  patch: async (id: number, payload: any) => await fetchFromAPI(`/api/config/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })
};

export const projectsRepository = {
  list: async (): Promise<Proyecto[]> => normalizeArray(await fetchFromAPI('/api/projects')),
  get: async (id: string): Promise<Proyecto | null> => await fetchFromAPI(`/api/projects/${id}`),
  create: async (payload: ProyectoCreate): Promise<Proyecto> => await fetchFromAPI('/api/projects', { method: 'POST', body: JSON.stringify(payload) })
};

export const approvalsRepository = {
  listAll: async (): Promise<Approval[]> => normalizeArray(await fetchFromAPI('/api/approvals')),
  approve: async (id: number): Promise<Approval> => await fetchFromAPI(`/api/approvals/${id}/approve`, { method: 'POST' }),
  reject: async (id: number): Promise<Approval> => await fetchFromAPI(`/api/approvals/${id}/reject`, { method: 'POST' })
};

export const filesRepository = {
  list: async (projectId: string): Promise<UploadedFile[]> => normalizeArray(await fetchFromAPI(`/api/files/${projectId}`)),
  upload: async (projectId: string, file: File): Promise<UploadedFile> => ({ 
    id: Date.now(), 
    proyecto_id: projectId, 
    nombre_archivo: file.name, 
    version: 1, 
    mime_type: file.type, 
    size_bytes: file.size, 
    ruta_archivo: "db" 
  })
};

export const futureRepository = {
  metrics: async (): Promise<MetricCard[]> => normalizeArray(await fetchFromAPI('/api/metrics')),
  messages: async (projectId: string): Promise<ChatMessage[]> => normalizeArray(await fetchFromAPI(`/api/projects/${projectId}/messages`)),
  tools: async (): Promise<ToolDefinition[]> => normalizeArray(await fetchFromAPI('/api/tools')),
  agents: async (): Promise<AgentDefinition[]> => normalizeArray(await fetchFromAPI('/api/agents')),
  workspace: async (projectId: string): Promise<WorkspaceNode[]> => normalizeArray(await fetchFromAPI(`/api/projects/${projectId}/workspace/tree`)),
  audit: async (): Promise<AuditEvent[]> => normalizeArray(await fetchFromAPI('/api/audit/events'))
};

export const githubRepository = {
  status: async (projectId: string) => await fetchFromAPI(`/api/github/${projectId}/status`, { method: 'POST' }),
  add: async (projectId: string) => await fetchFromAPI(`/api/github/${projectId}/add`, { method: 'POST' }),
  commit: async (projectId: string) => await fetchFromAPI(`/api/github/${projectId}/commit`, { method: 'POST' }),
  push: async (projectId: string) => await fetchFromAPI(`/api/github/${projectId}/push`, { method: 'POST' }),
};
