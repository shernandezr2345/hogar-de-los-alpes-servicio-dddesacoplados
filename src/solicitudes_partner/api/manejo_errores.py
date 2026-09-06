"""Traduce excepciones de dominio a respuestas HTTP."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from solicitudes_partner.dominio.excepciones import (
    SolicitudDuplicadaError,
    SolicitudNoEncontradaError,
    TransicionEstadoInvalidaError,
    ValueObjectInvalidoError,
)


def registrar_manejadores_errores(app: FastAPI) -> None:
    @app.exception_handler(ValueObjectInvalidoError)
    async def _manejar_value_object_invalido(
        request: Request, exc: ValueObjectInvalidoError
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detalle": str(exc)})

    @app.exception_handler(SolicitudDuplicadaError)
    async def _manejar_solicitud_duplicada(
        request: Request, exc: SolicitudDuplicadaError
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detalle": str(exc)})

    @app.exception_handler(TransicionEstadoInvalidaError)
    async def _manejar_transicion_invalida(
        request: Request, exc: TransicionEstadoInvalidaError
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detalle": str(exc)})

    @app.exception_handler(SolicitudNoEncontradaError)
    async def _manejar_no_encontrada(
        request: Request, exc: SolicitudNoEncontradaError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detalle": str(exc)})
