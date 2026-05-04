"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { AgentBadge } from "@/components/ui/AgentBadge";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { DATA_MODE, DEFAULT_USER_CONFIG_ID } from "@/lib/env";
import { createMultiAgentWsClient, simulateWsEvents } from "@/services/websocket-client";
import type { AgentName } from "@/types/domain";
import type { WsIncomingEvent } from "@/types/websocket";

function normalizeAgent(agent?: string): AgentName {
  if (agent === "gemini" || agent === "chatgpt" || agent === "claude" || agent === "orchestrator") return agent;
  return "chatgpt";
}

export function MultiAgentChat({ projectId }: { projectId: string }) {
  const [input, setInput] = useState("ChatGPT: valida el contrato Sprint 1 y responde breve.");
  const [events, setEvents] = useState<WsIncomingEvent[]>([]);
  const [status, setStatus] = useState<"connecting" | "open" | "closed" | "error" | "mock">("closed");
  const clientRef = useRef<ReturnType<typeof createMultiAgentWsClient> | null>(null);

  const liveContent = useMemo(() => events.filter((e) => e.type === "agent_delta").map((e) => e.delta || e.content || "").join(""), [events]);

  useEffect(() => {
    if (DATA_MODE === "mock") {
      setStatus("mock");
      return;
    }
    const client = createMultiAgentWsClient({
      projectId,
      usuarioConfigId: DEFAULT_USER_CONFIG_ID,
      onEvent: (event) => setEvents((prev) => [...prev, event]),
      onStatus: setStatus
    });
    clientRef.current = client;
    client.connect();
    return () => client.close();
  }, [projectId]);

  function send() {
    setEvents([]);
    if (status === "open" && clientRef.current) clientRef.current.send(input);
    else {
      setStatus("mock");
      simulateWsEvents(input, (event) => setEvents((prev) => [...prev, event]));
    }
  }

  return (
    <div>
      <SectionHeader
        title="Chat Multi-Agente"
        sprint="Sprint 1 · WebSocket"
        description="Cliente visual para /ws/chat/{proyecto_id}?usuario_config_id=1. Arquitectura vigente: Gemini Infra + ChatGPT Fullstack."
      />
      <div className="grid gap-6 xl:grid-cols-[1fr_380px]">
        <Card className="min-h-[620px]">
          <CardTitle eyebrow="Conversación" title="Sala de orquestación" action={<Badge tone={status === "open" ? "success" : status === "error" ? "danger" : "info"}>{status}</Badge>} />
          <div className="mb-5 flex flex-wrap gap-2">
            {[
              "Gemini: revisa infraestructura",
              "ChatGPT: valida backend, frontend y orquestación",
              "Alineación: cierre ejecutivo"
            ].map((preset) => <Button key={preset} type="button" variant="secondary" onClick={() => setInput(preset)}>{preset.split(":")[0]}</Button>)}
          </div>
          <div className="vf-scrollbar h-[360px] overflow-y-auto rounded-3xl border border-brand-border bg-brand-soft p-5">
            {events.length === 0 ? (
              <p className="text-sm text-brand-muted">Envía un mensaje para ver streaming y eventos de orquestación.</p>
            ) : (
              <div className="space-y-3">
                {events.map((event, idx) => (
                  <div key={`${event.type}-${idx}`} className="rounded-2xl bg-white p-3 shadow-sm">
                    <div className="flex items-center justify-between gap-3">
                      <code className="text-xs font-black text-brand-cyan">{event.type}</code>
                      {event.agent ? <AgentBadge agent={normalizeAgent(event.agent)} /> : null}
                    </div>
                    {(event.message || event.delta || event.error) ? <p className="mt-2 text-sm text-brand-muted">{event.message || event.delta || event.error}</p> : null}
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="mt-5 rounded-3xl border border-brand-cyan/20 bg-brand-cyan/5 p-5">
            <p className="text-xs font-black uppercase tracking-[0.2em] text-brand-cyan">Respuesta streaming</p>
            <p className="mt-3 min-h-16 text-sm leading-6 text-brand-navy">{liveContent || "Esperando deltas..."}</p>
          </div>
          <div className="mt-5 flex gap-3">
            <input className="min-w-0 flex-1 rounded-2xl border border-brand-border px-4 py-3 font-medium" value={input} onChange={(e) => setInput(e.target.value)} />
            <Button onClick={send}>Enviar</Button>
          </div>
        </Card>
        <Card>
          <CardTitle eyebrow="Eventos soportados" title="Contrato WebSocket" />
          <div className="space-y-2">
            {["orchestration_start", "agent_selected", "agent_message_start", "agent_delta", "agent_message_end", "human_approval_required", "tool_execution_start", "tool_execution_end", "agent_error", "orchestration_end"].map((event) => (
              <div key={event} className="rounded-xl bg-brand-soft px-3 py-2 text-xs font-bold text-brand-muted">{event}</div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
