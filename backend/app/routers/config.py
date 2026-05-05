from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.config import get_settings
router = APIRouter()
settings = get_settings()
@router.get('')
async def get_config(db: AsyncSession = Depends(get_db)):
    from app.models.governance import UsuarioConfig
    res = await db.execute(select(UsuarioConfig))
    cfg = res.scalars().first()
    return [{
        'id': cfg.id if cfg else 1,
        'auto_aprobar_ejecucion': cfg.auto_aprobar_ejecucion if cfg else False,
        'has_api_key_github': bool(settings.github_personal_access_token),
        'has_api_key_openai': bool(settings.openai_api_key),
        'has_api_key_anthropic': bool(settings.anthropic_api_key),
        'has_api_key_gemini': bool(settings.gemini_api_key)
    }]
@router.patch('/{config_id}')
async def update_config(config_id: int, payload: dict, db=Depends(get_db)):
    from app.models.governance import UsuarioConfig
    cfg = await db.get(UsuarioConfig, config_id)
    if not cfg: cfg = UsuarioConfig(id=config_id); db.add(cfg)
    for k, v in payload.items():
        if hasattr(cfg, k): setattr(cfg, k, v)
    await db.commit()
    return {'status': 'ok'}
