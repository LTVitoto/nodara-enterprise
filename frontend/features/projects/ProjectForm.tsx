"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { projectsRepository } from "@/services/repositories";
import type { ProyectoCreate } from "@/types/domain";

const defaultProject: ProyectoCreate = {
  nombre_slug: "orquestador-demo",
  titulo: "Orquestador Multi-Agente Demo",
  anio: 2026,
  descripcion: "Proyecto para validar la sala multi-agente enterprise con Gemini, ChatGPT y Claude.",
  tecnologias: { backend: "FastAPI", frontend: "Next.js", database: "PostgreSQL" },
  microservicios: { db: "orquestador_db", backend: "orquestador_backend", frontend: "orquestador_frontend" },
  instrucciones_deploy: "docker compose up -d --build",
  github_url: null,
  rol_gemini: "Arquitecto Cloud e Infraestructura",
  rol_chatgpt: "Arquitecto Backend y Datos",
  rol_claude: "Arquitecto Frontend y UX",
  estado: "activo"
};

export function ProjectForm() {
  const router = useRouter();
  const [payload, setPayload] = useState<ProyectoCreate>(defaultProject);
  const [saving, setSaving] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    const created = await projectsRepository.create(payload);
    setSaving(false);
    router.push(`/projects/${created.id}`);
  }

  function set<K extends keyof ProyectoCreate>(key: K, value: ProyectoCreate[K]) {
    setPayload((prev) => ({ ...prev, [key]: value }));
  }

  return (
    <div>
      <SectionHeader title="Crear proyecto" sprint="Sprint 1 · POST /api/projects" description="Formulario alineado al schema Gemini: UUID, nombre_slug, roles de agentes, tecnologías y microservicios." />
      <Card>
        <CardTitle eyebrow="Payload oficial" title="Datos base del proyecto" />
        <form onSubmit={submit} className="grid gap-5">
          <div className="grid gap-5 md:grid-cols-2">
            <label className="grid gap-2 text-sm font-bold">Slug<input className="rounded-2xl border border-brand-border p-3" value={payload.nombre_slug} onChange={(e) => set("nombre_slug", e.target.value)} /></label>
            <label className="grid gap-2 text-sm font-bold">Título<input className="rounded-2xl border border-brand-border p-3" value={payload.titulo} onChange={(e) => set("titulo", e.target.value)} /></label>
          </div>
          <label className="grid gap-2 text-sm font-bold">Descripción<textarea className="min-h-28 rounded-2xl border border-brand-border p-3" value={payload.descripcion || ""} onChange={(e) => set("descripcion", e.target.value)} /></label>
          <div className="grid gap-5 md:grid-cols-3">
            <label className="grid gap-2 text-sm font-bold">Año<input type="number" className="rounded-2xl border border-brand-border p-3" value={payload.anio} onChange={(e) => set("anio", Number(e.target.value))} /></label>
            <label className="grid gap-2 text-sm font-bold">Estado<input className="rounded-2xl border border-brand-border p-3" value={payload.estado} onChange={(e) => set("estado", e.target.value)} /></label>
            <label className="grid gap-2 text-sm font-bold">GitHub URL<input className="rounded-2xl border border-brand-border p-3" value={payload.github_url || ""} onChange={(e) => set("github_url", e.target.value || null)} /></label>
          </div>
          <div className="grid gap-5 md:grid-cols-3">
            <label className="grid gap-2 text-sm font-bold">Rol Gemini<textarea className="min-h-24 rounded-2xl border border-brand-border p-3" value={payload.rol_gemini || ""} onChange={(e) => set("rol_gemini", e.target.value)} /></label>
            <label className="grid gap-2 text-sm font-bold">Rol ChatGPT<textarea className="min-h-24 rounded-2xl border border-brand-border p-3" value={payload.rol_chatgpt || ""} onChange={(e) => set("rol_chatgpt", e.target.value)} /></label>
            <label className="grid gap-2 text-sm font-bold">Rol Claude<textarea className="min-h-24 rounded-2xl border border-brand-border p-3" value={payload.rol_claude || ""} onChange={(e) => set("rol_claude", e.target.value)} /></label>
          </div>
          <Button disabled={saving} className="justify-self-start">{saving ? "Creando..." : "Crear proyecto"}</Button>
        </form>
      </Card>
    </div>
  );
}
