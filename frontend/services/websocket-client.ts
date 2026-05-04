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
    message: raw?.message ?? data?.message ?? data?.status ?? data?.detail,
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
  let isIntentionallyClosed = false; // 🔥 Bandera para evitar re-conexiones zombis

  function connect() {
    if (socket) return; // Evita conexiones duplicadas
    params.onStatus?.("connecting");
    isIntentionallyClosed = false;

    const url = `${WS_BASE_URL}/ws/chat/${params.projectId}?usuario_config_id=${params.usuarioConfigId}`;
    socket = new WebSocket(url);

    socket.onopen = () => {
      console.log("[WS] conectado:", url);
      params.onStatus?.("open");
    };

    socket.onclose = (event) => {
      console.log(`[WS] cerrado: ${event.code}`);
      params.onStatus?.("closed");
      socket = null;
    };

    socket.onerror = (event) => {
      if (!isIntentionallyClosed) {
        console.error("[WS] error:", event);
        params.onStatus?.("error");
      }
    };

    socket.onmessage = (message) => {
      try {
        const raw = JSON.parse(message.data);
        params.onEvent(normalizeWsEvent(raw));
      } catch {
        params.onEvent({ type: "agent_delta", delta: String(message.data) });
      }
    };
  }

  function send(message: string) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      console.warn("[WS] Intento de envío sin conexión abierta.");
      return;
    }
    const payload: WsOutboundMessage = { message, correlation_id: crypto.randomUUID() };
    socket.send(JSON.stringify(payload));
  }

  function close() {
    isIntentionallyClosed = true;
    if (socket) {
      socket.close(1000, "Component Unmounted");
      socket = null;
    }
  }

  return { connect, send, close };
}

export function simulateWsEvents(message: string, onEvent: (event: WsIncomingEvent) => void) {
  // Mock simplificado
  onEvent({ type: "orchestration_start", message: "Iniciando orquestación mock" });
  setTimeout(() => onEvent({ type: "orchestration_end", message: "Fin mock" }), 1000);
}
