"""Endpoints REST para el recurso solicitudes-partner (comando + Read Model)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from solicitudes_partner.aplicacion.comandos import RegistrarSolicitudPartner
from solicitudes_partner.aplicacion.consultas_lectura import (
    ConsultarVistaSolicitudPartner,
    ConsultasSolicitudesPartner,
    ListarSolicitudesPartnerPorPartner,
)
from solicitudes_partner.aplicacion.servicios import ServicioSolicitudesPartner

from .dependencias import obtener_consultas, obtener_servicio
from .esquemas import (
    RegistrarSolicitudPartnerRequest,
    RegistrarSolicitudPartnerResponse,
    VistaSolicitudPartnerResponse,
)

router = APIRouter(prefix="/solicitudes-partner", tags=["solicitudes-partner"])


@router.post("", response_model=RegistrarSolicitudPartnerResponse, status_code=201)
def registrar_solicitud(
    peticion: RegistrarSolicitudPartnerRequest,
    servicio: ServicioSolicitudesPartner = Depends(obtener_servicio),
    consultas: ConsultasSolicitudesPartner = Depends(obtener_consultas),
) -> RegistrarSolicitudPartnerResponse:
    comando = RegistrarSolicitudPartner(
        solicitud_id=peticion.solicitud_id,
        partner_id=peticion.partner_id,
        referencia_externa=peticion.referencia_externa,
        tipo_servicio=peticion.tipo_servicio,
    )
    servicio.registrar_solicitud(comando)

    # Se relee del Read Model (no del agregado devuelto) para reflejar el estado final,
    # ya resuelto de forma sincrona por Reglas/ResultadoReglas antes de responder.
    vista = consultas.consultar_vista(
        ConsultarVistaSolicitudPartner(solicitud_id=peticion.solicitud_id)
    )
    return RegistrarSolicitudPartnerResponse(solicitud_id=vista.solicitud_id, estado=vista.estado)


@router.get("/{solicitud_id}", response_model=VistaSolicitudPartnerResponse)
def obtener_solicitud(
    solicitud_id: str,
    consultas: ConsultasSolicitudesPartner = Depends(obtener_consultas),
) -> VistaSolicitudPartnerResponse:
    vista = consultas.consultar_vista(ConsultarVistaSolicitudPartner(solicitud_id=solicitud_id))
    return VistaSolicitudPartnerResponse.model_validate(vista)


@router.get("", response_model=list[VistaSolicitudPartnerResponse])
def listar_solicitudes_por_partner(
    partner_id: str = Query(...),
    consultas: ConsultasSolicitudesPartner = Depends(obtener_consultas),
) -> list[VistaSolicitudPartnerResponse]:
    vistas = consultas.listar_por_partner(
        ListarSolicitudesPartnerPorPartner(partner_id=partner_id)
    )
    return [VistaSolicitudPartnerResponse.model_validate(vista) for vista in vistas]
