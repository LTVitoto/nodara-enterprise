"use client";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { formatDate } from "@/lib/format";
import { futureRepository, projectsRepository, githubRepository } from "@/services/repositories";
import type { AgentDefinition, AuditEvent, ChatMessage, MetricCard, ToolDefinition, WorkspaceNode, Proyecto } from "@/types/domain";

function ensureArray<T>(data: any): T[] { return Array.isArray(data) ? data : (Array.isArray(data?.data) ? data.data : []); }

function ProjectSelector({ projects, projectId, setProjectId }: { projects: Proyecto[], projectId: string, setProjectId: (id: string) => void }) {
    if (projects.length === 0) return null;
    return (
        <div className="mb-6">
            <label className="mr-4 font-bold text-sm">Seleccionar Proyecto:</label>
            <select className="border border-brand-border bg-white text-brand-navy p-2 rounded-xl text-sm" value={projectId} onChange={(e) => setProjectId(e.target.value)}>
                {projects.map(p => <option key={p.id} value={p.id}>{p.titulo}</option>)}
            </select>
        </div>
    );
}

export function MessagesView() {
  const [items, setItems] = useState<ChatMessage[]>([]);
  const [projects, setProjects] = useState<Proyecto[]>([]);
  const [projectId, setProjectId] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => { projectsRepository.list().then(p => { setProjects(p); if(p.length > 0) setProjectId(p[0].id); }); }, []);
  useEffect(() => {
    if (projectId) {
        setLoading(true);
        futureRepository.messages(projectId).then(data => setItems(ensureArray<ChatMessage>(data))).finally(() => setLoading(false));
    }
  }, [projectId]);

  return (
    <div>
      <SectionHeader title="Historial de mensajes" sprint="Sprint 2 · Contexto" description="Registro persistente del chat por proyecto." />
      <ProjectSelector projects={projects} projectId={projectId} setProjectId={setProjectId} />
      {loading ? <p>Cargando...</p> : items.length === 0 ? <p>No hay mensajes en este proyecto.</p> : (
        <div className="space-y-4">
            {items.map((m) => (
            <Card key={m.id}>
                <Badge tone={m.remitente.toLowerCase() === "user" || m.remitente.toLowerCase() === "usuario" ? "info" : "success"}>{m.remitente}</Badge>
                <p className="mt-3 text-sm text-brand-navy whitespace-pre-wrap">{m.contenido}</p>
                <p className="mt-2 text-xs text-brand-muted">{formatDate(m.fecha_envio)}</p>
            </Card>
            ))}
        </div>
      )}
    </div>
  );
}

export function ToolsView() {
  const [items, setItems] = useState<ToolDefinition[]>([]);
  useEffect(() => { futureRepository.tools().then(data => setItems(ensureArray<ToolDefinition>(data))); }, []);

  return (
    <div>
      <SectionHeader title="Catálogo de tools" sprint="Sprint 2 · Tools" description="Lectura libre vs escritura con aprobación." />
      <div className="grid gap-5 md:grid-cols-2">
        {items.map((t) => (
        <Card key={t.name}>
            <Badge tone={t.requires_approval ? "warning" : "success"}>{t.requires_approval ? "requiere aprobación" : "lectura libre"}</Badge>
            <h3 className="mt-3 text-lg font-black">{t.name}</h3>
            <p className="mt-2 text-sm text-brand-muted">{t.description}</p>
        </Card>
        ))}
      </div>
    </div>
  );
}

export function AgentsView() {
  const [items, setItems] = useState<AgentDefinition[]>([]);
  useEffect(() => { futureRepository.agents().then(data => setItems(ensureArray<AgentDefinition>(data))); }, []);

  return (
    <div>
      <SectionHeader title="Gestión de agentes" sprint="Sprint 3 · Agentes" description="Estado real de los agentes según API Keys cargadas." />
      <div className="grid gap-5 xl:grid-cols-3">
        {items.map((a) => (
        <Card key={a.name}>
            <Badge tone={a.status === "active" ? "success" : "danger"}>{a.status === "active" ? "API Key Activa" : "Sin API Key"}</Badge>
            <h3 className="mt-3 text-xl font-black">{a.label}</h3>
            <p className="mt-2 font-bold text-brand-navy">{a.role}</p>
            <p className="mt-2 text-sm text-brand-muted">{a.responsibility}</p>
        </Card>
        ))}
      </div>
    </div>
  );
}

export function MetricsView() {
  const [items, setItems] = useState<MetricCard[]>([]);
  useEffect(() => { futureRepository.metrics().then(data => setItems(ensureArray<MetricCard>(data))); }, []);

  return (
    <div>
      <SectionHeader title="Métricas, costos y uso" sprint="Sprint 3 · Observabilidad" description="Métricas leídas en tiempo real de PostgreSQL." />
      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        {items.map((m, i) => (
        <Card key={m?.label || i}>
            <p className="text-sm font-bold text-brand-muted">{m?.label}</p>
            <p className="mt-3 text-3xl font-black">{m?.value}</p>
            <Badge tone={m?.tone || "info"} className="mt-4">{m?.trend}</Badge>
        </Card>
        ))}
      </div>
    </div>
  );
}

function Tree({ nodes, depth = 0 }: { nodes: WorkspaceNode[]; depth?: number }) {
  return (
    <div className="space-y-2">
      {(nodes || []).map((node) => (
        <div key={node.id} style={{ marginLeft: depth * 18 }}>
          <div className="rounded-2xl bg-brand-soft px-4 py-3 text-sm font-bold">
            {node.type === "folder" ? "📁" : "📄"} {node.name}
          </div>
          {node.children && node.children.length > 0 ? <Tree nodes={node.children} depth={depth + 1} /> : null}
        </div>
      ))}
    </div>
  );
}

export function WorkspaceView() {
  const [items, setItems] = useState<WorkspaceNode[]>([]);
  const [projects, setProjects] = useState<Proyecto[]>([]);
  const [projectId, setProjectId] = useState<string>("");

  useEffect(() => { projectsRepository.list().then(p => { setProjects(p); if(p.length > 0) setProjectId(p[0].id); }); }, []);
  useEffect(() => { if (projectId) futureRepository.workspace(projectId).then(data => setItems(ensureArray<WorkspaceNode>(data))); }, [projectId]);

  return (
    <div>
      <SectionHeader title="Workspace / File Explorer" sprint="Sprint 3 · Filesystem" description="Lectura en tiempo real del directorio del proyecto en el servidor." />
      <ProjectSelector projects={projects} projectId={projectId} setProjectId={setProjectId} />
      <Card>
        <CardTitle eyebrow="Árbol" title="Estructura física del proyecto" />
        {items.length === 0 ? <p className="text-sm text-brand-muted">Carpeta de proyecto no encontrada o vacía.</p> : <Tree nodes={items} />}
      </Card>
    </div>
  );
}

export function GithubView() {
  const [projects, setProjects] = useState<Proyecto[]>([]);
  const [projectId, setProjectId] = useState<string>("");
  const [output, setOutput] = useState<string>("Selecciona un proyecto y ejecuta una acción de Git.");

  useEffect(() => { projectsRepository.list().then(p => { setProjects(p); if(p.length > 0) setProjectId(p[0].id); }); }, []);

  const runCmd = async (action: 'status' | 'add' | 'commit' | 'push') => {
      setOutput("Ejecutando...");
      try {
          const res = await githubRepository[action](projectId);
          setOutput(res?.output || "Comando ejecutado con éxito.");
      } catch (e) {
          setOutput("Error ejecutando el comando.");
      }
  };

  return (
    <div>
      <SectionHeader title="Integración GitHub" sprint="Sprint 4 · GitOps" description="Control de versiones directo sobre el directorio del proyecto." />
      <ProjectSelector projects={projects} projectId={projectId} setProjectId={setProjectId} />
      <Card>
        <CardTitle eyebrow="Acciones" title="Comandos Locales Git" />
        <div className="flex gap-2 mb-4">
            <Button variant="secondary" onClick={() => runCmd('status')}>Git Status</Button>
            <Button variant="secondary" onClick={() => runCmd('add')}>Git Add .</Button>
            <Button variant="secondary" onClick={() => runCmd('commit')}>Git Commit</Button>
            <Button onClick={() => runCmd('push')}>Git Push</Button>
        </div>
        <pre className="bg-brand-deep text-brand-bright p-4 rounded-xl text-sm whitespace-pre-wrap">{output}</pre>
      </Card>
    </div>
  );
}

export function AuditView() {
  const [items, setItems] = useState<AuditEvent[]>([]);
  useEffect(() => { futureRepository.audit().then(data => setItems(ensureArray<AuditEvent>(data))); }, []);

  return (
    <div>
      <SectionHeader title="Auditoría enterprise" sprint="Sprint 4 · Governance" description="Trazabilidad completa de operaciones críticas." />
      <div className="space-y-4">
        {items.map((a) => (
        <Card key={a.id}>
            <Badge tone={a.severity}>{a.severity}</Badge>
            <h3 className="mt-3 font-black">{a.action}</h3>
            <p className="mt-1 text-sm text-brand-muted">{a.actor} · {a.target} · {formatDate(a.timestamp)}</p>
        </Card>
        ))}
      </div>
    </div>
  );
}
