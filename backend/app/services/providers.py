from app.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


# ================================
# ERRORES TIPADOS
# ================================

class ProviderTransientError(Exception):
    """Error temporal (retryable)"""
    pass


class ProviderPermanentError(Exception):
    """Error permanente (no retry)"""
    pass


class ProviderQuotaError(Exception):
    """Error de cuota / billing"""
    pass


# ================================
# NORMALIZADOR DE ERRORES (CLAVE)
# ================================

def normalize_provider_error(agent: str, exc: Exception) -> str:
    text = str(exc)

    if "RESOURCE_EXHAUSTED" in text or "429" in text:
        return (
            f"{agent} no pudo responder porque la API devolvió 429 RESOURCE_EXHAUSTED. "
            "Esto indica cuota agotada, billing no habilitado o límite del modelo alcanzado."
        )

    if "API_KEY_INVALID" in text or "API key not valid" in text:
        return (
            f"{agent} rechazó la API key. La llave es inválida o no corresponde al proyecto."
        )

    if "permission_denied" in text.lower():
        return f"{agent} no tiene permisos para usar este modelo o API."

    return f"{agent} error no controlado: {text[:300]}"


# ================================
# GEMINI PROVIDER (REAL)
# ================================

class GeminiProvider:
    default_model = "gemini-2.5-flash"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = self.default_model

    async def generate(self, prompt: str) -> str:
        try:
            from google import genai
            import anyio

            client = genai.Client(api_key=self.api_key)

            def _call():
                return client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                )

            response = await anyio.to_thread.run_sync(_call)

            text = getattr(response, "text", None)
            if not text:
                text = str(response)

            return text

        except Exception as exc:
            msg = str(exc)

            if "API_KEY_INVALID" in msg:
                raise ProviderPermanentError(msg) from exc

            if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
                raise ProviderQuotaError(msg) from exc

            if "timeout" in msg.lower():
                raise ProviderTransientError(msg) from exc

            raise ProviderTransientError(msg) from exc


# ================================
# MOCK PROVIDER
# ================================

class MockProvider:
    def __init__(self, agent: str):
        self.agent = agent

    async def generate(self, prompt: str) -> str:
        return f"[MOCK:{self.agent}] respuesta simulada"


# ================================
# FACTORY
# ================================

def get_provider(agent: str):

    if settings.use_mock_apis:
        return MockProvider(agent)

    if agent == "gemini":
        if not settings.gemini_api_key:
            raise ProviderPermanentError("GEMINI_API_KEY no configurada")
        return GeminiProvider(settings.gemini_api_key)

    # fallback
    return MockProvider(agent)