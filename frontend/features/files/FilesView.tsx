"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { formatBytes } from "@/lib/format";
import { mockProjects } from "@/mocks/data";
import { filesRepository } from "@/services/repositories";
import type { UploadedFile } from "@/types/domain";

export function FilesView() {
  const [file, setFile] = useState<File | null>(null);
  const [uploaded, setUploaded] = useState<UploadedFile | null>(null);
  const projectId = mockProjects[0].id;

  async function upload() {
    if (!file) return;
    setUploaded(await filesRepository.upload(projectId, file));
  }

  return (
    <div>
      <SectionHeader title="Archivos y artefactos" sprint="Sprint 1 + Sprint 2" description="Upload híbrido enterprise: snippets pequeños en DB, archivos pesados en filesystem con metadata en PostgreSQL." />
      <Card>
        <CardTitle eyebrow="POST /api/files/{proyecto_id}/upload" title="Subida controlada" />
        <div className="rounded-3xl border border-dashed border-brand-border bg-brand-soft p-8 text-center">
          <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} className="mx-auto block rounded-2xl border border-brand-border bg-white p-3" />
          <Button onClick={upload} disabled={!file} className="mt-5">Subir archivo</Button>
        </div>
        {uploaded ? (
          <div className="mt-6 rounded-3xl border border-brand-border bg-white p-5">
            <div className="flex flex-wrap items-center gap-2"><Badge tone="success">subido</Badge><Badge>{uploaded.mime_type || "sin mime"}</Badge><Badge>{formatBytes(uploaded.size_bytes)}</Badge></div>
            <h3 className="mt-4 text-xl font-black">{uploaded.nombre_archivo}</h3>
            <p className="mt-2 text-sm text-brand-muted">Ruta física: {uploaded.ruta_archivo || "No aplica / contenido en DB"}</p>
          </div>
        ) : null}
      </Card>
    </div>
  );
}
