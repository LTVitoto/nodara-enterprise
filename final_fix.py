import os

print("🔥 INICIANDO CORRECCIÓN DEFINITIVA (FRONTEND + BACKEND)...")

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"✅ Archivo corregido: {path}")

# ==========================================
# 1. FIX BACKEND: UNIFICACIÓN DE BASE METADATA
# ==========================================
# Cambiamos "from app.db.base import Base" a "from app.database import Base"
write_file("backend/app/models/governance.py", r"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

# 🔥 FIX CRÍTICO: Usar la misma Base que el resto del sistema
from app.database import Base

class ToolCallStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTED = "executed"
    REJECTED = "rejected"
    FAILED = "failed"

class UsuarioConfig(Base):
    __tablename__ = "usuario_config"
    id = Column(Integer, primary_key=True, autoincrement=True)
    auto_aprobar_ejecucion = Column(Boolean, default=False)

class ToolCallPendiente(Base):
    __tablename__ = "tool_call_pendiente"
    id = Column(Integer, primary_key=True, autoincrement=True)
    proyecto_id = Column(UUID(as_uuid=True), index=True)
    usuario_config_id = Column(Integer, ForeignKey("usuario_config.id"))
    agente = Column(String, nullable=False)
    tool_name = Column(String, nullable=False)
    arguments_json = Column(JSONB, default={})
    status = Column(String, default=ToolCallStatus.PENDING.value)
    result_json = Column(JSONB, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
""")

# ==========================================
# 2. FIX FRONTEND: SINTAXIS TYPESCRIPT
# ==========================================
# Cambiamos "async def" a "async function" y limpiamos imports
write_file("frontend/services/repositories.ts", r"""
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
  list: async (): Promise<UploadedFile[]> => [],
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
""")

print("\n🚀 SCRIPT FINALIZADO CON ÉXITO.")
print("👉 PASO OBLIGATORIO: Ejecuta 'docker compose down' y luego 'docker compose up -d --build'")