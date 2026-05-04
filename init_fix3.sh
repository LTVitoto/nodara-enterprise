#!/bin/bash
set -e

echo "🛡️ Aplicando escudo contra dependencias circulares en routers/approvals.py..."

cat << 'EOF' > backend/app/routers/approvals.py
from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import ApprovalOut

router = APIRouter()

@router.get("", response_model=list[ApprovalOut])
async def list_approvals(status: str = "pending", db: AsyncSession = Depends(get_db)):
    # 🔥 IMPORTACIÓN DIFERIDA: Solo se evalúa cuando alguien llama a este endpoint
    from app.models import ToolCallPendiente
    
    result = await db.execute(
        select(ToolCallPendiente)
        .where(ToolCallPendiente.status == status)
        .order_by(ToolCallPendiente.id.desc())
    )
    return list(result.scalars().all())


@router.get("/{approval_id}", response_model=ApprovalOut)
async def get_approval(approval_id: int, db: AsyncSession = Depends(get_db)):
    from app.models import ToolCallPendiente
    
    obj = await db.get(ToolCallPendiente, approval_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Aprobación no encontrada")
    return obj


@router.post("/{approval_id}/approve", response_model=ApprovalOut)
async def approve_tool_call(approval_id: int, db: AsyncSession = Depends(get_db)):
    from app.models import ToolCallPendiente, ToolCallStatus
    from app.services.tools import ToolExecutionContext, execute_tool_by_name
    
    approval = await db.get(ToolCallPendiente, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Aprobación no encontrada")
    if approval.status != ToolCallStatus.PENDING.value:
        raise HTTPException(status_code=409, detail=f"Solicitud ya resuelta: {approval.status}")

    approval.status = ToolCallStatus.APPROVED.value
    await db.commit()
    await db.refresh(approval)

    try:
        context = ToolExecutionContext(
            proyecto_id=approval.proyecto_id,
            usuario_config_id=approval.usuario_config_id,
            agente=approval.agente,
            db=db,
            human_approved=True,
        )
        # 🔥 Ejecutamos la tool real saltando el HIL ya que el humano la acaba de aprobar
        result = await execute_tool_by_name(approval.tool_name, approval.arguments_json, context, bypass_hil=True)
        
        approval.status = ToolCallStatus.EXECUTED.value
        approval.result_json = result
        approval.resolved_at = datetime.utcnow()
        await db.commit()
        await db.refresh(approval)
        return approval
        
    except Exception as exc:
        approval.status = ToolCallStatus.FAILED.value
        approval.error_message = str(exc)
        approval.resolved_at = datetime.utcnow()
        await db.commit()
        await db.refresh(approval)
        return approval


@router.post("/{approval_id}/reject", response_model=ApprovalOut)
async def reject_tool_call(approval_id: int, db: AsyncSession = Depends(get_db)):
    from app.models import ToolCallPendiente, ToolCallStatus
    
    approval = await db.get(ToolCallPendiente, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Aprobación no encontrada")
    if approval.status != ToolCallStatus.PENDING.value:
        raise HTTPException(status_code=409, detail=f"Solicitud ya resuelta: {approval.status}")

    approval.status = ToolCallStatus.REJECTED.value
    approval.resolved_at = datetime.utcnow()
    await db.commit()
    await db.refresh(approval)
    return approval
EOF

echo "✅ Listo. Uvicorn debería poder compilar el árbol de dependencias exitosamente ahora."