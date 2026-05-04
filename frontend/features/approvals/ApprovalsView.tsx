"use client";

import { useEffect, useMemo, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { formatDate } from "@/lib/format";
import { approvalsRepository } from "@/services/repositories";
import type { Approval, ApprovalStatus } from "@/types/domain";

type ActionKind = "approve" | "reject";
type StatusFilter = ApprovalStatus | "all";

const statusFilters: Array<{ value: StatusFilter; label: string }> = [
  { value: "pending", label: "Pendientes" },
  { value: "executed", label: "Ejecutadas" },
  { value: "rejected", label: "Rechazadas" },
  { value: "failed", label: "Fallidas" },
  { value: "all", label: "Todas" },
];

function statusTone(status: ApprovalStatus): "info" | "success" | "warning" | "danger" | "neutral" {
  if (status === "pending") return "warning";
  if (status === "approved" || status === "executed") return "success";
  if (status === "rejected") return "neutral";
  if (status === "failed") return "danger";
  return "info";
}

function extractPath(item: Approval): string | null {
  const raw = item.arguments_json?.path;
  return typeof raw === "string" && raw.trim() ? raw : null;
}

function truncate(value: string, max = 72): string {
  if (value.length <= max) return value;
  return `${value.slice(0, max - 1)}…`;
}

function filterApprovals(items: Approval[], statusFilter: StatusFilter): Approval[] {
  if (statusFilter === "all") return items;
  return items.filter((item) => item.status === statusFilter);
}

function buildCounters(items: Approval[]) {
  return items.reduce(
    (acc, item) => {
      acc.total += 1;
      acc[item.status] = (acc[item.status] ?? 0) + 1;
      return acc;
    },
    {
      total: 0,
      pending: 0,
      approved: 0,
      executed: 0,
      rejected: 0,
      failed: 0,
    } as Record<ApprovalStatus | "total", number>
  );
}

function JsonPanel({ title, value }: { title: string; value: unknown }) {
  const [copied, setCopied] = useState(false);
  const json = useMemo(() => JSON.stringify(value ?? null, null, 2), [value]);

  async function copy() {
    try {
      await navigator.clipboard.writeText(json);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="rounded-3xl border border-brand-border bg-white">
      <div className="flex items-center justify-between gap-3 border-b border-brand-border px-4 py-3">
        <p className="text-xs font-black uppercase tracking-[0.18em] text-brand-cyan">{title}</p>
        <Button type="button" variant="ghost" className="px-3 py-1 text-xs" onClick={copy}>
          {copied ? "Copiado" : "Copiar JSON"}
        </Button>
      </div>
      <pre className="vf-scrollbar max-h-72 overflow-auto rounded-b-3xl bg-brand-deep p-4 text-xs leading-5 text-brand-bright">
        {json}
      </pre>
    </div>
  );
}

function ApprovalCard({
  item,
  actionBusy,
  onApprove,
  onReject,
}: {
  item: Approval;
  actionBusy?: ActionKind;
  onApprove: (id: number) => Promise<void>;
  onReject: (id: number) => Promise<void>;
}) {
  const path = extractPath(item);
  const isPending = item.status === "pending";
  const isBusy = Boolean(actionBusy);

  return (
    <Card className="overflow-hidden">
      <div className="flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone={statusTone(item.status)}>{item.status}</Badge>
            <Badge tone="info">{item.agente}</Badge>
            <Badge>{item.tool_name}</Badge>
            {path ? <Badge tone="neutral">{truncate(path, 56)}</Badge> : null}
          </div>

          <h2 className="mt-4 text-2xl font-black text-brand-navy">Aprobación #{item.id}</h2>

          <div className="mt-3 grid gap-2 text-sm text-brand-muted md:grid-cols-2">
            <p>
              <span className="font-black text-brand-navy">Proyecto:</span>{" "}
              <code className="break-all rounded-lg bg-brand-soft px-1.5 py-0.5 text-xs">{item.proyecto_id}</code>
            </p>
            <p>
              <span className="font-black text-brand-navy">Usuario config:</span> {item.usuario_config_id}
            </p>
            <p>
              <span className="font-black text-brand-navy">Creado:</span> {item.created_at ? formatDate(item.created_at) : "sin fecha"}
            </p>
            <p>
              <span className="font-black text-brand-navy">Resuelto:</span> {item.resolved_at ? formatDate(item.resolved_at) : "Pendiente"}
            </p>
          </div>

          {path ? (
            <div className="mt-4 rounded-3xl border border-brand-cyan/20 bg-brand-cyan/5 p-4">
              <p className="text-xs font-black uppercase tracking-[0.18em] text-brand-cyan">Archivo objetivo</p>
              <code className="mt-2 block break-all text-sm font-bold text-brand-navy">{path}</code>
            </div>
          ) : null}
        </div>

        <div className="flex flex-col gap-2 sm:flex-row xl:w-56 xl:flex-col">
          <Button
            type="button"
            disabled={!isPending || isBusy}
            onClick={() => onApprove(item.id)}
            className="w-full"
          >
            {actionBusy === "approve" ? "Aprobando..." : "Aprobar"}
          </Button>
          <Button
            type="button"
            variant="danger"
            disabled={!isPending || isBusy}
            onClick={() => onReject(item.id)}
            className="w-full"
          >
            {actionBusy === "reject" ? "Rechazando..." : "Rechazar"}
          </Button>
        </div>
      </div>

      <div className="mt-6 grid gap-4 xl:grid-cols-2">
        <JsonPanel title="Argumentos de la tool" value={item.arguments_json} />
        <JsonPanel title="Resultado / error" value={{ result_json: item.result_json ?? null, error_message: item.error_message ?? null }} />
      </div>
    </Card>
  );
}

export function ApprovalsView() {
  const [allApprovals, setAllApprovals] = useState<Approval[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("pending");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<string | null>(null);
  const [busyById, setBusyById] = useState<Record<number, ActionKind | undefined>>({});

  async function refresh(nextFilter: StatusFilter = statusFilter) {
    setLoading(true);
    setError(null);

    try {
      /**
       * Fuente de verdad para el panel: siempre cargamos TODAS las aprobaciones
       * consultando el backend por estado. Luego filtramos en cliente.
       * Esto evita el bug donde /api/approvals sin status devuelve solo pending.
       */
      const all = await approvalsRepository.listAll();
      setAllApprovals(all);
      setApprovals(filterApprovals(all, nextFilter));
      setLastRefresh(new Date().toISOString());
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "No se pudieron cargar las aprobaciones");
      setAllApprovals([]);
      setApprovals([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh(statusFilter);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  async function approve(id: number) {
    setBusyById((prev) => ({ ...prev, [id]: "approve" }));
    setError(null);
    setSuccess(null);

    try {
      await approvalsRepository.approve(id);
      setSuccess(`Aprobación #${id} ejecutada correctamente.`);
      await refresh(statusFilter);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : `No se pudo aprobar #${id}`);
    } finally {
      setBusyById((prev) => ({ ...prev, [id]: undefined }));
    }
  }

  async function reject(id: number) {
    const confirmed = window.confirm(`¿Rechazar la aprobación #${id}? La tool no se ejecutará.`);
    if (!confirmed) return;

    setBusyById((prev) => ({ ...prev, [id]: "reject" }));
    setError(null);
    setSuccess(null);

    try {
      await approvalsRepository.reject(id);
      setSuccess(`Aprobación #${id} rechazada. La tool no fue ejecutada.`);
      await refresh(statusFilter);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : `No se pudo rechazar #${id}`);
    } finally {
      setBusyById((prev) => ({ ...prev, [id]: undefined }));
    }
  }

  const counters = useMemo(() => buildCounters(allApprovals), [allApprovals]);
  const currentViewCount = approvals.length;

  return (
    <div>
      <SectionHeader
        title="Human-in-the-Loop"
        sprint="Sprint 1 · Gobernanza real"
        description="Panel operativo para aprobar o rechazar tools de escritura antes de que modifiquen el filesystem del proyecto."
      />

      <div className="mb-6 grid gap-4 xl:grid-cols-[1fr_460px]">
        <Card>
          <CardTitle eyebrow="Control humano" title="Aprobaciones de tools" />
          <p className="text-sm leading-6 text-brand-muted">
            Cuando <code className="rounded-lg bg-brand-soft px-1.5 py-0.5">auto_aprobar_ejecucion=false</code>, las tools como
            <strong className="text-brand-navy"> modificar_archivo</strong> o <strong className="text-brand-navy">crear_estructura_directorios</strong> quedan en estado
            <strong className="text-brand-navy"> pending</strong> hasta que Vitoto apruebe o rechace desde esta pantalla.
          </p>

          <div className="mt-5 flex flex-wrap gap-2">
            {statusFilters.map((filter) => (
              <Button
                key={filter.value}
                type="button"
                variant={statusFilter === filter.value ? "primary" : "secondary"}
                onClick={() => setStatusFilter(filter.value)}
              >
                {filter.label}
              </Button>
            ))}
          </div>
        </Card>

        <Card>
          <CardTitle
            eyebrow="Estado"
            title="Monitor HIL"
            action={<Badge tone={counters.pending ? "warning" : "success"}>{counters.pending} pendientes</Badge>}
          />

          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-2xl bg-brand-soft p-3">
              <p className="text-xs font-black uppercase tracking-[0.16em] text-brand-muted">Total HIL</p>
              <p className="mt-1 text-2xl font-black text-brand-navy">{counters.total}</p>
            </div>
            <div className="rounded-2xl bg-brand-soft p-3">
              <p className="text-xs font-black uppercase tracking-[0.16em] text-brand-muted">Vista actual</p>
              <p className="mt-1 text-2xl font-black text-brand-navy">{currentViewCount}</p>
            </div>
            <div className="rounded-2xl bg-brand-soft p-3">
              <p className="text-xs font-black uppercase tracking-[0.16em] text-brand-muted">Ejecutadas</p>
              <p className="mt-1 text-2xl font-black text-state-success">{counters.executed + counters.approved}</p>
            </div>
            <div className="rounded-2xl bg-brand-soft p-3">
              <p className="text-xs font-black uppercase tracking-[0.16em] text-brand-muted">Rechazadas</p>
              <p className="mt-1 text-2xl font-black text-brand-muted">{counters.rejected}</p>
            </div>
          </div>

          <div className="mt-4 flex items-center justify-between gap-3">
            <p className="text-xs text-brand-muted">Última actualización: {lastRefresh ? formatDate(lastRefresh) : "sin cargar"}</p>
            <Button type="button" variant="secondary" onClick={() => refresh(statusFilter)} disabled={loading}>
              {loading ? "Actualizando..." : "Refrescar"}
            </Button>
          </div>
        </Card>
      </div>

      {error ? (
        <div className="mb-5 rounded-3xl border border-state-danger/30 bg-state-danger/10 p-4 text-sm font-bold text-state-danger">
          {error}
        </div>
      ) : null}

      {success ? (
        <div className="mb-5 rounded-3xl border border-state-success/30 bg-state-success/10 p-4 text-sm font-bold text-state-success">
          {success}
        </div>
      ) : null}

      {loading ? (
        <Card>
          <p className="text-sm font-bold text-brand-muted">Cargando aprobaciones...</p>
        </Card>
      ) : approvals.length === 0 ? (
        <EmptyState
          title={statusFilter === "pending" ? "Sin aprobaciones pendientes" : "Sin aprobaciones para este filtro"}
          description="Cuando una IA solicite modificar archivos con HIL activo, aparecerá una tarjeta para aprobar o rechazar la ejecución."
        />
      ) : (
        <div className="grid gap-5">
          {approvals.map((item) => (
            <ApprovalCard
              key={item.id}
              item={item}
              actionBusy={busyById[item.id]}
              onApprove={approve}
              onReject={reject}
            />
          ))}
        </div>
      )}
    </div>
  );
}
