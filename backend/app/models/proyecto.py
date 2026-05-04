from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from app.database import Base


class Proyecto(Base):
    __tablename__ = "proyectos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_slug = Column(String(100), unique=True, nullable=False)
    titulo = Column(String(150), nullable=False)
    anio = Column(Integer, nullable=False)
    descripcion = Column(Text)

    tecnologias = Column(JSONB, default=[])
    microservicios = Column(JSONB, default=[])

    instrucciones_deploy = Column(Text)
    github_url = Column(String(255))

    rol_gemini = Column(Text, nullable=False)
    rol_chatgpt = Column(Text, nullable=False)
    rol_claude = Column(Text, nullable=False)

    estado = Column(String(20), default="Activo")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)