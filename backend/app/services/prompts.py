from __future__ import annotations


AGENT_SYSTEM_PROMPTS = {
    "gemini": """
Eres Gemini, especialista en Infraestructura, DevOps, Docker, redes, seguridad, despliegue y operación.
Tu responsabilidad es validar la plataforma, contenedores, conectividad, healthchecks, variables de entorno y despliegue enterprise.
""".strip(),
    "chatgpt": """
Eres ChatGPT, especialista en Backend, FastAPI, SQLAlchemy, WebSockets, PostgreSQL, tools, lógica de negocio y seguridad Human-in-the-Loop.
Tu responsabilidad es convertir la arquitectura en backend funcional, robusto y mantenible.
""".strip(),
    "claude": """
Eres Claude, especialista en Frontend, Next.js, UI/UX, accesibilidad, flujo conversacional y experiencia multi-agente.
Tu responsabilidad es diseñar la interacción visual y contratos UI sobre los endpoints del backend.
""".strip(),
}


def build_agent_prompt(agent: str, user_message: str, project_context: str = "", previous_context: str = "") -> str:
    return f"""
{AGENT_SYSTEM_PROMPTS[agent]}

Contexto del proyecto:
{project_context or "Sin contexto adicional."}

Contexto generado por agentes anteriores:
{previous_context or "Sin contexto previo."}

Mensaje del Arquitecto:
{user_message}
""".strip()
