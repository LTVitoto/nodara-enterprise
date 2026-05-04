from sqlalchemy.ext.asyncio import AsyncSession
from app.models.history_models import MensajeHistorial, Ejecucion
from app.core.tracing import get_correlation_id


class MessageLogger:

    @staticmethod
    async def log_message(
        db: AsyncSession,
        *,
        proyecto_id,
        ejecucion_id,
        remitente,
        destinatario,
        contenido,
        model=None,
        tokens_input=0,
        tokens_output=0,
        cost_usd=0.0,
        latency_ms=0,
        tool_name=None,
        tool_status=None
    ):
        msg = MensajeHistorial(
            proyecto_id=proyecto_id,
            ejecucion_id=ejecucion_id,
            remitente=remitente,
            destinatario=destinatario,
            contenido=contenido,
            model=model,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            tool_name=tool_name,
            tool_status=tool_status,
            correlation_id=get_correlation_id(),
        )

        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg