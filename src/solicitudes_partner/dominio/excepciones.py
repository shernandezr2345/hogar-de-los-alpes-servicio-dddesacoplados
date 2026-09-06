"""Excepciones del dominio de solicitudes de partner."""


class ErrorDominioSolicitudPartner(Exception):
    """Base para errores del dominio de solicitudes."""


class ValueObjectInvalidoError(ErrorDominioSolicitudPartner):
    """Se lanza cuando un Value Object no cumple sus invariantes."""


class SolicitudDuplicadaError(ErrorDominioSolicitudPartner):
    """Se lanza cuando ya existe una solicitud activa para partner+referencia."""


class TransicionEstadoInvalidaError(ErrorDominioSolicitudPartner):
    """Se lanza cuando se intenta una transición de estado no permitida."""


class SolicitudNoEncontradaError(ErrorDominioSolicitudPartner):
    """Se lanza cuando no existe una solicitud para el identificador dado."""
