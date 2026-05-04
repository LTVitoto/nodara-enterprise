#!/bin/bash
set -e

echo "🔌 INYECTANDO PROVEEDORES DE IA Y ESTABILIZANDO WEBSOCKETS..."

# ==========================================
# 1. FIX BACKEND: PROVIDERS (Añadiendo ChatGPT y Claude)
# ==========================================
cat << 'PY' > backend/app/services/providers.py
from app.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

class ProviderTransientError(Exception): pass
class ProviderPermanentError(Exception): pass
class ProviderQuotaError(Exception): pass

def normalize_provider_error(agent: str, exc: Exception) -> str:
    text = str(exc).lower()
    if "resource_exhausted" in text or "429" in text:
        return f"{agent} no pudo responder (429 Quota/Rate Limit)."
    if "api_key" in text or "key not valid" in text or "401" in text:
        return f"{agent} rechazó la API key (Inválida o falta saldo)."
    return f"{agent} error: {str(exc)[:200]}"

class MockProvider:
    def __init__(self, agent: str): self.agent = agent
    async def generate(self, prompt: str) -> str: return f"[MOCK:{self.agent}] Respuesta simulada."

class GeminiProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "gemini-2.5-flash"

    async def generate(self, prompt: str) -> str:
        try:
            from google import genai
            import anyio
            client = genai.Client(api_key=self.api_key)
            response = await anyio.to_thread.run_sync(lambda: client.models.generate_content(model=self.model, contents=prompt))
            return getattr(response, "text", str(response))
        except Exception as exc: raise ProviderTransientError(str(exc)) from exc

class ChatGPTProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "gpt-4o-mini"

    async def generate(self, prompt: str) -> str:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as exc: raise ProviderTransientError(str(exc)) from exc

class ClaudeProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "claude-3-haiku-20240307"

    async def generate(self, prompt: str) -> str:
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=self.api_key)
            response = await client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as exc: raise ProviderTransientError(str(exc)) from exc

def get_provider(agent: str):
    if settings.use_mock_apis: return MockProvider(agent)

    if agent == "gemini":
        if not settings.gemini_api_key: raise ProviderPermanentError("Falta GEMINI_API_KEY")
        return GeminiProvider(settings.gemini_api_key)
    elif agent == "chatgpt":
        if not settings.openai_api_key: raise ProviderPermanentError("Falta OPENAI_API_KEY")
        return ChatGPTProvider(settings.openai_api_key)
    elif agent == "claude":
        if not settings.anthropic_api_key: raise ProviderPermanentError("Falta ANTHROPIC_API_KEY")
        return ClaudeProvider(settings.anthropic_api_key)

    return MockProvider(agent)
PY
echo "✅ Proveedores IA (ChatGPT, Claude, Gemini) inyectados."

# ==========================================
# 2. FIX FRONTEND: WEBSOCKET CLIENT (Control estricto)
# ==========================================
cat << 'TS' > frontend/services/websocket-client.ts
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
TS
echo "✅ Cliente WebSocket del Frontend blindado contra re-renders."

