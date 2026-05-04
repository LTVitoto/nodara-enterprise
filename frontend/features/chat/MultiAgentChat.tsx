"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { AgentBadge } from "@/components/ui/AgentBadge";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { DATA_MODE, DEFAULT_USER_CONFIG_ID, WS_BASE_URL } from "@/lib/env";
import type { AgentName } from "@/types/domain";
import type { WsIncomingEvent } from "@/types/websocket";

function normalizeAgent(agent?: string): AgentName {
  if (agent === "gemini" || agent === "chatgpt" || agent === "claude" || agent === "orchestrator") return agent;
  return "chatgpt";
}

export function MultiAgentChat({ projectId }: { projectId: string }) {
  const [input, setInput] = useState("gemini: saludame con un hola mundo en ingles");
  const [events, setEvents] = useState<WsIncomingEvent[]>([]);
  const [status, setStatus] = useState<"connecting" | "open" | "closed" | "error" | "mock">("closed");
  const wsRef = useRef<WebSocket | null>(null);

  const liveContent = useMemo(() => events.filter((e) => e.type === "agent_delta" || e.type === "agent_response").map((e) => e.delta || e.message || e.content || "").join(""), [events]);

  useEffect(() => {
    if (DATA_MODE === "mock") {
      setStatus("mock");
      return;
    }

    setStatus("connecting");
    const wsUrl = `${WS_BASE_URL}/ws/chat/${projectId}?usuario_config_id=${DEFAULT_USER_CONFIG_ID}`;
    const socket = new WebSocket(wsUrl);
    wsRef.current = socket;

    socket.onopen = () => setStatus("open");
    socket.onclose = () => setStatus("closed");
    socket.onerror = () => setStatus("error");

    socket.onmessage = (event) => {
      try {
        const raw = JSON.parse(event.data);
        const wsEvent: WsIncomingEvent = {
          type: raw.event || raw.type || "unknown",
          agent: raw.data?.agent,
          message: raw.data?.message || raw.data?.error,
          tool_name: raw.data?.tool,
        };
        setEvents((prev) => [...prev, wsEvent]);
      } catch (e) {
        console.warn("Mensaje no parseable", event.data);
      }
    };

    return () => {
      socket.close();
    };
  }, [projectId]);

  function send() {
    if (!input.trim()) return;
    setEvents([]);
    
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ message: input, correlation_id: crypto.randomUUID() }));
    } else {
      console.warn("WebSocket no conectado");
    }
  }

  return (
    <div>
      <SectionHeader
        title="Chat Multi-Agente"
        sprint="Sprint 1 · WebSocket"
        description="Cliente visual conectado a las IAs reales. Envía comandos específicos usando los prefijos gemini: o chatgpt:."
      />
      <div className="grid gap-6 xl:grid-cols-[1fr_380px]">
        <Card className="min-h-[620px]">
          <CardTitle eyebrow="Conversación" title="Sala de orquestación" action={<Badge tone={status === "open" ? "success" : "danger"}>{status}</Badge>} />
          <div className="mb-5 flex flex-wrap gap-2">
            <Button type="button" variant="secondary" onClick={() => setInput("gemini: saludame con un hola mundo en ingles")}>Prueba Gemini</Button>
            <Button type="button" variant="secondary" onClick={() => setInput("chatgpt: dime adios en ingles")}>Prueba ChatGPT</Button>
          </div>
          <div className="vf-scrollbar h-[360px] overflow-y-auto rounded-3xl border border-brand-border bg-brand-soft p-5">
            {events.length === 0 ? (
              <p className="text-sm text-brand-muted">Escribe un comando para interactuar con los agentes.</p>
            ) : (
              <div className="space-y-3">
                {events.map((event, idx) => (
                  <div key={`${event.type}-${idx}`} className="rounded-2xl bg-white p-3 shadow-sm">
                    <div className="flex items-center justify-between gap-3">
                      <code className="text-xs font-black text-brand-cyan">{event.type}</code>
                      {event.agent ? <AgentBadge agent={normalizeAgent(event.agent)} /> : null}
                    </div>
                    {event.message ? <p className="mt-2 text-sm text-brand-muted">{event.message}</p> : null}
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="mt-5 rounded-3xl border border-brand-cyan/20 bg-brand-cyan/5 p-5">
            <p className="text-xs font-black uppercase tracking-[0.2em] text-brand-cyan">Respuesta Consolidada</p>
            <p className="mt-3 min-h-16 text-sm leading-6 text-brand-navy">{liveContent || "Esperando respuesta de la IA..."}</p>
          </div>
          <div className="mt-5 flex gap-3">
            <input className="min-w-0 flex-1 rounded-2xl border border-brand-border px-4 py-3 font-medium" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && send()} />
            <Button onClick={send} disabled={status !== "open"}>Enviar</Button>
          </div>
        </Card>
        <Card>
          <CardTitle eyebrow="Eventos soportados" title="Contrato WebSocket" />
          <div className="space-y-2">
            {["orchestration_start", "agent_response", "agent_tool_call", "hil_required", "agent_error", "orchestration_end"].map((event) => (
              <div key={event} className="rounded-xl bg-brand-soft px-3 py-2 text-xs font-bold text-brand-muted">{event}</div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
