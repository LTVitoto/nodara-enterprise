"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AgentBadge } from "@/components/ui/AgentBadge";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { formatDate, formatCurrency } from "@/lib/format";
import { projectsRepository, futureRepository } from "@/services/repositories";
import type { Proyecto } from "@/types/domain";

export function ProjectDetailView({ projectId }: { projectId: string }) {
  const router = useRouter();
  const [project, setProject] = useState<Proyecto | null>(null);
  const [costoTotal, setCostoTotal] = useState<number>(0);

  async function loadData() {
      const p = await projectsRepository.get(projectId);
      setProject(p);
      const msgs = await futureRepository.messages(projectId);
      setCostoTotal(msgs.reduce((acc, m) => acc + (m.costo_estimado || 0), 0));
  }

  useEffect(() => { loadData(); }, [projectId]);

  async function toggleStatus() {
      if(!project) return;
      const newStatus = project.estado === 'activo' ? 'inactivo' : 'activo';
      await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/projects/${projectId}`, {
          method: 'PATCH', headers:{'Content-Type':'application/json'}, body: JSON.stringify({estado: newStatus})
      });
      loadData();
  }

  async function deleteProject() {
      if(!confirm("¿Estás seguro de eliminar este proyecto y todos sus archivos?")) return;
      await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/projects/${projectId}`, { method: 'DELETE' });
      router.push("/projects");
  }

  if (!project) return <SectionHeader title="Cargando proyecto..." description="Consultando backend..." />;

  return (
    <div>
      <SectionHeader
        title={project.titulo}
        description={project.descripcion || "Sin descripción"}
        action={
            <div className="flex gap-2">
                <Button variant="danger" onClick={deleteProject}>Eliminar</Button>
                <Button variant="secondary" onClick={toggleStatus}>{project.estado === 'activo' ? 'Desactivar' : 'Activar'}</Button>
                <Link href={`/chat/${project.id}`}><Button>Abrir Chat</Button></Link>
            </div>
        }
      />
      <div className="grid gap-6 xl:grid-cols-[1.1fr_.9fr]">
        <Card>
          <CardTitle eyebrow={project.nombre_slug} title="Contrato del proyecto" />
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl bg-brand-soft p-4"><p className="text-xs font-black text-brand-muted">Responsable</p><p className="font-black text-brand-navy">{(project as any).responsable || "Vitoto"}</p></div>
            <div className="rounded-2xl bg-brand-soft p-4"><p className="text-xs font-black text-brand-muted">Costo Incurrido</p><Badge tone="warning" className="mt-1 text-sm">{formatCurrency(costoTotal)}</Badge></div>
            <div className="rounded-2xl bg-brand-soft p-4"><p className="text-xs font-black text-brand-muted">Estado</p><Badge tone={project.estado === 'activo' ? "success" : "danger"} className="mt-1">{project.estado}</Badge></div>
            <div className="rounded-2xl bg-brand-soft p-4"><p className="text-xs font-black text-brand-muted">GitHub</p><p className="font-bold text-sm truncate">{project.github_url || "No vinculado"}</p></div>
          </div>
          <pre className="mt-5 overflow-auto rounded-3xl bg-brand-deep p-5 text-xs leading-6 text-brand-bright">{JSON.stringify({ tecnologias: project.tecnologias, microservicios: project.microservicios }, null, 2)}</pre>
        </Card>
        <Card>
          <CardTitle eyebrow="Roles" title="Sala multi-agente" />
          <div className="space-y-4">
            <div className="rounded-3xl border border-brand-border p-4"><AgentBadge agent="gemini" /><p className="mt-3 text-sm text-brand-muted">{project.rol_gemini}</p></div>
            <div className="rounded-3xl border border-brand-border p-4"><AgentBadge agent="chatgpt" /><p className="mt-3 text-sm text-brand-muted">{project.rol_chatgpt}</p></div>
            <div className="rounded-3xl border border-brand-border p-4"><AgentBadge agent="claude" /><p className="mt-3 text-sm text-brand-muted">{project.rol_claude}</p></div>
          </div>
        </Card>
      </div>
    </div>
  );
}
