from datetime import datetime
from app.db import get_db

async def create_execution(project_id, correlation_id):
    db = get_db()

    result = await db.execute("""
        INSERT INTO ejecuciones (id, proyecto_id, correlation_id, started_at, status)
        VALUES (gen_random_uuid(), :p, :c, now(), 'running')
        RETURNING id
    """, {"p": project_id, "c": correlation_id})

    return result.scalar()


async def finalize_execution(exec_id, duration, tokens, cost):
    db = get_db()

    await db.execute("""
        UPDATE ejecuciones
        SET ended_at = now(),
            duration_ms = :d,
            total_tokens = :t,
            total_cost_usd = :c,
            status = 'completed'
        WHERE id = :id
    """, {"id": exec_id, "d": duration, "t": tokens, "c": cost})


async def save_message(exec_id, agent, tipo, contenido, tokens, cost):
    db = get_db()

    await db.execute("""
        INSERT INTO mensajes_historial
        (ejecucion_id, agente, tipo, contenido, tokens, cost_usd, timestamp)
        VALUES (:e, :a, :t, :c, :tk, :co, now())
    """, {
        "e": exec_id,
        "a": agent,
        "t": tipo,
        "c": contenido,
        "tk": tokens,
        "co": cost
    })