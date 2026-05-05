import os

print("🧹 LIMPIANDO FORMULARIO DE PROYECTOS...")

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"✅ {path}")

write_file("frontend/features/projects/ProjectForm.tsx", r"""
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { projectsRepository } from "@/services/repositories";
import type { ProyectoCreate } from "@/types/domain";

const defaultProject: ProyectoCreate = {
  titulo: "",
  descripcion: "",
  anio: new Date().getFullYear(),
  tecnologias: { backend: "FastAPI", frontend: "Next.js" },
  microservicios: { db: "orquestador_db" },
  instrucciones_deploy: "docker compose up -d",
  github_url: "",
  rol_gemini: "Experto en Infraestructura y Contenedores",
  rol_chatgpt: "Experto en Arquitectura Backend",
  rol_claude: "Experto en UX y Frontend",
  estado: "activo",
  responsable: "Vitoto"
};

export function ProjectForm() {
  const router = useRouter();
  const [payload, setPayload] = useState<ProyectoCreate>(defaultProject);
  const [saving, setSaving] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
        const created = await projectsRepository.create(payload);
        router.push(`/projects/${created.id}`);
    } catch(e) {
        console.error("Error creando proyecto", e);
        setSaving(false);
    }
  }

  function set<K extends keyof ProyectoCreate>(key: K, value: ProyectoCreate[K]) {
    setPayload((prev) => ({ ...prev, [key]: value }));
  }

  return (
    <div>
      <SectionHeader title="Crear proyecto" description="Registra una nueva iniciativa. La carpeta física y el repositorio Git se crearán automáticamente." />
      <Card>
        <CardTitle eyebrow="SETUP" title="Datos base del proyecto" />
        <form onSubmit={submit} className="grid gap-5">
          <div className="grid gap-5 md:grid-cols-2">
            <label className="grid gap-2 text-sm font-bold">Título (Nombre de la carpeta)
              <input required className="rounded-2xl border border-brand-border p-3" value={payload.titulo} onChange={(e) => set("titulo", e.target.value)} placeholder="Ej: NODARA Enterprise" />
            </label>
            <label className="grid gap-2 text-sm font-bold">Responsable
              <input required className="rounded-2xl border border-brand-cyan/50 p-3 bg-brand-soft" value={payload.responsable || ""} onChange={(e) => set("responsable", e.target.value)} />
            </label>
          </div>
          
          <label className="grid gap-2 text-sm font-bold">Descripción (Contexto para la IA)
            <textarea required className="min-h-28 rounded-2xl border border-brand-border p-3" value={payload.descripcion || ""} onChange={(e) => set("descripcion", e.target.value)} placeholder="Describe de qué trata el proyecto para que la IA entienda el contexto..." />
          </label>
          
          <div className="grid gap-5 md:grid-cols-2">
            <label className="grid gap-2 text-sm font-bold">GitHub URL (Opcional - GitOps Auto)
              <input className="rounded-2xl border border-brand-border p-3" value={payload.github_url || ""} onChange={(e) => set("github_url", e.target.value || null)} placeholder="https://github.com/LTVitoto/repo.git"/>
            </label>
            <label className="grid gap-2 text-sm font-bold">Año
              <input type="number" className="rounded-2xl border border-brand-border p-3" value={payload.anio} onChange={(e) => set("anio", Number(e.target.value))} />
            </label>
          </div>
          
          <div className="grid gap-5 md:grid-cols-3">
            <label className="grid gap-2 text-sm font-bold">Rol Gemini
              <textarea className="min-h-24 rounded-2xl border border-brand-border p-3 text-xs" value={payload.rol_gemini || ""} onChange={(e) => set("rol_gemini", e.target.value)} />
            </label>
            <label className="grid gap-2 text-sm font-bold">Rol ChatGPT
              <textarea className="min-h-24 rounded-2xl border border-brand-border p-3 text-xs" value={payload.rol_chatgpt || ""} onChange={(e) => set("rol_chatgpt", e.target.value)} />
            </label>
            <label className="grid gap-2 text-sm font-bold">Rol Claude
              <textarea className="min-h-24 rounded-2xl border border-brand-border p-3 text-xs" value={payload.rol_claude || ""} onChange={(e) => set("rol_claude", e.target.value)} />
            </label>
          </div>
          <Button disabled={saving} className="justify-self-start mt-2">{saving ? "Creando Entorno..." : "Crear proyecto"}</Button>
        </form>
      </Card>
    </div>
  );
}
""")

print("🚀 LISTO. Ve al navegador y recarga la página /projects/new.")