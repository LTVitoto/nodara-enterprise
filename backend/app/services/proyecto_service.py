from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.proyecto import Proyecto


async def crear_proyecto(db: AsyncSession, data: dict):
    proyecto = Proyecto(**data)
    db.add(proyecto)
    await db.commit()
    await db.refresh(proyecto)
    return proyecto


async def listar_proyectos(db: AsyncSession):
    result = await db.execute(select(Proyecto))
    return result.scalars().all()


async def obtener_proyecto(db: AsyncSession, proyecto_id):
    result = await db.execute(
        select(Proyecto).where(Proyecto.id == proyecto_id)
    )
    return result.scalar_one_or_none()


async def eliminar_proyecto(db: AsyncSession, proyecto_id):
    proyecto = await obtener_proyecto(db, proyecto_id)
    if proyecto:
        await db.delete(proyecto)
        await db.commit()
    return proyecto