from sqlalchemy import Column, String, Text, DateTime, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database import Base
class Proyecto(Base):
    __tablename__ = 'proyectos'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    titulo = Column(String(255), nullable=False)
    nombre_slug = Column(String(255), unique=True, nullable=False)
    anio = Column(Integer, nullable=False)
    descripcion = Column(Text)
    responsable = Column(String(255))
    github_url = Column(String(255))
    instrucciones_deploy = Column(Text)
    estado = Column(String(50), default='activo')
    tecnologias = Column(JSON, default=dict)
    microservicios = Column(JSON, default=dict)
    rol_gemini = Column(Text)
    rol_chatgpt = Column(Text)
    rol_claude = Column(Text)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
