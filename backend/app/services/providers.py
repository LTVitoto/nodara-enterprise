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
