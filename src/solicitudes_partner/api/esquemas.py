"""Modelos Pydantic de request/response del adaptador HTTP.

Deliberadamente simples: no repiten reglas de negocio (eso lo valida el dominio); solo
describen la forma de los datos que entran y salen por HTTP.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class RegistrarSolicitudPartnerRequest(BaseModel):
    solicitud_id: str
    partner_id: str
    referencia_externa: str
    tipo_servicio: str


class RegistrarSolicitudPartnerResponse(BaseModel):
    solicitud_id: str
    estado: str


class VistaSolicitudPartnerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    solicitud_id: str
    partner_id: str
    referencia_externa: str
    tipo_servicio: str
    estado: str


class ErrorResponse(BaseModel):
    detalle: str


class PublicarPendientesOutboxResponse(BaseModel):
    publicados: int
