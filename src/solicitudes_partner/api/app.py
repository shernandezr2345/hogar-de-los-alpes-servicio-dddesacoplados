"""Factory de la aplicacion FastAPI (adaptador primario) - Fase 5."""

from __future__ import annotations

from fastapi import FastAPI

from .manejo_errores import registrar_manejadores_errores
from .rutas_admin import router as router_admin
from .rutas_solicitudes_partner import router as router_solicitudes_partner


def crear_app() -> FastAPI:
    app = FastAPI(
        title="Hogar de los Alpes - Solicitudes de Partner",
        description="API REST para registrar y consultar solicitudes de partner.",
        version="1.0.0",
    )
    registrar_manejadores_errores(app)
    app.include_router(router_solicitudes_partner)
    app.include_router(router_admin)
    return app


app = crear_app()
