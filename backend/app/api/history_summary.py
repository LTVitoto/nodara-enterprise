
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.history_models import Ejecucion

router = APIRouter(prefix="/api/history", tags=["history"])

@router.get("/summary/{proyecto_id}")
def summary(proyecto_id: str, db: Session = Depends(get_db)):
    total_cost = db.query(func.sum(Ejecucion.total_cost_usd))        .filter(Ejecucion.proyecto_id == proyecto_id)        .scalar() or 0

    total_tokens = db.query(func.sum(Ejecucion.total_tokens))        .filter(Ejecucion.proyecto_id == proyecto_id)        .scalar() or 0

    executions = db.query(Ejecucion)        .filter(Ejecucion.proyecto_id == proyecto_id)        .all()

    duration_days = 0
    if executions:
        start = min(e.started_at for e in executions if e.started_at)
        end = max(e.finished_at for e in executions if e.finished_at)
        duration_days = (end - start).days if start and end else 0

    return {
        "total_cost_usd": total_cost,
        "total_tokens": total_tokens,
        "duration_days": duration_days,
        "executions": len(executions)
    }
