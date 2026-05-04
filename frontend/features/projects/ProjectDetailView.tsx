"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AgentBadge } from "@/components/ui/AgentBadge";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { formatDate } from "@/lib/format";
import { projectsRepository } from "@/services/repositories";
import type { Proyecto } from "@/types/domain";

export function ProjectDetailView({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<Proyecto | null>(null);
  useEffect(() => { projectsRepository.get(projectId).then(setProject); }, [projectId]);
  if (!project) return <SectionHeader title="Cargando proyecto..." description="Consultando backend o mock según configuración." />;

  return (
    <div>
      <SectionHeader
        title={project.titulo}
        sprint="Sprint 1 · Detalle de proyecto"
        description={project.descripcion || "Sin descripción"}
        action={<Link href={`/chat/${project.id}`}><Button>Abrir Chat</Button></Link>}
      />
      <div className="grid gap-6 xl:grid-cols-[1.1fr_.9fr]">
        <Card>
          <CardTitle eyebrow={project.nombre_slug} title="Contrato del proyecto" />
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl bg-brand-soft p-4"><p className="text-xs font-black text-brand-muted">UUID</p><code className="text-sm font-bold">{project.id}</code></div>
            <div className="rounded-2xl bg-brand-soft p-4"><p className="text-xs font-black text-brand-muted">Estado</p><Badge tone="success">{project.estado}</Badge></div>
            <div className="rounded-2xl bg-brand-soft p-4"><p className="text-xs font-black text-brand-muted">Año</p><p className="font-black">{project.anio}</p></div>
            <div className="rounded-2xl bg-brand-soft p-4"><p className="text-xs font-black text-brand-muted">Fecha creación</p><p className="font-bold">{formatDate(project.fecha_creacion)}</p></div>
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
