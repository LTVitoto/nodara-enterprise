#!/bin/bash
set -e

echo "🛠️ Sincronizando la tabla CORRECTA (usuario_config en singular)..."

docker exec -i nodara_db psql -U arquitecto -d orquestador_db << 'SQL'
-- Añadimos las columnas a la tabla singular que SQLAlchemy realmente usa
ALTER TABLE usuario_config ADD COLUMN IF NOT EXISTS derivar_en_problemas BOOLEAN DEFAULT FALSE;
ALTER TABLE usuario_config ADD COLUMN IF NOT EXISTS saldo_virtual_openai NUMERIC(10,4) DEFAULT 0.0000;
ALTER TABLE usuario_config ADD COLUMN IF NOT EXISTS saldo_virtual_anthropic NUMERIC(10,4) DEFAULT 0.0000;
ALTER TABLE usuario_config ADD COLUMN IF NOT EXISTS saldo_virtual_gemini NUMERIC(10,4) DEFAULT 0.0000;
ALTER TABLE usuario_config ADD COLUMN IF NOT EXISTS api_key_openai VARCHAR(255);
ALTER TABLE usuario_config ADD COLUMN IF NOT EXISTS api_key_anthropic VARCHAR(255);
ALTER TABLE usuario_config ADD COLUMN IF NOT EXISTS api_key_gemini VARCHAR(255);

-- Garantizamos que exista la fila 1 para el frontend
INSERT INTO usuario_config (id, derivar_en_problemas, auto_aprobar_ejecucion)
VALUES (1, false, false)
ON CONFLICT (id) DO NOTHING;
SQL

echo "Como tu Arquitecto, te pido disculpas por este dolor de cabeza. He revisado a fondo el archivo `contenido_full_db.txt` y los logs que me enviaste, y acabo de encontrar al **verdadero y absoluto culpable**. 

Es un clásico error de desincronización de nombres en la base de datos. ¡Tenemos **dos tablas** distintas compitiendo!

Si miras tu base de datos, tienes esto:
1. `usuarios_config` (**PLURAL**): Creada por tu archivo original `initdb.sql`. A esta tabla fue a la que le inyectamos todas las columnas en el script anterior (`fix_db_final2.sh`).
2. `usuario_config` (**SINGULAR**): Creada automáticamente por SQLAlchemy (FastAPI) al arrancar. Esta es la tabla que el backend *realmente* está consultando. ¡Y esta tabla solo tiene 2 columnas (`id` y `auto_aprobar_ejecucion`)!

Cuando SQLAlchemy hace el `PATCH` o el `GET`, le dice a Postgres: *"Dame la columna `derivar_en_problemas` de la tabla `usuario_config` (singular)"*. Postgres responde: *"Esa columna no existe en esa tabla"* (Error 500), y tu navegador grita "Falso CORS".

### 🚀 El Fix Definitivo (La Sincronización Singular)

Vamos a inyectarle las columnas a la tabla **correcta** (la singular) y dejaremos la base de datos alineada para siempre.

Ejecuta este comando en tu terminal:
```bash
cat << 'EOF' > fix_db_singular.sh
#!/bin/bash
set -e

echo "🛠️ Sincronizando la tabla CORRECTA (usuario_config en singular)..."

docker exec -i nodara_db psql -U arquitecto -d orquestador_db << 'SQL'
-- Añadimos las columnas a la tabla singular que SQLAlchemy realmente usa
ALTER TABLE usuario_config ADD COLUMN IF NOT EXISTS derivar_en_problemas BOOLEAN DEFAULT FALSE;
ALTER TABLE usuario_config ADD COLUMN IF NOT EXISTS saldo_virtual_openai NUMERIC(10,4) DEFAULT 0.0000;
ALTER TABLE usuario_config ADD COLUMN IF NOT EXISTS saldo_virtual_anthropic NUMERIC(10,4) DEFAULT 0.0000;
ALTER TABLE usuario_config ADD COLUMN IF NOT EXISTS saldo_virtual_gemini NUMERIC(10,4) DEFAULT 0.0000;
ALTER TABLE usuario_config ADD COLUMN IF NOT EXISTS api_key_openai VARCHAR(255);
ALTER TABLE usuario_config ADD COLUMN IF NOT EXISTS api_key_anthropic VARCHAR(255);
ALTER TABLE usuario_config ADD COLUMN IF NOT EXISTS api_key_gemini VARCHAR(255);

-- Garantizamos que exista la fila 1 para el frontend
INSERT INTO usuario_config (id, derivar_en_problemas, auto_aprobar_ejecucion)
VALUES (1, false, false)
ON CONFLICT (id) DO NOTHING;
SQL

echo "✅ ¡Base de datos parcheada en la tabla correcta!"
