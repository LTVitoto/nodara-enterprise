from sqlalchemy.ext.asyncio import AsyncSession
from app.models.history_models import MensajeHistorial

class MessageService:
    async def log(self, db: AsyncSession, *, proyecto_id, ejecucion_id=None, agente, role, content, correlation_id=None, model=None, tokens_input=0, tokens_output=0, cost_usd=0.0, latency_ms=0, tool_name=None, tool_status=None):
        remitente = agente if role == "assistant" else "Usuario"
        destinatario = "Usuario" if role == "assistant" else "Orquestador"
        
        # Mapeo estricto a las columnas que SI existen en tu Postgres
        msg = MensajeHistorial(
            proyecto_id=proyecto_id,
            remitente=remitente,
            destinatario=destinatario,
            contenido=content,
            tokens_consumidos=tokens_input + tokens_output,
            costo_estimado=cost_usd,
            incluir_en_contexto=True
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg
