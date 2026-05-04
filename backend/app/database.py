from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()

engine = create_async_engine(
    settings.effective_database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def _run_lightweight_migrations(conn) -> None:
    """Migraciones idempotentes para alinear la DB real del Sprint 1.

    create_all() crea tablas faltantes, pero no altera columnas existentes.
    Estas sentencias permiten mantener la DB creada por Gemini y agregar
    solo columnas backward-compatible aprobadas para el enfoque híbrido enterprise.
    """
    await conn.execute(text("ALTER TABLE archivos_temporales ADD COLUMN IF NOT EXISTS ruta_archivo TEXT"))
    await conn.execute(text("ALTER TABLE archivos_temporales ADD COLUMN IF NOT EXISTS mime_type VARCHAR(120)"))
    await conn.execute(text("ALTER TABLE archivos_temporales ADD COLUMN IF NOT EXISTS size_bytes INTEGER"))


async def init_db() -> None:
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _run_lightweight_migrations(conn)
