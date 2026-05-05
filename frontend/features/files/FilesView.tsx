"use client";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { formatBytes } from "@/lib/format";
import { filesRepository, projectsRepository } from "@/services/repositories";
import type { UploadedFile, Proyecto } from "@/types/domain";

export function FilesView() {
  const [file, setFile] = useState<File | null>(null);
  const [uploaded, setUploaded] = useState<UploadedFile | null>(null);
  const [filesList, setFilesList] = useState<UploadedFile[]>([]);
  const [projects, setProjects] = useState<Proyecto[]>([]);
  const [projectId, setProjectId] = useState<string>("");

  useEffect(() => {
    projectsRepository.list().then(p => {
        setProjects(p);
        if (p.length > 0) setProjectId(p[0].id);
    });
  }, []);

  useEffect(() => {
    if (projectId) filesRepository.list(projectId).then(setFilesList);
  }, [projectId, uploaded]);

  async function upload() {
    if (!file || !projectId) return;
    const res = await filesRepository.upload(projectId, file);
    setUploaded(res);
    setFile(null);
  }

  return (
    <div>
      <SectionHeader title="Archivos y artefactos" sprint="Sprint 1 + 2" description="Sube y visualiza archivos del proyecto seleccionado." />
      
      {projects.length > 0 && (
        <div className="mb-6">
          <label className="mr-4 font-bold text-sm">Seleccionar Proyecto:</label>
          <select className="border p-2 rounded-xl text-sm" value={projectId} onChange={(e) => setProjectId(e.target.value)}>
            {projects.map(p => <option key={p.id} value={p.id}>{p.titulo}</option>)}
          </select>
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          <Card>
            <CardTitle eyebrow="POST /api/files/upload" title="Subida controlada" />
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
            <CardTitle eyebrow="GET /api/files" title="Archivos del Proyecto" />
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
