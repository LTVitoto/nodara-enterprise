from fastapi import APIRouter

from .proyectos import router as proyectos
from .mensajes import router as mensajes
from .ejecuciones import router as ejecuciones

router = APIRouter()

router.include_router(proyectos)
router.include_router(mensajes)
router.include_router(ejecuciones)