-- /orquestador-multi-agente/postgres_init/initdb.sql

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS Usuarios_Config (
    id SERIAL PRIMARY KEY,
    derivar_en_problemas BOOLEAN DEFAULT FALSE,
    auto_aprobar_ejecucion BOOLEAN DEFAULT FALSE, -- Control Dev vs Prod
    saldo_virtual_openai NUMERIC(10,4) DEFAULT 0.0000,
    saldo_virtual_anthropic NUMERIC(10,4) DEFAULT 0.0000,
    api_key_openai VARCHAR(255),
    api_key_anthropic VARCHAR(255),
    api_key_gemini VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS Proyectos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre_slug VARCHAR(100) UNIQUE NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    anio INTEGER NOT NULL,
    descripcion TEXT NOT NULL,
    tecnologias JSONB NOT NULL DEFAULT '[]',
    microservicios JSONB NOT NULL DEFAULT '[]',
    instrucciones_deploy TEXT,
    github_url VARCHAR(255),
    rol_gemini TEXT NOT NULL,
    rol_chatgpt TEXT NOT NULL,
    rol_claude TEXT NOT NULL,
    estado VARCHAR(20) DEFAULT 'Activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Mensajes_Historial (
    id SERIAL PRIMARY KEY,
    proyecto_id UUID REFERENCES Proyectos(id) ON DELETE CASCADE,
    remitente VARCHAR(50) NOT NULL,
    destinatario VARCHAR(50) NOT NULL,
    contenido TEXT NOT NULL,
    tokens_consumidos INTEGER DEFAULT 0,
    costo_estimado NUMERIC(10,6) DEFAULT 0.000000,
    incluir_en_contexto BOOLEAN DEFAULT TRUE,
    fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Archivos_Temporales (
    id SERIAL PRIMARY KEY,
    proyecto_id UUID REFERENCES Proyectos(id) ON DELETE CASCADE,
    nombre_archivo VARCHAR(255) NOT NULL,
    contenido_codigo TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- INSERCIÓN SEGURA (IDEMPOTENTE)
INSERT INTO Usuarios_Config (derivar_en_problemas, auto_aprobar_ejecucion) 
SELECT TRUE, TRUE 
WHERE NOT EXISTS (SELECT 1 FROM Usuarios_Config LIMIT 1);

CREATE TABLE IF NOT EXISTS Eventos_Auditoria (
    id SERIAL PRIMARY KEY,
    actor VARCHAR(255),
    action VARCHAR(255),
    target VARCHAR(255),
    severity VARCHAR(50) DEFAULT 'info',
    fecha_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
