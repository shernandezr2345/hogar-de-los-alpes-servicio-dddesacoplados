CREATE TABLE IF NOT EXISTS solicitudes_partner (
    solicitud_id VARCHAR PRIMARY KEY,
    partner_id VARCHAR NOT NULL,
    referencia_externa VARCHAR NOT NULL,
    tipo_servicio VARCHAR NOT NULL,
    estado VARCHAR NOT NULL,
    UNIQUE (partner_id, referencia_externa)
);
