from sqlalchemy.ext.asyncio import AsyncSession
from app.models.history_models import MensajeHistorial


class MessageRepository:

    async def create(self, db: AsyncSession, obj: dict):
        message = MensajeHistorial(**obj)
        db.add(message)
        await db.flush()   # no commit aquí (IMPORTANTE CLEAN ARCH)
        return message