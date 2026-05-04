"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { StatCard } from "@/components/ui/StatCard";
import { Badge } from "@/components/ui/Badge";

import {
  configRepository,
  futureRepository,
  projectsRepository
} from "@/services/repositories";

import type {
  MetricCard,
  Proyecto,
  UsuarioConfig
} from "@/types/domain";

export function DashboardView() {
  const [config, setConfig] = useState<UsuarioConfig | null>(null);
  const [projects, setProjects] = useState<Proyecto[]>([]);
  const [metrics, setMetrics] = useState<MetricCard[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [cfg, p, m] = await Promise.all([
          configRepository.list(),
          projectsRepository.list(),
          futureRepository.metrics()
        ]);

        /* =========================
           CONFIG SAFE
        ========================= */
        setConfig(Array.isArray(cfg) ? cfg[0] ?? null : null);

        /* =========================
           PROJECTS SAFE
        ========================= */
        setProjects(Array.isArray(p) ? p : []);

        /* =========================
           🔥 METRICS NORMALIZATION
        ========================= */
        let safeMetrics: MetricCard[] = [];

        if (Array.isArray(m)) {
          safeMetrics = m;
        } else if (m && typeof m === "object") {
          // backend devuelve objeto en vez de array
          safeMetrics = [
            {
              label: "Proyectos Totales",
              value: String((m as any).total_projects ?? 0),
              trend: "global",
              tone: "info"
            },
            {
              label: "Agentes Activos",
              value: String((m as any).active_agents ?? 0),
              trend: "runtime",
              tone: "success"
            },
            {
              label: "Aprobaciones Pendientes",
              value: String((m as any).approvals_pending ?? 0),
              trend: "human loop",
              tone: "warning"
            }
          ];
        } else {
          // fallback duro (nunca rompe UI)
          safeMetrics = [];
        }

        setMetrics(safeMetrics);

      } catch (err) {
        console.error("Dashboard load error:", err);
        setMetrics([]);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  return (
    <div>
      <SectionHeader
        title="Control Tower Multi-Agente"
        sprint="Sprint 1 · Operación base"
        description="Vista ejecutiva para gobernar proyectos, aprobaciones humanas, endpoints activos y roadmap completo de la plataforma."
        action={
          <Link href="/projects/new">
            <Button>Crear Proyecto</Button>
          </Link>
        }
      />

      {/* =========================
          KPI BASE
      ========================= */}
      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Backend"
          value="Online"
          trend="GET /health OK"
          tone="success"
        />

        <StatCard
          label="Proyectos"
          value={String(projects.length)}
          trend={projects.length ? "datos disponibles" : "sin proyectos aún"}
          tone="info"
        />

        <StatCard
          label="Auto aprobación"
          value={config?.auto_aprobar_ejecucion ? "ON" : "OFF"}
          trend="Human-in-the-Loop"
          tone={config?.auto_aprobar_ejecucion ? "success" : "warning"}
        />

        <StatCard
          label="Sprints"
          value="1 → 4"
          trend="roadmap diseñado"
          tone="info"
        />
      </div>

      {/* =========================
          ARQUITECTURA + ENDPOINTS
      ========================= */}
      <div className="mt-8 grid gap-6 xl:grid-cols-[1.2fr_.8fr]">
        <Card>
          <CardTitle
            eyebrow="Arquitectura"
            title="Flujo operacional definido"
          />

          <div className="grid gap-4 md:grid-cols-3">
            {[
              ["Gemini", "Infraestructura, Docker, .env y despliegue"],
              ["ChatGPT", "Backend, modelo de datos, WebSocket y tools"],
              ["Claude", "Frontend, UX enterprise y experiencia visual"]
            ].map(([name, text]) => (
              <div
                key={name}
                className="rounded-3xl border border-brand-border bg-brand-soft p-5"
              >
                <div className="text-lg font-black text-brand-navy">
                  {name}
                </div>
                <p className="mt-2 text-sm leading-6 text-brand-muted">
                  {text}
                </p>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <CardTitle
            eyebrow="Contrato"
            title="Endpoints Sprint 1"
          />

          <div className="space-y-3 text-sm">
            {[
              "GET /health",
              "GET /api/config",
              "GET /api/projects",
              "POST /api/projects",
              "GET /api/approvals",
              "WS /ws/chat/{proyecto_id}"
            ].map((endpoint) => (
              <div
                key={endpoint}
                className="flex items-center justify-between rounded-2xl bg-brand-lilac/70 px-4 py-3"
              >
                <code className="font-bold text-brand-navy">
                  {endpoint}
                </code>
                <Badge tone="success">ready</Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* =========================
          METRICS DINÁMICAS
      ========================= */}
      <div className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        {loading ? (
          <div className="col-span-4 text-center text-sm text-gray-500">
            Cargando métricas...
          </div>
        ) : metrics.length === 0 ? (
          <div className="col-span-4 text-center text-sm text-gray-400">
            No hay métricas disponibles
          </div>
        ) : (
          metrics.map((metric) => (
            <StatCard key={metric.label} {...metric} />
          ))
        )}
      </div>
    </div>
  );
}