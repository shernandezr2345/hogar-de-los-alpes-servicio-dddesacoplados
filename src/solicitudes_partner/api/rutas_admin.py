"""Endpoint administrativo para drenar el Outbox transaccional (Bloque 2.5) via HTTP."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from .dependencias import obtener_relay
from .esquemas import PublicarPendientesOutboxResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/outbox/publicar-pendientes", response_model=PublicarPendientesOutboxResponse)
def publicar_pendientes_outbox(
    relay: Any | None = Depends(obtener_relay),
) -> PublicarPendientesOutboxResponse:
    if relay is None:
        raise HTTPException(
            status_code=501,
            detail="El Outbox no esta disponible con el backend actual (memoria)",
        )
    publicados = relay.publicar_pendientes()
    return PublicarPendientesOutboxResponse(publicados=publicados)
