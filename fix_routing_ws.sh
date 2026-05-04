#!/bin/bash
set -e

echo "🧠 INYECTANDO ENRUTAMIENTO INTELIGENTE Y ESTABILIZANDO WEBSOCKET..."

# ==========================================
# 1. FIX BACKEND: ORQUESTADOR (Enrutamiento por Prefijo)
# ==========================================
cat << 'PY' > backend/app/services/orchestrator.py
import uuid
from datetime import datetime
from app.database import AsyncSessionLocal
from app.core.tracing import ensure_correlation_id
from app.services.providers import get_provider, normalize_provider_error
from app.services.message_service import MessageService
from app.services.tools import execute_tool_by_name, ToolExecutionContext

def ws_event(event: str, correlation_id: str, data: dict):
    return {"event": event, "correlation_id": correlation_id, "data": data}

message_service = MessageService()

async def _execute_pipeline(websocket, project_id: uuid.UUID, usuario_config_id: int, data: dict, db, ejecucion):
    raw_prompt = data.get("message", "")
    correlation_id = ejecucion.correlation_id

    # 🔥 FIX: Lógica de enrutamiento basada en el prefijo del mensaje
    lower_prompt = raw_prompt.lower()
    if lower_prompt.startswith("gemini:"):
        agents = ["gemini"]
        prompt = raw_prompt[7:].strip()
    elif lower_prompt.startswith("chatgpt:"):
        agents = ["chatgpt"]
        prompt = raw_prompt[8:].strip()
    elif lower_prompt.startswith("claude:"):
        agents = ["claude"]
        prompt = raw_prompt[7:].strip()
    else:
        agents = data.get("agents", ["chatgpt"])
        prompt = raw_prompt

    await websocket.send_json(ws_event("orchestration_start", correlation_id, {"project_id": str(project_id), "agents": agents}))

    for agent in agents:
        try:
            provider = get_provider(agent)
        except Exception as provider_err:
            await websocket.send_json(ws_event("agent_error", correlation_id, {"agent": agent, "error": str(provider_err)}))
            continue
            
        loop_active = True
        current_prompt = prompt

        while loop_active:
            try:
                # LLAMADA A LA IA REAL
                response = await provider.generate(current_prompt)
                
                if '"tool_name"' in response: 
                    import json
                    try:
                        tool_req = json.loads(response)
                        tool_name = tool_req.get("tool_name")
                        tool_args = tool_req.get("arguments", {})
                        
                        await websocket.send_json(ws_event("agent_tool_call", correlation_id, {"tool": tool_name}))
                        
                        context = ToolExecutionContext(
                            proyecto_id=project_id, 
                            usuario_config_id=usuario_config_id, 
                            agente=agent, 
                            db=db
                        )
                        tool_result = await execute_tool_by_name(tool_name, tool_args, context)
                        
                        if tool_result.get("requires_human_approval"):
                            await websocket.send_json(ws_event("hil_required", correlation_id, tool_result))
                            loop_active = False 
                            break
                        
                        current_prompt = f"Resultado de tool {tool_name}: {json.dumps(tool_result)}. ¿Cuál es el siguiente paso?"
                        
                    except json.JSONDecodeError:
                        loop_active = False 
                else:
                    loop_active = False 

                await websocket.send_json(ws_event("agent_response", correlation_id, {"agent": agent, "message": response}))

            except Exception as exc:
                error_msg = normalize_provider_error(agent, exc)
                await websocket.send_json(ws_event("agent_error", correlation_id, {"agent": agent, "error": error_msg}))
                loop_active = False

    return {"status": "completed"}

async def run_orchestrator(websocket, proyecto_id: str, usuario_config_id: int, data: dict):
    from app.models.history_models import Ejecucion 
    correlation_id = ensure_correlation_id(data.get("correlation_id"))
    
    try:
        p_id = uuid.UUID(proyecto_id)
    except ValueError:
        await websocket.send_json(ws_event("error", correlation_id, {"message": "UUID de proyecto inválido"}))
        return {"status": "error"}
    
    try:
        async with AsyncSessionLocal() as db:
            ejecucion = Ejecucion(id=uuid.uuid4(), proyecto_id=p_id, correlation_id=correlation_id, started_at=datetime.utcnow())
            db.add(ejecucion)
            await db.commit()
            await db.refresh(ejecucion)
            
            try:
                await message_service.log(
                    db=db, proyecto_id=p_id, ejecucion_id=ejecucion.id, 
                    agente="user", role="user", content=data.get("message", ""), correlation_id=correlation_id
                )
            except Exception as sql_err:
                pass
            
            result = await _execute_pipeline(websocket, p_id, usuario_config_id, data, db, ejecucion)
            
            ejecucion.finished_at = datetime.utcnow()
            await db.commit()
            await websocket.send_json(ws_event("orchestration_end", correlation_id, result))
            return result
    except Exception as e:
        await websocket.send_json(ws_event("agent_error", correlation_id, {"agent": "orchestrator", "error": f"Fallo Crítico: {str(e)}"}))
        return {"status": "error"}
PY
echo "✅ Orquestador actualizado para enrutamiento por IA."

# ==========================================
# 2. FIX FRONTEND: COMPONENTE CHAT
# ==========================================
# Refactorizamos el frontend para limpiar conexiones zombis y estabilizar React
cat << 'TSX' > frontend/features/chat/MultiAgentChat.tsx
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
TSX
echo "✅ Componente de Chat Frontend refactorizado."

