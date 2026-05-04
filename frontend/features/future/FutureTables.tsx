"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Card, CardTitle } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { formatDate } from "@/lib/format";
import { mockProjects } from "@/mocks/data";
import { futureRepository } from "@/services/repositories";

import type {
  AgentDefinition,
  AuditEvent,
  ChatMessage,
  MetricCard,
  ToolDefinition,
  WorkspaceNode
} from "@/types/domain";

/* =========================
   Helpers
========================= */

function ensureArray<T>(data: any): T[] {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.data)) return data.data;
  return [];
}

/* =========================
   Messages
========================= */

export function MessagesView() {
  const [items, setItems] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await futureRepository.messages(mockProjects[0].id);
        setItems(ensureArray<ChatMessage>(data));
      } catch (err) {
        console.error("Messages error:", err);
        setItems([]);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <SimplePage
      title="Historial de mensajes"
      sprint="Sprint 2 · Contexto"
      description="Preparado para GET /api/projects/{proyecto_id}/messages."
    >
      {loading ? (
        <Loader />
      ) : (
        items.map((m) => (
          <Card key={m.id}>
            <Badge tone={m.incluir_en_contexto ? "success" : "neutral"}>
              {m.incluir_en_contexto ? "en contexto" : "excluido"}
            </Badge>

            <h3 className="mt-3 font-black">
              {m.remitente} → {m.destinatario}
            </h3>

            <p className="mt-2 text-sm text-brand-muted">{m.contenido}</p>

            <p className="mt-2 text-xs text-brand-muted">
              {formatDate(m.fecha_envio)} · {m.tokens_consumidos} tokens
            </p>
          </Card>
        ))
      )}
    </SimplePage>
  );
}

/* =========================
   Tools
========================= */

export function ToolsView() {
  const [items, setItems] = useState<ToolDefinition[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await futureRepository.tools();
        setItems(ensureArray<ToolDefinition>(data));
      } catch (err) {
        console.error("Tools error:", err);
        setItems([]);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <SimplePage
      title="Catálogo de tools"
      sprint="Sprint 2 · Tools"
      description="Lectura libre vs escritura con aprobación."
    >
      {loading ? (
        <Loader />
      ) : (
        <div className="grid gap-5 md:grid-cols-2">
          {items.map((t) => (
            <Card key={t.name}>
              <Badge tone={t.requires_approval ? "warning" : "success"}>
                {t.requires_approval ? "requiere aprobación" : "lectura libre"}
              </Badge>

              <h3 className="mt-3 text-lg font-black">{t.name}</h3>
              <p className="mt-2 text-sm text-brand-muted">{t.description}</p>

              <Badge className="mt-4">Sprint {t.sprint}</Badge>
            </Card>
          ))}
        </div>
      )}
    </SimplePage>
  );
}

/* =========================
   Agents
========================= */

export function AgentsView() {
  const [items, setItems] = useState<AgentDefinition[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await futureRepository.agents();
        setItems(ensureArray<AgentDefinition>(data));
      } catch (err) {
        console.error("Agents error:", err);
        setItems([]);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <SimplePage
      title="Gestión de agentes"
      sprint="Sprint 3 · Agentes"
      description="Roles y responsabilidades IA"
    >
      {loading ? (
        <Loader />
      ) : (
        <div className="grid gap-5 xl:grid-cols-3">
          {items.map((a) => (
            <Card key={a.name}>
              <Badge tone={a.status === "active" ? "success" : "info"}>
                {a.status}
              </Badge>

              <h3 className="mt-3 text-xl font-black">{a.label}</h3>
              <p className="mt-2 font-bold text-brand-navy">{a.role}</p>
              <p className="mt-2 text-sm text-brand-muted">
                {a.responsibility}
              </p>
            </Card>
          ))}
        </div>
      )}
    </SimplePage>
  );
}

/* =========================
   Metrics (FIX CRÍTICO)
========================= */

export function MetricsView() {
  const [items, setItems] = useState<MetricCard[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await futureRepository.metrics();

        const safe: MetricCard[] = Array.isArray(data)
          ? data
          : [
              {
                label: "Proyectos",
                value: String(data?.total_projects ?? 0),
                trend: "fallback",
                tone: "info"
              }
            ];

        setItems(safe);
      } catch (err) {
        console.error("Metrics error:", err);
        setItems([]);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  return (
    <SimplePage
      title="Métricas, costos y uso"
      sprint="Sprint 3 · Observabilidad"
      description="Uso por proyecto, agente y tokens."
    >
      {loading ? (
        <Loader />
      ) : (
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {(items || []).map((m, i) => (
            <Card key={m?.label || i}>
              <p className="text-sm font-bold text-brand-muted">{m?.label}</p>
              <p className="mt-3 text-3xl font-black">{m?.value}</p>
              <Badge tone={m?.tone || "info"} className="mt-4">
                {m?.trend}
              </Badge>
            </Card>
          ))}
        </div>
      )}
    </SimplePage>
  );
}

/* =========================
   Workspace
========================= */

export function WorkspaceView() {
  const [items, setItems] = useState<WorkspaceNode[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await futureRepository.workspace(mockProjects[0].id);
        setItems(ensureArray<WorkspaceNode>(data));
      } catch (err) {
        console.error("Workspace error:", err);
        setItems([]);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <SimplePage
      title="Workspace / File Explorer"
      sprint="Sprint 3 · Filesystem"
      description="Explorador de archivos"
    >
      <Card>
        <CardTitle eyebrow="Árbol" title="Estructura del proyecto" />
        {loading ? <Loader /> : <Tree nodes={items} />}
      </Card>
    </SimplePage>
  );
}

/* =========================
   Github
========================= */

export function GithubView() {
  return (
    <SimplePage
      title="Integración GitHub"
      sprint="Sprint 4 · GitOps"
      description="Pendiente backend"
    >
      <Card>
        <CardTitle eyebrow="Estado" title="No conectado" />
        <p className="text-sm text-brand-muted">
          Esperando implementación backend /api/integrations/github/*
        </p>
      </Card>
    </SimplePage>
  );
}

/* =========================
   Audit
========================= */

export function AuditView() {
  const [items, setItems] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await futureRepository.audit();
        setItems(ensureArray<AuditEvent>(data));
      } catch (err) {
        console.error("Audit error:", err);
        setItems([]);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <SimplePage
      title="Auditoría enterprise"
      sprint="Sprint 4 · Governance"
      description="Trazabilidad completa"
    >
      {loading ? (
        <Loader />
      ) : (
        <div className="space-y-4">
          {items.map((a) => (
            <Card key={a.id}>
              <Badge tone={a.severity}>{a.severity}</Badge>
              <h3 className="mt-3 font-black">{a.action}</h3>
              <p className="mt-1 text-sm text-brand-muted">
                {a.actor} · {a.target} · {formatDate(a.timestamp)}
              </p>
            </Card>
          ))}
        </div>
      )}
    </SimplePage>
  );
}

/* =========================
   UI helpers
========================= */

function SimplePage({
  title,
  sprint,
  description,
  children
}: {
  title: string;
  sprint: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <SectionHeader title={title} sprint={sprint} description={description} />
      {children}
    </div>
  );
}

function Loader() {
  return (
    <div className="col-span-4 text-center text-sm text-gray-500">
      Cargando...
    </div>
  );
}

function Tree({ nodes, depth = 0 }: { nodes: WorkspaceNode[]; depth?: number }) {
  return (
    <div className="space-y-2">
      {(nodes || []).map((node) => (
        <div key={node.id} style={{ marginLeft: depth * 18 }}>
          <div className="rounded-2xl bg-brand-soft px-4 py-3 text-sm font-bold">
            {node.type === "folder" ? "▸" : "•"} {node.name}
            <span className="ml-2 text-xs text-brand-muted">
              {node.path}
            </span>
          </div>

          {node.children && node.children.length > 0 ? (
            <Tree nodes={node.children} depth={depth + 1} />
          ) : null}
        </div>
      ))}
    </div>
  );
}