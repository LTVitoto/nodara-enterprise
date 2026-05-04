from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import ProyectoCreate, ProyectoOut, ProyectoUpdate
from app.services.slug import slugify

router = APIRouter()

@router.get("", response_model=list[ProyectoOut])
async def list_projects(db: AsyncSession = Depends(get_db)):
    from app.models import Proyecto
    result = await db.execute(select(Proyecto).order_by(Proyecto.fecha_creacion.desc()))
    return list(result.scalars().all())

@router.post("", response_model=ProyectoOut)
async def create_project(payload: ProyectoCreate, db: AsyncSession = Depends(get_db)):
    from app.models import Proyecto
    slug = payload.nombre_slug or slugify(payload.titulo)
    obj = Proyecto(
        nombre_slug=slug,
        titulo=payload.titulo,
        anio=payload.anio,
        descripcion=payload.descripcion,
        tecnologias=payload.tecnologias,
        microservicios=payload.microservicios,
        instrucciones_deploy=payload.instrucciones_deploy,
        github_url=payload.github_url,
        rol_gemini=payload.rol_gemini,
        rol_chatgpt=payload.rol_chatgpt,
        rol_claude=payload.rol_claude,
        estado=payload.estado,
    )
    db.add(obj)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=f"Ya existe un proyecto con nombre_slug={slug}") from exc
    await db.refresh(obj)
    return obj

@router.get("/{project_id}", response_model=ProyectoOut)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    from app.models import Proyecto
    try:
        # Validación segura de UUID para evitar Crash 500
        uid = UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato UUID inválido")
        
    obj = await db.get(Proyecto, uid)
    if not obj:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return obj

@router.patch("/{project_id}", response_model=ProyectoOut)
async def update_project(project_id: UUID, payload: ProyectoUpdate, db: AsyncSession = Depends(get_db)):
    from app.models import Proyecto
    obj = await db.get(Proyecto, project_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.get('/{project_id}/workspace/tree')
async def get_workspace_tree(project_id: str): return []

@router.get('/{project_id}/messages')
async def get_project_messages(project_id: str): return []
