from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.history_models import Ejecucion


async def crear_ejecucion(db: AsyncSession, proyecto_id, correlation_id):
    ejecucion = Ejecucion(
        proyecto_id=proyecto_id,
        correlation_id=correlation_id
    )
    db.add(ejecucion)
    await db.commit()
    await db.refresh(ejecucion)
    return ejecucion


async def finalizar_ejecucion(db: AsyncSession, ejecucion_id, total_tokens, total_cost):
    result = await db.execute(
        select(Ejecucion).where(Ejecucion.id == ejecucion_id)
    )
    ejecucion = result.scalar_one()

    ejecucion.total_tokens = total_tokens
    ejecucion.total_cost_usd = total_cost

    await db.commit()
    return ejecucion