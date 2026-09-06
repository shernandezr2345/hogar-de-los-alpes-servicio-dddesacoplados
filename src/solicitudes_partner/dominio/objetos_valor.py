"""Value Objects mínimos del agregado SolicitudPartner."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .excepciones import ValueObjectInvalidoError


def _validar_texto(valor: str, nombre_campo: str) -> str:
    texto = valor.strip() if isinstance(valor, str) else ""
    if not texto:
        raise ValueObjectInvalidoError(f"{nombre_campo} es obligatorio")
    return texto


class EstadoSolicitud(str, Enum):
    """Estados oficiales aprobados para la FASE 1."""

    RECIBIDA = "RECIBIDA"
    LISTA_PARA_ATENCION = "LISTA_PARA_ATENCION"
    RECHAZADA = "RECHAZADA"


@dataclass(frozen=True)
class SolicitudId:
    valor: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "valor", _validar_texto(self.valor, "solicitud_id"))


@dataclass(frozen=True)
class PartnerId:
    valor: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "valor", _validar_texto(self.valor, "partner_id"))


@dataclass(frozen=True)
class ReferenciaExterna:
    valor: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "valor", _validar_texto(self.valor, "referencia_externa"))


@dataclass(frozen=True)
class TipoServicio:
    valor: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "valor", _validar_texto(self.valor, "tipo_servicio"))
