from sqlalchemy.ext.asyncio import AsyncSession
from app.models.history_models import Ejecucion
from datetime import datetime
import uuid


class ExecutionRepository:

    async def create(self, db: AsyncSession, proyecto_id: str, correlation_id: str):
        execution = Ejecucion(
            id=uuid.uuid4(),
            proyecto_id=proyecto_id,
            correlation_id=correlation_id,
            started_at=datetime.utcnow(),
            total_tokens=0,
            total_cost_usd=0.0,
        )

        db.add(execution)
        await db.flush()  # IMPORTANTE: no commit aquí (Clean Architecture)
        return execution

    async def update_finish(
        self,
        db: AsyncSession,
        execution: Ejecucion,
        total_tokens: int,
        total_cost_usd: float,
    ):
        execution.total_tokens = total_tokens
        execution.total_cost_usd = total_cost_usd
        execution.finished_at = datetime.utcnow()

        db.add(execution)
        await db.flush()

        return execution

    async def get_by_id(self, db: AsyncSession, execution_id):
        return await db.get(Ejecucion, execution_id)