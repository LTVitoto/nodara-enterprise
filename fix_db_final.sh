#!/bin/bash
set -e

echo "🛠️ Inyectando columnas y tablas faltantes directamente en PostgreSQL..."

docker exec -i nodara_db psql -U arquitecto -d orquestador_db << 'SQL'
-- 1. Añadimos la columna faltante que estaba causando el Error 500
ALTER TABLE usuarios_config ADD COLUMN IF NOT EXISTS saldo_virtual_gemini NUMERIC(10,4) DEFAULT 0.0000;

-- 2. Aseguramos que la tabla de Gobernanza HIL exista (por si SQLAlchemy falló en crearla)
CREATE TABLE IF NOT EXISTS tool_call_pendiente (
    id SERIAL PRIMARY KEY,
    proyecto_id UUID,
    usuario_config_id INTEGER REFERENCES usuarios_config(id),
    agente VARCHAR NOT NULL,
    tool_name VARCHAR NOT NULL,
    arguments_json JSONB DEFAULT '{}',
    status VARCHAR DEFAULT 'pending',
    result_json JSONB,
    error_message VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);
SQL

echo "✅ Base de datos parcheada a nivel de motor."
