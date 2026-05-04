"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { formatDate } from "@/lib/format";
import { projectsRepository } from "@/services/repositories";
import type { Proyecto } from "@/types/domain";

export function ProjectsView() {
  const [projects, setProjects] = useState<Proyecto[]>([]);
  useEffect(() => { projectsRepository.list().then(setProjects); }, []);

  return (
    <div>
      <SectionHeader
        title="Proyectos"
        sprint="Sprint 1 · Gestión de proyectos"
        description="Listado de iniciativas gobernadas por el orquestador. Si el backend aún no tiene datos, esta pantalla puede mostrar vacío o mocks según NEXT_PUBLIC_DATA_MODE."
        action={<Link href="/projects/new"><Button>Nuevo proyecto</Button></Link>}
      />
      {projects.length === 0 ? (
        <EmptyState title="Aún no existen proyectos" description="Crea el primer proyecto para habilitar chat, aprobaciones, archivos y workspace." />
      ) : (
        <div className="grid gap-5 xl:grid-cols-2">
          {projects.map((project) => (
            <Card key={project.id} className="transition hover:-translate-y-0.5 hover:shadow-cyan">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <Badge tone="info">{project.nombre_slug}</Badge>
                  <h2 className="mt-4 text-2xl font-black text-brand-navy">{project.titulo}</h2>
                  <p className="mt-2 text-sm leading-6 text-brand-muted">{project.descripcion}</p>
                </div>
                <Badge tone={project.estado === "activo" ? "success" : "neutral"}>{project.estado}</Badge>
              </div>
              <div className="mt-6 flex flex-wrap gap-2">
                {Object.entries(project.tecnologias || {}).map(([key, value]) => <Badge key={key}>{key}: {String(value)}</Badge>)}
              </div>
              <div className="mt-6 flex items-center justify-between border-t border-brand-border pt-5">
                <span className="text-xs font-bold text-brand-muted">Creado: {formatDate(project.fecha_creacion)}</span>
                <div className="flex gap-2">
                  <Link href={`/projects/${project.id}`}><Button variant="secondary">Detalle</Button></Link>
                  <Link href={`/chat/${project.id}`}><Button>Chat</Button></Link>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
