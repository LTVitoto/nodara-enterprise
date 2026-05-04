from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.models.history_models import MensajeHistorial

class MessageService:

    async def log(
        self,
        db: AsyncSession,
        *,
        proyecto_id,
        ejecucion_id,
        agente,
        role,
        content,
        correlation_id,
        model=None,
        tokens_input=0,
        tokens_output=0,
        cost_usd=0.0,
        latency_ms=0,
        tool_name=None,
        tool_status=None,
    ):
        # 🔥 FIX: Mapear 'agente' y 'role' a 'remitente' y 'destinatario'
        remitente = agente if role == "assistant" else "Usuario"
        destinatario = "Usuario" if role == "assistant" else "Orquestador"

        msg = MensajeHistorial(
            proyecto_id=proyecto_id,
            ejecucion_id=ejecucion_id,
            remitente=remitente,
            destinatario=destinatario,
            contenido=content,
            model=model,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            correlation_id=correlation_id,
            tool_name=tool_name,
            tool_status=tool_status,
            fecha_envio=datetime.utcnow(),
        )

        db.add(msg)
        await db.commit()
        await db.refresh(msg)

        return msg
