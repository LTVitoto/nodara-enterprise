#!/bin/bash
set -e

echo "🛠️ Sincronizando columnas faltantes en PostgreSQL (mensajes_historial)..."

docker exec -i nodara_db psql -U arquitecto -d orquestador_db << 'SQL'
-- 1. Añadimos las columnas necesarias para el tracking de Agentes y Herramientas (Sprint 2/3)
ALTER TABLE mensajes_historial ADD COLUMN IF NOT EXISTS ejecucion_id UUID;
ALTER TABLE mensajes_historial ADD COLUMN IF NOT EXISTS model VARCHAR;
ALTER TABLE mensajes_historial ADD COLUMN IF NOT EXISTS tokens_input INTEGER DEFAULT 0;
ALTER TABLE mensajes_historial ADD COLUMN IF NOT EXISTS tokens_output INTEGER DEFAULT 0;
ALTER TABLE mensajes_historial ADD COLUMN IF NOT EXISTS cost_usd NUMERIC(10,6) DEFAULT 0.000000;
ALTER TABLE mensajes_historial ADD COLUMN IF NOT EXISTS latency_ms INTEGER DEFAULT 0;
ALTER TABLE mensajes_historial ADD COLUMN IF NOT EXISTS tool_name VARCHAR;
ALTER TABLE mensajes_historial ADD COLUMN IF NOT EXISTS tool_status VARCHAR;
ALTER TABLE mensajes_historial ADD COLUMN IF NOT EXISTS correlation_id VARCHAR;
SQL

echo "✅ Base de datos parcheada. El Orquestador ahora puede guardar los mensajes."
