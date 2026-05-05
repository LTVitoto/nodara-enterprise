from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base
class EventoAuditoria(Base):
    __tablename__ = 'eventos_auditoria'
    id = Column(Integer, primary_key=True, autoincrement=True)
    actor = Column(String(255))
    action = Column(String(255))
    target = Column(String(255))
    severity = Column(String(50), default='info')
    fecha_evento = Column(DateTime, default=datetime.utcnow)
