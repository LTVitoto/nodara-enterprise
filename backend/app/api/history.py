
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import MensajeHistorial

router = APIRouter(prefix="/api/history", tags=["history"])

@router.get("/{proyecto_id}")
def get_history(proyecto_id: str, db: Session = Depends(get_db)):
    mensajes = db.query(MensajeHistorial)        .filter(MensajeHistorial.proyecto_id == proyecto_id)        .order_by(MensajeHistorial.created_at.desc())        .all()

    return mensajes
