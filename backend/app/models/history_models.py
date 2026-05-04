from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Ejecucion(Base):
    __tablename__ = "ejecuciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proyecto_id = Column(UUID(as_uuid=True), nullable=False)
    correlation_id = Column(String, nullable=False)

    total_tokens = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)

    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)

    mensajes = relationship("MensajeHistorial", back_populates="ejecucion")


class MensajeHistorial(Base):
    __tablename__ = "mensajes_historial"

    id = Column(Integer, primary_key=True)

    proyecto_id = Column(UUID(as_uuid=True), nullable=True)

    ejecucion_id = Column(UUID(as_uuid=True), ForeignKey("ejecuciones.id"))
    ejecucion = relationship("Ejecucion", back_populates="mensajes")

    remitente = Column(String(50), nullable=False)
    destinatario = Column(String(50), nullable=False)

    contenido = Column(Text, nullable=False)

    tokens_consumidos = Column(Integer, default=0)
    costo_estimado = Column(Float, default=0.0)

    incluir_en_contexto = Column(Boolean, default=True)

    model = Column(String)
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)

    latency_ms = Column(Integer, default=0)

    tool_name = Column(String)
    tool_status = Column(String)

    correlation_id = Column(String)

    fecha_envio = Column(DateTime, default=datetime.utcnow)