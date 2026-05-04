import { WS_BASE_URL } from "@/lib/env";
import type { WsIncomingEvent, WsOutboundMessage } from "@/types/websocket";

export interface MultiAgentWsClient {
  connect: () => void;
  send: (message: string) => void;
  close: () => void;
}

function normalizeWsEvent(raw: any): WsIncomingEvent {
  const eventType = raw?.type ?? raw?.event ?? "unknown";
  const data = raw?.data ?? {};

  return {
    type: eventType,
    correlation_id: raw?.correlation_id ?? data?.correlation_id,
    agent: raw?.agent ?? data?.agent,
    delta: raw?.delta ?? data?.delta,
    content: raw?.content ?? data?.content,
    message:
      raw?.message ??
      data?.message ??
      data?.status ??
      data?.detail,
    approval_id: raw?.approval_id ?? data?.approval_id,
    tool_name: raw?.tool_name ?? data?.tool_name,
    payload: data,
    error: raw?.error ?? data?.error,
    timestamp: raw?.timestamp ?? data?.timestamp
  };
}

export function createMultiAgentWsClient(params: {
  projectId: string;
  usuarioConfigId: number;
  onEvent: (event: WsIncomingEvent) => void;
  onStatus?: (status: "connecting" | "open" | "closed" | "error") => void;
}): MultiAgentWsClient {
  let socket: WebSocket | null = null;

  function connect() {
    params.onStatus?.("connecting");

    const url = `${WS_BASE_URL}/ws/chat/${params.projectId}?usuario_config_id=${params.usuarioConfigId}`;

    socket = new WebSocket(url);

    socket.onopen = () => {
      console.log("[WS] conectado:", url);
      params.onStatus?.("open");
    };

    socket.onclose = (event) => {
      console.log("[WS] cerrado:", event.code, event.reason);
      params.onStatus?.("closed");
    };

    socket.onerror = (event) => {
      console.error("[WS] error:", event);
      params.onStatus?.("error");
    };

    socket.onmessage = (message) => {
      try {
        const raw = JSON.parse(message.data);
        const normalized = normalizeWsEvent(raw);
        console.log("[WS] evento normalizado:", normalized);
        params.onEvent(normalized);
      } catch {
        params.onEvent({
          type: "agent_delta",
          delta: String(message.data)
        });
      }
    };
  }

  function send(message: string) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      console.warn("[WS] socket no está abierto. Estado:", socket?.readyState);
      return;
    }

    const payload: WsOutboundMessage = {
      message,
      correlation_id: crypto.randomUUID()
    };

    console.log("[WS] enviando:", payload);
    socket.send(JSON.stringify(payload));
  }

  function close() {
    socket?.close();
    socket = null;
  }

  return { connect, send, close };
}

export function simulateWsEvents(message: string, onEvent: (event: WsIncomingEvent) => void) {
  const agent = message.toLowerCase().startsWith("gemini:")
    ? "gemini"
    : message.toLowerCase().startsWith("claude:")
      ? "claude"
      : message.toLowerCase().startsWith("alineación:") || message.toLowerCase().startsWith("alineacion:")
        ? "orchestrator"
        : "chatgpt";

  const script: WsIncomingEvent[] = [
    { type: "orchestration_start", message: "Iniciando orquestación" },
    { type: "agent_selected", agent, message: `Agente seleccionado: ${agent}` },
    { type: "agent_message_start", agent },
    { type: "agent_delta", agent, delta: "Validación mock activa. " },
    { type: "agent_delta", agent, delta: "El frontend está conectado al contrato Sprint 1 y preparado para Sprint 2-4 con mocks. " },
    { type: "agent_message_end", agent },
    { type: "orchestration_end", message: "Orquestación finalizada" }
  ];

  script.forEach((event, index) => setTimeout(() => onEvent(event), 220 * (index + 1)));
}
