import os

print("🏆 INICIANDO EL GOLDEN MASTER (CONEXIÓN TOTAL DE SPRINT 1 AL 4)...")

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"✅ {path}")

# ==========================================
# 1. FIX MENSAJES: Guardado estricto para evitar Crash en WS
# ==========================================
write_file("backend/app/services/message_service.py", r"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.history_models import MensajeHistorial

class MessageService:
    async def log(self, db: AsyncSession, *, proyecto_id, ejecucion_id=None, agente, role, content, correlation_id=None, model=None, tokens_input=0, tokens_output=0, cost_usd=0.0, latency_ms=0, tool_name=None, tool_status=None):
        remitente = agente if role == "assistant" else "Usuario"
        destinatario = "Usuario" if role == "assistant" else "Orquestador"
        
        # Mapeo estricto a las columnas que SI existen en tu Postgres
        msg = MensajeHistorial(
            proyecto_id=proyecto_id,
            remitente=remitente,
            destinatario=destinatario,
            contenido=content,
            tokens_consumidos=tokens_input + tokens_output,
            costo_estimado=cost_usd,
            incluir_en_contexto=True
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg
""")

# ==========================================
# 2. FIX ROUTERS: Tools, Agentes, Metricas, Auditoria, Archivos y Proyectos
# ==========================================
write_file("backend/app/routers/tools.py", r"""
from fastapi import APIRouter
from app.services.tools import TOOL_REGISTRY

router = APIRouter()

@router.get("")
async def list_tools():
    return [
        {
            "name": t.name,
            "description": t.description,
            "requires_approval": t.risk_level != "LOW",
            "sprint": 1 if t.name in ["crear_estructura_directorios", "modificar_archivo"] else 2,
            "category": "Escritura" if t.risk_level != "LOW" else "Lectura"
        }
        for t in TOOL_REGISTRY.values()
    ]
""")

write_file("backend/app/routers/agents.py", r"""
from fastapi import APIRouter
from app.config import get_settings

router = APIRouter()
settings = get_settings()

def _check_key(key):
    return bool(key) and "tu_llave" not in key.lower()

@router.get("")
async def list_agents():
    return [
        {"name": "gemini", "label": "Gemini", "role": "Infraestructura", "responsibility": "Docker, red, variables, despliegue", "sprint": 1, "status": "active" if _check_key(settings.gemini_api_key) else "disabled"},
        {"name": "chatgpt", "label": "ChatGPT", "role": "Backend y Datos", "responsibility": "FastAPI, PostgreSQL, WebSockets", "sprint": 1, "status": "active" if _check_key(settings.openai_api_key) else "disabled"},
        {"name": "claude", "label": "Claude", "role": "Frontend y UX", "responsibility": "Next.js, Tailwind, React", "sprint": 1, "status": "active" if _check_key(settings.anthropic_api_key) else "disabled"}
    ]
""")

write_file("backend/app/routers/metrics.py", r"""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter()

@router.get("")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    from app.models.history_models import MensajeHistorial
    from app.models import Proyecto
    
    # Obtenemos totales reales de la base de datos
    res_cost = await db.execute(select(func.sum(MensajeHistorial.costo_estimado)))
    res_proj = await db.execute(select(func.count(Proyecto.id)))
    
    total_cost = res_cost.scalar() or 0.0
    total_proj = res_proj.scalar() or 0

    return [
        {"label": "Proyectos Activos", "value": str(total_proj), "tone": "info", "trend": "global"},
        {"label": "Costo Histórico Total", "value": f"US$ {total_cost:.4f}", "tone": "success", "trend": "consumo real"},
        {"label": "Estado Servidor", "value": "Operativo", "tone": "success", "trend": "runtime"}
    ]
""")

# Reemplazamos los endpoints vacíos de projects por los reales
write_file("backend/app/routers/projects_extra.py", r"""
# Este archivo será cargado automáticamente por tu estructura
""")

# Inyectamos al final de projects.py
with open("backend/app/routers/projects.py", "a", encoding="utf-8") as f:
    f.write(r"""
@router.get('/{project_id}/messages')
async def get_project_messages(project_id: str, db: AsyncSession = Depends(get_db)):
    from app.models.history_models import MensajeHistorial
    try:
        result = await db.execute(select(MensajeHistorial).where(MensajeHistorial.proyecto_id == UUID(project_id)).order_by(MensajeHistorial.fecha_envio.asc()))
        mensajes = result.scalars().all()
        return [{
            "id": str(m.id), "proyecto_id": str(m.proyecto_id), "remitente": m.remitente, "destinatario": m.destinatario,
            "contenido": m.contenido, "tokens_consumidos": m.tokens_consumidos or 0, 
            "costo_estimado": float(m.costo_estimado) if m.costo_estimado else 0.0,
            "incluir_en_contexto": m.incluir_en_contexto, "fecha_envio": m.fecha_envio.isoformat() if m.fecha_envio else ""
        } for m in mensajes]
    except Exception as e:
        print(f"Error messages: {e}")
        return []

@router.get('/{project_id}/workspace/tree')
async def get_workspace_tree(project_id: str, db: AsyncSession = Depends(get_db)):
    from app.models import Proyecto
    from app.config import get_settings
    import os
    try:
        proyecto = await db.get(Proyecto, UUID(project_id))
        if not proyecto: return []
        base_dir = get_settings().base_projects_dir / proyecto.nombre_slug
        if not base_dir.exists(): return []
        
        def build_tree(path):
            name = os.path.basename(path)
            if os.path.isdir(path):
                return {"id": path, "name": name, "type": "folder", "path": path, "children": [build_tree(os.path.join(path, x)) for x in os.listdir(path)]}
            return {"id": path, "name": name, "type": "file", "path": path}
            
        return [build_tree(os.path.join(base_dir, x)) for x in os.listdir(base_dir)]
    except Exception as e:
        print(f"Error workspace: {e}")
        return []
""")

# Endpoint para listar archivos
with open("backend/app/routers/files.py", "a", encoding="utf-8") as f:
    f.write(r"""
from sqlalchemy import select
@router.get("/{proyecto_id}")
async def list_files(proyecto_id: UUID, db: AsyncSession = Depends(get_db)):
    from app.models import ArchivoTemporal
    result = await db.execute(select(ArchivoTemporal).where(ArchivoTemporal.proyecto_id == proyecto_id).order_by(ArchivoTemporal.fecha_creacion.desc()))
    return list(result.scalars().all())
""")

# ==========================================
# 3. FIX FRONTEND: Repositorios y Vistas
# ==========================================
with open("frontend/services/repositories.ts", "r", encoding="utf-8") as f:
    repo_content = f.read()
repo_content = repo_content.replace(
    "list: async (): Promise<UploadedFile[]> => [],",
    "list: async (projectId: string): Promise<UploadedFile[]> => normalizeArray(await fetchFromAPI(`/api/files/${projectId}`)),"
)
write_file("frontend/services/repositories.ts", repo_content)

write_file("frontend/features/files/FilesView.tsx", r"""
"use client";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { formatBytes, formatDate } from "@/lib/format";
import { mockProjects } from "@/mocks/data";
import { filesRepository, projectsRepository } from "@/services/repositories";
import type { UploadedFile, Proyecto } from "@/types/domain";

export function FilesView() {
  const [file, setFile] = useState<File | null>(null);
  const [uploaded, setUploaded] = useState<UploadedFile | null>(null);
  const [filesList, setFilesList] = useState<UploadedFile[]>([]);
  const [projects, setProjects] = useState<Proyecto[]>([]);
  
  // Usamos el primer proyecto como default para la vista
  const projectId = projects.length > 0 ? projects[0].id : mockProjects[0].id;

  useEffect(() => {
    projectsRepository.list().then(setProjects);
  }, []);

  useEffect(() => {
    filesRepository.list(projectId).then(setFilesList);
  }, [projectId, uploaded]);

  async function upload() {
    if (!file) return;
    const res = await filesRepository.upload(projectId, file);
    setUploaded(res);
    setFile(null); // Clear input
  }

  return (
    <div>
      <SectionHeader title="Archivos y artefactos" sprint="Sprint 1 + Sprint 2" description="Upload híbrido enterprise y listado de archivos en base de datos." />
      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          <Card>
            <CardTitle eyebrow="POST /api/files/{proyecto_id}/upload" title="Subida controlada" />
            <div className="rounded-3xl border border-dashed border-brand-border bg-brand-soft p-8 text-center">
              <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} className="mx-auto block rounded-2xl border border-brand-border bg-white p-3" />
              <Button onClick={upload} disabled={!file} className="mt-5">Subir archivo</Button>
            </div>
            {uploaded ? (
              <div className="mt-6 rounded-3xl border border-state-success/30 bg-state-success/10 p-5">
                <Badge tone="success">Subido Exitosamente</Badge>
                <h3 className="mt-4 text-xl font-black">{uploaded.nombre_archivo}</h3>
              </div>
            ) : null}
          </Card>

          <Card>
            <CardTitle eyebrow="GET /api/files/{proyecto_id}" title="Archivos del Proyecto" />
            <div className="space-y-3 max-h-[400px] overflow-y-auto vf-scrollbar pr-2">
                {filesList.length === 0 ? <p className="text-sm text-brand-muted">No hay archivos en la BD.</p> : null}
                {filesList.map(f => (
                    <div key={f.id} className="rounded-2xl border border-brand-border bg-white p-4">
                        <div className="flex justify-between">
                            <span className="font-bold">{f.nombre_archivo}</span>
                            <Badge>{formatBytes(f.size_bytes)}</Badge>
                        </div>
                        <p className="mt-2 text-xs text-brand-muted">Ruta: {f.ruta_archivo || "DB Inline"}</p>
                    </div>
                ))}
            </div>
          </Card>
      </div>
    </div>
  );
}
""")

write_file("frontend/features/projects/ProjectDetailView.tsx", r"""
"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { AgentBadge } from "@/components/ui/AgentBadge";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { formatDate, formatCurrency } from "@/lib/format";
import { projectsRepository, futureRepository } from "@/services/repositories";
import type { Proyecto } from "@/types/domain";

export function ProjectDetailView({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<Proyecto | null>(null);
  const [costoTotal, setCostoTotal] = useState<number>(0);

  useEffect(() => { 
      projectsRepository.get(projectId).then(setProject); 
      futureRepository.messages(projectId).then(msgs => {
          const total = msgs.reduce((acc, m) => acc + (m.costo_estimado || 0), 0);
          setCostoTotal(total);
      });
  }, [projectId]);

  if (!project) return <SectionHeader title="Cargando proyecto..." description="Consultando backend..." />;

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
            <div className="rounded-2xl bg-brand-soft p-4"><p className="text-xs font-black text-brand-muted">Costo Incurrido</p><Badge tone="warning" className="mt-1 text-sm">{formatCurrency(costoTotal)}</Badge></div>
            <div className="rounded-2xl bg-brand-soft p-4"><p className="text-xs font-black text-brand-muted">Estado</p><Badge tone="success" className="mt-1">{project.estado}</Badge></div>
            <div className="rounded-2xl bg-brand-soft p-4"><p className="text-xs font-black text-brand-muted">Año</p><p className="font-black">{project.anio}</p></div>
            <div className="rounded-2xl bg-brand-soft p-4"><p className="text-xs font-black text-brand-muted">Fecha creación</p><p className="font-bold text-sm">{formatDate(project.fecha_creacion)}</p></div>
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
""")

print("\n🚀 PARCHE APLICADO. TODO EL SISTEMA ESTÁ CONECTADO.")
print("👉 Reinicia tus contenedores: docker compose restart backend frontend")