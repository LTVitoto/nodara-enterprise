#!/bin/bash
set -e

echo "🛠️ Sincronizando columnas faltantes en PostgreSQL (usuarios_config)..."

docker exec -i nodara_db psql -U arquitecto -d orquestador_db << 'SQL'
-- 1. Añadimos TODAS las columnas que SQLAlchemy espera en UsuariosConfig
ALTER TABLE usuarios_config ADD COLUMN IF NOT EXISTS derivar_en_problemas BOOLEAN DEFAULT FALSE;
ALTER TABLE usuarios_config ADD COLUMN IF NOT EXISTS saldo_virtual_openai NUMERIC(10,4) DEFAULT 0.0000;
ALTER TABLE usuarios_config ADD COLUMN IF NOT EXISTS saldo_virtual_anthropic NUMERIC(10,4) DEFAULT 0.0000;
ALTER TABLE usuarios_config ADD COLUMN IF NOT EXISTS api_key_openai VARCHAR(255);
ALTER TABLE usuarios_config ADD COLUMN IF NOT EXISTS api_key_anthropic VARCHAR(255);
ALTER TABLE usuarios_config ADD COLUMN IF NOT EXISTS api_key_gemini VARCHAR(255);

-- 2. Nos aseguramos de que al menos exista el ID=1 para que el GET y PATCH no fallen
INSERT INTO usuarios_config (id, derivar_en_problemas, auto_aprobar_ejecucion)
VALUES (1, false, false)
ON CONFLICT (id) DO NOTHING;
SQL

echo "✅ Base de datos parcheada. El Error 500 (Falso CORS) ha desaparecido."
