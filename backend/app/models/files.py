from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.database import Base

class ArchivoTemporal(Base):
    __tablename__ = "archivos_temporales"
    id = Column(Integer, primary_key=True, autoincrement=True)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id", ondelete="CASCADE"))
    nombre_archivo = Column(String(255), nullable=False)
    contenido_codigo = Column(Text, nullable=False)
    version = Column(Integer, default=1)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    ruta_archivo = Column(Text)
    mime_type = Column(String(120))
    size_bytes = Column(Integer)
