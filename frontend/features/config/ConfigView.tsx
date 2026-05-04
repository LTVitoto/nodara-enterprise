"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { configRepository } from "@/services/repositories";
import type { UsuarioConfig } from "@/types/domain";

export function ConfigView() {
  const [config, setConfig] = useState<UsuarioConfig | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => { configRepository.list().then((items) => setConfig(items[0] || null)); }, []);

  async function toggleAutoApprove() {
    if (!config) return;
    setSaving(true);
    const updated = await configRepository.patch(config.id, { auto_aprobar_ejecucion: !config.auto_aprobar_ejecucion });
    setConfig(updated);
    setSaving(false);
  }

  return (
    <div>
      <SectionHeader
        title="Configuración operacional"
        sprint="Sprint 1 · Configuración"
        description="Control BYOK, modo de aprobación, saldos virtuales y flags del orquestador."
      />

      <div className="grid gap-6 xl:grid-cols-[.8fr_1.2fr]">
        <Card>
          <CardTitle eyebrow="Usuario Config" title={`ID ${config?.id ?? "..."}`} />
          <div className="space-y-4">
            <div className="flex items-center justify-between rounded-2xl bg-brand-soft p-4">
              <span className="font-bold">Derivar en problemas</span>
              <Badge tone={config?.derivar_en_problemas ? "success" : "neutral"}>{config?.derivar_en_problemas ? "Activo" : "Inactivo"}</Badge>
            </div>
            <div className="flex items-center justify-between rounded-2xl bg-brand-soft p-4">
              <span className="font-bold">Auto aprobar ejecución</span>
              <Badge tone={config?.auto_aprobar_ejecucion ? "success" : "warning"}>{config?.auto_aprobar_ejecucion ? "ON" : "OFF"}</Badge>
            </div>
            <Button onClick={toggleAutoApprove} disabled={!config || saving} className="w-full">
              {config?.auto_aprobar_ejecucion ? "Desactivar auto aprobación" : "Activar auto aprobación"}
            </Button>
          </div>
        </Card>

        <Card>
          <CardTitle eyebrow="BYOK" title="Estado de API Keys y saldos" />
          <div className="grid gap-4 md:grid-cols-3">
            {[
              ["OpenAI", config?.has_api_key_openai, config?.saldo_virtual_openai],
              ["Anthropic", config?.has_api_key_anthropic, config?.saldo_virtual_anthropic],
              ["Gemini", config?.has_api_key_gemini, config?.saldo_virtual_gemini]
            ].map(([name, hasKey, saldo]) => (
              <div key={String(name)} className="rounded-3xl border border-brand-border bg-white p-5">
                <div className="text-lg font-black">{String(name)}</div>
                <Badge tone={hasKey ? "success" : "neutral"} className="mt-3">{hasKey ? "Key cargada" : "Sin key"}</Badge>
                <p className="mt-5 text-sm text-brand-muted">Saldo virtual</p>
                <p className="text-2xl font-black text-brand-navy">{Number(saldo || 0).toFixed(4)}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
