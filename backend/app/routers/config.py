from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter()

@router.get("")
async def get_config(db: AsyncSession = Depends(get_db)):
    try:
        from app.models.governance import UsuarioConfig
        result = await db.execute(select(UsuarioConfig))
        configs = result.scalars().all()
        # Si no hay config, devolvemos un default seguro en vez de fallar
        if not configs:
            return [{"id": 1, "auto_aprobar_ejecucion": False}]
        return configs
    except Exception as e:
        # Evita el Error 500 que causa el bloqueo de CORS
        print(f"Error en BD Config: {e}")
        return [{"id": 1, "auto_aprobar_ejecucion": False, "error": str(e)}]
