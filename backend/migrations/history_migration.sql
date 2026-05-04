
CREATE TABLE ejecuciones (
    id UUID PRIMARY KEY,
    proyecto_id UUID NOT NULL,
    correlation_id TEXT NOT NULL,
    total_tokens INT DEFAULT 0,
    total_cost_usd FLOAT DEFAULT 0,
    started_at TIMESTAMP,
    finished_at TIMESTAMP
);

ALTER TABLE mensajes_historial
ADD COLUMN ejecucion_id UUID,
ADD COLUMN model TEXT,
ADD COLUMN tokens_input INT DEFAULT 0,
ADD COLUMN tokens_output INT DEFAULT 0,
ADD COLUMN cost_usd FLOAT DEFAULT 0,
ADD COLUMN latency_ms INT DEFAULT 0,
ADD COLUMN tool_name TEXT,
ADD COLUMN tool_status TEXT;

ALTER TABLE mensajes_historial
ADD CONSTRAINT fk_ejecucion
FOREIGN KEY (ejecucion_id) REFERENCES ejecuciones(id);
