CREATE TABLE IF NOT EXISTS solicitudes_partner (
    solicitud_id VARCHAR PRIMARY KEY,
    partner_id VARCHAR NOT NULL,
    referencia_externa VARCHAR NOT NULL,
    tipo_servicio VARCHAR NOT NULL,
    estado VARCHAR NOT NULL,
    UNIQUE (partner_id, referencia_externa)
);

-- Bloque 2.5: Transactional Outbox para publicacion confiable de eventos del agregado.
CREATE TABLE IF NOT EXISTS outbox_eventos (
    id BIGSERIAL PRIMARY KEY,
    solicitud_id VARCHAR NOT NULL,
    tipo_evento VARCHAR NOT NULL,
    payload JSONB NOT NULL,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    procesado_en TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS idx_outbox_eventos_pendientes
    ON outbox_eventos (id)
    WHERE procesado_en IS NULL;

-- Fase 4: Read Model (CQRS) - proyeccion de solo lectura, poblada por ProyeccionSolicitudesPartner.
CREATE TABLE IF NOT EXISTS solicitudes_partner_vista (
    solicitud_id VARCHAR PRIMARY KEY,
    partner_id VARCHAR NOT NULL,
    referencia_externa VARCHAR NOT NULL,
    tipo_servicio VARCHAR NOT NULL,
    estado VARCHAR NOT NULL,
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_solicitudes_partner_vista_partner_id
    ON solicitudes_partner_vista (partner_id);
